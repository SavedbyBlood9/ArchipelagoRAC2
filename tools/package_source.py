"""Bundle redistributable sources and current mod packages, excluding local game code/data."""
import argparse
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output',type=Path,default=root.parent/'ArchipelagoRAC2-source.zip')
a=p.parse_args()
excluded={'.git','__pycache__','local-play','build','.pytest_cache'}
packages={'ArchipelagoRAC2.apworld','ArchipelagoRAC2-0.5.0-windows-x86_64.zip','ArchipelagoRAC2-Probe-0.2.0-windows-x86_64.zip'}
files=[]
for path in sorted(root.rglob('*')):
    rel=path.relative_to(root)
    if not path.is_file() or excluded.intersection(rel.parts):continue
    if rel.parts[0]=='dist' and path.name not in packages:continue
    if rel.parts[0]=='host-patch':continue
    if path.suffix.lower() in {'.iso','.bin','.exe','.dll','.obj','.pyc','.log'}:continue
    files.append((path,rel))
a.output.parent.mkdir(parents=True,exist_ok=True)
with ZipFile(a.output,'w',ZIP_DEFLATED) as archive:
    for path,rel in files:archive.write(path,Path(root.name)/rel)
print(a.output)
