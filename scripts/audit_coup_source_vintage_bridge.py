#!/usr/bin/env python3
"""Compare original author archives; aggregate revision counts only."""
import csv, io, json, re, zipfile
from datetime import date
from decimal import Decimal
from xml.etree import ElementTree as ET
from audit_coup_sources import fetch, csv_schema, xlsx_schema
from audit_coup_reconciliation import ROOT, pinned, rows, memberships
from audit_coup_membership import get, URLS
from audit_coup_fixed_cohort import cohort, summarize

NS="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
FIELDS=("ccode","year","month","day","coup")

def integral(value):
    x=Decimal(str(value).strip())
    if not x.is_finite() or x!=x.to_integral_value():
        raise ValueError("Non-integral source field")
    return int(x)

def header_map(header):
    normalized=[str(x).strip().lower() for x in header]
    if len(set(normalized))!=len(normalized) or not set(FIELDS)<=set(normalized):
        raise ValueError("Unrecognized or ambiguous archive header")
    return [normalized.index(k) for k in FIELDS]

def workbook_rows(raw):
    xlsx_schema(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml",n)]
        if len(names)!=1:
            raise ValueError("Expected one original worksheet")
        shared=[]
        if "xl/sharedStrings.xml" in z.namelist():
            root=ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared=["".join(t.text or "" for t in s.iter(NS+"t")) for s in root.findall(NS+"si")]
        root=ET.fromstring(z.read(names[0]))
        for row in root.findall(".//"+NS+"sheetData/"+NS+"row"):
            data={}
            for cell in row.findall(NS+"c"):
                match=re.fullmatch(r"([A-Z]+)[1-9]\d*",cell.get("r",""))
                if not match:
                    raise ValueError("Unknown worksheet cell address")
                idx=0
                for c in match.group(1): idx=idx*26+ord(c)-64
                if idx in data: raise ValueError("Duplicate worksheet cell")
                t=cell.get("t","n");v=cell.findtext(NS+"v")
                if cell.find(NS+"f") is not None:
                    raise ValueError("Unexpected formula in archive")
                if t=="s":
                    i=integral(v)
                    if i<0 or i>=len(shared): raise ValueError("Invalid shared string")
                    data[idx]=shared[i]
                elif t=="inlineStr":
                    data[idx]="".join(e.text or "" for e in cell.iter(NS+"t"))
                elif t in ("n","str"):
                    data[idx]=v or ""
                elif v is None:
                    data[idx]=""
                else:
                    raise ValueError("Unsupported worksheet cell type")
            if data and any(str(x).strip() for x in data.values()):
                yield [data.get(i,"") for i in range(1,max(data)+1)]

def records(source_rows):
    iterator=iter(source_rows)
    idx=header_map(next(iterator))
    events=set();seen=set()
    for row in iterator:
        if not any(str(x).strip() for x in row): continue
        def value(k):
            j=idx[FIELDS.index(k)]
            if j>=len(row): raise ValueError("Missing required cell")
            return integral(row[j])
        y=value("year")
        if not 1950<=y<=2025: continue
        c=value("ccode");m=value("month");d=value("day");o=value("coup")
        stamp=date(y,m,d)
        if c<=0 or o not in (1,2) or (c,stamp) in seen:
            raise ValueError("Invalid or repeated country/date record")
        seen.add((c,stamp));events.add((y,c,m,d,o))
    if not events: raise ValueError("No in-scope events")
    return events

def compare(a,b):
    # a is older; b is newer. Only aggregate differences.
    pa={(y,c) for y,c,*_ in a};pb={(y,c) for y,c,*_ in b}
    return {"older_events":len(a),"newer_events":len(b),
            "event_records_removed_or_changed":len(a-b),
            "event_records_added_or_changed":len(b-a),
            "older_positive_country_years":len(pa),"newer_positive_country_years":len(pb),
            "positive_country_years_removed":len(pa-pb),
            "positive_country_years_added":len(pb-pa)}

def run():
    source=json.loads((ROOT/"data/coup-source-census.json").read_text())
    archives={x["archive_label"]:x for x in source["sources"] if x.get("provider")=="Powell-Thyne"}
    old,new=(archives[x] for x in ("2026-07-08","2026-08-29"))
    x=pinned(fetch(old["url"]),old);c=pinned(fetch(new["url"]),new)
    csv_schema(c)
    a=records(workbook_rows(x))
    b=records(csv.reader(io.StringIO(c.decode("utf-8-sig"),newline="")))
    manifest=json.loads((ROOT/"data/coup-membership-census.json").read_text())
    inputs={}
    for m in manifest["sources"]:
        raw=pinned(get(URLS[m["kind"]]),m)
        inputs[m["kind"]]=list(rows(raw,m["csv_member"]))
    _,_,sets,_=memberships(inputs["States2024"],inputs["System2024"])
    actual=summarize(sets)
    actual["source_sha256"]=[m["sha256"] for m in manifest["sources"]]
    if actual!=json.loads((ROOT/"data/coup-fixed-cohort-audit.json").read_text()):
        raise ValueError("Frozen cohort audit changed")
    roster=cohort(sets,"dec31",2024)
    if len(roster)!=195: raise ValueError("Unexpected cohort")
    if any(c not in roster for y,c,*_ in a|b if y==2025):
        raise ValueError("2025 outside-roster event requires adjudication")
    annual={str(y):compare({e for e in a if e[0]==y},{e for e in b if e[0]==y}) for y in range(2019,2026)}
    frozen=json.loads((ROOT/"data/coup2025-temporal-extension.json").read_text())
    if annual["2025"]["newer_positive_country_years"]!=frozen["positives"] or annual["2025"]["newer_events"]!=frozen["event_rows"]:
        raise ValueError("Frozen 2025 outcome totals differ")
    return {"status":"SAME_SOURCE_VINTAGE_COMPARISON_NOT_INDEPENDENT",
            "source_sha256":[old["sha256"],new["sha256"]],
            "source_dates":["2026-07-08","2026-08-29"],
            "roster_n":len(roster),"total":compare(a,b),"annual":annual,
            "new_forecasts":0,"modified_forecasts":0}

if __name__=="__main__":
    print("COUP_VINTAGE_BRIDGE_BEGIN",flush=True)
    print(json.dumps(run(),sort_keys=True,indent=2))
    print("COUP_VINTAGE_BRIDGE_END",flush=True)
