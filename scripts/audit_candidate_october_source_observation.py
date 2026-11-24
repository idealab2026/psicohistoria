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
from audit_candidate_monthly_bridge import decode
from experiment_annual_ged_rolling_probability import load,validate
INDEX="https://ucdp.uu.se/downloads/olddw.html"
URL="https://ucdp.uu.se/downloads/candidateged/GEDEvent_v26_01_26_10.csv"
START=date(2026,8,1)
END=date(2026,10,31)
class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            href=dict(attrs).get("href")
            if href: self.hrefs.append(urljoin(INDEX,href))
def verify_index(raw):
    p=Links();p.feed(raw.decode("utf-8-sig"))
    if p.hrefs.count(URL)!=1:
        raise ValueError("Official October cumulative link missing or ambiguous")
def fetch(url,max_bytes):
    if url not in (INDEX,URL): raise ValueError("Unknown institutional source")
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
    events=decode(raw,2026)
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
if __name__=="__main__":
    print("OCTOBER_SOURCE_BEGIN",flush=True)
    print(json.dumps(capture(),sort_keys=True,indent=2),flush=True)
    print("OCTOBER_SOURCE_END",flush=True)
