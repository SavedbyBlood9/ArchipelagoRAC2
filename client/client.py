"""ArchipelagoRAC2 OpenRAC sidecar: Archipelago WebSocket <-> authenticated loopback game bridge."""
import argparse
import asyncio
import contextlib
import json
import secrets
import uuid
from session import Session

MAX_PACKET = 1024 * 1024


class Bridge:
    def __init__(self, session, token):
        self.session, self.token = session, token
        self.outgoing = asyncio.Queue(maxsize=1024)
        self.game_connected = False

    async def game(self, reader, writer):
        claimed = False
        try:
            raw = await asyncio.wait_for(reader.readline(), 5)
            hello = json.loads(raw)
            if hello.get('type') != 'hello' or not secrets.compare_digest(str(hello.get('token', '')), self.token):
                return
            if self.game_connected:
                return
            self.game_connected = claimed = True
            print('OpenRAC bridge connected', flush=True)

            async def states():
                previous = None
                while True:
                    snapshot = self.session.snapshot()
                    raw = json.dumps(snapshot, separators=(',', ':')).encode() + b'\n'
                    if len(raw) > MAX_PACKET:
                        raise ValueError('Native state exceeds bridge packet limit')
                    if raw != previous:
                        writer.write(raw)
                        await writer.drain()
                        previous = raw
                    await asyncio.sleep(0.1)

            async def events():
                while raw := await reader.readline():
                    event = json.loads(raw)
                    for packet in self.session.game_event(event):
                        await self.outgoing.put(packet)

            send = asyncio.create_task(states())
            receive = asyncio.create_task(events())
            try:
                done, pending = await asyncio.wait([send, receive], return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    task.result()
            finally:
                send.cancel(); receive.cancel()
                await asyncio.gather(send, receive, return_exceptions=True)
        except (ValueError, KeyError, OSError, asyncio.TimeoutError, asyncio.LimitOverrunError) as error:
            print(f'Game bridge disconnected: {error}', flush=True)
        finally:
            if claimed:
                self.game_connected = False
            writer.close()
            with contextlib.suppress(OSError):
                await writer.wait_closed()

    async def archipelago(self, server):
        import websockets
        if '://' not in server:
            raise ValueError('Use an explicit ws:// or wss:// server URL')
        if not server.startswith(('ws://', 'wss://')):
            raise ValueError('Only ws:// and wss:// servers are supported')
        while not self.session.refused:
            self.session.disconnect()
            try:
                async with websockets.connect(server, max_size=MAX_PACKET, ping_interval=20) as socket:
                    print('Connected to Archipelago transport', flush=True)

                    async def sender():
                        while True:
                            packet = await self.outgoing.get()
                            # Native events from a dead connection are reconstructed from the loaded save.
                            if self.session.connected:
                                await socket.send(json.dumps([packet]))

                    async def receiver():
                        async for message in socket:
                            packets = json.loads(message)
                            if not isinstance(packets, list):
                                raise ValueError('Expected an Archipelago packet array')
                            for packet in packets:
                                response = self.session.receive(packet)
                                if response:
                                    await socket.send(json.dumps(response))
                            if self.session.refused:
                                print(self.session.error, flush=True)
                                return

                    send = asyncio.create_task(sender())
                    receive = asyncio.create_task(receiver())
                    try:
                        done, pending = await asyncio.wait([send, receive], return_when=asyncio.FIRST_COMPLETED)
                        for task in done:
                            task.result()
                    finally:
                        send.cancel(); receive.cancel()
                        await asyncio.gather(send, receive, return_exceptions=True)
            except (OSError, ValueError, websockets.WebSocketException) as error:
                self.session.error = str(error)
                print(f'Archipelago connection interrupted: {error}', flush=True)
            finally:
                self.session.disconnect()
                while not self.outgoing.empty():
                    self.outgoing.get_nowait()
            if not self.session.refused:
                await asyncio.sleep(3)


async def main(args):
    token = args.token or secrets.token_hex(16)
    session = Session(args.slot, args.password, str(uuid.uuid4()))
    bridge = Bridge(session, token)
    server = await asyncio.start_server(bridge.game, '127.0.0.1', args.port, limit=MAX_PACKET)
    print(f'Bridge listening on 127.0.0.1:{args.port}; launcher bridge_token: {token}', flush=True)
    async with server:
        await bridge.archipelago(args.server)
        if session.refused:
            raise SystemExit(session.error)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', required=True, help='wss://archipelago.gg:PORT or ws://localhost:PORT')
    parser.add_argument('--slot', required=True)
    parser.add_argument('--password', default='')
    parser.add_argument('--port', type=int, default=38282)
    parser.add_argument('--token', default='', help='Must match bridge_token in the launcher; random when omitted')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('--port must be from 1 to 65535')
    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        pass
