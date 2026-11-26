"""Exercise the native world against an official Archipelago checkout, including restrictive fill."""
import argparse
import importlib.util
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--archipelago',required=True,type=Path)
parser.add_argument('--deps',type=Path)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
if args.deps: sys.path.insert(0,str(args.deps.resolve()))
sys.path.insert(0,str(args.archipelago.resolve()))
os.environ['AP_TEST_WORLDS']='rac2_openrac'
os.environ['SKIP_REQUIREMENTS_UPDATE']='1'
destination=args.archipelago/'worlds/rac2_openrac'
shutil.copytree(root/'apworld/rac2_openrac',destination,dirs_exist_ok=True)

from worlds.rac2_openrac import Rac2World
from worlds.rac2_openrac.native import OPTION_KEYS, validate_slot_data
from test.general import setup_multiworld
from Fill import distribute_items_restrictive
import yaml


class WorldTest(unittest.TestCase):
    def test_original_yaml_and_slot_data(self):
        template=yaml.safe_load((root/'templates/ArchipelagoRAC2.yaml').read_text(encoding='utf-8'))
        options=template['Ratchet & Clank 2']
        self.assertTrue(set(OPTION_KEYS)<=set(options))
        multi=setup_multiworld(Rac2World,seed=12345,options=options)
        multi.seed_name='test-seed'
        world=multi.worlds[1]
        data=world.fill_slot_data()
        self.assertEqual(set(data)-{'openrac'},set(OPTION_KEYS))
        self.assertEqual(validate_slot_data(data),data)
        self.assertEqual(data['openrac']['target'],'rac2')
        self.assertEqual(data['openrac']['supported_discs'],['ntsc','pal','ntsc2'])
        self.assertEqual(len(data['openrac']['starting_weapon_ids']),2)
        self.assertGreaterEqual(len([i for i in data['openrac']['starting_items'] if 201<=i<=220]),3)
        with tempfile.TemporaryDirectory() as output:
            world.generate_output(output)
            paths=list(Path(output).glob('*.aprac2openrac.json'))
            self.assertEqual(len(paths),1)
            self.assertEqual(json.loads(paths[0].read_text()),data)
            self.assertEqual(list(Path(output).glob('*.iso')),[])

    def test_weapon_vendor_logic_and_fill(self):
        for mode in range(4):
            for vendors in (False,True):
                with self.subTest(mode=mode,vendors=vendors):
                    options=dict(starting_weapons=mode, randomize_megacorp_vendor=vendors,
                                 randomize_gadgetron_vendor=vendors, extra_spaceship_challenge_locations=vendors,
                                 first_person_mode_glitch_in_logic=mode, enable_bolt_multiplier=True,
                                 nanotech_xp_multiplier=20, weapon_xp_multiplier=600)
                    multi=setup_multiworld(Rac2World,seed=8675309+mode,options=options)
                    multi.seed_name='fill-test'
                    distribute_items_restrictive(multi)
                    self.assertTrue(multi.can_beat_game())
                    self.assertFalse(multi.get_unfilled_locations())
                    data=multi.worlds[1].fill_slot_data()
                    self.assertEqual(len(data['openrac']['active_locations']),123 if vendors else 114)
                    self.assertEqual(data['enable_bolt_multiplier'],1)
                    self.assertEqual(data['nanotech_xp_multiplier'],20)

    def test_snivelak_rescue_angela_glitch_levels(self):
        # With the first-person glitch in logic from easy up, Rescue Angela needs only the
        # Swingshot, as the other Snivelak checks do (the rule once read `>+`, which is `> +1`).
        from BaseClasses import CollectionState
        full=['Swingshot','Grindboots','Gravity Boots','Dynamo']
        for mode,needs_all in ((0,True),(1,False),(2,False),(3,False)):
            with self.subTest(mode=mode):
                multi=setup_multiworld(Rac2World,seed=4242,options=dict(first_person_mode_glitch_in_logic=mode))
                world=multi.worlds[1]
                location=multi.get_location('Snivelak: Rescue Angela',1)
                state=CollectionState(multi)
                state.collect(world.create_item('Swingshot'),True)
                self.assertEqual(location.access_rule(state),not needs_all)
                for name in full[1:]:state.collect(world.create_item(name),True)
                self.assertTrue(location.access_rule(state))

    def test_maktar_jamming_array_pb_glitch_levels(self):
        # The Tractor Beam at every level; with No Glitches, the Heli-Pack too.
        from BaseClasses import CollectionState
        for mode in range(4):
            with self.subTest(mode=mode):
                multi=setup_multiworld(Rac2World,seed=4242,options=dict(first_person_mode_glitch_in_logic=mode))
                world=multi.worlds[1]
                location=multi.get_location('Maktar: Jamming Array - Platinum Bolt',1)
                state=CollectionState(multi)
                state.collect(world.create_item('Heli-Pack'),True)
                self.assertFalse(location.access_rule(state))
                state=CollectionState(multi)
                state.collect(world.create_item('Tractor Beam'),True)
                self.assertEqual(location.access_rule(state),mode>=1)
                state.collect(world.create_item('Heli-Pack'),True)
                self.assertTrue(location.access_rule(state))

    def test_logic_doc_is_current(self):
        # LOGIC.md is generated from the rules (tools/generate_logic_doc.py): rerun it after a change.
        spec=importlib.util.spec_from_file_location('generate_logic_doc',root/'tools/generate_logic_doc.py')
        doc=importlib.util.module_from_spec(spec);spec.loader.exec_module(doc)
        expected=doc.render(*doc.load_world(args.archipelago))
        self.assertEqual((root/'LOGIC.md').read_text(encoding='utf-8'),expected,
                         'LOGIC.md is out of date: run tools/generate_logic_doc.py')

    def test_two_slots(self):
        multi=setup_multiworld([Rac2World,Rac2World],seed=999,
                               options=[dict(randomize_megacorp_vendor=True),dict(starting_weapons=3)])
        multi.seed_name='two-slots'
        distribute_items_restrictive(multi)
        self.assertTrue(multi.can_beat_game())
        self.assertEqual([multi.worlds[p].fill_slot_data()['openrac']['player'] for p in (1,2)],[1,2])
        self.assertTrue(any(loc.item.player!=loc.player for loc in multi.get_filled_locations()))


unittest.main(argv=[sys.argv[0]],verbosity=2)
