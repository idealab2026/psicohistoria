#!/usr/bin/env python3
"""Verify frozen FIN-DIC2026 bytes without refetching mutable input."""
import hashlib,json
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]
CANDIDATE="data/forecast-fin-dic2026.json"
MANIFEST="data/forecast-fin-dic2026-manifest.json"
EXPECTED="ff8cd766d67b2f1f124c540c4941a7b6b534bdda7b5bc97ac63218a439a63f6a"
def run():
    raw=(ROOT/CANDIDATE).read_bytes()
    m=json.loads((ROOT/MANIFEST).read_bytes());d=json.loads(raw)
    if hashlib.sha256(raw).hexdigest()!=EXPECTED or m["candidate_sha256"]!=EXPECTED:
        raise ValueError("Frozen candidate changed")
    if m["candidate_file"]!=CANDIDATE or m["protocol_commit"]!=d["protocol_commit"]:
        raise ValueError("Manifest candidate mismatch")
    if m["status"]!="ISSUED_EXPERIMENTAL_UNRESOLVED" or m["independently_notarized"] or m["outcomes_resolved"]!=0 or m["demonstrated_predictive_skill"]:
        raise ValueError("Unsupported issuance state")
    deadline=datetime.fromisoformat(d["publication_deadline_utc"].replace("Z","+00:00"))
    a,b=[datetime.fromisoformat(m[k].replace("Z","+00:00")) for k in ("first_public_candidate_at_utc","document_published_at_utc")]
    if not a<=b<deadline or m["publication_deadline_utc"]!=d["publication_deadline_utc"]:
        raise ValueError("Publication chronology invalid")
    if m["first_document_commit"]!="6f3e2e35a394305356a433298955845005591f0c" or m["candidate_run_id"]!="46019614340" or m["candidate_run_head"]!="7bb953cae2462f1dd163a3895cc99e1439ddcc8a":
        raise ValueError("Recorded evidence changed")
    if d["target_month"]!="2026-12" or d["feature_last_month"]!="2026-09" or d["feature_lag_months"]!=3 or d["previous_forecasts_modified"]!=0:
        raise ValueError("Candidate scope changed")
    print("FIN-DIC2026 immutable candidate verified",EXPECTED)
if __name__=="__main__": run()
