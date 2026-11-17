"""Offline adversarial Tunisia H2 UCDP source revision attribution tests."""
from __future__ import annotations

import copy
import json
import math
import unittest

from audit_geo2027_global_only_matched_issue import ISSUE
from audit_geo_legacy_ged_countryyear_bridge import PINNED_GED_SHA256
from audit_geo_ged20_21_coverage_revisions import PINNED_NEW_SHA256
from experiment_geo_ged_tunisia_2013_15_attribution import (
    _check_issues, _event_panel, _probabilities, _shapley21to22,
    BRIDGE, REVISIONS, H2, CHANGED_YEARS, EARLY_ORIGIN,
    HIST_ORIGIN, HIST_TARGET, MODELS, TUNISIA,
)


def sample():
    # All 196 countries; robust nondegenerate 4x4 transition exposure counts.
    # Sources are synthetic; no historical claim about their values.
    ids=list(range(1,196))+[TUNISIA]
    hist={}
    for cid in ids:
        hist[cid]={year:(0,5,35,150)[((year-1989)+(cid%7))%4]
                   for year in range(1989,2023)}
    return hist,ids


class TunisiaRevisionAttributionTests(unittest.TestCase):
    def test_official_anchors_do_not_change_original_2027_issue(self):
        issue=json.loads(ISSUE.read_text(encoding="utf8"))
        bridge=json.loads(BRIDGE.read_text(encoding="utf8"))
        revisions=json.loads(REVISIONS.read_text(encoding="utf8"))
        h2=json.loads(H2.read_text(encoding="utf8"))
        cohort=_check_issues(issue,bridge,revisions,h2)
        self.assertEqual(len(cohort),196)
        self.assertIn(TUNISIA,cohort)
        self.assertEqual(CHANGED_YEARS,(2013,2014,2015))
        self.assertEqual(revisions["source_zip_sha256"],
                         {**PINNED_GED_SHA256,**PINNED_NEW_SHA256})
        self.assertEqual(issue["official_2027_outcomes_resolved"],0)
        with self.assertRaisesRegex(ValueError,"anchors"):
            changed=copy.deepcopy(revisions)
            changed["source_zip_sha256"]["21.1"]="0"*64
            _check_issues(issue,bridge,changed,h2)
        with self.assertRaises(ValueError):
            changed=copy.deepcopy(issue)
            changed["official_2027_outcomes_resolved"]=196
            _check_issues(changed,bridge,revisions,h2)

    def test_ged_panel_fills_absent_event_with_zero_not_revised_future(self):
        hist,ids=sample()
        data={(x,y):v for x,h in hist.items() for y,v in h.items() if v}
        result=_event_panel(data,ids,max_year=EARLY_ORIGIN)
        self.assertEqual(len(result),196)
        self.assertEqual(len(result[TUNISIA]),EARLY_ORIGIN-1989+1)
        self.assertNotIn(2020,result[TUNISIA])
        self.assertEqual(result[TUNISIA][1989],hist[TUNISIA][1989])
        with self.assertRaises(ValueError):
            _event_panel(data,ids,max_year=2025)
        with self.assertRaises(ValueError):
            _event_panel({(616,2014):-1},ids,max_year=2019)
        with self.assertRaises(ValueError):
            _event_panel(data,ids[:-1],max_year=2019)

    def test_original_binary_and_four_state_origin_only_never_use_2020plus(self):
        hist,ids=sample()
        first=_probabilities(hist,EARLY_ORIGIN,ids)
        altered=copy.deepcopy(hist)
        for cid in ids:
            for year in range(2020,2023):
                altered[cid][year]=123456 if cid%2 else 0
        second=_probabilities(altered,EARLY_ORIGIN,ids)
        self.assertEqual(first,second)
        self.assertEqual(first["last_training_year"],2019)
        self.assertEqual(first["origin_binary_state"],
                         int(hist[TUNISIA][2019]>=25))
        self.assertTrue(all(0<first["p"][m]<1 for m in MODELS))

    def test_four_factor_shapley_exact_exhaustion_and_only_three_rows(self):
        old,ids=sample()
        new=copy.deepcopy(old)
        for year, value in zip(CHANGED_YEARS,(29,51,75)):
            new[TUNISIA][year]=value
            old[TUNISIA][year]=(0,0,17)[CHANGED_YEARS.index(year)]
        # Other revisions may affect global transition kernel.
        new[2][2014]=0 if old[2][2014] else 150
        res=_shapley21to22(old,new,ids)
        self.assertEqual(res["coalition_n"],16)
        self.assertEqual(list(res["intervention_bits"].values()),
                         ["all_other_source_edits","tunisia_2013",
                          "tunisia_2014","tunisia_2015"])
        self.assertEqual(res["old_full"]["p"],_probabilities(old,2019,ids)["p"])
        self.assertEqual(res["revised_full"]["p"],_probabilities(new,2019,ids)["p"])
        for model in MODELS:
            observed=(res["revised_full"]["p"][model]-
                      res["old_full"]["p"][model])
            self.assertAlmostEqual(
                sum(res["model_shapley_H2_probability_changes"][model].values()),
                observed,places=10)
        self.assertTrue(res["not_world_causal_or_real_asof_issued_predictions"])

    def test_h2_origin_and_target_prespecification(self):
        self.assertEqual((EARLY_ORIGIN,HIST_ORIGIN,HIST_TARGET),(2019,2022,2024))
        self.assertEqual(MODELS,("binary","four_state"))
        with self.assertRaises(ValueError):
            _probabilities({},2019,list(range(1,197)))


if __name__=="__main__":
    unittest.main()
