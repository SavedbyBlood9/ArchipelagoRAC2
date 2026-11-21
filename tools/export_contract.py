"""Extract APRac2's wire IDs without importing Archipelago or executing upstream code."""
import argparse
import ast
import hashlib
import json
from pathlib import Path


def assignments(tree):
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            yield node.targets[0].id, node.value


def extract(source):
    paths = ['data/Items.py', 'data/Locations.py', 'data/Planets.py', 'ClientCheckLocations.py']
    trees = {p: ast.parse((source / p).read_text(encoding='utf-8')) for p in paths}
    items = []
    for symbol, node in assignments(trees['data/Items.py']):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {
            'EquipmentData', 'WeaponData', 'CoordData', 'CollectableData', 'ProgressiveUpgradeData'
        }:
            row = dict(symbol=symbol, id=ast.literal_eval(node.args[0]),
                       name=ast.literal_eval(node.args[1]), kind=node.func.id)
            if node.func.id in {'EquipmentData', 'WeaponData', 'CoordData'}:
                row['game_value'] = ast.literal_eval(node.args[2])
            items.append(row)
    locations = []
    for symbol, node in assignments(trees['data/Locations.py']):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'LocationData':
            wire_id = ast.literal_eval(node.args[0])
            if wire_id is None:
                continue  # Victory is a logic event, not an AP location check.
            kw = {k.arg: k.value for k in node.keywords}
            locations.append(dict(symbol=symbol, id=wire_id, name=ast.literal_eval(node.args[1]),
                                  vendor=ast.literal_eval(kw['is_vendor']) if 'is_vendor' in kw else False,
                                  enabled_when=ast.unparse(kw['enable_if']) if 'enable_if' in kw else None,
                                  flag=ast.unparse(kw['checked_flag_address']) if 'checked_flag_address' in kw else None))
    planets = {symbol: ast.literal_eval(node.args[1])
               for symbol, node in assignments(trees['data/Planets.py'])
               if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'PlanetData'}
    item_by_symbol = {r['symbol']: r for r in items}
    loc_by_symbol = {r['symbol']: r for r in locations}

    def value(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mult)):
            a, b = value(node.left), value(node.right)
            return a + b if isinstance(node.op, ast.Add) else a * b
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute):
            namespace = node.value.value
            if isinstance(namespace, ast.Name):
                symbol, attr = node.value.attr, node.attr
                if namespace.id == 'Planets' and attr == 'number':
                    return planets[symbol]
                if namespace.id == 'Items' and attr == 'offset':
                    return item_by_symbol[symbol]['game_value']
                if namespace.id == 'Locations' and attr == 'location_id':
                    return loc_by_symbol[symbol]['id']
        raise ValueError(f'Unsupported mapping expression: {ast.unparse(node)}')

    maps = {}
    for node in trees['ClientCheckLocations.py'].body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and isinstance(node.value, ast.Dict):
            maps[node.target.id] = [{'game_value': value(k), 'location_id': value(v)}
                                    for k, v in zip(node.value.keys, node.value.values)]
    for rows in (items, locations):
        for field in ('id', 'name', 'symbol'):
            vals = [r[field] for r in rows]
            if len(set(vals)) != len(vals):
                raise ValueError(f'Duplicate {field}')
    return dict(format=1, game='Ratchet & Clank 2', target=dict(game='rac2', version='ntsc'),
                source_sha256={p: hashlib.sha256((source / p).read_bytes()).hexdigest() for p in paths},
                items=items, locations=locations, check_maps=maps)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'data/aprac2-contract.json')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text = json.dumps(extract(args.source), indent=2, ensure_ascii=False) + '\n'
    if args.check:
        if args.output.read_text(encoding='utf-8') != text:
            raise SystemExit('Contract differs from the pinned upstream source')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8', newline='\n')
    print('APRac2 contract verified' if args.check else 'APRac2 contract exported')


if __name__ == '__main__':
    main()
