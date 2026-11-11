import unittest

from probe_multiple_onset_vintages import source_urls,scan,probe,SCHEMA,HISTORY
from evaluate_homogeneous_onset2 import SOURCES

URL23="https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-multiple-onset-231.csv"
URL25="https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-multiple-onset-251.csv"

def html():
    return ("""<html><h2>UCDP Onset Dataset</h2>
 <p>version 25.1: <a href="%s">Intrastate Country Level Multiple Onset CSV</a></p>
 <p>version 23.1: <a href="%s">Intrastate Country Level Multiple Onset CSV</a></p>
 </html>"""%(URL25,URL23)).encode()

class MultipleOnsetProbeTests(unittest.TestCase):
    def test_distinct_original_version_urls_discovered_not_guessed(self):
        self.assertEqual(source_urls(html()),{"23.1":URL23,"25.1":URL25})
        corrupt=html().replace(b"Intrastate Country Level Multiple Onset CSV",
                               b"Intrastate Country Level Onset CSV")
        with self.assertRaisesRegex(ValueError,"Unable to uniquely identify"):
            source_urls(corrupt)
        injected=html().replace(b"https://ucdp.uu.se/",b"http://evil.example/")
        with self.assertRaisesRegex(ValueError,"Unable to uniquely identify"):
            source_urls(injected)

    def test_aggregate_real_episode_rows_without_inflating_country_years(self):
        content="gwno_a,year,onset2,newconf\n" + "".join(
            f"{n},{y},{int(y%17==0 and n%13==0)},{int(y%17==0 and n%13==0)}\n"
            for y in range(1950,2023) for n in range(1,197)
        )
        with_duplicate=content+"1,2022,0,1\n1,2022,0,1\n"
        groups,metadata=scan(with_duplicate.encode(),2022)
        self.assertEqual(len(groups),73*196)
        self.assertEqual(metadata["unique_country_years"],73*196)
        self.assertEqual(metadata["episode_rows"],73*196+2)
        self.assertEqual(metadata["duplicate_country_year_keys"],1)
        self.assertEqual(metadata["extra_episode_rows_over_country_years"],2)
        self.assertEqual(metadata["max_rows_in_a_country_year"],3)
        self.assertEqual(metadata["latest_year"]["country_years"],196)
        self.assertTrue(groups[(2022,"1")]["new_conflict_episode_count"]==2)
        self.assertTrue(groups[(2022,"1")]["onset2_episode_count"]==0)
        self.assertGreater(metadata["total_newconf_episode_rows"],0)
        self.assertIn("episode rows",metadata["unit"])
        with self.assertRaisesRegex(ValueError,"Non-binary"):
            scan(content.replace("1,1950,0,0","1,1950,2,0").encode(),2022)
        with self.assertRaisesRegex(ValueError,"requires both"):
            scan(content.replace("onset2,newconf","onset2").encode(),2022)


    def test_rejects_archive_without_real_links_before_any_download(self):
        calls=[]
        def fake_fetch(url,lim):
            calls.append(url)
            return b"<html><h2>UCDP Onset Dataset</h2>no csv</html>"
        with self.assertRaisesRegex(ValueError,"Unable to uniquely identify"):
            probe(fake_fetch)
        self.assertEqual(calls,[HISTORY])

if __name__=="__main__":
    unittest.main()
