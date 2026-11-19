#!/usr/bin/env python3
"""Burundi GED442626 independent-record audit: claim-specific source dependency.

Four public institutional documents, manually inspected 19 Nov 2026:
  - Belgium CGRS 2022-10-12 report pp11 (2022/Jun 18..20, >=10;
    *explicit* SOS 2022-06-21 endnote 52; ACLED contextual compilation).
  - Belgium CGRS 2023-05-31 update pp11 (same date/claim; explicit SOS
    endnote 58; institutional reuse does NOT equal another witness).
  - FEWS NET 2022-10 Burundi Food Security Outlook p4 (Mabayi conflict
    Jun 19..21 but NO fatality count and NO independently identified
    eyewitness; its underlying reporting chain remains unknown).
  - SOS-Torture Burundi weekly no341 dated 2022-06-25, pp1..3:
    period Jun18..25, three homicides *in monitoring scope*, no Mabayi
    battle in case descriptions. Omission does NOT prove zero battle deaths.

This adds to frozen PR #132, never alters its 6-document source ledger.
"Independent institution" != independent reporting/witness/victim evidence.
The paper/PDF URLs were reviewed via public text and page screenshots,
but NO PDF/HTML bytes were downloaded, saved or SHA-verified in git.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from audit_geo2027_global_only_matched_issue import (
    ISSUE, MANIFEST, OLD_SHADOW, OLD_MANIFEST, ORIGINAL, ALERTS,
    audit as audit_issued,
)
from prepare_geo2027_transition_alerts import FORECAST_PATH,SOURCE_SHA256

ROOT=Path(__file__).resolve().parents[1]
ANCHOR=ROOT/"data/geo-burundi-2022-source-dependency-evidence.json"
OUTPUT=ROOT/"data/geo-burundi-2022-institutional-source-independence.json"
OBSERVATION_DATE="2026-11-19"
LOCAL_TIMEFRAME=("2022-06-18","2022-06-21")
ALLOWED_SOURCE_HOSTS={"www.ecoi.net","fews.net","sostortureburundi.org"}

# Facts from inspected published documents are selective metadata/paraphrase,
# not reproduced copyright-protected content.
NEW_SOURCES=(
    {
        "id":"cgrs_belgium_20221012",
        "publisher":"Belgian CGRS/Cedoca",
        "institutional_family":"Belgian CGRS/Cedoca",
        "date":"2022-10-12",
        "precision":"day",
        "url":"https://www.ecoi.net/en/file/local/2085322/coi_focus_burundi._situation_securitaire_20221012.pdf",
        "locator":"p11/43, section 2.1 and footnotes 43, 50, 52",
        "document_type":"secondary_country_origin_information_compilation",
        "claim_scope":"burundi_mabayi_event",
        "claim_event_occurred":True,
        "reported_fatalities":10,
        "fatality_qualifier":"at_least",
        "reported_date_range":["2022-06-18","2022-06-20"],
        "event_actor_attribution":"alleged_Rwandan_border_forces_vs_FLN_as_reported",
        "directly_identified_witnesses_n":0,
        "directly_identified_fatality_records_n":0,
        "has_footnote_directly_to_sos_20220621":True,
        "has_access_to_acled_raw_event_in_our_project":False,
        "claim_transmission":"Explicitly cites SOS Médias Burundi 2022-06-21 for 10 deaths; discusses ACLED records drawn largely from SOS reporting",
        "local_primary_fatality_confirmation":False,
    },
    {
        "id":"cgrs_belgium_20230531",
        "publisher":"Belgian CGRS/Cedoca",
        "institutional_family":"Belgian CGRS/Cedoca",
        "date":"2023-05-31",
        "precision":"day",
        "url":"https://www.ecoi.net/en/file/local/2093002/coi_focus_burundi._situation_securitaire_20230531.pdf",
        "locator":"p11/55, section 2.1 and footnotes 56, 58",
        "document_type":"secondary_updated_country_origin_information_compilation",
        "claim_scope":"burundi_mabayi_event",
        "claim_event_occurred":True,
        "reported_fatalities":10,
        "fatality_qualifier":"at_least",
        "reported_date_range":["2022-06-18","2022-06-20"],
        "event_actor_attribution":"alleged_Rwandan_border_forces_vs_FLN_as_reported",
        "directly_identified_witnesses_n":0,
        "directly_identified_fatality_records_n":0,
        "has_footnote_directly_to_sos_20220621":True,
        "has_access_to_acled_raw_event_in_our_project":False,
        "claim_transmission":"Update repeats ten-death paragraph with footnote 58 to SOS 21 June, ACLED context described as mostly based on SOS.",
        "local_primary_fatality_confirmation":False,
    },
    {
        "id":"fewsnet_burundi_202210",
        "publisher":"FEWS NET (Famine Early Warning Systems Network)",
        "institutional_family":"FEWS NET",
        "date":"2022-10",
        "precision":"month",
        "url":"https://fews.net/fr/east-africa/burundi/perspectives-sur-la-securite-alimentaire/octobre-2022/print",
        "locator":"p4, October 2022 to May 2023 outlook; section Sécurité",
        "document_type":"food_security_country_outlook_with_security_context",
        "claim_scope":"burundi_mabayi_event",
        "claim_event_occurred":True,
        "reported_fatalities":None,
        "fatality_qualifier":"no_number_asserted",
        "reported_date_range":["2022-06-19","2022-06-21"],
        "event_actor_attribution":"armed_conflict_unspecified_actors",
        "directly_identified_witnesses_n":0,
        "directly_identified_fatality_records_n":0,
        "has_footnote_directly_to_sos_20220621":False,
        "has_access_to_acled_raw_event_in_our_project":False,
        "claim_transmission":"Reports Mabayi armed conflict on Jun19..21, no death total, no specific upstream source citation for episode in the examined passage",
        "local_primary_fatality_confirmation":False,
    },
    {
        "id":"sostorture_weekly_341_20220625",
        "publisher":"SOS-Torture Burundi",
        "institutional_family":"SOS-Torture Burundi",
        "date":"2022-06-25",
        "precision":"day",
        "url":"https://sostortureburundi.org/wp-content/uploads/2022/06/Rapport-hebdomadaire-no-341.pdf",
        "locator":"pp1-3, weekly monitoring 18..25 June 2022; described homicides and assaults",
        "document_type":"weekly_human_rights_abuse_monitoring",
        "claim_scope":"noncomprehensive_rights_monitoring_not_battle_registry",
        "claim_event_occurred":None,
        "reported_fatalities":None,
        "fatality_qualifier":"omission_not_zero",
        "reported_date_range":None,
        "event_actor_attribution":"none_on_ged_442626",
        "directly_identified_witnesses_n":0,
        "directly_identified_fatality_records_n":0,
        "has_footnote_directly_to_sos_20220621":False,
        "has_access_to_acled_raw_event_in_our_project":False,
        "claim_transmission":"Summarizes 3 homicides under specific human-rights monitoring mandate; does not describe GED 442626 Mabayi FLN battle; no contradiction with 10 reported rebel combatants",
        "local_primary_fatality_confirmation":False,
    },
)

# Edge direction always "claim was carried or reported THROUGH from -> to".
# No ACLED raw record is downloaded, so no direct ACLED -> SOS edge is
# asserted; the Belgian institutional report's OWN words describe overlap.
NEW_EDGES=(
    {
        "from":"cgrs_belgium_20221012","to":"sos_20220621",
        "kind":"explicit_citation_of_original_ten_casualty_news",
        "directed":True,"fatality_confirmation_independent":False,
        "evidence_locator":"CGRS 2022 p11 n52"
    },
    {
        "from":"cgrs_belgium_20230531","to":"sos_20220621",
        "kind":"explicit_citation_of_original_ten_casualty_news",
        "directed":True,"fatality_confirmation_independent":False,
        "evidence_locator":"CGRS 2023 p11 n58"
    },
    {
        "from":"cgrs_belgium_20230531","to":"cgrs_belgium_20221012",
        "kind":"same_institution_two_versions_shared_source_no_direct_copy_claim",
        "directed":False,"fatality_confirmation_independent":False,
        "evidence_locator":"Common CGRS/Cedoca series, same location/event/underlying SOS footnote"
    },
    {
        "from":"fewsnet_burundi_202210","to":"sos_20220621",
        "kind":"possible_unverified_shared_upstream_reporting",
        "directed":False,"fatality_confirmation_independent":False,
        "evidence_locator":"FEWS NET 2022 p4 does not attribute Mabayi report; unknown"
    },
)

CLAIMS={
    "armed_clashes_in_mabayi_june_2022":
        "reported_by_sos_and_fewsnet_and_secondary_belgian_compilations",
    "fatalities_10_confirmed_by_original_unnamed_source":
        "reported_not_independently_adjudicated",
    "mabayi_fatalities_10_at_least":
        "both_cgrs_reports_repeat_sos_20220621_explicit_source",
    "reuters_rwanda_bus_event_victims_separate":
        "same_original_boundary_from_prior_report",
    "date_window_18_20":
        "sos_derivative_and_cgrs_secondary",
    "date_window_19_21":
        "ged_source_and_fewsnet_and_icg_secondhand",
    "sos_torture_three_homicides_not_a_denial":
        "different_monitoring_scope_no_record_of_mabayi_battle",
    "acled_event_independent_fatality_census":
        "not_established_raw_acled_2022_record_unavailable",
}

def validate_anchor(prior):
    if (prior.get("schema")!="idealab.psico.geo_burundi_2022_documentary_source_genealogy.v1"
        or prior.get("original_GEO2027_SHA256")!=SOURCE_SHA256
        or prior.get("prior_GED_event_id")!=442626
        or prior.get("prior_GED_best_deaths")!=10
        or prior.get("prior_GDELT_no_local_100km_footprint") is not True
        or prior.get("original_GEO2027_GEO2028_not_modified") is not True
        or prior.get("verified_independent_named_victim_lists_n")!=0
        or prior.get("verified_disjoint_firsthand_witness_sets_n")!=0
        or len(prior.get("sources",[]))!=6):
        raise ValueError("Previous primary source genealogy or original issue modified")


def check_documents_and_edges(prior):
    nodes={s["id"]:s for s in prior["sources"]}
    for src in NEW_SOURCES:
        if src["id"] in nodes:
            raise ValueError("Institutional source id duplicates frozen ledger")
        nodes[src["id"]]=src
    if len(nodes)!=len(prior["sources"])+len(NEW_SOURCES):
        raise ValueError("Duplicated new documentary evidence")
    if {s["institutional_family"] for s in NEW_SOURCES}!={
        "Belgian CGRS/Cedoca","FEWS NET","SOS-Torture Burundi"}:
        raise ValueError("Expected three distinct institutional families")
    hosts={"www.ecoi.net","fews.net","sostortureburundi.org"}
    for src in NEW_SOURCES:
        host=urlsplit(src["url"]).hostname
        if host not in hosts:
            raise ValueError("Unreviewed institutional documentary URL")
        d=src["date"]
        date.fromisoformat(d if src["precision"]=="day" else d+"-01")
        rng=src["reported_date_range"]
        if rng is not None:
            if len(rng)!=2 or rng[0]>rng[1]:
                raise ValueError("Invalid publication case-date claim")
            if rng[0]<LOCAL_TIMEFRAME[0] or rng[1]>LOCAL_TIMEFRAME[1]:
                raise ValueError("Not in the predeclared June 18–21 research window")
        if (src["directly_identified_witnesses_n"]!=0
            or src["directly_identified_fatality_records_n"]!=0
            or src["local_primary_fatality_confirmation"] is not False):
            raise ValueError("Improperly claimed individual witness confirmation")
    for src in NEW_SOURCES[:2]:
        if (not src["has_footnote_directly_to_sos_20220621"]
            or src["reported_fatalities"]!=10
            or src["reported_date_range"]!=["2022-06-18","2022-06-20"]):
            raise ValueError("Secondary count/explicit SOS footnotes must be retained")
    for src in NEW_SOURCES[2:]:
        if src["reported_fatalities"] is not None:
            raise ValueError("FEWSNET and rights monitoring are not ten-death counts")
    for edge in NEW_EDGES:
        if edge["from"] not in nodes or edge["to"] not in nodes:
            raise ValueError("Evidence edge references missing source")
        if edge["fatality_confirmation_independent"] is not False:
            raise ValueError("Inferred fatality independence prohibited")
    if [e["directed"] for e in NEW_EDGES]!=[True,True,False,False]:
        raise ValueError("Unverified transmission must not acquire direction")
    return nodes


def build_report(prior):
    validate_anchor(prior)
    nodes=check_documents_and_edges(prior)
    new=[dict(x) for x in NEW_SOURCES]
    dep=[dict(x) for x in NEW_EDGES]
    doc_index={s["id"]:s for s in NEW_SOURCES}
    evid={
        "event_exists":{
            "new_institutional_context": [
                "fewsnet_burundi_202210",
                "cgrs_belgium_20221012",
                "cgrs_belgium_20230531",
            ],
            "independent_firsthand_episode_witness_confirmed":False,
            "fewsnet_confirms_event_occurrence_as_reported":True,
            "fewsnet_reports_fatality_count":False,
            "fewsnet_upstream_reporting_provenance_known":False,
        },
        "fatalities_exactly_ten":{
            "cgrs_sources_carry_ten": [
                "cgrs_belgium_20221012","cgrs_belgium_20230531"],
            "cgrs_cite_sos_for_episode":True,
            "distinct_independent_ten_death_censuses_confirmed":0,
            "witness_or_victim_roster_identified":False,
            "source_redundancy_risk":"high_due_to_explicit_SOS_citation",
        },
        "temporal_scope":{
            "early_window":["2022-06-18","2022-06-20"],
            "late_window":["2022-06-19","2022-06-21"],
            "window_intersection":["2022-06-19","2022-06-20"],
            "exact_first_last_day_independently_verified":False,
        },
        "human_rights_monitoring_omission":{
            "source":"sostorture_weekly_341_20220625",
            "period":["2022-06-18","2022-06-25"],
            "reported_homicides_in_scope_n":3,
            "specific_ged_event_442626_listed":False,
            "scope_is_exhaustive_of_rebel_combat_deaths":False,
            "omission_proves_no_ten_battle_deaths":False,
            "Cibitoke_June_23_unidentified_bodies_are_GED_442626":False,
        },
        "secondary_ACLED_reporting":{
            "ACLED_firsthand_event_data_obtained":False,
            "CGRS_reports_2022_ACLED_combat_records_based_largely_on_SOS":True,
            "ACLED_confirms_ten_fatalities_independently":False,
        },
    }
    # Document source metadata are an editorial source snapshot, not raw PDF bytes.
    source_payload=json.dumps({
        "new_documents":new,"edges":dep,"assertions":evid,
        "prior_ledger_sha":prior["source_snapshot_sha256_not_remote_page_byte_hash"],
    },sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    return {
        "schema":"idealab.psico.geo_burundi_2022_institutional_dependency_audit.v1",
        "status":"DOCUMENTARY_EVENT_CORROBORATION_UNVERIFIED_FATALITY_INDEPENDENCE",
        "research_date":OBSERVATION_DATE,
        "original_GEO2027_issue_SHA256":SOURCE_SHA256,
        "frozen_prior_genealogy":str(ANCHOR.relative_to(ROOT)),
        "prior_genealogy_structured_sha256":
            prior["source_snapshot_sha256_not_remote_page_byte_hash"],
        "new_source_metadata_and_assertions_sha256_not_remote_pdf_bytes":
            hashlib.sha256(source_payload).hexdigest(),
        "new_institutional_document_entries_n":len(new),
        "new_distinct_institutional_families_n":3,
        "previous_reported_sources_n":len(prior["sources"]),
        "total_reviewed_source_records_n":len(nodes),
        "new_institutional_documents":new,
        "new_dependency_edges":dep,
        "claim_classification":evid,
        "ordinal_scientific_assessment":{
            "evidence_of_reported_battle":"broader_documentary_context",
            "independence_of_battle_reporting":"unproven_FEWS_underlying_inputs_unknown",
            "evidence_of_ten_fatalities":"documented_but_secondary_reuse",
            "independent_person_level_fatality_validation":"not_demonstrated",
            "accurate_18_to_21_day_window":"unresolved_conflicting_sources",
            "alleged_actor_identity":"not_established",
            "change_to_GEO_model_justified":False,
        },
        "statistical_independence_or_true_error_rate_estimated":False,
        "source_documents_bytes_SHA256_pinned":False,
        "sos_torture_three_homicides_can_be_compared_as_total_statebased_deaths":False,
        "original_GEO2027_GEO2028_issued_vectors_modified":False,
        "limitations":"FEWS NET is an institutionally separate security-context report but its underlying information provenance is not identified. Both Belgian official country reports explicitly cite SOS 21 June for the ten-death incident while referencing ACLED coverage largely derived from SOS; they do NOT independently identify the dead. The June25 SOS-Torture weekly's three homicide cases are from a different monitoring mandate, not an exhaustive fatality count; absence of the clash is not counterevidence. Two windows 18-20 and 19-21 cannot be reconciled without first-hand dates. Original PDF and webpage bytes were read through public views, not downloaded/hashed/archived; SHA refers only to manually curated structured annotations. No model, issue, or source recoding.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--print-report",action="store_true")
    p.add_argument("--check-report",action="store_true")
    args=p.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Original GEO2027 issue hash changed")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    prior=json.loads(ANCHOR.read_text(encoding="utf-8"))
    report=build_report(prior)
    if args.check_report and json.loads(OUTPUT.read_text(encoding="utf-8"))!=report:
        raise ValueError("Frozen source-dependency study changed")
    if args.print_report:
        print("BURUNDI_INSTITUTIONAL_DEPENDENCY_BEGIN",flush=True)
        print(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False))
        print("BURUNDI_INSTITUTIONAL_DEPENDENCY_END",flush=True)
    else:
        print(json.dumps({"new_institutional_entries":
                          report["new_institutional_document_entries_n"],
                          "new_institutional_families":
                          report["new_distinct_institutional_families_n"],
                          "independent_fatality_sources":
                          report["claim_classification"]["fatalities_exactly_ten"]["distinct_independent_ten_death_censuses_confirmed"]},
                         sort_keys=True))


if __name__=="__main__":
    main()
