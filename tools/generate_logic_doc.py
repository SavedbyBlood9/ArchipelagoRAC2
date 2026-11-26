"""Write LOGIC.md, the randomizer requirements in tables (the RAC1 item randomizer's layout), from the
APWorld's own rules.

Each check's rule (apworld/rac2_openrac/Logic.py, named in data/Locations.py) is evaluated against
a stand-in inventory at each First Person Mode Glitch In Logic level, and written as the smallest
sets of items that pass it. Nothing is typed by hand, so the file follows the code: rerun this
after changing the logic, and tools/test_world.py fails while LOGIC.md is out of date.

    python tools/generate_logic_doc.py --archipelago C:/path/to/Archipelago [--check]
"""
import argparse
import importlib
import itertools
import random
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'LOGIC.md'
LEVELS = ('No Glitches', 'Easy', 'Medium', 'Hard')
JUMP = '(Heli-Pack *or* Thruster-Pack)'
DASH = '\u2014'
PARTS = 'Hypnomatic Part'


def load_world(archipelago: Path):
    """The APWorld's data and logic modules, without loading Archipelago's worlds."""
    sys.path.insert(0, str(archipelago.resolve()))
    package = types.ModuleType('rac2_openrac')
    package.__path__ = [str(ROOT / 'apworld/rac2_openrac')]
    sys.modules['rac2_openrac'] = package
    return (importlib.import_module('rac2_openrac.data.Items'),
            importlib.import_module('rac2_openrac.data.Planets'))


class Options:
    def __init__(self, level: int):
        self.first_person_mode_glitch_in_logic = level
        self.randomize_megacorp_vendor = 1  # the Spiderbot Glove is an item of its own
        self.randomize_gadgetron_vendor = 1


class State:
    """Just enough of CollectionState for the rules: an inventory of names (3x Hypnomatic Part for
    all three parts)."""
    def __init__(self, items, level):
        self.items = set(items)
        world = types.SimpleNamespace(options=Options(level))
        self.multiworld = types.SimpleNamespace(worlds={1: world})

    def has(self, name, player, count=1):
        return (name if count == 1 else f'{count}\u00d7 {name}') in self.items

    def has_any(self, names, player):
        return any(n in self.items for n in names)

    def has_all(self, names, player):
        return all(n in self.items for n in names)


def minimal_sets(rule, level, pool):
    """Every smallest set of names from pool that passes rule ([frozenset()]: nothing needed)."""
    passes = lambda items: rule(State(items, level), 1)
    if rule is None or passes(()):
        return [frozenset()]
    if not passes(pool):
        return None
    # The names that matter: shrink the whole pool in many orders, keep what each order needs.
    relevant = set()
    orders = [sorted(pool), sorted(pool, reverse=True)]
    rng = random.Random(0)
    for _ in range(60):
        order = sorted(pool)
        rng.shuffle(order)
        orders.append(order)
    for order in orders:
        need = set(pool)
        for name in order:
            if passes(need - {name}):
                need.discard(name)
        relevant |= need
    # Then every subset of those, smallest first, keeping each one no smaller passing set is in.
    found = []
    names = sorted(relevant)
    for size in range(len(names) + 1):
        for combo in itertools.combinations(names, size):
            combo = frozenset(combo)
            if not any(f <= combo for f in found) and passes(combo):
                found.append(combo)
    return found


def describe(sets):
    """Items all the sets share, then the ways they differ: A, B + (C *or* D)."""
    if sets is None:
        return 'not in logic'
    if sets == [frozenset()]:
        return DASH
    common = frozenset.intersection(*sets)
    rest = [sorted(s - common) for s in sets]
    text = ', '.join(sorted(common))
    if len(sets) > 1:
        options = ' *or* '.join(r[0] if len(r) == 1 else '(' + ', '.join(r) + ')' for r in rest)
        text = (text + ' + ' if text else '') + '(' + options + ')'
    return text


def extra(level_sets, always_sets):
    """What a level needs on top of Always, or its whole rule where it is not simply more items."""
    if level_sets == always_sets:
        return DASH
    if always_sets == [frozenset()]:
        return describe(level_sets)
    if level_sets and always_sets:
        if len(always_sets) == 1 and always_sets[0] <= frozenset.intersection(*level_sets):
            return describe([s - always_sets[0] for s in level_sets])
        # Each of Always's ways with the same items added (Always: A + Jump, here: A, B + Jump).
        if len(level_sets) == len(always_sets):
            added = {s - a for s in level_sets for a in always_sets if a <= s}
            if (len(added) == 1 and all(any(a <= s for a in always_sets) for s in level_sets)
                    and sorted(a | next(iter(added)) for a in always_sets) == sorted(level_sets)):
                return ', '.join(sorted(next(iter(added))))
    return 'only: ' + describe(level_sets)


