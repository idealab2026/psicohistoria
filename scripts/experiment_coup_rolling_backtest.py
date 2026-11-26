#!/usr/bin/env python3
"""Four fixed retrospective COUP models, never a prospective issue."""
import json,sys
from collections import defaultdict
from audit_coup_origin_panel import build,summarize,ROOT
from experiment_annual_ged_rolling_probability import score
from experiment_candidate_monthly_alert_value import alert,pooled,rounded,BUDGETS
MODELS=("global_all","global_recent","country_history","prior5_group")
def rate(rows): return (1+sum(v for _,_,v in rows))/(2+len(rows))
def make_index(rows):
    byyear=defaultdict(list);bycountry=defaultdict(dict)
    for y,c,v in rows:
        if v not in (0,1) or y in bycountry[c]: raise ValueError("Invalid or duplicate label")
        byyear[y].append((y,c,v));bycountry[c][y]=v
    return byyear,bycountry
def flag(hist,c,y):
    prior=[hist[c][a] for a in range(y-6,y-1) if a in hist[c]]
    return int(any(prior)) if prior else None
def forecast(rows,origin):
    byyear,hist=make_index(rows)
    train=[x for x in rows if x[0]<=origin-2]
    recent=[x for x in train if x[0]>=origin-6]
    test=sorted(byyear[origin],key=lambda x:x[1])
    if not train or not recent or not test: raise ValueError("Incomplete origin")
    g=rate(train);r=rate(recent)
    counts=defaultdict(lambda:[0,0]);groups=defaultdict(lambda:[0,0])
    for y,c,v in train:
        counts[c][0]+=1;counts[c][1]+=v
        if y>=1956:
            z=flag(hist,c,y)
            if z is not None: groups[z][0]+=1;groups[z][1]+=v
    def shrink(pair):
        n,k=pair;return (k+20*r)/(n+20)
    pred=[]
    for y,c,v in test:
        z=flag(hist,c,origin)
        pred.append((g,r,shrink(counts[c]),r if z is None else shrink(groups[z])))
    return test,pred
def run(rows,origins=tuple(range(1980,2025))):
    folds=[];allp={m:[] for m in MODELS};ally=[];allalerts={m:{k:[] for k in BUDGETS} for m in MODELS}
    for y in origins:
        test,p=forecast(rows,y);labels=[x[2] for x in test];ally.extend(labels)
        scores={};alerts={}
        for i,m in enumerate(MODELS):
            v=[x[i] for x in p];allp[m]+=v;scores[m]=score(v,labels)
            alerts[m]={}
            for k in BUDGETS:
                a=alert(v,labels,k);allalerts[m][k].append(a)
                alerts[m][str(k)]={key:a[key] for key in ("expected_hits","minimum_hits","maximum_hits","random_expected_hits","tied_at_cutoff","slots_in_tie")}
        b=scores["global_recent"]
        folds.append({"year":y,"n":len(labels),"positives":sum(labels),"scores":scores,
            "primary_brier_gain":b["brier"]-scores["country_history"]["brier"],
            "primary_log_loss_gain":b["log_loss"]-scores["country_history"]["log_loss"],"alerts":alerts})
    base=score(allp["global_recent"],ally)
    summary={}
    for m in MODELS:
        s=score(allp[m],ally)
        summary[m]={**s,"brier_skill_vs_recent":1-s["brier"]/base["brier"],
            "log_loss_gain_vs_recent":base["log_loss"]-s["log_loss"],
            "mean_probability":sum(allp[m])/len(ally),
            "alerts":{str(k):pooled(allalerts[m][k]) for k in BUDGETS}}
    total=sum(x["n"]*x["primary_brier_gain"] for x in folds);n=len(ally)
    loo=[(total-x["n"]*x["primary_brier_gain"])/(n-x["n"]) for x in folds if n>x["n"]]
    return rounded({"n":n,"positives":sum(ally),"years":len(folds),"models":summary,"folds":folds,
        "primary":{"brier_gain":total/n,"positive_gain_years":sum(x["primary_brier_gain"]>0 for x in folds),
            "negative_gain_years":sum(x["primary_brier_gain"]<0 for x in folds),
            "zero_gain_years":sum(x["primary_brier_gain"]==0 for x in folds),
            "leave_one_year_out_gain_min":min(loo) if loo else None,"leave_one_year_out_gain_max":max(loo) if loo else None}})
def report():
    p,d=build()
    if summarize(p,d)!=json.loads((ROOT/"data/coup-origin-panel.json").read_text()):
        raise ValueError("Frozen panel does not reproduce")
    a=run([(y,c,u) for y,c,u,v in p]);b=run([(y,c,v) for y,c,u,v in p])
    if a["n"]!=8241 or a["positives"]!=186 or a["years"]!=45 or a!=b:
        raise ValueError("Unexpected evaluation denominators or label equality")
    return {"status":"RETROSPECTIVE_NOT_ASOF_NOT_PROSPECTIVE","strict_relaxed_equal":True,
        "identical_labels_not_independent_replication":True,"results":a,
        "new_forecasts":0,"modified_forecasts":0}
if __name__=="__main__":
    d=report()
    if "--check" in sys.argv and d!=json.loads((ROOT/"data/coup-rolling-backtest.json").read_text()):
        raise ValueError("Frozen backtest mismatch")
    print("COUP_BACKTEST_BEGIN",flush=True)
    raw=json.dumps(d,sort_keys=True,separators=(",",":"))
    for i in range(0,len(raw),4000): print(raw[i:i+4000])
    print("COUP_BACKTEST_END",flush=True)
