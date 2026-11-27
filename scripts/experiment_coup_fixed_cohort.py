#!/usr/bin/env python3
"""Historical fixed-roster sensitivity, missing-label bounds, no issuance."""
import json, math, sys
from audit_coup_fixed_cohort import ROOT, cohort, summarize
from audit_coup_reconciliation import pinned, rows, memberships
from audit_coup_membership import get, URLS
from audit_coup_origin_panel import build, summarize as summarize_panel
from experiment_coup_rolling_backtest import forecast
from experiment_coup_mean_constraint import constrain
from experiment_annual_ged_rolling_probability import score

def gains(p, q, label):
    # Positive means model p improves on reference q.
    return ((q-label)**2-(p-label)**2,
            math.log(p/q) if label else math.log1p(-p)-math.log1p(-q))

def bound(p, q, label):
    if label is not None:
        g = gains(p,q,label)
        return tuple((x,x) for x in g)
    a,b = gains(p,q,0),gains(p,q,1)
    return tuple((min(x,y),max(x,y)) for x,y in zip(a,b))

def evaluate(panel, sets, origins=range(1980,2025), lags=(1,3)):
    history = [(y,c,v) for y,c,v,_ in panel]
    result = {}
    for lag in lags:
        totals = {m: {"known":0,"unknown":0,"positives":0,"brier_known_gain_sum":0.,
                  "log_loss_known_gain_sum":0.,"brier_lo":0.,"brier_hi":0.,
                  "log_loss_lo":0.,"log_loss_hi":0.}
                  for m in ("country_constrained","prior5_constrained")}
        for y in origins:
            fixed = cohort(sets,"dec31",y-lag)
            actual = {c:v for yr,c,v in history if yr==y}
            if set(actual) != cohort(sets,"jan1",y) or not fixed:
                raise ValueError("Unexpected risk-set mismatch")
            # Placeholder target labels never enter fitting or lagged features.
            # Replace every test row, rather than select retrospectively on membership.
            training = [x for x in history if x[0]<y]
            test, raw = forecast(training+[(y,c,0) for c in sorted(fixed)],y)
            if {c for _,c,_ in test} != fixed:
                raise ValueError("Fixed risk set changed")
            base = [x[1] for x in raw]
            if len(set(base))!=1:
                raise ValueError("Nonconstant recent baseline")
            predictions = {"country_constrained":constrain([x[2] for x in raw],base[0])[0],
                           "prior5_constrained":constrain([x[3] for x in raw],base[0])[0]}
            for m, probabilities in predictions.items():
                t=totals[m]
                for (_,c,_),p,q in zip(test,probabilities,base):
                    label=actual.get(c)
                    if label is None:
                        t["unknown"]+=1
                    else:
                        t["known"]+=1
                        t["positives"]+=label
                        b,ll=gains(p,q,label)
                        t["brier_known_gain_sum"]+=b
                        t["log_loss_known_gain_sum"]+=ll
                    (bl,bh),(ll,lh)=bound(p,q,label)
                    t["brier_lo"]+=bl;t["brier_hi"]+=bh
                    t["log_loss_lo"]+=ll;t["log_loss_hi"]+=lh
        for t in totals.values():
            n=t["known"]+t["unknown"]
            for metric in ("brier","log_loss"):
                t[metric+"_known_gain"]=round(t.pop(metric+"_known_gain_sum")/t["known"],9)
                t[metric+"_full_roster_gain_bounds"]=[round(t.pop(metric+"_lo")/n,9),
                                                    round(t.pop(metric+"_hi")/n,9)]
        result[str(lag)]=totals
    return {"status":"HISTORICAL_FIXED_ROSTER_SENSITIVITY_UNKNOWN_LABEL_BOUNDS",
            "results":result,"new_forecasts":0,"modified_forecasts":0}

def run():
    manifest=json.loads((ROOT/"data/coup-membership-census.json").read_text())
    inputs={}
    for m in manifest["sources"]:
        raw=pinned(get(URLS[m["kind"]]),m)
        inputs[m["kind"]]=list(rows(raw,m["csv_member"]))
    _,_,sets,_=memberships(inputs["States2024"],inputs["System2024"])
    frozen=json.loads((ROOT/"data/coup-fixed-cohort-audit.json").read_text())
    actual=summarize(sets)
    actual["source_sha256"]=[m["sha256"] for m in manifest["sources"]]
    if actual!=frozen: raise ValueError("Roster audit changed")
    panel,diag=build()
    if summarize_panel(panel,diag)!=json.loads((ROOT/"data/coup-origin-panel.json").read_text()):
        raise ValueError("Frozen outcome panel changed")
    result=evaluate(panel,sets)
    for lag,t in result["results"].items():
        for v in t.values():
            s=frozen["summary"][lag]
            if v["unknown"]!=s["stale_country_years"] or v["known"]+v["unknown"]!=s["fixed_country_years"]:
                raise ValueError("Unexpected fixed cohort counts")
    return result

if __name__=="__main__":
    print("COUP_ROSTER_SCORE_BEGIN",flush=True)
    report=run()
    if "--check" in sys.argv and report!=json.loads((ROOT/"data/coup-fixed-cohort-score.json").read_text()):
        raise ValueError("Frozen fixed cohort score differs")
    print(json.dumps(report,sort_keys=True,indent=2))
    print("COUP_ROSTER_SCORE_END",flush=True)
