#!/usr/bin/env python3
"""Resolve a frozen DEC2026 horizon only with reviewed first annual GED sources."""
import argparse,csv,hashlib,io,json,re,zipfile
from datetime import date,datetime,timezone
from pathlib import Path
from check_dec2026_publication import check,FROZEN_SHA,ROOT
from experiment_annual_ged_rolling_probability import load,validate,score
from experiment_candidate_monthly_alert_value import alert,rounded,BUDGETS
from audit_candidate_to_annual_ged import examine_zip
from check_ucdp_candidate_asof import ged_day
YEARS={30:(2026,),90:(2026,2027)}
START=date(2026,12,1)
ENDS={30:date(2026,12,30),90:date(2027,2,28)}
def gate(h,now):
    if h not in YEARS or now.tzinfo is None or now.utcoffset().total_seconds()!=0:
        raise ValueError("Invalid horizon or UTC time")
    if now.date()<date(max(YEARS[h])+1,1,1):
        raise ValueError("Annual outcome year not yet closed")
def registry_entry(meta,year,now):
    v=str(year+1)[-2:]
    url=f"https://ucdp.uu.se/downloads/ged/ged{v}1-csv.zip"
    if meta.get("year")!=year or meta.get("edition")!=v+".1" or meta.get("url")!=url:
        raise ValueError("Wrong first annual edition")
    if not re.fullmatch("[a-f0-9]{64}",meta.get("sha256","")) or not re.fullmatch("[a-f0-9]{40}",meta.get("review_commit","")):
        raise ValueError("Missing original hash or public review commit")
    if meta.get("status")!="OFFICIAL_FIRST_EDITION_REVIEWED" or not meta.get("evidence_url","").startswith("https://ucdp.uu.se/"):
        raise ValueError("Official release review missing")
    observed=datetime.fromisoformat(meta["observed_at_utc"].replace("Z","+00:00"))
    if observed.tzinfo is None or observed.utcoffset().total_seconds()!=0 or not date(year+1,1,1)<=observed.date() or observed>now:
        raise ValueError("Invalid source observation chronology")
    return v
def count_year(raw,year,ids,h,expected_sha):
    if hashlib.sha256(raw).hexdigest()!=expected_sha:
        raise ValueError("Original annual ZIP SHA mismatch")
    examine_zip(raw)
    v=str(year+1)[-2:]; member=f"GEDEvent_v{v}_1.csv"
    seen=set();eligible=set();out=dict.fromkeys(ids,0);n=0;maximum=0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.namelist()!=[member]: raise ValueError("Unexpected annual archive member")
        with z.open(member) as stream:
            reader=csv.DictReader(io.TextIOWrapper(stream,encoding="utf-8-sig",newline=""))
            required={"id","year","country_id","type_of_violence","date_prec","best","date_start","date_end"}
            if not required.issubset(reader.fieldnames or []) or len(set(reader.fieldnames))!=len(reader.fieldnames):
                raise ValueError("Invalid annual CSV schema")
            for x in reader:
                y=int(x["year"]);maximum=max(y,maximum)
                if y!=year: continue
                n+=1;eid=(x["id"] or "").strip()
                if not eid or eid in seen: raise ValueError("Duplicate or blank annual ID")
                seen.add(eid)
                c,t,p,b=map(int,(x["country_id"],x["type_of_violence"],x["date_prec"],x["best"]))
                a,e=ged_day(x["date_start"],"start"),ged_day(x["date_end"],"end")
                if c<=0 or t not in (1,2,3) or p not in range(6) or b<0 or a>e:
                    raise ValueError("Invalid annual coding")
                if c in out and t==1 and p in (1,2) and START<=a<=e<=ENDS[h]:
                    if a.year!=year or e.year!=year:
                        # A genuinely cross-year event wholly inside the window is assigned
                        # once to its coded GED year; never split or double-count it.
                        if year not in range(a.year,e.year+1): raise ValueError("Inconsistent event year")
                    eligible.add(eid);out[c]+=b
    if not n or maximum!=year: raise ValueError("Missing or unexpected annual coverage")
    return out,eligible
