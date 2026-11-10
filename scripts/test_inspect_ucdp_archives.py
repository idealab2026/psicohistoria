import unittest
import hashlib
from inspect_ucdp_archives import HISTORY,PINNED,discover,parse_source,inspect,onset_labels,compare_revisions

class DiscoveryTests(unittest.TestCase):
    def test_official_links_section_and_version(self):
        html='''<h2>UCDP Onset Dataset</h2>
        <p>version 24.1: <a href="/downloads/onset/special-241.csv">Intrastate Country Level Onset CSV</a></p>
        <p>version 23.1: <a href="/downloads/onset/ucdp-intrastate-country-onset-231.csv">Intrastate Country Level Onset CSV</a></p>
        <h2>UCDP Country-Year Dataset</h2><p>version 23.1:
        <a href="/downloads/onset/fake-231.csv">CSV</a></p>'''
        links=discover(html)
        self.assertEqual([r["version"] for r in links],["24.1","23.1"])
        self.assertTrue(all(r["url"].startswith("https://ucdp.uu.se/downloads/onset/") for r in links))

    def test_official_parse_country_year(self):
        rows="year,onset2,gwno_a,abc\n"+ "".join(
            f"{y},{1 if y==2024 and i==1 else 0},{i},TST\n"
            for y in range(1946,2025) for i in range(130))
        result=parse_source(rows.encode())
        self.assertEqual(result["last_year"],2024)
        self.assertEqual(result["latest_onset2_positives"],1)
        self.assertEqual(result["latest_country_count"],130)

    def test_digest_guard_blocks_manipulated_official_vintage(self):
        html=b'<h2>UCDP Onset Dataset</h2>'
        def fake(url,limit):
            return html if url==HISTORY else b"incorrect-data"
        with self.assertRaisesRegex(ValueError,"hash mismatch"):
            inspect(fake)

    def test_historical_label_drift_distinguishes_flips_from_coverage(self):
        header="year,gwno_a,onset2\n"
        old=header+"2021,230,0\n2021,231,1\n2022,230,1\n2022,231,0\n"
        new=header+"2021,230,1\n2021,231,1\n2022,230,0\n2022,232,1\n2023,230,1\n"
        score=compare_revisions(onset_labels(old.encode()),onset_labels(new.encode()),2022)
        self.assertEqual(score["common_country_years"],3)
        self.assertEqual(score["country_years_only_in_23_1"],1)
        self.assertEqual(score["country_years_only_in_25_1"],1)
        self.assertEqual(score["onset2_label_flips"],2)
        self.assertEqual(score["flips_0_to_1"],1)
        self.assertEqual(score["flips_1_to_0"],1)
        self.assertTrue(score["not_prospective"])

    def test_labels_are_not_presented_as_prospective(self):
        # The schema and historical-issuance flags cannot depend on URL names.
        self.assertEqual(len(PINNED),2)
        self.assertEqual(set(PINNED),{"23.1","25.1"})

if __name__=="__main__":unittest.main()
