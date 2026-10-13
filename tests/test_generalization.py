"""Recipient configuration tests; not a claim of physical cross-OS coverage."""
import importlib
import unittest
import tempfile
import test_reader as reader
import test_session as sessions


class GeneralizationTests(unittest.TestCase):
    def test_url_only_page_listing_opens_one_tab_and_keeps_auth_query_private(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        sso = {'ok': True, 'result': '## Pages\n17: https://sso.newtecons.vn/realms/Newtecons/protocol/openid-connect/auth?state=never-retain [selected]'}
        ctx.call_mcp.side_effect = [{'ok': True, 'result': '## Pages\n3: about:blank [selected]'}, sso, sso]
        result = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'cold', 'task': {'kind': 'search_download_one', 'query': 'Quy trình'}})
        self.assertEqual(result['status'], 'awaiting_login')
        self.assertEqual(sum(c.args[1] == 'new_page' for c in ctx.call_mcp.call_args_list), 1)
        self.assertNotIn('never-retain', str(result) + str(ctx.state.values))

    def test_attempt_cannot_be_reused_after_recipient_changes_server(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        with tempfile.TemporaryDirectory() as root:
            task = {'kind': 'search_download_one', 'query': 'Quy trình', 'url': reader.URL, 'expected_title': 'Quy trình', 'expected_code': 'QT-KT-07', 'output_dir': root}
            ctx.get_config.side_effect = lambda key, default=None: root if key == 'download_dir' else 'new_chrome' if key == 'mcp_server' else default
            ctx.state.set('download_recipient', {'server': 'old_chrome', 'task': task, 'attempted': True})
            ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot()]
            result = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'recipient', 'task': task})
            self.assertEqual(result['status'], 'pending_work_conflict')
            self.assertEqual([c.args[1] for c in ctx.call_mcp.call_args_list], ['list_pages', 'take_snapshot'])

    def test_selected_download_requires_explicit_recipient_directory_before_browser(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        with tempfile.TemporaryDirectory() as root:
            task = {'kind': 'search_download_one', 'query': 'Quy trình', 'url': reader.URL, 'expected_title': 'Quy trình', 'expected_code': 'QT-KT-07', 'output_dir': root}
            result = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'recipient', 'task': task})
            self.assertEqual(result['status'], 'configuration_required')
            self.assertEqual(result['missing_fields'], ['download_dir'])
            ctx.call_mcp.assert_not_called()

    def test_guard_uses_recipient_server_alias_and_hermes_sanitization(self):
        for server in ('chrome_team', 'chrome-team', 'chrome.team'):
            with self.subTest(server=server):
                ctx = sessions.SessionTests().context()
                ctx.get_config.side_effect = lambda key, default=None: server if key == 'mcp_server' else default
                hooks = {}
                ctx.register_hook.side_effect = lambda name, fn: hooks.update({name: fn})
                reader.plugin.register(ctx)
                exposed = 'mcp__' + server.replace('-', '_').replace('.', '_') + '__click'
                self.assertEqual(hooks['pre_tool_call'](tool_name=exposed, args={})['action'], 'block')
                self.assertIsNone(hooks['pre_tool_call'](tool_name='mcp__other__click', args={}))
                ctx.call_mcp.return_value = sessions.SessionTests().sso()
                result = sessions.SessionTests().invoke(ctx, {'action': 'prepare', 'work_id': 'alias', 'task': {'kind': 'search_download_one', 'query': 'Quy trình'}})
                self.assertEqual(result['status'], 'awaiting_login')
                self.assertEqual(ctx.call_mcp.call_args.args[0], server)


if __name__ == '__main__':
    unittest.main()
