#!/usr/bin/env python3
"""Monthly Q1 bridge: fixed original source hashes, no historical as-of claim."""
import csv
import hashlib
import io
import json
from collections import Counter
from datetime import date
import zipfile
from pathlib import Path
import sys
from audit_candidate_monthly_bridge_census import BASE,PINS,GED_SHA,get_ged,header_metadata
from audit_candidate_q2_q3_vintages import get_source
from audit_candidate_to_annual_ged import examine_zip
from check_ucdp_candidate_asof import SourceError,ged_day
from experiment_annual_ged_rolling_probability import load,validate

YEARS=(2021,2022,2023,2025)
THRESHOLDS=(1,5,10,25)

def decode(raw,year):
    header_metadata(raw)
    rows={}
    for x in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline="")):
        eid=(x["id"] or "").strip()
        if not eid or eid in rows:
            raise SourceError("Missing or duplicate event ID within release")
        c,t,p,b=map(int,(x["country_id"],x["type_of_violence"],x["date_prec"],x["best"]))
        start,end=ged_day(x["date_start"],"start"),ged_day(x["date_end"],"end")
        if c<=0 or t not in (1,2,3) or p not in range(6) or b<0 or start>end:
            raise SourceError("Invalid event coding")
        rows[eid]=(c,t,p,b,start,end)
    if not rows:
        raise SourceError("Empty monthly release")
    return rows

def union(snapshots):
    """Last observed representation wins BEFORE eligibility filtering."""
    events={}
    stats=Counter()
    for snap in snapshots:
        for eid,x in snap.items():
            if eid in events:
                stats["repeated_ids"]+=1
                stats["changed_representations"]+=int(events[eid]!=x)
            events[eid]=x
    return events,dict(stats)

def counts(events,year,ids):
    out=dict.fromkeys(ids,0)
    for c,t,p,b,start,end in events.values():
        if c in out and t==1 and p in (1,2) and date(year,1,1)<=start<=end<=date(year,3,31):
            out[c]+=b
    return out

def compare(a,b):
    if set(a)!=set(b):
        raise SourceError("Country universe mismatch")
    return {"n":len(a),"monthly_best_total":sum(a.values()),"reference_best_total":sum(b.values()),
            "country_counts_changed":sum(a[c]!=b[c] for c in a),
            "country_nonzero_changed":sum((a[c]>0)!=(b[c]>0) for c in a),
            "absolute_country_count_change":sum(abs(a[c]-b[c]) for c in a),
            "risk_sets":{str(t):{"monthly_n":sum(a[c]<t for c in a),
                 "reference_n":sum(b[c]<t for c in a),
                 "changed_membership":sum((a[c]<t)!=(b[c]<t) for c in a)}
                 for t in THRESHOLDS}}

def verified(name,fetch=get_source):
    raw=fetch(BASE+name)
    if hashlib.sha256(raw).hexdigest()!=PINS[name]:
        raise SourceError("Monthly source changed: "+name)
    return raw

def annual_2023(raw,ids):
    if hashlib.sha256(raw).hexdigest()!=GED_SHA:
        raise SourceError("Annual GED24.1 source changed")
    examine_zip(raw)
    out30=dict.fromkeys(ids,0);out90=dict.fromkeys(ids,0)
    seen=set();n=0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.namelist()!=["GEDEvent_v24_1.csv"]:
            raise SourceError("Unexpected annual CSV member")
        with z.open("GEDEvent_v24_1.csv") as stream:
            reader=csv.DictReader(io.TextIOWrapper(stream,encoding="utf-8-sig",newline=""))
            if not {"id","year","country_id","type_of_violence","date_prec","best","date_start","date_end"}.issubset(reader.fieldnames or []):
                raise SourceError("Invalid annual schema")
            for x in reader:
                if int(x["year"])!=2023: continue
                n+=1
                eid=(x["id"] or "").strip()
                if not eid or eid in seen: raise SourceError("Duplicate annual event ID")
                seen.add(eid)
                c,t,p,b=map(int,(x["country_id"],x["type_of_violence"],x["date_prec"],x["best"]))
                start,end=ged_day(x["date_start"],"start"),ged_day(x["date_end"],"end")
                if c<=0 or t not in (1,2,3) or p not in range(6) or b<0 or start>end:
                    raise SourceError("Invalid annual coding")
                if c not in out90 or t!=1 or p not in (1,2) or not date(2023,5,1)<=start<=end<=date(2023,7,29):
                    continue
                out90[c]+=b
                if end<=date(2023,5,30): out30[c]+=b
    if not n: raise SourceError("No 2023 annual records")
    return out30,out90

def build(include_panel=False):
    previous=load();validate(previous)
    ids=sorted({x[1] for x in previous})
    refs={y:{x[1]:x[2] for x in previous if x[0]==y} for y in (2021,2022,2025)}
    refs[2023]=counts(decode(verified("GEDEvent_v23_01_23_04.csv"),2023),2023,ids)
    diagnostics={}; monthly={}
    for y in YEARS:
        snapshots=[decode(verified(f"GEDEvent_v{y%100}_0_{m}.csv"),y) for m in (1,2,3)]
        events,stats=union(snapshots)
        monthly[y]=counts(events,y,ids)
        diagnostics[str(y)]={**stats,**compare(monthly[y],refs[y]),
          "reference":"Jan-Apr restricted to Q1 (retrospective)" if y==2023 else "original cumulative Q1"}
    a,b=annual_2023(get_ged(),ids)
    outcomes=[]
    for t in THRESHOLDS:
        for h,labels in ((30,a),(90,b)):
            risk=[c for c in ids if monthly[2023][c]<t]
            outcomes.append({"threshold":t,"horizon":h,"n_at_risk":len(risk),
                 "annual_positive":sum(labels[c]>=t for c in risk)})
    report={"status":"RETROSPECTIVE_MONTHLY_BRIDGE_NOT_ASOF_NOT_ISSUED",
        "control_years":[2021,2022,2025],"quarantined_year":2024,
        "diagnostics":diagnostics,"2023_annual_outcomes":outcomes,
        "new_forecasts":0,"modified_forecasts":0}
    if include_panel:
        # The monthly feature and annual label are kept distinct.
        panel=[(x[0],x[1],monthly[x[0]][x[1]],x[3],x[4])
               for x in previous if x[0] in (2021,2022,2025)]
        panel.extend((2023,c,monthly[2023][c],a[c],b[c]) for c in ids)
        return report,sorted(panel)
    return report

def check_report(report):
    expected=json.loads((Path(__file__).resolve().parents[1]/"data/candidate-monthly-bridge-audit.json").read_text())
    if report!=expected: raise SourceError("Frozen monthly bridge does not reproduce")

if __name__=="__main__":
    print("MONTHLY_BRIDGE_BEGIN")
    report=build()
    if "--check" in sys.argv: check_report(report)
    print(json.dumps(report,indent=2,sort_keys=True))
    print("MONTHLY_BRIDGE_END")
