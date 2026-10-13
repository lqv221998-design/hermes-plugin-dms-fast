import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class NativeRepositoryPackage(unittest.TestCase):
 def test_plain_repository_root_is_an_agent_and_desktop_package(self):
  self.assertTrue((ROOT/'plugin.yaml').is_file(),'Bare repository URL must expose native manifest at root')
  self.assertTrue((ROOT/'__init__.py').is_file(),'Root agent entry missing')
  self.assertTrue((ROOT/'desktop/plugin.js').is_file(),'Unified Desktop half missing')
  self.assertTrue((ROOT/'skills/reading/SKILL.md').is_file(),'Bundled skill must follow root agent package')
 def test_legacy_subdirectory_and_root_share_exact_reviewed_runtime(self):
  self.assertTrue((ROOT/'plugin.yaml').is_file(),'Root package absent')
  for p in (ROOT/'dms-fast').rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
    with self.subTest(source=p.name):self.assertEqual(p.read_bytes(),(ROOT/p.relative_to(ROOT/'dms-fast')).read_bytes())
