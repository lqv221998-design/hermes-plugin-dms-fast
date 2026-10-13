"""Exercise the real session handler; only the MCP/state boundaries are fixtures."""
import json
import unittest
from unittest.mock import Mock
import test_reader as reader


class State:
    def __init__(self):
        self.values = {}

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = json.loads(json.dumps(value))


class SessionTests(unittest.TestCase):
    def context(self):
        ctx = Mock()
        ctx.get_config.side_effect = lambda key, default=None: default
        ctx.state = State()
        return ctx

    def invoke(self, ctx, args):
        tools = {}
        ctx.register_tool.side_effect = lambda **kwargs: tools.update({kwargs['name']: kwargs['handler']})
        reader.plugin.register(ctx)
        self.assertIn('dms_fast_session', tools, 'Missing browser/login lifecycle tool')
        return json.loads(tools['dms_fast_session'](args))

    def test_existing_sso_is_normal_waiting_not_an_error_or_new_browser(self):
        ctx = self.context()
        ctx.call_mcp.return_value = {'ok': True, 'result': '## Pages\n2: Sign in to Newtecons (https://sso.newtecons.vn/realms/Newtecons/protocol/openid-connect/auth?state=sensitive-do-not-store) [selected]'}
        result = self.invoke(ctx, {'action': 'prepare', 'work_id': 'one-qaqc', 'task': {'kind': 'search_download_one', 'query': 'quy trình qaqc'}})
        self.assertTrue(result['ok'])
        self.assertEqual(result['status'], 'awaiting_login')
        self.assertNotIn('error', result)
        self.assertEqual(ctx.call_mcp.call_count, 1)
        self.assertNotIn('sensitive-do-not-store', str(ctx.state.values))
        self.assertNotIn('sensitive-do-not-store', str(result))
        self.assertEqual(result['pending_task']['query'], 'quy trình qaqc')

    def listing(self, page_id=9):
        return {'ok': True, 'result': f'## Pages\n{page_id}: Quy trình - Newtecons ({reader.URL}) [selected]'}

    def sso(self):
        return {'ok': True, 'result': '## Pages\n2: Sign in to Newtecons (https://sso.example.test/login?state=do-not-retain) [selected]'}

    def snapshot(self, text=reader.TEXT):
        return {'ok': True, 'result': '## Latest page snapshot\n' + text}

    def prepare(self, ctx, task=None):
        ctx.call_mcp.return_value = self.sso()
        return self.invoke(ctx, {'action': 'prepare', 'work_id': 'one-qaqc', 'task': task or {'kind': 'search_download_one', 'query': 'quy trình qaqc'}})

    def test_cold_browser_opens_one_visible_tab_without_isolated_context(self):
        ctx = self.context()
        ctx.call_mcp.side_effect = [{'ok': True, 'result': '## Pages\n0: about:blank (about:blank)'}, self.sso(), self.sso()]
        result = self.invoke(ctx, {'action': 'prepare', 'work_id': 'one-qaqc', 'task': {'kind': 'search_download_one', 'query': 'quy trình qaqc'}})
        self.assertEqual(result['status'], 'awaiting_login')
        opened = ctx.call_mcp.call_args_list[1]
        self.assertEqual(opened.args[:2], ('chrome_dms', 'new_page'))
        self.assertEqual(opened.args[2], {'url': 'https://dms.newtecons.vn/', 'background': False, 'timeout': 10000})

    def test_ready_session_reused_without_new_tab_or_login_prompt(self):
        ctx = self.context()
        ctx.call_mcp.side_effect = [self.listing(), self.snapshot()]
        result = self.invoke(ctx, {'action': 'prepare', 'work_id': 'one-qaqc', 'task': {'kind': 'search_download_one', 'query': 'quy trình qaqc'}})
        self.assertEqual(result['status'], 'search_ui_changed')
        self.assertEqual(result['page_id'], 9)
        self.assertEqual([c.args[1] for c in ctx.call_mcp.call_args_list], ['list_pages', 'take_snapshot'])
        self.assertNotIn('page_id', str(ctx.state.values))

    def test_new_context_resumes_task_using_fresh_page_id(self):
        first = self.context()
        self.prepare(first)
        second = self.context()
        second.state = first.state
        second.call_mcp.side_effect = [self.listing(42), self.snapshot()]
        result = self.invoke(second, {'action': 'resume', 'work_id': 'one-qaqc'})
        self.assertEqual(result['status'], 'search_ui_changed')
        self.assertEqual(result['pending_task']['query'], 'quy trình qaqc')
        self.assertEqual(second.call_mcp.call_args_list[1].args[2]['pageId'], 42)

    def test_read_task_continues_real_reader_and_clears_only_on_success(self):
        ctx = self.context()
        self.prepare(ctx, {'kind': 'read', 'action': 'open', 'url': reader.URL, 'expected_code': 'QT-KT-07', 'expected_title': 'Quy trình'})
        ctx.call_mcp.side_effect = [self.listing(42), self.snapshot(), self.snapshot()]
        result = self.invoke(ctx, {'action': 'resume', 'work_id': 'one-qaqc'})
        self.assertEqual(result['status'], 'completed')
        self.assertTrue(result['result']['ok'])
        self.assertEqual(result['result']['source_identity'], 'matched_expected_fields')
        self.assertIsNone(ctx.state.get('session_work'))

    def test_bad_source_keeps_task_without_claiming_completion(self):
        ctx = self.context()
        self.prepare(ctx, {'kind': 'read', 'action': 'open', 'url': reader.URL, 'expected_code': 'WRONG'})
        ctx.call_mcp.side_effect = [self.listing(), self.snapshot(), self.snapshot()]
        result = self.invoke(ctx, {'action': 'resume', 'work_id': 'one-qaqc'})
        self.assertEqual(result['status'], 'read_stopped')
        self.assertIsNotNone(ctx.state.get('session_work'))

    def test_expired_login_returns_to_waiting_and_preserves_work(self):
        ctx = self.context()
        self.prepare(ctx)
        ctx.call_mcp.reset_mock()
        result = self.invoke(ctx, {'action': 'resume', 'work_id': 'one-qaqc'})
        self.assertEqual(result['status'], 'awaiting_login')
        self.assertEqual(ctx.call_mcp.call_count, 1)
        self.assertIsNotNone(ctx.state.get('session_work'))

    def test_bounded_wait_observes_login_without_reading_sso_snapshot(self):
        ctx = self.context()
        self.prepare(ctx)
        ctx.call_mcp.reset_mock()
        ctx.call_mcp.side_effect = [self.sso(), self.listing(), self.snapshot()]
        from unittest.mock import patch
        with patch('dms_fast_test.session.time.sleep'), patch('dms_fast_test.session.time.monotonic', side_effect=[0, 0, 0, 1]):
            result = self.invoke(ctx, {'action': 'resume', 'work_id': 'one-qaqc', 'wait_seconds': 5})
        self.assertEqual(result['status'], 'search_ui_changed')
        self.assertEqual([c.args[1] for c in ctx.call_mcp.call_args_list], ['list_pages', 'list_pages', 'take_snapshot'])

    def test_bounded_wait_timeout_is_still_normal_pending(self):
        ctx = self.context()
        self.prepare(ctx)
        ctx.call_mcp.reset_mock()
        from unittest.mock import patch
        with patch('dms_fast_test.session.time.monotonic', side_effect=[0, 61]):
            result = self.invoke(ctx, {'action': 'resume', 'work_id': 'one-qaqc', 'wait_seconds': 60})
        self.assertTrue(result['ok'])
        self.assertEqual(result['status'], 'awaiting_login')
        self.assertEqual(ctx.call_mcp.call_count, 1)

    def test_cancellation_uses_no_browser_calls(self):
        ctx = self.context()
        self.prepare(ctx)
        ctx.call_mcp.reset_mock()
        result = self.invoke(ctx, {'action': 'cancel', 'work_id': 'one-qaqc'})
        self.assertEqual(result['status'], 'cancelled')
        self.assertIsNone(ctx.state.get('session_work'))
        ctx.call_mcp.assert_not_called()

    def test_no_work_after_cancellation_is_not_recreated(self):
        ctx = self.context()
        result = self.invoke(ctx, {'action': 'resume', 'work_id': 'one-qaqc'})
        self.assertEqual(result['status'], 'no_pending_work')
        ctx.call_mcp.assert_not_called()

    def test_ambiguous_tabs_stop_without_closing_or_navigating(self):
        ctx = self.context()
        ctx.call_mcp.return_value = {'ok': True, 'result': '## Pages\n2: DMS (https://dms.newtecons.vn/)\n9: DMS (https://dms.newtecons.vn/document/list) [selected]'}
        result = self.invoke(ctx, {'action': 'prepare', 'work_id': 'one-qaqc', 'task': {'kind': 'search_download_one', 'query': 'quy trình qaqc'}})
        self.assertEqual(result['status'], 'ambiguous_tabs')
        self.assertEqual(ctx.call_mcp.call_count, 1)

    def test_refusal_and_truncation_never_retried_or_echoed(self):
        for value in [{'ok': False, 'error': 'private detail'}, {'ok': True, 'truncated': True, 'result': 'private detail'}, RuntimeError('private detail')]:
            ctx = self.context()
            if isinstance(value, Exception):
                ctx.call_mcp.side_effect = value
            else:
                ctx.call_mcp.return_value = value
            result = self.invoke(ctx, {'action': 'prepare', 'work_id': 'one-qaqc', 'task': {'kind': 'search_download_one', 'query': 'quy trình qaqc'}})
            self.assertFalse(result['ok'])
            self.assertEqual(ctx.call_mcp.call_count, 1)
            self.assertNotIn('private detail', str(result))

    def test_dms_denial_does_not_continue(self):
        ctx = self.context()
        ctx.call_mcp.side_effect = [self.listing(), self.snapshot(reader.TEXT + '\nuid=1_22 StaticText "Không có quyền"')]
        result = self.invoke(ctx, {'action': 'prepare', 'work_id': 'one-qaqc', 'task': {'kind': 'search_download_one', 'query': 'quy trình qaqc'}})
        self.assertEqual(result['status'], 'access_denied')
        self.assertEqual(ctx.call_mcp.call_count, 2)

    def test_conflicts_and_changed_server_do_not_replay_task(self):
        ctx = self.context()
        self.prepare(ctx)
        ctx.call_mcp.reset_mock()
        result = self.invoke(ctx, {'action': 'resume', 'work_id': 'another-work'})
        self.assertEqual(result['status'], 'pending_work_conflict')
        ctx.get_config.side_effect = lambda key, default=None: 'another_chrome'
        result = self.invoke(ctx, {'action': 'resume', 'work_id': 'one-qaqc'})
        self.assertEqual(result['status'], 'pending_work_conflict')
        ctx.call_mcp.assert_not_called()

    def test_invalid_tasks_are_rejected_before_state_or_browser(self):
        for task in [{'kind': 'search_download_one', 'query': ''}, {'kind': 'read', 'action': 'open', 'url': reader.URL + '?token=secret'}, {'kind': 'read', 'action': 'open', 'url': reader.URL, 'cookie': 'secret'}, {'kind': 'execute', 'script': 'alert(1)'}]:
            ctx = self.context()
            result = self.invoke(ctx, {'action': 'prepare', 'work_id': 'one-qaqc', 'task': task})
            self.assertFalse(result['ok'])
            self.assertEqual(ctx.state.values, {})
            ctx.call_mcp.assert_not_called()

    def test_wait_limit_and_fields_rejected_before_browser(self):
        for extra in [{'wait_seconds': 61}, {'wait_seconds': True}, {'page_id': 2}, {'mcp_server': 'other'}]:
            ctx = self.context()
            args = {'action': 'prepare', 'work_id': 'one-qaqc', 'task': {'kind': 'search_download_one', 'query': 'quy trình qaqc'}} | extra
            self.assertFalse(self.invoke(ctx, args)['ok'])
            ctx.call_mcp.assert_not_called()

    def test_task_ttl_prevents_old_work_replay(self):
        ctx = self.context()
        self.prepare(ctx)
        ctx.state.values['session_work']['created_at'] = 0
        ctx.call_mcp.reset_mock()
        result = self.invoke(ctx, {'action': 'resume', 'work_id': 'one-qaqc'})
        self.assertEqual(result['status'], 'expired')
        self.assertIsNone(ctx.state.get('session_work'))
        ctx.call_mcp.assert_not_called()

    def test_quoted_logout_text_does_not_authorize_resume(self):
        ctx = self.context()
        text = reader.TEXT.replace('link "Đăng xuất" url="https://dms.newtecons.vn/baseview/logout"', 'StaticText "Đăng xuất"')
        ctx.call_mcp.side_effect = [self.listing(), self.snapshot(text)]
        result = self.invoke(ctx, {'action': 'prepare', 'work_id': 'one-qaqc', 'task': {'kind': 'search_download_one', 'query': 'quy trình qaqc'}})
        self.assertEqual(result['status'], 'awaiting_login')

    def test_profiles_do_not_share_pending_work(self):
        first, second = self.context(), self.context()
        self.prepare(first)
        result = self.invoke(second, {'action': 'resume', 'work_id': 'one-qaqc'})
        self.assertEqual(result['status'], 'no_pending_work')
        second.call_mcp.assert_not_called()


if __name__ == '__main__':
    unittest.main()
