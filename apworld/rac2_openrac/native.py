"""Versioned native seed contract shared by the generator and sidecar client."""
FORMAT = 1
GAME = 'Ratchet & Clank 2'
OPTION_KEYS = (
    'death_link', 'starting_weapons', 'randomize_megacorp_vendor',
    'randomize_gadgetron_vendor', 'exclude_very_expensive_items', 'skip_wupash_nebula',
    'enable_bolt_multiplier', 'no_revisit_reward_change', 'no_kill_reward_degradation',
    'free_challenge_selection', 'nanotech_xp_multiplier', 'weapon_xp_multiplier',
    'extra_spaceship_challenge_locations', 'extend_weapon_progression',
    'first_person_mode_glitch_in_logic',
)
DEFAULTS = dict.fromkeys(OPTION_KEYS, 0)
DEFAULTS.update(exclude_very_expensive_items=1, skip_wupash_nebula=1,
                nanotech_xp_multiplier=100, weapon_xp_multiplier=100)
RANGES = dict.fromkeys(OPTION_KEYS, (0, 1))
RANGES.update(starting_weapons=(0, 3), first_person_mode_glitch_in_logic=(0, 3),
              nanotech_xp_multiplier=(20, 600), weapon_xp_multiplier=(30, 600))


def validate_options(options):
    result = {}
    for key in OPTION_KEYS:
        value = options.get(key, DEFAULTS[key])
        if isinstance(value, bool):
            value = int(value)
        lo, hi = RANGES[key]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f'{key} must be an integer from {lo} to {hi}')
        result[key] = value
    return result


# The discs the native mod plays: USA v1.01, Locked & Loaded PAL and USA v2.00. A seed lists the
# ones it was made for; seeds from before v2.00 list only the first two and stay valid.
DISCS = ('ntsc', 'pal', 'ntsc2')


def build_slot_data(world):
    from .data import Planets
    options = validate_options(world.get_options_as_dict())
    active = sorted(loc.location_id for loc in Planets.get_all_active_locations(options))
    starting = sorted(item.code for item in world.multiworld.precollected_items[world.player]
                      if item.code is not None)
    return dict(options, openrac=dict(
        format=FORMAT, game=GAME, target='rac2', supported_discs=list(DISCS),
        seed=str(world.multiworld.seed_name), player=world.player,
        starting_items=starting,
        starting_weapon_ids=[item.item_id for item in world.starting_weapons],
        active_locations=active,
    ))


def validate_slot_data(data):
    if not isinstance(data, dict) or not isinstance(data.get('openrac'), dict):
        raise ValueError('This seed is from the PS2 APWorld; regenerate with ArchipelagoRAC2.apworld')
    native = data['openrac']
    if native.get('format') != FORMAT or native.get('game') != GAME or native.get('target') not in ('rac2',*(f'rac2/{d}' for d in DISCS)):
        raise ValueError('Unsupported APRac2 OpenRAC seed format or game target')
    discs=native.get('supported_discs')
    if discs is not None and (not isinstance(discs,list) or not discs or
                              any(d not in DISCS for d in discs) or len(set(discs))!=len(discs)):
        raise ValueError('Unsupported disc list in native slot data')
    if not isinstance(native.get('seed'), str) or not native['seed']:
        raise ValueError('Missing seed identity')
    if type(native.get('player')) is not int or native['player'] <= 0:
        raise ValueError('Invalid player identity')
    for key in ('starting_items', 'starting_weapon_ids', 'active_locations'):
        if not isinstance(native.get(key), list) or any(type(x) is not int or x <= 0 for x in native[key]):
            raise ValueError(f'Invalid {key}')
    if len(set(native['active_locations'])) != len(native['active_locations']):
        raise ValueError('Duplicate active locations')
    if len(native['starting_weapon_ids']) != 2:
        raise ValueError('Expected two starting weapons')
    options = validate_options(data)
    return dict(options, openrac=dict(native))
