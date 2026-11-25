"""Package with the public SDK and preserve the original APRac2 MIT notice verbatim."""
import argparse
import importlib.util
from pathlib import Path
import shutil
from zipfile import ZipFile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--sdk',type=Path,required=True)
p.add_argument('--input',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
spec=importlib.util.spec_from_file_location('openrac_package_mod',a.sdk/'tools/package_mod.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
project=Path(__file__).resolve().parents[1]
shutil.copyfile(project/'CREDITS.md',a.input/'README-CREDITS.md')
shutil.copyfile(project/'development/README.md',a.input/'README.md')
upstream=project/'third_party/APRac2-LICENSE.md'
shutil.copyfile(upstream,a.input/'LICENSE.APRac2')
packaged=module.package(a.input,a.output)
with ZipFile(packaged) as archive:
    if archive.read('LICENSE.APRac2')!=upstream.read_bytes():
        raise RuntimeError('Packaged APRac2 license differs from the original notice')
branded=a.output/packaged.name.replace('aprac2-openrac-dev-','ArchipelagoRAC2-').replace('aprac2-openrac-probe-','ArchipelagoRAC2-Probe-')
if packaged!=branded:packaged.replace(branded)
print(branded)
