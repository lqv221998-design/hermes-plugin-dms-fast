import unittest
import test_reader as reader

plugin, TEXT, URL = reader.plugin, reader.TEXT, reader.URL


class ContractTests(unittest.TestCase):
    def context(self, text=TEXT):
        return reader.ReaderTests().context(text)

    def test_handler_rejects_unknown_or_inapplicable_fields_before_mcp(self):
        cases = [None, [], {'action': 'inspect', 'page_id': 1, 'url': URL},
                 {'action': 'open', 'page_id': 1},
                 {'action': 'inspect', 'page_id': 1, 'uid': 'old_uid'},
                 {'action': 'inspect', 'page_id': 1, 'expected_code': 42}]
        for args in cases:
            with self.subTest(args=args):
                ctx = self.context()
                result = plugin.run(ctx, args)
                self.assertFalse(result['ok'])
                ctx.call_mcp.assert_not_called()

    def test_server_settings_are_resolved_per_context_a_b_a(self):
        for server in ('company_chrome_a', 'company_chrome_b', 'company_chrome_a'):
            ctx = self.context()
            ctx.get_config.side_effect = lambda key, default=None: server if key == 'mcp_server' else default
            result = plugin.run(ctx, {'action': 'inspect', 'page_id': 9})
            self.assertTrue(result['ok'])
            self.assertEqual(ctx.call_mcp.call_args.args[0], server)
            self.assertEqual(ctx.call_mcp.call_args.args[2], {'pageId': 9})

    def test_invalid_server_setting_stops_without_mcp(self):
        for value in (None, [], '', 'https://remote.example', '../other'):
            ctx = self.context()
            ctx.get_config.side_effect = lambda key, default=None: value if key == 'mcp_server' else default
            result = plugin.run(ctx, {'action': 'inspect', 'page_id': 9})
            self.assertFalse(result['ok'])
            ctx.call_mcp.assert_not_called()


    def test_expected_source_fields_are_checked_not_ignored(self):
        for key, value in (('expected_code', 'QT-KT-08'), ('expected_title', 'Nguồn khác')):
            ctx = self.context()
            result = plugin.run(ctx, {'action': 'open', 'page_id': 1, 'url': URL, key: value})
            self.assertFalse(result['ok'])
            self.assertEqual(ctx.call_mcp.call_count, 1)
        ctx = self.context()
        result = plugin.run(ctx, {'action': 'open', 'page_id': 1, 'url': URL,
                                  'expected_code': 'QT-KT-07', 'expected_title': 'Quy trình'})
        self.assertTrue(result['ok'])
        self.assertEqual(result['source_identity'], 'matched_expected_fields')

    def test_empty_destination_heading_does_not_verify_source(self):
        text = TEXT.replace('RootWebArea "Quy trình - Newtecons"', 'RootWebArea ""')
        text = text.replace('uid=1_2 heading "Quy trình" level="1"', '')
        ctx = self.context(text)
        result = plugin.run(ctx, {'action': 'open', 'page_id': 1, 'url': URL})
        self.assertFalse(result['ok'])

    def test_transport_errors_are_not_retried_or_echoed(self):
        ctx = self.context()
        ctx.call_mcp.side_effect = RuntimeError('private_transport_detail_must_not_escape')
        result = plugin.run(ctx, {'action': 'inspect', 'page_id': 1})
        self.assertFalse(result['ok'])
        self.assertNotIn('private_transport_detail_must_not_escape', str(result))
        self.assertEqual(ctx.call_mcp.call_count, 1)


if __name__ == '__main__':
    unittest.main()
