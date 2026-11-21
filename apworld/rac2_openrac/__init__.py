"""APRac2's world generation for OpenRAC; no PCSX2 or ISO patching dependency.

ItemPool, Logic, Regions, options and data are from evilwb/APRac2 (MIT).
Install this APWorld instead of the original: both register the same game.
"""
import json
from pathlib import Path
from BaseClasses import Item, ItemClassification
from worlds.AutoWorld import World, WebWorld
from . import ItemPool
from .data import Items, Locations, Planets
from .Regions import create_regions
from .Rac2Options import Rac2Options
from .native import OPTION_KEYS, build_slot_data


class Rac2Item(Item):
    game = 'Ratchet & Clank 2'


class Rac2World(World):
    """APRac2 multiworld generation for the OpenRAC native port of Going Commando."""
    game = 'Ratchet & Clank 2'
    web = WebWorld()
    options_dataclass = Rac2Options
    options: Rac2Options
    topology_present = True
    required_client_version = (0, 6, 9)
    item_name_to_id = {item.name: item.item_id for item in Items.ALL}
    location_name_to_id = {loc.name: loc.location_id for loc in Planets.ALL_LOCATIONS if loc.location_id}
    item_name_groups = Items.get_item_groups()
    location_name_groups = Planets.get_location_groups()

    def __init__(self, multiworld, player):
        super().__init__(multiworld, player)
        self.starting_weapons = []
        self.prefilled_item_map = {}

    def get_filler_item_name(self):
        return Items.BOLT_PACK.name

    def create_regions(self):
        create_regions(self)

    def create_item(self, name, override=None):
        classification = override if override is not None else ItemPool.get_classification(Items.from_name(name))
        return Rac2Item(name, classification, self.item_name_to_id[name], self.player)

    def create_event(self, name):
        return Rac2Item(name, ItemClassification.progression, None, self.player)

    def pre_fill(self):
        for location_name, item_name in self.prefilled_item_map.items():
            self.get_location(location_name).place_locked_item(self.create_item(item_name, ItemClassification.progression))

    def create_items(self):
        items = (ItemPool.create_planets(self) + ItemPool.create_equipment(self)
                 + ItemPool.create_collectables(self) + ItemPool.create_upgrades(self))
        unfilled = [loc for loc in self.multiworld.get_unfilled_locations(self.player) if not loc.is_event]
        remaining = len(unfilled) - len(items)
        if remaining < 0:
            raise ValueError('APRac2 item pool exceeds available locations')
        items += [self.create_item(Items.BOLT_PACK.name) for _ in range(remaining)]
        self.multiworld.itempool += items

    def set_rules(self):
        self.get_location(Locations.YEEDIL_DEFEAT_MUTATED_PROTOPET.name).place_locked_item(self.create_event('Victory'))
        self.multiworld.completion_condition[self.player] = lambda state: state.has('Victory', self.player)

    def get_options_as_dict(self):
        return self.options.as_dict(*OPTION_KEYS)

    def fill_slot_data(self):
        return build_slot_data(self)

    def generate_output(self, output_directory):
        # This informational file contains no ROM data or server password. The authoritative
        # settings still arrive through Connected.slot_data; the client does not trust this file.
        path = Path(output_directory) / (self.multiworld.get_out_file_name_base(self.player) + '.aprac2openrac.json')
        path.write_text(json.dumps(self.fill_slot_data(), indent=2) + '\n', encoding='utf-8')
