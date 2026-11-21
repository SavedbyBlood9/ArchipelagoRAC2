import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'data/aprac2-contract.json').read_text(encoding='utf-8'))

    def test_aprac2_identity(self):
        self.assertEqual(self.data['game'], 'Ratchet & Clank 2')
        items = {r['symbol']: r for r in self.data['items']}
        locations = {r['symbol']: r for r in self.data['locations']}
        self.assertEqual(items['DYNAMO']['id'], 10)
        self.assertEqual(items['DYNAMO']['game_value'], 0x24)
        self.assertEqual(items['PLATINUM_BOLT']['id'], 301)
        self.assertEqual(locations['OOZLA_OUTSIDE_MEGACORP_STORE']['id'], 10)

    def test_complete_observation_tables(self):
        expected = {'PLANET_UNLOCK_TO_LOCATION_ID': 20, 'INVENTORY_OFFSET_TO_LOCATION_ID': 19,
                    'PLAT_BOLT_OFFSET_TO_LOCATION_ID': 40, 'NANOTECH_OFFSET_TO_LOCATION_ID': 10}
        self.assertEqual({k: len(v) for k, v in self.data['check_maps'].items()}, expected)
        ids = {r['id'] for r in self.data['locations']}
        for rows in self.data['check_maps'].values():
            self.assertEqual(len(rows), len({r['game_value'] for r in rows}))
            self.assertTrue(all(r['location_id'] in ids for r in rows))

    def test_ids_and_optional_locations(self):
        for key in ('items', 'locations'):
            rows = self.data[key]
            self.assertEqual(len(rows), len({r['id'] for r in rows}))
        optional = [r for r in self.data['locations'] if r['enabled_when']]
        self.assertTrue(optional)
        self.assertTrue(any('extra_spaceship_challenge_locations' in r['enabled_when'] for r in optional))
        self.assertTrue(any(r['vendor'] for r in self.data['locations']))


if __name__ == '__main__':
    unittest.main()
