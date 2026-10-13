import importlib.util,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SetupBootstrap(unittest.TestCase):
 def test_node_support_rule_is_explicit_and_rejects_eol_versions(self):
  path=ROOT/'bootstrap.py'
  self.assertTrue(path.exists(),'Missing bootstrap entry point')
  spec=importlib.util.spec_from_file_location('dms_bootstrap',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  for version,expected in [('20.20.2',False),('22.11.0',False),('22.12.0',True),('24.21.0',True),('25.9.0',False),('26.7.0',True)]:
   with self.subTest(version=version):self.assertEqual(mod.node_supported(version),expected)

 def test_missing_tools_plan_is_read_only_and_names_pm_packages(self):
  spec=importlib.util.spec_from_file_location('dms_bootstrap',ROOT/'bootstrap.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  self.assertTrue(hasattr(mod,'plan_from_facts'),'Missing diagnostic plan')
  result=mod.plan_from_facts({'node_version':None,'npm_cli':None,'chrome':None,'python_supported':False,'hermes_api':False})
  self.assertEqual(result['pm_packages'],['python','node','chromium'])
  self.assertTrue(result['requires_dependency_consent']);self.assertFalse(result['ready_to_use'])

 def test_connector_keeps_minimum_tools_and_no_trust_or_secret_transfer(self):
  spec=importlib.util.spec_from_file_location('dms_bootstrap',ROOT/'bootstrap.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  self.assertTrue(hasattr(mod,'connector_entry'),'Missing scoped connector recipe')
  with tempfile.TemporaryDirectory() as temp:
   home=Path(temp);entry=mod.connector_entry(home,{'node':'node-local','chrome':'chrome-local','mcp_bin':'mcp-local'})
   self.assertEqual(entry['trust'],'untrusted');self.assertFalse(entry['sampling']['enabled']);self.assertFalse(entry['elicitation']['enabled'])
   self.assertEqual(set(entry['tools']['include']),{'list_pages','new_page','take_snapshot','navigate_page','fill','press_key','click'})
   self.assertNotIn('headers',entry);self.assertNotIn('--headless',entry['args']);self.assertIn('--no-javascript-evaluation',entry['args'])

 def test_manifest_rejects_changed_payload_and_traversal(self):
  import json,hashlib
  spec=importlib.util.spec_from_file_location('dms_bootstrap',ROOT/'bootstrap.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  self.assertTrue(hasattr(mod,'verify_bundle'),'Missing payload verification')
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'data.txt').write_text('authored')
   manifest={'files':{'data.txt':hashlib.sha256(b'authored').hexdigest()}}
   (root/'SHA256SUMS.json').write_text(json.dumps(manifest));self.assertEqual(mod.verify_bundle(root),1)
   (root/'data.txt').write_text('changed')
   with self.assertRaises(ValueError):mod.verify_bundle(root)
   (root/'SHA256SUMS.json').write_text(json.dumps({'files':{'../outside.txt':'0'*64}}))
   with self.assertRaises(ValueError):mod.verify_bundle(root)

 def test_mutating_cli_phases_stop_before_writes_without_approval(self):
  spec=importlib.util.spec_from_file_location('dms_bootstrap',ROOT/'bootstrap.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  self.assertTrue(hasattr(mod,'main'),'Missing runnable setup helper')
  with tempfile.TemporaryDirectory() as temp:
   home=Path(temp);(home/'config.yaml').write_text('synthetic: true\n');before=(home/'config.yaml').read_bytes()
   for phase in ('deps','install'):
    with self.assertRaises(PermissionError):mod.main([phase,'--home',str(home)])
   self.assertEqual(before,(home/'config.yaml').read_bytes());self.assertFalse((home/'plugins').exists())

 def test_approved_install_byte_verifies_and_preserves_profile(self):
  import shutil,json,hashlib,contextlib,io
  spec=importlib.util.spec_from_file_location('dms_bootstrap',ROOT/'bootstrap.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  with tempfile.TemporaryDirectory() as temp:
   base=Path(temp);bundle=base/'bundle';bundle.mkdir();home=base/'home';home.mkdir();(home/'config.yaml').write_text('synthetic: true\n');before=(home/'config.yaml').read_bytes()
   shutil.copy2(ROOT/'install.py',bundle/'install.py');shutil.copytree(ROOT/'dms-fast',bundle/'dms-fast',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
   hashes={p.relative_to(bundle).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in bundle.rglob('*') if p.is_file()}
   (bundle/'SHA256SUMS.json').write_text(json.dumps({'files':hashes}));mod.ROOT=bundle
   with contextlib.redirect_stdout(io.StringIO()):result=mod.main(['install','--home',str(home),'--approve-install'])
   self.assertEqual(result['status'],'installed_disabled');self.assertEqual(before,(home/'config.yaml').read_bytes())
   self.assertEqual((ROOT/'dms-fast/session.py').read_bytes(),(home/'plugins/dms-fast/session.py').read_bytes())
   with self.assertRaises(FileExistsError):mod.main(['install','--home',str(home),'--approve-install'])

 def test_actual_environment_audit_does_not_change_profile(self):
  spec=importlib.util.spec_from_file_location('dms_bootstrap',ROOT/'bootstrap.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  self.assertTrue(hasattr(mod,'audit_environment'),'Missing real environment detection')
  with tempfile.TemporaryDirectory() as temp:
   home=Path(temp);(home/'config.yaml').write_text('synthetic: true\n');before=(home/'config.yaml').read_bytes()
   result=mod.audit_environment(home)
   self.assertIn('python_supported',result);self.assertIn('node_version',result);self.assertIn('chrome',result)
   self.assertEqual(before,(home/'config.yaml').read_bytes());self.assertFalse((home/'plugin-tools').exists())

 def test_recipe_is_explicit_scoped_data_not_an_automatic_config_write(self):
  spec=importlib.util.spec_from_file_location('dms_bootstrap',ROOT/'bootstrap.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  self.assertTrue(hasattr(mod,'configuration_recipe'),'Missing recipient configuration recipe')
  with tempfile.TemporaryDirectory() as temp:
   home=Path(temp);before=set(home.iterdir());facts={'node':'node-local','chrome':'chrome-local','mcp_bin':'mcp-local'}
   result=mod.configuration_recipe(home,'chrome_dms_recipient',facts)
   self.assertEqual(result['status'],'recipe_only_not_applied');self.assertEqual(before,set(home.iterdir()))
   self.assertEqual(result['plugin_settings']['mcp_allowlist'],['chrome_dms_recipient'])
   self.assertEqual(result['connector']['trust'],'untrusted');self.assertFalse(result['ready_to_use'])
   with self.assertRaises(ValueError):mod.configuration_recipe(home,'bad name',facts)
