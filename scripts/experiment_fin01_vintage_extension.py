#!/usr/bin/env python3
"""FIN-01 vintage sensitivity and fixed temporal extension; no issuance."""
import hashlib, json
from pathlib import Path
from urllib.request import Request,urlopen
from html.parser import HTMLParser
from urllib.parse import urljoin
from experiment_fin01_monthly_downside import (URL,LIMIT,parse,month_index,month_name,
    label,predict,summary,evaluate)

ROOT=Path(__file__).resolve().parents[1]
CATALOGUE="https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors_archive.html"
BASE="https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/Historical_Archives/"
SOURCES={
    "202407":BASE+"08%202024%20Update/ftp/F-F_Research_Data_Factors_CSV.zip",
    "202507":BASE+"08%202025%20Update/ftp/F-F_Research_Data_Factors_CSV.zip",
    "202608":BASE+"09%202026%20Update/ftp/F-F_Research_Data_Factors_CSV.zip",
}

class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.urls=set()
    def handle_starttag(self,tag,attrs):
        if tag=="a" and dict(attrs).get("href"):
            self.urls.add(urljoin(CATALOGUE,dict(attrs)["href"]))

def get(url):
    if url not in (CATALOGUE,URL,*SOURCES.values()):
        raise ValueError("Unregistered source")
    with urlopen(Request(url,headers={"User-Agent":"IDEA-LAB-institutional-science-audit/1.0"}),timeout=60) as response:
        if response.url!=url: raise ValueError("Unexpected redirect")
        raw=response.read(LIMIT+1)
    if not raw or len(raw)>LIMIT: raise ValueError("Source size invalid")
    return raw

def load(raw,end,url):
    values,member=parse(raw,end)
    return values,{"url":url,"sha256":hashlib.sha256(raw).hexdigest(),
                   "bytes":len(raw),"csv_member":member,"last_month":month_name(max(values)),
                   "months":len(values)}

def revisions(old,new):
    keys=sorted(old)
    if not keys or not set(keys)<=set(new): raise ValueError("Incomplete overlap")
    diff=[abs(old[k]-new[k]) for k in keys]
    changed=[k for k in keys if label(old[k])!=label(new[k])]
    return {"n":len(keys),"return_changes":sum(x>1e-12 for x in diff),
            "label_changes":len(changed),"evaluation_label_changes":sum(k>=month_index("199001") for k in changed),
            "max_abs_return_difference":max(diff),"mean_abs_return_difference":sum(diff)/len(diff)}

def one_month(train,outcomes,target):
    t=month_index(target)
    if max(train)!=t-2 or t not in outcomes:
        raise ValueError("Invalid source-separated dates")
    p=predict(train,t)
    return {"target_month":month_name(t),"training_last_month":month_name(max(train)),
            "result":summary([(t,label(outcomes[t]),p)])}

def run():
    catalogue=get(CATALOGUE);links=Links();links.feed(catalogue.decode("utf-8"))
    if not set(SOURCES.values())<=links.urls:
        raise ValueError("Official archive links changed")
    old,oldmeta=load(get(URL),"202412",URL)
    frozen=json.loads((ROOT/"data/fin01-monthly-downside.json").read_text())
    if oldmeta["sha256"]!=frozen["source"]["sha256"]:
        raise ValueError("Frozen FIZ source changed")
    data={};meta={}
    for end,url in SOURCES.items():
        data[end],meta[end]=load(get(url),end,url)
    new=data["202608"]
    historical=evaluate(new)
    extension=summary([(t,label(new[t]),predict(new,t)) for t in range(month_index("202501"),month_index("202608")+1)])
    return {"status":"RETROSPECTIVE_SOURCE_VINTAGE_AND_TEMPORAL_EXTENSION_NO_ISSUE",
        "catalogue_sha256":hashlib.sha256(catalogue).hexdigest(),"sources":{"202412":oldmeta,**meta},
        "revision_sensitivity":revisions(old,new),"ciz_1990_2024":historical,
        "ciz_2025_2026":extension,
        "dated_source_tests":[one_month(data["202407"],data["202507"],"202409"),
                              one_month(data["202507"],new,"202509")],
        "new_forecasts":0,"modified_forecasts":0}

if __name__=="__main__":
    print("FIN01_VINTAGES_BEGIN",flush=True)
    print(json.dumps(run(),sort_keys=True,indent=2))
    print("FIN01_VINTAGES_END",flush=True)
