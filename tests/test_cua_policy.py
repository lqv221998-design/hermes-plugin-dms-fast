"""Public Agent hook contract; legacy fixture helpers are not browser authority."""
import copy
import unittest
import test_session as sessions
import test_reader as reader


class CuaPolicyTests(unittest.TestCase):
    def context(self):
        ctx = sessions.SessionTests().context()
        self.hooks = {}
        ctx.register_hook.side_effect = lambda name, fn: self.hooks.update({name: fn})
        reader.plugin.register(ctx)
        return ctx

    def test_reading_and_transfer_have_distinct_controller_policy(self):
        ctx = self.context()
        message = self.hooks['pre_llm_call']()['context']
        self.assertIn('computer_use', message)
        self.assertIn('completed source verification and handoff', message)
        self.assertIn('SHA256', message)
        ctx.call_mcp.assert_not_called()

    def test_new_plugin_download_is_blocked_without_state_changes(self):
        ctx = self.context()
        ctx.state.set('quota_latch', {'daily_limit': 5, 'server': 'chrome_dms'})
        before = copy.deepcopy(ctx.state.values)
        decision = self.hooks['pre_tool_call'](tool_name='dms_fast_session', args={
            'action': 'prepare', 'work_id': 'new-one',
            'task': {'kind': 'search_download_one', 'query': 'fixture'}})
        self.assertIsNotNone(decision, 'Native hook must gate the new transfer')
        self.assertEqual(decision['action'], 'block')
        self.assertIn('computer_use', decision['message'])
        self.assertEqual(ctx.state.values, before)
        ctx.call_mcp.assert_not_called()

    def test_nested_legacy_calls_cannot_start_transfer_or_reset_quota(self):
        ctx = self.context()
        before = copy.deepcopy(ctx.state.values)
        for payload in ({'action': 'prepare', 'task': {'kind': 'search_download_one'}},
                        {'action': 'continue_download'}, {'action': 'resume_after_quota'}):
            result = self.hooks['pre_tool_call'](tool_name='tool_call', args={
                'calls': [{'name': 'dms_fast_session', 'arguments': payload}]})
            self.assertIsNotNone(result)
            self.assertEqual(result['action'], 'block')
        self.assertEqual(ctx.state.values, before)
        ctx.call_mcp.assert_not_called()

    def test_resume_checks_only_an_existing_attempt_and_keeps_history(self):
        ctx = self.context()
        ctx.state.set('session_work', {'work_id': 'old', 'task': {'kind': 'search_download_one'}})
        self.assertEqual(self.hooks['pre_tool_call'](tool_name='dms_fast_session',
            args={'action': 'resume', 'work_id': 'old'})['action'], 'block')
        ctx.state.set('download_old', {'attempted': True, 'file_transfer_attempted': True})
        before = copy.deepcopy(ctx.state.values)
        for action in ('status', 'resume'):
            self.assertIsNone(self.hooks['pre_tool_call'](tool_name='dms_fast_session',
                args={'action': action, 'work_id': 'old'}))
        self.assertEqual(ctx.state.values, before)
        ctx.call_mcp.assert_not_called()

    def test_cancel_requires_work_specific_operator_approval(self):
        ctx = self.context()
        result = self.hooks['pre_tool_call'](tool_name='dms_fast_session',
            args={'action': 'cancel', 'work_id': 'familiar'})
        self.assertEqual(result['action'], 'approve')
        self.assertEqual(result['rule_key'], 'dms-cancel-familiar')
        ctx.call_mcp.assert_not_called()

    def test_schema_and_capabilities_expose_no_new_legacy_transfer(self):
        import json
        ctx = self.context()
        tools = {}
        ctx.register_tool.side_effect = lambda **kw: tools.update({kw['name']: kw})
        reader.plugin.register(ctx)
        tool = tools['dms_fast_session']
        properties = tool['schema']['parameters']['properties']
        self.assertNotIn('search_download_one', properties['task']['properties']['kind']['enum'])
        self.assertNotIn('continue_download', properties['action']['enum'])
        self.assertNotIn('resume_after_quota', properties['action']['enum'])
        result = json.loads(tool['handler']({'action': 'capabilities', 'work_id': 'cap'}))
        self.assertEqual(result['capabilities']['download_controller'], 'computer_use')
        self.assertFalse(result['capabilities']['plugin_new_downloads_enabled'])
        ctx.call_mcp.assert_not_called()

    def test_exact_ma_hieu_remains_bound_when_so_hieu_is_a_different_number(self):
        from unittest.mock import patch
        from test_executor import ExecutorTests
        text = reader.TEXT.replace('StaticText "Số hiệu"', 'StaticText "Mã hiệu"')
        text += '\nuid=8_1 StaticText "Số hiệu"\nuid=8_2 StaticText "012/2024/QD"\n'
        with patch.object(reader, 'TEXT', text):
            ExecutorTests().test_completed_file_is_copied_hashed_and_reused_without_download()


if __name__ == '__main__':
    unittest.main()
