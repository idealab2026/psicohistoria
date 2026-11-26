#!/usr/bin/env python3
"""Frozen-origin COUP label sensitivity; no model fit, no forecast."""
import csv,io,json
from collections import Counter
from datetime import date
from audit_coup_reconciliation import ROOT,FIRST,LAST,pinned,rows,memberships,reconcile
from audit_coup_membership import get,URLS,census_zip
from audit_coup_sources import fetch

def panel(raw,spans,keys,sets):
    risk=sets["jan1"]
    if sets["any_day"]!=keys or not risk<=keys:
        raise ValueError("Membership sources disagree")
    strict=set();relaxed=set();exceptions=[]
    seen=set();dates=set()
    for x in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline="")):
        y=int(x["year"])
        if not FIRST<=y<=LAST: continue
        c=int(x["ccode"]);d=date(y,int(x["month"]),int(x["day"]));o=int(x["coup"])
        identity=tuple(x.items())
        if c not in spans or o not in (1,2) or identity in seen or (c,d) in dates:
            raise ValueError("Unresolved coding or duplicate")
        seen.add(identity);dates.add((c,d))
        k=(c,y)
        valid=any(a<=d<=b for a,b in spans[c])
        if valid and k not in keys: raise ValueError("Membership key missing")
        if not valid: exceptions.append(k)
        if k not in risk: continue
        relaxed.add(k)
        if valid: strict.add(k)
    if not strict<=relaxed<=risk: raise ValueError("Invalid nested label sets")
    diagnostics={"date_mismatch_rows":len(exceptions),
        "date_mismatch_rows_in_origin_risk":sum(k in risk for k in exceptions),
        "date_mismatch_distinct_origin_keys":len(set(exceptions)&risk),
        "changed_binary_labels":len(relaxed-strict)}
    return [(y,c,int((c,y) in strict),int((c,y) in relaxed)) for c,y in sorted(risk,key=lambda k:(k[1],k[0]))],diagnostics

def summarize(panel,diagnostics):
    annual=[]
    for y in range(FIRST,LAST+1):
        sub=[x for x in panel if x[0]==y]
        if not sub: raise ValueError("Empty historical risk set")
        annual.append({"year":y,"n":len(sub),"strict_positive":sum(x[2] for x in sub),
            "relaxed_positive":sum(x[3] for x in sub)})
    n=len(panel);a=sum(x[2] for x in panel);b=sum(x[3] for x in panel)
    return {"status":"RETROSPECTIVE_ORIGIN_PANEL_NO_MODEL_NO_FORECAST",
        "n":n,"strict_positive":a,"relaxed_positive":b,
        "strict_rate":round(a/n,9),"relaxed_rate":round(b/n,9),
        "annual":annual,"label_sensitivity":diagnostics,
        "new_forecasts":0,"modified_forecasts":0}

def build():
    cm=json.loads((ROOT/"data/coup-source-census.json").read_text())
    mm=json.loads((ROOT/"data/coup-membership-census.json").read_text())
    frozen=json.loads((ROOT/"data/coup-membership-reconciliation.json").read_text())
    source=next(x for x in cm["sources"] if x.get("archive_label")=="2026-08-29")
    raw=pinned(fetch(source["url"]),source)
    inputs={}
    for m in mm["sources"]:
        z=pinned(get(URLS[m["kind"]]),m)
        if census_zip(z,m["kind"])["csv_member"]!=m["csv_member"]: raise ValueError("Archive member changed")
        inputs[m["kind"]]=list(rows(z,m["csv_member"]))
    spans,keys,sets,diag=memberships(inputs["States2024"],inputs["System2024"])
    if diag!=frozen["membership"] or reconcile(raw,spans,keys,sets)!=frozen["events"]:
        raise ValueError("Prior reconciliation does not reproduce")
    p,d=panel(raw,spans,keys,sets)
    if len(p)!=11674 or sum(x[2] for x in p)!=421 or d["date_mismatch_rows"]!=3:
        raise ValueError("Unexpected frozen panel counts")
    return p,d
if __name__=="__main__":
    p,d=build()
    print("COUP_PANEL_BEGIN",flush=True)
    print(json.dumps(summarize(p,d),sort_keys=True,indent=2))
    print("COUP_PANEL_END",flush=True)
