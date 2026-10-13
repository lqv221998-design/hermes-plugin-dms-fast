import json
import unittest
import test_session as sessions
import test_reader as reader


class RoutingTests(unittest.TestCase):
    def test_direct_reader_is_blocked_before_browser(self):
        ctx = sessions.SessionTests().context()
        tools, hooks = {}, {}
        ctx.register_tool.side_effect = lambda **kw: tools.update({kw['name']: kw['handler']})
        ctx.register_hook.side_effect = lambda name, fn: hooks.update({name: fn})
        reader.plugin.register(ctx)
        result = json.loads(tools['dms_fast_read']({'action': 'inspect', 'page_id': 9}))
        self.assertEqual(result.get('status'), 'session_required')
        ctx.call_mcp.assert_not_called()
        self.assertIn('pre_tool_call', hooks)
        blocked = hooks['pre_tool_call'](tool_name='mcp__chrome_dms__click', args={'pageId': 9, 'uid': 'old'})
        self.assertEqual(blocked['action'], 'block')
        self.assertIsNone(hooks['pre_tool_call'](tool_name='read_file', args={'path': 'local.docx'}))
        self.assertEqual(hooks['pre_tool_call'](tool_name='tool_call', args={'calls': [{'name': 'mcp__chrome_dms__click', 'arguments': {}}]})['action'], 'block')


if __name__ == '__main__':
    unittest.main()
