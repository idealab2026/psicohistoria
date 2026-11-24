#!/usr/bin/env python3
"""Contemporary official-source observation only; no forecast or release-date claim."""
import hashlib
import json
import os
import sys
from datetime import date,datetime,timezone
from html.parser import HTMLParser
from urllib.parse import urljoin
from urllib.request import Request,urlopen
from pathlib import Path
from collections import Counter
from audit_candidate_monthly_bridge import decode,union
from experiment_annual_ged_rolling_probability import load,validate
INDEX="https://ucdp.uu.se/downloads/olddw.html"
URL="https://ucdp.uu.se/downloads/candidateged/GEDEvent_v26_01_26_10.csv"
CURRENT="https://ucdp.uu.se/downloads/"
API_DOC="https://ucdp.uu.se/apidocs/"
MONTHLY={m:f"https://ucdp.uu.se/downloads/candidateged/GEDEvent_v26_0_{m}.csv" for m in (8,9,10)}
START=date(2026,8,1)
END=date(2026,10,31)
class Links(HTMLParser):
    def __init__(self,base=INDEX):
        super().__init__(); self.hrefs=[]; self.base=base
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            href=dict(attrs).get("href")
            if href: self.hrefs.append(urljoin(self.base,href))
def verify_index(raw):
    p=Links();p.feed(raw.decode("utf-8-sig"))
    if p.hrefs.count(URL)!=1:
        raise ValueError("Official October cumulative link missing or ambiguous")
def fetch(url,max_bytes):
    if url not in (INDEX,URL,CURRENT,API_DOC,*MONTHLY.values()): raise ValueError("Unknown institutional source")
    req=Request(url,headers={"User-Agent":"IDEA-LAB-institutional-science-audit/1.0"})
    with urlopen(req,timeout=120) as response:
        if response.url!=url: raise ValueError("Unexpected official source redirect")
        raw=response.read(max_bytes+1)
    if not raw or len(raw)>max_bytes: raise ValueError("Source empty or too large")
    return raw
def inspect(raw,ids,observed):
    if observed.tzinfo is None or observed.utcoffset().total_seconds()!=0:
        raise ValueError("UTC observation required")
    if not 0<(observed.date()-END).days<=45:
        raise ValueError("Source too old or observation precedes coverage")
    return inspect_events(decode(raw,2026),ids,observed)
def inspect_events(events,ids,observed):
    if observed.tzinfo is None or observed.utcoffset().total_seconds()!=0 or not 0<(observed.date()-END).days<=45:
        raise ValueError('Invalid UTC observation or stale source')
    stats=Counter(); recent=set();state=set();other=set()
    for c,t,p,b,start,end in events.values():
        if end>=observed.date():
            raise ValueError("Event ends on or after observation date")
        stats["all_rows"]+=1
        if not START<=start<=end<=END:
            stats["outside_recent_window"]+=1
            continue
        if p not in (1,2):
            stats["precision_excluded"]+=1;continue
        if c not in ids:
            stats["outside_universe"]+=1;continue
        stats["eligible_recent_rows"]+=1
        stats["state_based_rows" if t==1 else "other_violence_rows"]+=1
        recent.add(c)
        if b>0: (state if t==1 else other).add(c)
    if not stats["eligible_recent_rows"]:
        raise ValueError("No eligible recent records")
    return {"event_counts":dict(sorted(stats.items())),"countries_with_eligible_records":len(recent),
            "countries_with_positive_state_based_best":len(state),
            "countries_with_positive_other_violence_best":len(other),
            "universe_size":len(ids)}
def capture():
    index=fetch(INDEX,5_000_000);verify_index(index)
    raw=fetch(URL,30_000_000)
    observed=datetime.now(timezone.utc)
    run=os.environ.get("GITHUB_RUN_ID","")
    if not run.isdecimal(): raise ValueError("Public CI run ID required")
    rows=load();validate(rows);ids={x[1] for x in rows}
    return {"status":"OBSERVED_SOURCE_ONLY_NO_FORECAST",
        "source_url":URL,"source_version":"26.01.26.10",
        "observed_at_utc":observed.isoformat(),"ci_run_id":run,
        "catalogue_url":INDEX,"catalogue_sha256":hashlib.sha256(index).hexdigest(),
        "source_sha256":hashlib.sha256(raw).hexdigest(),"source_bytes":len(raw),
        "coverage_start":"2026-01-01","coverage_end":END.isoformat(),
        "recent_start":START.isoformat(),"recent_end":END.isoformat(),
        "original_release_date_certified":False,"new_forecasts":0,"modified_forecasts":0,
        **inspect(raw,ids,observed)}
