import importlib
import tempfile
import unittest
import zipfile
from pathlib import Path
import test_reader as reader
import test_session as sessions

files = importlib.import_module('dms_fast_test.files')


class FileSafetyTests(unittest.TestCase):
    def test_rejects_html_empty_partial_pdf_unsafe_zip_and_symlink(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            for name, content in [('empty.zip', b''), ('login.pdf', b'<html>login</html>'), ('partial.pdf', b'%PDF-1.4\nmissing eof')]:
                path = root / name; path.write_bytes(content)
                with self.subTest(name=name), self.assertRaises(ValueError):
                    files.inspect_file(path)
            for name in ('../escape.txt', '/absolute.txt', 'C:/outside.txt'):
                path = root / 'bad.zip'
                with zipfile.ZipFile(path, 'w') as archive:
                    archive.writestr(name, 'fixture')
                with self.subTest(name=name), self.assertRaises(ValueError):
                    files.inspect_file(path)

    def test_uncertain_attempt_is_checked_only_and_cannot_rebind_work_id(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        with tempfile.TemporaryDirectory() as root:
            task = {'kind': 'search_download_one', 'query': 'Quy trình', 'url': reader.URL, 'expected_title': 'Quy trình', 'expected_code': 'QT-KT-07', 'output_dir': root}
            saved = {'server': 'chrome_dms', 'source': {'url': reader.URL, 'code': 'QT-KT-07', 'title': 'Quy trình', 'revision': '1', 'effective_date': '21/12/2022'}, 'task': task, 'download_dir': root, 'before': {}, 'attempted': True}
            ctx.state.set('download_uncertain', saved)
            ctx.get_config.side_effect = lambda key, default=None: root if key == 'download_dir' else 0 if key == 'download_wait_seconds' else default
            ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot()]
            result = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'uncertain', 'task': task})
            self.assertEqual(result['status'], 'download_unconfirmed')
            self.assertEqual(ctx.call_mcp.call_count, 2)
            helper.invoke(ctx, {'action': 'cancel', 'work_id': 'uncertain'})
            ctx.call_mcp.reset_mock()
            ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot()]
            result = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'uncertain', 'task': dict(task, expected_code='WRONG')})
            self.assertEqual(result['status'], 'pending_work_conflict')
            self.assertEqual(ctx.call_mcp.call_count, 2)


if __name__ == '__main__':
    unittest.main()
