"""Regression: explicit entry guidance without changing pending/attempt/quota."""
import copy
import unittest
import test_session as sessions
import test_reader as reader

class EntryGuidance(unittest.TestCase):
    def context(self):return sessions.SessionTests().context()
    def invoke(self,ctx,args):return sessions.SessionTests().invoke(ctx,args)
    def saved(self,ctx,created=0):
        ctx.state.set('session_work',{'work_id':'old-work','server':'chrome_dms',
            'task':{'kind':'read','action':'open','url':reader.URL},'created_at':created})
    def test_expired_inspect_conflict_explains_prepare_without_mutating_old_work(self):
        ctx=self.context();self.saved(ctx);before=copy.deepcopy(ctx.state.values)
        r=self.invoke(ctx,{'action':'inspect','work_id':'new-read'})
        self.assertEqual(r['status'],'pending_work_conflict')
        self.assertTrue(r.get('pending_work_expired',False))
        self.assertEqual(r.get('next_action'),'prepare')
        self.assertEqual(ctx.state.values,before);ctx.call_mcp.assert_not_called()
    def test_expired_status_is_observational_and_exposes_ttl(self):
        ctx=self.context();self.saved(ctx);before=copy.deepcopy(ctx.state.values)
        r=self.invoke(ctx,{'action':'status','work_id':'old-work'})
        self.assertTrue(r.get('pending_work_expired',False))
        self.assertEqual(r.get('work_ttl_seconds'),86400)
        self.assertEqual(ctx.state.values,before);ctx.call_mcp.assert_not_called()
    def test_cold_inspect_points_to_home_prepare_without_opening_a_tab(self):
        ctx=self.context();ctx.call_mcp.return_value={'ok':True,'result':'## Pages\n0: about:blank'}
        r=self.invoke(ctx,{'action':'inspect','work_id':'entry'})
        self.assertEqual(r['status'],'browser_not_ready')
        self.assertEqual(r.get('reason'),'no_dms_or_login_tab')
        self.assertEqual(r.get('next_action'),'prepare')
        self.assertEqual(r.get('suggested_task'),{'kind':'read','action':'open','url':'https://dms.newtecons.vn/'})
        self.assertEqual(ctx.call_mcp.call_count,1);self.assertEqual(ctx.state.values,{})
    def test_live_pending_conflict_never_advises_overwrite_or_new_prepare(self):
        import time
        ctx=self.context();self.saved(ctx,time.time());before=copy.deepcopy(ctx.state.values)
        r=self.invoke(ctx,{'action':'inspect','work_id':'new-read'})
        self.assertFalse(r.get('pending_work_expired',True))
        self.assertEqual(r.get('next_action'),'status')
        self.assertEqual(r.get('next_work_id'),'old-work')
        self.assertEqual(ctx.state.values,before);ctx.call_mcp.assert_not_called()
    def test_prepare_home_replaces_only_expired_work_not_attempt_or_quota(self):
        ctx=self.context();self.saved(ctx)
        ctx.state.set('download_old-work',{'attempted':True,'file_transfer_attempted':True})
        ctx.state.set('quota_latch',{'server':'chrome_dms','scope':'old-download'})
        preserved=copy.deepcopy({k:v for k,v in ctx.state.values.items() if k!='session_work'})
        helper=sessions.SessionTests();text=reader.TEXT.replace(reader.URL,'https://dms.newtecons.vn/')
        listing={'ok':True,'result':'## Pages\n9: Home (https://dms.newtecons.vn/) [selected]'}
        ctx.call_mcp.side_effect=[listing,helper.snapshot(text),helper.snapshot(text)]
        r=self.invoke(ctx,{'action':'prepare','work_id':'new-read','task':{'kind':'read','action':'open','url':'https://dms.newtecons.vn/'}})
        self.assertEqual(r['status'],'completed')
        self.assertIsNone(ctx.state.get('session_work'))
        self.assertEqual({k:v for k,v in ctx.state.values.items() if k!='session_work'},preserved)
        self.assertEqual([c.args[1] for c in ctx.call_mcp.call_args_list],['list_pages','take_snapshot','take_snapshot'])

    def test_expired_download_diagnostics_do_not_advertise_a_new_attempt(self):
        ctx=self.context();self.saved(ctx)
        ctx.state.values['session_work']['task']={'kind':'search_download_one','query':'fixture'}
        ctx.state.set('download_old-work',{'attempted':True,'file_transfer_attempted':True})
        ctx.state.set('quota_latch',{'server':'chrome_dms'})
        before=copy.deepcopy(ctx.state.values)
        r=self.invoke(ctx,{'action':'inspect','work_id':'new-read'})
        self.assertTrue(r['pending_work_expired'])
        self.assertEqual(r['next_action'],'status')
        self.assertEqual(r['next_work_id'],'old-work')
        self.assertEqual(ctx.state.values,before);ctx.call_mcp.assert_not_called()

    def test_expired_foreign_server_is_not_automatically_rebound(self):
        ctx=self.context();self.saved(ctx)
        ctx.state.values['session_work']['server']='other_chrome'
        before=copy.deepcopy(ctx.state.values)
        r=self.invoke(ctx,{'action':'inspect','work_id':'new-read'})
        self.assertEqual(r['next_action'],'status')
        self.assertEqual(ctx.state.values,before);ctx.call_mcp.assert_not_called()

if __name__=='__main__':unittest.main()
