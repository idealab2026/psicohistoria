#!/usr/bin/env python3
"""Public 2027 prospective predictions: one row per issued COUNTRY x ENDPOINT.

Original GEO 196, NEWCONF 196, ACD active-origin 32 = 424 independent
country-question records, NOT 424 independent observations or 424 skill tests.
The GEO 15 alerts are subsets of GEO, and GEO shadow is a companion model,
not fourth/fifth independent cohorts. Never modify first-issued probabilities.
Read ONLY already public, SHA-pinned IDEA LAB issue documents and manifests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/prospective-2027-registry.json"
META=ROOT/"data/prospective-2027-registry-manifest.json"
COHORTS=("GEO2027","NEWCONF2027","ACD2027")
EXPECTED={
 "geo":("data/forecast-2027-ucdp261.json",
        "5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5",
        "3bb3561c8d6182c30624591276c705fb76ce99dc"),
 "newconf":("data/forecast-2027-newconf.json",
        "e4482da7396872645d5101115435143d98fd9fdb1db1b1fdf41a42c99fc04b74",
        "f3f2c17c9d4f5dd56266e376cd2d765f33f3dd97"),
 "acd":("data/forecast-2027-acd-retention.json",
        "6cf7d0340a4c25062af7a040586fb6a73a98c9e6ab80473527171c0a5a963d9c",
        "41db7bd154e0140ced15abd8727a7d52d998852c"),
 "shadow":("data/forecast-2027-geo-shadow.json",
        "1d0880f6e95e77d5e203b186e45a035676c7f724ecbe6a8b323f776b9eaa9188",
        "ed3e764a191b24bc2a01f4d877b115db2e247a20"),
 "alerts":("data/forecast-2027-transition-alerts.json",
        "309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb",
        "5938db3c93661ce04ed35902b2bdaa68abfb8daa"),
}
META_FILES={
 "geo":"data/forecast-2027-manifest.json",
 "newconf":"data/forecast-2027-newconf-manifest.json",
 "acd":"data/forecast-2027-acd-retention-manifest.json",
 "shadow":"data/forecast-2027-geo-shadow-manifest.json",
 "alerts":"data/forecast-2027-transition-alerts-manifest.json",
}


def canonical(data):
    return (json.dumps(data,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf8")


def read_issued(root=ROOT):
    docs={};manifests={}
    for name,(path,digest,commit) in EXPECTED.items():
        raw=(root/path).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=digest:
            raise ValueError("Issued "+name+" SHA-256 does not match immutable first-public issue")
        docs[name]=json.loads(raw)
        manifests[name]=json.loads((root/META_FILES[name]).read_text(encoding="utf8"))
    g,n,a,s,al=(manifests[k] for k in ("geo","newconf","acd","shadow","alerts"))
    if (g["forecast_sha256"]!=EXPECTED["geo"][1]
        or g["first_public_forecast_commit"]!=EXPECTED["geo"][2]
        or g["first_public_forecast_commit_utc"]!="2026-11-10T17:23:12Z"
        or n["forecast_sha256"]!=EXPECTED["newconf"][1]
        or n["first_public_forecast_commit"]!=EXPECTED["newconf"][2]
        or n["first_public_forecast_commit_utc"]!="2026-11-11T10:10:21Z"
        or a["issue_forecast_sha256"]!=EXPECTED["acd"][1]
        or a["first_public_git_commit"]!=EXPECTED["acd"][2]
        or a["first_public_git_commit_utc"]!="2026-11-12T22:24:56Z"
        or s["shadow_forecast_sha256"]!=EXPECTED["shadow"][1]
        or s["first_public_shadow_commit"]!=EXPECTED["shadow"][2]
        or al["issue_sha256"]!=EXPECTED["alerts"][1]
        or al["first_public_issue_commit"]!=EXPECTED["alerts"][2]):
        raise ValueError("Original 2026 first-public issue chain changed")
    for name,m in manifests.items():
        if (name=="acd" and m["2027_outcomes_resolved"]!=0 or
            name=="shadow" and m["2027_outcomes_resolved"]!=0 or
            name=="alerts" and m["outcomes_resolved"]!=0 or
            name=="geo" and m["outcomes_resolved"]!=0 or
            name=="newconf" and m["outcomes_resolved"]!=0):
            raise ValueError("2027 was unexpectedly resolved in an original issue")
    return docs,manifests


def probability(p):
    if type(p) not in (float,int) or not math.isfinite(p) or not 0<p<1:
        raise ValueError("Invalid first-issued probability")
    return p


def make_registry(docs,manifests):
    geo,newconf,acd,shadow,alerts=(docs[k] for k in ("geo","newconf","acd","shadow","alerts"))
    if (geo.get("forecast_id")!="PSICO-GEO2027-STATEBASED25-V1"
        or newconf.get("forecast_id")!="PSICO-QGEO01-NEWCONF2027-ORIGIN2025-V1"
        or acd.get("forecast_id")!="PSICO-ACD2027-INTRASTATE-T2-PERSISTENCE-V1"
        or len(geo.get("countries",[]))!=196
        or len(newconf.get("countries",[]))!=196
        or len(acd.get("countries",[]))!=32
        or len(shadow.get("countries",[]))!=196
        or geo["target"]["year"]!=2027
        or newconf["target"]["year"]!=2027
        or acd["target_year"]!=2027
        or acd["2027_outcomes_resolved"]!=0
        or newconf["source"]["newconf_2027_outcome_observed"] is not False
        or shadow["2027_outcomes_resolved"]!=0
        or alerts["2027_outcomes_resolved"]!=0):
        raise ValueError("Issued 2027 cohort identity, targets, or unresolved status changed")
    names={}
    for x in geo["countries"]:
        cid=x["country_id"]
        if (type(cid) is not int or cid in names or not isinstance(x["country"],str)
            or len(x["country"].strip())<2):
            raise ValueError("Country ID/name crosswalk corrupt")
        names[cid]=x["country"]
    if len(names)!=196:
        raise ValueError("Missing original named GEO country records")
    shadow_by_id={}
    for x in shadow["countries"]:
        cid=x["country_id"]
        if cid in shadow_by_id or cid not in names:
            raise ValueError("Shadow country ID changed")
        shadow_by_id[cid]=x
    if set(shadow_by_id)!=set(names):
        raise ValueError("Shadow 196-country coverage incomplete")
    alerts_by_id={}
    for st,g in alerts["risk_groups"].items():
        if st not in ("0","1") or len(g["selected_countries"])!=(10 if st=="0" else 5):
            raise ValueError("Original GEO alert budget changed")
        for x in g["selected_countries"]:
            cid=x["country_id"]
            if cid in alerts_by_id or cid not in names:
                raise ValueError("Invalid or duplicated originally selected GEO alert")
            alerts_by_id[cid]="ENTRADA" if st=="0" else "RESOLUCION"
    if len(alerts_by_id)!=15:
        raise ValueError("Original exactly 15 GEO alerts missing")
    summaries={
      "GEO2027":{
        "question":"¿Se superará el umbral de 25 muertes anuales de violencia organizada estatal en 2027?",
        "source":"UCDP OrganizedViolenceCY 26.1",
        "source_url":geo["source"]["url"],
        "source_sha256":geo["source"]["sha256"],
        "primary_model":"p_model",
        "issue_utc":manifests["geo"]["first_public_forecast_commit_utc"],
        "first_public_commit":EXPECTED["geo"][2],
        "forecast_sha256":EXPECTED["geo"][1],
        "fixed_country_count":196,
        "origin_data_through":2025,
        "resolution":"PENDIENTE_FUENTE_ANUAL_OFICIAL_2027",
        "evaluation":"Brier del modelo principal sobre las 196 etiquetas completas del primer corte anual oficial.",
      },
      "NEWCONF2027":{
        "question":"¿Se registrará al menos un nuevo episodio de conflicto intraestatal (newconf) en 2027?",
        "source":"UCDP Intrastate Country Level Multiple Onset 25.1 + ACD 26.1",
        "source_url":newconf["source"]["multiple_onset_training_url"],
        "source_sha256":newconf["source"]["multiple_onset_training_sha256"],
        "primary_model":"p_model",
        "issue_utc":manifests["newconf"]["first_public_forecast_commit_utc"],
        "first_public_commit":EXPECTED["newconf"][2],
        "forecast_sha256":EXPECTED["newconf"][1],
        "fixed_country_count":196,
        "origin_data_through":2025,
        "resolution":"PENDIENTE_FUENTE_ANUAL_OFICIAL_2027",
        "evaluation":"Brier sobre los 196 países originales con ANY(newconf=1) por país; sin ceros imputados.",
      },
      "ACD2027":{
        "question":"¿Seguirá registrándose algún conflicto intraestatal ACD tipo 3/4 en 2027 entre países activos en 2025?",
        "source":"UCDP/PRIO Armed Conflict Dataset 26.1",
        "source_url":acd["source_official_url"],
        "source_sha256":acd["source_zip_sha256"],
        "primary_model":"p_global_recent5",
        "issue_utc":manifests["acd"]["first_public_git_commit_utc"],
        "first_public_commit":EXPECTED["acd"][2],
        "forecast_sha256":EXPECTED["acd"][1],
        "fixed_country_count":32,
        "origin_data_through":2025,
        "resolution":"PENDIENTE_FUENTE_ANUAL_OFICIAL_2027",
        "evaluation":"Brier primario de persistencia ACD en los 32 países de origen 2025.",
      }
    }
    rows=[]; seen=set()
    def put(cohort,cid,primary,secondary,alert=None):
        if type(cid) is not int or cid not in names:
            raise ValueError("Unknown institutional GWNO country code")
        key=(cohort,cid)
        if key in seen:
            raise ValueError("Duplicate prospective country-question issue")
        seen.add(key)
        rows.append({
            "cohort":cohort,"country_id":cid,"country":names[cid],
            "p_primary":probability(primary),
            "p_secondary":{k:probability(v) for k,v in secondary.items()},
            "issued_status":"EMITIDA_PENDIENTE",
            "resolved_2027":False,
            "observed_2027":None,
            "certified_result":False,
            "geo_transition_alert":alert,
        })
    for x in geo["countries"]:
        cid=x["country_id"]
        sh=shadow_by_id[cid]
        if (x["p_model"]!=sh["original_issued_p_active_2027"]
            or x["last_observed_state_2025"]!=sh["origin_state_2025"]):
            raise ValueError("GEO shadow is not paired with issued main model")
        if cid in alerts_by_id:
            expected_type="ENTRADA" if x["last_observed_state_2025"]==0 else "RESOLUCION"
            if alerts_by_id[cid]!=expected_type:
                raise ValueError("GEO original 15 alerts origin-state mismatch")
        put("GEO2027",cid,x["p_model"],{
            "p_global_markov":x["p_global_markov"],
            "p_shadow_exploratorio":sh["shadow_p_active_2027"],
        },alerts_by_id.get(cid))
    for x in newconf["countries"]:
        cid_text=x["country_id"]
        if not isinstance(cid_text,str) or not cid_text.isdecimal():
            raise ValueError("NEWCONF GWNO ID is not numeric string")
        put("NEWCONF2027",int(cid_text),x["p_model"],{
            "p_baseline_global_5y":x["p_baseline_global_5y"],
        })
    for x in acd["countries"]:
        if x["conflict_present_in_origin_2025"] is not True:
            raise ValueError("ACD original cohort wrongly includes inactive 2025 country")
        put("ACD2027",x["country_id"],x["p_global_recent5"],{
            "p_country_eb_exploratorio":x["p_country_eb"],
            "p_lag1_group_exploratorio":x["p_lag1_group"],
        })
    total=sum(d["fixed_country_count"] for d in summaries.values())
    if len(rows)!=424 or len(seen)!=424 or total!=424:
        raise ValueError("Total first-issued 2027 country-endpoint records changed")
    if sum(x["geo_transition_alert"] is not None for x in rows)!=15:
        raise ValueError("Original GEO transition alert subset changed")
    for name,detail in summaries.items():
        count=sum(r["cohort"]==name for r in rows)
        if count!=detail["fixed_country_count"]:
            raise ValueError("Cohort count changed")
    rows.sort(key=lambda x:(COHORTS.index(x["cohort"]),x["country_id"]))
    return {
        "schema":"idealab.psico.prospective_2027_issued_registry.v1",
        "status":"PROSPECTIVE_ISSUED_ALL_OUTCOMES_2027_UNRESOLVED",
        "target_year":2027,
        "cohort_order":list(COHORTS),
        "n_distinct_issued_endpoints":3,
        "n_unique_country_endpoint_rows":424,
        "n_verified_future_2027_outcomes":0,
        "n_original_geo_transition_alerts_subset":15,
        "n_original_geo_shadow_comparator_countries":196,
        "observational_skill_demonstrated":False,
        "first_commit_times_are_public_metadata_not_independent_notarization":True,
        "independent_country_endpoints_or_country_years":False,
        "possible_cross_cohort_overlap":True,
        "cohorts":summaries,
        "rows":rows,
        "interpretation":"Three genuinely distinct 2027 binary targets: GEO state-based >=25 death threshold, NEWCONF intrastate multiple-onset, ACD intrastate conflict persistence. A GEO selected alert is NOT an additional event forecast. Shadow/EB models are comparators, not new country-question rows. 424 records share country-years; no 2027 labels observed or prospective skill certified.",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check-report",action="store_true")
    args=ap.parse_args()
    docs,m=read_issued()
    doc=make_registry(docs,m)
    body=canonical(doc)
    sha=hashlib.sha256(body).hexdigest()
    print("PROSPECTIVE_2027_REGISTRY_SHA256",sha)
    print("PROSPECTIVE_2027_REGISTRY_COUNTS",len(doc["rows"]),len(doc["cohorts"]))
    print("PROSPECTIVE_2027_REGISTRY_JSON_BEGIN")
    print(body.decode(),end="")
    print("PROSPECTIVE_2027_REGISTRY_JSON_END")
    if args.check_report:
        if OUT.read_bytes()!=body:
            raise ValueError("Frozen three-cohort prospective registry altered or out of sync")
        manifest=json.loads(META.read_text(encoding="utf8"))
        expected_sha={c:EXPECTED[k][1] for c,k in zip(COHORTS,("geo","newconf","acd"))}
        expected_commits={c:EXPECTED[k][2] for c,k in zip(COHORTS,("geo","newconf","acd"))}
        if (manifest.get("schema")!="idealab.psico.prospective_2027_registry_attestation.v1"
            or manifest.get("status")!="DERIVED_FROM_ALREADY_ISSUED_2027_COHORTS_NO_NEW_FORECAST"
            or manifest.get("registry_sha256")!=sha
            or manifest.get("n_country_endpoint_rows")!=424
            or manifest.get("n_cohorts")!=3
            or manifest.get("n_2027_outcomes_resolved")!=0
            or manifest.get("n_geo_alerts_subset_not_additional")!=15
            or manifest.get("n_unique_countries")!=196
            or manifest.get("original_forecast_sha256")!=expected_sha
            or manifest.get("first_public_commits")!=expected_commits
            or manifest.get("sha_issued_shadow")!=EXPECTED["shadow"][1]
            or manifest.get("sha_issued_geo_15_alerts")!=EXPECTED["alerts"][1]
            or manifest.get("not_issued_on_registry_creation") is not True
            or manifest.get("forecast_skill_certified") is not False):
            raise ValueError("Derived 2027 registry SHA/first-public issue attestation altered")


if __name__=="__main__":
    main()
