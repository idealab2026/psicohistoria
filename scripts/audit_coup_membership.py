#!/usr/bin/env python3
"""COW historical membership census; no coup outcomes read."""
import csv,hashlib,io,json,zipfile,re
from collections import Counter
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from pathlib import PurePosixPath
from audit_coup_sources import Links
PAGE="https://correlatesofwar.org/data-sets/state-system-membership/"
BASE="https://correlatesofwar.org/wp-content/uploads/"
URLS={k:BASE+k+".zip" for k in ("States2024","System2024")}
MAX=20_000_000
def get(url):
    if url not in (PAGE,*URLS.values()): raise ValueError("Unknown official source")
    with urlopen(Request(url,headers={"User-Agent":"IDEA-LAB-institutional-science-audit/1.0"}),timeout=60) as response:
        if response.url!=url: raise ValueError("Unexpected redirect")
        raw=response.read(MAX+1)
    if not raw or len(raw)>MAX: raise ValueError("Invalid size")
    return raw
def sha(raw): return hashlib.sha256(raw).hexdigest()
def census_zip(raw,kind):
    if not raw or len(raw)>MAX: raise ValueError("Invalid ZIP size")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        items=z.infolist()
        if sum(i.file_size for i in items)>100_000_000 or any(i.filename.startswith("/") or ".." in PurePosixPath(i.filename).parts for i in items):
            raise ValueError("Unsafe archive")
        csvs=[i for i in items if i.filename.lower().endswith(".csv") and not i.filename.startswith("__MACOSX/")]
        if len(csvs)!=1: raise ValueError("Expected one CSV member")
        with z.open(csvs[0]) as f:
            reader=csv.DictReader(io.TextIOWrapper(f,encoding="utf-8-sig",newline=""))
            header=reader.fieldnames or []
            normalized={x.strip().lower():x for x in header}
            if len(normalized)!=len(header) or not {"ccode"}.issubset(normalized):
                raise ValueError("Unrecognized state membership header")
            result={"header":header,"csv_member":csvs[0].filename,
                    "members":[i.filename for i in items],"bytes":len(raw),"sha256":sha(raw)}
            if kind=="System2024":
                if "year" not in normalized: raise ValueError("No year column")
                seen=set();counts=Counter()
                for row in reader:
                    c,y=int(row[normalized["ccode"]]),int(row[normalized["year"]])
                    if c<=0 or not 1816<=y<=2024 or (c,y) in seen: raise ValueError("Invalid or duplicate membership")
                    seen.add((c,y));counts[y]+=1
                if not seen or min(counts)!=1816 or max(counts)!=2024 or not all(y in counts for y in range(1816,2025)):
                    raise ValueError("Unexpected historical coverage")
                result.update(rows=len(seen),distinct_codes=len({c for c,y in seen}),benchmark_rows=sum(counts[y] for y in range(1950,2025)),annual_membership={str(y):counts[y] for y in range(1950,2025)})
            elif kind=="States2024":
                required={"styear","stmonth","stday","endyear","endmonth","endday"}
                if not required.issubset(normalized): raise ValueError("Missing membership interval columns")
                from datetime import date
                intervals=set();codes=set()
                for row in reader:
                    c=int(row[normalized["ccode"]])
                    start=date(*(int(row[normalized[x]]) for x in ("styear","stmonth","stday")))
                    end=date(*(int(row[normalized[x]]) for x in ("endyear","endmonth","endday")))
                    if c<=0 or start>end or end.year>2024 or (c,start,end) in intervals: raise ValueError("Invalid or duplicate interval")
                    intervals.add((c,start,end));codes.add(c)
                if not intervals or max(e.year for c,s,e in intervals)!=2024: raise ValueError("Unexpected interval coverage")
                result.update(rows=len(intervals),distinct_codes=len(codes))
            else: raise ValueError("Unexpected archive")
            return result
def run():
    page=get(PAGE);links=Links(PAGE);links.feed(page.decode("utf-8"))
    sources=[]
    for kind,url in URLS.items():
        if url not in links.links: raise ValueError("Official archive link absent")
        raw=get(url)
        sources.append({"kind":kind,"url":url,**census_zip(raw,kind)})
    return {"status":"MEMBERSHIP_CENSUS_ONLY_NO_COUP_OUTCOMES","observed_at_utc":datetime.now(timezone.utc).isoformat(),"catalogue_sha256":sha(page),"sources":sources,"new_forecasts":0,"modified_forecasts":0}
if __name__=="__main__":
    d=run();print("COUP_MEMBERSHIP_BEGIN");print(json.dumps(d,sort_keys=True,indent=2));print("COUP_MEMBERSHIP_END")
