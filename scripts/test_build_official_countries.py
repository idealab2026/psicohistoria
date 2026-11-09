import io
import unittest
import zipfile
from build_official_countries import parse_public_source, read_zip, derive_catalog

class PublicUCDPCatalogTests(unittest.TestCase):
    def test_parse_public_state_based_binary_threshold(self):
        s="country,country_id,year,sb_total_deaths_best\nSpain,230,2013,0\nSpain,230,2014,25\nTunisia,325,2013,24\nTunisia,325,2014,26\n"
        records,names=parse_public_source(s,expected_rows=4)
        self.assertEqual(records[230],{2013:0,2014:1})
        self.assertEqual(records[325][2013],0)
        self.assertEqual(names[325],"Tunisia")

    def test_no_duplicate_or_missing_source_fields(self):
        s="country,country_id,year,sb_total_deaths_best\nSpain,230,2014,0\nSpain,230,2014,1\n"
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            parse_public_source(s,expected_rows=2)
        with self.assertRaisesRegex(ValueError,"column"):
            parse_public_source("country,country_id,year\nSpain,230,2014\n",expected_rows=1)

    def test_cutoff_only_country_counts_not_leaking_later_observations(self):
        years=range(1989,2026)
        records={cid:{year:int((year+cid)%7<2) for year in years}
                 for cid in range(200,390)}
        names={cid:"Country "+str(cid) for cid in records}
        source="a"*64
        a=derive_catalog(records,names,2020,2018,6,source,"b"*64)
        self.assertEqual(len(a["countries"]),190)
        self.assertEqual(a["maxHorizon"],6)
        self.assertEqual(a["cutoff"],2018)
        self.assertFalse(a["prospectiveEligible"])
        c=a["countries"][0]
        copy={cid:dict(history) for cid,history in records.items()}
        for country in records:
            for year in range(2019,2026):
                copy[country][year]=1-copy[country][year]
        b=derive_catalog(copy,names,2020,2018,6,source,"b"*64)
        self.assertEqual(a,b)
        self.assertEqual(c["initial"],records[c["id"]][2017]*2+records[c["id"]][2018])

    def test_official_zip_contract(self):
        rows="country,country_id,year,sb_total_deaths_best\n"+"\n".join(
           f"Country{i},999,2000,{i}" for i in range(7500))+"\n"
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,"w",zipfile.ZIP_DEFLATED) as z:
            z.writestr("official.csv",rows)
        self.assertEqual(read_zip(stream.getvalue()),rows)

if __name__=="__main__":unittest.main()
