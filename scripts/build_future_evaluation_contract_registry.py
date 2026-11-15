#!/usr/bin/env python3
"""A SINGLE audit index of FOUR issued prospective 2027/2028 evaluation contracts.

Source is original SHA-256 pinned 2027 (424 country-endpoint questions) and
original first-public GEO2028 (196), NOT retrospective tests or synthetic
observations. This is a read-only, zero-outcomes contract index, NOT an
evaluated score table. Never pool outcomes, Brier, IID samples or horizons.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import build_2027_prospective_registry as registry
import audit_geo2028_first_public_issue as first28
import evaluate_2027_official as geo27
import evaluate_2027_newconf_official as new27
import evaluate_acd2027_retention_official as acd27
import evaluate_geo2028_first_complete_official as geo28

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/future-evaluation-contracts.json"
COHORT_ORDER=("GEO2027","NEWCONF2027","ACD2027","GEO2028")
COUNT={"GEO2027":196,"NEWCONF2027":196,"ACD2027":32,"GEO2028":196}
FIRST_COMPLETE={"GEO2027":196,"NEWCONF2027":196,"ACD2027":32,"GEO2028":196}
EARLIEST={
    "GEO2027":"2028-01-01",
    "NEWCONF2027":"2028-01-01",
    "ACD2027":"2028-01-01",
    "GEO2028":"2029-01-01",
}


def authenticated_sources():
    docs,manifests=registry.read_issued()
    original=registry.make_registry(docs,manifests)
    raw=(ROOT/first28.SOURCE_PATH).read_bytes()
    m28=json.loads((ROOT/first28.MANIFEST_PATH).read_text(encoding="utf8"))
    first28.check_raw(raw,m28,docs["geo"],original)
    d28=json.loads(raw)
    geo27.load_frozen_issue(
        ROOT/"data/forecast-2027-ucdp261.json",
        ROOT/"data/forecast-2027-manifest.json")
    new27.load_issued()
    acd27.authenticated_issue()
    geo28.load_immutable_issue()
    if (original["n_unique_country_endpoint_rows"]!=424 or
        original["n_verified_future_2027_outcomes"]!=0 or
        original["observational_skill_demonstrated"] is not False or
        d28["2028_outcomes_resolved"]!=0 or
        d28["prospective_predictive_skill_demonstrated"] is not False):
        raise ValueError("A first-issued future cohort is not unchanged and unresolved")
    return original,d28,m28


def ensure_future_gates():
    """Test existing evaluation software's immutable forward-only gate."""
    if ("bootstrap_interval" in vars(geo27) or
        "bootstrap_delta" in vars(new27) or
        "random" in vars(geo27) or "random" in vars(new27) or
        not callable(geo27.sharp_partial_paired_brier) or
        not callable(new27.sharp_partial_paired_brier)):
        raise ValueError("Country-IID bootstrap reintroduced into official 2027 candidates")
    if (geo27.YEAR!=2027 or geo27.COHORT!=196 or
        geo27.MIN_RESOLVED!=187 or
        new27.YEAR!=2027 or new27.COHORT!=196 or
        new27.MIN_RESOLVED!=187 or
        acd27.TARGET_YEAR!=2027 or acd27.COUNTRY_COUNT!=32 or
        acd27.REQUIRED_INITIAL_VERSION!="281" or
        geo28.YEAR!=2028 or geo28.ORIGIN_YEAR!=2025 or
        geo28.HORIZON!=3 or geo28.COHORT!=196):
        raise ValueError("Existing 2027/2028 future evaluator coverage/horizon changed")
    fake="a"*64
    future_sources=(
        (geo27.validate_future_source,
         "https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-281-csv.zip","2028-07-01"),
        (new27.validate_future_source,
         "https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-multiple-onset-281.csv","2028-07-01"),
        (acd27.validate_future_source,
         "https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-281-csv.zip","2028-07-01"),
    )
    for gate,url,released in future_sources:
        gate(url,fake,released)
    geo28.validate_candidate_source(
        "https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-291-csv.zip",
        fake,"2029-07-01",as_of=date(2030,1,1))
    denied=(
        (geo27.validate_future_source,
         "https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-261-csv.zip","2028-07-01"),
        (new27.validate_future_source,
         "https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-multiple-onset-251.csv","2028-07-01"),
        (acd27.validate_future_source,
         "https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-261-csv.zip","2028-07-01"),
    )
    for gate,url,released in denied:
        try:
            gate(url,fake,released)
        except ValueError:
            pass
        else:
            raise ValueError("Historical UCDP release would be mistaken for future observations")
    try:
        geo28.validate_candidate_source(
            "https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-291-csv.zip",
            fake,"2028-12-31",as_of=date(2030,1,1))
    except ValueError:
        pass
    else:
        raise ValueError("Future GEO2028 2028 label leak gate failed")
    return True


