#!/usr/bin/env python3
"""Monthly homogeneous panel, fixed models, 2023 training ablation."""
import sys
import json
from pathlib import Path
from audit_candidate_monthly_bridge import build,check_report,YEARS,THRESHOLDS
from experiment_annual_ged_rolling_probability import predict,summary,decompose_q1_gain
def validate_panel(panel):
    keys={(x[0],x[1]) for x in panel}
    ids=[{x[1] for x in panel if x[0]==year} for year in YEARS]
    if len(panel)!=784 or len(keys)!=784 or len(ids[0])!=196 or any(x!=ids[0] for x in ids):
        raise ValueError("Invalid homogeneous monthly country-year panel")
    if set(x[0] for x in panel)!=set(YEARS) or any(
        any(type(v) is not int or v<0 for v in x[2:]) or x[3]>x[4] for x in panel):
        raise ValueError("Invalid panel year or count")
def evaluate(panel):
    validate_panel(panel)
    results=[]
    for t in THRESHOLDS:
        for h in (30,90):
            col=3 if h==30 else 4
            folds=[]; pooled_p=[]; pooled_y=[]
            for origin,years in ((2023,(2021,)),(2025,(2021,2022,2023))):
                train=[x for x in panel if x[0] in years and x[2]<t]
                test=[x for x in panel if x[0]==origin and x[2]<t]
                if set(x[0] for x in train)!=set(years):
                    raise ValueError("Missing historical risk cohort")
                p=predict(train,test,origin,t,h)
                y=[int(x[col]>=t) for x in test]
                fold={"origin":origin,"train_years":list(years),"n_train":len(train),
                    "n_test":len(test),"positives":sum(y),"scores":summary(p,y),
                    "q1_gain_by_outcome":decompose_q1_gain(p,y)}
                if origin==2025:
                    ablated=[x for x in train if x[0]!=2023]
                    p0=predict(ablated,test,origin,t,h)
                    fold["without_2023"]={"train_years":[2021,2022],"n_train":len(ablated),
                        "scores":summary(p0,y),"q1_gain_by_outcome":decompose_q1_gain(p0,y)}
                folds.append(fold);pooled_p+=p;pooled_y+=y
            results.append({"threshold":t,"horizon":h,"folds":folds,
                "n_test":len(pooled_y),"positives":sum(pooled_y),"scores":summary(pooled_p,pooled_y),
                "q1_gain_by_outcome":decompose_q1_gain(pooled_p,pooled_y)})
    return {"status":"EXPLORATORY_MONTHLY_NOT_ASOF_NOT_ISSUED","years":list(YEARS),
        "excluded_year":2024,"new_forecasts":0,"modified_forecasts":0,"results":results}
if __name__=="__main__":
    report,panel=build(include_panel=True)
    check_report(report)
    result=evaluate(panel)
    if "--check" in sys.argv:
        expected=json.loads((Path(__file__).resolve().parents[1]/"data/candidate-monthly-probability.json").read_text())
        if result!=expected: raise ValueError("Frozen monthly probability report mismatch")
    print("MONTHLY_PROBABILITY_BEGIN")
    print(json.dumps(result,sort_keys=True,indent=2))
    print("MONTHLY_PROBABILITY_END")
