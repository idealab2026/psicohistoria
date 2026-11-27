#!/usr/bin/env python3
"""One-year retrospective extension; fixed source-record endpoint, no issuance."""
import csv, io, json, sys
from datetime import date
from audit_coup_fixed_cohort import ROOT, cohort, summarize
from audit_coup_reconciliation import pinned, rows, memberships
from audit_coup_membership import get, URLS
from audit_coup_sources import fetch, csv_schema
from audit_coup_origin_panel import build, summarize as summarize_panel
from experiment_coup_rolling_backtest import forecast
from experiment_coup_mean_constraint import constrain
from experiment_annual_ged_rolling_probability import score
from experiment_candidate_monthly_alert_value import alert, rounded, BUDGETS

YEAR=2025
def labels(raw, roster):
    csv_schema(raw)
    positives=set(); seen=set(); event_rows=0
    for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline="")):
        y=int(row["year"])
        if y!=YEAR: continue
        c=int(row["ccode"]); outcome=int(row["coup"])
        d=date(y,int(row["month"]),int(row["day"]))
        if c not in roster or outcome not in (1,2) or (c,d) in seen:
            raise ValueError("2025 target requires separate source/code adjudication")
        seen.add((c,d)); positives.add(c); event_rows+=1
    return {c:int(c in positives) for c in sorted(roster)},event_rows

def predictions(history,roster):
    if not roster or any(y>2023 for y,c,v in history):
        raise ValueError("Training cutoff or empty roster")
    a,p=forecast(history+[(YEAR,c,0) for c in sorted(roster)],YEAR)
    b,q=forecast(history+[(YEAR,c,1) for c in sorted(roster)],YEAR)
    if p!=q or [c for y,c,v in a]!=sorted(roster) or [c for y,c,v in b]!=sorted(roster):
        raise ValueError("Target label dependence or roster mismatch")
    base=[x[1] for x in p]
    if len(set(base))!=1: raise ValueError("Nonconstant reference")
    return {"global_recent":base,
            "country_constrained":constrain([x[2] for x in p],base[0])[0],
            "prior5_constrained":constrain([x[3] for x in p],base[0])[0]}

def run():
    manifest=json.loads((ROOT/"data/coup-membership-census.json").read_text())
    inputs={}
    for m in manifest["sources"]:
        raw=pinned(get(URLS[m["kind"]]),m)
        inputs[m["kind"]]=list(rows(raw,m["csv_member"]))
    _,_,sets,_=memberships(inputs["States2024"],inputs["System2024"])
    actual=summarize(sets)
    actual["source_sha256"]=[m["sha256"] for m in manifest["sources"]]
    if actual!=json.loads((ROOT/"data/coup-fixed-cohort-audit.json").read_text()):
        raise ValueError("Roster changed")
    roster=cohort(sets,"dec31",2024)
    if len(roster)!=195: raise ValueError("Unexpected cohort")
    panel,diag=build()
    if summarize_panel(panel,diag)!=json.loads((ROOT/"data/coup-origin-panel.json").read_text()):
        raise ValueError("Historical panel changed")
    history=[(y,c,u) for y,c,u,v in panel if y<=2023]
    pred=predictions(history,roster)
    source=next(m for m in json.loads((ROOT/"data/coup-source-census.json").read_text())["sources"] if m.get("archive_label")=="2026-08-29")
    raw=pinned(fetch(source["url"]),source)
    lab,event_rows=labels(raw,roster)
    obs=[lab[c] for c in sorted(roster)]
    base=score(pred["global_recent"],obs)
    result={}
    for m,v in pred.items():
        s=score(v,obs)
        result[m]={**s,"brier_gain":base["brier"]-s["brier"],
                   "log_loss_gain":base["log_loss"]-s["log_loss"],
                   "mean_probability":sum(v)/len(v),
                   "alerts":{str(k):{key:alert(v,obs,k)[key] for key in
                   ("expected_hits","minimum_hits","maximum_hits","random_expected_hits","tied_at_cutoff","slots_in_tie")}
                   for k in BUDGETS}}
    return rounded({"status":"RETROSPECTIVE_2025_SOURCE_RECORD_ENDPOINT_NOT_ASOF_NOT_PROSPECTIVE",
        "year":YEAR,"n":len(obs),"positives":sum(obs),"event_rows":event_rows,
        "training_last_year":2023,"recent_first_year":2019,
        "source_sha256":source["sha256"],"roster_source_sha256":actual["source_sha256"],
        "models":result,"new_forecasts":0,"modified_forecasts":0})

if __name__=="__main__":
    print("COUP2025_EXTENSION_BEGIN",flush=True)
    report=run()
    if "--check" in sys.argv and report!=json.loads((ROOT/"data/coup2025-temporal-extension.json").read_text()):
        raise ValueError("Frozen 2025 extension differs")
    print(json.dumps(report,sort_keys=True,indent=2))
    print("COUP2025_EXTENSION_END",flush=True)
