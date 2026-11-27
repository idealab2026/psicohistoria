#!/usr/bin/env python3
"""FIN-01 lag sensitivity and source admission census, not an issuance."""
import hashlib, json, math, statistics
from datetime import datetime, timezone
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin
from urllib.request import Request,urlopen
from experiment_fin01_monthly_downside import (
    MODELS, LIMIT, retrieve, parse, month_index, month_name, label,
    probability, predict, summary)

ROOT=Path(__file__).resolve().parents[1]
PAGE="https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html"
LIVE="https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip"

def features(values,t,lag):
    x=[values[j] for j in range(t-lag-11,t-lag+1)]
    vol=statistics.stdev(x)
    mom=math.prod(1+v for v in x[-3:])-1
    return vol,(int(vol>=.05),int(mom<0))

def lag_predict(values,t,lag):
    if lag not in (2,3): raise ValueError("Unregistered lag")
    first=min(values)
    past=[label(values[j]) for j in range(first,t-lag+1)]
    if len(past)<120: raise ValueError("Insufficient training")
    recent=(sum(past[-120:])+1)/122
    vol,key=features(values,t,lag)
    normal=0.0 if vol==0 else .5*math.erfc(.05/(vol*math.sqrt(2)))
    groups=[[],[]]
    for j in range(first+lag+11,t-lag+1):
        _,k=features(values,j,lag)
        if k[0]==key[0]: groups[0].append(label(values[j]))
        if k==key: groups[1].append(label(values[j]))
    return dict(zip(MODELS,map(probability,[(sum(past)+1)/(len(past)+2),recent,normal,
                (sum(groups[0])+24*recent)/(len(groups[0])+24),
                (sum(groups[1])+24*recent)/(len(groups[1])+24)])))

def benchmark(values,frozen):
    out={}
    for lag in (2,3):
        rows=[]
        for t in range(month_index("199001"),month_index("202412")+1):
            p=lag_predict(values,t,lag)
            if lag==2 and p!=predict(values,t):
                raise ValueError("Original model changed")
            rows.append((t,label(values[t]),p))
        result=summary(rows)
        if lag==2 and any(result["models"][m][k]!=frozen["results"]["models"][m][k]
                          for m in MODELS for k in ("brier","log_loss","mean_probability")):
            raise ValueError("Frozen original losses changed")
        result["periods"]={f"{a}-{b}":summary([row for row in rows if a<=row[0]//12<=b])
                           for a,b in [(1990,2004),(2005,2014),(2015,2024)]}
        for s in [result,*result["periods"].values()]:
            global_brier=s["models"]["global"]["brier"]
            for model in s["models"].values():
                model["brier_skill_vs_global"]=1-model["brier"]/global_brier
        out[str(lag)]=result
    return out

class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.urls=set()
    def handle_starttag(self,tag,attrs):
        href=dict(attrs).get("href")
        if tag=="a" and href: self.urls.add(urljoin(PAGE,href))

def get(url):
    if url not in (PAGE,LIVE): raise ValueError("Unregistered source")
    with urlopen(Request(url,headers={"User-Agent":"IDEA-LAB-institutional-science-audit/1.0"}),timeout=60) as response:
        if response.url!=url: raise ValueError("Unexpected redirect")
        raw=response.read(LIMIT+1)
    if not raw or len(raw)>LIMIT: raise ValueError("Invalid source size")
    return raw

def source_census():
    page=get(PAGE);links=Links();links.feed(page.decode("utf-8"))
    if LIVE not in links.urls: raise ValueError("Official current archive link missing")
    raw=get(LIVE); matches=[]
    for end in ("202609","202610"):
        try: values,member=parse(raw,end)
        except ValueError: continue
        matches.append((values,member))
    if len(matches)!=1: raise ValueError("Current source coverage or schema unadmitted")
    values,member=matches[0]
    target=month_index("202612")
    return {"status":"INPUT_COVERAGE_ONLY_NO_FORECAST",
        "observed_at_utc":datetime.now(timezone.utc).isoformat(),
        "url":LIVE,"catalogue_sha256":hashlib.sha256(page).hexdigest(),
        "sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"csv_member":member,
        "first_month":month_name(min(values)),"last_month":month_name(max(values)),
        "months":len(values),"december_lag2_inputs_present":max(values)>=target-2,
        "december_lag3_inputs_present":max(values)>=target-3}

def run():
    frozen=json.loads((ROOT/"data/fin01-monthly-downside.json").read_text())
    raw=retrieve()
    if hashlib.sha256(raw).hexdigest()!=frozen["source"]["sha256"]:
        raise ValueError("Frozen source changed")
    values,_=parse(raw)
    result=benchmark(values,frozen)
    try: current=source_census()
    except (ValueError,OSError) as exc:
        current={"status":"BLOCKED_NO_CURRENT_SOURCE_ADMISSION","error_type":type(exc).__name__,
                 "http_status":getattr(exc,"code",None)}
    return {"status":"RETROSPECTIVE_PUBLICATION_LAG_SENSITIVITY_NO_ISSUE",
            "source_sha256":frozen["source"]["sha256"],"lags":result,"current_source":current,
            "new_forecasts":0,"modified_forecasts":0}

if __name__=="__main__":
    print("FIN01_LAG_BEGIN",flush=True)
    print(json.dumps(run(),sort_keys=True,indent=2))
    print("FIN01_LAG_END",flush=True)
