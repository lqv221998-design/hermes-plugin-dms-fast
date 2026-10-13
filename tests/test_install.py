import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

spec = importlib.util.spec_from_file_location('dms_install', Path(__file__).resolve().parents[1]/'install.py')
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class InstallTests(unittest.TestCase):
    def test_recipient_without_desktop_can_install_backend_only(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            (home / 'config.yaml').write_text('sentinel: preserve\n', encoding='utf-8')
            result = module.install(home, include_panel=False)
            self.assertEqual(len(result), 1)
            self.assertTrue((home / 'plugins/dms-fast/skills/reading/SKILL.md').is_file())
            self.assertFalse((home / 'desktop-plugins').exists())

    def test_install_preserves_config_and_refuses_any_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            config = home/'config.yaml'
            config.write_text('sentinel: preserve\n', encoding='utf-8')
            result = module.install(home)
            self.assertEqual(len(result),2)
            self.assertEqual(config.read_text(encoding='utf-8'),'sentinel: preserve\n')
            self.assertTrue((home/'plugins/dms-fast/skills/reading/SKILL.md').exists())
            self.assertFalse(list(home.rglob('*.pyc')))
            original = (home/'plugins/dms-fast/core.py').read_bytes()
            with self.assertRaises(FileExistsError):
                module.install(home)
            self.assertEqual((home/'plugins/dms-fast/core.py').read_bytes(),original)

if __name__=='__main__':
    unittest.main()
