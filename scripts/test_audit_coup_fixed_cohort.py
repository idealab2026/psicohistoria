import unittest
from audit_coup_fixed_cohort import compare

class RosterTest(unittest.TestCase):
    def test_enter_exit_and_stale(self):
        sets = {"dec31": {(1, 2022), (2, 2022), (3, 2022)},
                "jan1": {(1, 2025), (4, 2025)},
                "full_year": {(4, 2025)},
                "any_day": {(1, 2025), (3, 2025), (4, 2025)}}
        x = compare(sets, 2025, 3)
        self.assertEqual((x["intersection_n"], x["missing_from_fixed"], x["stale_in_fixed"]), (1, 1, 2))
        self.assertEqual(x["fixed_no_membership_during_year"], 1)
        self.assertEqual(x["fixed_not_full_year"], 3)
        self.assertFalse(x["exact_match"])
    def test_exact(self):
        sets = {"dec31": {(1, 2024)}, "jan1": {(1, 2025)},
                "full_year": {(1, 2025)}, "any_day": {(1, 2025)}}
        self.assertTrue(compare(sets, 2025, 1)["exact_match"])
    def test_invalid(self):
        sets = {"dec31": set(), "jan1": {(1, 2025)},
                "full_year": {(1, 2025)}, "any_day": {(1, 2025)}}
        with self.assertRaises(ValueError):
            compare(sets, 2025, 1)
    def test_full_not_subset(self):
        sets = {"dec31": {(1, 2024)}, "jan1": {(1, 2025)},
                "full_year": {(2, 2025)}, "any_day": {(1, 2025), (2, 2025)}}
        with self.assertRaises(ValueError):
            compare(sets, 2025, 1)

if __name__ == "__main__":
    unittest.main()
