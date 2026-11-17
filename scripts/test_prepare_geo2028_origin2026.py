"""Source-vintage-safe first NEW-origin prospective GEO2028 contract. Synthetic only."""
import copy
from datetime import date
import hashlib
import io
import unittest
from zipfile import ZIP_DEFLATED,ZipFile

import forecast_2027_statebased as original2027
import prepare_geo2028_origin2026 as future
from test_forecast_2027_statebased import toy


def origin_2025_issue():
    r,n=toy()
    old,old_summary=original2027.estimate_from_history(r,n)
    issued={
        "forecast_id":"PSICO-GEO2028-STATEBASED25-H3-ORIGIN2025-V1",
        "origin":{"year":2025},
        "target":{"year":2028},
        "protocol":{"horizon_years":3},
        "2028_outcomes_resolved":0,
        "countries":[{
            "country_id":item["country_id"],
            "country":item["country"],
            "last_observed_state_2025":item["last_observed_state_2025"],
        } for item in old],
    }
    return r,n,issued,old,old_summary


def new_origin_data():
    r,n,_,_,_=origin_2025_issue()
    for cid,h in r.items():
        h[2026]=int((cid%17==0 or cid%9==0) and cid%5!=0)
    return r,n


def csv_rows(records,names):
    lines=["country_id,country,year,sb_total_deaths_best"]
    for cid,h in sorted(records.items()):
        for year,y in sorted(h.items()):
            lines.append(f"{cid},{names[cid]},{year},{25 if y else 0}")
    return "\n".join(lines)+"\n"


def archive(csv_text,extra=None):
    fd=io.BytesIO()
    with ZipFile(fd,"w",compression=ZIP_DEFLATED) as z:
        z.writestr("organizedviolencecy.csv",csv_text)
        if extra is not None:
            z.writestr("unexpected.csv",extra)
    return fd.getvalue()


def pin(raw):
    return {
        "schema":future.PIN_SCHEMA,
        "dataset":"UCDP OrganizedViolenceCY",
        "version":"27.1",
        "last_observed_year":2026,
        "pin_status":"SOURCE_CANDIDATE_UNCERTIFIED",
        "first_release_independently_attested":False,
        "official_url":future.URL,
        "official_zip_sha256":hashlib.sha256(raw).hexdigest(),
        "publication_date_claimed":"2027-07-01",
    }


