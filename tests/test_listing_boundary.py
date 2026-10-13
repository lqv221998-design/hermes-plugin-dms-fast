import unittest
import test_session as sessions


class ListingBoundaryTests(unittest.TestCase):
    def test_failure_reports_only_listing_shape_never_auth_content(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        ctx.call_mcp.return_value = {'ok': True, 'result': {'unknown_format': 'never-echo-boundary'}}
        result = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'boundary', 'task': {'kind': 'search_download_one', 'query': 'quản lý chất lượng'}})
        self.assertFalse(result['ok'])
        self.assertEqual(result.get('listing_diagnostic'), {'type': 'dict', 'pages_section': False, 'starts_with_pages': False, 'note_prefix': False})
        self.assertNotIn('never-echo-boundary', str(result) + str(ctx.state.values))
        self.assertEqual(ctx.call_mcp.call_count, 1)

    def test_documented_reconnect_note_and_extension_section_are_not_page_rows(self):
        pages = sessions.reader.plugin.session.pages
        text = ('Note: the browser was restarted or reconnected since the last call. Page ids have changed. Call list_pages to see open pages.\n'
                '## Pages\n9: DMS (https://dms.newtecons.vn/) [selected]\n'
                '## Extension Pages\n90: helper (chrome-extension://example/popup.html)')
        self.assertEqual(pages(text), [{'id': 9, 'url': 'https://dms.newtecons.vn/', 'login': False, 'dms': True}])


if __name__ == '__main__':
    unittest.main()
