"""Opt-in real npm integration, never connects a browser or DMS."""
import os,tempfile,unittest,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(os.environ.get('DMS_SETUP_NETWORK_TEST')=='1','Explicit opt-in for official npm download')
class SetupNetwork(unittest.TestCase):
 def test_official_package_install_verifies_pin_and_executable(self):
  spec=importlib.util.spec_from_file_location('dms_network_bootstrap',ROOT/'bootstrap.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  self.assertTrue(hasattr(mod,'install_dependencies'),'Missing actual prerequisite installer')
  with tempfile.TemporaryDirectory() as temp:
   home=Path(temp);(home/'config.yaml').write_text('synthetic: true\n');before=(home/'config.yaml').read_bytes()
   result=mod.install_dependencies(home)
   self.assertEqual(result['mcp_version'],'1.10.1');self.assertTrue(Path(result['facts']['mcp_bin']).is_file())
   self.assertEqual(before,(home/'config.yaml').read_bytes());self.assertFalse((home/'plugins').exists())
   self.assertEqual(mod.install_dependencies(home)['mcp_version'],'1.10.1')
   binary=Path(result['facts']['mcp_bin']);binary.write_bytes(binary.read_bytes()+b'\n// fixture tamper\n')
   with self.assertRaises(ValueError):mod.install_dependencies(home)
