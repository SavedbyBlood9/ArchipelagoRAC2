import asyncio
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'client'))
from session import Session
from client import Bridge
from test_session import connected

try:
    import websockets
except ImportError:
    websockets=None


@unittest.skipIf(websockets is None,'Install client/requirements.txt for transport integration tests')
class TransportTest(unittest.IsolatedAsyncioTestCase):
    async def test_authenticated_bridge_and_websocket(self):
        session=Session('Tester')
        # Build the same Connected packet the pure protocol tests validate.
        fixture=Session('Tester'); connected(fixture)
        data=fixture.options
        received=asyncio.Queue()
        async def fake_server(socket, path):
            await socket.send(json.dumps([dict(cmd='RoomInfo',seed_name='seed-1')]))
            response=json.loads(await socket.recv())[0]
            self.assertEqual(response['cmd'],'Connect')
            self.assertEqual(response['items_handling'],7)
            await socket.send(json.dumps([
                dict(cmd='Connected',team=0,slot=1,checked_locations=[],
                     missing_locations=data['openrac']['active_locations'],slot_data=data),
                dict(cmd='ReceivedItems',index=0,items=[dict(item=10,location=10,player=1,flags=1)])]))
            try:
                async for raw in socket:
                    for packet in json.loads(raw):
                        await received.put(packet)
            except websockets.ConnectionClosed:
                pass

        bridge=Bridge(session,'unit-test-token-012345')
        async with websockets.serve(fake_server,'127.0.0.1',0) as websocket_server:
            port=websocket_server.sockets[0].getsockname()[1]
            task=asyncio.create_task(bridge.archipelago(f'ws://127.0.0.1:{port}'))
            listener=await asyncio.start_server(bridge.game,'127.0.0.1',0)
            local_port=listener.sockets[0].getsockname()[1]
            writer=None
            try:
                # Wrong-token peers get no state.
                bad_reader,bad_writer=await asyncio.open_connection('127.0.0.1',local_port)
                bad_writer.write(b'{"type":"hello","token":"wrong"}\n'); await bad_writer.drain()
                self.assertEqual(await asyncio.wait_for(bad_reader.read(),2),b'')
                bad_writer.close(); await bad_writer.wait_closed()
                reader,writer=await asyncio.open_connection('127.0.0.1',local_port)
                writer.write(b'{"type":"hello","token":"unit-test-token-012345"}\n'); await writer.drain()
                state={}
                async with asyncio.timeout(3):
                    while not state.get('synced'):
                        state=json.loads(await reader.readline())
                self.assertEqual(state['items'][0]['item'],10)
                writer.write((json.dumps(dict(type='checks',identity=state['identity'],locations=[10]))+'\n').encode())
                await writer.drain()
                async with asyncio.timeout(3):
                    while True:
                        packet=await received.get()
                        if packet['cmd']=='LocationChecks':
                            self.assertEqual(packet['locations'],[10]); break
            finally:
                if writer:
                    writer.close(); await writer.wait_closed()
                listener.close(); await listener.wait_closed()
                task.cancel(); await asyncio.gather(task,return_exceptions=True)


if __name__=='__main__': unittest.main()
