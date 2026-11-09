#!/usr/bin/env python3
"""Public UCDP 26.1 country-year -> independently reconstructed retrospective Markov inputs.

This script NEVER loads institutional or personal research data. It accepts only
official UCDP OrganizedViolenceCY 26.1 CSV data under CC BY 4.0.
Scientific caution: 26.1 includes revisions known in 2026, so the calculations
are NOT prospective predictions made in 2016/2020.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile, BadZipFile

OFFICIAL_URL = "https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-261-csv.zip"
SOURCE = "UCDP OrganizedViolenceCY 26.1"
SCHEMA = "idealab.psico.public_official_country_markov.v1"
EXPECTED_ROWS = 7132
MAX_ZIP = 4_000_000
MAX_CSV = 12_000_000
ORIGINS = ((2016, 2014, 10), (2020, 2018, 6))
PROTOCOL = "four-state-binary-markov-prior20-cutoff-only-v1"

def _int(x, key):
    if not str(x).strip().isdigit():
        raise ValueError("Invalid integer in UCDP official source: " + key)
    return int(str(x).strip())

def _sha(data):
    return hashlib.sha256(data).hexdigest()

def read_zip(data):
    if not data or len(data) > MAX_ZIP:
        raise ValueError("Invalid source size")
    try:
        with ZipFile(io.BytesIO(data)) as z:
            members=[e for e in z.infolist() if not e.is_dir()]
            if len(members)!=1 or not members[0].filename.lower().endswith(".csv"):
                raise ValueError("Official ZIP must contain exactly one CSV")
            if members[0].file_size > MAX_CSV or members[0].file_size < 100_000:
                raise ValueError("Invalid official CSV size")
            with z.open(members[0]) as fd:
                raw=fd.read(MAX_CSV+1)
    except BadZipFile as e:
        raise ValueError("Invalid official ZIP") from e
    if len(raw)>MAX_CSV:
        raise ValueError("Oversized official CSV")
    return raw.decode("utf-8-sig")

def parse_public_source(csv_text, expected_rows=EXPECTED_ROWS):
    reader=csv.DictReader(io.StringIO(csv_text,newline=""))
    headers=set(reader.fieldnames or [])
    needed={"country","country_id","year"}
    if not needed.issubset(headers):
        raise ValueError("Official data columns missing")
    mortality="sb_total_deaths_best" if "sb_total_deaths_best" in headers else (
        "sb_total_deaths_best_cy" if "sb_total_deaths_best_cy" in headers else None)
    if mortality is None:
        raise ValueError("State-based deaths column missing")
    records=defaultdict(dict)
    countries={}
    total=0
    for row in reader:
        total+=1
        cid=_int(row["country_id"],"country_id")
        year=_int(row["year"],"year")
        deaths=_int(row[mortality],mortality)
        name=str(row["country"] or "").strip()
        if not (1<=cid<=2000 and 1989<=year<=2025 and 0<=deaths<=10_000_000 and 1<=len(name)<=120):
            raise ValueError("Invalid country-year in UCDP official source")
        if year in records[cid]:
            raise ValueError("Duplicate country-year")
        if cid in countries and countries[cid] != name:
            raise ValueError("Country label changed within official source")
        countries[cid]=name
        records[cid][year]=int(deaths>=25)
    if total != expected_rows:
        raise ValueError(f"Unexpected country-year count: {total}")
    if len(countries)<190 or len(countries)>210:
        raise ValueError("Official country coverage inconsistent")
    return records,countries

def pairs():
    return [[0,0],[0,0]]

def derive_catalog(records,names,origin,cutoff,horizon,source_sha,script_sha):
    if origin!=cutoff+2 or horizon!=2026-origin:
        raise ValueError("Invalid original retrospective year structure")
    included=[]
    frequency=[0,0]
    transitions=pairs()
    memory=[[0,0] for _ in range(4)]
    for cid,history in records.items():
        for year in sorted(history):
            if year>cutoff:continue
            now=history[year]
            frequency[now]+=1
            if year-1 in history:
                transitions[history[year-1]][now]+=1
            if year-2 in history and year-1 in history:
                memory[history[year-2]*2+history[year-1]][now]+=1
        if cutoff not in history or cutoff-1 not in history:
            continue
        own=pairs()
        for year in sorted(history):
            if year>cutoff or year-1 not in history:continue
            own[history[year-1]][history[year]]+=1
        included.append({
            "id":cid,"name":names[cid],
            "initial":history[cutoff-1]*2+history[cutoff],
            "counts":own
        })
    included.sort(key=lambda c:c["id"])
    if not (180<=len(included)<=210):
        raise ValueError("Incomplete country population for historical cutoff")
    if sum(frequency)<1000 or any(sum(r)==0 for r in transitions):
        raise ValueError("Insufficient historical transitions")
    run_hash=_sha((source_sha+script_sha+str(origin)+PROTOCOL).encode())
    return {
        "schema":"psychohistory.futures.catalog.v1",
        "version":"ucdp-futures-v1",
        "runType":"retrospective_revised_release",
        "vintageVerified":False,"prospectiveEligible":False,
        "datasetVersion":SOURCE,
        "runId":run_hash,
        "protocolSha256":_sha(PROTOCOL.encode()),
        "codeSha256":script_sha,
        "sourceClass":"PUBLIC_OFFICIAL_INDEPENDENT_RECONSTRUCTION",
        "sourceSha256":source_sha,
        "origin":origin,"cutoff":cutoff,"observedThrough":2025,
        "maxHorizon":horizon,"priorStrength":20,
        "global":{"frequency":frequency,"transitions":transitions,"memory":memory},
        "countries":included
    }

def build(data,source_sha,script_sha):
    csv_text=read_zip(data)
    records,names=parse_public_source(csv_text)
    result={
        "schema":SCHEMA,
        "source":{"dataset":SOURCE,"url":OFFICIAL_URL,"sha256":source_sha,
                  "license":"CC BY 4.0","reference":"Davies, Pettersson & Öberg (2026); Sundberg & Melander (2013)",
                  "rowCount":EXPECTED_ROWS},
        "method":"Independent four-state retrospective reconstruction from public official country-year data. The entire 26.1 edition was published in 2026; historical as-of availability is NOT verified.",
        "forecastsIssued":0,"prospectiveSkillVerified":False,
        "catalogs":[derive_catalog(records,names,*params,source_sha,script_sha) for params in ORIGINS]
    }
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    parser.add_argument("--source-zip",help="Offline authenticated ZIP input for testing or reproducibility")
    parser.add_argument("--require-source-sha256",default="")
    args=parser.parse_args()
    if args.source_zip:
        data=Path(args.source_zip).read_bytes()
    else:
        req=Request(OFFICIAL_URL,headers={"User-Agent":"IDEA-LAB-research-replication/1.0 (UCDP CC BY 4.0)"})
        with urlopen(req,timeout=55) as stream:
            if stream.geturl()!=OFFICIAL_URL:
                raise ValueError("Official source unexpectedly redirected")
            data=stream.read(MAX_ZIP+1)
    digest=_sha(data)
    if args.require_source_sha256 and digest!=args.require_source_sha256:
        raise ValueError("Official source SHA-256 unexpectedly changed")
    source_file=Path(__file__).read_bytes()
    result=build(data,digest,_sha(source_file))
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf8")
    print("OFFICIAL_UCDP_PUBLIC_RECONSTRUCTION_OK source_sha256="+digest,
          "rows="+str(EXPECTED_ROWS),
          "countries="+",".join(f"{x['origin']}:{len(x['countries'])}" for x in result["catalogs"]))
if __name__=="__main__":main()
