"""Apply APRac2's NTSC native changes to an isolated OpenRAC checkout; never alters a disc or decompilation."""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

def append(target,rows,columns=1):
    text=target.read_text()
    old={tuple(r.split('\t')[:columns]):r for r in text.splitlines() if r and not r.startswith('#')}
    for row in rows:
        if not row or row.startswith('#'):continue
        key=tuple(row.split('\t')[:columns])
        if key in old and old[key]!=row:raise ValueError(f'Conflicting entry {key} in {target}')
        if key not in old:text+=row+'\n';old[key]=row
    target.write_text(text,encoding='utf-8',newline='\n')

def replace(target,old,new):
    text=target.read_text()
    if new not in text:
        if text.count(old)!=1:raise ValueError('Upstream source changed: '+str(target))
        text=text.replace(old,new)
    target.write_text(text,encoding='utf-8',newline='\n')

def apply(root,pal=False):
    patch=Path(__file__).resolve().parents[1]/'host-patch'
    if not(root/'port/game/rac2-ntsc/hostgen.json').is_file():raise ValueError('Not an OpenRAC checkout')
    # Generated game-function bodies stay local; publication carries only the generator.
    rows=(patch/'overrides/overrides.tsv').read_text().splitlines()
    missing=any(not(patch/'overrides'/row.split('\t')[1]).is_file() for row in rows if row and not row.startswith('#'))
    if missing:
        subprocess.run([sys.executable,str(patch.parent/'tools/generate_host_overrides.py'),str(root)],check=True)
    shutil.copyfile(patch/'host/mod_pages_headless.cpp',root/'port/game/common/program/mod_pages_headless.cpp')
    target=root/'port/game/rac2-ntsc/libraries.tsv';text=target.read_text()
    for row in (patch/'hooks.tsv').read_text().splitlines():
        symbol=row.split('\t')[0]
        existing=[r for r in text.splitlines() if r.startswith(symbol+'\t') and '\thook\t' in r]
        if existing and row not in existing:raise ValueError('Hook already bound differently: '+symbol)
        if not existing:text+=row+'\n'
    target.write_text(text,encoding='utf-8',newline='\n')
    parity=root/'port/game/rac2/parity.tsv'
    pal=pal or '\tAPRac2_CountKill\thook\t' in (root/'port/game/rac2-pal/libraries.tsv').read_text()
    parity_rows=(patch/'parity.tsv').read_text().splitlines()
    if pal:
        # The PAL layer removes the former PAL-only difference and leaves only USA v2.00
        # without the new save hook. Replace only the rows owned by this adapter.
        owned=('func_0029ADA0\tboot\t','func_002B0DB8\tboot\t')
        lines=[line for line in parity.read_text().splitlines()
               if not(line.startswith(owned) and 'APRac2' in line)]
        parity.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
        parity_rows=[line for line in parity_rows if not line.startswith(owned)]
        parity_rows.append('func_0029ADA0\tboot\trac2-ntsc2\tAPRac2 save serialization hooks are installed for USA v1.01 and PAL; USA v2.00 remains unsupported.')
    append(parity,parity_rows,2)
    dest=root/'port/game/rac2-ntsc/hand/aprac2';dest.mkdir(exist_ok=True)
    rows=[]
    for row in (patch/'overrides/overrides.tsv').read_text().splitlines():
        if not row or row.startswith('#'):continue
        symbol,name=row.split('\t');shutil.copyfile(patch/'overrides'/name,dest/name)
        rows.append(symbol+'\taprac2/'+name)
    append(root/'port/game/rac2-ntsc/hand/overrides.tsv',rows)
    old='  foreach(config IN LISTS configs)\n'
    replace(root/'port/cmake/Games.cmake',old,old+'    if(OPENRAC_ONLY_GAME AND NOT config MATCHES "/${OPENRAC_ONLY_GAME}/hostgen.json$")\n      continue()\n    endif()\n')
    old='    frontend::debug_overlay::set_picker_report_folder(g_options.data.string());'
    replace(root/'port/game/common/main.cpp',old,'#ifdef OPENRAC_FRONTEND\n'+old+'\n#endif')
    old='    const int errors = func_0029B168__game(save, slot, blocks);'
    options=root/'port/game/rac2/host/options.c'
    portable='    GREF(uint8_t, RAC2_g_inventoryNewFlag + 33) = 0;'
    text=options.read_text().replace('    GREF(uint8_t, 0x001A7B51u) = 0;',portable)
    options.write_text(text,encoding='utf-8',newline='\n')
    replace(options,old,old+'\n    /* Only the live APRac2 mod may activate the native option overrides. */\n'+portable)
    # Generated cast-record prefixes otherwise backtrack exponentially when an override
    # name occurs only as a declaration/call in a unit with many records on one line.
    old="_CAST_RECORDS_AHEAD = r'(?:(?:struct|union) openrac_cast_\\d+_\\d+ \\{.*?\\}; )*'"
    new="_CAST_RECORDS_AHEAD = r'(?>(?:(?:struct|union) openrac_cast_\\d+_\\d+ \\{.*?\\}; )*)'"
    replace(root/'port/tools/hostgen/prep.py',old,new)
    print('APRac2 native hooks and opt-in option overrides applied to',root)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('checkout',type=Path);a=p.parse_args();apply(a.checkout.resolve())
