import unittest
from unittest import mock
import test_session as sessions
import test_executor as executor


class SearchWorkflowTests(unittest.TestCase):
    def test_search_only_completes_and_clears_work_without_download_state(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(executor.HOME), {'ok': True, 'result': 'filled'}, {'ok': True, 'result': 'pressed'}, helper.snapshot(executor.RESULT)]
        result = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'only-search', 'task': {'kind': 'search', 'query': 'Quy trình'}})
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['operation'], 'search')
        self.assertIsInstance(result.get('elapsed_ms'), int)
        self.assertGreaterEqual(result['elapsed_ms'], 0)
        self.assertEqual(result['candidates'], [{'title': 'Quy trình', 'url': sessions.reader.URL}])
        self.assertFalse(result['download_attempted'])
        self.assertIsNone(ctx.state.get('session_work'))
        self.assertNotIn('download_only-search', ctx.state.values)
        self.assertEqual([c.args[1] for c in ctx.call_mcp.call_args_list], ['list_pages', 'take_snapshot', 'fill', 'press_key', 'take_snapshot'])

    def test_search_is_not_blocked_by_download_quota_and_retains_latch(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        latch = {'server': 'chrome_dms', 'source': {'code': 'QT-KT-07'}, 'daily_limit': 5}
        ctx.state.set('quota_latch', latch)
        ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(executor.HOME), {'ok': True, 'result': 'filled'}, {'ok': True, 'result': 'pressed'}, helper.snapshot(executor.RESULT)]
        result = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'quota-search', 'task': {'kind': 'search', 'query': 'Quy trình'}})
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(ctx.state.get('quota_latch'), latch)
        self.assertFalse(result['download_attempted'])

    def test_empty_parsed_links_are_unverified_not_claimed_no_results(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(executor.HOME), {'ok': True, 'result': 'filled'}, {'ok': True, 'result': 'pressed'}, helper.snapshot(executor.HOME), helper.snapshot(executor.HOME), helper.snapshot(executor.HOME)]
        result = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'empty-search', 'task': {'kind': 'search', 'query': 'Quy trình'}})
        self.assertEqual(result['status'], 'search_result_unverified')
        self.assertEqual(result['candidates'], [])
        self.assertIsNotNone(ctx.state.get('session_work'))
        self.assertFalse(result['inventory_complete'])

    def test_loading_results_rechecked_without_second_submission(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(executor.HOME), {'ok': True, 'result': 'filled'}, {'ok': True, 'result': 'pressed'}, helper.snapshot(executor.HOME), helper.snapshot(executor.RESULT)]
        with mock.patch('time.sleep') as sleeper:
            result = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'loading-search', 'task': {'kind': 'search', 'query': 'Quy trình'}})
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['mcp_calls'], 6)
        methods = [args[0][1] for args in ctx.call_mcp.call_args_list]
        self.assertEqual(methods.count('fill'), 1)
        self.assertEqual(methods.count('press_key'), 1)
        sleeper.assert_called_once_with(0.25)

    def test_search_rejects_download_fields_and_invalid_queries_before_browser(self):
        helper = sessions.SessionTests()
        for task in [{'kind': 'search', 'query': ''}, {'kind': 'search', 'query': 1}, {'kind': 'search', 'query': 'x' * 121}, {'kind': 'search', 'query': 'Quy trình', 'url': sessions.reader.URL}, {'kind': 'search', 'query': 'Quy trình', 'output_dir': 'unapproved'}]:
            ctx = helper.context()
            result = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'invalid-search', 'task': task})
            self.assertFalse(result['ok'])
            ctx.call_mcp.assert_not_called()
            self.assertEqual(ctx.state.values, {})

    def test_conflict_reports_active_identity_without_browser_calls(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        helper.prepare(ctx)
        ctx.call_mcp.reset_mock()
        result = helper.invoke(ctx, {'action': 'status', 'work_id': 'different-search'})
        self.assertEqual(result['status'], 'pending_work_conflict')
        self.assertEqual(result.get('active_work_id'), 'one-qaqc')
        self.assertEqual(result['pending_task']['query'], 'quy trình qaqc')
        ctx.call_mcp.assert_not_called()


if __name__ == '__main__':
    unittest.main()
