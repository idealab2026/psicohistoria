#!/usr/bin/env python3
"""Adversarial episode-linkage gates for Burundi GED442626."""
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import audit_geo_burundi_2022_neighbor_event_linkage as m


def fixture():
    return json.loads(m.INPUT.read_text(encoding="utf-8"))


class NeighborEventControls(unittest.TestCase):
    def test_five_replayed_hard_negatives(self):
        r = m.build(fixture())
        self.assertEqual(r["records_n"], 5)
        self.assertEqual(r["excluded_as_direct_june_episode_n"], 4)
        self.assertEqual(r["ambiguous_later_discovery_n"], 1)
        self.assertEqual(r["additional_independent_june_fatality_verifications_n"], 0)
        self.assertEqual(r["confirmed_disjoint_person_rosters_n"], 0)

    def test_publication_before_june_cannot_observe_future(self):
        c = fixture()["case_records"][0]
        self.assertEqual(m.classify(c), "EXCLUDE_PUBLICATION_PREDATES_JUNE")

    def test_july_four_bodies_are_not_june_four(self):
        c = fixture()["case_records"][1]
        self.assertEqual(m.classify(c), "EXCLUDE_SEPARATE_REPORTED_BATTLE_WINDOW")
        self.assertIn("not verified death dates", c["window_basis"])

    def test_september_offensive_not_june(self):
        c = fixture()["case_records"][2]
        self.assertEqual(m.classify(c), "EXCLUDE_SEPARATE_REPORTED_BATTLE_WINDOW")
        self.assertEqual(c["reported_count"], 42)

    def test_december_late_body_discovery_not_forcibly_cleared(self):
        c = fixture()["case_records"][3]
        self.assertIsNone(c["event_window"])
        self.assertEqual(m.classify(c),
                         "UNRESOLVED_DEATH_DATES_NOT_JUNE_CORROBORATION")

    def test_mine_disaster_not_war_deaths(self):
        c = fixture()["case_records"][4]
        self.assertEqual(m.classify(c), "EXCLUDE_INCOMPATIBLE_CAUSE")

    def test_host_allowlist_blocks_unreviewed_sources(self):
        c = copy.deepcopy(fixture()["case_records"][1])
        c["source_url"] = "https://example.org/fake"
        with self.assertRaises(ValueError):
            m.classify(c)

    def test_fatality_verification_forgery_is_rejected(self):
        c = copy.deepcopy(fixture()["case_records"][1])
        c["local_primary_june_2022_fatality_verification"] = True
        with self.assertRaises(ValueError):
            m.classify(c)

    def test_manually_changing_count_or_relation_breaks_replay(self):
        data = fixture()
        data["expected_results"]["excluded_as_direct_june_episode_n"] = 5
        with self.assertRaises(ValueError):
            m.build(data)

    def test_shift_to_target_window_requires_manual_review(self):
        c = copy.deepcopy(fixture()["case_records"][1])
        c["event_window"] = ["2022-06-19", "2022-06-21"]
        self.assertEqual(m.classify(c), "MANUAL_SAME_EPISODE_REVIEW_REQUIRED")

    def test_event_window_cannot_exceed_publication(self):
        c = copy.deepcopy(fixture()["case_records"][1])
        c["event_window"] = ["2022-07-19", "2022-07-20"]
        with self.assertRaises(ValueError):
            m.classify(c)

    def test_original_anchor_and_window_cannot_change(self):
        data = fixture()
        data["target"]["fatalities_in_GED_best"] = 42
        with self.assertRaises(ValueError):
            m.build(data)


if __name__ == "__main__":
    unittest.main()