def tidy(text):
    return text.replace(JUMP, '*Jump*').replace(f'3\u00d7 {PARTS}', f'all 3 {PARTS}s')


def render(Items, Planets):
    pool = {v.name for v in vars(Items).values()
            if hasattr(v, 'item_id') and isinstance(getattr(v, 'name', None), str)}
    pool.add(f'3\u00d7 {PARTS}')
    planet_rules = {
        'Tabora': 'Reaching Tabora also needs Heli-Pack and Swingshot, on top of its coordinates.',
        'Aranos Prison': 'Reaching Aranos Prison also needs Gravity Boots, Levitator and Infiltrator, '
                         'on top of its coordinates.',
    }
    starts = ', '.join(c.name.removesuffix(' Coordinates').removesuffix(' Coords')
                       for c in Items.STARTABLE_COORDS)
    lines = [
        '# RAC2 randomizer requirements',
        '',
        '<!-- Generated by tools/generate_logic_doc.py from apworld/rac2_openrac: do not edit by hand. -->',
        '',
        "Encoded logic for ArchipelagoRAC2: APRac2's access rules, with two changes. Snivelak: "
        "Rescue Angela takes the glitch from Easy up, as its neighbours do; Maktar: Jamming Array - "
        "Platinum Bolt also needs Jump (Heli-Pack or Thruster-Pack) with No Glitches. These are "
        "the generator's rules, not a guarantee that every physical obstacle has been modeled.",
        '',
        '## How to read the list',
        '',
        'Every location also requires access to its planet. Each planet opens with its coordinates; '
        'Tabora also needs Heli-Pack and Swingshot, and Aranos Prison also needs Gravity Boots, '
        f'Levitator and Infiltrator. A seed starts with at least 3 coordinates from {starts} (any in '
        'the starting inventory count) and 2 weapons by the Starting Weapons option.',
        '',
        'The First Person Mode Glitch In Logic option (No Glitches, Easy, Medium, Hard; No Glitches is '
        "the option's `disabled`, the default) lets the "
        'first-person movement glitch stand in for items. "Always" applies at every level, Hard '
        'included. "No Glitches", "Easy" and "Medium" are what that level needs on top of "Always"; '
        "\"only:\" gives a level's whole rule where it is narrower than \"Always\" in another way. All listed items "
        'are required unless a rule says "or". A dash means no additional encoded item requirement.',
        '',
        '*Jump* means one of Heli-Pack or Thruster-Pack.',
        '',
        'Goal: Yeedil: Defeat Mutated Protopet, which holds the Victory event. With Randomize '
        'Megacorp Vendor off, the logic takes the Joba coordinates in place of the Spiderbot Glove. '
        'Extra Spaceship Challenge Locations adds the rows marked "Extra spaceship challenge".',
        '',
    ]
    for planet in Planets.LOGIC_PLANETS:
        if not planet.locations:
            continue
        lines += [f'## {planet.name}', '']
        if planet.name in planet_rules:
            lines += [planet_rules[planet.name], '']
        lines += ['| Location | Always | No Glitches | Easy | Medium | Other rules |',
                  '|---|---|---|---|---|---|']
        for loc in planet.locations:
            sets = [minimal_sets(loc.access_rule, level, pool) for level in range(len(LEVELS))]
            always = sets[3]
            cells = [describe(always)] + [extra(sets[level], always) for level in range(3)]
            other = []
            if loc.enable_if is not None:
                other.append('Extra spaceship challenge')
            if loc.is_vendor:
                other.append('Vendor slot')
            if loc.name == 'Yeedil: Defeat Mutated Protopet':
                other.append('Goal (Victory)')
            cells.append('; '.join(other) or DASH)
            lines.append(f'| {loc.name} | ' + ' | '.join(tidy(c) for c in cells) + ' |')
        lines.append('')
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--archipelago', required=True, type=Path)
    p.add_argument('--check', action='store_true', help='fail if LOGIC.md is out of date, write nothing')
    a = p.parse_args()
    text = render(*load_world(a.archipelago))
    if a.check:
        current = OUT.read_text(encoding='utf-8') if OUT.is_file() else ''
        if current != text:
            print('LOGIC.md is out of date: run tools/generate_logic_doc.py', file=sys.stderr)
            return 1
        print('LOGIC.md matches the logic')
        return 0
    OUT.write_text(text, encoding='utf-8', newline='\n')
    print(f'wrote {OUT.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
