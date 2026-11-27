#!/usr/bin/env python3
"""FIN-DIC2026 candidate, no outcome retrieval or publication attestation."""
import hashlib,json
from datetime import datetime,timezone
from experiment_fin01_monthly_downside import parse,month_index,MODELS
from experiment_fin01_publication_lag import get,LIVE,lag_predict

SOURCE_SHA="b03d39e4bb253dda0f14893db3b78e64b40b8d6549a0fc0fd4111dae84c98618"
SOURCE_BYTES=13078
DEADLINE=datetime(2026,12,1,tzinfo=timezone.utc)

def build(raw,now):
    if now.tzinfo is None or now>=DEADLINE:
        raise ValueError("Candidate generation deadline passed")
    if len(raw)!=SOURCE_BYTES or hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:
        raise ValueError("Source bytes changed; new protocol required")
    values,member=parse(raw,"202609")
    target=month_index("202612")
    if len(values)!=1203 or max(values)!=target-3:
        raise ValueError("Unexpected feature cutoff")
    p=lag_predict(values,target,3)
    if set(p)!=set(MODELS) or not all(0<x<1 for x in p.values()):
        raise ValueError("Invalid probability output")
    return {"schema":"idealab.psico.fin_dic2026.candidate.v1",
            "status":"CANDIDATE_REQUIRES_PUBLICATION_EVIDENCE",
            "target_month":"2026-12","target_start":"2026-12-01",
            "target_end":"2026-12-31","endpoint":"US_BROAD_MARKET_MONTHLY_TOTAL_RETURN_LE_MINUS_5_PERCENT",
            "feature_last_month":"2026-09","feature_lag_months":3,
            "publication_deadline_utc":"2026-12-01T00:00:00Z",
            "primary_model":"vol_regime","primary_reference":"recent",
            "secondary_model":"joint_regime","probabilities":{k:round(p[k],12) for k in MODELS},
            "source":{"url":LIVE,"sha256":SOURCE_SHA,"bytes":SOURCE_BYTES,"csv_member":member},
            "protocol_commit":"2c9aa2237d497788dff677513f4799190ce96bb2",
            "outcomes_resolved":0,"demonstrated_predictive_skill":False,
            "previous_forecasts_modified":0}

def canonical(d):
    return (json.dumps(d,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()

if __name__=="__main__":
    d=build(get(LIVE),datetime.now(timezone.utc))
    raw=canonical(d)
    print("FIN_DIC2026_CANDIDATE_BEGIN",flush=True)
    print(raw.decode().rstrip("\n"))
    print("FIN_DIC2026_CANDIDATE_END",flush=True)
    print("FIN_DIC2026_SHA256="+hashlib.sha256(raw).hexdigest())