class FutureOrigin2026Safety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records,cls.names=new_origin_data()
        cls.raw=archive(csv_rows(cls.records,cls.names))
        cls.pin=pin(cls.raw)
        cls.issued=origin_2025_issue()[2]
        cls.as_of=date(2027,8,1)

    def test_original_2025_two_step_model_regression_is_exact(self):
        records,names,_,rows,reference=origin_2025_issue()
        replicated,stats=future.estimate_from_origin(records,names,origin=2025)
        self.assertEqual(replicated,rows)
        for key in ("cohort_n","global_transition_counts",
                    "global_transition_p_active","global_5y_exposures",
                    "global_5y_positive","baseline_global_5y"):
            self.assertEqual(stats[key],reference[key],key)
        self.assertEqual(stats["recent_years"],[2021,2022,2023,2024,2025])

    def test_future_source_2026_real_explicit_gwno_all_196_probs_are_candidate_only(self):
        r,n,facts=future.parse_annual_2026_csv(csv_rows(self.records,self.names))
        self.assertEqual(facts["eligible_2025_2026_country_count"],196)
        self.assertEqual(facts["max_source_year"],2026)
        self.assertEqual(facts["source_country_year_rows"],196*38)
        d=future.build_candidate(self.raw,self.pin,self.issued,as_of=self.as_of)
        self.assertTrue(future.validate_candidate(d))
        self.assertEqual(d["n_candidate_country_probabilities"],196)
        self.assertEqual(d["n_issued_country_questions"],0)
        self.assertEqual(d["origin_year"],2026)
        self.assertEqual(d["target_year"],2028)
        self.assertEqual(d["horizon_years"],2)
        self.assertEqual(d["model_fit"]["recent_years"],[2022,2023,2024,2025,2026])
        self.assertEqual(d["country_universe_comparison_to_original_2025_origin"]["common_gwno"],196)
        self.assertEqual(d["country_universe_comparison_to_original_2025_origin"]["revised_2025_annual_state_n"],0)
        self.assertFalse(d["statistically_independent_of_origin2025_GEO2028"])
        self.assertTrue(d["no_first_public_forecast_commit_yet"])
        self.assertFalse(d["independently_attested_source_release"])
        self.assertTrue(d["no_2028_outcomes_observed"])
        self.assertFalse(d["source_provenance"]["first_release_independently_verified"])
        self.assertEqual([x["country_id"] for x in d["countries"]],list(range(1,197)))
        self.assertTrue(all(0<x[k]<1 for x in d["countries"]
                            for k in ("p_model","p_global_markov",
                                      "p_baseline_global_5y")))
        self.assertEqual(future.canonical(d),future.canonical(
            future.build_candidate(self.raw,self.pin,self.issued,as_of=self.as_of)))
        self.assertEqual(future.canonical(d)[-1:],b"\n")

    def test_new_country_population_and_revised_2025_vintage_reported(self):
        records,names=new_origin_data()
        del records[1][2026]  # old GWNO no longer eligible
        records[197]={y:0 for y in range(1989,2027)}
        names[197]="Test_Country_197"
        records[2][2025]=1-records[2][2025] # 27.1 revised the old year!
        raw=archive(csv_rows(records,names))
        d=future.build_candidate(raw,pin(raw),self.issued,as_of=self.as_of)
        self.assertTrue(future.validate_candidate(d))
        diff=d["country_universe_comparison_to_original_2025_origin"]
        self.assertEqual(diff["candidate_2026_origin_n"],196)
        self.assertEqual(diff["common_gwno"],195)
        self.assertEqual(diff["new_in_2026_origin"],[197])
        self.assertEqual(diff["not_in_2026_origin"],[1])
        self.assertEqual(diff["revised_2025_annual_state_gwno_in_27_1"],[2])
        self.assertTrue(diff["differences_include_new_2026_data_and_historical_vintage_revisions"])

    def test_cannot_replace_2026_full_annual_edition_with_2025_or_future_records(self):
        for yr in (2027,2028):
            modified=copy.deepcopy(self.records)
            modified[2][yr]=1
            with self.subTest(future_year=yr):
                with self.assertRaisesRegex(ValueError,"Post-origin"):
                    future.parse_annual_2026_csv(csv_rows(modified,self.names))
                # The archive and its pinned SHA must refer to the *same*
                # bytes. Creating two ZIPs can cross the ZIP entry timestamp
                # second, causing a spurious checksum failure BEFORE the
                # intended post-origin parsing/chronology rejection.
                raw_future=archive(csv_rows(modified,self.names))
                with self.assertRaisesRegex(ValueError,"Post-origin"):
                    future.build_candidate(raw_future,pin(raw_future),
                                           self.issued,as_of=self.as_of)
        old=copy.deepcopy(self.records)
        for h in old.values():
            del h[2026]
        with self.assertRaisesRegex(ValueError,"coverage incomplete"):
            future.parse_annual_2026_csv(csv_rows(old,self.names))

    def test_source_27_1_exact_version_checksum_clock_and_notarization_not_forged(self):
        source=future.pin_source_metadata(self.pin,self.raw,as_of=self.as_of)
        self.assertEqual(source["official_zip_sha256"],hashlib.sha256(self.raw).hexdigest())
        for change in (
            ("version","26.1"),
            ("version","28.1"),
            ("last_observed_year",2025),
            ("official_url",future.URL+"?rev=1"),
            ("official_url","https://ucdp.uu.se.evil.test/downloads/organizedviolencecy/organizedviolencecy-271-csv.zip"),
            ("official_url",future.URL.replace("https:","http:")),
            ("first_release_independently_attested",True),
            ("pin_status","ATTESTED_OFFICIAL"),
            ("official_zip_sha256","0"*64),
        ):
            bad=copy.deepcopy(self.pin)
            bad[change[0]]=change[1]
            with self.subTest(change=change):
                with self.assertRaisesRegex(ValueError,"exact original"):
                    future.pin_source_metadata(bad,self.raw,as_of=self.as_of)
        with self.assertRaisesRegex(ValueError,"exact original"):
            future.pin_source_metadata(self.pin,self.raw+b"tamper",as_of=self.as_of)
        for claim,now in (
            ("2026-12-31",date(2027,8,1)),
            ("2027-07-01",date(2026,11,15)),
            ("2028-02-01",date(2028,2,2)),
        ):
            bad=copy.deepcopy(self.pin);bad["publication_date_claimed"]=claim
            with self.assertRaisesRegex(ValueError,"cannot be issued"):
                future.pin_source_metadata(bad,self.raw,as_of=now)

    def test_csv_duplicate_missing_mortality_missing_2026_and_bad_zip(self):
        basic=csv_rows(self.records,self.names)
        bad=[
            basic+basic.splitlines()[1]+"\n",
            basic.replace("sb_total_deaths_best","not_mortality"),
            basic.replace("sb_total_deaths_best","sb_total_deaths_best,sb_total_deaths_best_cy")
                  .replace(",0\n",",0,0\n"),
            basic.replace(",2026,25",",2026,-1",1),
            basic.replace(",2026,0",",2026,n/a",1),
            basic.replace(",2026,0",",2026,0,EXTRA",1),
        ]
        for text in bad:
            with self.subTest(case=text[-80:]):
                with self.assertRaises(ValueError):
                    future.parse_annual_2026_csv(text)
        with self.assertRaises(ValueError):
            future.build_candidate(archive(basic,"more rows"),pin(
                archive(basic,"more rows")),self.issued,as_of=self.as_of)

    def test_dynamic_cohort_must_not_pretend_the_2025_196_ids_are_unchanged(self):
        records,names=new_origin_data()
        for cid in range(1,15):
            del records[cid][2026]
        with self.assertRaisesRegex(ValueError,"plausible"):
            future.parse_annual_2026_csv(csv_rows(records,names))
        for wrong in (
            {"target":{"year":2027}},
            {"forecast_id":"unissued_synthetic", "origin":{"year":2025},
             "target":{"year":2028},"protocol":{"horizon_years":3},
             "2028_outcomes_resolved":0,"countries":self.issued["countries"]},
        ):
            with self.assertRaisesRegex(ValueError,"not authenticated"):
                future.build_candidate(self.raw,self.pin,wrong,as_of=self.as_of)

    def test_validate_rejects_false_issuance_false_independence_and_fabricated_2028(self):
        doc=future.build_candidate(self.raw,self.pin,self.issued,as_of=self.as_of)
        for kind,value in (
            ("status","ISSUED_PROSPECTIVE_UNRESOLVED"),
            ("origin_year",2025),("target_year",2027),("horizon_years",3),
            ("n_issued_country_questions",196),
            ("no_first_public_forecast_commit_yet",False),
            ("independently_attested_source_release",True),
            ("statistically_independent_of_origin2025_GEO2028",True),
            ("no_2028_outcomes_observed",False),
        ):
            bad=copy.deepcopy(doc);bad[kind]=value
            with self.subTest(change=kind):
                with self.assertRaisesRegex(ValueError,"Unsafe chronology"):
                    future.validate_candidate(bad)
        bad=copy.deepcopy(doc);bad["countries"][0]["p_model"]=1
        with self.assertRaisesRegex(ValueError,"probability"):
            future.validate_candidate(bad)
        bad=copy.deepcopy(doc);bad["countries"][0]["country_id"]=197
        with self.assertRaisesRegex(ValueError,"GWNO"):
            future.validate_candidate(bad)
        bad=copy.deepcopy(doc);bad["expected_2028_active_country_counts"]["p_model"]+=1
        with self.assertRaisesRegex(ValueError,"expected count"):
            future.validate_candidate(bad)


if __name__=="__main__":
    unittest.main()
