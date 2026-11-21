"""Archipelago protocol state for APRac2, independent from sockets and game memory."""
import importlib.util
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rac2_native_contract', ROOT / 'apworld/rac2_openrac/native.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class Session:
    def __init__(self, slot, password='', uuid='', contract=None):
        import json
        contract = contract or json.loads((ROOT / 'data/aprac2-contract.json').read_text(encoding='utf-8'))
        self.item_ids = {row['id'] for row in contract['items']}
        self.location_ids = {row['id'] for row in contract['locations']}
        self.slot_name, self.password, self.uuid = slot, password, uuid
        self.seed = None
        self.identity = None
        self.connected = self.synced = self.refused = False
        self.options = None
        self.items = []
        self.checked = set()
        self.scouted = {}
        self.pending = set()
        self.goal = False
        self.error = ''
        self.messages = []
        self.deaths = []
        self.last_death = 0.0
        self.last_native_death = None

    def disconnect(self):
        self.connected = self.synced = False

    def snapshot(self):
        return dict(type='state', connected=self.connected, synced=self.synced,
                    identity=self.identity, options=self.options, items=self.items,
                    checked=sorted(self.checked), scouts=self.scouted, goal=self.goal,
                    error=self.error, death_events=self.deaths[-32:])

    def reject(self, reason):
        self.error = reason
        self.refused = True
        self.connected = self.synced = False
        return []

    def receive(self, packet):
        if not isinstance(packet, dict):
            return self.reject('Malformed Archipelago packet')
        cmd = packet.get('cmd')
        if cmd == 'RoomInfo':
            seed = packet.get('seed_name')
            if not isinstance(seed, str) or not seed:
                return self.reject('Server did not provide a seed name')
            if self.seed is not None and seed != self.seed:
                return self.reject('Server changed seeds; restart the client and start a matching game')
            self.seed = seed
            return [dict(cmd='Connect', game=native.GAME, name=self.slot_name,
                         password=self.password or None, uuid=self.uuid,
                         version=dict(major=0, minor=6, build=9, **{'class': 'Version'}),
                         items_handling=7, tags=['AP'], slot_data=True)]
        if cmd == 'ConnectionRefused':
            return self.reject('Connection refused: ' + ', '.join(map(str, packet.get('errors', []))))
        if cmd == 'Connected':
            try:
                options = native.validate_slot_data(packet.get('slot_data'))
                team, slot = packet['team'], packet['slot']
                if type(team) is not int or team < 0 or type(slot) is not int or slot <= 0:
                    raise ValueError('Invalid server slot identity')
                if options['openrac']['seed'] != self.seed or options['openrac']['player'] != slot:
                    raise ValueError('Native seed metadata does not match this server slot')
                active = set(options['openrac']['active_locations'])
                checked = set(packet.get('checked_locations', []))
                missing = set(packet.get('missing_locations', []))
                if active != checked | missing or not active <= self.location_ids:
                    raise ValueError('Server locations differ from the native seed metadata')
                if not set(options['openrac']['starting_items']) <= self.item_ids:
                    raise ValueError('Unknown starting item')
                identity = dict(seed=self.seed, team=team, slot=slot)
                if self.identity is not None and identity != self.identity:
                    raise ValueError('Slot identity changed; restart the client')
            except (ValueError, KeyError, TypeError) as error:
                return self.reject(str(error))
            self.identity, self.options = identity, options
            self.connected, self.synced, self.refused = True, False, False
            self.error = ''
            self.items = []
            self.checked = checked
            outgoing = [dict(cmd='Sync'), dict(cmd='LocationScouts', locations=sorted(active), create_as_hint=0)]
            if options['death_link']:
                outgoing.append(dict(cmd='ConnectUpdate', tags=['AP', 'DeathLink']))
            if self.pending:
                outgoing.append(dict(cmd='LocationChecks', locations=sorted(self.pending)))
            if self.goal:
                outgoing.append(dict(cmd='StatusUpdate', status=30))
            return outgoing
        if not self.connected:
            return []
        if cmd == 'ReceivedItems':
            index, rows = packet.get('index'), packet.get('items')
            if type(index) is not int or index < 0 or not isinstance(rows, list):
                return self.reject('Malformed ReceivedItems')
            if any(not isinstance(row, dict) or type(row.get('item')) is not int
                   or row['item'] not in self.item_ids for row in rows):
                return self.reject('Received an unknown APRac2 item; update the matching APWorld and mod')
            if index > len(self.items) or (not self.synced and index != 0):
                self.synced = False
                return [dict(cmd='Sync')]
            incoming = [dict(item=row['item'], location=row.get('location', 0), player=row.get('player', 0),
                             flags=row.get('flags', 0)) for row in rows]
            overlap = min(len(incoming), len(self.items) - index)
            if self.items[index:index + overlap] != incoming[:overlap]:
                return self.reject('ReceivedItems history changed for this slot')
            if index == 0 and len(incoming) < len(self.items):
                self.synced = False
                return [dict(cmd='Sync')]
            self.items[index:index + len(incoming)] = incoming
            self.synced = True
        elif cmd == 'RoomUpdate':
            self.checked.update(packet.get('checked_locations', []))
        elif cmd == 'LocationInfo':
            for row in packet.get('locations', []):
                if isinstance(row, dict) and row.get('location') in self.options['openrac']['active_locations']:
                    self.scouted[str(row['location'])] = row
        elif cmd == 'PrintJSON':
            self.messages.append(packet.get('data', []))
            self.messages = self.messages[-32:]
        elif cmd == 'Bounced' and self.options['death_link'] and 'DeathLink' in packet.get('tags', []):
            data = packet.get('data', {})
            stamp = data.get('time')
            if isinstance(stamp, (int, float)) and stamp != self.last_death:
                # Event identity survives repeated state snapshots and avoids echoing our own bounce.
                event = dict(time=stamp, source=str(data.get('source', '')), cause=str(data.get('cause', '')))
                if event not in self.deaths:
                    self.deaths.append(event)
                    self.deaths = self.deaths[-32:]
        return []

    def game_event(self, event):
        if not self.connected or not self.synced or event.get('identity') != self.identity:
            return []
        kind = event.get('type')
        if kind == 'checks':
            locations = event.get('locations', [])
            if not isinstance(locations, list) or any(type(x) is not int for x in locations):
                raise ValueError('Malformed game location checks')
            if not set(locations) <= set(self.options['openrac']['active_locations']):
                raise ValueError('Game submitted a location disabled in this seed')
            self.pending.update(locations)
            return [dict(cmd='LocationChecks', locations=sorted(set(locations)))] if locations else []
        if kind == 'goal':
            self.goal = True
            return [dict(cmd='StatusUpdate', status=30)]
        if kind == 'death' and self.options['death_link']:
            event_id = event.get('event_id')
            if event_id is None or event_id == self.last_native_death:
                return []
            self.last_native_death = event_id
            self.last_death = time.time()
            return [dict(cmd='Bounce', tags=['DeathLink'], data=dict(
                time=self.last_death, source=self.slot_name, cause=f'{self.slot_name} ran out of Nanotech.'))]
        return []
