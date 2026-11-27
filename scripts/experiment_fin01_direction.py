#!/usr/bin/env python3
"""FIN-01C fixed monthly return and direction models."""
import hashlib, json, math, statistics, sys
from pathlib import Path
from experiment_fin01_monthly_downside import retrieve,parse,month_index

SHA="fc9e41cc3b66c62fa8f565a01fb4c8c0d7962c777303c46b8ab7102190b98ea2"
MODELS=("global","recent","vol_regime","joint_regime","momentum_regime")
K=24

def features(values,t,lag):
    x=[values[j] for j in range(t-lag-11,t-lag+1)]
    return int(statistics.stdev(x)>=.05),int(math.prod(1+v for v in x[-3:])<1)

def predict(values,t,lag,keys=None):
    if lag not in (2,3): raise ValueError("Unregistered lag")
    start=min(values)
    hist=[values[j] for j in range(start,t-lag+1)]
    if len(hist)<120: raise ValueError("Insufficient history")
    def base(x):
        return {"mean_return":math.fsum(x)/len(x),"p_positive":(sum(v>0 for v in x)+1)/(len(x)+2)}
    out={"global":base(hist),"recent":base(hist[-120:])}
    prior=out["recent"]
    key=features(values,t,lag)
    groups=[[],[],[]]
    for j in range(start+lag+11,t-lag+1):
        k=features(values,j,lag) if keys is None else keys[j]
        for ok,group in zip((k[0]==key[0],k==key,k[1]==key[1]),groups):
            if ok: group.append(values[j])
    for m,x in zip(MODELS[2:],groups):
        n=len(x)+K
        out[m]={"mean_return":(math.fsum(x)+K*prior["mean_return"])/n,
                "p_positive":(sum(v>0 for v in x)+K*prior["p_positive"])/n}
    return out

def summary(rows):
    n=len(rows)
    if n==0: raise ValueError("Empty evaluation")
    models={}
    for m in MODELS:
        e=[];b=[];ll=[]
        for t,y,p in rows:
            a=p[m]["mean_return"];q=p[m]["p_positive"];z=int(y>0)
            if not 0<q<1 or not math.isfinite(a): raise ValueError("Invalid prediction")
            e.append(a-y);b.append((q-z)**2)
            ll.append(-math.log(q) if z else -math.log1p(-q))
        models[m]={"mse":math.fsum(x*x for x in e)/n,"mae":math.fsum(abs(x) for x in e)/n,
                   "brier":math.fsum(b)/n,"log_loss":math.fsum(ll)/n,
                   "mean_predicted_return":math.fsum(p[m]["mean_return"] for t,y,p in rows)/n,
                   "mean_positive_probability":math.fsum(p[m]["p_positive"] for t,y,p in rows)/n}
    for s in models.values():
        for metric in ("mse","brier","log_loss"):
            for ref in ("recent","global"):
                denom=models[ref][metric]
                s[metric+"_skill_vs_"+ref]=1-s[metric]/denom if denom else None
    return {"n":n,"positive_months":sum(y>0 for t,y,p in rows),
            "mean_realized_return":math.fsum(y for t,y,p in rows)/n,
            "zero_return_mse":math.fsum(y*y for t,y,p in rows)/n,
            "coin_flip_brier":.25,"coin_flip_log_loss":math.log(2),"models":models}

def evaluate(values,lag):
    # Precompute only trailing features, never target values.
    keys={j:features(values,j,lag) for j in range(min(values)+lag+11,max(values)+1)}
    rows=[(t,values[t],predict(values,t,lag,keys)) for t in range(month_index("199001"),month_index("202412")+1)]
    d=summary(rows)
    d["periods"]={f"{a}-{b}":summary([row for row in rows if a<=row[0]//12<=b]) for a,b in [(1990,2004),(2005,2014),(2015,2024)]}
    return d

def run():
    raw=retrieve()
    if hashlib.sha256(raw).hexdigest()!=SHA: raise ValueError("Frozen source changed")
    values,member=parse(raw)
    return {"status":"RETROSPECTIVE_REVISED_SOURCE_NOT_ASOF_NOT_PROSPECTIVE",
        "source_sha256":SHA,"source_bytes":len(raw),"csv_member":member,
        "endpoint_direction":"MONTHLY_TOTAL_RETURN_GT_ZERO","endpoint_return":"MONTHLY_TOTAL_RETURN",
        "primary_lag":3,"primary_model":"joint_regime","primary_reference":"recent",
        "results":{str(lag):evaluate(values,lag) for lag in (3,2)},
        "new_forecasts":0,"modified_forecasts":0,"trading_strategies_tested":0}

if __name__=="__main__":
    print("FIN01_DIRECTION_BEGIN",flush=True)
    report=run()
    if "--check" in sys.argv and report!=json.loads((Path(__file__).resolve().parents[1]/"data/fin01-direction.json").read_text()):
        raise ValueError("Frozen direction benchmark differs")
    print(json.dumps(report,sort_keys=True,indent=2,allow_nan=False))
    print("FIN01_DIRECTION_END",flush=True)
