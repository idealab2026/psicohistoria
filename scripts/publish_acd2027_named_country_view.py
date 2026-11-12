#!/usr/bin/env python3
"""Readable country-named view of IMMUTABLE first issued ACD2027 predictions.

Never changes the 32-country issue nor GEO2027. GWNO country identifiers
map one-to-one to official country names in original SHA-pinned 196-country
UCDP GEO2027 issue. Secondary country-EB ranking is exploratory; primary
global recent5 forecast stays the preregistered reference (not a ranking).
"""
import argparse
import hashlib
import json
from pathlib import Path

from audit_issued_acd2027_retention import (
    EXPECTED_ISSUE_SHA256, EXPECTED_FIRST_COMMIT,
)
from prepare_geo2027_transition_alerts import (
    FORECAST_PATH, MANIFEST_PATH, SOURCE_SHA256, verify_source, sha,
)
from prepare_acd2027_prospective_retention import ISSUE_PATH, FORECAST_ID

OUT=Path("data/forecast-2027-acd-retention-country-view.json")
VIEW_ID="PSICO-ACD2027-RETENTION-COUNTRY-VIEW-V1"
MODELS=("p_global_recent5","p_country_eb","p_lag1_group")


def make_view(acd_raw,geo_raw,geo_manifest):
    if (hashlib.sha256(acd_raw).hexdigest()!=EXPECTED_ISSUE_SHA256
        or sha(geo_raw)!=SOURCE_SHA256):
        raise ValueError("Original first-public 2027 ACD/GEO probabilities modified")
    geo,geo_rows=verify_source(geo_raw,geo_manifest)
    if len(geo_rows)!=196:
        raise ValueError("Named reference GEO original 196-country source missing")
    labels={r["country_id"]:r["country"] for r in geo_rows}
    if len(labels)!=196 or any(not isinstance(v,str) or not v.strip()
                               for v in labels.values()):
        raise ValueError("Original source country name crosswalk invalid")
    acd=json.loads(acd_raw)
    src=acd["countries"]
    if (acd["forecast_id"]!=FORECAST_ID
        or acd["origin_year"]!=2025
        or acd["target_year"]!=2027
        or acd["n_origin_active_countries"]!=32
        or len(src)!=32 or
        acd["2027_outcomes_resolved"]!=0
        or acd["actual_2027_outcomes_used"] is not False
        or acd["prospective_skill_demonstrated"] is not False
        or acd["primary_model"]!="p_global_recent5"
        or acd["secondary_models"]!=["p_country_eb","p_lag1_group"]):
        raise ValueError("Cannot derive labels from a changed ACD2027 issue")
    ids=[r["country_id"] for r in src]
    if len(set(ids))!=32 or ids!=sorted(ids) or any(cid not in labels for cid in ids):
        raise ValueError("One or more ACD country IDs absent or unordered in original GEO")
    rows=[]
    for r in src:
        p={k:r[k] for k in MODELS}
        if any(type(v) not in (float,int) or not 0<v<1 for v in p.values()):
            raise ValueError("Invalid frozen country probabilities")
        rows.append({
            "gwno_country_id":r["country_id"],
            "country_name_from_original_geo_source":labels[r["country_id"]],
            "known_at_issue_active_2025":True,
            "also_active_in_2024":r["also_active_in_2024"],
            "historical_training_country_examples":r["origin_only_historical_country_training_rows"],
            "p_primary_global_recent5":r["p_global_recent5"],
            "p_secondary_country_eb":r["p_country_eb"],
            "p_secondary_lag1_group":r["p_lag1_group"],
            "country_eb_minus_issued_primary":round(r["p_country_eb"]-r["p_global_recent5"],12),
            "secondary_ranking_not_prospectively_validated":True,
        })
    rows.sort(key=lambda r:(-r["p_secondary_country_eb"],r["gwno_country_id"]))
    for i,r in enumerate(rows,1):
        r["secondary_country_eb_rank"]=i
    if (len(rows)!=32
        or sorted(r["gwno_country_id"] for r in rows)!=ids):
        raise ValueError("Derived secondary presentation changed original country list")
    expected={k:acd["model_expected_2027_persistence"][k] for k in MODELS}
    if any(abs(sum(r[{
        "p_global_recent5":"p_primary_global_recent5",
        "p_country_eb":"p_secondary_country_eb",
        "p_lag1_group":"p_secondary_lag1_group",
    }[k]] for r in rows)-expected[k])>1e-9 for k in MODELS):
        raise ValueError("Named view does not preserve all three 32-country model sums")
    return {
        "schema":"idealab.psico.acd2027_retention_country_named_view.v1",
        "view_id":VIEW_ID,
        "immutable_issued_acd2027_sha256":EXPECTED_ISSUE_SHA256,
        "first_public_acd2027_issue_commit":EXPECTED_FIRST_COMMIT,
        "immutable_geo2027_country_name_reference_sha256":SOURCE_SHA256,
        "target_year":2027,
        "origin_year":2025,
        "fixed_country_count":32,
        "primary_model":"p_global_recent5",
        "secondary_display_order":"p_country_eb descending, GWNO code ascending tie",
        "secondary_model_evidence":"EXPLORATORY; not independently demonstrated better than globally calibrated primary",
        "all_three_model_expected_persistent_counts":expected,
        "observed_target_2027_labels":0,
        "new_forecast_issued":False,
        "original_acd_geo_shadow_alerts_newconf_probabilities_changed":False,
        "country_names_source":"Earlier issued SHA-pinned original GEO2027 196-country country names, keyed only by same numeric GWNO",
        "rows":rows,
        "limitations":"Names and display ranks are a derived view of existing 2027 issue. Rank uses unvalidated exploratory per-country secondary model; primary is shared global rate. Not a claim of peace, new war, or evidence of 2027 forecasting skill."
    }


def canonical(report):
    return (json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--check-report",action="store_true")
    args=p.parse_args()
    report=make_view(
        ISSUE_PATH.read_bytes(),FORECAST_PATH.read_bytes(),
        json.loads(MANIFEST_PATH.read_text(encoding="utf8")))
    raw=canonical(report)
    print("ACD2027_NAMED_COUNTRY_VIEW_BEGIN")
    print(raw.decode(),end="")
    print("ACD2027_NAMED_COUNTRY_VIEW_END")
    if args.check_report and OUT.read_bytes()!=raw:
        raise ValueError("Country-name view changed relative to first-public forecasts")


if __name__=="__main__":
    main()
