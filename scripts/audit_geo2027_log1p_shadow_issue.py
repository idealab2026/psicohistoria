#!/usr/bin/env python3
"""Fail-closed immutability audit for distinct prospective GEO2027 LOG1P shadow.

The SHA locked here, the source SHA, the 196 original probabilities and the
separate immutable shadow manifest all must agree. No future outcomes scored.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from prepare_geo2027_transition_alerts import SOURCE_SHA256

ROOT=Path(__file__).resolve().parents[1]
ISSUE=ROOT/"data/forecast-2027-log1p-shadow.json"
MANIFEST=ROOT/"data/forecast-2027-log1p-shadow-manifest.json"
ORIGINAL=ROOT/"data/forecast-2027-ucdp261.json"
FROZEN_ISSUE_SHA256="PENDING_FIRST_COMPLETE_SOURCE_ISSUE"
ID="PSICO-GEO2027-STATEBASED25-LOG1P-INTENSITY-SHADOW-V1"
SOURCE_SHA="66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def audit(issue_raw,manifest_raw,original_raw,*,frozen_sha=FROZEN_ISSUE_SHA256):
    if sha(original_raw)!=SOURCE_SHA256:
        raise ValueError("Original 2027 forecast SHA changed")
    original=json.loads(original_raw)
    manifest=json.loads(manifest_raw)
    issue=json.loads(issue_raw)
    if (not re.fullmatch("[a-f0-9]{64}",frozen_sha) or
        sha(issue_raw)!=frozen_sha or
        manifest.get("shadow_file_sha256")!=frozen_sha):
        raise ValueError("Prospective LOG1P first-issued shadow bytes changed")
    if sha(original_raw)!=SOURCE_SHA256:
        raise ValueError("Original 2027 forecast SHA changed")
    if (manifest.get("schema")!="idealab.psico.geo2027_log1p_shadow_manifest.v1"
        or manifest.get("forecast_id")!=ID
        or manifest.get("status")!="ISSUED_PROSPECTIVE_UNRESOLVED"
        or manifest.get("target_year")!=2027
        or manifest.get("issued_country_count")!=196
        or manifest.get("outcomes_resolved")!=0
        or manifest.get("demonstrated_predictive_skill") is not False
        or manifest.get("original_forecast_sha256")!=SOURCE_SHA256
        or manifest.get("source_26_1_sha256")!=SOURCE_SHA
        or not re.fullmatch("[a-f0-9]{40}",
                            str(manifest.get("first_complete_forecast_commit","")))):
        raise ValueError("Prospective shadow provenance manifest changed")
    if (issue.get("schema")!="idealab.psico.geo2027_log1p_intensity_shadow.v1"
        or issue.get("forecast_id")!=ID
        or issue.get("status")!="ISSUED_PROSPECTIVE_UNRESOLVED"
        or issue.get("target",{}).get("year")!=2027
        or issue.get("target",{}).get("final_metrics_require_all_196_resolved") is not True
        or issue.get("source",{}).get("last_observed_year")!=2025
        or issue.get("source",{}).get("sha256")!=SOURCE_SHA
        or issue.get("original_2027_immutable_sha256")!=SOURCE_SHA256
        or issue.get("outcomes_2027_resolved")!=0
        or issue.get("demonstrated_prospective_skill") is not False
        or issue.get("original_2027_probabilities_or_15_alerts_modified") is not False
        or issue.get("new_transition_alert_list_issued") is not False
        or issue.get("n_countries")!=196):
        raise ValueError("Prospective issue specification altered")
    original_map={r["country_id"]:r for r in original["countries"]}
    rows=issue.get("countries")
    if not isinstance(rows,list) or len(rows)!=196 or len(original_map)!=196:
        raise ValueError("Issued 196-country forecast not complete")
    ids=[r["country_id"] for r in rows]
    if ids!=sorted(ids) or set(ids)!=set(original_map) or len(set(ids))!=196:
        raise ValueError("Shadow membership changed")
    for r in rows:
        a=original_map[r["country_id"]]
        if (r["country"]!=a["country"]
            or r["origin_binary_state_2025"]!=a["last_observed_state_2025"]
            or r["original_2027_p_active"]!=a["p_model"]
            or int(r["origin_deaths_best_2025"]>=25)!=a["last_observed_state_2025"]
            or any(type(r[k]) not in (int,float) or not 0<r[k]<1
                   for k in ("original_2027_p_active",
                             "intercept_only_control_p_active_2027",
                             "log1p_shadow_p_active_2027"))):
            raise ValueError("Original/shadow country probability and origin mismatched")
    return {
        "sha256":frozen_sha,"country_n":len(rows),
        "first_complete_public_commit":manifest["first_complete_forecast_commit"],
        "future_2027_outcomes_resolved":0
    }


def main():
    result=audit(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes())
    print("OK separate GEO log1p first-public shadow immutability "+json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
