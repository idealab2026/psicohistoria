#!/usr/bin/env python3
"""Fail-closed first-public 196-country GEO2027 global-only issue audit.

Also implements a deterministic prospective FULL-196 scoring contract for
when the *first complete official UCDP 2027 vintage* arrives. All current
test labels are synthetic. No real 2027 outcomes have been resolved.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from audit_geo2027_log1p_shadow_issue import (
    ISSUE as OLD_SHADOW, MANIFEST as OLD_MANIFEST, ORIGINAL,
    FROZEN_ISSUE_SHA256, audit as audit_old,
)
from audit_geo2027_log1p_issued_death_stress import ALERTS, ALERT_SHA
from prepare_geo2027_transition_alerts import SOURCE_SHA256
from prepare_geo2027_global_only_matched_shadow import (
    ISSUE, ID, SCHEMA,
)

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"data/forecast-2027-global-only-matched-manifest.json"
FROZEN_SHA256="251595a12758e006cf21dabbb9771e10b5961c469a5317d6b2b1c5de227f3697"
FIRST_COMMIT="52ab9ffe7d49e4574b61a9f6a35c57cf7b43082d"
FIRST_COMMIT_UTC="2026-11-16T19:49:19Z"
SOURCE_SHA="66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _valid_prob(p):
    return type(p) in (int,float) and math.isfinite(p) and 0<p<1


def audit(issue_raw,manifest_raw,original_raw,old_shadow_raw,
          old_manifest_raw,alerts_raw):
    audit_old(old_shadow_raw,old_manifest_raw,original_raw)
    if sha(original_raw)!=SOURCE_SHA256 or sha(alerts_raw)!=ALERT_SHA:
        raise ValueError("Original GEO forecast or transition alerts mutated")
    if sha(issue_raw)!=FROZEN_SHA256:
        raise ValueError("First complete global-only prospective issue SHA modified")
    manifest=json.loads(manifest_raw)
    issue=json.loads(issue_raw)
    original=json.loads(original_raw)
    oldshadow=json.loads(old_shadow_raw)
    if (manifest.get("schema")!="idealab.psico.geo2027_global_only_matched_shadow_manifest.v1"
        or manifest.get("forecast_id")!=ID
        or manifest.get("status")!="ISSUED_PROSPECTIVE_UNRESOLVED"
        or manifest.get("forecast_path")!=str(ISSUE.relative_to(ROOT))
        or manifest.get("forecast_sha256")!=FROZEN_SHA256
        or manifest.get("first_complete_forecast_commit")!=FIRST_COMMIT
        or manifest.get("first_complete_forecast_commit_utc")!=FIRST_COMMIT_UTC
        or manifest.get("independently_notarized") is not False
        or manifest.get("original_GEO_forecast_sha256")!=SOURCE_SHA256
        or manifest.get("original_LOG1P_shadow_sha256")!=FROZEN_ISSUE_SHA256
        or manifest.get("original_15_alerts_sha256")!=ALERT_SHA
        or manifest.get("source_26_1_sha256")!=SOURCE_SHA
        or manifest.get("fixed_original_gwno_cohort_n")!=196
        or manifest.get("individual_country_blocked_calibrations_n")!=196
        or manifest.get("target_year")!=2027
        or manifest.get("training_max_label_year")!=2025
        or manifest.get("training_max_feature_year")!=2023
        or manifest.get("outcomes_resolved")!=0
        or manifest.get("predictive_skill_demonstrated") is not False
        or manifest.get("issued_alpha_arms")!=[0,1]
        or manifest.get("no_old_forecast_or_alert_modified") is not True):
        raise ValueError("Global-only first-complete issue manifest contract differs")
    if (issue.get("schema")!=SCHEMA or issue.get("forecast_id")!=ID
        or issue.get("status")!="ISSUED_PROSPECTIVE_UNRESOLVED"
        or issue.get("source",{}).get("source_archive_sha256")!=SOURCE_SHA
        or issue.get("source",{}).get("last_observed_year")!=2025
        or issue.get("target",{}).get("year")!=2027
        or issue.get("target",{}).get("all_196_GWNO_fixed_identical_to_original_issue") is not True
        or issue.get("target",{}).get("official_2027_labels_missing_are_not_zero") is not True
        or issue.get("target",{}).get("final_scoring_requires_all_196_2027_labels") is not True
        or issue.get("method",{}).get("country_models_fitted")!=196
        or issue.get("method",{}).get("no_2026_or_2027_label_or_transition_used") is not True
        or issue.get("method",{}).get("each_forecast_country_all_supervised_historical_rows_excluded") is not True
        or issue.get("method",{}).get("each_training_row_prior_excludes_forecast_country") is not True
        or issue.get("method",{}).get("each_training_row_prior_excludes_its_own_source_country") is not True
        or issue.get("method",{}).get("two_published_alpha_variants")!=[0.0,1.0]
        or issue.get("training",{}).get("latest_training_outcome_year")!=2025
        or issue.get("training",{}).get("latest_training_feature_origin_year")!=2023
        or issue.get("n_countries")!=196
        or issue.get("official_2027_outcomes_resolved")!=0
        or issue.get("demonstrated_prospective_predictive_skill") is not False
        or issue.get("original_GEO_or_LOG1P_or_15_alerts_modified") is not False
        or issue.get("new_transition_alerts_issued") is not False
        or issue.get("replaces_any_existing_2027_issue") is not False
        or issue.get("prior_frozen_original_geo_sha256")!=SOURCE_SHA256
        or issue.get("prior_frozen_log1p_shadow_sha256")!=FROZEN_ISSUE_SHA256
        or issue.get("prior_frozen_15_alerts_sha256")!=ALERT_SHA):
        raise ValueError("Global-only country-blocked 2027 probability issue specification altered")
    score=issue.get("prospective_scoring_precommitment",{})
    if (score.get("primary_pair")!=
            "full196_Brier_global_only_alpha1_minus_frozen_original_LOG1P_shadow"
        or score.get("fixed_country_universe")!=196
        or score.get("no_ex_post_threshold_or_model_selection") is not True
        or score.get("do_not_treat_missing_country_label_as_zero") is not True
        or score.get("report_all_candidates_and_pairs_even_if_unfavourable") is not True
        or score.get("primary_2027_official_UCDP_edition")!=
        "first_complete_edition_with_2027_country_year_labels_for_all_original_196_ids"):
        raise ValueError("First-public future scoring protocol mutated")
    rows=issue.get("countries")
    old_rows=oldshadow.get("countries")
    orig_rows=original.get("countries")
    if (not isinstance(rows,list) or not isinstance(old_rows,list)
        or not isinstance(orig_rows,list) or
        len(rows)!=196 or len(old_rows)!=196 or len(orig_rows)!=196):
        raise ValueError("Fixed 196-country prospective risk universe absent")
    o={r["country_id"]:r for r in orig_rows}
    s={r["country_id"]:r for r in old_rows}
    ids=[r["country_id"] for r in rows]
    if (ids!=sorted(ids) or len(set(ids))!=196 or
        set(ids)!=set(o) or set(ids)!=set(s)):
        raise ValueError("First-country issue IDs differ from original GWNO")
    for r in rows:
        a=o[r["country_id"]];b=s[r["country_id"]]
        d=r["origin_deaths_best_2025"];state=r["origin_binary_state_2025"]
        if (r["country"]!=a["country"] or r["country"]!=b["country"]
            or type(d) is not int or d<0 or state!=int(d>=25)
            or state!=a["last_observed_state_2025"]
            or d!=b["origin_deaths_best_2025"]
            or r["original_GEO2027_p_active_frozen"]!=a["p_model"]
            or r["original_LOG1P2027_p_active_frozen"]!=
                b["log1p_shadow_p_active_2027"]
            or r["original_intercept_control_p_active_frozen"]!=
                b["intercept_only_control_p_active_2027"]
            or not all(_valid_prob(r[k]) for k in (
                "original_GEO2027_p_active_frozen",
                "original_LOG1P2027_p_active_frozen",
                "original_intercept_control_p_active_frozen",
                "global_only_markov_H2_p_active",
                "global_only_alpha0_p_active_2027",
                "global_only_alpha1_p_active_2027"))
            or len(r["country_blocked_logistic_beta"])!=3
            or any(not math.isfinite(v) or type(v) not in (float,int)
                   for v in r["country_blocked_logistic_beta"])
            or not 2700<=r["training_rows_after_country_withheld"]<=2742
            or not 1<=r["country_supervised_training_rows_withheld"]<=20):
            raise ValueError("Unmatched 196-country original forecast or invalid prospective model")
        if (d==0 or d>=25) and (
            r["global_only_alpha0_p_active_2027"]!=
            r["global_only_alpha1_p_active_2027"]):
            raise ValueError("Fixed 0/1 slope arms must agree with no subthreshold feature")
    expected=issue.get("expected_active_countries_sum_probabilities",{})
    summands={
        "original_GEO":"original_GEO2027_p_active_frozen",
        "original_LOG1P":"original_LOG1P2027_p_active_frozen",
        "global_only_alpha0":"global_only_alpha0_p_active_2027",
        "global_only_alpha1":"global_only_alpha1_p_active_2027",
    }
    if any(abs(expected.get(k,math.inf)-round(
        sum(r[field] for r in rows),10))>1e-9 for k,field in summands.items()):
        raise ValueError("Expected-active sums changed")
    return {
        "sha256":FROZEN_SHA256,
        "first_complete_public_commit":FIRST_COMMIT,
        "first_complete_commit_utc":FIRST_COMMIT_UTC,
        "country_n":196,
        "fixed_alpha_arms":[0,1],
        "official_2027_outcomes_resolved":0,
    }


def prospective_full196_score(issue,labels):
    """Synthetic-label-tested scoring kernel; NEVER infer missing zero.

    The caller must independently authenticate which FIRST COMPLETE
    official 2027 UCDP edition supplies the labels; this function does
    not claim to authenticate a future release by itself.
    """
    rows=issue["countries"]
    ids={r["country_id"] for r in rows}
    if (issue.get("official_2027_outcomes_resolved")!=0
        or len(rows)!=196 or len(ids)!=196
        or type(labels) is not dict or set(labels)!=ids
        or any(type(x) is not int or x not in (0,1)
               for x in labels.values())):
        raise ValueError("All 196 independently verified 2027 binary labels required")
    arm_fields={
        "original_GEO":"original_GEO2027_p_active_frozen",
        "original_LOG1P":"original_LOG1P2027_p_active_frozen",
        "intercept_control":"original_intercept_control_p_active_frozen",
        "global_only_alpha0":"global_only_alpha0_p_active_2027",
        "global_only_alpha1":"global_only_alpha1_p_active_2027",
    }
    metrics={}
    for name,field in arm_fields.items():
        p=[r[field] for r in rows];y=[labels[r["country_id"]] for r in rows]
        if not all(_valid_prob(v) for v in p):
            raise ValueError("Invalid prospective probability")
        metrics[name]={
            "brier":sum((v-u)**2 for v,u in zip(p,y))/196,
            "logloss":-sum(u*math.log(v)+(1-u)*math.log1p(-v)
                          for v,u in zip(p,y))/196,
        }
    diffs={
        "primary_Brier_globalonly_alpha1_minus_original_LOG1P":
            metrics["global_only_alpha1"]["brier"]-
            metrics["original_LOG1P"]["brier"],
        "secondary_Brier_globalonly_alpha0_minus_alpha1":
            metrics["global_only_alpha0"]["brier"]-
            metrics["global_only_alpha1"]["brier"],
        "secondary_Brier_globalonly_alpha1_minus_GEO":
            metrics["global_only_alpha1"]["brier"]-
            metrics["original_GEO"]["brier"],
        "secondary_Brier_globalonly_alpha0_minus_GEO":
            metrics["global_only_alpha0"]["brier"]-
            metrics["original_GEO"]["brier"],
        "secondary_Brier_globalonly_alpha0_minus_original_LOG1P":
            metrics["global_only_alpha0"]["brier"]-
            metrics["original_LOG1P"]["brier"],
        "secondary_Logloss_globalonly_alpha1_minus_original_LOG1P":
            metrics["global_only_alpha1"]["logloss"]-
            metrics["original_LOG1P"]["logloss"],
        "secondary_Logloss_globalonly_alpha0_minus_alpha1":
            metrics["global_only_alpha0"]["logloss"]-
            metrics["global_only_alpha1"]["logloss"],
    }
    return {
        "target_year":2027,"n_country_labels":196,
        "positive_labels":sum(labels.values()),
        "first_complete_official_edition_must_be_external_verified":True,
        "metrics":metrics,
        "predeclared_paired_differences":diffs,
        "not_a_country_independent_hypothesis_test":True,
    }


def main():
    result=audit(ISSUE.read_bytes(),MANIFEST.read_bytes(),
                 ORIGINAL.read_bytes(),OLD_SHADOW.read_bytes(),
                 OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    print("OK first-complete 196-country global-only prospective GEO2027 immutable audit "+
          json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
