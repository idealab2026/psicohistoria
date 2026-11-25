#!/usr/bin/env python3
"""Candidate progress only; never an outcome resolver or scoring engine."""
import argparse,calendar,hashlib,json,re
from datetime import date,datetime,timezone,timedelta
from pathlib import Path
from audit_candidate_monthly_bridge import decode,union
from resolve_dec2026_pilot import issuance,START,ENDS,FROZEN_SHA,ROOT
MONTHS=((2026,12),(2027,1),(2027,2))
MAX_CSV=30_000_000
def end_month(y,m): return date(y,m,calendar.monthrange(y,m)[1])
def version(y,m): return f"{y%100:02d}.0.{m}"
def filename(y,m): return f"GEDEvent_v{y%100:02d}_0_{m}.csv"
def utc(s):
    d=datetime.fromisoformat(s.replace("Z","+00:00"))
    if d.tzinfo is None or d.utcoffset()!=timedelta(0): raise ValueError("UTC required")
    return d
def verify_prefix(entries,now):
    if now.tzinfo is None or now.utcoffset()!=timedelta(0): raise ValueError("UTC required")
    if not isinstance(entries,list) or not 1<=len(entries)<=len(MONTHS): raise ValueError("Missing or invalid monthly prefix")
    previous=None
    for (y,m),e in zip(MONTHS,entries):
        expected=f"https://ucdp.uu.se/downloads/candidateged/{filename(y,m)}"
        if e.get("year")!=y or e.get("month")!=m or e.get("version")!=version(y,m) or e.get("url")!=expected:
            raise ValueError("Missing month or wrong official source version")
        if e.get("status")!="OFFICIAL_MONTHLY_REVIEWED" or not e.get("evidence_url","").startswith("https://ucdp.uu.se/"):
            raise ValueError("Missing reviewed official evidence")
        if not re.fullmatch("[a-f0-9]{64}",e.get("sha256","")) or not re.fullmatch("[a-f0-9]{40}",e.get("review_commit","")):
            raise ValueError("Unpinned source or absent review commit")
        observed=utc(e["observed_at_utc"])
        if not end_month(y,m)<observed.date() or observed>now or (previous and observed<previous):
            raise ValueError("Invalid source observation chronology")
        previous=observed
    return end_month(*MONTHS[len(entries)-1])
def read_snapshot(raw,entry):
    if not raw or len(raw)>MAX_CSV or hashlib.sha256(raw).hexdigest()!=entry["sha256"]:
        raise ValueError("Original source bytes mismatch or size invalid")
    y,m=entry["year"],entry["month"]; observed=utc(entry["observed_at_utc"])
    rows=decode(raw,y)
    if any(x[5]>=observed.date() for x in rows.values()): raise ValueError("Event at or after source observation")
    if not any(date(y,m,1)<=x[4]<=x[5]<=end_month(y,m) for x in rows.values()):
        raise ValueError("No records wholly in advertised calendar month")
    return rows
def progress(doc,ids,snapshots,coverage_end):
    if coverage_end not in {end_month(y,m) for y,m in MONTHS}:
        raise ValueError("Invalid observed coverage end")
    if len(snapshots)!=next(i+1 for i,(y,m) in enumerate(MONTHS) if end_month(y,m)==coverage_end):
        raise ValueError("Snapshot prefix length mismatch")
    events,stats=union(snapshots)
    counts={h:dict.fromkeys(ids,0) for h in ENDS}
    for c,t,p,b,a,e in events.values():
        if c not in ids or t!=1 or p not in (1,2): continue
        for h,end in ENDS.items():
            if START<=a<=e<=min(end,coverage_end): counts[h][c]+=b
    cells=[]
    for cell in doc["cells"]:
        h,t=cell["horizon"],cell["threshold"]
        if {x["country_id"] for x in cell["countries"]}!=set(ids) or len(cell["countries"])!=len(ids):
            raise ValueError("Frozen universe mismatch")
        states=[]
        for row in cell["countries"]:
            c=row["country_id"]
            status=("NOT_ELIGIBLE" if not row["eligible"] else
                "PROVISIONAL_THRESHOLD_RECORDED" if counts[h][c]>=t else "THRESHOLD_NOT_RECORDED")
            states.append({"country_id":c,"status":status,"resolved":False})
        if sum(x["status"]!="NOT_ELIGIBLE" for x in states)!=cell["n_eligible"]:
            raise ValueError("Frozen eligibility changed")
        cells.append({"threshold":t,"horizon":h,"n_eligible":cell["n_eligible"],
            "window_start":START.isoformat(),"window_end":ENDS[h].isoformat(),
            "observed_calendar_through":min(coverage_end,ENDS[h]).isoformat(),
            "window_calendar_complete":coverage_end>=ENDS[h],
            "provisional_threshold_recorded":sum(x["status"]=="PROVISIONAL_THRESHOLD_RECORDED" for x in states),
            "threshold_not_recorded":sum(x["status"]=="THRESHOLD_NOT_RECORDED" for x in states),
            "countries":states})
    return {"status":"PROVISIONAL_CANDIDATE_NOT_OFFICIALLY_RESOLVED",
            "forecast_sha256":FROZEN_SHA,"coverage_end":coverage_end.isoformat(),
            "deduplication":stats,"cells":cells,"outcomes_resolved":0,
            "scores_computed":False,"forecast_modified":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--monitor",action="store_true");p.add_argument("--csv-dir",type=Path)
    args=p.parse_args();doc,ids=issuance()
    if not args.monitor:
        print(json.dumps({"status":"AWAITING_REVIEWED_MONTHLY_SOURCES_NO_OUTCOMES_READ",
            "forecast_sha256":FROZEN_SHA,"outcomes_resolved":0,"scores_computed":False}));return
    now=datetime.now(timezone.utc)
    if now.date()<=end_month(*MONTHS[0]): raise ValueError("First full target month has not ended")
    if args.csv_dir is None: raise ValueError("Original local CSV directory required")
    registry=json.loads((ROOT/"data/dec2026-reviewed-monthly-sources.json").read_text())
    if registry.get("schema")!="idealab.psico.dec2026.reviewed-monthly.v1": raise ValueError("Wrong source registry")
    entries=registry["sources"];end=verify_prefix(entries,now)
    snapshots=[]
    for entry in entries:
        path=args.csv_dir/filename(entry["year"],entry["month"])
        if path.stat().st_size>MAX_CSV: raise ValueError("Source too large")
        snapshots.append(read_snapshot(path.read_bytes(),entry))
    report=progress(doc,ids,snapshots,end);report["sources"]=entries
    print(json.dumps(report,sort_keys=True,indent=2))
if __name__=="__main__": main()
