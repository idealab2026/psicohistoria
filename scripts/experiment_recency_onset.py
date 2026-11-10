#!/usr/bin/env python3
"""Q-GEO-01: recency sensitivity within consistent UCDP COUNTRY-level onset releases.

All grid choices are exploratory and post-hoc (following observed 2024 results).
No vintage-19.1 conflict-level reconstruction is allowed in the model.
No country-level scores or identities are printed/persisted to public assets.
"""
from __future__ import annotations
import argparse
import json
import math
from collections import defaultdict
from inspect_ucdp_archives import fetch, digest, onset_labels
from run_legacy_vintage_holdout import SOURCES

CANDIDATE_WINDOWS = (5, 10, 20)
TRAIN_START = 2000
SHRINKAGE = 20
INTERNAL_TEST_YEARS = tuple(range(2015, 2023))
EXTERNAL_YEAR = 2024
EXTERNAL_CUTOFF = 2022
MIN_TARGET_COVERAGE = 150
VERSIONS = ("23.1", "25.1")

def verified_sources(fetcher=fetch):
    result={}
    for version in VERSIONS:
        expected=SOURCES[version]
        raw=fetcher(expected["url"],6_000_000)
        if digest(raw)!=expected["sha256"]:
            raise ValueError("Official country-level source hash mismatch: "+version)
        labels=onset_labels(raw)  # Country-level vintage must be exactly unique.
        if max(year for year,code in labels)!=expected["last_year"]:
            raise ValueError("Unexpected country-level source coverage: "+version)
        result[version]=labels
    return result

def frozen_probabilities(source, cutoff, universe, windows=CANDIDATE_WINDOWS):
    """Fit every candidate exclusively from historical information <=cutoff."""
    if tuple(windows)!=CANDIDATE_WINDOWS or not isinstance(cutoff,int) or cutoff<TRAIN_START+20:
        raise ValueError("Cannot change exploratory fixed grid or origin")
    history=[(year,code,y) for (year,code),y in source.items()
             if TRAIN_START<=year<=cutoff and code in universe]
    if not history or set(universe)!={code for year,code,y in history if year==cutoff}:
        raise ValueError("Incomplete fixed origin universe")
    def global_p(rows):
        return (sum(y for _,_,y in rows)+1)/(len(rows)+2)
    full=global_p(history)
    recent={}
    for w in windows:
        subset=[r for r in history if r[0]>cutoff-w]
        if not subset or min(r[0] for r in subset)!=cutoff-w+1:
            raise ValueError("Window does not cover required calendar years")
        recent[w]=global_p(subset)
    by_country=defaultdict(lambda:[0,0])
    for _,code,y in history:
        by_country[code][0]+=y
        by_country[code][1]+=1
    predictions={}
    for code in sorted(universe):
        count,k=by_country[code]
        item={"global_full":full,
              "country_full":(count+SHRINKAGE*full)/(k+SHRINKAGE)}
        for w,p in recent.items():
            item["global_"+str(w)]=p
            item["country_"+str(w)]=(count+SHRINKAGE*p)/(k+SHRINKAGE)
        predictions[code]=item
    return predictions,{"training_n":len(history),"training_events":sum(y for _,_,y in history),
                        "source_last_year_used":cutoff,
                        "full_global":full,
                        "recent_global_rates":{str(w):recent[w] for w in windows}}

def year_predictions(training, outcomes, cutoff, target_year):
    """Do not use any target-year label to estimate a probability."""
    if target_year<=cutoff or cutoff+2<target_year or target_year>2024:
        raise ValueError("Target is not within declared temporal envelope")
    # Explicit country-cohort selection based ONLY on training edition.
    universe={code for year,code in training if year==cutoff}
    if len(universe)<MIN_TARGET_COVERAGE:
        raise ValueError("Inadequate origin-year cohort")
    models,metadata=frozen_probabilities(training,cutoff,universe)
    actual={code:y for (year,code),y in outcomes.items() if year==target_year}
    common=universe & actual.keys()
    if len(common)<MIN_TARGET_COVERAGE or len(common)<len(universe)-10:
        raise ValueError("Insufficient target-country coverage")
    rows=[{"country":code,"year":target_year,"y":actual[code],**models[code]}
          for code in sorted(common)]
    return rows,{**metadata,"origin_universe":len(universe),"evaluated_n":len(rows),
                 "missing_from_target":len(universe)-len(common),"events":sum(x["y"] for x in rows)}

