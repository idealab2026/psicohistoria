#!/usr/bin/env python3
"""Coup/membership reconciliation, not a model or definitive negative-label panel."""
import csv,hashlib,io,json,re,zipfile,sys
from collections import Counter,defaultdict
from datetime import date,timedelta
from pathlib import Path
from audit_coup_membership import get,URLS,census_zip
from audit_coup_sources import fetch,csv_schema
ROOT=Path(__file__).resolve().parents[1]
FIRST,LAST=1950,2024
def pinned(raw,meta):
    if hashlib.sha256(raw).hexdigest()!=meta["sha256"]: raise ValueError("Frozen source changed")
    return raw
def rows(raw,member):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        with z.open(member) as f:
            yield from csv.DictReader(io.TextIOWrapper(f,encoding="utf-8-sig",newline=""))
def memberships(states,system):
    spans=defaultdict(list); keys=set(); overlap_pairs=0
    for x in states:
        c=int(x["ccode"])
        a=date(*(int(x[k]) for k in ("styear","stmonth","stday")))
        b=date(*(int(x[k]) for k in ("endyear","endmonth","endday")))
        if c<=0 or a>b: raise ValueError("Invalid membership")
        spans[c].append((a,b))
    merged={}
    for c,intervals in spans.items():
        out=[]
        for a,b in sorted(intervals):
            if out and a<=out[-1][1]+timedelta(days=1):
                overlap_pairs+=int(a<=out[-1][1])
                out[-1]=(out[-1][0],max(out[-1][1],b))
            else: out.append((a,b))
        merged[c]=out
    for x in system:
        c,y=int(x["ccode"]),int(x["year"])
        if FIRST<=y<=LAST:
            if (c,y) in keys: raise ValueError("Duplicate state-year")
            keys.add((c,y))
    sets={k:set() for k in ("any_day","jan1","jul1","dec31","full_year")}
    for c,intervals in merged.items():
        for y in range(FIRST,LAST+1):
            a,b=date(y,1,1),date(y,12,31)
            mid=date(y,7,1);key=(c,y)
            if any(s<=b and e>=a for s,e in intervals): sets["any_day"].add(key)
            for name,d in (("jan1",a),("jul1",mid),("dec31",b)):
                if any(s<=d<=e for s,e in intervals): sets[name].add(key)
            if any(s<=a<=b<=e for s,e in intervals): sets["full_year"].add(key)
    diagnostics={k:{"rows":len(v),"system_only":len(keys-v),"interval_only":len(v-keys)} for k,v in sets.items()}
    diagnostics.update(system_rows=len(keys),overlapping_interval_pairs=overlap_pairs,
        codes_with_separate_membership_spans=sum(len(v)>1 for v in merged.values()),
        jan1_not_full_year=len(sets["jan1"]-sets["full_year"]),
        entered_after_jan1=len(sets["any_day"]-sets["jan1"]))
    return merged,keys,sets,diagnostics
def reconcile(raw,spans,keys,sets):
    csv_schema(raw)
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    required={"ccode","year","month","day","coup"}
    if not required.issubset(reader.fieldnames or []): raise ValueError("Missing coup columns")
    stats=Counter();seen=set();dates=set();matched=set();by_outcome=Counter()
    for x in reader:
        stats["source_rows"]+=1
        try: y=int(x["year"])
        except (ValueError,TypeError):
            stats["invalid_year"]+=1;continue
        if not FIRST<=y<=LAST: stats["out_of_scope_year"]+=1;continue
        stats["in_scope_rows"]+=1
        identity=tuple(x.items())
        if identity in seen: stats["exact_duplicate_rows"]+=1
        seen.add(identity)
        try: outcome=int(x["coup"])
        except (ValueError,TypeError): outcome=-1
        if outcome not in (1,2): stats["unexpected_outcome_code"]+=1;continue
        try: c=int(x["ccode"])
        except (ValueError,TypeError): stats["missing_or_invalid_cow_code"]+=1;continue
        if c not in spans: stats["unknown_cow_code"]+=1;continue
        try: d=date(y,int(x["month"]),int(x["day"]))
        except (ValueError,TypeError): stats["invalid_or_unknown_date"]+=1;continue
        if (c,d) in dates: stats["repeated_country_date"]+=1
        dates.add((c,d))
        if not any(a<=d<=b for a,b in spans[c]):
            stats["date_outside_membership"]+=1;continue
        if (c,y) not in keys:
            stats["missing_system_year"]+=1;continue
        stats["matched_rows"]+=1;by_outcome[str(outcome)]+=1
        matched.add((c,y))
    stats["unmatched_in_scope_rows"]=stats["in_scope_rows"]-stats["matched_rows"]
    return {"event_diagnostics":dict(sorted(stats.items())),"matched_rows_by_outcome":dict(sorted(by_outcome.items())),
        "matched_unique_positive_country_years":len(matched),
        "positive_years_in_jan1_membership":len(matched&sets["jan1"]),
        "positive_years_in_full_year_membership":len(matched&sets["full_year"]),
        "positive_years_entering_after_jan1":len(matched-sets["jan1"])}
def run():
    cm=json.loads((ROOT/"data/coup-source-census.json").read_text())
    mm=json.loads((ROOT/"data/coup-membership-census.json").read_text())
    source=next(x for x in cm["sources"] if x.get("archive_label")=="2026-08-29")
    raw=pinned(fetch(source["url"]),source)
    inputs={}
    for m in mm["sources"]:
        z=pinned(get(URLS[m["kind"]]),m)
        if census_zip(z,m["kind"])["csv_member"]!=m["csv_member"]: raise ValueError("Archive member changed")
        inputs[m["kind"]]=list(rows(z,m["csv_member"]))
    spans,keys,sets,diag=memberships(inputs["States2024"],inputs["System2024"])
    return {"status":"RECONCILIATION_ONLY_NO_MODEL_NO_FINAL_NEGATIVES",
        "year_start":FIRST,"year_end":LAST,"membership":diag,
        "events":reconcile(raw,spans,keys,sets),
        "source_sha256":[source["sha256"],*[x["sha256"] for x in mm["sources"]]],
        "new_forecasts":0,"modified_forecasts":0}
if __name__=="__main__":
    print("COUP_RECONCILE_BEGIN",flush=True)
    d=run()
    if "--check" in sys.argv and d!=json.loads((ROOT/"data/coup-membership-reconciliation.json").read_text()): raise ValueError("Frozen reconciliation mismatch")
    print(json.dumps(d,sort_keys=True,indent=2))
    print("COUP_RECONCILE_END",flush=True)
