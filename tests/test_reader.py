import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1] / 'dms-fast'
spec = importlib.util.spec_from_file_location('dms_fast_test', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
assert spec is not None and spec.loader is not None
plugin = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = plugin
# This fails RED until the real plugin exists.
spec.loader.exec_module(plugin)
URL = 'https://dms.newtecons.vn/document/detail/cab9eb52-bb54-4e32-ba4a-766717c488ac'
TEXT = f'''uid=1_0 RootWebArea "Quy trình - Newtecons" url="{URL}"
uid=1_1 link "Đăng xuất" url="https://dms.newtecons.vn/baseview/logout"
uid=1_2 heading "Quy trình" level="1"
uid=1_3 link "Thông tin" url="javascript:;"
uid=1_4 link "Văn bản gốc" url="javascript:;"
uid=1_5 StaticText "Số hiệu"
uid=1_6 StaticText "QT-KT-07"
uid=1_7 StaticText "Ngày hiệu lực"
uid=1_8 StaticText "21/12/2022"
uid=1_9 StaticText "Tình trạng"
uid=1_10 StaticText "Còn hiệu lực"
'''

class ReaderTests(unittest.TestCase):
    def context(self, text=TEXT):
        ctx = Mock()
        ctx.get_config.side_effect = lambda key, default=None: default
        ctx.call_mcp.return_value = {'ok': True, 'result': '## Latest page snapshot\n'+text}
        return ctx

    def test_inspect_is_one_call_and_extracts_metadata(self):
        ctx = self.context()
        result = plugin.run(ctx, {'action': 'inspect', 'page_id': 1})
        self.assertTrue(result['ok'])
        self.assertEqual(ctx.call_mcp.call_count, 1)
        self.assertEqual(result['page']['metadata']['Số hiệu'], 'QT-KT-07')
        self.assertFalse(result['page']['full_document_read'])

    def test_invalid_action_url_page_fail_without_calls(self):
        for args in [{'action':'delete','page_id':1}, {'action':'open','page_id':1,'url':URL+'?token=x'}, {'action':'inspect','page_id':True}, {'action':'inspect','page_id':-1}, {'action':'inspect'}]:
            ctx = self.context()
            self.assertFalse(plugin.run(ctx, args)['ok'])
            ctx.call_mcp.assert_not_called()

    def test_denial_stops_without_retry_or_fallback(self):
        ctx = self.context()
        ctx.call_mcp.return_value = {'ok':False, 'error':'Not approved'}
        result = plugin.run(ctx, {'action':'original','page_id':1})
        self.assertFalse(result['ok'])
        self.assertEqual(ctx.call_mcp.call_count,1)

    def test_original_uses_current_uid_and_reads_back(self):
        ctx = self.context()
        result = plugin.run(ctx, {'action':'original','page_id':1})
        self.assertTrue(result['ok'])
        self.assertEqual(ctx.call_mcp.call_count,3)
        self.assertEqual(ctx.call_mcp.call_args_list[1].args[:3], ('chrome_dms','click',{'uid':'1_4','pageId':1}))
        self.assertEqual(result['verification'], 'same_source_after_tab_click; render_not_verified')

    def test_no_click_on_login_offsite_denial_or_ambiguous_tab(self):
        for text in [TEXT.replace('Đăng xuất','Đăng nhập'), TEXT.replace(URL,'https://example.com/'), TEXT+'\nuid=1_11 StaticText "Không có quyền"', TEXT+'\nuid=1_12 link "Văn bản gốc" url="javascript:;"']:
            ctx = self.context(text)
            self.assertFalse(plugin.run(ctx, {'action':'original','page_id':1})['ok'])
            self.assertEqual(ctx.call_mcp.call_count,1)

    def test_wrong_source_after_open_is_failure(self):
        ctx = self.context()
        target = 'https://dms.newtecons.vn/document/list'
        result = plugin.run(ctx, {'action':'open','page_id':1,'url':target})
        self.assertFalse(result['ok'])
        self.assertEqual(ctx.call_mcp.call_count,3)

    def test_truncated_snapshot_fails(self):
        ctx = self.context()
        ctx.call_mcp.return_value['truncated'] = True
        self.assertFalse(plugin.run(ctx, {'action':'inspect','page_id':1})['ok'])
        self.assertEqual(ctx.call_mcp.call_count,1)

if __name__ == '__main__':
    unittest.main()
