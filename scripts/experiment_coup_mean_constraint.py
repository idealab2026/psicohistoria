#!/usr/bin/env python3
"""Exploratory intercept correction, no future outcome access or model selection."""
import json,math,sys
from experiment_coup_rolling_backtest import forecast,run,ROOT
from audit_coup_origin_panel import build,summarize
from experiment_annual_ged_rolling_probability import score
from experiment_candidate_monthly_alert_value import rounded
def sigmoid(x):
    return 1/(1+math.exp(-x)) if x>=0 else math.exp(x)/(1+math.exp(x))
def constrain(p,target):
    if not p or not 0<target<1 or any(not 0<x<1 for x in p): raise ValueError("Invalid probabilities")
    logit=[math.log(x)-math.log1p(-x) for x in p]
    lo,hi=-60.,60.
    for _ in range(100):
        mid=(lo+hi)/2
        if sum(sigmoid(x+mid) for x in logit)/len(p)<target:lo=mid
        else:hi=mid
    delta=(lo+hi)/2
    # The exact real-valued transform is strictly monotone. Binary64
    # can collapse adjacent inputs into one output or invert them by rounding.
    # Preserve the frozen ordering using minimal representable increments.
    # Identical input floats are always mapped to identical output floats.
    mapped={};previous=None;repairs=0;max_adjustment=0.
    for value in sorted(set(p)):
        ideal=sigmoid(math.log(value)-math.log1p(-value)+delta)
        corrected=ideal
        if previous is not None and corrected<=previous:
            corrected=math.nextafter(previous,math.inf)
            repairs+=1
        adjustment=abs(corrected-ideal)
        if adjustment>1e-14: raise ValueError("Non-negligible rank repair")
        max_adjustment=max(max_adjustment,adjustment)
        mapped[value]=corrected;previous=corrected
    out=[mapped[x] for x in p]
    if abs(sum(out)/len(out)-target)>1e-12 or any(not 0<x<1 for x in out): raise ValueError("Mean constraint failed")
    ordered=sorted(set(zip(p,out)))
    if any(a>=b or x>=y for (a,x),(b,y) in zip(ordered,ordered[1:])): raise ValueError("Ranking or ties changed")
    return out,delta,{"repaired_distinct_values":repairs,"max_adjustment":max_adjustment}
def evaluate(rows):
    names=("global_recent","country_history","country_constrained","prior5_group","prior5_constrained")
    allp={m:[] for m in names};labels=[];folds=[]
    for y in range(1980,2025):
        test,p=forecast(rows,y);obs=[x[2] for x in test];labels+=obs
        g=[x[1] for x in p];c=[x[2] for x in p];r=[x[3] for x in p]
        cc,dc,rc=constrain(c,g[0]);rr,dr,rrp=constrain(r,g[0])
        probs=dict(zip(names,(g,c,cc,r,rr)))
        scores={m:score(v,obs) for m,v in probs.items()}
        for m,v in probs.items():allp[m]+=v
        folds.append({"year":y,"n":len(obs),"positives":sum(obs),"scores":scores,
            "country_intercept":dc,"prior5_intercept":dr,"country_numeric_repair":{**rc,"max_adjustment":format(rc["max_adjustment"],".17g")},"prior5_numeric_repair":{**rrp,"max_adjustment":format(rrp["max_adjustment"],".17g")}})
    base=score(allp["global_recent"],labels);results={};n=len(labels)
    for m in names:
        s=score(allp[m],labels)
        diffs=[(x["n"],x["scores"]["global_recent"]["brier"]-x["scores"][m]["brier"]) for x in folds]
        gain=sum(k*d for k,d in diffs)
        loo=[(gain-k*d)/(n-k) for k,d in diffs]
        results[m]={**s,"mean_probability":sum(allp[m])/n,"brier_skill_vs_recent":1-s["brier"]/base["brier"],
            "log_loss_gain_vs_recent":base["log_loss"]-s["log_loss"],"positive_brier_gain_years":sum(d>0 for k,d in diffs),
            "leave_one_year_out_gain_min":min(loo),"leave_one_year_out_gain_max":max(loo)}
    return rounded({"status":"EXPLORATORY_POST_BENCHMARK_NOT_INDEPENDENT_TEST","n":n,"positives":sum(labels),
        "observed_rate":sum(labels)/n,"models":results,"folds":folds,"ranking_unchanged":True,
        "new_forecasts":0,"modified_forecasts":0})
def main():
    p,d=build()
    if summarize(p,d)!=json.loads((ROOT/"data/coup-origin-panel.json").read_text()): raise ValueError("Panel changed")
    if any(u!=v for y,c,u,v in p): raise ValueError("Label equality changed")
    rows=[(y,c,u) for y,c,u,v in p]
    frozen=json.loads((ROOT/"data/coup-rolling-backtest.json").read_text())
    if run(rows)!=frozen["results"]: raise ValueError("Original benchmark changed")
    result=evaluate(rows)
    if "--check" in sys.argv and result!=json.loads((ROOT/"data/coup-mean-constraint.json").read_text()): raise ValueError("Frozen constraint diagnostic mismatch")
    print("COUP_CONSTRAINT_BEGIN",flush=True)
    raw=json.dumps(result,sort_keys=True,separators=(",",":"))
    for i in range(0,len(raw),4000):print(raw[i:i+4000])
    print("COUP_CONSTRAINT_END",flush=True)
if __name__=="__main__":main()
