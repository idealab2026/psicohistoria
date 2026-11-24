import unittest
from datetime import datetime,timezone
from audit_candidate_october_source_observation import inspect,verify_index,URL
HEADER="id,country_id,type_of_violence,date_prec,date_start,date_end,best\n"
OBS=datetime(2026,11,24,tzinfo=timezone.utc)
class Tests(unittest.TestCase):
    def test_exact_official_link(self):
        verify_index(('<a href="'+URL+'">October</a>').encode())
        with self.assertRaises(ValueError): verify_index(b'<a href="https://example.org">October</a>')
    def test_recent_window(self):
        raw=(HEADER+"1,1,1,1,2026-08-01,2026-08-01,2\n2,1,2,1,2026-10-31,2026-11-01,2\n3,2,3,2,2026-10-01,2026-10-02,3\n").encode()
        result=inspect(raw,{1,2},OBS)
        self.assertEqual(result["event_counts"]["eligible_recent_rows"],2)
        self.assertEqual(result["event_counts"]["outside_recent_window"],1)
        self.assertEqual(result["countries_with_positive_state_based_best"],1)
    def test_future_event_rejected(self):
        with self.assertRaises(ValueError):
            inspect((HEADER+"1,1,1,1,2026-11-24,2026-11-24,1\n").encode(),{1},OBS)
    def test_stale_source_rejected(self):
        with self.assertRaises(ValueError):
            inspect(HEADER.encode(),{1},datetime(2026,12,20,tzinfo=timezone.utc))
if __name__=="__main__": unittest.main()
