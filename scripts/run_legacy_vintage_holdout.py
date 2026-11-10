#!/usr/bin/env python3
"""UCDP historical cross-release model comparison, IDEA LAB Q-GEO-01.

Two fixed source/holdout designs; NO claim that forecasts were historically issued.
Only public aggregates are emitted. Never persist or print country-level predictions.
"""
from __future__ import annotations
from collections import defaultdict
import argparse
import json
import math
import random
from inspect_ucdp_archives import fetch, digest, onset_labels

SOURCES = {
    "19.1": {
        "url":"https://ucdp.uu.se/downloads/onset/onsets_computed.csv",
        "sha256":"ba54aeace175173b7643a2c14ba35ce89a2fcfd31712085e4fd13de656f752a8",
        "last_year":2018,
    },
    "23.1": {
        "url":"https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-onset-231.csv",
        "sha256":"e2cadfa7a87b3949f8c638c27381fbb1b44fb076ccb00570782252d0935a2289",
        "last_year":2022,
    },
    "25.1": {
        "url":"https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-onset-251.csv",
        "sha256":"e2b59e65aaca88403991465b78fb407d7eddcefadeb18c7f1397bfe2ea83fe6a",
        "last_year":2024,
    }
}
STUDIES = (
    {"origin":"19.1","outcome":"23.1","years":(2020,2021,2022)},
    {"origin":"23.1","outcome":"25.1","years":(2024,)},
)
START_TRAIN_YEAR=2000
REGULARIZATION=20
BOOTSTRAPS=2000
RANDOM_SEED=20261110

def load_sources(fetcher=fetch):
    data={}
    for version,src in SOURCES.items():
        raw=fetcher(src["url"],6_000_000)
        if digest(raw)!=src["sha256"]:
            raise ValueError("Refused altered official edition "+version)
        d=onset_labels(raw)
        if max(year for year,_ in d)!=src["last_year"]:
            raise ValueError("Unexpected last year of historical edition "+version)
        if len(d)<9000:
            raise ValueError("Unexpectedly small historical edition "+version)
        data[version]=d
    return data

def score(records,column):
    n=len(records)
    if not n:
        raise ValueError("No evaluation observations")
    brier=sum((r[column]-r["y"])**2 for r in records)/n
    def loss(row):
        p=min(1-1e-12,max(1e-12,row[column]))
        return -(row["y"]*math.log(p)+(1-row["y"])*math.log1p(-p))
    return {"brier":brier,"logloss":sum(loss(r) for r in records)/n}

def records_for_study(orig, final, origin_last, years, prior_strength=REGULARIZATION):
    if (not isinstance(prior_strength,(int,float)) or not math.isfinite(prior_strength)
        or prior_strength<=0):
        raise ValueError("Invalid prior strength")
    if any(y <= origin_last or y>origin_last+4 for y in years):
        raise ValueError("Temporal holdout not beyond archival vintage")
    training=[(year,code,y) for (year,code),y in orig.items()
              if START_TRAIN_YEAR<=year<=origin_last]
    if not training:
        raise ValueError("Empty historical training period")
    n=len(training)
    pos=sum(row[2] for row in training)
    global_prior=(pos+1)/(n+2)
    countries=defaultdict(lambda:[0,0])
    for year,code,y in training:
        countries[code][0]+=y
        countries[code][1]+=1
    origin_universe={code for year,code in orig if year==origin_last}
    if len(origin_universe)<150:
        raise ValueError("Origin country universe incomplete")
    output=[]
    for year in years:
        actual={code:y for (yr,code),y in final.items() if yr==year}
        shared=origin_universe & set(actual)
        if len(shared)<len(origin_universe)-10:
            raise ValueError("Insufficient covered origin countries in outcome vintage")
        for code in sorted(shared):
            count=countries[code][1]
            prior=(countries[code][0]+prior_strength*global_prior)/(count+prior_strength)
            output.append({"year":year,"country":code,"y":actual[code],
                           "model":prior,"global":global_prior,"no_event":0.0})
    return output,{"origin_universe_size":len(origin_universe),
                   "training_country_years":n,"training_events":pos,
                   "baseline_probability":global_prior}

