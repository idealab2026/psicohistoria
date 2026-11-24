#!/usr/bin/env python3
"""Conservative retrospective rolling-origin probability benchmark, not as-of certified."""
import hashlib
import json
import math
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
 "candidate-ged-2021-22-resolution.json":"3b2576bae226251aa9a0fc4582cd4b5a185185662a1c04646bb7254d04caa1b0",
 "candidate-to-annual-ged-resolution.json":"01e59980294c67115e1253b52cd9595d9389e59c2bd003ee8bb747cd433a4db4",
}
YEARS=(2021,2022,2024,2025)
MODELS=("global","q1_nonzero","country_history")
def load():
    rows=[]
    for idx,(name,sha) in enumerate(SOURCES.items()):
        raw=(ROOT/"data"/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sha:
            raise ValueError("Source SHA mismatch")
        d=json.loads(raw)
        for x in d["country_vectors_new" if idx==0 else "country_vectors"]:
            q=x["q1_candidate_best" if idx==0 else "candidate_q1_prior_best"]
            a=x["annual_ged_may30_best" if idx==0 else "ged_annual_may30_best"]
            b=x["annual_ged_may90_best" if idx==0 else "ged_annual_90_best"]
            if any(type(v) is not int or v<0 for v in (q,a,b)) or a>b:
                raise ValueError("Invalid counts or nested windows")
            if x["year"] not in ((2021,2022) if idx==0 else (2024,2025)):
                raise ValueError("Source year mismatch")
            rows.append((x["year"],x["country_id"],q,a,b))
    return rows
def validate(rows):
    if len(rows)!=784 or len({(x[0],x[1]) for x in rows})!=784:
        raise ValueError("Invalid panel size/duplicates")
    ids=[{x[1] for x in rows if x[0]==y} for y in YEARS]
    if len(ids[0])!=196 or any(i!=ids[0] for i in ids):
        raise ValueError("Unequal country universes")
def predict(train,test,origin,threshold,h):
    if not train or any(x[0]>origin-2 or x[2]>=threshold for x in train):
        raise ValueError("Temporal leakage or invalid training risk set")
    if any(x[0]!=origin or x[2]>=threshold for x in test):
        raise ValueError("Invalid test risk set")
    col=3 if h==30 else 4
    g=(1+sum(x[col]>=threshold for x in train))/(len(train)+2)
    def shrink(sub):
        return (sum(x[col]>=threshold for x in sub)+20*g)/(len(sub)+20)
    return [(g,shrink([z for z in train if (z[2]>0)==(x[2]>0)]),
             shrink([z for z in train if z[1]==x[1]])) for x in test]
def score(pred,y):
    if not y or len(pred)!=len(y) or any(not 0<p<1 for p in pred):
        raise ValueError("Invalid probability vector")
    return {"brier":sum((p-v)**2 for p,v in zip(pred,y))/len(y),
            "log_loss":-sum(v*math.log(p)+(1-v)*math.log1p(-p) for p,v in zip(pred,y))/len(y)}
def summary(pred,y):
    s={m:score([p[i] for p in pred],y) for i,m in enumerate(MODELS)}
    base=s["global"]["brier"]
    return {m:{**{k:round(v,9) for k,v in vals.items()},
               "brier_skill_vs_global":round(1-vals["brier"]/base,9)} for m,vals in s.items()}
def decompose_q1_gain(pred,y):
    """Post-outcome descriptive attribution; not a training input."""
    n=len(y)
    out={}
    for label,name in ((0,"negative"),(1,"positive")):
        subset=[p for p,v in zip(pred,y) if v==label]
        count=len(subset)
        out[name]={
            "n":count,
            "global_mean_probability":round(sum(p[0] for p in subset)/count,9) if count else None,
            "q1_mean_probability":round(sum(p[1] for p in subset)/count,9) if count else None,
            "brier_gain_contribution":round(sum((p[0]-label)**2-(p[1]-label)**2 for p in subset)/n,9)
        }
    return out
def run(rows):
    validate(rows)
    results=[]
    for t in (1,5,10,25):
        for h in (30,90):
            folds=[]; allp=[]; ally=[]
            for origin in (2024,2025):
                train=[x for x in rows if x[0]<=origin-2 and x[2]<t]
                test=[x for x in rows if x[0]==origin and x[2]<t]
                if set(x[0] for x in train)!={2021,2022}:
                    raise ValueError("Unexpected historical training years")
                p=predict(train,test,origin,t,h)
                col=3 if h==30 else 4
                y=[int(x[col]>=t) for x in test]
                folds.append({"origin":origin,"train_years":[2021,2022],"n_train":len(train),
                    "n_test":len(test),"positives":sum(y),"scores":summary(p,y)})
                allp+=p; ally+=y
            results.append({"threshold":t,"horizon":h,"folds":folds,"n_test":len(ally),
                 "positives":sum(ally),"scores":summary(allp,ally),
                 "q1_brier_gain_by_outcome":decompose_q1_gain(allp,ally)})
    return {"status":"RETROSPECTIVE_NOT_ASOF_NOT_PROSPECTIVE","source_sha256":SOURCES,
             "new_forecasts":0,"modified_prior_forecasts":0,"results":results}
if __name__=="__main__":
    result=run(load())
    if "--check" in sys.argv:
        expected=json.loads((ROOT/"data/annual-ged-rolling-probability.json").read_text())
        if result!=expected: raise ValueError("Frozen report mismatch")
        print("OK: exact replay of eight temporal benchmark cells")
    else: print(json.dumps(result,indent=2,sort_keys=True))
