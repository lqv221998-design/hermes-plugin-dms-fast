import os,subprocess,tempfile,unittest
from pathlib import Path
import test_install as old
import test_reader as reader
class ReparseSafety(unittest.TestCase):
 def test_offline_install_rejects_destination_parent_junction_before_any_write(self):
  with tempfile.TemporaryDirectory() as temp:
   base=Path(temp);home=base/'home';home.mkdir();outside=base/'outside';outside.mkdir();(home/'config.yaml').write_text('synthetic: true\n')
   if os.name=='nt':
    p=subprocess.run(['cmd.exe','/c','mklink','/J',str(home/'plugins'),str(outside)],capture_output=True);self.assertEqual(p.returncode,0)
   else:(home/'plugins').symlink_to(outside,target_is_directory=True)
   try:
    with self.assertRaises(ValueError):old.module.install(home,include_panel=False)
    self.assertFalse((outside/'dms-fast').exists())
   finally:
    if os.name=='nt':os.rmdir(home/'plugins')
    else:(home/'plugins').unlink()

 def test_download_validation_rejects_output_parent_junction(self):
  import importlib
  session=importlib.import_module(reader.plugin.__name__+'.session')
  with tempfile.TemporaryDirectory() as temp:
   base=Path(temp);outside=base/'outside';outside.mkdir();(outside/'output').mkdir();linked=base/'link'
   if os.name=='nt':
    p=subprocess.run(['cmd.exe','/c','mklink','/J',str(linked),str(outside)],capture_output=True);self.assertEqual(p.returncode,0)
   else:linked.symlink_to(outside,target_is_directory=True)
   try:
    task={'kind':'search_download_one','query':'fixture','url':reader.URL,'expected_title':'fixture','expected_code':'QT-KT-07','output_dir':str(linked/'output')}
    with self.assertRaises(ValueError):session.validate_task(task)
   finally:
    if os.name=='nt':os.rmdir(linked)
    else:linked.unlink()