def scores(rows):
    if not rows:
        raise ValueError("No observations")
    labels={k for row in rows for k in row if k.startswith("global_") or k.startswith("country_")}
    answer={}
    for key in sorted(labels):
        probabilities=[row[key] for row in rows]
        if not all(0<p<1 and math.isfinite(p) for p in probabilities):
            raise ValueError("Non finite or boundary probability")
        brier=sum((p-row["y"])**2 for p,row in zip(probabilities,rows))/len(rows)
        logloss=sum(-(row["y"]*math.log(p)+(1-row["y"])*math.log1p(-p))
                    for p,row in zip(probabilities,rows))/len(rows)
        answer[key]={"brier":brier,"logloss":logloss}
    answer["no_event"]={"brier":sum(row["y"] for row in rows)/len(rows),
                        "logloss":None}
    return answer

def evaluate(vintages):
    early=vintages["23.1"]
    later=vintages["25.1"]
    internal=[]; all_internal=[]
    # Conservative 2-year label lag within the already revised 23.1 edition.
    for year in INTERNAL_TEST_YEARS:
        rows,metadata=year_predictions(early,early,year-2,year)
        internal.append({"year":year,"n":len(rows),"events":metadata["events"],
                         "training_end":year-2,"metrics":scores(rows)})
        all_internal.extend(rows)
    external_rows,metadata=year_predictions(early,later,EXTERNAL_CUTOFF,EXTERNAL_YEAR)
    all_models=scores(external_rows)
    aggregate=scores(all_internal)
    # All candidates must be retained regardless of their score. No selection.
    for key in aggregate:
        if key not in all_models:raise ValueError("Inconsistent candidate grids")
    return {
        "schema":"idealab.psico.recency_sensitivity.v1",
        "status":"EXPLORATORY_POSTHOC_NOT_PROSPECTIVE",
        "question":"Q-GEO-01",
        "source_urls":{v:SOURCES[v]["url"] for v in VERSIONS},
        "source_sha256":{v:SOURCES[v]["sha256"] for v in VERSIONS},
        "source_vintages":["23.1","25.1"],
        "legacy_19_1_excluded_due_to_country_year_unit_mismatch":True,
        "windows_years":list(CANDIDATE_WINDOWS),
        "training_start":TRAIN_START,
        "country_prior_strength":SHRINKAGE,
        "internally_revised_vintage":{
            "assessment":"SAME_VINTAGE_REVISED_DATA_LEAKAGE_NOT_HISTORICALLY_ASOF",
            "tested_years":list(INTERNAL_TEST_YEARS),
            "n":len(all_internal),"events":sum(x["y"] for x in all_internal),
            "per_year":internal,"pooled_metrics":aggregate
        },
        "cross_release_holdout_2024":{
            "assessment":"EXTERNAL_VINTAGE_LABELS_BUT_2024_PREVIOUSLY_EXAMINED",
            "year":EXTERNAL_YEAR,"training_last_year":EXTERNAL_CUTOFF,
            "n":len(external_rows),"events":metadata["events"],
            "metrics":all_models,
            "training_rates":metadata["recent_global_rates"],
            "training_full_global_rate":metadata["full_global"]
        },
        "prospective_forecasts_issued":0,
        "skill_demonstrated":False,
        "source_release_dates_verified":False,
        "new_independent_confirmatory_holdout":False,
        "conclusion":"Exploratory grid only. Model selection on these results would be post-hoc. The older 19.1 archive and the later 23.1 country-level set do not have demonstrated identical units of analysis; the 715-row mixed-vintage result is excluded from this assessment."
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--report")
    args=parser.parse_args()
    study=evaluate(verified_sources())
    rendered=json.dumps(study,ensure_ascii=False,indent=2,sort_keys=True)
    print(rendered)
    if args.report:
        from pathlib import Path
        path=Path(args.report).resolve()
        if ".git" in path.parts:
            raise ValueError("No reports in .git")
        path.write_text(rendered+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
