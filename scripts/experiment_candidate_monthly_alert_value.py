#!/usr/bin/env python3
"""Tie-safe historical alert budgets, not a prospective evaluation."""
import json
import math
import sys
from pathlib import Path
from audit_candidate_monthly_bridge import build,check_report,THRESHOLDS
from experiment_candidate_monthly_probability import evaluate
from experiment_candidate_monthly_complementary_signals import run,extended_predict,MODELS
ROOT=Path(__file__).resolve().parents[1]
BUDGETS=(5,10,20)
def hit_probability(n,p,k):
    if not 0<=p<=n or not 0<=k<=n: raise ValueError("Invalid hypergeometric parameters")
    if k>n-p: return 1.0
    return 1-math.comb(n-p,k)/math.comb(n,k)
def alert(prob,y,k):
    n=len(y)
    if len(prob)!=n or not 0<k<=n or any(v not in (0,1) for v in y) or any(not 0<v<1 for v in prob):
        raise ValueError("Invalid alert inputs")
    cutoff=sorted(prob,reverse=True)[k-1]
    top=[v for p,v in zip(prob,y) if p>cutoff]
    tied=[v for p,v in zip(prob,y) if p==cutoff]
    slots=k-len(top)
    a,b=sum(top),sum(tied)
    hits=a+slots*b/len(tied)
    positives=sum(y); random=k*positives/n
    return {"n":n,"positives":positives,"budget":k,"strictly_above":len(top),
        "tied_at_cutoff":len(tied),"slots_in_tie":slots,
        "expected_hits":hits,"minimum_hits":a+max(0,slots-(len(tied)-b)),
        "maximum_hits":a+min(slots,b),"precision":hits/k,
        "recall":hits/positives if positives else None,
        "random_expected_hits":random,"lift":hits/random if random else None,
        "probability_at_least_one_hit":1.0 if a else hit_probability(len(tied),b,slots),
        "random_probability_at_least_one_hit":hit_probability(n,positives,k)}
def pooled(folds):
    n=sum(x["n"] for x in folds); p=sum(x["positives"] for x in folds)
    k=sum(x["budget"] for x in folds); hits=sum(x["expected_hits"] for x in folds)
    random=sum(x["random_expected_hits"] for x in folds)
    return {"n":n,"positives":p,"budget":k,"expected_hits":hits,
        "minimum_hits":sum(x["minimum_hits"] for x in folds),
        "maximum_hits":sum(x["maximum_hits"] for x in folds),
        "precision":hits/k,"recall":hits/p if p else None,
        "random_expected_hits":random,"lift":hits/random if random else None}
def rounded(obj):
    if isinstance(obj,float): return round(obj,9)
    if isinstance(obj,list): return [rounded(v) for v in obj]
    if isinstance(obj,dict): return {k:rounded(v) for k,v in obj.items()}
    return obj
def study(panel,other):
    out=[]
    for t in THRESHOLDS:
        for h in (30,90):
            col=3 if h==30 else 4
            data=[]
            for origin,years in ((2023,(2021,)),(2025,(2021,2022,2023))):
                train=[x for x in panel if x[0] in years and x[2]<t]
                test=[x for x in panel if x[0]==origin and x[2]<t]
                pred=extended_predict(train,test,other,origin,t,h)
                data.append((origin,pred,[int(x[col]>=t) for x in test]))
            for k in BUDGETS:
                models={}
                for i,m in enumerate(MODELS):
                    folds=[alert([v[i] for v in pred],y,k) for _,pred,y in data]
                    models[m]={"pooled":pooled(folds),"folds":[{"origin":d[0],**f} for d,f in zip(data,folds)]}
                out.append({"threshold":t,"horizon":h,"budget_per_year":k,"models":models})
    return rounded({"status":"EXPLORATORY_ALERT_VALUE_NOT_ASOF_NOT_ISSUED",
        "new_forecasts":0,"modified_forecasts":0,"results":out})
def main():
    bridge,panel,other=build(include_panel=True,include_other=True)
    check_report(bridge)
    for name,result in (("candidate-monthly-probability",evaluate(panel)),
                        ("candidate-monthly-complementary-signals",run(panel,other))):
        if result!=json.loads((ROOT/"data"/(name+".json")).read_text()):
            raise ValueError("Previous benchmark does not replay: "+name)
    result=study(panel,other)
    if "--check" in sys.argv and result!=json.loads((ROOT/"data/candidate-monthly-alert-value.json").read_text()):
        raise ValueError("Frozen alert report mismatch")
    print("ALERT_VALUE_BEGIN")
    print(json.dumps(result,sort_keys=True,indent=2))
    print("ALERT_VALUE_END")
if __name__=="__main__": main()
