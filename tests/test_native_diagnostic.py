import unittest
import test_session as session


class NativeDiagnosticTests(unittest.TestCase):
    def test_unsupported_listing_has_static_diagnostic_without_echo(self):
        fixture = session.SessionTests()
        ctx = fixture.context()
        ctx.call_mcp.return_value = {'ok': True, 'result': '## Pages\n0: javascript:unapproved\n2: https://sso.newtecons.vn/login?state=never-echo-this'}
        result = fixture.invoke(ctx, {'action': 'prepare', 'work_id': 'diagnostic', 'task': {'kind': 'search_download_one', 'query': 'quản lý chất lượng'}})
        self.assertEqual(result.get('error_code'), 'unsupported_page_url')
        self.assertNotIn('never-echo-this', str(result))
        self.assertEqual(ctx.call_mcp.call_count, 1)

    def test_chrome_internal_tab_does_not_break_normal_login_wait(self):
        fixture = session.SessionTests()
        ctx = fixture.context()
        ctx.call_mcp.return_value = {'ok': True, 'result': '## Pages\n0: chrome://newtab/\n2: https://sso.newtecons.vn/login?state=never-echo-this'}
        result = fixture.invoke(ctx, {'action': 'prepare', 'work_id': 'internal-tab', 'task': {'kind': 'search_download_one', 'query': 'quản lý chất lượng'}})
        self.assertEqual(result['status'], 'awaiting_login')
        self.assertTrue(result['ok'])
        self.assertEqual(ctx.call_mcp.call_count, 1)
        self.assertNotIn('never-echo-this', str(result) + str(ctx.state.values))


if __name__ == '__main__':
    unittest.main()
