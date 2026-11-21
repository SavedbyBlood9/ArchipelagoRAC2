"""Package the native world without bytecode, tests, ROMs or an ISO patcher."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
root = Path(__file__).resolve().parents[1]
source = root / 'apworld/rac2_openrac'
out = root / 'dist/ArchipelagoRAC2.apworld'
out.parent.mkdir(parents=True, exist_ok=True)
(source / 'CREDITS.md').write_text((root / 'CREDITS.md').read_text(), encoding='utf-8')
with ZipFile(out, 'w', ZIP_DEFLATED) as archive:
    for path in sorted(source.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            archive.write(path, Path('rac2_openrac') / path.relative_to(source))
print(out)
