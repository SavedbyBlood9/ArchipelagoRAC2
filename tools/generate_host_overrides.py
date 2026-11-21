"""Prepare opt-in native C changes in hostgen's build copies, never in the decompilation."""
from pathlib import Path
import argparse,json,re,sys
p=argparse.ArgumentParser(description=__doc__);p.add_argument('checkout',type=Path);a=p.parse_args()
project=Path(__file__).resolve().parents[1]
root=a.checkout.resolve()
sys.path.insert(0,str(root/'port/tools/hostgen'))
import prep
source=root/'games/rac2/decomp'
facts=json.loads((project/'data/native-host-symbols.json').read_text())
names={}
for header in (source/'include/names').glob('*.h'):
 for readable,symbol in re.findall(r'^#define\s+(\w+)\s+(func_\w+)\s*$',header.read_text(),re.M):names[symbol]=readable
paths=[p for p in (source/'src').rglob('*.c') if '/pal/' not in p.as_posix() and '/us2/' not in p.as_posix()]
out=project/'host-patch/overrides'
out.mkdir(parents=True,exist_ok=True)
magic='(D_001A7B30[33]==169 && D_001A7B30[34]==82 && D_001A7B30[35]==50 && (D_001A7B30[40]&1))'
free='('+magic+' && (D_001A7B30[40]&2))'
revisit='('+magic+' && (D_001A7B30[40]&4))'
table=[]
def find(symbol):
 name=names.get(symbol,symbol)
 for path in paths:
  text=path.read_text(errors='replace');span=prep._definition(text,name)
  if span:return path,text[span[0]:span[1]],name
 raise ValueError('No C definition for '+symbol+' / '+name)
def arrays(body,all_reads):
 needle='g_game_flag_table[';at=0;edits=[]
 while (start:=body.find(needle,at))>=0:
  pos=start+len(needle);depth=1
  while depth:
   if body[pos]=='[':depth+=1
   if body[pos]==']':depth-=1
   pos+=1
  expr=body[start:pos]
  if 'arena_get_challenge_' in expr and (all_reads or '[i]' in expr):edits.append((start,pos,'('+free+' || '+expr+')'))
  at=pos
 for a,b,text in reversed(edits):body=body[:a]+text+body[b:]
 return body,len(edits)
keys=['RESET_MOBY_FUNCS','SPECIAL_MENU_FUNCS','SHORTCUT_MENU_FUNCS','MAKTAR_ARENA_MENU_FUNC','JOBA_ARENA_MENU_FUNC',
 'MAKTAR_ARENA_DISPLAY_PREV_FUNC','MAKTAR_ARENA_DISPLAY_NEXT_FUNC','JOBA_ARENA_DISPLAY_PREV_FUNC','JOBA_ARENA_DISPLAY_NEXT_FUNC',
 'SPACESHIP_MENU_FUNCS','START_SPACESHIP_CHALLENGE_FUNCS','HOVERBIKE_MENU_FUNCS','START_HOVERBIKE_CHALLENGE_FUNCS',
 'OOZLA_CONTROLLER_FUNC','MAKTAR_CONTROLLER_FUNC','BARLOW_SPAWN_CONTROLLER_FUNC','JOBA_CONTROLLER_FUNC','TABORA_CONTROLLER_FUNC','DAMOSEL_CONTROLLER_FUNC','SWAMP_MONSTER_GATE_FUNC']
