import unittest
import test_session as sessions
import test_reader as reader

HOME = '''uid=1_0 RootWebArea "DMS" url="https://dms.newtecons.vn/"
uid=1_1 link "Đăng xuất" url="https://dms.newtecons.vn/baseview/logout"
uid=1_3 searchbox "Bạn muốn tìm gì?"
'''
RESULT = HOME + f'uid=2_4 link "Quy trình" url="{reader.URL}"\n'


class ExecutorTests(unittest.TestCase):
    def test_completed_file_is_copied_hashed_and_reused_without_download(self):
        import tempfile
        import hashlib
        import zipfile
        from pathlib import Path
        helper = sessions.SessionTests()
        ctx = helper.context()
        detail = reader.TEXT + '\nuid=1_20 StaticText "Lần ban hành"\nuid=1_21 StaticText "1"\nuid=1_22 link "Tải về" url="javascript:;"\n'
        with tempfile.TemporaryDirectory() as root:
            downloads, output = Path(root) / 'downloads', Path(root) / 'output'
            downloads.mkdir(); output.mkdir()
            task = {'kind': 'search_download_one', 'query': 'Quy trình', 'url': reader.URL, 'expected_title': 'Quy trình', 'expected_code': 'QT-KT-07', 'output_dir': str(output)}
            ctx.get_config.side_effect = lambda key, default=None: str(downloads) if key == 'download_dir' else 0 if key == 'download_wait_seconds' else default
            answers = iter([helper.listing(), helper.snapshot(HOME), {'ok': True, 'result': 'navigated'}, helper.snapshot(detail), {'ok': True, 'result': 'clicked'}, helper.snapshot(detail)])
            def mcp(server, name, payload, **kw):
                if name == 'click':
                    with zipfile.ZipFile(downloads / 'QT-KT-07.zip', 'w') as archive:
                        archive.writestr('QT-KT-07.txt', 'download fixture, not real company content')
                return next(answers)
            ctx.call_mcp.side_effect = mcp
            result = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'file-one', 'task': task})
            self.assertEqual(result['status'], 'completed')
            path = Path(result['file']['path'])
            self.assertEqual(path.parent, output.resolve())
            self.assertEqual(result['file']['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(path.read_bytes(), (downloads / 'QT-KT-07.zip').read_bytes())
            self.assertIsNone(ctx.state.get('session_work'))
            self.assertFalse(result['full_document_read'])
            ctx.call_mcp.reset_mock()
            ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(detail)]
            reused = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'file-one', 'task': task})
            self.assertEqual(reused['status'], 'completed')
            self.assertTrue(reused['reused_local'])
            self.assertEqual(ctx.call_mcp.call_count, 2)
            ctx.call_mcp.reset_mock()
            ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(detail.replace('StaticText "1"', 'StaticText "2"'))]
            changed = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'file-one', 'task': task})
            self.assertEqual(changed['status'], 'source_revision_changed')
            self.assertFalse(changed['download_attempted'])
            helper.invoke(ctx, {'action': 'cancel', 'work_id': 'file-one'})
            # A new work ID for the same live revision must reuse the verified local ledger.
            ctx.call_mcp.reset_mock()
            ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(HOME), {'ok': True, 'result': 'navigated'}, helper.snapshot(detail)]
            duplicate = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'another-one', 'task': task})
            self.assertEqual(duplicate['status'], 'completed')
            self.assertTrue(duplicate['reused_local'])
            self.assertEqual(sum(c.args[1] == 'click' for c in ctx.call_mcp.call_args_list), 0)

    def test_selected_source_quota_is_pending_and_never_clicks_twice(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        detail = reader.TEXT + '\nuid=1_20 StaticText "Lần ban hành"\nuid=1_21 StaticText "1"\nuid=1_22 link "Tải về" url="javascript:;"\n'
        notice = detail + '\nuid=1_30 StaticText "Đã quá số lượng tải văn bản trong ngày, vui lòng liên hệ BP Hệ thống (5 văn bản/ngày).."\n'
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as root:
            task = {'kind': 'search_download_one', 'query': 'Quy trình', 'url': reader.URL, 'expected_title': 'Quy trình', 'expected_code': 'QT-KT-07', 'output_dir': root}
            ctx.get_config.side_effect = lambda key, default=None: root if key == 'download_dir' else default
            ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(HOME), {'ok': True, 'result': 'navigated'}, helper.snapshot(detail), {'ok': True, 'result': 'clicked'}, helper.snapshot(notice)]
            result = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'quota-one', 'task': task})
            self.assertEqual(result['status'], 'awaiting_quota')
            self.assertTrue(result['ok'])
            self.assertEqual(result['source']['revision'], '1')
            self.assertEqual(sum(c.args[1] == 'click' for c in ctx.call_mcp.call_args_list), 1)
            self.assertIsNotNone(ctx.state.get('session_work'))
            ctx.call_mcp.reset_mock()
            ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(detail)]
            resumed = helper.invoke(ctx, {'action': 'resume', 'work_id': 'quota-one'})
            self.assertEqual(resumed['status'], 'awaiting_quota')
            self.assertEqual(sum(c.args[1] == 'click' for c in ctx.call_mcp.call_args_list), 0)

            ctx.call_mcp.reset_mock()
            ctx.call_mcp.side_effect = [helper.sso()]
            acknowledged = helper.invoke(ctx, {'action': 'resume_after_quota', 'work_id': 'quota-one'})
            self.assertEqual(acknowledged['status'], 'awaiting_login')
            self.assertIsNone(ctx.state.get('quota_latch'))
            self.assertIsNone(ctx.state.get('download_quota-one'))

    def test_session_executes_search_and_returns_observed_candidates(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(HOME), {'ok': True, 'result': 'filled'}, {'ok': True, 'result': 'pressed'}, helper.snapshot(RESULT)]
        result = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'search-one', 'task': {'kind': 'search_download_one', 'query': 'Quy trình'}})
        self.assertEqual(result['status'], 'source_selection_required')
        self.assertEqual(result['candidates'], [{'title': 'Quy trình', 'url': reader.URL}])
        self.assertEqual([c.args[1] for c in ctx.call_mcp.call_args_list], ['list_pages', 'take_snapshot', 'fill', 'press_key', 'take_snapshot'])
        self.assertFalse(result['inventory_complete'])
        self.assertIsNotNone(ctx.state.get('session_work'))


if __name__ == '__main__':
    unittest.main()
