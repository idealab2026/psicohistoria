#!/usr/bin/env python3
"""FIN-01 preregistered monthly downside retrospective benchmark."""
import csv, hashlib, io, json, math, re, statistics, zipfile
from collections import defaultdict
from decimal import Decimal
from urllib.request import Request, urlopen

URL="https://mba.tuck.dartmouth.edu/pages/faculty/Ken.french/ftp_202412/F-F_Research_Data_Factors_CSV.zip"
MODELS=("global","recent","normal_vol","vol_regime","joint_regime")
THRESHOLD=-0.05
LIMIT=10_000_000

def month_index(s):
    if not re.fullmatch(r"[0-9]{6}",s): raise ValueError("Invalid month")
    y,m=int(s[:4]),int(s[4:])
    if not 1<=m<=12: raise ValueError("Invalid month")
    return 12*y+m-1

def month_name(i):
    y,m=divmod(i,12)
    return f"{y:04d}-{m+1:02d}"

def retrieve():
    with urlopen(Request(URL,headers={"User-Agent":"IDEA-LAB-institutional-science-audit/1.0"}),timeout=60) as response:
        if response.url!=URL: raise ValueError("Unexpected source redirect")
        raw=response.read(LIMIT+1)
    if not raw or len(raw)>LIMIT: raise ValueError("Source size invalid")
    return raw

def parse(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        items=z.infolist()
        if sum(i.file_size for i in items)>20_000_000 or any(i.filename.startswith("/") or ".." in i.filename.split("/") for i in items):
            raise ValueError("Unsafe ZIP")
        files=[i for i in items if i.filename.lower().endswith(".csv")]
        if len(files)!=1: raise ValueError("Expected one CSV")
        text=z.read(files[0]).decode("utf-8-sig")
    out={}; started=False; done=False
    for row in csv.reader(io.StringIO(text)):
        if not started:
            if [x.strip() for x in row]==["","Mkt-RF","SMB","HML","RF"]:
                started=True
            continue
        if not row or not row[0].strip():
            if out: done=True
            continue
        s=row[0].strip()
        if not re.fullmatch(r"[0-9]{6}",s):
            if out: done=True
            continue
        if done: raise ValueError("Unexpected monthly rows after section")
        if len(row)!=5: raise ValueError("Unexpected monthly fields")
        idx=month_index(s)
        vals=[Decimal(x.strip()) for x in row[1:]]
        if any(not x.is_finite() or abs(x)>=Decimal("99") for x in vals) or idx in out:
            raise ValueError("Missing or invalid factor or duplicate date")
        total=(vals[0]+vals[3])/100
        if not -1<total<1: raise ValueError("Unexpected market return")
        out[idx]=float(total)
    first,last=month_index("192607"),month_index("202412")
    if set(out)!=set(range(first,last+1)): raise ValueError("Monthly coverage not exactly 1926-07..2024-12")
    return out,files[0].filename

def label(x):
    return int(x<=THRESHOLD)

def features(values,t):
    # Feature information available only through target month minus two.
    x=[values[j] for j in range(t-13,t-1)]
    vol=statistics.stdev(x)
    mom=math.prod(1+v for v in x[-3:])-1
    return vol,(int(vol>=.05),int(mom<0))

def probability(p):
    return min(.999,max(.001,p))

def predict(values,t):
    first=min(values)
    past=[label(values[j]) for j in range(first,t-1)]
    if len(past)<120: raise ValueError("Insufficient training")
    recent=(sum(past[-120:])+1)/122
    vol,key=features(values,t)
    normal=0.0 if vol==0 else .5*math.erfc(.05/(vol*math.sqrt(2)))
    groups=[[],[]]
    for j in range(first+13,t-1):
        _,k=features(values,j)
        if k[0]==key[0]: groups[0].append(label(values[j]))
        if k==key: groups[1].append(label(values[j]))
    return dict(zip(MODELS,map(probability,[(sum(past)+1)/(len(past)+2),recent,normal,
                (sum(groups[0])+24*recent)/(len(groups[0])+24),
                (sum(groups[1])+24*recent)/(len(groups[1])+24)])))

def losses(p,y):
    return ((p-y)**2,-math.log(p) if y else -math.log1p(-p))

def summary(rows):
    if not rows: raise ValueError("Empty evaluation")
    n=len(rows)
    models={}
    for m in MODELS:
        vals=[losses(p[m],y) for t,y,p in rows]
        models[m]={"brier":sum(x[0] for x in vals)/n,"log_loss":sum(x[1] for x in vals)/n,
                   "mean_probability":sum(p[m] for t,y,p in rows)/n}
    base=models["recent"]["brier"]
    for m in MODELS:
        models[m]["brier_skill_vs_recent"]=1-models[m]["brier"]/base
        models[m]["log_loss_gain_vs_recent"]=models["recent"]["log_loss"]-models[m]["log_loss"]
    return {"n":n,"positives":sum(y for t,y,p in rows),"observed_rate":sum(y for t,y,p in rows)/n,"models":models}

def evaluate(values):
    rows=[(t,label(values[t]),predict(values,t)) for t in range(month_index("199001"),month_index("202412")+1)]
    result=summary(rows)
    result["periods"]={f"{a}-{b}":summary([row for row in rows if a<=row[0]//12<=b]) for a,b in [(1990,2004),(2005,2014),(2015,2024)]}
    result["years"]={str(y):summary([row for row in rows if row[0]//12==y]) for y in range(1990,2025)}
    for m in ("vol_regime","joint_regime"):
        gains=[]
        for year in range(1990,2025):
            s=summary([row for row in rows if row[0]//12!=year])
            gains.append(s["models"][m]["brier_skill_vs_recent"])
        result["models"][m]["leave_one_year_out_skill_range"]=[min(gains),max(gains)]
    return result

def run():
    raw=retrieve()
    values,member=parse(raw)
    return {"status":"RETROSPECTIVE_REVISED_SOURCE_NOT_ASOF_NOT_PROSPECTIVE",
        "source":{"url":URL,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"csv_member":member,
        "first_month":month_name(min(values)),"last_month":month_name(max(values)),"months":len(values)},
        "endpoint":"US_BROAD_MARKET_MONTHLY_TOTAL_RETURN_LE_MINUS_5_PERCENT",
        "feature_lag_months":2,"results":evaluate(values),
        "new_forecasts":0,"modified_forecasts":0,"trading_strategies_tested":0}

if __name__=="__main__":
    print("FIN01_BEGIN",flush=True)
    print(json.dumps(run(),sort_keys=True,indent=2))
    print("FIN01_END",flush=True)
