"""Source-vintage controls using synthetic UCDP/PRIO conflict-year ZIPs only."""
from __future__ import annotations
import copy
import csv
import hashlib
import io
import unittest
from unittest.mock import patch
from zipfile import ZipFile,ZIP_DEFLATED

import diagnose_ucdp_prio_older_vintages as study


FIELDS=("conflict_id","year","type_of_conflict","gwno_a","gwno_loc")


def fake_zip(last_year,*,altered=False,unsafe=False):
    stream=io.StringIO()
    writer=csv.DictWriter(stream,fieldnames=FIELDS)
    writer.writeheader()
    for cid in range(1,106):
        for y in range(last_year-19,last_year+1):
            if altered and cid==12 and y==last_year-1:
                continue
            writer.writerow({
                "conflict_id":str(1000+cid),
                "year":str(y),
                "type_of_conflict":"3",
                "gwno_a":str(cid),
                "gwno_loc":"1" if unsafe and cid==20 else str(cid),
            })
    if altered:
        writer.writerow({
            "conflict_id":"9999","year":str(last_year-1),
            "type_of_conflict":"4","gwno_a":"108","gwno_loc":"108"
        })
    raw=io.BytesIO()
    with ZipFile(raw,"w",ZIP_DEFLATED) as z:
        z.writestr("ucdp-prio-synthetic-conflict-year.csv",stream.getvalue())
    return raw.getvalue()


class OlderACDVintageTests(unittest.TestCase):
    def test_source_metadata_and_4_adjacent_historical_revisions(self):
        blobs={v:fake_zip(spec["last_year"],altered=(v=="22.1"))
               for v,spec in study.HISTORICAL.items()}
        patched=copy.deepcopy(study.HISTORICAL)
        for v,data in blobs.items():
            patched[v]["sha256"]=hashlib.sha256(data).hexdigest()
        def fetcher(url,limit):
            self.assertGreater(limit,1_000_000)
            return next(blobs[v] for v,s in patched.items() if s["url"]==url)
        with patch.object(study,"HISTORICAL",patched):
            report=study.diagnose(fetcher)
        self.assertEqual(report["status"],"SHA_PINNED_SOURCE_METADATA_REPRODUCIBLE")
        self.assertFalse(report["source_metadata_provisional"])
        self.assertEqual(len(report["revision_of_historical_intrastate_country_year_incidence"]),4)
        self.assertEqual(report["source_metadata"]["20.1"]["last_year"],2019)
        self.assertEqual(report["source_metadata"]["25.1"]["last_year"],2024)
        self.assertTrue(report["explicitly_not_original_geo2027_statebased_25_deaths"])
        self.assertFalse(report["country_wide_inactive_labels_derivable_from_ACD_alone"])
        self.assertEqual(report["target_2027_observations"],0)
        self.assertFalse(report["original_geo2027_or_newconf2027_or_shadow_modified"])
        self.assertFalse(report["structural_geopolitical_dependence_identified"])

    def test_unpinned_source_is_discovery_only_never_certified(self):
        body=fake_zip(2019)
        with self.assertRaisesRegex(ValueError,"Unpinned historical"):
            study.parse_version(body,"20.1",allow_probe=False)
        active,meta=study.parse_version(body,"20.1",allow_probe=True)
        self.assertEqual(meta["last_year"],2019)
        self.assertFalse(meta["sha256_pinned_before_run"])
        self.assertGreater(len(active),1200)
        self.assertEqual(meta["unique_active_intrastate_country_years"],len(active))
        self.assertFalse(meta["all_implicit_country_year_non_events_recovered"])

    def test_sha_mismatch_and_noninstitutional_url_rejected(self):
        body=fake_zip(2022)
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            study.parse_version(body,"23.1")
        for url in ("http://ucdp.uu.se/downloads/ucdpprio/foo-csv.zip",
                    "https://malicious.org/downloads/ucdpprio/foo-csv.zip",
                    "https://ucdp.uu.se/downloads/ucdpprio/foo-csv.zip?x=1"):
            with self.assertRaisesRegex(ValueError,"Non-institutional"):
                study.official_download_url(url)

    def test_duplicate_year_and_multicode_country_fail_closed(self):
        wrong=fake_zip(2019,unsafe=True)
        with self.assertRaisesRegex(ValueError,"Cannot resolve"):
            study.parse_version(wrong,"20.1",allow_probe=True)
        stream=io.StringIO();w=csv.DictWriter(stream,fieldnames=FIELDS)
        w.writeheader()
        for cid in range(1,106):
            for y in range(2000,2020):
                row={"conflict_id":str(cid),"year":str(y),
                     "type_of_conflict":"3","gwno_a":str(cid),"gwno_loc":str(cid)}
                w.writerow(row)
                if cid==1 and y==2000:
                    w.writerow(row)
        buffer=io.BytesIO()
        with ZipFile(buffer,"w",ZIP_DEFLATED) as z:
            z.writestr("test.csv",stream.getvalue())
        with self.assertRaisesRegex(ValueError,"Repeated conflict-year"):
            study.parse_version(buffer.getvalue(),"20.1",allow_probe=True)

    def test_historical_revisions_are_edits_not_future_changes(self):
        old={("10",2018),("11",2018),("12",2019)}
        new={("10",2018),("11",2018),("13",2019)}
        cmp=study.compare(old,new,2019)
        self.assertEqual(cmp["newly_coded_active_country_years"],1)
        self.assertEqual(cmp["no_longer_coded_active_country_years"],1)
        self.assertEqual(cmp["net_change_in_active_incidence_count"],0)
        self.assertEqual(cmp["sum_absolute_label_changes_in_recorded_active_set"],2)
        self.assertFalse(cmp["implies_statebased_25death_label_revision"])


if __name__=="__main__":
    unittest.main()
