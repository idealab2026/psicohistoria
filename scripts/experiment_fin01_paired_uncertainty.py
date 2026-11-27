#!/usr/bin/env python3
"""Exploratory paired circular year-block bootstrap; no source downloads."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
YEARS=range(1990,2025)
N=35
DRAWS=20000
SEED=27012026
PAIRS=(
 ("downside_joint_recent","downside","joint_regime","recent","brier"),
 ("downside_joint_global","downside","joint_regime","global","brier"),
 ("downside_vol_recent","downside","vol_regime","recent","brier"),
 ("har_qlike","volatility","har_proxy","trailing12","qlike"),
 ("har_mae","volatility","har_proxy","trailing12","volatility_mae"),
 ("ewma_qlike","volatility","ewma94","trailing12","qlike"),
 ("ewma_mae","volatility","ewma94","trailing12","volatility_mae"),
)
# Independent JS execution on the frozen annual reports, 2026-11-27.
# Expected 3-year block percentile bounds, rounded to 12 decimals.
EXPECTED={
 "downside_joint_recent":(-.029467144870,.070922703444),
 "downside_joint_global":(-.023188437828,.043906747923),
 "downside_vol_recent":(-.043613619365,.050851067807),
 "har_qlike":(-.092766465514,.170405605439),
 "har_mae":(.022432422180,.168577539457),
 "ewma_qlike":(-.209952893044,.167291800614),
 "ewma_mae":(-.189673030583,.060137782505),
}
def run():
    reports={k:json.loads((ROOT/path).read_text())["results"] for k,path in
             (("downside","data/fin01-monthly-downside.json"),("volatility","data/fin01-volatility.json"))}
    pairs={};result={}
    for name,key,model,base,metric in PAIRS:
        report=reports[key];a=[]
        for year in YEARS:
            row=report["years"][str(year)]
            if row["n"]!=12: raise ValueError("Unexpected year coverage")
            a.append((row["models"][base][metric],row["models"][model][metric]))
        point=1-sum(x[1] for x in a)/sum(x[0] for x in a)
        check=1-report["models"][model][metric]/report["models"][base][metric]
        if abs(point-check)>1e-12: raise ValueError("Pooled score reconciliation failed")
        pairs[name]=a;result[name]={"point":round(point,12),"blocks":{}}
    for length in (1,3,5):
        state=SEED;sims={name:[] for name in pairs}
        for _ in range(DRAWS):
            idx=[]
            while len(idx)<N:
                state=(1664525*state+1013904223)&0xffffffff
                start=(state*N)//2**32
                idx.extend((start+j)%N for j in range(min(length,N-len(idx))))
            for name,a in pairs.items():
                ref=sum(a[j][0] for j in idx);model=sum(a[j][1] for j in idx)
                sims[name].append(1-model/ref)
        for name,z in sims.items():
            z.sort()
            bounds=[round(z[499],12),round(z[19499],12)]
            if length==3 and any(abs(a-b)>1e-10 for a,b in zip(bounds,EXPECTED[name])):
                raise ValueError("Independent numerical replay mismatch")
            result[name]["blocks"][str(length)]={"interval":bounds,"positive_fraction":sum(x>0 for x in z)/DRAWS}
    return {"status":"EXPLORATORY_PAIRED_YEAR_BLOCK_BOOTSTRAP_NOT_INDEPENDENT",
            "n_years":N,"draws_per_block_length":DRAWS,"seed":SEED,"comparisons":result,
            "new_forecasts":0,"modified_forecasts":0}
if __name__=="__main__":
    print(json.dumps(run(),sort_keys=True,indent=2,allow_nan=False))
