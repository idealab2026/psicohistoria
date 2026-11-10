import unittest
from forecast_2027_statebased import (
    PROTOCOL_ID,estimate_from_history,build_forecast,validate_candidate
)

def toy():
    countries={}
    labels={}
    for country in range(1,197):
        labels[country]="Test_Country_"+str(country)
        h={}
        for year in range(1989,2026):
            h[year]=int((country%11<2 and year%5<3) or (country%11>=2 and country%9==0 and year%7==0))
        countries[country]=h
    return countries,labels

class ProspectiveRegistry(unittest.TestCase):
    def test_cohort_probabilities_are_deterministic_and_bounded(self):
        records,names=toy()
        a,summary=estimate_from_history(records,names)
        b,second=estimate_from_history(records,names)
        self.assertEqual(a,b)
        self.assertEqual(summary,second)
        self.assertEqual(len(a),196)
        self.assertEqual(summary["global_5y_exposures"],980)
        self.assertEqual(a[0]["country_id"],1)
        self.assertEqual(a[-1]["country_id"],196)
        self.assertTrue(all(0<x["p_model"]<1 and 0<x["p_baseline_global_5y"]<1
                            for x in a))
        self.assertEqual(len(set(x["p_baseline_global_5y"] for x in a)),1)
        self.assertGreater(len(set(x["p_model"] for x in a)),2)

    def test_twostep_model_is_not_simple_last_year_copy(self):
        r,n=toy()
        predictions,info=estimate_from_history(r,n)
        q0,q1=info["global_transition_p_active"]
        row=predictions[0]
        s=row["last_observed_state_2025"]
        expected=(1-[q0,q1][s])*q0+[q0,q1][s]*q1
        self.assertAlmostEqual(row["p_global_markov"],expected,places=11)
        self.assertGreater(row["p_global_markov"],0)
        self.assertLess(row["p_global_markov"],1)

    def test_2026_2027_or_later_observations_are_rejected(self):
        r,n=toy()
        r[3][2026]=1
        with self.assertRaisesRegex(ValueError,"Future"):
            estimate_from_history(r,n)
        r[3].pop(2026);r[3][2027]=0
        with self.assertRaisesRegex(ValueError,"Future"):
            estimate_from_history(r,n)

    def test_invalid_cohort_or_future_source_does_not_issue(self):
        r,n=toy()
        del r[3][2025]
        with self.assertRaisesRegex(ValueError,"cohort incomplete"):
            estimate_from_history(r,n)
        with self.assertRaisesRegex(ValueError,"SHA-256 mismatch"):
            build_forecast(b"tampered",b"test source")

    def test_document_and_frozen_probabilities_reject_posthoc_changes(self):
        # Tests use synthetic records; they NEVER claim a genuine issuance.
        rows,stats=estimate_from_history(*toy())
        candidate={
            "forecast_id":PROTOCOL_ID,"state":"PREPARED_FOR_PUBLIC_GIT_COMMIT",
            "training_summary":stats,
            "countries":rows,
            "target":{"year":2027},
            "source":{"data_last_year":2025},
            "protocol":{"skill_not_demonstrated":True},
        }
        self.assertTrue(validate_candidate(candidate))
        changed={**candidate,"state":"ISSUED_PROSPECTIVE_UNRESOLVED"}
        with self.assertRaisesRegex(ValueError,"freeze protocol"):
            validate_candidate(changed)
        changed={**candidate,"countries":rows[:-1]}
        with self.assertRaisesRegex(ValueError,"cohort"):
            validate_candidate(changed)
        changed={**candidate,"target":{"year":2026}}
        with self.assertRaisesRegex(ValueError,"temporal"):
            validate_candidate(changed)
        changed={**candidate,"protocol":{"skill_not_demonstrated":False}}
        with self.assertRaisesRegex(ValueError,"unverified"):
            validate_candidate(changed)
        changed={**candidate,"countries":[{**row} for row in rows]}
        changed["countries"][0]["p_model"]=2
        with self.assertRaisesRegex(ValueError,"probability"):
            validate_candidate(changed)

if __name__=="__main__":
    unittest.main()
