#!/usr/bin/env python3
"""Audit 2022 Burundi GED442626 source genealogy without false independence.

Manually checked, explicitly cited public-source claim registry as-of
2026-11-19. Deterministic and offline: not an archive downloader, and
NOT a claim that original public pages/PDF bytes are SHA-pinned.

Distinguish an original-ish report, a secondary digest, explicit press
republication, and an overlapping NGO report whose actual information
chain cannot be resolved. Also separate a contemporaneous attack on a
bus IN RWANDA from the deaths IN BURUNDI. An independent victim list or
forensic count is not available. The 2027 original forecasts are not
reissued or rescored.
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
from prepare_geo2027_transition_alerts import FORECAST_PATH, SOURCE_SHA256

ROOT=Path(__file__).resolve().parents[1]
PREVIOUS=ROOT/"data/geo-burundi-2022-multiday-independent-event-evidence.json"
OUTPUT=ROOT/"data/geo-burundi-2022-source-dependency-evidence.json"
REVIEW_DATE="2026-11-19"
EXPECTED_GED=442626
EXPECTED_GWNO=516
EXPECTED_BEST=10
REQUIRED_BURUNDI_GROUPS=("sos_reporting","ngo_text_overlap","icg_digest_unresolved")

# Structured summaries only: the website and PDF texts are copyrighted.
# This is an editorial reading snapshot, not preserved raw-page evidence.
# Citation URLs and page/section locators permit independent human review.
SOURCES=(
    {
        "id":"sos_20220621",
        "publisher":"SOS Médias Burundi",
        "url":"https://www.sosmediasburundi.org/2022/06/21/cibitoke-une-dizaine-de-morts-et-plusieurs-blesses-decouverts-a-la-kibira/",
        "document_type":"contemporaneous_journalism",
        "publication_date":"2022-06-21",
        "date_precision":"day",
        "reporting_stream":"sos_reporting",
        "claims_direct_local_or_military_contacts":True,
        "named_independently_verifiable_event_witnesses_n":0,
        "reference_locator":"article body, paragraphs on clashes, casualties, and military source",
        "event":"burundi_kibira_mabayi_2022",
        "claims":["burundi_mabayi_kibira","rutorero_gafumbegeti",
                  "casualties_10_deaths","casualties_8_injured",
                  "fighters_kinyarwanda_speaking",
                  "FLN_identity_reported_unverified",
                  "RDF_perpetrator_speculated_not_proven",
                  "three_days_of_fighting_reported"],
        "own_publication_before_2022_06_21_verified":False,
        "limitations":"Anonymous residents and military source: no independently identified victims or RDF attribution.",
    },
    {
        "id":"iteka_q2_2022",
        "publisher":"Ligue Iteka",
        "url":"https://ligue-iteka.bi/wp-content/uploads/2022/07/PERS-TUEES-PAR-DES-GENS-NON-IDENTIFIES-TRIM-2-2022.pdf",
        "document_type":"ngo_quarterly_compilation",
        "publication_date":"2022-07",
        "date_precision":"month_unverified_release_day",
        "reporting_stream":"ngo_text_overlap",
        "claims_direct_local_or_military_contacts":True,
        "named_independently_verifiable_event_witnesses_n":0,
        "reference_locator":"Mabayi section, PDF extracted text near lines 411-420",
        "event":"burundi_kibira_mabayi_2022",
        "claims":["burundi_mabayi_kibira","rutorero_gafumbegeti",
                  "casualties_10_deaths","casualties_8_injured",
                  "bodies_observed_june_19_reported",
                  "information_received_june_20_claimed",
                  "congolese_army_uniforms_reported",
                  "injured_transported_bujumbura_reported",
                  "bodies_buried_imbonerakure_reported",
                  "fighters_kinyarwanda_speaking"],
        "own_publication_before_2022_06_21_verified":False,
        "limitations":"States information reached Ligue Iteka on 20 June, but the July compilation is NOT independently authenticated as published on 20 June.",
    },
    {
        "id":"aprodh_june2022",
        "publisher":"APRODH",
        "url":"https://www.aprodhasbl.org/wp-content/uploads/2022/07/Rapport-Mensuel-Juin-2022.pdf",
        "document_type":"ngo_monthly_compilation",
        "publication_date":"2022-07",
        "date_precision":"month_unverified_release_day",
        "reporting_stream":"ngo_text_overlap",
        "claims_direct_local_or_military_contacts":False,
        "named_independently_verifiable_event_witnesses_n":0,
        "reference_locator":"monthly June 2022 PDF page 12, item 16; visually inspected",
        "event":"burundi_kibira_mabayi_2022",
        "claims":["burundi_mabayi_kibira","rutorero_gafumbegeti",
                  "casualties_10_deaths","casualties_8_injured",
                  "bodies_observed_june_19_reported",
                  "congolese_army_uniforms_reported",
                  "injured_transported_bujumbura_reported",
                  "bodies_buried_imbonerakure_reported",
                  "fighters_kinyarwanda_speaking"],
        "own_publication_before_2022_06_21_verified":False,
        "limitations":"Near-verbatim overlap with Ligue Iteka; no independently named witnesses; copying direction not established.",
    },
    {
        "id":"hitamwoneza_20220622",
        "publisher":"HITAMWONEZA",
        "url":"https://hitamwukuri.org/burundi-que-ferrait-le-pouvoir-cnddfdd-des-cadavres-et-blesses-fln-ramasses-dans-cibitoke/",
        "document_type":"commentary_explicitly_citing_reporting",
        "publication_date":"2022-06-22",
        "date_precision":"day",
        "reporting_stream":"sos_reporting",
        "claims_direct_local_or_military_contacts":False,
        "named_independently_verifiable_event_witnesses_n":0,
        "reference_locator":"article paragraphs 14-18, direct attribution to SOS Médias",
        "event":"burundi_kibira_mabayi_2022",
        "claims":["burundi_mabayi_kibira","rutorero_gafumbegeti",
                  "casualties_10_deaths","casualties_8_injured",
                  "fighters_kinyarwanda_speaking",
                  "FLN_identity_reported_unverified",
                  "RDF_perpetrator_speculated_not_proven",
                  "event_dates_june_18_20_alternate",
                  "rwanda_bus_causal_link_proposed_not_demonstrated"],
        "own_publication_before_2022_06_21_verified":False,
        "limitations":"Explicitly attributes military testimony to SOS; dates 18-20 conflict with GED 19-21; proposed chase after Rwanda bus attack unverified.",
    },
    {
        "id":"icg_crisiswatch_june2022",
        "publisher":"International Crisis Group",
        "url":"https://crisisgroup-staging-3.sbx.so/crisiswatch/july-alerts-and-june-trends-2022",
        "document_type":"secondary_monthly_conflict_digest",
        "publication_date":"2022-07",
        "date_precision":"month",
        "reporting_stream":"icg_digest_unresolved",
        "claims_direct_local_or_military_contacts":False,
        "named_independently_verifiable_event_witnesses_n":0,
        "reference_locator":"CrisisWatch Burundi / June 2022 paragraph",
        "event":"burundi_kibira_mabayi_2022",
        "claims":["burundi_mabayi_kibira","casualties_10_deaths",
                  "casualties_8_injured","event_dates_june_19_21_reported",
                  "FLN_identity_reported_unverified",
                  "RDF_perpetrator_speculated_not_proven"],
        "own_publication_before_2022_06_21_verified":False,
        "limitations":"No separately named witness or source in the excerpt; could repeat upstream reporting rather than independently count casualties.",
    },
    {
        "id":"rwanda_bus_reuters_20220620",
        "publisher":"Reuters, as published by Citizen Digital",
        "url":"https://citizen.digital/article/suspected-militants-shoot-at-bus-in-southwestern-rwanda-kill-two-n300483",
        "document_type":"press_account_of_rwandan_police_statement",
        "publication_date":"2022-06-20",
        "date_precision":"day",
        "reporting_stream":"separate_rwanda_bus_police_statement",
        "claims_direct_local_or_military_contacts":False,
        "named_independently_verifiable_event_witnesses_n":0,
        "reference_locator":"Reuters report of Rwanda police statement, 18 June bus attack",
        "event":"rwanda_bus_nyamagabe_2022_06_18",
        "claims":["rwanda_bus_attack_june_18_police_report",
                  "rwanda_bus_two_killed_police_report",
                  "rwanda_bus_six_injured_police_report",
                  "suspected_FLN_perpetrator_police_attribution_only"],
        "own_publication_before_2022_06_21_verified":True,
        "limitations":"The bus attack took place in RWANDA, not the Mabayi GED incident. The police attribution does not prove a cross-border chase or 10 deaths in Burundi.",
    },
)

EDGES=(
    {
        "from":"hitamwoneza_20220622",
        "to":"sos_20220621",
        "kind":"explicit_editorial_attribution",
        "direction_established":True,
        "basis":"HITAMWONEZA directly attributes military-source information to SOS Médias Burundi",
        "count_as_independent_confirmation":False,
    },
    {
        "from":"aprodh_june2022",
        "to":"iteka_q2_2022",
        "kind":"near_verbatim_same_report_unresolved_direction",
        "direction_established":False,
        "basis":"Manually compared NGO passages: same ten bodies, eight injured, Congolese uniforms, hill names, transfer and burial details, parallel phrasing",
        "count_as_independent_confirmation":False,
    },
    {
        "from":"icg_crisiswatch_june2022",
        "to":"sos_20220621",
        "kind":"potential_upstream_overlap_unverified",
        "direction_established":False,
        "basis":"Later summary gives same ten/eight, site and suspected actors but visible excerpt does not document distinct witnesses",
        "count_as_independent_confirmation":False,
    },
    {
        "from":"hitamwoneza_20220622",
        "to":"rwanda_bus_reuters_20220620",
        "kind":"proposed_temporal_context_not_proven_event_identity",
        "direction_established":False,
        "basis":"HITAMWONEZA hypothesizes connection to 18 June Rwanda bus attack; Reuters independently reports Rwanda bus from police statement, not Burundi reprisal",
        "count_as_independent_confirmation":False,
    },
)

KNOWN_UNRESOLVED=(
    "Whether SOS and Ligue Iteka interviewed different local witnesses or share one original informant is unverified.",
    "Whether International Crisis Group independently corroborated the Burundi casualty count is unknown.",
    "The direction of near-verbatim copying or information sharing between APRODH and Ligue Iteka cannot be determined from the published PDFs.",
    "No independent roster of ten identified deceased persons, burial register, clinical record, or forensic confirmation has been located in the reviewed material.",
    "A separately reported 18 June 2022 attack on a bus in RWANDA is documented, but its causal link to the Burundi 19-21 June deaths is NOT established.",
)

def source_date_eligible(src):
    value=src["publication_date"]
    precision=src["date_precision"]
    if precision=="day":
        date.fromisoformat(value)
    elif precision.startswith("month"):
        date.fromisoformat(value+"-01")
    else:
        raise ValueError("Unsupported publication date precision")
    if src["event"] not in (
        "burundi_kibira_mabayi_2022","rwanda_bus_nyamagabe_2022_06_18"):
        raise ValueError("Unregistered source event domain")
    host=(__import__("urllib.parse",fromlist=["urlsplit"]).urlsplit(
        src["url"]).hostname or "").lower()
    if host not in {"www.sosmediasburundi.org","ligue-iteka.bi",
                    "www.aprodhasbl.org","hitamwukuri.org",
                    "crisisgroup-staging-3.sbx.so","citizen.digital"}:
        raise ValueError("Source URL outside documentary host allowlist")
    if len(src["claims"])!=len(set(src["claims"])):
        raise ValueError("Duplicated source statement")
    if src["named_independently_verifiable_event_witnesses_n"]!=0:
        raise ValueError("Unsupported witnessed identity claim")
    if src["event"].startswith("rwanda_") and src["reporting_stream"] in REQUIRED_BURUNDI_GROUPS:
        raise ValueError("Rwanda bus victims wrongly merged into Burundi casualty reports")
    if src["event"].startswith("burundi_") and "rwanda_bus_two_killed_police_report" in src["claims"]:
        raise ValueError("Rwanda deaths must never be counted in Burundi")
    return True


def validate_anchor(prior):
    if (prior.get("schema")!="idealab.psico.geo_burundi_2022_statebased_multiday_external_evidence.v1"
        or prior.get("original_GEO2027_SHA256")!=SOURCE_SHA256
        or prior.get("two_original_GEO2027_GEO2028_issues_unchanged") is not True
        or prior.get("GED_record",{}).get("GED_event_id")!=EXPECTED_GED
        or prior["GED_record"].get("GWNO")!=EXPECTED_GWNO
        or prior["GED_record"].get("GED_type_of_violence")!=1
        or prior["GED_record"].get("best_fatalities_estimate")!=EXPECTED_BEST
        or prior["GED_record"].get("event_start")!="2022-06-19"
        or prior["GED_record"].get("event_end")!="2022-06-21"
        or prior["GDELT_news_events"]["same_2022_06_19_to_21_event_date"]["within_100km_n"]!=0):
        raise ValueError("Already published June 2022 Burundi GED/GDELT anchor changed")


def build_report(prior):
    validate_anchor(prior)
    nodes={src["id"]:src for src in SOURCES}
    if len(nodes)!=len(SOURCES):
        raise ValueError("Duplicate source ID")
    for src in SOURCES:
        source_date_eligible(src)
    if len({src["url"] for src in SOURCES})!=len(SOURCES):
        raise ValueError("Duplicate original source URL")
    for edge in EDGES:
        if (edge["from"] not in nodes or edge["to"] not in nodes
            or edge["from"]==edge["to"]
            or edge["count_as_independent_confirmation"] is not False):
            raise ValueError("Invalid dependency assertion")
        if edge["kind"]=="explicit_editorial_attribution" and not edge["direction_established"]:
            raise ValueError("Explicit attribution direction must be established")
        if edge["kind"]=="near_verbatim_same_report_unresolved_direction" and edge["direction_established"]:
            raise ValueError("Textual overlap does not establish copying direction")
    burundi=[x for x in SOURCES if x["event"]=="burundi_kibira_mabayi_2022"]
    if (len(burundi)!=5 or len(SOURCES)!=6 or
        {s["reporting_stream"] for s in burundi}!=set(REQUIRED_BURUNDI_GROUPS)):
        raise ValueError("Wrong number/type of Burundi source genealogy records")
    all_claims=sorted(set(x for src in SOURCES for x in src["claims"]))
    support={claim:sorted(src["id"] for src in SOURCES if claim in src["claims"])
             for claim in all_claims}
    if len(support["casualties_10_deaths"])!=5 or len(support["casualties_8_injured"])!=5:
        raise ValueError("Reported 10/8 death and injury assertion not reproduced")
    # Semantic overlap flags, not an assertion of textual copyright or a
    # statistical independence test. Reviewed excerpts corroborate the labels.
    pairs=[]
    for lhs,rhs in (("iteka_q2_2022","aprodh_june2022"),
                    ("sos_20220621","iteka_q2_2022"),
                    ("sos_20220621","icg_crisiswatch_june2022")):
        a=set(nodes[lhs]["claims"])
        b=set(nodes[rhs]["claims"])
        pairs.append({
            "left":lhs,"right":rhs,
            "shared_claim_id_n":len(a&b),
            "claim_jaccard":len(a&b)/len(a|b),
            "overlap_claims":sorted(a&b),
            "this_is_not_a_textual_source_independence_probability":True,
        })
    deltas=[
        {"source":"hitamwoneza_20220622",
         "source_claimed_dates":["2022-06-18","2022-06-20"],
         "GED_interval":["2022-06-19","2022-06-21"],
         "kind":"one_day_shift_in_reported_fighting_window",
         "effect_on_ten_deaths_truth":"not_determined"},
        {"source":"iteka_q2_2022",
         "source_reported_body_discovery_date":"2022-06-19",
         "claimed_information_received_date":"2022-06-20",
         "document_archival_month":"2022-07",
         "source_was_public_by_received_date_verified":False,
         "kind":"received_date_is_not_publication_date"},
    ]
    snapshot=json.dumps({
        "sources":SOURCES,"edges":EDGES,"claim_support":support,
    },sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return {
        "schema":"idealab.psico.geo_burundi_2022_documentary_source_genealogy.v1",
        "status":"DOCUMENTARY_GENEALOGY_NOT_INDEPENDENT_CASUALTY_VERIFICATION",
        "review_date":REVIEW_DATE,
        "anchor_report_path":str(PREVIOUS.relative_to(ROOT)),
        "original_GEO2027_SHA256":SOURCE_SHA256,
        "prior_GED_event_id":EXPECTED_GED,
        "prior_GED_best_deaths":EXPECTED_BEST,
        "prior_GDELT_no_local_100km_footprint":True,
        "source_snapshot_sha256_not_remote_page_byte_hash":hashlib.sha256(snapshot).hexdigest(),
        "raw_web_pages_or_pdf_bytes_snapshotted":False,
        "source_url_and_claim_manual_review_required":True,
        "sources":[dict(s) for s in SOURCES],
        "dependency_edges":[dict(x) for x in EDGES],
        "source_claim_support":support,
        "semantic_claim_overlap_diagnostic_not_independence":pairs,
        "reported_temporal_discrepancies":deltas,
        "burundi_reporting_publishers_n":len(burundi),
        "burundi_provisional_editorial_reporting_groups_n":len(REQUIRED_BURUNDI_GROUPS),
        "verified_independent_named_victim_lists_n":0,
        "verified_disjoint_firsthand_witness_sets_n":0,
        "editorial_groups_proven_statistically_independent":False,
        "explicit_derivative_outlets_n":1,
        "other_NGO_pair_with_near_verbatim_case_text_n":1,
        "secondary_ICG_upstream_provenance_resolved":False,
        "rwanda_bus_event_is_separate_from_burundi_ged_event":True,
        "ten_burundi_deaths_confirmed_by_independent_forensic_source":False,
        "Rwandan_force_involvement_proven":False,
        "unresolved_source_dependencies":list(KNOWN_UNRESOLVED),
        "original_GEO2027_GEO2028_not_modified":True,
        "methodology":"Curated citation and claim ledger; exact manual editorial checks of NGO PDF passages plus contemporary HTML; dependent outlets are grouped for cautious interpretation. Structural CI checks verify frozen logical claims and previously published GEO source anchors, but do NOT attest live availability or original PDF-byte integrity. Semantically identical reporting can reflect shared origin, so no casualty verification or source-independence probability is inferred.",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-report",action="store_true")
    parser.add_argument("--print-report",action="store_true")
    args=parser.parse_args()
    if hashlib.sha256(FORECAST_PATH.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError("GEO2027 original issued vector changed")
    audit_issued(ISSUE.read_bytes(),MANIFEST.read_bytes(),ORIGINAL.read_bytes(),
                 OLD_SHADOW.read_bytes(),OLD_MANIFEST.read_bytes(),ALERTS.read_bytes())
    prior=json.loads(PREVIOUS.read_text(encoding="utf-8"))
    report=build_report(prior)
    if args.check_report:
        actual=json.loads(OUTPUT.read_text(encoding="utf-8"))
        if report!=actual:
            raise ValueError("Frozen reviewed source-dependency report changed")
    if args.print_report:
        print("BURUNDI_SOURCE_CHAIN_BEGIN",flush=True)
        print(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2))
        print("BURUNDI_SOURCE_CHAIN_END",flush=True)
    else:
        print(json.dumps({
            "source_publishers":report["burundi_reporting_publishers_n"],
            "editorial_groups":report["burundi_provisional_editorial_reporting_groups_n"],
            "verified_independent_victim_lists":
                report["verified_independent_named_victim_lists_n"],
            "explicit_derivative_outlets":report["explicit_derivative_outlets_n"],
            "near_verbatim_NGO_pairs":report["other_NGO_pair_with_near_verbatim_case_text_n"],
        },sort_keys=True))


if __name__=="__main__":
    main()
