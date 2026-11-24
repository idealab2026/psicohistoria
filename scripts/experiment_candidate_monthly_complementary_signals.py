#!/usr/bin/env python3
"""Fixed complementary signals; exploratory retrospective only."""
import json
import sys
from pathlib import Path
from audit_candidate_monthly_bridge import build,check_report,THRESHOLDS
from experiment_candidate_monthly_probability import evaluate,validate_panel
from experiment_annual_ged_rolling_probability import predict,score
ROOT=Path(__file__).resolve().parents[1]
MODELS=("global","q1_nonzero","country_history","pool_two","other_violence","pool_three")
def extended_predict(train,test,other,origin,t,h):
    base=predict(train,test,origin,t,h)
    col=3 if h==30 else 4
    out=[]
    for x,(g,q,c) in zip(test,base):
        z=other[(x[0],x[1])]>0
        sub=[v for v in train if (other[(v[0],v[1])]>0)==z]
        o=(sum(v[col]>=t for v in sub)+20*g)/(len(sub)+20)
        out.append((g,q,c,(q+c)/2,o,(q+c+o)/3))
    return out
def metrics(p,y):
    raw={m:score([v[i] for v in p],y) for i,m in enumerate(MODELS)}
    b=raw["global"]["brier"]; q=raw["q1_nonzero"]
    result={}
    for i,m in enumerate(MODELS):
        d=raw[m]
        means={}
        for label,name in ((0,"negative"),(1,"positive")):
            v=[x[i] for x,k in zip(p,y) if k==label]
            means[name]=round(sum(v)/len(v),9) if v else None
        result[m]={**{k:round(v,9) for k,v in d.items()},
            "brier_skill_vs_global":round(1-d["brier"]/b,9),
            "brier_gain_vs_q1":round(q["brier"]-d["brier"],9),
            "log_loss_gain_vs_q1":round(q["log_loss"]-d["log_loss"],9),
            "mean_probability_by_outcome":means}
    return result
def run(panel,other):
    validate_panel(panel)
    if set(other)!={(x[0],x[1]) for x in panel} or any(type(v) is not int or v<0 for v in other.values()):
        raise ValueError("Missing or invalid other-violence feature")
    results=[]
    for t in THRESHOLDS:
        for h in (30,90):
            col=3 if h==30 else 4
            folds=[]; pooled=[]; labels=[]
            for origin,years in ((2023,(2021,)),(2025,(2021,2022,2023))):
                train=[x for x in panel if x[0] in years and x[2]<t]
                test=[x for x in panel if x[0]==origin and x[2]<t]
                p=extended_predict(train,test,other,origin,t,h)
                y=[int(x[col]>=t) for x in test]
                folds.append({"origin":origin,"train_years":list(years),"n":len(y),
                    "positives":sum(y),"scores":metrics(p,y)})
                pooled+=p; labels+=y
            results.append({"threshold":t,"horizon":h,"n":len(labels),"positives":sum(labels),
                "folds":folds,"scores":metrics(pooled,labels)})
    return {"status":"EXPLORATORY_FIXED_SIGNAL_POOL_NOT_ASOF_NOT_ISSUED",
        "new_forecasts":0,"modified_forecasts":0,"results":results}
def main():
    bridge,panel,other=build(include_panel=True,include_other=True)
    check_report(bridge)
    previous=json.loads((ROOT/"data/candidate-monthly-probability.json").read_text())
    if evaluate(panel)!=previous:
        raise ValueError("Previous monthly benchmark does not replay")
    result=run(panel,other)
    if "--check" in sys.argv and result!=json.loads((ROOT/"data/candidate-monthly-complementary-signals.json").read_text()):
        raise ValueError("Frozen signal pool report mismatch")
    print("SIGNAL_POOL_BEGIN")
    print(json.dumps(result,sort_keys=True,indent=2))
    print("SIGNAL_POOL_END")
if __name__=="__main__": main()