def combine(parts,ids):
    out=dict.fromkeys(ids,0);seen=set()
    for counts,events in parts:
        if set(counts)!=set(ids) or seen&events: raise ValueError("Universe mismatch or cross-edition duplicate")
        seen|=events
        for c,v in counts.items(): out[c]+=v
    return out
def evaluate(doc,counts,h):
    cells=[c for c in doc["cells"] if c["horizon"]==h]
    if [c["threshold"] for c in cells]!=[1,5,10,25]: raise ValueError("Incomplete horizon")
    result=[]
    for cell in cells:
        rows=cell["countries"];ids={r["country_id"] for r in rows}
        if len(rows)!=len(ids) or ids!=set(counts) or any(type(v) is not int or v<0 for v in counts.values()):
            raise ValueError("Invalid outcome universe")
        eligible=[r for r in rows if r["eligible"]]
        y=[int(counts[r["country_id"]]>=cell["threshold"]) for r in eligible]
        if len(y)!=cell["n_eligible"]: raise ValueError("Risk set changed")
        base=score([r["probabilities"]["global"] for r in eligible],y)
        models={}
        for m in doc["models"]:
            p=[r["probabilities"][m] for r in eligible];s=score(p,y)
            models[m]={**s,"brier_skill_vs_global":1-s["brier"]/base["brier"],
                "log_loss_gain_vs_global":base["log_loss"]-s["log_loss"],
                "mean_probability":sum(p)/len(p),"alerts":{str(k):alert(p,y,k) for k in BUDGETS}}
        result.append({"threshold":cell["threshold"],"horizon":h,"n":len(y),"positives":sum(y),"models":models})
    return rounded(result)
def issuance():
    rows=load();validate(rows);ids={x[1] for x in rows}
    raw=(ROOT/"data/forecast-dec2026-pilot.json").read_bytes()
    receipt=json.loads((ROOT/"data/forecast-dec2026-pilot-manifest.json").read_text())
    source=json.loads((ROOT/"data/candidate-october-2026-source-observation.json").read_text())
    if hashlib.sha256(raw).hexdigest()!=FROZEN_SHA: raise ValueError("Issued forecast changed")
    check(raw,receipt,ids,source["source_manifest"])
    return json.loads(raw),ids
def main():
    p=argparse.ArgumentParser();p.add_argument("--resolve",type=int,choices=(30,90));p.add_argument("--zip-dir",type=Path)
    args=p.parse_args();doc,ids=issuance()
    if args.resolve is None:
        print(json.dumps({"status":"ISSUANCE_ONLY_NO_OUTCOMES_ACCESSED","resolved":0,"forecast_sha256":FROZEN_SHA}));return
    h=args.resolve;now=datetime.now(timezone.utc);gate(h,now)
    if args.zip_dir is None: raise ValueError("Original local ZIP directory required")
    # File intentionally absent until separately reviewed official release evidence.
    registry=json.loads((ROOT/"data/dec2026-reviewed-annual-sources.json").read_text())
    if registry.get("schema")!="idealab.psico.dec2026.reviewed-annual.v1": raise ValueError("Wrong registry")
    parts=[];sources=[]
    for year in YEARS[h]:
        meta=registry["sources"][str(year)];v=registry_entry(meta,year,now)
        raw=(args.zip_dir/f"ged{v}1-csv.zip").read_bytes()
        parts.append(count_year(raw,year,ids,h,meta["sha256"]));sources.append(meta)
    print(json.dumps({"status":"RESOLUTION_CANDIDATE_REQUIRES_PUBLIC_REVIEW","horizon":h,
        "forecast_sha256":FROZEN_SHA,"sources":sources,"results":evaluate(doc,combine(parts,ids),h),
        "modified_forecasts":0,"independent_skill_demonstrated":False},sort_keys=True,indent=2))
if __name__=="__main__": main()
