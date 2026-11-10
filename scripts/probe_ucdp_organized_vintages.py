#!/usr/bin/env python3
"""Inspect UCDP's actual OrganizedViolenceCY historical archive links.

A reconnaissance tool, not a model score: fetches current archive page and linked
historical edition bytes, prints only provenance, hashes, formats, and schemas.
The presence of a version today does NOT prove its original 2023/2024 date.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

ARCHIVE="https://ucdp.uu.se/downloads/olddw.html"
ALLOWED_HOST="ucdp.uu.se"
VERSIONS=("23.1","24.1","25.1")
LIMIT=8_000_000

class ArchiveParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.heading=None
        self.heading_parts=[]
        self.country_section=False
        self.version=None
        self.href=None
        self.anchor_parts=[]
        self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag in ("h2","h3"):
            self.heading=tag
            self.heading_parts=[]
        elif tag=="a" and self.country_section and self.version in VERSIONS:
            self.href=dict(attrs).get("href")
            self.anchor_parts=[]
    def handle_endtag(self,tag):
        if self.heading==tag:
            title="".join(self.heading_parts).strip().lower()
            if title:
                self.country_section=("country-year dataset on organized violence within country borders" in title)
                self.version=None
            self.heading=None
        elif tag=="a" and self.href is not None:
            label="".join(self.anchor_parts).strip().upper()
            if label in ("CSV","EXCEL","XLSX") and self.version in VERSIONS:
                url=urljoin(ARCHIVE,self.href)
                self.links.append({"version":self.version,"format":label,"url":url})
            self.href=None
    def handle_data(self,data):
        if self.heading:
            self.heading_parts.append(data)
        if self.country_section and not self.heading:
            match=re.search(r"version\s+(23\.1|24\.1|25\.1)\s*:",data,re.I)
            if match:
                self.version=match.group(1)
        if self.href is not None:
            self.anchor_parts.append(data)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def request(url,limit=LIMIT):
    parts=urlsplit(url)
    if parts.scheme!="https" or parts.netloc!=ALLOWED_HOST or parts.query or parts.fragment:
        raise ValueError("Only official, literal UCDP download URLs allowed")
    with urlopen(Request(url,headers={"User-Agent":"IDEA-LAB-GEO2027-vintage-audit/1.0"}),timeout=60) as response:
        if urlsplit(response.geturl()).netloc!=ALLOWED_HOST:
            raise ValueError("Unexpected external download redirect")
        data=response.read(limit+1)
    if not data or len(data)>limit:
        raise ValueError("UCDP download outside size limit")
    return data

def discover(html):
    parser=ArchiveParser()
    parser.feed(html)
    selected={}
    for link in parser.links:
        parts=urlsplit(link["url"])
        if parts.scheme!="https" or parts.netloc!=ALLOWED_HOST:
            raise ValueError("Archive links unexpectedly leave official UCDP")
        selected.setdefault(link["version"],[]).append(link)
    return selected

def xlsx_first_row(data):
    """Read first sheet column labels with stdlib only."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        members=z.namelist()
        if "xl/worksheets/sheet1.xml" not in members:
            raise ValueError("No first XLSX worksheet")
        strings=[]
        if "xl/sharedStrings.xml" in members:
            with z.open("xl/sharedStrings.xml") as f:
                for _,el in ET.iterparse(f,events=("end",)):
                    if el.tag.endswith("}si"):
                        strings.append("".join(el.itertext()))
                        el.clear()
        with z.open("xl/worksheets/sheet1.xml") as f:
            for _,el in ET.iterparse(f,events=("end",)):
                if el.tag.endswith("}row"):
                    values={}
                    for cell in el:
                        if not cell.tag.endswith("}c"): continue
                        addr=cell.attrib.get("r","")
                        m=re.match(r"([A-Z]+)",addr)
                        if not m:continue
                        col=0
                        for char in m.group(1):
                            col=col*26+ord(char)-64
                        value_el=next((ch for ch in cell if ch.tag.endswith("}v")),None)
                        if value_el is not None and value_el.text is not None:
                            value=value_el.text
                            if cell.attrib.get("t")=="s":
                                value=strings[int(value)]
                            values[col]=value
                        elif cell.attrib.get("t")=="inlineStr":
                            values[col]="".join(cell.itertext())
                    return [values.get(i,"") for i in range(1,max(values,default=0)+1)]
    raise ValueError("XLSX has no row values")

