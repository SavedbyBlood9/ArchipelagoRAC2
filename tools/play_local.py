"""Connect Archipelago, then launch the API-preview host with isolated cards/settings/plugins."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--server',required=True)
p.add_argument('--slot',required=True)
p.add_argument('--password')
p.add_argument('--region',choices=['auto','ntsc','ntsc2','pal'],default='auto')
p.add_argument('--host',type=Path)
p.add_argument('--data-root',type=Path)
a=p.parse_args()
if os.name!='nt':p.error('This local launcher targets Windows')
if a.data_root is None:
    local_pal=ROOT.parents[1]/'work/OpenRAC/build/aprac2-pal-data'
    a.data_root=local_pal if a.region=='pal' and local_pal.is_dir() else Path.home()/'OpenRAC/active/rac2/data'
iso=a.data_root/'iso_data/rac2'
detected='pal' if (iso/'SCES_516.07').is_file() else 'ntsc' if (iso/'SCUS_972.68').is_file() else None
if detected is None:p.error('--data-root must contain an extracted supported rac2 executable')
# USA v1.01 and v2.00 share SCUS_972.68: the extracted port/<disc> folder tells them apart.
if detected=='ntsc' and (a.region=='ntsc2' or (a.region=='auto' and (a.data_root/'port/ntsc2').is_dir()
                                                and not (a.data_root/'port/ntsc').is_dir())):
    detected='ntsc2'
if a.region!='auto' and a.region!=detected:p.error('Selected region does not match the extracted game data')
region=detected
if a.host is None:
    a.host=ROOT.parents[1]/f'work/OpenRAC-hooks-split/port/build/api-queries-windowed/openrac-rac2-{region}.exe'
if not a.host.is_file():p.error('Windowed API-preview host not found; pass --host with an API 1.40 windowed host')
if not (a.data_root/'iso_data/rac2').is_dir():p.error('--data-root must contain extracted iso_data/rac2')
levels=a.data_root/'port'/region
if not (levels/'level_24/manifest.json').is_file():p.error('--data-root must also contain extracted port/'+region+' rendering assets')
try:import websockets
except ImportError:p.error('Install the sidecar first: python -m pip install -r client/requirements.txt')
run=ROOT/'local-play/api40'/region
data=run/'data';data.mkdir(parents=True,exist_ok=True)
assets=data/'iso_data';target=(a.data_root/'iso_data').resolve()
if assets.exists():
    if assets.resolve()!=target:p.error('Existing local-play assets point to another data root')
else:
    # PowerShell single-quoted literals escape embedded quotes by doubling them.
    quote=lambda path:"'"+str(path).replace("'","''")+"'"
    command='New-Item -ItemType Junction -Path '+quote(assets)+' -Target '+quote(target)+' | Out-Null'
    subprocess.run(['powershell.exe','-NoProfile','-Command',command],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
plugins=run/'plugins';mod=plugins/'archipelago-rac2';mod.mkdir(parents=True,exist_ok=True)
archive=ROOT/'dist/archipelago-rac2-0.6.2-windows-x86_64.zip'
with zipfile.ZipFile(archive) as z:z.extractall(mod)
with socket.socket() as candidate:
    candidate.bind(('127.0.0.1',0));port=candidate.getsockname()[1]
token=secrets.token_urlsafe(32)
config=dict(format=1,mods=[dict(id='archipelago-rac2',enabled=True,settings=dict(
    enable_gameplay=True,bridge_port=port,bridge_token=token))])
(plugins/'plugins.json').write_text(json.dumps(config,indent=2))
client=[sys.executable,str(ROOT/'client/client.py'),'--server',a.server,'--slot',a.slot,'--port',str(port),'--token',token]
if a.password is not None:client+=['--password',a.password]

async def wait_for_slot():
    for attempt in range(240):
        try:
            reader,writer=await asyncio.open_connection('127.0.0.1',port)
        except OSError:
            if sidecar.poll() is not None:raise RuntimeError('Sidecar exited; see local-play/client.log')
            await asyncio.sleep(.25);continue
        try:
            writer.write((json.dumps(dict(type='hello',token=token))+'\n').encode());await writer.drain()
            while packet:=await reader.readline():
                state=json.loads(packet)
                if state.get('error'):raise RuntimeError(state['error'])
                if state.get('connected') and state.get('synced'):return
        finally:writer.close();await writer.wait_closed()
    raise RuntimeError('Sidecar did not open its local bridge; see local-play/client.log')

with (run/'client.log').open('w') as client_log,(run/'game.log').open('w') as game_log:
    sidecar=subprocess.Popen(client,stdout=client_log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        print('Connecting to Archipelago...',flush=True)
        asyncio.run(asyncio.wait_for(wait_for_slot(),90))
        print('Connected. Start a new campaign in the game. Test cards/settings are under local-play.',flush=True)
        result=subprocess.run([str(a.host.resolve()),'--window','--data',str(data),'--cards',str(run/'cards'),
            '--levels',str(levels.resolve()),'--settings',str(run/'settings.ini'),'--controls',str(run/'controls'),
            '--plugins',str(plugins/'plugins.json'),'--probes',str(run/'probes')],
            stdout=game_log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:raise RuntimeError('Game exited with an error; see local-play/game.log')
    finally:
        if sidecar.poll() is None:sidecar.terminate()
        try:sidecar.wait(timeout=5)
        except subprocess.TimeoutExpired:sidecar.kill();sidecar.wait()
