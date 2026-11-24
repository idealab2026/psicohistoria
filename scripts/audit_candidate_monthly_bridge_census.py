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
PINS={
    "GEDEvent_v21_0_1.csv": "0b74e86f773705cf0cd96bf36a67cabbf0d260b6ed849e6e74faedc9afd1a141",
    "GEDEvent_v21_0_2.csv": "5b9dece2138daa4c523b03be7b1bdfeb9a256914d414811a44a0441e1360be0a",
    "GEDEvent_v21_0_3.csv": "1b4a4a98b178f2318dafb95f3c2d639409e275100248aeb6fd044afd27a975ad",
    "GEDEvent_v22_0_1.csv": "01e8f1ac9fae1af64ec656a703724f9b1c6827717a720c3623fad936cf251b61",
    "GEDEvent_v22_0_2.csv": "c537e8a02fc2905a9a94397965882cdf7c15f01819305e12554bb0d0e0263615",
    "GEDEvent_v22_0_3.csv": "37cad1e648433cb295ba2eb36acffd2fabaf4aede4e5349b83e854816ab26c00",
    "GEDEvent_v23_0_1.csv": "ebe8a5429cbc4b135b474a369a8d8ceca6eb396e0628fce880a9cf5131eaaa6a",
    "GEDEvent_v23_0_2.csv": "520339ac65fc16902ee55679ccbdcacc14ef9d0cfa3b8e5f7322ad06c409ac21",
    "GEDEvent_v23_0_3.csv": "07a76a241bc1080e71f88e1a641077861c13ec85d4472234b72795b1c8406857",
    "GEDEvent_v24_0_1.csv": "841a3e1b133dbb8c3923c4a0e27969b28f2874b70ff3b53f4f3a5d1caefbea3d",
    "GEDEvent_v24_0_2.csv": "a387c54146b7e2595cb84f7216839a4817a6fc014be0adbcd7fcdfd3a3817235",
    "GEDEvent_v24_0_3.csv": "f34584213737d22f51f9e4e95ce62c29996e0898bc4a27606f224b862cc300a1",
    "GEDEvent_v25_0_1.csv": "805c36c8ca7e2fa71285a5dc7db3461e3d4b1724ddd99ded48e2aab2bb27c9a3",
    "GEDEvent_v25_0_2.csv": "22f3a0c3b5fe57a2ef258bba96f0c577f43ea3773518d69aa68a1c98b665686d",
    "GEDEvent_v25_0_3.csv": "727967c3c20fdc60c1695c3dc952d2fdaf3a0989b1e992a8126ddc047dcf7240",
    "GEDEvent_v23_01_23_04.csv": "4244614e4a6b94115617b50401b971d8ebacf1c66e82e3fb1eba0f0b946c0191"
}
GED_SHA="202e84f3bc91f085b2a886959cbbdeed9d381d758ee897b68520f59ea631c760"
QUARANTINE=BASE+"GEDEvent_v24_0_1.csv"
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
                   "bytes":len(raw),"field_count":len(fields),
                   "missing_required":sorted(REQUIRED-set(fields)),
                   "duplicate_fields":len(fields)!=len(set(fields))}
            entry["schema_eligible"]=not entry["missing_required"] and not entry["duplicate_fields"]
            if entry["schema_eligible"]:
                entry["header"]=fields
            # Never print an unrecognized first record: it could be an event.
            result.append(entry)
            print("SOURCE_METADATA "+json.dumps(entry,sort_keys=True),flush=True)
        except (OSError,ValueError) as exc:
            entry={"url":url,"schema_eligible":False,"error":str(exc)}
            result.append(entry)
            print("SOURCE_METADATA "+json.dumps(entry,sort_keys=True),flush=True)
    raw=fetch_ged()
    if hashlib.sha256(raw).hexdigest()!=GED_SHA:
        raise SourceError("Frozen annual GED source changed")
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
    for x in report["candidate_sources"]:
        if x.get("sha256")!=PINS[x["url"].rsplit("/",1)[-1]]:
            raise SourceError("Frozen Candidate source changed: "+x["url"])
        if x["schema_eligible"]!=(x["url"]!=QUARANTINE):
            raise SourceError("Unexpected schema eligibility: "+x["url"])
    print("OK: 15 schema-eligible files and one exact hash-pinned quarantined file")
