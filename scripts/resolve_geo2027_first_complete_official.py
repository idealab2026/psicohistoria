#!/usr/bin/env python3
"""Fail-closed first-complete-official UCDP 2027 outcome resolution gateway.

In 2026, default run is READINESS ONLY and cannot score hypothetical labels.
Actual future assessment requires (a) a local official country-year CSV/ZIP,
(b) independent human/operator provenance review manifest, (c) explicit
196/196 official 2027 rows and SHA, (d) release date passed 2027, and
(e) immutable verification of the original forecast, two shadows and alerts.

IMPORTANT: No code can establish first-official-complete release priority from
a self-supplied manifest; published scores MUST preserve that qualification.
All historical backtests are ex-post; future official Brier is not yet known.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
from urllib.parse import urlparse
from zipfile import ZipFile, BadZipFile

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    FROZEN_SHA256, FIRST_COMMIT, audit as audit_issued,
    prospective_full196_score,
)
from audit_geo2027_log1p_shadow_issue import FROZEN_ISSUE_SHA256
from audit_geo2027_log1p_issued_death_stress import ALERT_SHA
from prepare_geo2027_transition_alerts import SOURCE_SHA256

ROOT=Path(__file__).resolve().parents[1]
PRECOMMIT_REPORT=ROOT/"data/geo2027-global-only-issued-disagreement.json"
META_SCHEMA="idealab.psico.geo2027_first_complete_ucdp_release_review.v1"
READINESS_SCHEMA="idealab.psico.geo2027_full196_official_resolution_readiness.v1"
SCORING_SCHEMA="idealab.psico.geo2027_full196_operator_attested_future_scoring.v1"
TARGET_YEAR=2027
FIRST_POSSIBLE_RELEASE_DATE=date(2028,1,1)
N_COUNTRIES=196
MAX_RAW_BYTES=25_000_000
MAX_UNCOMPRESSED_BYTES=40_000_000
FIELDS=(
    ("country_id","year","sb_total_deaths_best"),
    ("country_id_cy","year_cy","sb_total_deaths_best_cy"),
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def loaded_immutable_issues():
    """Never infer country membership from prospective source itself."""
    raw=ISSUE.read_bytes()
    audit_issued(raw,MANIFEST.read_bytes(),
                 ORIGINAL.read_bytes(),OLD_SHADOW.read_bytes(),
                 OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    issue=json.loads(raw)
    ids=sorted(row["country_id"] for row in issue["countries"])
    if len(ids)!=N_COUNTRIES or len(set(ids))!=N_COUNTRIES:
        raise ValueError("Immutable 196-country GWNO list changed")
    return issue,ids


def preflight():
    """2026 status: no source file and no official future outcomes."""
    issue,ids=loaded_immutable_issues()
    return {
        "schema":READINESS_SCHEMA,
        "evaluation_target_year":TARGET_YEAR,
        "status":"NOT_READY_NO_VERIFIED_OFFICIAL_2027_RELEASE",
        "n_fixed_first_issued_GWNO":len(ids),
        "n_official_2027_labels_resolved":0,
        "first_complete_verified_official_source_available":False,
        "first_possible_full_2027_calendar_source_release_date":
            FIRST_POSSIBLE_RELEASE_DATE.isoformat(),
        "first_complete_source_priority_requires_external_release_review":True,
        "no_absent_country_is_automatically_zero":True,
        "source_data_must_represent_UCDP_OrganizedViolenceCY_state_based_best":True,
        "primary_pair_predeclared":
            issue["prospective_scoring_precommitment"]["primary_pair"],
        "new_global_only_issue_sha256":FROZEN_SHA256,
        "new_global_only_first_commit":FIRST_COMMIT,
        "original_GEO_sha256":SOURCE_SHA256,
        "original_LOG1P_sha256":FROZEN_ISSUE_SHA256,
        "original_15_alerts_sha256":ALERT_SHA,
        "all_prospective_model_probabilities_unchanged":True,
        "no_current_brier_or_logloss_reported":True,
        "manual_release_review_not_completed":True,
    }


def _strict_nonnegative_int(s,field):
    if type(s) is not str or re.fullmatch(r"(?:0|[1-9][0-9]*)",s.strip()) is None:
        raise ValueError("Invalid official UCDP integer field "+field)
    n=int(s.strip())
    if n>100_000_000:
        raise ValueError("UCDP count beyond reasonable range")
    return n


def _csv_bytes(raw):
    if not 0<len(raw)<=MAX_RAW_BYTES:
        raise ValueError("Invalid official UCDP archive size")
    if raw.startswith(b"PK\x03\x04"):
        try:
            with ZipFile(io.BytesIO(raw)) as z:
                entries=[x for x in z.infolist() if not x.is_dir()]
                if (len(entries)!=1 or
                    not entries[0].filename.lower().endswith(".csv") or
                    entries[0].file_size>MAX_UNCOMPRESSED_BYTES or
                    entries[0].file_size<100):
                    raise ValueError("Expected exactly one bounded official CSV")
                return z.read(entries[0])
        except BadZipFile as exc:
            raise ValueError("Corrupt official source archive") from exc
    if len(raw)>MAX_UNCOMPRESSED_BYTES:
        raise ValueError("Plain CSV source too large")
    return raw


def extract_complete_2027_labels(raw,expected_ids):
    """Parse data, never infer missing country-year rows as genuine zeros."""
    if (type(expected_ids) is not list or
        len(expected_ids)!=N_COUNTRIES or
        len(set(expected_ids))!=N_COUNTRIES or
        any(type(cid) is not int for cid in expected_ids)):
        raise ValueError("Need exactly 196 first-issued original GWNO IDs")
    try:
        content=_csv_bytes(raw).decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Official country-year CSV encoding invalid") from exc
    reader=csv.DictReader(io.StringIO(content))
    header=reader.fieldnames or []
    formats=[trio for trio in FIELDS if set(trio).issubset(set(header))]
    if len(formats)!=1:
        raise ValueError("Ambiguous or missing official UCDP CY best deaths schema")
    idkey,yearkey,countkey=formats[0]
    all_seen=set()
    labels={}
    deaths={}
    rows_total=0
    rows_2027=0
    for row in reader:
        rows_total+=1
        if rows_total>100_000:
            raise ValueError("Unexpected source rows")
        if row.get(None):
            raise ValueError("Malformed row has unexpected extra CSV columns")
        cid=_strict_nonnegative_int(row.get(idkey),"country_id")
        year=_strict_nonnegative_int(row.get(yearkey),"year")
        if not 1<=cid<=2000 or not 1989<=year<=TARGET_YEAR:
            raise ValueError("Official UCDP country-year range or cutoff invalid")
        key=(cid,year)
        if key in all_seen:
            raise ValueError("Duplicate official country-year record")
        all_seen.add(key)
        if year!=TARGET_YEAR:
            continue
        rows_2027+=1
        count=_strict_nonnegative_int(row.get(countkey),
                                      "sb_total_deaths_best")
        if cid in labels:
            raise ValueError("Duplicate 2027 GWNO record")
        labels[cid]=int(count>=25)
        deaths[cid]=count
    absent=sorted(set(expected_ids)-set(labels))
    if absent:
        raise ValueError(
            "INCOMPLETE official 2027 UCDP labels: "+str(len(absent))+
            " first-issued countries missing; never impute as zero")
    if not set(expected_ids).issubset(labels) or rows_total<196:
        raise ValueError("Future risk universe not observed in source")
    labels={cid:labels[cid] for cid in expected_ids}
    return labels,{
        "country_year_rows_read":rows_total,
        "year_2027_rows_present_in_source":rows_2027,
        "countries_2027_matched_to_first_issued_GWNO":N_COUNTRIES,
        "other_2027_country_ids_not_in_original_cohort":
            rows_2027-N_COUNTRIES,
        "n_binary_positives":sum(labels.values()),
        "min_2027_best_deaths":min(deaths[cid] for cid in expected_ids),
        "max_2027_best_deaths":max(deaths[cid] for cid in expected_ids),
        "positive_rule":"sb_total_deaths_best >= 25; explicit 2027 row required",
        "zero_is_accepted_only_as_literal_valid_record":True,
        "parser_fields_used":[idkey,yearkey,countkey],
    }


def _check_https(url):
    if (type(url) is not str or len(url)>2048 or
        urlparse(url).scheme!="https" or
        not urlparse(url).hostname or
        urlparse(url).username or urlparse(url).password):
        raise ValueError("Release citation must be an HTTPS public URL")


def review_provenance(meta,raw,as_of_date=None):
    """Human first-complete priority cannot be cryptographically inferred."""
    if not isinstance(meta,dict) or meta.get("schema")!=META_SCHEMA:
        raise ValueError("Missing independently reviewed UCDP source schema")
    if as_of_date is None:
        as_of_date=date.today()
    if type(as_of_date) is not date:
        raise ValueError("Invalid trusted calendar date")
    try:
        published=date.fromisoformat(meta["official_publication_date"])
        reviewed=datetime.fromisoformat(meta["human_reviewed_at_utc"].replace(
            "Z","+00:00"))
    except (KeyError,ValueError,AttributeError) as exc:
        raise ValueError("Source release and review dates required") from exc
    if (published<FIRST_POSSIBLE_RELEASE_DATE or
        published>as_of_date or
        reviewed.tzinfo is None or
        reviewed.utcoffset().total_seconds()!=0 or
        reviewed.date()<published or
        reviewed.date()>as_of_date):
        raise ValueError("Cannot certify a future/unreviewed 2027 official source")
    for field in ("official_source_landing_page",
                  "official_source_download_url",
                  "official_archive_release_listing_url"):
        _check_https(meta.get(field))
    if (meta.get("dataset")!="UCDP OrganizedViolenceCY"
        or meta.get("year_target")!=2027
        or meta.get("outcome_column")!="sb_total_deaths_best"
        or meta.get("state_based_threshold")!=25
        or meta.get("verified_official_release_by_human") is not True
        or meta.get("human_review_first_complete_196_by_edition") is not True
        or meta.get("human_review_previous_2027_editions") is not True
        or meta.get("source_country_universe_check")!="first_issued_196_GWNO"
        or not isinstance(meta.get("edition"),str)
        or not 1<=len(meta["edition"])<=100
        or not isinstance(meta.get("first_complete_review_evidence"),str)
        or len(meta["first_complete_review_evidence"].strip())<60
        or not isinstance(meta.get("earlier_release_inventory"),list)
        or any(type(x) is not str or not 1<=len(x)<=200
               for x in meta["earlier_release_inventory"])):
        raise ValueError("Source authenticity and first-complete review incomplete")
    digest=meta.get("source_sha256")
    if (type(digest) is not str or
        re.fullmatch("[a-f0-9]{64}",digest) is None or
        sha(raw)!=digest):
        raise ValueError("Official first-complete source SHA mismatch")
    return {
        "source_edition":meta["edition"],
        "source_sha256":digest,
        "official_publication_date":published.isoformat(),
        "human_reviewed_at_utc":meta["human_reviewed_at_utc"],
        "official_source_landing_page":meta["official_source_landing_page"],
        "official_source_download_url":meta["official_source_download_url"],
        "official_archive_release_listing_url":
            meta["official_archive_release_listing_url"],
        "earlier_release_inventory":meta["earlier_release_inventory"],
        "human_attested_first_complete_not_machine_proven":True,
        "review_evidence":meta["first_complete_review_evidence"].strip(),
        "provenance_manifest_sha256":sha(
            (json.dumps(meta,sort_keys=True,ensure_ascii=False,
                        separators=(",",":"))+"\n").encode("utf-8")),
    }


def evaluate_release(source_bytes,metadata,as_of_date=None):
    """Evaluate ONLY when official future archive/review is supplied.

    This is an operator-attested evaluation. A valid ZIP, release date or
    HTTPS link does not independently establish official publisher identity
    or whether an earlier complete edition existed.
    """
    issue,ids=loaded_immutable_issues()
    review=review_provenance(metadata,source_bytes,as_of_date)
    labels,coverage=extract_complete_2027_labels(source_bytes,ids)
    s=prospective_full196_score(issue,labels)
    if s["n_country_labels"]!=196:
        raise AssertionError("Fixed prospective scoring changed")
    prior=json.loads(PRECOMMIT_REPORT.read_text(encoding="utf-8"))
    cases=prior.get("all_country_probability_and_future_Brier_conditional_effects")
    if (prior.get("fixed_original_GWNO_country_n")!=196 or
        prior.get("official_2027_outcomes_resolved")!=0 or
        prior.get("new_global_only_first_issue_sha256")!=FROZEN_SHA256 or
        not isinstance(cases,list) or len(cases)!=196):
        raise ValueError("First-issued ex ante error-attribution source changed")
    expected=0.0
    seen=set()
    for r in cases:
        cid=r["country_id"]
        if cid not in labels or cid in seen:
            raise ValueError("Predeclared Brier attribution country mismatch")
        seen.add(cid)
        canonical=next(z for z in issue["countries"] if z["country_id"]==cid)
        if abs(100*(
            canonical["global_only_alpha1_p_active_2027"]-
            canonical["original_LOG1P2027_p_active_frozen"])-
            r["primary_probability_delta_pp"])>1e-8:
            raise ValueError("Predeclared probability delta not reproducible")
        expected+=(
            canonical["global_only_alpha1_p_active_2027"]-
            labels[cid])**2-(
            canonical["original_LOG1P2027_p_active_frozen"]-
            labels[cid])**2
    primary=s["predeclared_paired_differences"][
        "primary_Brier_globalonly_alpha1_minus_original_LOG1P"]
    if abs(primary-expected/N_COUNTRIES)>1e-11 or len(seen)!=196:
        raise AssertionError("First-issued prospective primary score changed")
    return {
        "schema":SCORING_SCHEMA,
        "status":"SCORED_FROM_OPERATOR_ATTESTED_FUTURE_SOURCE_NOT_AUTOMATICALLY_AUTHENTICATED",
        "strictly_future_official_release_required":True,
        "original_2027_forecasts_or_alerts_modified":False,
        "first_issued_global_only_sha256":FROZEN_SHA256,
        "first_issued_LOG1P_sha256":FROZEN_ISSUE_SHA256,
        "original_GEO_sha256":SOURCE_SHA256,
        "original_15_alerts_sha256":ALERT_SHA,
        "source_review":review,
        "source_coverage":coverage,
        "score":s,
        "first_issued_countrywise_primary_Brier_identity_verified":True,
        "primary_score_does_not_select_a_model_for_2027_post_hoc":True,
        "country_outcomes_correlated_no_IID_significance_test":True,
        "manual_first_complete_release_priority_review_still_required":True,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path)
    parser.add_argument("--provenance",type=Path)
    args=parser.parse_args()
    if (args.source is None)!=(args.provenance is None):
        parser.error("--source and --provenance are both required to score")
    if args.source is None:
        print(json.dumps(preflight(),sort_keys=True,ensure_ascii=False,indent=2))
        return
    if date.today()<FIRST_POSSIBLE_RELEASE_DATE:
        raise ValueError("Cannot score 2027 before calendar year 2028")
    meta=json.loads(args.provenance.read_text(encoding="utf-8"))
    source=args.source.read_bytes()
    report=evaluate_release(source,meta)
    print(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
