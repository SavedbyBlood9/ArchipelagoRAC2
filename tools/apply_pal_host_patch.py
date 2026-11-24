"""Apply the verified SCES_516.07 native hooks and PAL-specific gameplay overrides."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from apply_host_patch import apply,append

p=argparse.ArgumentParser(description=__doc__);p.add_argument('checkout',type=Path);a=p.parse_args()
root=a.checkout.resolve();project=Path(__file__).resolve().parents[1]
apply(root,pal=True)
subprocess.run([sys.executable,str(project/'tools/generate_host_overrides.py'),str(root),'--version','pal'],check=True)
symbols=json.loads((project/'data/pal-host-symbols.json').read_text())
rows=[]
for line in (project/'host-patch/hooks.tsv').read_text().splitlines():
    cols=line.split('\t');cols[0]=symbols[cols[0]]['symbol'];rows.append('\t'.join(cols))
target=root/'port/game/rac2-pal'
if not(target/'hostgen.json').is_file():raise ValueError('The checkout has no PAL host')
append(target/'libraries.tsv',rows,1)
dest=target/'hand/aprac2';dest.mkdir(exist_ok=True)
rows=[];generated=project/'host-patch/overrides-pal'
for line in (generated/'overrides.tsv').read_text().splitlines():
    if not line or line.startswith('#'):continue
    symbol,name=line.split('\t');shutil.copyfile(generated/name,dest/name)
    rows.append(symbol+'\taprac2/'+name)
append(target/'hand/overrides.tsv',rows,1)
print('Applied PAL callbacks and twenty region-specific overrides for SCES_516.07')
