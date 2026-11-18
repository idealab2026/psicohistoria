#!/usr/bin/env python3
"""GEO H2 vintage-based origin-state uncertainty: frozen editorial rates.

Estimate (old category 0->later 1, old 1->later 0) from *only* consecutive
UCDP editions 23.1->24.1 and 24.1->25.1, country-years <=2021.
Jeffreys Beta(.5,.5) pooled pseudo-counts chosen before evaluation.
Hold out edition 25.1->26.1 to test revision occurrence, NOT true-state
accuracy. Never treat editorial revision probabilities as P(true state).
Use frozen rates in an unscored 2027 shadow and a retrospective diagnostic.
No reissuance of original GEO2027/GEO2028 vectors.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

from audit_geo2027_global_only_matched_issue import (
    ISSUE,MANIFEST,OLD_SHADOW,OLD_MANIFEST,ORIGINAL,ALERTS,
    audit as audit_issued,
)
from backtest_archived_country_vintages import SOURCES
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD,EXPECTED_ROWS,VERSION_ORDER,STATES,ACTIVE,LAPLACE,
    SHRINK,intensity_state,parse_counts,four_state_forecast,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH,SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"data/geo-h2-empirical-origin-revision-rate-2027-shadow.json"
ANCHOR=ROOT/"data/geo-h2-origin-state-10pct-uncertainty-shadow.json"
TRAIN_PAIRS=(("23.1","24.1"),("24.1","25.1"))
HOLDOUT_PAIR=("25.1","26.1")
CUTOFF=2021
N=196
TRAIN_N=199
ALPHA=.5
ORIGINS=tuple(range(2012,2023))
PROSPECTIVE_ORIGIN=2025
EPS=1e-10


def revision_event(a,b):
    """Only asymmetric 0<->low state revisions, not all category changes."""
    if type(a) is not int or type(b) is not int or a<0 or b<0:
        raise ValueError("Counts must be nonnegative official integers")
    return intensity_state(a),intensity_state(b)


def state_revision_counts(old,new,year_cutoff=CUTOFF):
    if set(old)!=set(new) or len(old)!=TRAIN_N:
        raise ValueError("Incorrect source-country universe")
    out={0:{"n":0,"cross_to_adjacent":0},1:{"n":0,"cross_to_adjacent":0}}
    examples=[]
    for cid in sorted(old):
        older={y:v for y,v in old[cid].items() if y<=year_cutoff}
        newer={y:v for y,v in new[cid].items() if y<=year_cutoff}
        if set(older)!=set(newer):
            raise ValueError("Country-year mismatch: cannot impute absent records")
        for yr,a in sorted(older.items()):
            prev,following=revision_event(a,newer[yr])
            if prev in (0,1):
                out[prev]["n"]+=1
                if following==1-prev:
                    out[prev]["cross_to_adjacent"]+=1
                    examples.append({"GWNO":cid,"year":yr,"old":a,
                                     "new":newer[yr],"old_state":prev,
                                     "new_state":following})
    return out,examples


def jeffreys_rates(counts):
    result={}
    for state in (0,1):
        n=counts[state]["n"]
        k=counts[state]["cross_to_adjacent"]
        if type(n) is not int or type(k) is not int or not 0<=k<=n or n<100:
            raise ValueError("Missing adequate frozen categorical denominator")
        result[state]=(k+ALPHA)/(n+2*ALPHA)
    return result


def conditional_h2(records,origin,cohort):
    """Exactly regenerate original four-state H2 matrix, no future years."""
    histories={cid:{yr:intensity_state(d) for yr,d in hist.items()
                    if yr<=origin} for cid,hist in records.items()}
    if len(histories)!=TRAIN_N or len(cohort)!=N or not set(cohort).issubset(histories):
        raise ValueError("Official 199-country transition panel or 196 cohort changed")
    if any(origin not in histories[cid] or origin-1 not in histories[cid]
           for cid in cohort):
        raise ValueError("Incomplete original risk cohort")
    gcount=[[0]*STATES for _ in range(STATES)]
    local={}
    for cid,h in histories.items():
        c=[[0]*STATES for _ in range(STATES)]
        for yr in sorted(h):
            if yr-1 in h:
                a,b=h[yr-1],h[yr]
                c[a][b]+=1
                gcount[a][b]+=1
        local[cid]=c
    if any(sum(row)<10 for row in gcount):
        raise ValueError("Insufficient global transitions")
    g=[[(gcount[s][t]+LAPLACE)/(sum(gcount[s])+STATES*LAPLACE)
        for t in range(STATES)] for s in range(STATES)]
    output={}
    for cid in sorted(cohort):
        c=local[cid]
        q=[[(c[s][t]+SHRINK*g[s][t])/(sum(c[s])+SHRINK)
            for t in range(STATES)] for s in range(STATES)]
        conditional=[sum(q[st][j]*sum(q[j][a] for a in ACTIVE)
                         for j in range(STATES)) for st in range(STATES)]
        state=histories[cid][origin]
        output[cid]={"origin_state":state,"conditional_H2":conditional,
                     "hard_p":round(conditional[state],12)}
    return output


def score_holdout(source_counts,holdout_counts):
    outcome={}
    for st in (0,1):
        n=holdout_counts[st]["n"]
        k=holdout_counts[st]["cross_to_adjacent"]
        p=source_counts[st]
        if n<1 or not 0<p<1:
            raise ValueError("Missing revision holdout or invalid prior")
        # The two probabilities predict the occurrence of an editorial
        # category crossing under the next release, not truth/error.
        logloss=-(k*math.log(p)+(n-k)*math.log1p(-p))/n
        baseline=.5 # predeclared uninformed event baseline, not fitted
        raw_brier=(k*(1-p)**2+(n-k)*p*p)/n
        outcome[str(st)]={
            "revised_n":k,"old_state_exposure_n":n,
            "estimated_training_transition_rate":p,
            "observed_holdout_transition_rate":k/n,
            "mean_holdout_revision_event_brier":raw_brier,
            "mean_holdout_revision_event_logloss":logloss,
            "unskilled_half_probability_event_brier":.25,
        }
    return outcome


def evaluate(sources,cohort,prior_shadow):
    if (prior_shadow.get("schema")!=
        "idealab.psico.geo_h2_fixed10pct_origin_state_uncertainty.v1"
        or prior_shadow.get("original_GEO2027_source_sha256")!=SOURCE_SHA256
        or prior_shadow.get("source_sha256")!=
        {v:SOURCES[v]["sha256"] for v in VERSION_ORDER}
        or prior_shadow.get("lambda_assumed_a_priori_not_fitted")!=.1
        or prior_shadow.get("original_issued_GEO2027_or_GEO2028_modified") is not False
        or len(cohort)!=N or len(set(cohort))!=N):
        raise ValueError("Frozen original and shadow provenance unverified")
    counts={st:{"n":0,"cross_to_adjacent":0} for st in (0,1)}
    training_details={}
    for old,new in TRAIN_PAIRS:
        one,examples=state_revision_counts(sources[old],sources[new])
        training_details[f"{old}->{new}"]={
            "denominator_by_old_state":{str(st):one[st] for st in (0,1)},
            "observed_zero_low_revisions":examples,
        }
        for st in (0,1):
            for key in counts[st]:
                counts[st][key]+=one[st][key]
    weights=jeffreys_rates(counts)
    holdout,examples=state_revision_counts(
        sources[HOLDOUT_PAIR[0]],sources[HOLDOUT_PAIR[1]])
    holdout_result=score_holdout(weights,holdout)
    historical=[]
    for vintage in ("23.1","24.1"):
        for origin in ORIGINS:
            rows=conditional_h2(sources[vintage],origin,cohort)
            original,meta=four_state_forecast(
                sources[vintage],origin,historical_rolling_diagnostic=True)
            if (meta["cutoff_max"]!=origin or meta["eligible_countries"]!=N
                or any(rows[c]["hard_p"]!=original[c]["p_intensity_markov"]
                       for c in cohort)):
                raise AssertionError("Hard original H2 probability mismatch")
            yref=sources["26.1"]
            brier_hard=0.
            brier_empirical=0.
            for cid in cohort:
                target=origin+2
                if target not in yref[cid]:
                    raise ValueError("Target official year missing")
                y=int(yref[cid][target]>=25)
                st=rows[cid]["origin_state"]
                conditional=rows[cid]["conditional_H2"]
                p_hard=rows[cid]["hard_p"]
                p_edit=(round((1-weights[st])*conditional[st]+
                              weights[st]*conditional[1-st],12)
                        if st in (0,1) else p_hard)
                brier_hard+=(p_hard-y)**2
                brier_empirical+=(p_edit-y)**2
            historical.append({
                "origin_release":vintage,"origin_year":origin,
                "target_year":origin+2,
                "mean_brier_hard":brier_hard/N,
                "mean_brier_revision_rate_mixture":brier_empirical/N,
                "delta_brier_mixture_minus_hard":(brier_empirical-brier_hard)/N,
            })
    new=conditional_h2(sources["26.1"],PROSPECTIVE_ORIGIN,cohort)
    # The original historical diagnostic API intentionally rejects origins >2023.
    # Do not weaken that contract just to introduce the distinct 2025 shadow;
    # the identical transition arithmetic is independently replayed at every
    # valid historical origin above, including both source vintages.
    forecasts=[]
    for cid in sorted(cohort):
        row=new[cid]
        st=row["origin_state"]
        p0=row["hard_p"]
        cond=row["conditional_H2"]
        empirical=(round((1-weights[st])*cond[st]+
                         weights[st]*cond[1-st],12)
                   if st in (0,1) else p0)
        forecasts.append({"GWNO":cid,"origin_year":2025,"target_year":2027,
                          "origin_four_state":st,
                          "p_hard_four_state":p0,
                          "p_revision_rate_shadow":empirical,
                          "shadow_minus_hard":empirical-p0})
    byv={}
    for v in ("23.1","24.1"):
        fs=[x for x in historical if x["origin_release"]==v]
        byv[v]={
            "pooled_hard_brier":sum(x["mean_brier_hard"] for x in fs)/len(fs),
            "pooled_empirical_mixture_brier":sum(
                x["mean_brier_revision_rate_mixture"] for x in fs)/len(fs),
            "pooled_delta_brier":sum(
                x["delta_brier_mixture_minus_hard"] for x in fs)/len(fs),
        }
        prev=prior_shadow["historical_pooled"][v]["mean_hard_brier"]
        if not math.isclose(byv[v]["pooled_hard_brier"],prev,
                            rel_tol=0,abs_tol=EPS):
            raise AssertionError("Previous hard model Brier changed")
    return {
        "schema":"idealab.psico.geo_h2_empirical_editorial_revision_rate_shadow.v1",
        "status":"PROSPECTIVE_UNSCORED_SHADOW_AND_RETROSPECTIVE_CAVEATED_DIAGNOSTIC",
        "input_source_SHA256":{v:SOURCES[v]["sha256"] for v in VERSION_ORDER},
        "original_GEO2027_issue_SHA256":SOURCE_SHA256,
        "editorial_transition_training_pairs":[list(x) for x in TRAIN_PAIRS],
        "held_out_editorial_transition_pair":list(HOLDOUT_PAIR),
        "editorial_calibration_training_max_country_year":CUTOFF,
        "beta_smoothing_prior":"Jeffreys Beta(0.5, 0.5), fixed before holdout",
        "pooled_training_exposure_counts":{str(s):counts[s] for s in (0,1)},
        "observed_editorial_revision_probabilities":{
            str(s):weights[s] for s in (0,1)},
        "training_pair_details":training_details,
        "holdout_editorial_transition_examples":examples,
        "holdout_revision_event_assessment":holdout_result,
        "historical_11_origin_by_source":historical,
        "historical_pooled_brier":byv,
        "prospective_unscored_2027_shadow":{
            "origin_year":2025,"target_year":2027,
            "source":"26.1","country_n":N,
            "issued_result_labels_2027_available":False,
            "prospective_skill_established":False,
            "probabilities":forecasts,
        },
        "original_GEO2027_or_GEO2028_issued_vectors_modified":False,
        "not_estimated_latent_state_truth_probabilities":True,
        "historical_editions_postdate_some_pseudoorigins":True,
        "limitations":"Editorial cross-vintage revision rate is NOT probability recorded state is incorrect or probability of true latent state. Source training country-years recur across overlapping edition transitions (not IID), and same two empirical rates are applied to all countries and years. Retrospective Brier uses later editions than simulated origins; 2027 shadow is distinct and unscored.",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    ap.add_argument("--print-report",action="store_true")
    args=ap.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Frozen original issued GEO2027 vector has changed")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    raw={v:request(SOURCES[v]["url"],MAX_DOWNLOAD) for v in VERSION_ORDER}
    sources={v:parse_counts(raw[v],v) for v in VERSION_ORDER}
    if any(sum(map(len,sources[v].values()))!=EXPECTED_ROWS[v]
           for v in VERSION_ORDER):
        raise ValueError("Official source count differs from expected SHA row set")
    cohort=[c["country_id"] for c in json.loads(ISSUE.read_text())["countries"]]
    report=evaluate(sources,cohort,json.loads(ANCHOR.read_text(encoding="utf-8")))
    payload=json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n"
    if args.check_report and json.loads(OUTPUT.read_text(encoding="utf-8"))!=report:
        raise ValueError("Stored editorial revision shadow does not reproduce")
    if args.print_report:
        print("GEO_EMPIRICAL_REVISION_BEGIN",flush=True)
        print(payload,end="")
        print("GEO_EMPIRICAL_REVISION_END",flush=True)
    else:
        print(json.dumps({"rates":report["observed_editorial_revision_probabilities"],
                          "holdout":report["holdout_revision_event_assessment"],
                          "historical":report["historical_pooled_brier"]},sort_keys=True))


if __name__=="__main__":
    main()
