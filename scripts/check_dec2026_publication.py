#!/usr/bin/env python3
"""Structural and temporal audit of an experimental DEC2026 publication receipt.
GitHub server evidence must be independently retrieved and reviewed; local validation
does not notarize timestamps. No network and no outcome access.
"""
import hashlib
import json
import re
import sys
from datetime import datetime,timezone,timedelta
from pathlib import Path
from generate_dec2026_pilot import OBS,DEADLINE,TARGET,TRAIN,MODELS,THRESHOLDS
from experiment_annual_ged_rolling_probability import load,validate
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL="e9ff37ba21f0a4994d6baa347c7f932ea5bf9393"
def moment(s):
    d=datetime.fromisoformat(s.replace("Z","+00:00"))
    if d.tzinfo is None or d.utcoffset()!=timedelta(0): raise ValueError("UTC required")
    return d
def digest(raw): return hashlib.sha256(raw).hexdigest()
def check(raw,receipt,ids,manifest):
    d=json.loads(raw)
    if raw!=(json.dumps(d,sort_keys=True,separators=(",",":"))+"\n").encode():
        raise ValueError("Noncanonical candidate bytes")
    if d["schema"]!="idealab.psico.dec2026.pilot.v1" or d["status"]!="CANDIDATE_REQUIRES_PUBLICATION_EVIDENCE":
        raise ValueError("Unexpected candidate schema or status")
    if d["source_manifest"]!=manifest or d["training_years"]!=list(TRAIN) or d["models"]!=list(MODELS):
        raise ValueError("Changed sources or model specification")
    if d["feature_start"]!="2026-08-01" or d["feature_end"]!="2026-10-31" or moment(d["publication_deadline_utc"])!=DEADLINE:
        raise ValueError("Changed temporal specification")
    if d["primary_probability"]!={"threshold":10,"horizon":90,"model":"pool_three","control":"global"} or d["primary_ranking"]!={"threshold":10,"horizon":90,"model":"country_history","budget":5,"control":"random"}:
        raise ValueError("Changed primary endpoints")
    if d["previous_forecasts_modified"]!=0 or d["outcomes_resolved"]!=0 or d["demonstrated_predictive_skill"] is not False:
        raise ValueError("Unsupported claim")
    cells=d["cells"]
    if [(x["threshold"],x["horizon"]) for x in cells]!=[(t,h) for t in THRESHOLDS for h in (30,90)]:
        raise ValueError("Incomplete scenario grid")
    if len(ids)!=196: raise ValueError("Wrong universe")
    seen={}
    for x in cells:
        t,h=x["threshold"],x["horizon"]
        if x["target_start"]!=TARGET.isoformat() or x["target_end"]!=(TARGET+timedelta(days=h-1)).isoformat():
            raise ValueError("Wrong evaluation window")
        rows=x["countries"]
        if [z["country_id"] for z in rows]!=sorted(ids) or not 0<x["n_train"]<=588:
            raise ValueError("Wrong universe or training size")
        eligible=set()
        for row in rows:
            c=row["country_id"]; p=row["probabilities"]
            if type(row["eligible"]) is not bool: raise ValueError("Invalid eligibility flag")
            if row["eligible"]:
                eligible.add(c)
                if not isinstance(p,dict) or set(p)!=set(MODELS) or any(type(v) not in (int,float) or not 0<v<1 for v in p.values()):
                    raise ValueError("Invalid probability vector")
            elif p is not None: raise ValueError("Excluded country has a probability")
        if len(eligible)!=x["n_eligible"]: raise ValueError("Wrong eligibility count")
        seen[t,h]=eligible
        if h==90 and eligible!=seen[t,30]: raise ValueError("Different risk sets by horizon")
    for a,b in zip(THRESHOLDS,THRESHOLDS[1:]):
        if not seen[a,30]<=seen[b,30]: raise ValueError("Risk sets not nested")
    if receipt["status"]!="ISSUED_EXPERIMENTAL_UNRESOLVED" or receipt["candidate_sha256"]!=digest(raw) or receipt["protocol_main_commit"]!=PROTOCOL:
        raise ValueError("Publication receipt mismatch")
    if receipt["independently_notarized"] is not False or receipt["outcomes_resolved"]!=0 or receipt["demonstrated_predictive_skill"] is not False:
        raise ValueError("Unsupported receipt claim")
    for field in ("candidate_run_head","first_document_commit"):
        if not re.fullmatch("[0-9a-f]{40}",receipt[field]): raise ValueError("Invalid commit")
    if not re.fullmatch("[0-9]+",receipt["candidate_run_id"]): raise ValueError("Invalid run")
    first=moment(receipt["first_public_candidate_at_utc"])
    published=moment(receipt["document_published_at_utc"])
    if not OBS<first<=published<DEADLINE:
        raise ValueError("Publication outside prospective interval")
    return {"status":"STRUCTURAL_AND_DECLARED_CHRONOLOGY_OK","eligible_country_scenarios":sum(len(v) for v in seen.values()),
        "probability_values":sum(len(v) for v in seen.values())*len(MODELS),"sha256":digest(raw),
        "independent_timestamp_verification":False}
if __name__=="__main__":
    rows=load();validate(rows)
    raw=(ROOT/"data/forecast-dec2026-pilot.json").read_bytes()
    receipt=json.loads((ROOT/"data/forecast-dec2026-pilot-manifest.json").read_text())
    source=json.loads((ROOT/"data/candidate-october-2026-source-observation.json").read_text())
    print(json.dumps(check(raw,receipt,{x[1] for x in rows},source["source_manifest"]),sort_keys=True))