for key in keys:
 symbol=facts[key][0]['symbol'];path,body,name=find(symbol);before=body;count=0
 if key in ['OOZLA_CONTROLLER_FUNC','MAKTAR_CONTROLLER_FUNC','BARLOW_SPAWN_CONTROLLER_FUNC','JOBA_CONTROLLER_FUNC','TABORA_CONTROLLER_FUNC','DAMOSEL_CONTROLLER_FUNC']:
  predicates={
   'OOZLA_CONTROLLER_FUNC':'g_item_owned_flags[0x2e] && !g_game_flag_table.flag9b && hints->cameraIndex != -1',
   'MAKTAR_CONTROLLER_FUNC':'g_frame_l02_counter<3 && g_item_owned_flags[0x26]',
   'BARLOW_SPAWN_CONTROLLER_FUNC':'g_inventory_have_flags[0x1F] != 0 && g_game_flag_table[0x12] == 0 && g_game_tick_counter[0] < 5',
   'JOBA_CONTROLLER_FUNC':'g_focus_lock_flag',
   'TABORA_CONTROLLER_FUNC':'g_item_owned_flags[0x15] && *(int *)(vars+0x20)!=-1',
   'DAMOSEL_CONTROLLER_FUNC':'TRIGGER(0xB4) && !TRIGGER(0xB8)',
  }
  old='if ('+predicates[key] if key not in ['MAKTAR_CONTROLLER_FUNC'] else 'if('+predicates[key]
  assert body.count(old)==(2 if key=='DAMOSEL_CONTROLLER_FUNC' else 1),(key,body.count(old))
  body=body.replace(old,old.split('(')[0]+'(!'+magic+' && '+old[old.index('(')+1:],1);count=1
 elif key=='SWAMP_MONSTER_GATE_FUNC':
  old='g_hero_override_flag[0]';assert body.count(old)==1
  body=body.replace(old,'('+magic+' ? D_001A7B30[50] : '+old+')');count=1
 elif key=='RESET_MOBY_FUNCS':
  body,n=re.subn(r'bolts2\s*=\s*\*\(int\s*\*\)p;',f'bolts2 = {revisit} ? bolts : *(int *)p;',body);count+=n
  body,n=re.subn(r'xp2\s*=\s*\*\(int\s*\*\)p;',f'xp2 = {revisit} ? xp : *(int *)p;',body);count+=n
  assert count==2,(key,count)
 elif key=='SHORTCUT_MENU_FUNCS':
  at=body.index('{')+1
  body=body[:at]+f'\n    if ({magic}) {{ data_set_small_value_and_refresh(24, 1); return 0; }}\n'+body[at:]
  count=1
 elif key=='SPECIAL_MENU_FUNCS':
  needle='tab_menu_set_tables('
  index=body.index(needle)
  body=body[:index]+f'''if ({magic}) {{
            Menu *ap_menu = &g_extras_tab_table_c;
            ap_menu->entries[0].text_id = 0x3202;
            ap_menu->entries[0].data = g_extras_unlock_entry_a;
            ap_menu->entries[1].text_id = 0x320C;
            ap_menu->entries[1].data = g_extras_unlock_entry_b;
        }}
        '''+body[index:];count=1
 elif 'ARENA' in key:
  body,count=arrays(body,'MENU_FUNC' in key)
 elif key=='START_SPACESHIP_CHALLENGE_FUNCS':
  body,n=re.subn(r'if\s*\(\s*!\s*(g_feltzin_challenge_data|D_L05_001B1350_4\[[12]\])\s*\)',lambda m:'if (!'+free+' && !'+m[1]+')',body);count+=n
 elif key=='SPACESHIP_MENU_FUNCS':
  # The three prior-win booleans only affect lock labels in this native panel.
  body,n=re.subn(r'\b(D_L05_001B1350_gp\[0\]|g_feltzin_challenge_data\[[12]\])',lambda m:'('+free+' || '+m[1]+')',body);count+=n
 else:
  body,n=re.subn(r'(g_race_challenge_table\[[^\]]+\]\.flags\s*&\s*0x10000000)',lambda m:'('+free+' || ('+m[1]+'))',body);count+=n
  # Selection reads the flag through a short pointer into the same challenge record.
  if not count:
   body,n=re.subn(r'(\([^\n;]+?&\s*0x10000000\))',lambda m:'('+free+' || '+m[1]+')',body);count+=n
 if not count:raise ValueError('No verified source rewrite for '+key+' '+name)
 first=body.index('{')+1
 body=body[:first]+'\n    extern unsigned char D_001A7B30[];\n'+body[first:]
 notice=f'/* SPDX-License-Identifier: GPL-3.0-only\n * Derived from OpenRAC/rac2-decomp {path.relative_to(source).as_posix()}\n * Copyright (c) the OpenRAC contributors. APRac2 changes gated by native mod control bytes.\n * Replaces only the native build copy; the matching decompilation is untouched. */\n'
 (out/(symbol+'.c')).write_text(notice+body+'\n',encoding='utf-8',newline='\n')
 table.append(symbol+'\t'+symbol+'.c')
 print(key,symbol,count)
(out/'overrides.tsv').write_text('# Native-only, opt-in APRac2 behavior; GPL-3.0-only.\n'+'\n'.join(table)+'\n')