def grouped_bootstrap(data, comparisons=("global","no_event"), replications=BOOTSTRAPS, seed=RANDOM_SEED):
    if replications<100:
        raise ValueError("Too few bootstrap replications")
    bycountry=defaultdict(list)
    for record in data:
        bycountry[record["country"]].append(record)
    codes=sorted(bycountry)
    rng=random.Random(seed)
    result={}
    for competitor in comparisons:
        draws=[]
        for _ in range(replications):
            country_sample=[rng.choice(codes) for i in range(len(codes))]
            total=0.0; n=0
            for code in country_sample:
                for row in bycountry[code]:
                    total+=(row["model"]-row["y"])**2 - (row[competitor]-row["y"])**2
                    n+=1
            draws.append(total/n)
        draws.sort()
        result[competitor]={"delta_brier_95pct_interval":[
            draws[int(.025*(replications-1))],draws[int(.975*(replications-1))]],
            "resampling_unit":"country","replications":replications}
    return result

def experiment(src):
    studies=[]; combined=[]
    for spec in STUDIES:
        origin,outcome=src[spec["origin"]],src[spec["outcome"]]
        scores,train=records_for_study(origin,outcome,SOURCES[spec["origin"]]["last_year"],spec["years"])
        tests=[]
        for year in spec["years"]:
            subset=[row for row in scores if row["year"]==year]
            tests.append({"year":year,"n":len(subset),"events":sum(r["y"] for r in subset),
                          "brier_model":score(subset,"model")["brier"],
                          "brier_global":score(subset,"global")["brier"],
                          "brier_no_event":score(subset,"no_event")["brier"],
                          "logloss_model":score(subset,"model")["logloss"],
                          "logloss_global":score(subset,"global")["logloss"]})
        studies.append({"origin_version":spec["origin"],"outcome_version":spec["outcome"],
                        **train,"years":tests})
        combined.extend(scores)
    model=score(combined,"model")
    global_=score(combined,"global")
    zero=score(combined,"no_event")
    positive=sum(row["y"] for row in combined)
    return {
        "schema":"idealab.psico.cross_release_external_holdout.v1",
        "status":"RETROSPECTIVE_CROSS_RELEASE_NOT_HISTORICALLY_ISSUED",
        "question":"Q-GEO-01",
        "target":"UCDP intrastate country level onset2 across all available origin countries",
        "training_since":START_TRAIN_YEAR,
        "country_prior_strength":REGULARIZATION,
        "sources":{k:{"url":v["url"],"sha256":v["sha256"],"last_year":v["last_year"]}
                   for k,v in SOURCES.items()},
        "studies":studies,
        "aggregate":{"country_years":len(combined),"events":positive,
                     "brier_model":model["brier"],"brier_global":global_["brier"],
                     "brier_no_event":zero["brier"],
                     "logloss_model":model["logloss"],"logloss_global":global_["logloss"],
                     "relative_brier_skill_global":1-model["brier"]/global_["brier"],
                     "cluster_bootstrap":grouped_bootstrap(combined)},
        "historical_release_timing_cryptographically_verified":False,
        "prospective_predictions_issued":0,
        "operational_utility_demonstrated":False,
        "disclaimer":"The model never saw holdout labels during fitting, but this study was conducted ex post in 2026. Publication date of archived releases has not been cryptographically verified. This is not an actual historical issue, and any comparisons are exploratory rather than prospective."
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--report")
    args=ap.parse_args()
    summary=experiment(load_sources())
    text=json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)
    print(text)
    if args.report:
        from pathlib import Path
        p=Path(args.report).resolve()
        if ".git" in p.parts:
            raise ValueError("Refusing to persist research report inside .git")
        p.write_text(text+"\n",encoding="utf8")

if __name__=="__main__":main()