def build_index(original:dict,d28:dict,m28:dict)->dict:
    ensure_future_gates()
    if (original.get("schema")!="idealab.psico.prospective_2027_issued_registry.v1"
        or original.get("status")!="PROSPECTIVE_ISSUED_ALL_OUTCOMES_2027_UNRESOLVED"
        or original.get("cohort_order")!=list(COHORT_ORDER[:3])
        or original.get("target_year")!=2027 or
        original.get("n_unique_country_endpoint_rows")!=424 or
        original.get("n_verified_future_2027_outcomes")!=0 or
        original.get("observational_skill_demonstrated") is not False or
        original.get("independent_country_endpoints_or_country_years") is not False):
        raise ValueError("Immutable three-2027-cohort source registry changed")
    if (d28.get("forecast_id")!=first28.preparation.PROTOCOL_ID or
        d28.get("target",{}).get("year")!=2028 or
        d28.get("origin",{}).get("year")!=2025 or
        d28.get("protocol",{}).get("horizon_years")!=3 or
        d28.get("2028_outcomes_resolved")!=0 or
        d28.get("prospective_predictive_skill_demonstrated") is not False or
        m28.get("forecast_sha256")!=first28.ISSUE_SHA or
        m28.get("first_public_forecast_commit")!=first28.FIRST or
        m28.get("actual_2028_outcomes_observed")!=0 or
        m28.get("independently_notarized") is not False):
        raise ValueError("Immutable GEO2028 first public issue source changed")
    rows=original["rows"]
    if (len(rows)!=424 or any(row.get("observed_2027") is not None or
          row.get("resolved_2027") is not False or
          row.get("certified_result") is not False for row in rows)):
        raise ValueError("2027 country-endpoint outcome leaked into original issued index")
    counts={k:sum(row.get("cohort")==k for row in rows) for k in COHORT_ORDER[:3]}
    if (counts!={"GEO2027":196,"NEWCONF2027":196,"ACD2027":32}
        or len(d28.get("countries",[]))!=196):
        raise ValueError("Issued 2027/28 cohort sizes changed")
    p28={r["country_id"]:r for r in d28["countries"]}
    p27={r["country_id"]:r for r in rows if r["cohort"]=="GEO2027"}
    if (len(p28)!=196 or len(p27)!=196 or set(p28)!=set(p27) or
        any(p28[k]["p_issued_geo2027_2step_for_temporal_comparison_only"]!=
            p27[k]["p_primary"] for k in p28)):
        raise ValueError("GEO2027/GEO2028 origin country crosswalk changed")
    contracts={
        "GEO2027":{
            "event_definition":"Estado binario UCDP OrganizedViolenceCY, violencia estatal >=25 muertes en 2027",
            "origin_year":2025,"target_year":2027,"horizon_years":2,
            "source_family":"UCDP OrganizedViolenceCY","official_first_candidate_version":"28.1",
            "first_eligible_source_date":EARLIEST["GEO2027"],
            "primary_field":"p_model","primary_comparison_field":"p_baseline_global_5y",
            "secondary_model_fields":["p_global_markov"],
            "comparison_sign":"Brier(primario)-Brier(referencia), negativo favorece primario",
            "provisional_score_min_coverage":187,
            "complete_source_coverage_required_for_certification":196,
            "coverage_basis":"GWNO explicit year-2027 official binary state-based records",
            "evaluation_script":"scripts/evaluate_2027_official.py",
            "experimental_interval_warning":"Bootstrap IID por países desactivado; solo diferencia Brier descriptiva y cotas exactas ante etiquetas faltantes, no intervalos de confianza",
        },
        "NEWCONF2027":{
            "event_definition":"ANY(newconf=1) nuevos episodios intraestatales por GWNO-año 2027",
            "origin_year":2025,"target_year":2027,"horizon_years":2,
            "source_family":"UCDP Intrastate Country Level Multiple Onset",
            "official_first_candidate_version":"28.1",
            "first_eligible_source_date":EARLIEST["NEWCONF2027"],
            "primary_field":"p_model","primary_comparison_field":"p_baseline_global_5y",
            "secondary_model_fields":["p_country_eb","p_activity_global"],
            "comparison_sign":"Brier(primario)-Brier(referencia), negativo favorece primario",
            "provisional_score_min_coverage":187,
            "complete_source_coverage_required_for_certification":196,
            "coverage_basis":"GWNO con filas de episodio 2027 explícitas y no ambiguas; ausencia no equivale a cero",
            "evaluation_script":"scripts/evaluate_2027_newconf_official.py",
            "experimental_interval_warning":"Bootstrap IID por países desactivado; solo diferencia Brier descriptiva y cotas exactas ante etiquetas faltantes, no intervalos de confianza",
        },
        "ACD2027":{
            "event_definition":"Persistencia de cualquier conflicto intraestatal tipo 3/4 ACD en 2027 entre 32 países activos en 2025",
            "origin_year":2025,"target_year":2027,"horizon_years":2,
            "source_family":"UCDP/PRIO Armed Conflict Dataset",
            "official_first_candidate_version":"28.1",
            "first_eligible_source_date":EARLIEST["ACD2027"],
            "primary_field":"p_global_recent5","primary_comparison_field":"p_country_eb",
            "secondary_model_fields":["p_lag1_group"],
            "comparison_sign":"Brier(primario)-Brier(comparador), negativo favorece primario",
            "provisional_score_min_coverage":32,
            "complete_source_coverage_required_for_certification":32,
            "coverage_basis":"32 GWNO con codificación histórica inequívoca, sin filas futuras ambiguas; debe certificarse convención de ausencias",
            "evaluation_script":"scripts/evaluate_acd2027_retention_official.py",
            "experimental_interval_warning":"Sin IID bootstrap; las cotas Brier dependen del recuento de resultados",
        },
        "GEO2028":{
            "event_definition":"Estado binario UCDP OrganizedViolenceCY, violencia estatal >=25 muertes en 2028",
            "origin_year":2025,"target_year":2028,"horizon_years":3,
            "source_family":"UCDP OrganizedViolenceCY",
            "official_first_candidate_version":"29.1",
            "first_eligible_source_date":EARLIEST["GEO2028"],
            "primary_field":"p_model","primary_comparison_field":"p_baseline_global_5y",
            "secondary_model_fields":["p_global_markov_3step"],
            "comparison_sign":"Brier(primario)-Brier(referencia), negativo favorece primario",
            "provisional_score_min_coverage":196,
            "complete_source_coverage_required_for_certification":196,
            "coverage_basis":"196 GWNO con fila binaria 2028 explícita; no imputar países ausentes",
            "evaluation_script":"scripts/evaluate_geo2028_first_complete_official.py",
            "experimental_interval_warning":"Sin IID bootstrap ni p-valores; panel anual único y mismo origen que GEO2027",
        },
    }
    out=[]
    for c in COHORT_ORDER:
        x=contracts[c]
        known=original["cohorts"][c] if c!="GEO2028" else None
        source_sha=known["forecast_sha256"] if known else first28.ISSUE_SHA
        first_commit=known["first_public_commit"] if known else first28.FIRST
        issued_utc=known["issue_utc"] if known else first28.ISSUE_UTC
        n=COUNT[c]
        if (x["origin_year"]!=2025 or
            x["target_year"]-x["origin_year"]!=x["horizon_years"] or
            x["provisional_score_min_coverage"]>n or
            x["complete_source_coverage_required_for_certification"]!=n or
            x["first_eligible_source_date"]!=EARLIEST[c]):
            raise ValueError("Future country/year metric and chronological contract invalid")
        if c!="GEO2028" and (
            known["fixed_country_count"]!=n or
            known["origin_data_through"]!=2025 or
            known["resolution"]!="PENDIENTE_FUENTE_ANUAL_OFICIAL_2027" or
            known["primary_model"]!=x["primary_field"]):
            raise ValueError("2027 original primary model or certification status drifted")
        out.append({
            "iid_country_bootstrap_disabled_in_official_candidate_evaluator":True,
            "sharp_missing_label_brier_region_available":c in ("GEO2027","NEWCONF2027"),
            "statistical_confidence_interval_claimed":False,
            "cohort":c,"forecast_sha256":source_sha,
            "first_public_forecast_commit":first_commit,
            "first_public_forecast_utc":issued_utc,
            "issued_country_questions":n,
            "original_issued_country_questions_unresolved":n,
            "source_independently_verified_full_future_release":False,
            "future_country_labels_certified":0,
            "official_scores_certified":False,
            "candidate_scores_available_now":False,
            "prospective_skill_demonstrated":False,
            "independently_notarized":False,
            "depends_on_same_2025_origin_as_GEO2027":c=="GEO2028",
            "provisional_scoring_is_never_certification":True,
            **x,
        })
    if (sum(x["issued_country_questions"] for x in out)!=620 or
        sum(x["future_country_labels_certified"] for x in out)!=0):
        raise ValueError("Some prospective observations have been manufactured")
    return {
        "schema":"idealab.psico.future_evaluation_contract_registry.v1",
        "status":"FOUR_ISSUED_COHORTS_ZERO_OFFICIAL_CERTIFIED_LABELS",
        "publication_purpose":"READ_ONLY_EVALUATION_CONTRACT_NOT_2027_2028_OUTCOME",
        "first_issued_2027_country_endpoint_questions":424,
        "additional_issued_GEO2028_country_questions":196,
        "total_issued_country_endpoint_year_questions":620,
        "n_forecast_emissions":4,
        "n_future_outcomes_independently_certified":0,
        "n_official_scoring_reports_certified":0,
        "n_independent_country_year_trials_claimed":0,
        "cross_endpoint_country_overlap_present":True,
        "cross_year_2027_2028_GEO_origin_overlap_present":True,
        "global_prospective_skill_demonstrated":False,
        "first_public_utc_is_github_metadata_not_independent_notary":True,
        "first_complete_source_must_be_independently_attested":True,
        "never_treat_exploratory_score_as_certified":True,
        "never_pool_Brier_or_country_years_from_distinct_endpoints":True,
        "never_claim_IID_country_bootstrap_significance":True,
        "ordered_cohorts":list(COHORT_ORDER),
        "cohorts":out,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--check-report")
    args=p.parse_args()
    data=build_index(*authenticated_sources())
    body=registry.canonical(data)
    if args.check_report and Path(args.check_report).read_bytes()!=body:
        raise ValueError("Source-pinned future evaluation registry changed")
    print("UNIFIED_FUTURE_EVALUATION_BEGIN")
    print(body.decode(),end="")
    print("UNIFIED_FUTURE_EVALUATION_END")


if __name__=="__main__":
    main()
