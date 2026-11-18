#!/usr/bin/env python3
"""Independent institutional *contextual* corroboration for UCDP H2.

Official World Bank WGI Political Stability (GOV_WGI_PV_EST) is an
expert/survey-based perception composite, NOT independently annotated
organized-violence fatalities and NOT latent truth. The two sources have
different estimands and potentially overlapping secondary inputs.

SHA-verify official UCDP 26.1, use frozen 196 GWNO and an auditable
country-name/ISO3 crosswalk. Measure same-year rank concordance for
2012..2025; show lag-two-year contrast separately (NOT prospective).
Compare 2025 WGI rank to the distinct, original-model four-state 2027
shadow without scoring 2027. No 2027/2028 issue modifications.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit as audit_issued,
)
from backtest_archived_country_vintages import SOURCES
from experiment_geo2027_intensity_markov_cross_release import (
    MAX_DOWNLOAD, EXPECTED_ROWS, parse_counts,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256
from probe_ucdp_organized_vintages import request

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"data/geo-h2-wgi-political-stability-contextual-concordance.json"
COUNTRY_NAMES=ROOT/"data/forecast-2027-global-only-matched-shadow.json"
PRIOR_SHADOW=ROOT/"data/geo-h2-fourstate-observation-kernel-latent-bounds-2027.json"
WGI_INDICATOR="GOV_WGI_PV_EST"
WGI_URL=("https://api.worldbank.org/v2/country/all/indicator/"
         f"{WGI_INDICATOR}?format=json&per_page=20000&date=2012%3A2025")
YEARS=tuple(range(2012,2026))
N=196
MIN_MATCHED_PER_YEAR=155
MIN_SPEARMAN_N=30
# Explicit country-name disambiguation for institutional name conventions.
# A named country can only be joined if the World Bank returns that ISO3
# with a real observation; never infer a missing indicator as zero.
GWNO_TO_ISO3={
    2:"USA",31:"BHS",58:"ATG",316:"CZE",343:"MKD",
    345:"SRB",346:"BIH",347:"XKX",365:"RUS",402:"CPV",
    403:"STP",420:"GMB",437:"CIV",484:"COG",490:"COD",
    510:"TZA",552:"ZWE",572:"SWZ",580:"MDG",630:"IRN",
    640:"TUR",651:"EGY",652:"SYR",678:"YEM",731:"PRK",
    732:"KOR",775:"MMR",811:"KHM",812:"LAO",816:"VNM",
    860:"TLS",987:"FSM",990:"WSM",
}
# Deliberate exclusions: no comparable World Bank record or territories
# whose 196-country GEO definition is not safely aligned.
EXCLUDE_GWNO={327,713}


def normalize_name(name):
    if not isinstance(name,str) or not name.strip():
        raise ValueError("Empty or non-string country name")
    s=unicodedata.normalize("NFKD",name).encode("ascii","ignore").decode().lower()
    s=s.replace("&"," and ")
    return re.sub(r"[^a-z0-9]+"," ",s).strip()


def fetch_wgi():
    req=Request(WGI_URL,headers={"User-Agent":"IDEA-LAB-PSICOHISTORIA-WGI/1.0"})
    with urlopen(req,timeout=60) as response:
        raw=response.read(9_000_001)
    if len(raw)>9_000_000:
        raise ValueError("WGI API payload exceeds declared limit")
    try:
        payload=json.loads(raw)
    except ValueError as exc:
        raise ValueError("World Bank API did not return JSON") from exc
    if (not isinstance(payload,list) or len(payload)!=2
        or not isinstance(payload[0],dict)
        or not isinstance(payload[1],list)
        or payload[0].get("pages")!=1):
        raise ValueError("Incomplete or paginated World Bank WGI API result")
    data=payload[1]
    if len(data)<2000:
        raise ValueError("Missing WGI global time-series rows")
    observations={}
    names={}
    for row in data:
        if row.get("indicator",{}).get("id")!=WGI_INDICATOR:
            raise ValueError("Wrong WGI variable returned by World Bank")
        iso=row.get("countryiso3code","")
        year=row.get("date","")
        value=row.get("value")
        if (not isinstance(iso,str) or not re.fullmatch(r"[A-Z]{3}",iso)
            or not isinstance(year,str) or not re.fullmatch(r"20[0-9]{2}",year)):
            continue
        y=int(year)
        if y not in YEARS or value is None:
            continue
        if type(value) not in (int,float) or not math.isfinite(value) or not -5<value<5:
            raise ValueError("Invalid WGI estimate")
        key=(iso,y)
        if key in observations:
            raise ValueError("Duplicate WGI country-year record")
        observations[key]=float(value)
        names.setdefault(iso,row["country"]["value"])
        if names[iso]!=row["country"]["value"]:
            raise ValueError("Inconsistent country label across years")
    if len(observations)<2000:
        raise ValueError("Insufficient non-missing official WGI indicator values")
    return observations,names


def country_crosswalk(frozen,iso_names):
    """Exact-name automatic joins + explicit ISO3 aliases; never fuzzy join."""
    byname=defaultdict(list)
    for iso,label in iso_names.items():
        byname[normalize_name(label)].append(iso)
    matched={}
    skipped=[]
    manual=[]
    for row in frozen:
        cid,name=row["country_id"],row["country"]
        if cid in EXCLUDE_GWNO:
            skipped.append({"GWNO":cid,"name":name,"reason":"explicit_exclusion"})
            continue
        if cid in GWNO_TO_ISO3:
            iso=GWNO_TO_ISO3[cid]
            manual.append(cid)
            if iso not in iso_names:
                skipped.append({"GWNO":cid,"name":name,
                                "iso3_proposed":iso,"reason":"manual_iso3_not_in_wgi"})
                continue
        else:
            opts=byname.get(normalize_name(name),[])
            if len(opts)!=1:
                skipped.append({"GWNO":cid,"name":name,"reason":
                                "no_exact_unique_world_bank_name",
                                "candidate_iso3":opts})
                continue
            iso=opts[0]
        if iso in matched.values():
            raise ValueError("Two GWNO countries map to same World Bank ISO3")
        matched[cid]=iso
    if len(frozen)!=N or len(matched)<MIN_MATCHED_PER_YEAR:
        raise ValueError(f"Crosswalk incomplete: only {len(matched)} matched out of {len(frozen)}")
    return matched,skipped,manual


def concordance_auc(rows):
    """Rank concordance P(lower WGI | active >=25 vs inactive), tie-half."""
    active=[float(x["wgi_pv_est"]) for x in rows if x["ucdp_active_25_plus"]]
    inactive=[float(x["wgi_pv_est"]) for x in rows if not x["ucdp_active_25_plus"]]
    if not active or not inactive:
        raise ValueError("Requires active and inactive countries")
    wins=sum(int(a<b)+.5*(a==b) for a in active for b in inactive)
    return wins/(len(active)*len(inactive))


def ranks(v):
    n=len(v)
    order=sorted(range(n),key=lambda i:(v[i],i))
    out=[None]*n
    k=0
    while k<n:
        j=k+1
        while j<n and v[order[j]]==v[order[k]]:
            j+=1
        rank=(k+1+j)/2
        for p in range(k,j):
            out[order[p]]=rank
        k=j
    return out


def spearman(a,b):
    if len(a)!=len(b) or len(a)<MIN_SPEARMAN_N:
        raise ValueError("Insufficient comparable country ranking")
    ra,rb=ranks(a),ranks(b)
    ma=sum(ra)/len(ra)
    mb=sum(rb)/len(rb)
    aa=sum((x-ma)**2 for x in ra)
    bb=sum((y-mb)**2 for y in rb)
    if aa==0 or bb==0:
        raise ValueError("Constant-rank data")
    return sum((x-ma)*(y-mb) for x,y in zip(ra,rb))/math.sqrt(aa*bb)


def analyze(ucdp,raw_names,observations,wb_names,shadow,source_sha):
    country_rows=raw_names["countries"]
    issue_ids={x["country_id"] for x in json.loads(ISSUE.read_text())["countries"]}
    if (raw_names.get("n_countries")!=N or len(country_rows)!=N
        or {r["country_id"] for r in country_rows}!=issue_ids
        or len(ucdp)!=199
        or shadow.get("schema")!="idealab.psico.geo_h2_fourstate_editorial_kernel_latent_partial_id.v1"
        or shadow.get("prospective_GEO2027_or_GEO2028_original_issues_modified") is not False
        or shadow.get("original_issued_GEO2027_SHA256")!=SOURCE_SHA256
        or shadow.get("prospective_unscored_2027_shadow",{}).get("countries_n")!=N):
        raise ValueError("Original GEO2027 risk set or shadow anchor changed")
    xwalk,skipped,manual=country_crosswalk(country_rows,wb_names)
    shadow_probs={r["GWNO"]:r["hard_four_state_p"] for r in
                  shadow["prospective_unscored_2027_shadow"]["predictions"]}
    if set(shadow_probs)!=issue_ids:
        raise ValueError("2027 first-issue shadow countries do not match")
    data=[]
    annual=[]
    for year in YEARS:
        now=[]
        for cid in sorted(xwalk):
            value=observations.get((xwalk[cid],year))
            deaths=ucdp.get(cid,{}).get(year)
            if value is None or deaths is None:
                continue
            row={"GWNO":cid,"iso3":xwalk[cid],"year":year,
                 "wgi_pv_est":value,"ucdp_best_deaths":deaths,
                 "ucdp_active_25_plus":int(deaths>=25)}
            now.append(row)
        if len(now)<MIN_MATCHED_PER_YEAR:
            raise ValueError(f"Insufficient country-year overlap in {year}: {len(now)}")
        active=sum(r["ucdp_active_25_plus"] for r in now)
        if active<5 or len(now)-active<5:
            raise ValueError("No meaningful active/inactive comparison")
        auc=concordance_auc(now)
        annual.append({
            "year":year,"matched_country_year_n":len(now),
            "active_25_plus_n":active,
            "inactive_less_25_n":len(now)-active,
            "contemporaneous_wgi_lower_when_ucdp_active_pairwise_auc":auc,
            "mean_wgi_active":sum(r["wgi_pv_est"] for r in now if r["ucdp_active_25_plus"])/active,
            "mean_wgi_inactive":sum(r["wgi_pv_est"] for r in now if not r["ucdp_active_25_plus"])/(len(now)-active),
        })
        data.extend(now)
    by_year={(r["GWNO"],r["year"]):r for r in data}
    # Lagged contextual comparison: indicator from year t to a conflict
    # label in t+2. Retrospective only: source vintage was released 2026.
    lagged=[]
    for origin in range(2012,2024):
        matched=[]
        for cid in sorted(xwalk):
            a=by_year.get((cid,origin))
            b=by_year.get((cid,origin+2))
            if a is not None and b is not None:
                matched.append({
                    "wgi_pv_est":a["wgi_pv_est"],
                    "ucdp_active_25_plus":b["ucdp_active_25_plus"]})
        if len(matched)<MIN_MATCHED_PER_YEAR:
            raise ValueError("Historical lag-two contextual overlap missing")
        lagged.append({
            "origin_year":origin,"target_year":origin+2,"matched_n":len(matched),
            "active_target_n":sum(r["ucdp_active_25_plus"] for r in matched),
            "rank_concordance_auc_wgi_origin_vs_ucdp_t_plus_2":
                concordance_auc(matched),
        })
    latest=[r for r in data if r["year"]==2025]
    if len(latest)<MIN_MATCHED_PER_YEAR:
        raise ValueError("2025 WGI contextual coverage too low")
    rank2027=spearman(
        [-r["wgi_pv_est"] for r in latest],
        [shadow_probs[r["GWNO"]] for r in latest])
    canonical_wgi=[{"iso3":iso,"year":year,"value":value}
                   for (iso,year),value in sorted(observations.items())]
    canonical_digest=hashlib.sha256(json.dumps(
        canonical_wgi,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {
        "schema":"idealab.psico.geo_h2_wgi_external_perception_context_v1",
        "status":"INSTITUTIONALLY_SEPARATE_CONTEXT_NOT_INDEPENDENT_FATALITY_TRUTH",
        "world_bank_indicator":WGI_INDICATOR,
        "world_bank_api_url":WGI_URL,
        "world_bank_2026_current_vintage_historical_data_can_be_revised":True,
        "world_bank_canonical_2012_2025_observations_sha256":canonical_digest,
        "world_bank_nonmissing_country_year_observations_n":len(canonical_wgi),
        "world_bank_country_iso3_n":len(wb_names),
        "official_ucdp_26_1_source_sha256":source_sha,
        "original_GEO2027_issued_sha256":SOURCE_SHA256,
        "source_definitions_not_equivalent":True,
        "crosswalk_method":"Audited GWNO to ISO3 name exactness with explicit disambiguation; never fuzzy or impute absent observations",
        "matched_GWNO_iso3":[{"GWNO":cid,"iso3":iso} for cid,iso in sorted(xwalk.items())],
        "manual_GWNO_iso3_ids":sorted(manual),
        "country_join_unmatched_or_excluded":skipped,
        "matched_country_n":len(xwalk),
        "annual_same_year_source_concordance":annual,
        "lag2_contextual_rank_concordance_not_prospective":lagged,
        "matched_country_year_data":data,
        "2025_world_bank_perception_vs_preissued_2027_fourstate_shadow":{
            "matched_countries_n":len(latest),
            "spearman_higher_2027_h2_risk_vs_lower_2025_wgi_perception":rank2027,
            "expected_direction_positive_not_tested_for_skill":True,
            "actual_2027_outcome_not_observed":True,
        },
        "joint_data_proves_ucdp_true_latent_state":False,
        "wgi_valid_as_independent_fatality_ground_truth":False,
        "external_overlap_of_underlying_wgi_secondary_inputs_fully_excluded":False,
        "original_GEO2027_or_GEO2028_issue_modified":False,
        "limitations":"WGI Political Stability is a composite of citizen/expert perceptions of instability, not an independent census of fatal organized-violence events. Some WGI inputs may overlap indirectly with conflict data. Association/concordance (same-year or lagged) does not verify UCDP fatality accuracy or imply prospective H2 forecast skill. The official WGI 2026 update backfills historical values, so lagged years are not true historical as-of evaluations.",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    ap.add_argument("--print-report",action="store_true")
    args=ap.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Original 2027 issued forecast source SHA changed")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    raw=request(SOURCES["26.1"]["url"],MAX_DOWNLOAD)
    ucdp=parse_counts(raw,"26.1")
    if sum(map(len,ucdp.values()))!=EXPECTED_ROWS["26.1"]:
        raise ValueError("Official UCDP country-year count or SHA changed")
    wb,wb_names=fetch_wgi()
    report=analyze(ucdp,json.loads(COUNTRY_NAMES.read_text(encoding="utf-8")),
                   wb,wb_names,json.loads(PRIOR_SHADOW.read_text(encoding="utf-8")),
                   SOURCES["26.1"]["sha256"])
    payload=json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    if args.check_report and json.loads(REPORT.read_text(encoding="utf-8"))!=report:
        raise ValueError("Published WGI context report does not match newly observed official data; review upstream vintage")
    if args.print_report:
        print("GEO_WGI_EXTERNAL_CONTEXT_BEGIN",flush=True)
        print(payload,end="")
        print("GEO_WGI_EXTERNAL_CONTEXT_END",flush=True)
    else:
        print(json.dumps({
            "matched":report["matched_country_n"],
            "annual":len(report["annual_same_year_source_concordance"]),
            "spearman_2025_wgi_vs_2027_shadow":
                report["2025_world_bank_perception_vs_preissued_2027_fourstate_shadow"]["spearman_higher_2027_h2_risk_vs_lower_2025_wgi_perception"],
        },sort_keys=True))


if __name__=="__main__":
    main()
