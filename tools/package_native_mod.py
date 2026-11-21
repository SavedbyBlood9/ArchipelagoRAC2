"""Package against the stock SDK plus this project's additional native hook declarations."""
import argparse
import importlib.util
from pathlib import Path
import shutil
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--sdk',type=Path,required=True)
p.add_argument('--input',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
spec=importlib.util.spec_from_file_location('openrac_package_mod',a.sdk/'tools/package_mod.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
with tempfile.TemporaryDirectory(prefix='aprac2-bindings-') as folder:
    bindings=Path(folder)
    for source in (a.sdk/'bindings').glob('*.ids.lock'):shutil.copyfile(source,bindings/source.name)
    lock=bindings/'rac2.ids.lock'
    text=lock.read_text(encoding='utf-8')
    hooks=Path(__file__).resolve().parents[1]/'host-patch/hooks.tsv'
    for row in hooks.read_text().splitlines():
        symbol,area,name,kind,*_=row.split('\t')
        # Packaging names only; the native host resolves these added aliases directly.
        text+='rac2.archipelago.'+name.lower()+'\t'+symbol+'\t'+name+'\n'
    lock.write_text(text,encoding='utf-8')
    module._BINDINGS=bindings
    project=Path(__file__).resolve().parents[1]
    shutil.copyfile(project/'CREDITS.md',a.input/'README-CREDITS.md')
    packaged=module.package(a.input,a.output)
    branded=a.output/str(packaged.name).replace('aprac2-openrac-dev-','ArchipelagoRAC2-').replace('aprac2-openrac-probe-','ArchipelagoRAC2-Probe-')
    if packaged!=branded:packaged.replace(branded)
    print(branded)