def monthly_metadata(raw,month):
    events=decode(raw,2026)
    # Require actual evidence of the advertised month, even for the
    # convention-derived August URL whose archive hyperlink is erroneous.
    own=sum(start.year==2026 and start.month==month and end.year==2026 and end.month==month
            for _,_,_,_,start,end in events.values())
    if not own: raise ValueError("Monthly source has no records in its stated month")
    return events,{"month":month,"url":MONTHLY[month],
        "sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),
        "rows":len(events),"rows_wholly_in_calendar_month":own}
def capture_monthly():
    index=fetch(INDEX,5_000_000)
    current=fetch(CURRENT,5_000_000)
    docs=fetch(API_DOC,5_000_000)
    history=Links(INDEX);history.feed(index.decode("utf-8-sig"))
    latest=Links(CURRENT);latest.feed(current.decode("utf-8-sig"))
    # The catalogue currently uses a shared hyperlink for Aug/Sep labels.
    # Record actual canonical href presence, rather than assuming label mapping.
    link_evidence={str(m):{"historical":url in history.hrefs,
                           "current":url in latest.hrefs}
                   for m,url in MONTHLY.items()}
    print("CATALOGUE_LINK_EVIDENCE "+json.dumps(link_evidence,sort_keys=True),flush=True)
    if not any(link_evidence["10"].values()):
        raise ValueError("October official monthly link absent")
    if not any(any(link_evidence[str(m)].values()) for m in (8,9)):
        raise ValueError("Neither August nor September monthly link present")
    if any(f"26.0.{m}".encode() not in docs for m in MONTHLY):
        raise ValueError("Monthly version not documented")
    snapshots=[];manifest=[];failures=[]
    for m,url in MONTHLY.items():
        try:
            raw=fetch(url,30_000_000)
            events,meta=monthly_metadata(raw,m)
            snapshots.append(events);manifest.append(meta)
            print("MONTHLY_SOURCE_METADATA "+json.dumps(meta,sort_keys=True),flush=True)
        except (OSError,ValueError) as exc:
            failure={"month":m,"url":url,"error_type":type(exc).__name__,
                     "http_status":getattr(exc,"code",None)}
            failures.append(failure)
            print("MONTHLY_SOURCE_BLOCKED "+json.dumps(failure,sort_keys=True),flush=True)
    if failures: raise ValueError("Monthly source gate blocked; see per-source diagnostics")
    observed=datetime.now(timezone.utc)
    run=os.environ.get("GITHUB_RUN_ID","")
    if not run.isdecimal(): raise ValueError("Public CI run ID required")
    # Reject any future-ending record before deduplication, even if replaced.
    for snap in snapshots:
        if any(x[5]>=observed.date() for x in snap.values()):
            raise ValueError("Event ends on or after observation date")
    rows=load();validate(rows);ids={x[1] for x in rows}
    events,stats=union(snapshots)
    return {"status":"OBSERVED_MONTHLY_SOURCES_ONLY_NO_FORECAST",
        "observed_at_utc":observed.isoformat(),"ci_run_id":run,
        "source_manifest":manifest,"catalogue_sha256":hashlib.sha256(index).hexdigest(),
        "current_catalogue_sha256":hashlib.sha256(current).hexdigest(),
        "api_docs_sha256":hashlib.sha256(docs).hexdigest(),
        "catalogue_link_evidence":link_evidence,
        "convention_derived_months":[m for m in MONTHLY if not any(link_evidence[str(m)].values())],
        "recent_start":START.isoformat(),"recent_end":END.isoformat(),
        "deduplication":stats,"original_release_date_certified":False,
        "new_forecasts":0,"modified_forecasts":0,**inspect_events(events,ids,observed)}
if __name__=="__main__":
    print("OCTOBER_SOURCE_BEGIN",flush=True)
    print(json.dumps(capture_monthly() if "--monthly" in sys.argv else capture(),sort_keys=True,indent=2),flush=True)
    print("OCTOBER_SOURCE_END",flush=True)
