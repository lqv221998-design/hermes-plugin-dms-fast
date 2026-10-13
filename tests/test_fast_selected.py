import tempfile
import unittest
import zipfile
from pathlib import Path
import test_session as sessions
import test_reader as reader
import test_executor as executor


class FastSelectedTests(unittest.TestCase):
    def test_exact_selected_source_skips_search_and_verifies_file(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        detail = reader.TEXT + '\nuid=1_20 StaticText "Lần ban hành"\nuid=1_21 StaticText "1"\nuid=1_22 link "Tải về" url="javascript:;"\n'
        with tempfile.TemporaryDirectory() as root:
            downloads, output = Path(root) / 'downloads', Path(root) / 'output'
            downloads.mkdir(); output.mkdir()
            ctx.get_config.side_effect = lambda key, default=None: str(downloads) if key == 'download_dir' else 0 if key == 'download_wait_seconds' else default
            def mcp(server, name, payload, **kwargs):
                if name == 'list_pages':
                    return helper.listing()
                if name == 'take_snapshot':
                    return helper.snapshot(detail if any(c.args[1] == 'navigate_page' for c in ctx.call_mcp.call_args_list) else executor.HOME)
                if name == 'click':
                    with zipfile.ZipFile(downloads / 'QT-KT-07.zip', 'w') as archive:
                        archive.writestr('fixture.txt', 'Test bytes, not company content')
                return {'ok': True, 'result': 'UI action acknowledged'}
            ctx.call_mcp.side_effect = mcp
            task = {'kind': 'search_download_one', 'query': 'Quy trình', 'url': reader.URL, 'expected_title': 'Quy trình', 'expected_code': 'QT-KT-07', 'output_dir': str(output)}
            result = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'fast-source', 'task': task})
            self.assertEqual(result['status'], 'completed')
            names = [c.args[1] for c in ctx.call_mcp.call_args_list]
            self.assertNotIn('fill', names)
            self.assertNotIn('press_key', names)
            self.assertEqual(names.count('click'), 1)
            self.assertEqual(len(names), 6)
            self.assertEqual(Path(result['file']['path']).read_bytes(), (downloads / 'QT-KT-07.zip').read_bytes())


if __name__ == '__main__':
    unittest.main()
