import importlib.util,tempfile,unittest,json,contextlib,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load():
 s=importlib.util.spec_from_file_location('dual_setup',ROOT/'bootstrap.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
FACTS={'node':'recipient-node','chrome':'recipient-chrome','mcp_bin':'one-shared-pinned-package'}
class DualMcpRecipes(unittest.TestCase):
 def test_web_profile_is_generic_separate_and_not_a_dms_plugin_grant(self):
  m=load()
  with tempfile.TemporaryDirectory() as temp:
   h=Path(temp);before=set(h.iterdir());r=m.configuration_recipe(h,'chrome_web',FACTS,mode='web');e=r['connector']
   self.assertEqual(before,set(h.iterdir()));self.assertFalse(r['ready_to_use']);self.assertNotIn('plugin_settings',r)
   self.assertEqual(e['trust'],'untrusted');self.assertIn('upload_file',e['tools']['include']);self.assertIn('select_page',e['tools']['include']);self.assertNotIn('evaluate_script',e['tools']['include'])
   self.assertFalse(any('url-pattern' in a.lower() or 'urlpattern' in a.lower() for a in e['args']))
   self.assertIn('--user-data-dir='+str(h/'browser-profiles/chrome-web-setup'),e['args']);self.assertIn('--no-javascript-evaluation',e['args']);self.assertFalse(e['sampling']['enabled'])
 def test_both_share_package_but_not_profiles_or_dms_binding(self):
  m=load()
  with tempfile.TemporaryDirectory() as temp:
   h=Path(temp);r=m.dual_configuration_recipe(h,'chrome_dms_setup','chrome_web',FACTS);c=r['connectors'];self.assertEqual(set(c),{'chrome_dms_setup','chrome_web'})
   self.assertEqual(c['chrome_web']['args'][0],c['chrome_dms_setup']['args'][0]);self.assertEqual(r['dms_plugin_settings']['mcp_allowlist'],['chrome_dms_setup'])
   a={x for x in c['chrome_web']['args'] if x.startswith('--user-data-dir=')};b={x for x in c['chrome_dms_setup']['args'] if x.startswith('--user-data-dir=')};self.assertTrue(a.isdisjoint(b));self.assertEqual(len(r['create_after_consent']),4);self.assertEqual(list(h.iterdir()),[])
 def test_invalid_mode_and_same_server_names_stop(self):
  m=load()
  with self.assertRaises(ValueError):m.configuration_recipe(Path('.'),'x',FACTS,mode='everything')
  with self.assertRaises(ValueError):m.dual_configuration_recipe(Path('.'),'same','same',FACTS)
 def test_both_cli_is_recipe_only_and_preserves_recipient_config(self):
  m=load()
  with tempfile.TemporaryDirectory() as temp:
   h=Path(temp);cfg=h/'config.yaml';cfg.write_text('fixture: untouched\n');before=cfg.read_bytes()
   # Actual helper CLI, only manifest/audit boundaries replaced by known facts.
   m.verify_bundle=lambda *a:1;m.audit_environment=lambda *a:dict(FACTS)
   with contextlib.redirect_stdout(io.StringIO()):r=m.main(['recipe-both','--home',str(h)])
   self.assertEqual(set(r['connectors']),{'chrome_dms_setup','chrome_web'});self.assertEqual(cfg.read_bytes(),before);self.assertFalse((h/'plugins').exists())
if __name__=='__main__':unittest.main()
