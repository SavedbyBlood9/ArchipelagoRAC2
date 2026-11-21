"""Export source facts and XP rules for the native adapter; never reads a game image."""
import argparse
import ast
import importlib.util
import json
import sys
import types
from pathlib import Path

def generate(source, root):
    package=types.ModuleType('_aprac2_data'); package.__path__=[str(source/'data')]
    sys.modules[package.__name__]=package
    modules={}
    for name in ('Items','ExperienceTables'):
        spec=importlib.util.spec_from_file_location(package.__name__+'.'+name,source/'data'/f'{name}.py')
        module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)
        modules[name]=module
    items=modules['Items']; xp=modules['ExperienceTables']
    data=json.loads((root/'data/aprac2-contract.json').read_text())
    for row in data['items']:
        item=getattr(items,row['symbol'])
        for field in ('base_weapon_offset','max_ammo','max_capacity','oclass_id','icon_id'):
            if hasattr(item,field): row[field]=getattr(item,field)
    planets={}
    for node in ast.parse((source/'data/Planets.py').read_text()).body:
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='PlanetData':
            planets[node.targets[0].id]=ast.literal_eval(node.value.args[1])
    addresses={}; level_data={}
    for node in ast.walk(ast.parse((source/'data/RamAddresses.py').read_text())):
        target=node.target if isinstance(node,ast.AnnAssign) else node.targets[0] if isinstance(node,ast.Assign) and len(node.targets)==1 else None
        if not isinstance(target,ast.Attribute) or not isinstance(target.value,ast.Name) or target.value.id!='self': continue
        if target.attr=='planet' and isinstance(node.value,ast.Dict):
            for key,value in zip(node.value.keys,node.value.values):
                number=planets[key.value.id] if isinstance(key,ast.Attribute) else ast.literal_eval(key)
                fields={}
                for keyword in value.keywords:
                    try: fields[keyword.arg]=ast.literal_eval(keyword.value)
                    except (ValueError,TypeError): pass
                level_data[number]=fields
        else:
            try: value=ast.literal_eval(node.value)
            except (ValueError,TypeError): continue
            if isinstance(value,(int,list)): addresses[target.attr]=value
    data.update(addresses=addresses,levels=level_data,nanotech_xp=xp.get_nanotech_xp_table(1.0),
                weapon_xp={str(int(extended)):xp.get_weapon_upgrades_table(1.0,extended) for extended in (False,True)})
    item_map={r['symbol']:r for r in data['items']}
    direct=[]
    def evaluate(node):
        if isinstance(node,ast.Constant): return node.value
        if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add): return evaluate(node.left)+evaluate(node.right)
        if isinstance(node,ast.Attribute) and isinstance(node.value,ast.Name) and node.value.id=='ram': return addresses[node.attr]
        if isinstance(node,ast.Attribute) and node.attr=='offset': return item_map[node.value.attr]['game_value']
        raise ValueError(ast.unparse(node))
    for row in data['locations']:
        if not row.get('flag'): continue
        try: address=evaluate(ast.parse(row['flag'],mode='eval').body.body)
        except (ValueError,KeyError): continue
        direct.append(dict(location=row['id'],address=address,vendor=row['vendor']))
    data['direct_checks']=direct
    loc_planets={}
    for node in ast.parse((source/'data/Planets.py').read_text()).body:
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and getattr(node.value.func,'id',None)=='PlanetData' and len(node.value.args)>2 and isinstance(node.value.args[2],ast.List):
            number=ast.literal_eval(node.value.args[1])
            for symbol in node.value.args[2].elts:
                if isinstance(symbol,ast.Name):loc_planets[symbol.id]=number
    data['vendors']={}
    for label,weapons,first,last in [('megacorp',items.MEGACORP_VENDOR_WEAPONS,300,313),('gadgetron',items.GADGETRON_VENDOR_WEAPONS,314,319)]:
        locations=sorted([r for r in data['locations'] if r['vendor'] and first<=r['id']<=last],key=lambda r:r['id'])
        data['vendors'][label]=[dict(location=r['id'],item=w.offset,planet=loc_planets[r['symbol']],model=w.oclass_id)
                                for r,w in zip(locations,weapons)]
    data['extended_pairs']={str(key):[base.offset,upgraded.offset] for key,(base,upgraded) in xp._EXTENDED_UPGRADES.items()}
    text=json.dumps(data,separators=(',',':'),ensure_ascii=True)
    (root/'src/native_data.hpp').write_text('// Generated source facts by tools/generate_native_data.py. No disc bytes.\n#pragma once\ninline constexpr const char* kNativeData = R"APDATA('+text+')APDATA";\n',encoding='utf-8',newline='\n')
    print(len(data['items']),'items;',len(direct),'direct checks;',len(level_data),'level layouts')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('source',type=Path)
    args=parser.parse_args(); generate(args.source,Path(__file__).resolve().parents[1])
