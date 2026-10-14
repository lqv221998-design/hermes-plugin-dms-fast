import copy
import tempfile
import unittest
from pathlib import Path
import test_session as sessions
import test_reader as reader


class UIAdapterTests(unittest.TestCase):
    def test_chart_menu_uses_its_own_live_label_and_reads_department_route(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        before = reader.TEXT + '\nuid=8_1 link "Xem dạng biểu đồ, hình ảnh" url="https://dms.newtecons.vn/document/dept"\n'
        after = before.replace(reader.URL, 'https://dms.newtecons.vn/document/dept')
        ctx.call_mcp.side_effect = [helper.listing(),helper.snapshot(before),{'ok':True,'result':'clicked'},helper.snapshot(after)]
        result = helper.invoke(ctx, {'action':'inspect','work_id':'one-qaqc','menu':'charts'})
        self.assertEqual(result['status'], 'observed')
        self.assertEqual(result['ui_observation']['url'], 'https://dms.newtecons.vn/document/dept')

    def test_menu_target_diagnostics_never_execute_or_echo_auth_queries(self):
        adapter = __import__(reader.plugin.__name__ + '.adapter', fromlist=['observe'])
        text = reader.TEXT + '\nuid=7_1 link "Tài liệu hướng dẫn" url="https://dms.newtecons.vn/document/download/manual.pdf"\n'
        target = adapter.observe(text)['menu_targets'][0]
        self.assertEqual(target['target_kind'], 'same_origin_unverified_route')
        self.assertEqual(target['url'], 'https://dms.newtecons.vn/document/download/manual.pdf')
        self.assertFalse(target['navigation_authorized'])
        secret = text.replace('manual.pdf','manual.pdf?token=SECRET')
        target = adapter.observe(secret)['menu_targets'][0]
        self.assertNotIn('url', target)
        self.assertNotIn('SECRET', str(adapter.observe(secret)))

    def test_guide_target_url_is_checked_even_after_other_ax_attributes(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        text = reader.TEXT + '\nuid=8_1 link "Tài liệu hướng dẫn" description="manual" url="https://outside.example/manual"\n'
        ctx.call_mcp.side_effect = [helper.listing(),helper.snapshot(text)]
        result = helper.invoke(ctx, {'action':'inspect','work_id':'one-qaqc','menu':'guides'})
        self.assertEqual(result.get('error_code'), 'guide_target_unverified')
        self.assertEqual(ctx.call_mcp.call_count, 2)

    def test_guides_opens_live_no_href_control_but_requires_visible_new_content(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        before = reader.TEXT + '\nuid=8_1 link "Tài liệu hướng dẫn"\n'
        after = before + '\nuid=9_1 dialog "Tài liệu hướng dẫn"\n'
        ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(before), {'ok':True,'result':'clicked'}, helper.snapshot(after)]
        result = helper.invoke(ctx, {'action':'inspect','work_id':'one-qaqc','menu':'guides'})
        self.assertEqual(result['status'], 'observed')
        self.assertIn('Tài liệu hướng dẫn',result['ui_observation']['dialogs'])
        ctx.call_mcp.reset_mock()
        ctx.call_mcp.side_effect = [helper.listing(),helper.snapshot(before),{'ok':True,'result':'clicked'},helper.snapshot(before)]
        result = helper.invoke(ctx, {'action':'inspect','work_id':'one-qaqc','menu':'guides'})
        self.assertFalse(result['ok'])

    def test_grid_column_headers_are_not_document_metadata(self):
        adapter = __import__(reader.plugin.__name__ + '.adapter', fromlist=['observe'])
        text = reader.TEXT.replace(reader.URL, 'https://dms.newtecons.vn/document/list') + '\nuid=8_8 StaticText "Mã hiệu"\nuid=8_9 StaticText "Tên văn bản"\n'
        self.assertEqual(adapter.observe(text)['metadata'], {})

    def test_read_menu_navigates_only_exact_live_link_and_reads_back(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        before = reader.TEXT + '\nuid=8_1 link "Đặt lịch họp/xe" url="https://dms.newtecons.vn/schedule/booking"\n'
        after = before.replace(reader.URL, 'https://dms.newtecons.vn/schedule/booking')
        ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(before), {'ok': True, 'result': 'clicked'}, helper.snapshot(after)]
        result = helper.invoke(ctx, {'action':'inspect','work_id':'one-qaqc','menu':'booking'})
        self.assertEqual(result['status'], 'observed')
        self.assertEqual(result['ui_observation']['url'], 'https://dms.newtecons.vn/schedule/booking')
        self.assertEqual(ctx.call_mcp.call_args_list[2].args[2]['uid'], '8_1')
        self.assertEqual(ctx.state.values, {})

    def test_menu_inspect_rejects_pending_and_unknown_business_action_before_click(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        helper.prepare(ctx)
        ctx.call_mcp.reset_mock()
        result = helper.invoke(ctx, {'action':'inspect','work_id':'one-qaqc','menu':'booking'})
        self.assertEqual(result['status'], 'pending_work_conflict')
        ctx.call_mcp.assert_not_called()
        result = helper.invoke(ctx, {'action':'inspect','work_id':'one-qaqc','menu':'delete'})
        self.assertFalse(result['ok'])
        ctx.call_mcp.assert_not_called()

    def test_navigation_discovery_reports_only_safe_observed_read_menu_routes(self):
        adapter = __import__(reader.plugin.__name__ + '.adapter', fromlist=['observe'])
        text = reader.TEXT + '\nuid=7_1 link "Đặt lịch họp/xe" url="https://dms.newtecons.vn/booking"\nuid=7_2 link "Đăng xuất" url="https://dms.newtecons.vn/baseview/logout"\nuid=7_3 link "Tài liệu hướng dẫn" url="https://sso.newtecons.vn/?token=SECRET"\nuid=7_4 link "Phòng ban" url="https://dms.newtecons.vn/department"\n'
        result = adapter.observe(text)
        self.assertEqual(result['navigation_links'], [
            {'label': 'Đặt lịch họp/xe', 'url': 'https://dms.newtecons.vn/booking'},
            {'label': 'Phòng ban', 'url': 'https://dms.newtecons.vn/department'}])
        self.assertNotIn('SECRET', str(result))
        self.assertNotIn('7_1', str(result))

    def test_transport_failure_reports_stage_without_echoing_upstream_secrets(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(),
                                    {'ok': False, 'error': 'password=DO-NOT-RETURN token=SECRET'}]
        result = helper.invoke(ctx, {'action': 'inspect', 'work_id': 'one-qaqc', 'section': 'info'})
        self.assertEqual(result['status'], 'browser_unavailable_or_refused')
        self.assertEqual(result['failed_mcp_tool'], 'click')
        self.assertEqual(result['plugin_version'], __import__(reader.plugin.__name__ + '.session', fromlist=['VERSION']).VERSION)
        self.assertNotIn('DO-NOT-RETURN', str(result))
        self.assertNotIn('SECRET', str(result))
        self.assertEqual(ctx.call_mcp.call_count, 3)

    def test_status_exposes_two_stage_intent_without_browser_calls(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        ctx.state.set('download_one-qaqc', {'attempted': True, 'file_transfer_attempted': True,
                                          'selected_file_name': 'QT-KT-07.docx'})
        result = helper.invoke(ctx, {'action': 'status', 'work_id': 'one-qaqc'})
        self.assertTrue(result['file_transfer_attempted'])
        self.assertEqual(result['download_phase'], 'transfer_attempted')
        ctx.call_mcp.assert_not_called()

    def test_list_opener_returns_selection_required_instead_of_waiting_for_file(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        with tempfile.TemporaryDirectory() as root:
            task = {'kind': 'search_download_one', 'query': 'Quy trình', 'url': reader.URL,
                    'expected_title': 'Quy trình', 'expected_code': 'QT-KT-07', 'output_dir': root}
            ctx.get_config.side_effect = lambda key, default=None: root if key == 'download_dir' else 0 if key == 'download_wait_seconds' else default
            detail = reader.TEXT + '\nuid=1_20 StaticText "Lần ban hành"\nuid=1_21 StaticText "1"\nuid=1_22 link "Tải về" url="javascript:;"\n'
            inner = detail + '\nuid=9_1 heading "QT-KT-07.docx" level="3"\nuid=9_2 link "Tải về Download" url="javascript:;"\n'
            ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(detail), {'ok': True, 'result': 'clicked'}, helper.snapshot(inner)]
            result = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'one-qaqc', 'task': task})
            self.assertEqual(result['status'], 'download_selection_required')
            self.assertEqual(result['file_candidates'], ['QT-KT-07.docx'])
            self.assertEqual(sum(c.args[1] == 'click' for c in ctx.call_mcp.call_args_list), 1)
            self.assertFalse(ctx.state.get('download_one-qaqc').get('file_transfer_attempted', False))

    def test_legacy_file_continuation_is_blocked_before_browser(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        hooks = {}
        ctx.register_hook.side_effect = lambda name, fn: hooks.update({name: fn})
        reader.plugin.register(ctx)
        args = {'action': 'continue_download', 'work_id': 'one-qaqc', 'expected_file_name': 'QT-KT-07.docx'}
        result = hooks['pre_tool_call'](tool_name='dms_fast_session', args=args)
        self.assertIsNotNone(result)
        self.assertEqual(result['action'], 'block')
        ctx.call_mcp.assert_not_called()

    def test_two_stage_download_continues_inner_link_once_and_keeps_legacy_attempt(self):
        import zipfile
        helper = sessions.SessionTests()
        ctx = helper.context()
        with tempfile.TemporaryDirectory() as root:
            downloads, output = Path(root) / 'downloads', Path(root) / 'output'
            downloads.mkdir(); output.mkdir()
            task = {'kind': 'search_download_one', 'query': 'Quy trình', 'url': reader.URL,
                    'expected_title': 'Quy trình', 'expected_code': 'QT-KT-07', 'output_dir': str(output)}
            ctx.get_config.side_effect = lambda key, default=None: str(downloads) if key == 'download_dir' else 0 if key == 'download_wait_seconds' else default
            saved = {'server': 'chrome_dms', 'source': {'url': reader.URL, 'title': 'Quy trình', 'code': 'QT-KT-07', 'revision': '1', 'effective_date': '21/12/2022'},
                     'task': task, 'attempted': True, 'download_dir': str(downloads), 'before': {}, 'started_at': 123}
            ctx.state.set('download_one-qaqc', saved)
            helper.prepare(ctx, task)
            listing = reader.TEXT + '\nuid=9_1 heading "QT-KT-07.docx" level="3"\nuid=9_2 link "Tải về Download" url="javascript:;"\n'
            responses = iter([helper.listing(), helper.snapshot(listing), {'ok': True, 'result': 'clicked'}, helper.snapshot(listing)])
            def mcp(server, name, payload, **kw):
                if name == 'click':
                    self.assertTrue(ctx.state.get('download_one-qaqc')['file_transfer_attempted'])
                    self.assertEqual(payload['uid'], '9_2')
                    with zipfile.ZipFile(downloads / 'QT-KT-07.docx', 'w') as z:
                        z.writestr('test.txt', 'fixture only')
                return next(responses)
            ctx.call_mcp.reset_mock(); ctx.call_mcp.side_effect = mcp
            result = helper.invoke(ctx, {'action': 'continue_download', 'work_id': 'one-qaqc', 'expected_file_name': 'QT-KT-07.docx'})
            self.assertEqual(result['status'], 'completed')
            state = ctx.state.get('download_one-qaqc')
            self.assertEqual(state['started_at'], 123)
            self.assertTrue(state['attempted'])
            ctx.call_mcp.reset_mock(); ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(listing)]
            repeated = helper.invoke(ctx, {'action': 'prepare', 'work_id': 'one-qaqc', 'task': task})
            self.assertEqual(repeated['status'], 'source_revision_changed')
            self.assertNotIn('click', [c.args[1] for c in ctx.call_mcp.call_args_list])

    def test_section_read_back_preserves_work_and_never_claims_fulltext(self):
        helper = sessions.SessionTests()
        for section, uid in [('info', '1_3'), ('original', '1_4')]:
            ctx = helper.context()
            helper.prepare(ctx, {'kind': 'read', 'action': 'open', 'url': reader.URL})
            before = copy.deepcopy(ctx.state.values)
            ctx.call_mcp.reset_mock()
            ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(), {'ok': True, 'result': 'clicked'}, helper.snapshot()]
            result = helper.invoke(ctx, {'action': 'inspect', 'work_id': 'one-qaqc', 'section': section})
            self.assertEqual(result['status'], 'observed')
            self.assertFalse(result['ui_observation']['full_document_read'])
            self.assertEqual(ctx.call_mcp.call_args_list[2].args[2]['uid'], uid)
            self.assertEqual(ctx.state.values, before)

    def test_capabilities_are_explicit_without_browser_or_state_writes(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        result = helper.invoke(ctx, {'action': 'capabilities', 'work_id': 'catalog'})
        self.assertEqual(result['status'], 'capabilities')
        self.assertIn('inspect', result['capabilities']['supported'])
        self.assertIn('upload', result['capabilities']['gated_not_implemented'])
        self.assertFalse(result['capabilities']['all_dms_functions_verified'])
        ctx.call_mcp.assert_not_called()
        self.assertEqual(ctx.state.values, {})

    def test_inspection_preserves_pending_work_attempt_and_quota(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        helper.prepare(ctx)
        ctx.state.set('quota_latch', {'server': 'chrome_dms'})
        before = copy.deepcopy(ctx.state.values)
        ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot()]
        result = helper.invoke(ctx, {'action': 'inspect', 'work_id': 'one-qaqc'})
        self.assertEqual(result['status'], 'observed')
        self.assertEqual(result['ui_observation']['url'], reader.URL)
        self.assertEqual(ctx.state.values, before)
        self.assertEqual([c.args[1] for c in ctx.call_mcp.call_args_list][-2:], ['list_pages', 'take_snapshot'])

    def test_uncertain_download_reports_visible_next_step_without_reclick(self):
        helper = sessions.SessionTests()
        ctx = helper.context()
        with tempfile.TemporaryDirectory() as root:
            task = {'kind': 'search_download_one', 'query': 'Quy trình', 'url': reader.URL,
                    'expected_title': 'Quy trình', 'expected_code': 'QT-KT-07', 'output_dir': root}
            ctx.get_config.side_effect = lambda key, default=None: root if key == 'download_dir' else default
            saved = {'server': 'chrome_dms', 'source': {'url': reader.URL, 'code': 'QT-KT-07'},
                     'task': task, 'attempted': True, 'download_dir': root, 'before': {}}
            ctx.state.set('download_one-qaqc', saved)
            helper.prepare(ctx, task)
            ctx.call_mcp.reset_mock()
            modal = reader.TEXT + '\nuid=9_1 dialog "Chọn tệp"\nuid=9_2 button "Tải văn bản"\nuid=9_3 textbox "Mật khẩu" value="DO-NOT-RETURN"\n'
            ctx.call_mcp.side_effect = [helper.listing(), helper.snapshot(modal)]
            result = helper.invoke(ctx, {'action': 'resume', 'work_id': 'one-qaqc'})
            self.assertEqual(result['status'], 'download_unconfirmed')
            self.assertIn('ui_observation', result)
            self.assertIn({'role': 'button', 'label': 'Tải văn bản'}, result['ui_observation']['controls'])
            self.assertEqual(result['ui_observation']['dialogs'], ['Chọn tệp'])
            self.assertNotIn('DO-NOT-RETURN', str(result))
            self.assertNotIn('9_2', str(result))
            self.assertEqual([c.args[1] for c in ctx.call_mcp.call_args_list], ['list_pages', 'take_snapshot'])
            self.assertEqual(ctx.state.get('download_one-qaqc'), saved)


if __name__ == '__main__':
    unittest.main()
