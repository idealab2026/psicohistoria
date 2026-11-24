#!/usr/bin/env python3
"""Official Candidate monthly source census, no event rows or outcomes read."""
import csv
import hashlib
import io
import json
import urllib.request
from audit_candidate_q2_q3_vintages import get_source
from audit_candidate_to_annual_ged import examine_zip
from check_ucdp_candidate_asof import SourceError
BASE="https://ucdp.uu.se/downloads/candidateged/"
MONTHLY_YEARS=(2021,2022,2023,2024,2025)
CSV_URLS=tuple(BASE+f"GEDEvent_v{y%100}_0_{m}.csv"
               for y in MONTHLY_YEARS for m in (1,2,3))+(BASE+"GEDEvent_v23_01_23_04.csv",)
GED_URL="https://ucdp.uu.se/downloads/ged/ged241-csv.zip"
MAX_ZIP=110_000_000
REQUIRED={"id","country_id","type_of_violence","date_prec","date_start","date_end","best"}
def header_metadata(raw):
    if not raw:
        raise SourceError("Empty official Candidate source")
    reader=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    fields=next(reader,[])
    if len(fields)!=len(set(fields)) or not REQUIRED.issubset(fields):
        raise SourceError("Missing or duplicate Candidate header")
    return fields
def get_ged():
    req=urllib.request.Request(GED_URL,headers={"User-Agent":"IDEA-LAB-institutional-science-audit/1.0"})
    with urllib.request.urlopen(req,timeout=120) as response:
        if response.url!=GED_URL:
            raise SourceError("Unexpected GED ZIP redirect")
        raw=response.read(MAX_ZIP+1)
    if not raw or len(raw)>MAX_ZIP:
        raise SourceError("Invalid GED ZIP size")
    return raw
def census(fetch_csv=get_source,fetch_ged=get_ged):
    result=[]
    for url in CSV_URLS:
        try:
            raw=fetch_csv(url)
            # Inspect first CSV record only, even if the historic schema differs.
            fields=next(csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline="")),[])
            entry={"url":url,"sha256":hashlib.sha256(raw).hexdigest(),
                   "bytes":len(raw),"header":fields,
                   "missing_required":sorted(REQUIRED-set(fields)),
                   "duplicate_fields":len(fields)!=len(set(fields))}
            entry["schema_eligible"]=not entry["missing_required"] and not entry["duplicate_fields"]
            result.append(entry)
            print("SOURCE_METADATA "+json.dumps(entry,sort_keys=True),flush=True)
        except (OSError,ValueError) as exc:
            entry={"url":url,"schema_eligible":False,"error":str(exc)}
            result.append(entry)
            print("SOURCE_METADATA "+json.dumps(entry,sort_keys=True),flush=True)
    raw=fetch_ged()
    return {"status":"SOURCE_CENSUS_ONLY_NO_EVENT_OR_OUTCOME_ROWS_READ",
            "candidate_sources":result,
            "annual_ged":{"url":GED_URL,"sha256":hashlib.sha256(raw).hexdigest(),
                          "bytes":len(raw),"members":examine_zip(raw)},
            "new_forecasts":0,"modified_forecasts":0}
if __name__=="__main__":
    report=census()
    print("MONTHLY_CENSUS_BEGIN")
    print(json.dumps(report,sort_keys=True,indent=2))
    print("MONTHLY_CENSUS_END")
    if not all(x["schema_eligible"] for x in report["candidate_sources"]):
        raise SourceError("One or more monthly sources not yet schema eligible")
