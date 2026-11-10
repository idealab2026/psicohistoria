#!/usr/bin/env python3
"""Independent reproducibility audit for the already issued GEO-2027 country cohort.

Never issues new forecasts, never recalibrates, never reads 2026/2027 labels.
Recreates the immutable generator output byte for byte from the pinned UCDP ZIP
and independently verifies its probability equations using official 1989–2025 rows.
Only aggregated, outcome-free audit diagnostics are printed/published.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from forecast_2027_statebased import (
    build_forecast, download_official, sha256, PINNED_SOURCE_SHA256,
    estimate_from_history, EXPECTED_COHORT, CUTOFF_YEAR,
)
from build_official_countries import parse_public_source, read_zip

ROOT=Path(__file__).resolve().parents[1]
FROZEN_SHA="5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5"
GENERATOR=ROOT/"scripts/forecast_2027_statebased.py"
FORECAST=ROOT/"data/forecast-2027-ucdp261.json"
MANIFEST=ROOT/"data/forecast-2027-manifest.json"
HISTOGRAM_EDGES=(0,0.05,0.1,0.2,0.5,0.8,1.0)

def canonical_bytes(document):
    return (json.dumps(document,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode("utf8")

def read_issue(forecast_path=FORECAST,manifest_path=MANIFEST,generator_path=GENERATOR):
    raw=Path(forecast_path).read_bytes()
    d=json.loads(raw)
    m=json.loads(Path(manifest_path).read_bytes())
    code=Path(generator_path).read_bytes()
    if sha256(raw)!=FROZEN_SHA or sha256(raw)!=m.get("forecast_sha256"):
        raise ValueError("Frozen 2027 probability bytes differ from first public canonical SHA")
    if d.get("forecast_id")!="PSICO-GEO2027-STATEBASED25-V1" or \
       m.get("status")!="ISSUED_PROSPECTIVE_UNRESOLVED" or \
       m.get("outcomes_resolved")!=0 or \
       m.get("demonstrated_predictive_skill") is not False or \
       m.get("first_public_forecast_commit")!="3bb3561c8d6182c30624591276c705fb76ce99dc" or \
       m.get("canonical_document_commit")!="8b924e0b0c7a07e27977160c9658cfed77940aff" or \
       m.get("preregistered_protocol_main_commit")!="87959a117e1b30323392a488c48c9afb1cb0bffc" or \
       not m.get("preregistered_at_utc","")<m.get("first_public_forecast_commit_utc","")<"2027-01-01T00:00:00Z" or \
       sha256(code)!=d.get("provenance",{}).get("generator_sha256") or \
       d.get("target",{}).get("year")!=2027 or d.get("source",{}).get("data_last_year")!=2025:
        raise ValueError("Issued 2027 provenance, original generator or timing not validated")
    if raw!=canonical_bytes(d):
        raise ValueError("Issued document is not byte canonical")
    return raw,d,m,code

def independent_recomputation(records,names):
    """Separate equations and loop structure from the frozen generator code."""
    cohort=sorted(cid for cid,h in records.items() if 2024 in h and 2025 in h)
    if len(cohort)!=EXPECTED_COHORT or set(records)!=set(names):
        raise ValueError("Source country cohort differs from original")
    if any(not h or max(h)>2025 or any(v not in (0,1) for v in h.values())
           for h in records.values()):
        raise ValueError("Future data or invalid state in re-audit")

    global_matrix=[[0,0],[0,0]]
    individual={}
    for cid,h in records.items():
        matrix=[[0,0],[0,0]]
        for year in h:
            if year-1 in h:
                before=h[year-1]; after=h[year]
                matrix[before][after]+=1
                global_matrix[before][after]+=1
        individual[cid]=matrix
    global_active=[
        (matrix[1]+1)/(sum(matrix)+2)
        for matrix in global_matrix
    ]
    last5=[records[cid][y] for cid in cohort for y in range(2021,2026)
           if y in records[cid]]
    if len(last5)!=980:
        raise ValueError("2021–2025 cohort exposure changed")
    baseline=(sum(last5)+1)/(len(last5)+2)
    out=[]
    for cid in cohort:
        transition=individual[cid]
        q=[(transition[s][1]+20*global_active[s])/(sum(transition[s])+20)
           for s in range(2)]
        previous_state=records[cid][2025]
        p2026=q[previous_state]
        p2027=(1-p2026)*q[0]+p2026*q[1]
        p_global_2026=global_active[previous_state]
        p_global_2027=(1-p_global_2026)*global_active[0]+p_global_2026*global_active[1]
        out.append({
            "country_id":cid,
            "country":names[cid],
            "last_observed_state_2025":previous_state,
            "p_model":round(p2027,12),
            "p_global_markov":round(p_global_2027,12),
            "p_baseline_global_5y":round(baseline,12),
        })
    return out,global_matrix,sum(last5)

def report(official_zip, frozen_raw, forecast, manifest, generator):
    if sha256(official_zip)!=PINNED_SOURCE_SHA256:
        raise ValueError("Pinned official UCDP 26.1 source ZIP changed")
    # Replicate original algorithm exactly (byte-for-byte document verification).
    reproduced=build_forecast(official_zip,generator)
    if canonical_bytes(reproduced)!=frozen_raw:
        raise ValueError("Original preregistered generator cannot reproduce the public forecast")
    # Independently re-implement probabilities from the public country-year panel.
    records,names=parse_public_source(read_zip(official_zip))
    manual,matrix,positives=independent_recomputation(records,names)
    published=forecast["countries"]
    if manual!=published or matrix!=forecast["training_summary"]["global_transition_counts"] or \
       positives!=forecast["training_summary"]["global_5y_positive"]:
        raise ValueError("Independent Markov transition/probability reconstruction mismatch")
    if len(published)!=196 or manifest["issued_country_count"]!=196:
        raise ValueError("Frozen forecast cohort unexpectedly changed")
    probs=sorted(row["p_model"] for row in published)
    summed={key:round(sum(row[key] for row in published),9)
            for key in ("p_model","p_global_markov","p_baseline_global_5y")}
    histogram=[
        {"range":[HISTOGRAM_EDGES[i],HISTOGRAM_EDGES[i+1]],
         "countries":sum(HISTOGRAM_EDGES[i]<=p<HISTOGRAM_EDGES[i+1] for p in probs)}
        for i in range(len(HISTOGRAM_EDGES)-1)
    ]
    if sum(x["countries"] for x in histogram)!=196:
        raise ValueError("Probability histogram omitted frozen countries")
    return {
        "schema":"idealab.psico.forecast_2027_frozen_audit.v1",
        "forecast_id":forecast["forecast_id"],
        "status":"PRE_OUTCOME_PROBABILITY_REPRODUCIBILITY_AUDIT",
        "method":"BYTE_EXACT_PREREGISTERED_GENERATOR_PLUS_SEPARATE_FORMULA_RECONSTRUCTION",
        "source_zip_sha256":PINNED_SOURCE_SHA256,
        "forecast_file_sha256":FROZEN_SHA,
        "first_public_forecast_commit":manifest["first_public_forecast_commit"],
        "canonical_document_commit":manifest["canonical_document_commit"],
        "preregistered_protocol_commit":manifest["preregistered_protocol_main_commit"],
        "training_last_year":2025,
        "target_year":2027,
        "countries":len(published),
        "active_state_countries_in_2025":sum(row["last_observed_state_2025"] for row in published),
        "inactive_state_countries_in_2025":sum(1-row["last_observed_state_2025"] for row in published),
        "distinct_model_probabilities":len(set(probs)),
        "model_probability_min":probs[0],
        "model_probability_max":probs[-1],
        "model_probability_median":(probs[97]+probs[98])/2,
        "model_expected_positive_countries":summed["p_model"],
        "global_markov_expected_positive_countries":summed["p_global_markov"],
        "global_5y_expected_positive_countries":summed["p_baseline_global_5y"],
        "model_histogram":histogram,
        "resolution_count":0,
        "forecast_skill_demonstrated":False,
        "not_an_outcome":"These are sums and distributions of probabilities issued in 2026, not actual 2027 conflict outcomes. Source 26.1 contains only observations to 2025; no 2026/2027 events were used."
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-zip",help="Use hash-pinned ZIP already downloaded instead of refetching")
    ap.add_argument("--check-report",help="Compare candidate aggregate report against committed JSON")
    args=ap.parse_args()
    frozen,d,m,code=read_issue()
    source=Path(args.source_zip).read_bytes() if args.source_zip else download_official()
    audit=report(source,frozen,d,m,code)
    rendered=(json.dumps(audit,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf8")
    if args.check_report and rendered!=Path(args.check_report).read_bytes():
        raise ValueError("Published pre-outcome audit does not exactly match official source recomputation")
    print("GEO2027_FROZEN_AUDIT_OK",sha256(rendered),"cohort",audit["countries"],
          "expected_positive_countries",audit["model_expected_positive_countries"])
    print("GEO2027_AUDIT_REPORT_BEGIN")
    print(rendered.decode("utf8"),end="")
    print("GEO2027_AUDIT_REPORT_END")

if __name__=="__main__":
    main()
