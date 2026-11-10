import json
import tempfile
import unittest
from pathlib import Path
from forecast_2027_statebased import estimate_from_history,sha256
from test_forecast_2027_statebased import toy
from audit_frozen_2027 import (
    read_issue,independent_recomputation,canonical_bytes,HISTOGRAM_EDGES,
    FORECAST,MANIFEST,GENERATOR,FROZEN_SHA,
)

class Independent2027Audit(unittest.TestCase):
    def test_existing_issued_bytes_and_generator_fingerprint_are_frozen(self):
        raw,forecast,manifest,script=read_issue()
        self.assertEqual(sha256(raw),FROZEN_SHA)
        self.assertEqual(raw,canonical_bytes(forecast))
        self.assertEqual(sha256(script),forecast["provenance"]["generator_sha256"])
        self.assertEqual(len(forecast["countries"]),196)
        self.assertEqual(manifest["outcomes_resolved"],0)

    def test_independent_markov_equations_reproduce_original_on_synthetic_panel(self):
        history,names=toy()
        separate,matrix,positives=independent_recomputation(history,names)
        original,metadata=estimate_from_history(history,names)
        self.assertEqual(separate,original)
        self.assertEqual(matrix,metadata["global_transition_counts"])
        self.assertEqual(positives,metadata["global_5y_positive"])
        self.assertEqual(len(separate),196)
        self.assertEqual(len(HISTOGRAM_EDGES),7)

    def test_perturbed_2026_data_cannot_appear_in_audited_historical_source(self):
        history,names=toy()
        history[1][2026]=1
        with self.assertRaisesRegex(ValueError,"Future data"):
            independent_recomputation(history,names)

    def test_tampered_probabilities_fail_closed_even_if_json_remains_well_formed(self):
        raw,doc,m,script=read_issue()
        changed=json.loads(raw)
        changed["countries"][0]["p_model"]=0.9999999
        with tempfile.TemporaryDirectory() as directory:
            candidate=Path(directory)/"candidate.json"
            candidate.write_bytes(canonical_bytes(changed))
            with self.assertRaisesRegex(ValueError,"Frozen 2027 probability bytes"):
                read_issue(candidate,MANIFEST,GENERATOR)

    def test_manifest_misreports_2027_resolution_or_metadata_cannot_pass(self):
        raw,doc,manifest,script=read_issue()
        with tempfile.TemporaryDirectory() as directory:
            candidate=Path(directory)/"manifest.json"
            for label,value in [("outcomes_resolved",1),
                ("demonstrated_predictive_skill",True),
                ("first_public_forecast_commit","f"*40),
                ("preregistered_at_utc","2027-04-01T00:00:00Z")]:
                changed={**manifest,label:value}
                candidate.write_text(json.dumps(changed),encoding="utf8")
                with self.assertRaisesRegex(ValueError,"Issued 2027 provenance"):
                    read_issue(FORECAST,candidate,GENERATOR)

    def test_missing_countries_in_2025_source_are_not_silently_replaced(self):
        history,names=toy()
        del history[3][2025]
        with self.assertRaisesRegex(ValueError,"cohort differs"):
            independent_recomputation(history,names)

if __name__=="__main__":unittest.main()
