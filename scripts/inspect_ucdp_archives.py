#!/usr/bin/env python3
"""Explore OFFICIAL UCDP onset historical vintages, without fabricating release dates.

Offline regression tests use fixtures only. This tool emits metadata, NOT
prospective forecasts. It does not save any raw country-level source in git.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError

HISTORY = "https://ucdp.uu.se/downloads/olddw.html"
PINNED = {
    "23.1": ("https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-onset-231.csv",
             "e2cadfa7a87b3949f8c638c27381fbb1b44fb076ccb00570782252d0935a2289"),
    "25.1": ("https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-onset-251.csv",
             "e2b59e65aaca88403991465b78fb407d7eddcefadeb18c7f1397bfe2ea83fe6a"),
}
MAX_HTML = 1_500_000
MAX_CSV = 6_000_000

def digest(data):
    return hashlib.sha256(data).hexdigest()

def official_url(value, extension=".csv"):
    u=urlsplit(value)
    if u.scheme != "https" or u.netloc != "ucdp.uu.se" or not u.path.startswith("/downloads/onset/") \
        or not u.path.lower().endswith(extension) or u.query or u.fragment:
        raise ValueError("Not an allowed official UCDP onset download")
    return value

class HistoricalLinks(HTMLParser):
    """Capture original HTML anchor context, not search-engine inferred filenames."""
    def __init__(self):
        super().__init__()
        self.section = ""
        self.heading_level = 0
        self.heading = []
        self.text = ""
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag in ("h2", "h3"):
            self.heading_level += 1
            self.heading = []
        if tag == "a":
            self.current = {"url": dict(attrs).get("href", ""), "offset":len(self.text), "caption":""}

    def handle_data(self, data):
        if self.heading_level:
            self.heading.append(data)
        if self.current is not None:
            self.current["caption"] += data
        self.text += " " + data

    def handle_endtag(self, tag):
        if tag in ("h2", "h3") and self.heading_level:
            self.heading_level -= 1
            self.section = " ".join(self.heading).strip()
        if tag == "a" and self.current is not None:
            self.links.append({**self.current, "section":self.section, "before":self.text[max(0,self.current["offset"]-180):]})
            self.current = None

def discover(html):
    parser=HistoricalLinks()
    parser.feed(html)
    selected=[]
    for anchor in parser.links:
        if "Onset Dataset" not in anchor["section"]:
            continue
        url=urljoin(HISTORY,anchor["url"])
        try: official_url(url)
        except ValueError: continue
        prefix=anchor["before"][-240:]
        m=list(re.finditer(r"(?:version\s*)?(\d\d\.1)\s*:",prefix,re.I))
        version=m[-1].group(1) if m else None
        if version in ("19.1","22.1","23.1","24.1","25.1"):
            selected.append({"version":version,"url":url,"caption":anchor["caption"].strip()})
    return selected

def parse_source(data):
    try: text=data.decode("utf-8-sig")
    except UnicodeDecodeError as e: raise ValueError("Non UTF-8 onset source") from e
    reader=csv.DictReader(io.StringIO(text))
    headers=reader.fieldnames or []
    if not {"year","onset2","gwno_a"}.issubset(headers):
        raise ValueError("UCDP country onset expected schema not found: "+repr(headers[:30]))
    counts={}
    countries={}
    used=set()
    for row in reader:
        year=int(row["year"])
        key=(year,row["gwno_a"])
        if key in used: raise ValueError("Duplicate country-year in official onset source")
        used.add(key)
        v=row["onset2"].strip()
        if v not in ("0","1"):
            raise ValueError("Nonbinary onset2 label")
        counts[year]=counts.get(year,0)+int(v)
        countries.setdefault(year,set()).add(row["gwno_a"])
    if not (1946 <= min(counts) <= 2000 and 2020 <= max(counts) <= 2025 and len(used)>9000):
        raise ValueError("Unexpected onset temporal coverage")
    return {"rows":len(used),"first_year":min(counts),"last_year":max(counts),
            "latest_onset2_positives":counts[max(counts)],
            "latest_country_count":len(countries[max(counts)]),
            "headers":headers}

def onset_labels(data):
    """Internal comparison only: never emit country-level values to public results."""
    reader=csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    if not {"year","gwno_a","onset2"}.issubset(reader.fieldnames or []):
        raise ValueError("Missing historical UCDP onset labels")
    labels={}
    for row in reader:
        key=(int(row["year"]),row["gwno_a"].strip())
        if key in labels: raise ValueError("Duplicate archived country-year")
        if row["onset2"].strip() not in ("0","1"):
            raise ValueError("Unexpected onset2 value")
        labels[key]=int(row["onset2"])
    return labels

def compare_revisions(old, new, old_max_year):
    """Compare frozen versions only on old-period country-years, without data leakage."""
    a={k:v for k,v in old.items() if k[0]<=old_max_year}
    b={k:v for k,v in new.items() if k[0]<=old_max_year}
    old_keys,new_keys=set(a),set(b)
    both=old_keys & new_keys
    changes=[k for k in both if a[k]!=b[k]]
    grouping=[
        ("1946-1989",1946,1989),
        ("1990-2009",1990,2009),
        ("2010-2020",2010,2020),
        ("2021-2022",2021,2022),
    ]
    return {
        "comparison":"UCDP_Onset_23_1_vs_25_1_onset2_historical_label_drift",
        "common_country_years":len(both),
        "country_years_only_in_23_1":len(old_keys-new_keys),
        "country_years_only_in_25_1":len(new_keys-old_keys),
        "onset2_label_flips":len(changes),
        "shared_positive_labels_23_1":sum(a[k] for k in both),
        "shared_positive_labels_25_1":sum(b[k] for k in both),
        "years_with_revisions":[
            {"year":year,"flips_0_to_1":sum(k[0]==year and a[k]==0 for k in changes),
             "flips_1_to_0":sum(k[0]==year and a[k]==1 for k in changes)}
            for year in sorted(set(k[0] for k in changes))
        ],
        "flips_0_to_1":sum(a[k]==0 for k in changes),
        "flips_1_to_0":sum(a[k]==1 for k in changes),
        "flips_by_period":[
            {"period":label,"shared":sum(lo<=k[0]<=hi for k in both),
             "flips":sum(lo<=k[0]<=hi for k in changes)}
            for label,lo,hi in grouping
        ],
        "not_prospective":True,
        "interpretation":"Measures cross-release retrospective label revisions, not forecast skill; incomplete territory overlap is reported separately."
    }

def fetch(url, limit):
    request=Request(url,headers={"User-Agent":"IDEA-LAB-scientific-archive-audit/1.0"})
    with urlopen(request,timeout=35) as response:
        if response.geturl() != url: raise ValueError("Unexpected official source redirect")
        raw=response.read(limit+1)
    if len(raw)>limit: raise ValueError("Oversized response")
    return raw

def inspect(fetcher=fetch):
    archive=fetcher(HISTORY,MAX_HTML)
    links=discover(archive.decode("utf-8-sig"))
    report={"schema":"idealab.psico.vintage_discovery.v1",
            "scientific_status":"ARCHIVE_METADATA_ONLY_NOT_HISTORICALLY_ISSUED",
            "archive_url":HISTORY,"archive_sha256":digest(archive),
            "official_onset_country_links":[],
            "pinned_downloads":[],
            "archive_lists_22_1":False,
            "archive_lists_24_1":False,
            "archived_24_1_download":{"status":"NOT_CHECKED"},
            "legacy_19_1_download":{"status":"NOT_CHECKED"},
            "historical_release_dates_cryptographically_verified":False,
            "prospective_predictions_issued":0}
    seen=set()
    for l in links:
        if l["url"] in seen:continue
        seen.add(l["url"])
        report["official_onset_country_links"].append(l)
        if l["version"]=="22.1":
            report["archive_lists_22_1"]=True
        if l["version"]=="24.1":
            report["archive_lists_24_1"]=True
    legacy_links=[item for item in links if item["version"]=="19.1" and "CSV" in item["caption"]]
    report["legacy_19_1_links"]=legacy_links
    if legacy_links:
        url=legacy_links[0]["url"]
        try:
            raw=fetcher(url,MAX_CSV)
            header=next(csv.reader(io.StringIO(raw.decode("utf-8-sig"))),[])
            report["legacy_19_1_download"]={
                "status":"RETRIEVED_UNPINNED",
                "url":url,"sha256":digest(raw),"length":len(raw),
                "headers":header[:40],
                "preview_lines_count":min(10,len(raw.splitlines()))
            }
        except HTTPError as error:
            report["legacy_19_1_download"]={"status":"HTTP_ERROR","http_status":error.code,"url":url}
    version_labels={}
    for item in links:
        if item["version"]=="24.1" and item["caption"]=="Intrastate Country Level Onset CSV":
            try:
                raw=fetcher(item["url"],MAX_CSV)
                report["archived_24_1_download"]={"status":"RETRIEVED_UNPINNED",
                    "url":item["url"],"sha256":digest(raw),**parse_source(raw)}
            except HTTPError as error:
                report["archived_24_1_download"]={"status":"HTTP_ERROR",
                    "url":item["url"],"http_status":error.code}
            break
    for version,(url,sha) in PINNED.items():
        raw=fetcher(url,MAX_CSV)
        if digest(raw)!=sha:
            raise ValueError("Pinned UCDP "+version+" hash mismatch; abort")
        report["pinned_downloads"].append({"version":version,"url":url,"sha256":sha,**parse_source(raw)})
        version_labels[version]=onset_labels(raw)
    report["historical_label_revisions"]=compare_revisions(version_labels["23.1"],version_labels["25.1"],2022)
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--report",help="Optional output outside source-controlled repository")
    args=ap.parse_args()
    data=inspect()
    rendered=json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)
    print(rendered)
    if args.report:
        from pathlib import Path
        p=Path(args.report).resolve()
        if ".git" in p.parts: raise ValueError("Cannot save metadata into git directory")
        p.write_text(rendered+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
