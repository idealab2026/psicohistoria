"""Tests for 196-country truly prospective global-only matched issue preparation."""
from __future__ import annotations

import copy
import json
import unittest

from audit_geo2027_log1p_shadow_issue import (
    ISSUE as OLD_ISSUE, MANIFEST as OLD_MANIFEST,
    ORIGINAL, FROZEN_ISSUE_SHA256,
    audit as audit_old,
)
from audit_geo2027_log1p_issued_death_stress import ALERTS, ALERT_SHA
from experiment_geo2027_intensity_markov_cross_release import counts_to_binary
from experiment_geo2027_log1p_matched_global_only import markov_global_only_offset
from prepare_geo2027_global_only_matched_shadow import (
    transition_snapshots, prospective_matched_rows, sha,
    ISSUE, ID, SCHEMA, TARGET_YEAR, SOURCE_YEAR,
)
from prepare_geo2027_log1p_shadow import origin_internal_rows
from test_experiment_geo2027_intensity_markov_cross_release import sample


class GlobalOnlyProspectiveShadowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.counts=sample()
        cls.binary=counts_to_binary(cls.counts)
        cls.rows=origin_internal_rows(cls.counts)
        cls.snaps=transition_snapshots(
            cls.binary,(r["origin_year"] for r in cls.rows))
        cls.ids=sorted(cls.counts)

    def test_196_country_future_reference_and_issued_artifacts_immutable(self):
        audit=audit_old(OLD_ISSUE.read_bytes(),OLD_MANIFEST.read_bytes(),
                        ORIGINAL.read_bytes())
        self.assertEqual(audit["country_n"],196)
        self.assertEqual(audit["future_2027_outcomes_resolved"],0)
        self.assertEqual(sha(ALERTS.read_bytes()),ALERT_SHA)
        self.assertEqual(TARGET_YEAR,2027)
        self.assertEqual(SOURCE_YEAR,2025)
        self.assertEqual(SCHEMA,"idealab.psico.geo2027_global_only_country_block_shadow.v1")
        self.assertTrue(ID.endswith("SHADOW-V1"))

    def test_15_snapshot_years_end_at_2025_not_2026_2027(self):
        self.assertEqual(sorted(self.snaps),list(range(2010,2024))+[2025])
        for y in range(2010,2024):
            self.assertEqual(len(self.snaps[y]),2)
            self.assertEqual(len(self.snaps[y][1]),196)

    def test_training_rows_omit_all_target_country_labels_and_leave_out_every_source_country_transition(self):
        target=self.ids[0]
        rows,n=prospective_matched_rows(self.rows,self.snaps,target)
        self.assertEqual(n,14)
        self.assertEqual(len(rows),len(self.rows)-n)
        self.assertTrue(all(r["country_id"]!=target for r in rows))
        self.assertEqual(max(r["target_year"] for r in rows),2025)
        self.assertEqual(max(r["origin_year"] for r in rows),2023)
        r=next(x for x in rows if x["target_year"]==2023)
        full,local=self.snaps[r["origin_year"]]
        direct=markov_global_only_offset(
            full,local,int(r["origin_deaths"]>=25),target,
            r["country_id"])
        self.assertEqual(r["p_original_binary"],direct)

    def test_target_country_history_changes_do_not_change_others_matched_training_offsets(self):
        cid=self.ids[0]
        baseline,_=prospective_matched_rows(self.rows,self.snaps,cid)
        altered_binary=copy.deepcopy(self.binary)
        for year in range(1989,2026):
            altered_binary[cid][year]=1-altered_binary[cid][year]
        updated_snaps=transition_snapshots(
            altered_binary,(r["origin_year"] for r in self.rows))
        changed,_=prospective_matched_rows(self.rows,updated_snaps,cid)
        self.assertEqual(baseline,changed)

    def test_source_future_labels_or_transitions_do_not_enter_forecast(self):
        changed=copy.deepcopy(self.counts)
        for cid,h in changed.items():
            h[2026]=1000 if cid%3 else 0
            h[2027]=1000 if cid%5 else 0
        rows_new=origin_internal_rows(changed)
        self.assertEqual(self.rows,rows_new)
        new_snaps=transition_snapshots(
            counts_to_binary(changed),
            (r["origin_year"] for r in rows_new))
        self.assertEqual(self.snaps,new_snaps)

    def test_global_only_forecast_drops_country_transitions_but_observes_origin_state(self):
        counts,local=self.snaps[2025]
        for cid in self.ids[::11]:
            state=self.binary[cid][2025]
            p=markov_global_only_offset(counts,local,state,cid)
            self.assertTrue(0<p<1)
            self.assertEqual(
                p,markov_global_only_offset(counts,local,state,cid))

    def test_missing_or_bad_training_fails_closed(self):
        with self.assertRaises(ValueError):
            prospective_matched_rows([],self.snaps,self.ids[0])
        with self.assertRaises(ValueError):
            prospective_matched_rows(self.rows,self.snaps,999999)
        with self.assertRaises(ValueError):
            transition_snapshots(self.binary,[2016])
        with self.assertRaises(ValueError):
            transition_snapshots(self.binary,[2026])

    def test_canonical_issue_must_not_be_placeholder_when_checking_report(self):
        self.assertTrue(ISSUE.as_posix().endswith(
            "forecast-2027-global-only-matched-shadow.json"))


if __name__=="__main__":
    unittest.main()
