import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'client'))
from session import Session, native


def connected(session, **changes):
    session.receive(dict(cmd='RoomInfo', seed_name='seed-1'))
    contract = json.loads((ROOT / 'data/aprac2-contract.json').read_text(encoding='utf-8'))
    locations = [row['id'] for row in contract['locations']]
    data = dict(native.DEFAULTS, openrac=dict(format=1, game=native.GAME, target='rac2/ntsc',
                seed='seed-1', player=1, starting_items=[115,120,201,202,203],
                starting_weapon_ids=[115,120], active_locations=locations))
    data.update(changes)
    return session.receive(dict(cmd='Connected', team=0, slot=1, checked_locations=[],
                                missing_locations=locations, slot_data=data))


class SessionTest(unittest.TestCase):
    def test_pal_and_shared_seed_targets(self):
        fixture=Session('PAL');connected(fixture)
        data=copy.deepcopy(fixture.options)
        for target in ('rac2','rac2/pal','rac2/ntsc'):
            data['openrac']['target']=target
            data['openrac']['supported_discs']=['ntsc','pal']
            self.assertEqual(native.validate_slot_data(data)['openrac']['supported_discs'],['ntsc','pal'])
        data['openrac']['supported_discs']=['ntsc2']
        with self.assertRaises(ValueError):native.validate_slot_data(data)

    def test_connect_identity_and_all_options(self):
        session = Session('Tester', 'secret', 'unit')
        connect = session.receive(dict(cmd='RoomInfo', seed_name='seed-1'))[0]
        self.assertEqual(connect['items_handling'], 7)
        self.assertEqual(connect['game'], 'Ratchet & Clank 2')
        self.assertEqual(connect['password'], 'secret')
        outgoing = connected(session, nanotech_xp_multiplier=600, weapon_xp_multiplier=30)
        self.assertTrue(session.connected)
        self.assertFalse(session.synced)
        self.assertEqual(session.options['nanotech_xp_multiplier'], 600)
        self.assertTrue(any(p['cmd'] == 'Sync' for p in outgoing))
        self.assertNotIn('secret', json.dumps(session.snapshot()))

    def test_received_history_replay_and_gap(self):
        session = Session('Tester'); connected(session)
        item = dict(item=304, location=10, player=2, flags=0)
        session.receive(dict(cmd='ReceivedItems', index=0, items=[item]))
        session.receive(dict(cmd='ReceivedItems', index=0, items=[item]))
        self.assertEqual(len(session.items), 1)
        outgoing = session.receive(dict(cmd='ReceivedItems', index=3, items=[item]))
        self.assertEqual(outgoing, [dict(cmd='Sync')]); self.assertFalse(session.synced)
        session.receive(dict(cmd='ReceivedItems', index=0, items=[item,item]))
        self.assertTrue(session.synced); self.assertEqual(len(session.items), 2)
        session.receive(dict(cmd='ReceivedItems', index=0, items=[dict(item=301)]))
        self.assertTrue(session.refused)

    def test_checks_reconnect_and_foreign_save(self):
        session = Session('Tester'); connected(session)
        session.receive(dict(cmd='ReceivedItems', index=0, items=[]))
        wrong = dict(type='checks', identity=dict(seed='wrong',team=0,slot=1), locations=[10])
        self.assertEqual(session.game_event(wrong), [])
        event = dict(type='checks', identity=session.identity, locations=[10])
        self.assertEqual(session.game_event(event), [dict(cmd='LocationChecks',locations=[10])])
        with self.assertRaises(ValueError):
            session.game_event(dict(event, locations=[999999]))
        session.disconnect()
        self.assertEqual(session.game_event(event), [])
        outgoing = connected(session)
        self.assertIn(dict(cmd='LocationChecks',locations=[10]), outgoing)

    def test_original_ps2_seed_and_invalid_options_rejected(self):
        session=Session('Tester'); session.receive(dict(cmd='RoomInfo',seed_name='seed-1'))
        session.receive(dict(cmd='Connected', team=0, slot=1, slot_data=dict(skip_wupash_nebula=True)))
        self.assertTrue(session.refused); self.assertIn('PS2',session.error)
        for key, value in [('nanotech_xp_multiplier',19),('weapon_xp_multiplier',601),('starting_weapons',4)]:
            session=Session('Tester'); connected(session, **{key:value})
            self.assertTrue(session.refused); self.assertIn(key,session.error)

    def test_goal_and_deathlink(self):
        session=Session('Tester'); outgoing=connected(session,death_link=1)
        self.assertTrue(any(p['cmd']=='ConnectUpdate' for p in outgoing))
        session.receive(dict(cmd='ReceivedItems',index=0,items=[]))
        identity=session.identity
        self.assertEqual(session.game_event(dict(type='goal',identity=identity)),[dict(cmd='StatusUpdate',status=30)])
        event=dict(type='death',identity=identity,event_id='death-1')
        bounce=session.game_event(event)[0]
        self.assertEqual(session.game_event(event),[])
        session.receive(dict(cmd='Bounced',tags=['DeathLink'],data=bounce['data']))
        self.assertEqual(session.deaths,[])
        session.receive(dict(cmd='Bounced',tags=['DeathLink'],data=dict(time=1,source='Other')))
        self.assertEqual(len(session.deaths),1)


if __name__ == '__main__':
    unittest.main()
