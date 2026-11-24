#!/usr/bin/env python3
"""DEC2026 pilot generator; deterministic candidate bytes, not issuance evidence."""
import hashlib
import json
import sys
from datetime import date,datetime,timezone,timedelta
from pathlib import Path
from audit_candidate_october_source_observation import replay_monthly,START,END
from audit_candidate_monthly_bridge import build,check_report,THRESHOLDS
from experiment_candidate_monthly_probability import evaluate,validate_panel
from experiment_candidate_monthly_complementary_signals import run,extended_predict,MODELS
ROOT=Path(__file__).resolve().parents[1]
TARGET=date(2026,12,1)
DEADLINE=datetime(2026,12,1,tzinfo=timezone.utc)
OBS=datetime.fromisoformat("2026-11-24T19:20:07.692599+00:00")
TRAIN=(2021,2022,2023)
def time_gate(now):
    if now.tzinfo is None or not OBS<now<DEADLINE:
        raise ValueError("Candidate generation outside preregistered observation/publication interval")
def recent_features(events,ids):
    q=dict.fromkeys(ids,0); other=dict.fromkeys(ids,0)
    for c,t,p,b,start,end in events.values():
        if c in q and p in (1,2) and START<=start<=end<=END:
            (q if t==1 else other)[c]+=b
    return q,other
def generate(panel,other,q,new_other,manifest):
    validate_panel(panel)
    ids={x[1] for x in panel}
    if set(q)!=ids or set(new_other)!=ids or any(type(v) is not int or v<0 for v in (*q.values(),*new_other.values())):
        raise ValueError("Invalid complete prospective universe/features")
    if set(other)!={(x[0],x[1]) for x in panel}: raise ValueError("Historical other feature incomplete")
    combined={**other,**{(2026,c):n for c,n in new_other.items()}}
    cells=[]
    for t in THRESHOLDS:
        for h in (30,90):
            train=[x for x in panel if x[0] in TRAIN and x[2]<t]
            if {x[0] for x in train}!=set(TRAIN): raise ValueError("Training cohort incomplete")
            test=[(2026,c,q[c],None,None) for c in sorted(ids) if q[c]<t]
            p=extended_predict(train,test,combined,2026,t,h)
            by_id={x[1]:dict(zip(MODELS,[round(v,12) for v in probs])) for x,probs in zip(test,p)}
            if any(not 0<v<1 for probs in by_id.values() for v in probs.values()):
                raise ValueError("Invalid serialized probability")
            cells.append({"threshold":t,"horizon":h,"target_start":TARGET.isoformat(),
                "target_end":(TARGET+timedelta(days=h-1)).isoformat(),"n_train":len(train),
                "n_eligible":len(test),"countries":[{"country_id":c,"eligible":c in by_id,
                   "probabilities":by_id.get(c)} for c in sorted(ids)]})
    return {"schema":"idealab.psico.dec2026.pilot.v1","status":"CANDIDATE_REQUIRES_PUBLICATION_EVIDENCE",
        "source_manifest":manifest,"feature_start":START.isoformat(),"feature_end":END.isoformat(),
        "training_years":list(TRAIN),"models":list(MODELS),
        "primary_probability":{"threshold":10,"horizon":90,"model":"pool_three","control":"global"},
        "primary_ranking":{"threshold":10,"horizon":90,"model":"country_history","budget":5,"control":"random"},
        "publication_deadline_utc":DEADLINE.isoformat(),"cells":cells,
        "previous_forecasts_modified":0,"outcomes_resolved":0,"demonstrated_predictive_skill":False}
def main():
    # Deliberately no normal CI issuance. Explicit run only after protocol merge.
    if sys.argv[1:]!=["--candidate"]: raise ValueError("Explicit candidate mode required")
    time_gate(datetime.now(timezone.utc))
    frozen,events,ids=replay_monthly(include_events=True)
    bridge,panel,other=build(include_panel=True,include_other=True)
    check_report(bridge)
    for name,value in (("candidate-monthly-probability",evaluate(panel)),
                       ("candidate-monthly-complementary-signals",run(panel,other))):
        if value!=json.loads((ROOT/"data"/(name+".json")).read_text()):
            raise ValueError("Historical benchmark does not reproduce")
    q,o=recent_features(events,ids)
    candidate=generate(panel,other,q,o,frozen["source_manifest"])
    time_gate(datetime.now(timezone.utc))
    raw=(json.dumps(candidate,sort_keys=True,separators=(",",":"))+"\n").encode()
    print("CANDIDATE_SHA256 "+hashlib.sha256(raw).hexdigest())
    print("CANDIDATE_BEGIN")
    payload=raw.decode().rstrip("\n")
    for i in range(0,len(payload),4000):
        print(payload[i:i+4000])
    print("CANDIDATE_END")
if __name__=="__main__": main()