def source_metadata(data,format_label):
    import csv
    def describe_csv(raw):
        decoded=raw.decode("utf-8-sig")
        reader=csv.DictReader(io.StringIO(decoded))
        header=reader.fieldnames or []
        country=next((col for col in ("country_id","country_id_cy") if col in header),None)
        year=next((col for col in ("year","year_cy") if col in header),None)
        deaths=next((col for col in ("sb_total_deaths_best","sb_total_deaths_best_cy")
                     if col in header),None)
        if not country or not year:
            raise ValueError("Country/year columns missing")
        if deaths is None: raise ValueError("No comparable state-based deaths field")
        years=set(); keys=set(); count=0; positives_last=0; last=0
        for row in reader:
            count+=1
            y=int(row[year])
            key=(int(row[country]),y)
            if key in keys:raise ValueError("Country-year duplication detected")
            keys.add(key); years.add(y)
            last=max(last,y)
        return {"format":"CSV","columns":header[:30],
                "rows":count,"last_year":last,
                "country_year_unique":True,"deaths_field":deaths,
                "country_id_field":country,"year_field":year}
    if data[:2]==b"PK":
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            members=z.namelist()
            csvfiles=[p for p in members if p.lower().endswith(".csv") and not p.endswith("/")]
            xlsx=("xl/workbook.xml" in members)
            if len(csvfiles)==1:
                raw=z.read(csvfiles[0])
                result=describe_csv(raw)
                result["format"]="CSV_ZIP"
                return result
            if xlsx:
                headers=xlsx_first_row(data)
                return {"format":"XLSX","entries":len(members),
                        "shared_strings":"xl/sharedStrings.xml" in members,
                        "sheet_files":len([x for x in members if re.fullmatch(r"xl/worksheets/sheet\d+\.xml",x)]),
                        "headers":headers[:35],
                        "country_id_field":next((x for x in ("country_id","country_id_cy") if x in headers),None),
                        "year_field":next((x for x in ("year","year_cy") if x in headers),None),
                        "deaths_field":next((x for x in ("sb_total_deaths_best","sb_total_deaths_best_cy") if x in headers),None),
                        "requires_column_validation":True}
            raise ValueError("Unknown ZIP download contents")
    return describe_csv(data)

def inspect(fetch=request):
    raw=fetch(ARCHIVE)
    links=discover(raw.decode("utf8"))
    report={"schema":"idealab.psico.ucdp_archive_country_discovery.v1",
            "archive":ARCHIVE,"archive_sha256_at_inspection":sha(raw),
            "historical_availability_independently_certified":False,
            "versions":{}}
    for version in VERSIONS:
        choices=links.get(version,[])
        rec={"linked_formats":[{"format":x["format"],"url":x["url"]} for x in choices],
             "results":[]}
        # Only one chosen format per version: prefer CSV over Excel.
        chosen=next((x for x in choices if x["format"]=="CSV"),choices[0] if choices else None)
        if chosen:
            try:
                data=fetch(chosen["url"])
                basic={"url":chosen["url"],"download_status":"retrieved",
                       "sha256":sha(data),"bytes":len(data)}
                try:
                    basic.update(source_metadata(data,chosen["format"]))
                except ValueError as error:
                    basic["schema_status"]="NOT_YET_COMPATIBLE"
                    basic["schema_error"]=str(error)[:150]
                    if data[:2]==b"PK":
                        with zipfile.ZipFile(io.BytesIO(data)) as z:
                            basic["archive_members"]=[item.filename for item in z.infolist() if not item.is_dir()][:12]
                            csv_members=[item.filename for item in z.infolist() if item.filename.lower().endswith(".csv")]
                            if len(csv_members)==1:
                                first=z.read(csv_members[0],5000).decode("utf-8-sig").splitlines()[0]
                                basic["original_headers"]=first[:800]
                rec["results"].append(basic)
            except Exception as exc:
                rec["results"].append({"url":chosen["url"],
                                      "download_status":"unavailable",
                                      "error":type(exc).__name__})
        report["versions"][version]=rec
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report")
    args=p.parse_args()
    report=inspect()
    content=json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    print("UCDP_COUNTRY_VINTAGES_DISCOVERY_BEGIN")
    print(content,end="")
    print("UCDP_COUNTRY_VINTAGES_DISCOVERY_END")
    if args.report:
        from pathlib import Path
        Path(args.report).write_text(content,encoding="utf8")

if __name__=="__main__":main()
