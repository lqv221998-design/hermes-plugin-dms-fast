import tempfile
import unittest
from unittest.mock import Mock, patch
import test_reader as reader


class LateQuotaTests(unittest.TestCase):
    def test_resumed_attempt_reads_late_quota_without_second_click(self):
        ctx = Mock()
        import test_session as sessions
        ctx.state = sessions.State()
        ctx.get_config.side_effect = lambda key, default=None: 0 if key == 'download_wait_seconds' else default
        from dms_fast_test.executor import execute
        with tempfile.TemporaryDirectory() as directory:
            task = {'kind': 'search_download_one', 'query': 'Quy trình', 'url': reader.URL, 'expected_title': 'Quy trình', 'expected_code': 'QT-KT-07', 'output_dir': directory}
            source = {'url': reader.URL, 'code': 'QT-KT-07', 'title': 'Quy trình', 'revision': '1', 'effective_date': '21/12/2022'}
            ctx.state.set('download_late', {'attempted': True, 'task': task, 'server': 'chrome_dms', 'source': source, 'download_dir': directory, 'before': {}})
            text = reader.TEXT + '\nuid=1_30 StaticText "Đã quá số lượng tải văn bản trong ngày, vui lòng liên hệ BP Hệ thống (5 văn bản/ngày).."'
            call = Mock()
            result = execute(ctx, task, 2, text, call, 'late')
            self.assertEqual(result['status'], 'awaiting_quota')
            self.assertEqual(ctx.state.get('quota_latch')['source'], source)
            call.assert_not_called()

    def test_resume_checks_files_without_repeating_the_configured_wait(self):
        import test_session as sessions
        from dms_fast_test.executor import execute
        ctx = sessions.SessionTests().context()
        ctx.get_config.side_effect = lambda key, default=None: 20 if key == 'download_wait_seconds' else default
        with tempfile.TemporaryDirectory() as directory:
            task = {'kind': 'search_download_one', 'query': 'Quy trình', 'url': reader.URL, 'expected_title': 'Quy trình', 'expected_code': 'QT-KT-07', 'output_dir': directory}
            source = {'url': reader.URL, 'code': 'QT-KT-07', 'title': 'Quy trình', 'revision': '1', 'effective_date': '21/12/2022'}
            ctx.state.set('download_nowait', {'attempted': True, 'task': task, 'server': 'chrome_dms', 'source': source, 'download_dir': directory, 'before': {}})
            with patch('dms_fast_test.files.time.monotonic', side_effect=[0, 0, 0, 30]), patch('dms_fast_test.files.time.sleep') as sleep:
                result = execute(ctx, task, 2, reader.TEXT, Mock(), 'nowait')
            self.assertEqual(result['status'], 'download_unconfirmed')
            sleep.assert_not_called()


if __name__ == '__main__':
    unittest.main()
