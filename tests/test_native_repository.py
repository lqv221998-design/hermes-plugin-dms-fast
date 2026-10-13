import unittest
import os,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class NativeRepositoryPackage(unittest.TestCase):
 def test_git_checkout_preserves_desktop_bytes_with_windows_autocrlf(self):
  git=os.environ.get('HERMES_TEST_GIT') or shutil.which('git')
  self.assertTrue(git,'Git is required for native repository acceptance')
  with tempfile.TemporaryDirectory(prefix='dms-lf-',dir=os.environ.get('TMPDIR')) as temp:
   source=Path(temp)/'source';source.mkdir();(source/'desktop').mkdir()
   original=(ROOT/'desktop/plugin.js').read_bytes();(source/'desktop/plugin.js').write_bytes(original)
   if (ROOT/'.gitattributes').is_file():shutil.copy2(ROOT/'.gitattributes',source/'.gitattributes')
   def run(*args):subprocess.run([git,*map(str,args)],cwd=source,check=True,capture_output=True)
   run('init');run('config','core.autocrlf','false');run('config','user.name','Fixture');run('config','user.email','fixture@example.invalid');run('add','.');run('commit','-m','LF fixture')
   checked=Path(temp)/'checked';run('-c','core.autocrlf=true','clone',source,checked)
   self.assertEqual((checked/'desktop/plugin.js').read_bytes(),original,'Native Desktop clone must preserve bytes even with core.autocrlf=true')
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
