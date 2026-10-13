import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('core', ROOT / 'dms-fast/core.py')
assert spec is not None and spec.loader is not None
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

class SnapshotTests(unittest.TestCase):
    def test_extracts_links_dedupes_and_preserves_partial_coverage(self):
        text = '''uid=1_0 RootWebArea "Thử" url="https://dms.newtecons.vn/"
  uid=1_1 link "Hồ sơ nghiệm thu" url="https://dms.newtecons.vn/document/detail/cab9eb52-bb54-4e32-ba4a-766717c488ac"
  uid=1_2 link "Hồ sơ nghiệm thu" url="https://dms.newtecons.vn/document/detail/cab9eb52-bb54-4e32-ba4a-766717c488ac"
  uid=1_3 link "Đăng xuất" url="https://dms.newtecons.vn/baseview/logout"
  uid=1_4 StaticText "Còn hiệu lực"
'''
        self.assertTrue(callable(getattr(core, 'parse_snapshot', None)), 'Missing semantic snapshot parser')
        result = core.parse_snapshot(text)
        self.assertEqual(len(result['documents']), 1)
        self.assertEqual(result['documents'][0]['title'], 'Hồ sơ nghiệm thu')
        self.assertFalse(result['full_document_read'])
        self.assertFalse(result['inventory_complete'])
        self.assertEqual(result['documents'][0]['uid'], '1_1')
        self.assertNotIn('Đăng xuất', str(result['documents']))

if __name__ == '__main__':
    unittest.main()
