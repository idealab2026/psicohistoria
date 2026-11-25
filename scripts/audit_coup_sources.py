#!/usr/bin/env python3
"""Audit official coup data bytes and metadata only, before modelling."""
import csv,hashlib,io,json,re,zipfile
from datetime import datetime,timezone
from html.parser import HTMLParser
from urllib.parse import urlsplit,urljoin
from urllib.request import Request,urlopen
from xml.etree import ElementTree as ET
PAGE="https://jonathanmpowell.com/coups/"
POWELL={
 "2026-08-29":"https://jonathanmpowell.com/wp-content/uploads/2026/08/pt_20260829.csv",
 "2026-07-08":"https://jonathanmpowell.com/wp-content/uploads/2026/08/pt_20260708-1.xlsx",
}
DOIS={8:"2.2.0",9:"2.2.1",10:"2.2.2"}
MAX=15_000_000
class Links(HTMLParser):
    def __init__(self,base): super().__init__();self.base=base;self.links=set()
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            href=dict(attrs).get("href")
            if href:self.links.add(urljoin(self.base,href))
def fetch(url):
    host=urlsplit(url).netloc
    if urlsplit(url).scheme!="https" or host not in ("jonathanmpowell.com","api.datacite.org","databank.illinois.edu"):
        raise ValueError("Unregistered institutional source")
    with urlopen(Request(url,headers={"User-Agent":"IDEA-LAB-institutional-science-audit/1.0"}),timeout=45) as response:
        if response.url!=url: raise ValueError("Unexpected redirect")
        raw=response.read(MAX+1)
    if not raw or len(raw)>MAX: raise ValueError("Source size invalid")
    return raw
def meta(raw): return {"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
def csv_schema(raw):
    header=next(csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline="")),[])
    if len(header)<3 or len(header)!=len(set(header)) or any(not re.fullmatch(r"[A-Za-z][A-Za-z0-9_. ()/\-]{0,60}",x) for x in header):
        raise ValueError("Unrecognized CSV header")
    return {"header":header,"columns":len(header)}
def xlsx_schema(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        items=z.infolist()
        if sum(i.file_size for i in items)>100_000_000 or any(i.filename.startswith("/") or ".." in i.filename.split("/") for i in items):
            raise ValueError("Unsafe workbook archive")
        ns={"s":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        root=ET.fromstring(z.read("xl/workbook.xml"))
        sheets=root.findall(".//s:sheet",ns)
        if not sheets: raise ValueError("No worksheet")
        # Only structural inventory. Do not read shared strings or event rows.
        return {"sheet_count":len(sheets),"worksheet_members":len([i for i in items if re.fullmatch(r"xl/worksheets/sheet\d+\.xml",i.filename)])}
def doi_metadata(raw,expected):
    d=json.loads(raw)["data"]["attributes"]
    if d["doi"].lower()!=expected.lower() or d.get("types",{}).get("resourceTypeGeneral")!="Dataset":
        raise ValueError("Wrong DOI identity or resource type")
    url=d["url"]
    if urlsplit(url).scheme!="https" or urlsplit(url).netloc!="databank.illinois.edu":
        raise ValueError("Unexpected DOI landing host")
    return {"doi":d["doi"],"landing_url":url,"publication_year":d.get("publicationYear"),
        "version_field":d.get("version"),"dates":[{"date":x.get("date"),"type":x.get("dateType")} for x in d.get("dates",[])]}
def capture():
    page=fetch(PAGE);links=Links(PAGE);links.feed(page.decode("utf8"))
    out=[]
    for date,url in POWELL.items():
        e={"provider":"Powell-Thyne","archive_label":date,"url":url,"linked_by_author":url in links.links}
        try:
            if not e["linked_by_author"]: raise ValueError("Author link absent")
            raw=fetch(url);e.update(meta(raw))
            e.update(csv_schema(raw) if url.endswith(".csv") else xlsx_schema(raw))
            e["status"]="ORIGINAL_BYTES_OBSERVED"
        except (ValueError,OSError,zipfile.BadZipFile,ET.ParseError) as exc:
            e.update(status="BLOCKED",error_type=type(exc).__name__,http_status=getattr(exc,"code",None))
        out.append(e)
    for i,v in DOIS.items():
        doi=f"10.13012/B2IDB-9651987_V{i}"
        e={"provider":"Cline Center","expected_version":v,"doi":doi}
        try:
            raw=fetch("https://api.datacite.org/dois/"+doi)
            e.update(doi_metadata(raw,doi),metadata_sha256=meta(raw)["sha256"])
            # DOI metadata is not the original CSV. Record landing accessibility only.
            landing=e["landing_url"]
            try:
                original=fetch(landing);e["landing_metadata_sha256"]=meta(original)["sha256"]
                parser=Links(landing);parser.feed(original.decode("utf8"))
                e["csv_link_count"]=sum(urlsplit(x).path.lower().endswith(".csv") for x in parser.links)
            except (ValueError,OSError) as exc:
                e["landing_http_status"]=getattr(exc,"code",None)
                e["landing_error_type"]=type(exc).__name__
            e["status"]="DOI_METADATA_ONLY_NO_DATA_BYTES"
        except (ValueError,OSError,KeyError) as exc:
            e.update(status="BLOCKED",error_type=type(exc).__name__,http_status=getattr(exc,"code",None))
        out.append(e)
    return {"status":"SOURCE_CENSUS_ONLY_NO_OUTCOMES","author_page_sha256":meta(page)["sha256"],
      "observed_at_utc":datetime.now(timezone.utc).isoformat(),"sources":out,
      "new_forecasts":0,"modified_forecasts":0,"outcomes_read":0}
if __name__=="__main__":
    d=capture();print("COUP_CENSUS_BEGIN");print(json.dumps(d,sort_keys=True,indent=2));print("COUP_CENSUS_END")
    if not any(x["status"]=="ORIGINAL_BYTES_OBSERVED" for x in d["sources"]): raise ValueError("No original data bytes available")
