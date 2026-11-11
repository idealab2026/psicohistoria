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

    def test_binary_country_year_requires_a_real_compatible_dataset(self):
        import csv,io
        content="gwno_a,year,onset2\n" + "".join(
            f"{n},{y},{int(y%17==0 and n%13==0)}\n"
            for y in range(1950,2023) for n in range(1,197)
        )
        labels,metadata=scan(content.encode(),2022)
        self.assertEqual(len(labels),73*196)
        self.assertEqual(metadata["latest_year"],2022)
        self.assertEqual(metadata["latest_country_count"],196)
        self.assertTrue(metadata["binary_onset2"])
        with self.assertRaisesRegex(ValueError,"Duplicate country-year"):
            scan((content+"1,2022,0\n").encode(),2022)
        with self.assertRaisesRegex(ValueError,"Non-binary"):
            scan(content.replace("1,1950,0","1,1950,2").encode(),2022)

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
