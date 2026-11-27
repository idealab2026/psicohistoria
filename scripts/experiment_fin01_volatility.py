#!/usr/bin/env python3
"""FIN-01B fixed monthly realized-volatility benchmark; no issuance."""
import csv, hashlib, io, json, math, re, zipfile, sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from urllib.request import Request,urlopen
from experiment_fin01_monthly_downside import month_index,month_name

URL="https://mba.tuck.dartmouth.edu/pages/faculty/Ken.french/ftp_202412/F-F_Research_Data_Factors_daily_CSV.zip"
MODELS=("global","trailing12","last_month","ewma94","har_proxy")
LIMIT=20_000_000

def retrieve():
    with urlopen(Request(URL,headers={"User-Agent":"IDEA-LAB-institutional-science-audit/1.0"}),timeout=60) as response:
        if response.url!=URL: raise ValueError("Unexpected redirect")
        raw=response.read(LIMIT+1)
    if not raw or len(raw)>LIMIT: raise ValueError("Invalid archive size")
    return raw

def parse(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        items=z.infolist()
        if sum(i.file_size for i in items)>40_000_000 or any(i.filename.startswith("/") or ".." in i.filename.split("/") for i in items):
            raise ValueError("Unsafe ZIP")
        files=[i for i in items if i.filename.lower().endswith(".csv")]
        if len(files)!=1: raise ValueError("Expected one CSV")
        text=z.read(files[0]).decode("utf-8-sig")
    out=defaultdict(list);started=False;done=False;prior=""
    for row in csv.reader(io.StringIO(text)):
        if not started:
            if [x.strip() for x in row]==["","Mkt-RF","SMB","HML","RF"]:
                started=True
            continue
        if not row or not re.fullmatch(r"[0-9]{8}",row[0].strip()):
            if out: done=True
            continue
        if done or len(row)!=5: raise ValueError("Invalid daily section")
        s=row[0].strip();d=datetime.strptime(s,"%Y%m%d")
        if s<=prior or d.weekday()>5: raise ValueError("Duplicate, unordered or Sunday observation")
        prior=s
        vals=[Decimal(x.strip()) for x in row[1:]]
        if any(not x.is_finite() or abs(x)>=Decimal("99") for x in vals):
            raise ValueError("Missing or invalid factor")
        total=(vals[0]+vals[3])/100
        if not -1<total<1: raise ValueError("Unexpected return")
        out[month_index(s[:6])].append(float(total)**2)
    if set(out)!=set(range(month_index("192607"),month_index("202412")+1)):
        raise ValueError("Unexpected monthly coverage")
    counts={t:len(v) for t,v in out.items()}
    if any(n<15 or n>31 for t,n in counts.items() if t>=month_index("195001")):
        raise ValueError("Suspicious daily coverage")
    variances={t:math.fsum(v) for t,v in out.items()}
    if any(x<=0 or not math.isfinite(x) for x in variances.values()):
        raise ValueError("Nonpositive realized variance")
    return variances,{"csv_member":files[0].filename,"daily_rows":sum(counts.values()),
                      "months":len(counts),"first_month":month_name(min(counts)),
                      "last_month":month_name(max(counts)),
                      "min_daily_rows_since_1950":min(n for t,n in counts.items() if t>=month_index("195001"))}

def predict(values,t):
    past=[values[j] for j in range(month_index("195001"),t-1)]
    if len(past)<12 or any(x<=0 or not math.isfinite(x) for x in past):
        raise ValueError("Invalid training history")
    last=past[-1];avg3=math.fsum(past[-3:])/3;avg12=math.fsum(past[-12:])/12
    ewma=past[0]
    for v in past[1:]: ewma=.94*ewma+.06*v
    return dict(zip(MODELS,[math.fsum(past)/len(past),avg12,last,ewma,(last+avg3+avg12)/3]))

def loss(p,y):
    if not (p>0 and y>0 and math.isfinite(p) and math.isfinite(y)):
        raise ValueError("Invalid variance")
    z=y/p
    return z-math.log(z)-1,abs(math.sqrt(p)-math.sqrt(y))

def summary(rows):
    if not rows: raise ValueError("Empty evaluation")
    models={};n=len(rows)
    for m in MODELS:
        losses=[loss(p[m],y) for t,y,p in rows]
        models[m]={"qlike":math.fsum(x[0] for x in losses)/n,
                   "volatility_mae":math.fsum(x[1] for x in losses)/n,
                   "mean_predicted_monthly_volatility":math.fsum(math.sqrt(p[m]) for t,y,p in rows)/n}
    base=models["trailing12"]
    for s in models.values():
        s["qlike_skill_vs_trailing12"]=1-s["qlike"]/base["qlike"] if base["qlike"] else None
        s["mae_skill_vs_trailing12"]=1-s["volatility_mae"]/base["volatility_mae"] if base["volatility_mae"] else None
    return {"n":n,"mean_observed_monthly_volatility":math.fsum(math.sqrt(y) for t,y,p in rows)/n,"models":models}

def evaluate(values):
    rows=[(t,values[t],predict(values,t)) for t in range(month_index("199001"),month_index("202412")+1)]
    report=summary(rows)
    report["periods"]={f"{a}-{b}":summary([row for row in rows if a<=row[0]//12<=b]) for a,b in [(1990,2004),(2005,2014),(2015,2024)]}
    report["years"]={str(y):summary([row for row in rows if row[0]//12==y]) for y in range(1990,2025)}
    return report

def run():
    raw=retrieve();values,meta=parse(raw)
    return {"status":"RETROSPECTIVE_REVISED_SOURCE_NOT_ASOF_NOT_PROSPECTIVE",
        "source":{"url":URL,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),**meta},
        "endpoint":"MONTHLY_REALIZED_VARIANCE_SUM_DAILY_MARKET_TOTAL_RETURNS_SQUARED",
        "feature_lag_months":2,"results":evaluate(values),
        "new_forecasts":0,"modified_forecasts":0,"trading_strategies_tested":0}

if __name__=="__main__":
    print("FIN01_VOL_BEGIN",flush=True)
    report=run()
    if "--check" in sys.argv and report!=json.loads((Path(__file__).resolve().parents[1]/"data/fin01-volatility.json").read_text()):
        raise ValueError("Frozen volatility benchmark differs")
    print(json.dumps(report,sort_keys=True,indent=2))
    print("FIN01_VOL_END",flush=True)
