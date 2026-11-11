#!/usr/bin/env python3
"""Fail-closed audit of the FIRST PUBLIC NEWCONF-2027 196-country issue.

Runs without future outcomes. Separate CI job independently reconstructs the
entire canonical issue byte-for-byte from its 25.1/26.1 official sources.
No alteration to the existing statebased GEO-2027 forecast is permitted.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FORECAST=ROOT/"data/forecast-2027-newconf.json"
MANIFEST=ROOT/"data/forecast-2027-newconf-manifest.json"
GENERATOR=ROOT/"scripts/forecast_2027_newconf.py"
FROZEN_SHA="e4482da7396872645d5101115435143d98fd9fdb1db1b1fdf41a42c99fc04b74"
FROZEN_GENERATOR_SHA="353508031023a16f901b61c80d23f6ee83af29e80745a757011881f0dc8c2d14"
FIRST_COMMIT="f3f2c17c9d4f5dd56266e376cd2d765f33f3dd97"
PREREG_COMMIT="1ff68f29914124763e29651e956f0086ce0caac4"
FIRST_UTC="2026-11-11T10:10:21Z"
SOURCE_25="5fe7411942aa7e6a38d6386faa64f4d7f0703482509f121c4136c0e3223d7f05"
SOURCE_ACD_25="b49f7e80510d8a5779a52d872aef5b26456b3f5cbdd3ec32031339488e81813f"
SOURCE_ACD_26="5f951743222964674a446e32a5a871077b29bd13349588d85fc59953d89c878a"
STATEBASED_SHA="5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5"
SCHEMA="idealab.psico.prospective_newconf_2027_manifest.v1"

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def audit(forecast_bytes,manifest,generator_bytes):
    if digest(forecast_bytes)!=FROZEN_SHA or digest(generator_bytes)!=FROZEN_GENERATOR_SHA:
        raise ValueError("First NEWCONF-2027 canonical source or generator has been modified")
    doc=json.loads(forecast_bytes)
    if (json.dumps(doc,sort_keys=True,ensure_ascii=False,separators=(",",":"))+"\n").encode("utf-8")!=forecast_bytes:
        raise ValueError("Canonical forecast changed formatting or bytes")
    if doc.get("schema")!="idealab.psico.prospective_newconf_2027.v1" or \
       doc.get("forecast_id")!="PSICO-QGEO01-NEWCONF2027-ORIGIN2025-V1" or \
       doc.get("state")!="PREPARED_FOR_FIRST_PUBLIC_ISSUE":
        raise ValueError("Not the original preregistered NEWCONF-2027 model document")
    if manifest.get("schema")!=SCHEMA or manifest.get("status")!="ISSUED_PROSPECTIVE_UNRESOLVED" or \
       manifest.get("forecast_id")!=doc["forecast_id"] or \
       manifest.get("forecast_sha256")!=FROZEN_SHA or \
       manifest.get("generator_sha256")!=FROZEN_GENERATOR_SHA or \
       manifest.get("first_public_forecast_commit")!=FIRST_COMMIT or \
       manifest.get("preregistered_protocol_main_commit")!=PREREG_COMMIT or \
       manifest.get("first_public_forecast_commit_utc")!=FIRST_UTC or \
       not "2026-11-11T00:00:00Z"<FIRST_UTC<"2027-01-01T00:00:00Z":
        raise ValueError("Prospective issue has no valid pre-event GitHub evidence")
    if manifest.get("outcomes_resolved")!=0 or manifest.get("demonstrated_predictive_skill") is not False or \
       manifest.get("evaluation_first_complete_release_only") is not True or \
       manifest.get("revision_changes_baseline_forbidden") is not True or \
       manifest.get("independent_timestamp_notary") is not False or \
       manifest.get("independent_confirmatory_retrospective_holdout") is not False:
        raise ValueError("Unverified outcomes or prospective skill asserted prematurely")
    src=doc["source"]
    if src["multiple_onset_training_sha256"]!=SOURCE_25 or \
       src["historical_acd_sha256"]!=SOURCE_ACD_25 or src["origin_acd_sha256"]!=SOURCE_ACD_26 or \
       src["training_newconf_last_year"]!=2024 or src["origin_conflict_activity_year"]!=2025 or \
       any(src[key] is not False for key in ("future_newconf_2025_observed",
           "future_newconf_2026_observed","newconf_2027_outcome_observed")):
        raise ValueError("UCDP source vintages or future-outcome safeguards changed")
    if manifest["sources"]!={"multiple_onset_25_1_sha256":SOURCE_25,
                             "acd_25_1_sha256":SOURCE_ACD_25,
                             "acd_26_1_sha256":SOURCE_ACD_26}:
        raise ValueError("Manifest source hashes differ from genuine preregistered sources")
    if doc["provenance"]["generator_sha256"]!=FROZEN_GENERATOR_SHA or \
       doc["provenance"]["statebased_geo2027_separate_and_unchanged"] is not True or \
       manifest.get("original_statebased_forecast_2027_unchanged_sha256")!=STATEBASED_SHA or \
       doc["provenance"]["independent_timestamp_notary"] is not False or \
       doc["protocol"]["skill_demonstrated"] is not False:
        raise ValueError("The original GEO-2027 issue is not isolated")
    if manifest.get("target_year")!=2027 or \
       manifest.get("origin_acd_activity_year")!=2025 or \
       manifest.get("training_newconf_last_year")!=2024 or \
       manifest.get("issued_country_count")!=196 or doc["target"]["year"]!=2027:
        raise ValueError("Target, issue cohort or time window changed")
    rows=doc["countries"]
    if len(rows)!=196 or len({row["country_id"] for row in rows})!=196 or \
       [row["country_id"] for row in rows]!=sorted(row["country_id"] for row in rows):
        raise ValueError("Frozen cohort country identities changed")
    for row in rows:
        if row["active_intrastate_2025"] not in (0,1):
            raise ValueError("2025 origin activity is not binary")
        for k in ("p_model","p_baseline_global_5y","p_country_eb","p_activity_global"):
            if not isinstance(row[k],(int,float)) or not math.isfinite(row[k]) or not 0<row[k]<1:
                raise ValueError("2027 forecast probability invalid")
    counts=Counter(row["active_intrastate_2025"] for row in rows)
    if counts[1]!=32 or counts[0]!=164:
        raise ValueError("Origin-2025 active risk set changed")
    sums={
      "model_expected_newconf_country_years":round(sum(v["p_model"] for v in rows),9),
      "baseline_expected_newconf_country_years":round(sum(v["p_baseline_global_5y"] for v in rows),9),
      "country_eb_expected_newconf_country_years":round(sum(v["p_country_eb"] for v in rows),9),
      "activity_global_expected_newconf_country_years":round(sum(v["p_activity_global"] for v in rows),9)
    }
    if sums["model_expected_newconf_country_years"]!=2.490944756 or \
       sums["baseline_expected_newconf_country_years"]!=1.397148676 or \
       manifest["expected_positive_country_years_model"]!=sums["model_expected_newconf_country_years"] or \
       manifest["expected_positive_country_years_baseline"]!=sums["baseline_expected_newconf_country_years"]:
        raise ValueError("Published number of expected 2027 new conflicts differs from original probabilities")
    return {
      "schema":"idealab.psico.prospective_newconf_2027_immutable_audit.v1",
      "forecast_id":doc["forecast_id"],
      "status":"ISSUED_PROSPECTIVE_OUTCOMES_UNRESOLVED",
      "preregistered_protocol_main_commit":PREREG_COMMIT,
      "first_public_forecast_commit":FIRST_COMMIT,
      "first_public_commit_utc":FIRST_UTC,
      "forecast_sha256":FROZEN_SHA,
      "generator_sha256":FROZEN_GENERATOR_SHA,
      "issued_country_count":len(rows),
      "origin_2025_active_countries":counts[1],
      "training_newconf_last_year":2024,
      "target_year":2027,
      "source_sha256":{
         "multiple_onset_25_1":SOURCE_25,
         "acd_25_1":SOURCE_ACD_25,
         "acd_26_1":SOURCE_ACD_26
      },
      **sums,
      "unique_model_probabilities":len({r["p_model"] for r in rows}),
      "minimum_model_probability":min(r["p_model"] for r in rows),
      "maximum_model_probability":max(r["p_model"] for r in rows),
      "model_probability_quantile_median":sorted(r["p_model"] for r in rows)[97:99],
      "target_labels_2027_resolved":0,
      "independent_skill_demonstrated":False,
      "statebased_2027_forecast_unchanged":True,
      "interpretation":"Expected value sums of issued probabilities, NOT observed events. First official UCDP Multiple Onset edition with 2027 outcomes required before evaluation; historical 2023/24 comparisons are exploratory."
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report")
    args=ap.parse_args()
    study=audit(FORECAST.read_bytes(),json.loads(MANIFEST.read_bytes()),GENERATOR.read_bytes())
    payload=json.dumps(study,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    print("NEWCONF2027_IMMUTABLE_AUDIT_BEGIN")
    print(payload,end="")
    print("NEWCONF2027_IMMUTABLE_AUDIT_END")
    if args.check_report and Path(args.check_report).read_text(encoding="utf8")!=payload:
        raise ValueError("Public immutable NEWCONF-2027 audit changed")

if __name__=="__main__":
    main()
