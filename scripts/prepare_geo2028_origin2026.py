#!/usr/bin/env python3
"""PRE-REGISTERED, UNISSUED GEO2028 origin-2026 horizon-2 candidate.

This module cannot be a new country origin today: UCDP annual 27.1 containing
2026 is not yet available (protocol written 2026-11-15). It NEVER downloads
monthly UCDP Candidate events as proxy for the completed annual dataset and
NEVER writes forecast probabilities into the institutional repository.

An eventual full 27.1 ZIP, its actual SHA-256 and official first-release
publication evidence must be source-frozen in a separate public commit BEFORE
any probability issue. This script generates an *unissued candidate only*.

Same primary Markov country model as first-issued GEO2027, rolled forward
one origin year to 2026, target 2028, H=2. Shares 2028 target with first-issued
GEO2028 origin-2025 H=3; comparison is NOT independent statistical replication.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
import hashlib
import io
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

import forecast_2027_statebased as old_model
from build_official_countries import MAX_ZIP, read_zip
from evaluate_geo2028_first_complete_official import load_immutable_issue

ROOT=Path(__file__).resolve().parents[1]
ID="PSICO-GEO2028-ORIGIN2026-H2-UCDP271-PREREG-V1"
SCHEMA="idealab.psico.geo2028_origin2026_h2_unissued_candidate.v1"
PIN_SCHEMA="idealab.psico.future_ucdp_2026_origin_source_pin.v1"
URL="https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-271-csv.zip"
VERSION="27.1"
ORIGIN=2026
TARGET=2028
HORIZON=2
RECENT=(2022,2023,2024,2025,2026)
MIN_COHORT=190
MAX_COHORT=210
FIRST_POSSIBLE_RELEASE=date(2027,1,1)
FIRST_PUBLIC_PRIOR_YEAR=2025
PREVIOUS_FORECAST_SHA="fd5832c6896548b053202f2f84bd0f7cd4a75df44462fbd4f259b9d8d4c39bde"
PRIMARY="p_model"
BASELINE="p_baseline_global_5y"
SECONDARY="p_global_markov"


def canonical(document):
    return (json.dumps(document,sort_keys=True,ensure_ascii=False,
                       separators=(",",":"))+"\n").encode("utf8")


def _positive_int(value,field):
    if type(value) is not str or not re.fullmatch(r"\d+",value.strip()):
        raise ValueError("Missing/invalid numeric UCDP field: "+field)
    return int(value.strip())


def parse_annual_2026_csv(csv_text):
    """Strict country-year parse: 1989..2026 only; no future or inferred zeros.

    Does not reuse the legacy 26.1 parser because it FIXES last year=2025
    and EXPECTED_ROWS=7132. A new 27.1 release has its own source checksum.
    """
    if isinstance(csv_text,bytes):
        csv_text=csv_text.decode("utf-8-sig")
    if type(csv_text) is not str or not 100000<=len(csv_text)<=12000000:
        raise ValueError("Future official annual UCDP CSV missing or implausibly small")
    reader=csv.DictReader(io.StringIO(csv_text,newline=""))
    headers=reader.fieldnames or []
    if len(headers)!=len(set(headers)):
        raise ValueError("Duplicate official annual source CSV headers")
    if not {"country_id","country","year"}.issubset(headers):
        raise ValueError("Missing official annual GWNO/country/year fields")
    available=[x for x in ("sb_total_deaths_best","sb_total_deaths_best_cy")
               if x in headers]
    if len(available)!=1:
        raise ValueError("Missing or ambiguous state-based best mortality field")
    best=available[0]
    records={}
    names={}
    nrows=0
    for row in reader:
        if None in row or row.get(None) is not None:
            raise ValueError("Malformed UCDP annual source row")
        cid=_positive_int(row["country_id"],"country_id")
        year=_positive_int(row["year"],"year")
        deaths=_positive_int(row[best],best)
        name=(row["country"] or "").strip()
        if (not 1<=cid<=2000 or not 1989<=year<=ORIGIN or
            not 0<=deaths<=10000000 or not 1<=len(name)<=120):
            raise ValueError("Post-origin/invalid country-year or deaths in future ZIP")
        history=records.setdefault(cid,{})
        if year in history:
            raise ValueError("Duplicate source country-year")
        if cid in names and names[cid]!=name:
            raise ValueError("Source country name changed within one official edition")
        names[cid]=name
        history[year]=int(deaths>=25)
        nrows+=1
    if nrows<6900 or not 190<=len(records)<=230 or (
        max(max(h) for h in records.values())!=ORIGIN):
        raise ValueError("Annual UCDP 27.1 source global coverage incomplete")
    eligible=[cid for cid,h in records.items() if ORIGIN in h and ORIGIN-1 in h]
    if not MIN_COHORT<=len(eligible)<=MAX_COHORT:
        raise ValueError("No complete and plausible 2025/26 two-year GWNO cohort")
    return records,names,{"source_country_year_rows":nrows,
                          "source_country_ids":len(records),
                          "eligible_2025_2026_country_count":len(eligible),
                          "max_source_year":ORIGIN}


def pin_source_metadata(pin,raw,*,as_of=None):
    """Provenance claims are NOT a third-party publication attestation."""
    if type(pin) is not dict or type(raw) is not bytes:
        raise ValueError("Future source pin must be a JSON object and raw ZIP bytes")
    actual=hashlib.sha256(raw).hexdigest()
    url=pin.get("official_url")
    parts=urlsplit(url) if type(url) is str else urlsplit("")
    sha=pin.get("official_zip_sha256")
    if (pin.get("schema")!=PIN_SCHEMA or
        pin.get("dataset")!="UCDP OrganizedViolenceCY" or
        pin.get("version")!=VERSION or
        pin.get("last_observed_year")!=ORIGIN or
        pin.get("first_release_independently_attested") is not False or
        pin.get("pin_status")!="SOURCE_CANDIDATE_UNCERTIFIED" or
        parts.scheme!="https" or parts.netloc!="ucdp.uu.se" or
        parts.username is not None or parts.password is not None or
        parts.query or parts.fragment or parts.path!=urlsplit(URL).path or
        type(sha) is not str or not re.fullmatch(r"[0-9a-f]{64}",sha) or
        sha!=actual or not 100000<len(raw)<=MAX_ZIP):
        raise ValueError("No exact original UCDP 27.1 2026 source ZIP pin")
    when=pin.get("publication_date_claimed")
    if type(when) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",when):
        raise ValueError("Unverifiable annual publication date")
    try:
        released=date.fromisoformat(when)
    except ValueError:
        raise ValueError("Unverifiable annual publication date") from None
    today=as_of if as_of is not None else date.today()
    if type(today) is not date or (
        released<FIRST_POSSIBLE_RELEASE or released>today or today>=date(2028,1,1)):
        raise ValueError("2026 origin cannot be issued before complete 2026 or after target starts")
    return {
        "source_version":VERSION,
        "source_url":URL,
        "official_zip_sha256":sha,
        "publication_date_operator_claimed":when,
        "first_release_independently_verified":False,
        "first_complete_annual_2026_source_verified_externally":False,
        "source_pin_registered_by_institution":True,
        "operator_claim_is_not_independent_publication_proof":True,
    }


def estimate_from_origin(records,names,*,origin=ORIGIN):
    """Freeze 2027 issued model family; only origin-year shift is allowed.

    For synthetic regression tests origin=2025 MUST reproduce exactly the
    already issued GEO2027 model. For real future issuance origin MUST 2026.
    """
    if type(origin) is not int or origin not in (2025,2026) or (
        not records or not names or set(records)!=set(names)):
        raise ValueError("Illegal origin or country universe")
    for cid,h in records.items():
        if (type(cid) is not int or not 1<=cid<=2000 or
            not h or any(type(y) is not int or y>origin or y<1989 or
                         type(z) is not int or z not in (0,1)
                         for y,z in h.items())):
            raise ValueError("Post-origin, invalid or empty country histories")
    cohort=sorted(cid for cid,h in records.items()
                  if origin in h and origin-1 in h)
    if not MIN_COHORT<=len(cohort)<=MAX_COHORT:
        raise ValueError("Unstable annual 2026 risk population")
    transitions=[[0,0],[0,0]]
    local={}
    for cid,h in records.items():
        per=[[0,0],[0,0]]
        for year in sorted(h):
            if year>1989 and year-1 in h:
                s,t=h[year-1],h[year]
                per[s][t]+=1
                transitions[s][t]+=1
        local[cid]=per
    if min(sum(t) for t in transitions)<100:
        raise ValueError("Insufficient original-origined Markov transitions")
    lap=old_model.LAPLACE
    alpha=old_model.TRANSITION_PRIOR
    if alpha!=20 or lap!=1:
        raise ValueError("Original 2027 transition estimator has changed")
    global_q=[(transitions[s][1]+lap)/(sum(transitions[s])+2*lap)
              for s in (0,1)]
    recent=tuple(range(origin-4,origin+1))
    exposures=[records[cid][year] for cid in cohort for year in recent
               if year in records[cid]]
    if len(exposures)<.95*len(cohort)*5:
        raise ValueError("Original five-year reference lacks >=95% coverage")
    global_recent=(sum(exposures)+lap)/(len(exposures)+2*lap)
    def two_steps(initial,q):
        p=q[initial]
        return (1-p)*q[0]+p*q[1]
    issued=[]
    for cid in cohort:
        last=records[cid][origin]
        per=local[cid]
        q=[(per[s][1]+alpha*global_q[s])/(sum(per[s])+alpha)
           for s in (0,1)]
        vals=[two_steps(last,q),two_steps(last,global_q),global_recent]
        if not all(math.isfinite(p) and 0<p<1 for p in vals):
            raise ValueError("Invalid 2026 origin probability")
        issued.append({
            "country_id":cid,
            "country":names[cid],
            "last_observed_state_2026" if origin==2026 else
                "last_observed_state_2025":last,
            "p_model":round(vals[0],12),
            "p_global_markov":round(vals[1],12),
            "p_baseline_global_5y":round(vals[2],12),
        })
    return issued,{
        "origin_year":origin,
        "cohort_n":len(cohort),
        "global_transition_counts":transitions,
        "global_transition_p_active":[round(q,12) for q in global_q],
        "global_5y_exposures":len(exposures),
        "global_5y_positive":sum(exposures),
        "baseline_global_5y":round(global_recent,12),
        "recent_years":list(recent),
    }


def build_candidate(raw,pin,original_2025_issue,*,as_of=None):
    """Future source already pin-checked; output is NOT a public forecast issue."""
    source=pin_source_metadata(pin,raw,as_of=as_of)
    if (original_2025_issue.get("forecast_id")!=
        "PSICO-GEO2028-STATEBASED25-H3-ORIGIN2025-V1" or
        original_2025_issue.get("origin",{}).get("year")!=2025 or
        original_2025_issue.get("target",{}).get("year")!=2028 or
        original_2025_issue.get("protocol",{}).get("horizon_years")!=3 or
        len(original_2025_issue.get("countries",[]))!=196 or
        original_2025_issue.get("2028_outcomes_resolved")!=0):
        raise ValueError("Original GEO2028 origin-2025 issuance not authenticated")
    histories,names,facts=parse_annual_2026_csv(read_zip(raw))
    rows,fit=estimate_from_origin(histories,names,origin=2026)
    previous={r["country_id"]:r for r in original_2025_issue["countries"]}
    ids=set(r["country_id"] for r in rows)
    common=sorted(ids & previous.keys())
    additions=sorted(ids - previous.keys())
    absent=sorted(previous.keys() - ids)
    revisions=sorted(cid for cid in common
                     if histories[cid][2025]!=previous[cid][
                         "last_observed_state_2025"])
    # Actual 2028 outcome is NEVER present; same target and near origins
    # make these forecasts paired but NOT statistically independent.
    return {
        "schema":SCHEMA,
        "forecast_id":ID,
        "status":"UNISSUED_CANDIDATE_DO_NOT_CLAIM_PUBLIC_FORECAST",
        "origin_year":2026,
        "target_year":2028,
        "horizon_years":2,
        "target_definition":"UCDP OrganizedViolenceCY state-based best annual deaths >=25 for GWNO country in 2028",
        "model_primary":"country_markov_2step_laplace_global_shrink20",
        "primary_reference":"global_laplace_5y_2022_2026",
        "secondary_comparator":"global_markov_2step_laplace",
        "first_complete_2028_official_outcome_required":True,
        "paired_brier_model_minus_global5y_preregistered":True,
        "frozen_origin_2025_GEO2028_first_issue_sha256":PREVIOUS_FORECAST_SHA,
        "shares_2028_target_with_original_GEO2028_horizon3":True,
        "statistically_independent_of_origin2025_GEO2028":False,
        "model_selection_or_skill_from_2028_outcomes":False,
        "no_data_after_origin_2026":True,
        "no_2028_outcomes_observed":True,
        "no_first_public_forecast_commit_yet":True,
        "independently_attested_source_release":False,
        "generator_does_not_certify_or_issue_itself":True,
        "source_provenance":source,
        "source_facts":facts,
        "model_fit":fit,
        "n_issued_country_questions":0,
        "n_candidate_country_probabilities":len(rows),
        "country_universe_comparison_to_original_2025_origin":{
            "original_2025_origin_n":196,
            "candidate_2026_origin_n":len(rows),
            "common_gwno":len(common),
            "new_in_2026_origin":additions,
            "not_in_2026_origin":absent,
            "revised_2025_annual_state_gwno_in_27_1":revisions,
            "revised_2025_annual_state_n":len(revisions),
            "differences_include_new_2026_data_and_historical_vintage_revisions":True,
        },
        "expected_2028_active_country_counts":{
            key:round(sum(r[key] for r in rows),12)
            for key in ("p_model","p_global_markov","p_baseline_global_5y")},
        "countries":rows,
    }


def validate_candidate(doc):
    if (doc.get("schema")!=SCHEMA or doc.get("forecast_id")!=ID or
        doc.get("status")!="UNISSUED_CANDIDATE_DO_NOT_CLAIM_PUBLIC_FORECAST" or
        doc.get("origin_year")!=2026 or doc.get("target_year")!=2028 or
        doc.get("horizon_years")!=2 or
        doc.get("model_primary")!="country_markov_2step_laplace_global_shrink20" or
        doc.get("primary_reference")!="global_laplace_5y_2022_2026" or
        doc.get("source_provenance",{}).get("source_version")!=VERSION or
        doc.get("source_facts",{}).get("max_source_year")!=2026 or
        doc.get("no_data_after_origin_2026") is not True or
        doc.get("no_2028_outcomes_observed") is not True or
        doc.get("no_first_public_forecast_commit_yet") is not True or
        doc.get("n_issued_country_questions")!=0 or
        doc.get("generator_does_not_certify_or_issue_itself") is not True or
        doc.get("independently_attested_source_release") is not False or
        doc.get("statistically_independent_of_origin2025_GEO2028") is not False or
        doc.get("frozen_origin_2025_GEO2028_first_issue_sha256")!=PREVIOUS_FORECAST_SHA):
        raise ValueError("Unsafe chronology, source or false issued/validated status")
    rows=doc.get("countries")
    if type(rows) is not list or not MIN_COHORT<=len(rows)<=MAX_COHORT or (
        doc.get("n_candidate_country_probabilities")!=len(rows)):
        raise ValueError("Incomplete dynamic 2026 GWNO cohort")
    ids=[r.get("country_id") for r in rows]
    if any(type(i) is not int for i in ids) or ids!=sorted(set(ids)):
        raise ValueError("Duplicate/unsorted 2026 GWNO countries")
    for row in rows:
        if (type(row.get("last_observed_state_2026")) is not int or
            row["last_observed_state_2026"] not in (0,1) or
            type(row.get("country")) is not str or
            any(type(row.get(k)) not in (int,float) or not
                math.isfinite(row[k]) or not 0<row[k]<1
                for k in (PRIMARY,BASELINE,SECONDARY))):
            raise ValueError("Invalid original 2026 origin candidate probability")
    for key,value in doc.get("expected_2028_active_country_counts",{}).items():
        if key not in (PRIMARY,BASELINE,SECONDARY) or abs(
            sum(r[key] for r in rows)-value)>1e-10:
            raise ValueError("Candidate expected count disagrees with rows")
    if (set(doc.get("expected_2028_active_country_counts",{}))!=
        {PRIMARY,BASELINE,SECONDARY}):
        raise ValueError("Missing comparator in future candidate")
    return True


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--official-zip",required=True,
                   help="Only future full original UCDP 27.1 annual ZIP, no candidate events")
    p.add_argument("--source-pin-json",required=True,
                   help="First publicly archived exact official 27.1 source SHA and release metadata")
    p.add_argument("--output",required=True,
                   help="Candidate output outside the institutional repository only")
    args=p.parse_args()
    output=Path(args.output).resolve()
    if output==ROOT or ROOT in output.parents:
        raise ValueError("Unissued candidate probabilities cannot be saved inside repo")
    # Reject an impossible 2026 origin before reading any future data.
    if date.today()<FIRST_POSSIBLE_RELEASE or date.today()>=date(2028,1,1):
        raise ValueError("2026 annual UCDP cannot be complete before 2027; origin issuance closed after 2027")
    original,_=load_immutable_issue()
    pin=json.loads(Path(args.source_pin_json).read_text(encoding="utf8"))
    raw=Path(args.official_zip).read_bytes()
    candidate=build_candidate(raw,pin,original)
    validate_candidate(candidate)
    output.write_bytes(canonical(candidate))
    print("GEO2028_ORIGIN2026_CANDIDATE_ONLY",json.dumps({
        "country_probability_candidates":candidate["n_candidate_country_probabilities"],
        "first_public_2026_origin_issues":0,
        "original_2025_issue_untouched":True,
        "original_2025_vs_2026_origin_independent_trials":False,
        "2028_outcomes_observed":0,
        "source_certified_independently":False,
        "sha256":hashlib.sha256(canonical(candidate)).hexdigest(),
    },sort_keys=True))


if __name__=="__main__":
    main()
