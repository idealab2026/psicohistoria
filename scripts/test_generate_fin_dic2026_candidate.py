import unittest
from datetime import datetime,timezone
from generate_fin_dic2026_candidate import build,canonical,DEADLINE

class CandidateTests(unittest.TestCase):
    def test_deadline(self):
        with self.assertRaisesRegex(ValueError,"deadline"):
            build(b"",DEADLINE)
    def test_wrong_bytes(self):
        with self.assertRaisesRegex(ValueError,"Source bytes"):
            build(b"wrong",datetime(2026,11,27,tzinfo=timezone.utc))
    def test_canonical(self):
        self.assertEqual(canonical({"b":1,"a":2}),b'{"a":2,"b":1}\n')

if __name__=="__main__": unittest.main()
