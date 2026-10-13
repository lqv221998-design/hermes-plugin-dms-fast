import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class PolicyTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / 'dms-fast' / 'core.py'
        self.assertTrue(path.exists(), 'Missing DMS URL policy implementation')
        spec = importlib.util.spec_from_file_location('dms_fast_core', path)
        self.core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.core)

    def test_only_canonical_read_routes_are_accepted(self):
        base = 'https://dms.newtecons.vn'
        doc = base + '/document/detail/cab9eb52-bb54-4e32-ba4a-766717c488ac'
        for good in [base + '/', base + '/document/list', base + '/document/dept', base + '/document/site', doc]:
            self.assertEqual(self.core.validate_url(good), good)
        for bad in [base, doc+'?token=a', doc+'#x', doc.upper(), base+'/baseview/logout', base+'/document/detail/not-uuid', 'http://dms.newtecons.vn/', 'https://dms.newtecons.vn.evil/', 'https://a@dms.newtecons.vn/', base+':443/', base+'/document/%64etail/cab9eb52-bb54-4e32-ba4a-766717c488ac']:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.core.validate_url(bad)

if __name__ == '__main__':
    unittest.main()
