"""Local relocation/profile tests, not proof of a second physical machine."""
import importlib.util
import re
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_installer(bundle):
    spec = importlib.util.spec_from_file_location('relocated_installer', bundle / 'install.py')
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PortabilityTests(unittest.TestCase):
    def test_relocated_bundle_and_two_unicode_profiles_are_independent(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            bundle = base / 'gói chuyển máy' / 'source'
            shutil.copytree(ROOT, bundle, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'VERIFICATION.json'))
            installer = load_installer(bundle)
            first = base / 'Máy A' / 'profile người đọc'
            second = base / 'Máy B' / 'profile giám sát'
            for home in (first, second):
                home.mkdir(parents=True)
                (home / 'config.yaml').write_text('sentinel: ' + home.name + '\n', encoding='utf-8')
                installer.install(home)
                for directory in ('dms-fast', 'desktop-plugins/dms-fast-panel'):
                    target = home / ('plugins/dms-fast' if directory == 'dms-fast' else directory)
                    for source in (bundle / directory).rglob('*'):
                        if source.is_file() and '__pycache__' not in source.parts and source.suffix != '.pyc':
                            self.assertEqual((target / source.relative_to(bundle / directory)).read_bytes(), source.read_bytes())
            self.assertNotEqual((first / 'config.yaml').read_bytes(), (second / 'config.yaml').read_bytes())
            changed = first / 'plugins/dms-fast/core.py'
            changed.write_text('# private local edit\n', encoding='utf-8')
            self.assertEqual((second / 'plugins/dms-fast/core.py').read_bytes(), (bundle / 'dms-fast/core.py').read_bytes())
            with self.assertRaises(FileExistsError):
                installer.install(first)
            self.assertEqual(changed.read_text(encoding='utf-8'), '# private local edit\n')
            self.assertEqual((first / 'config.yaml').read_text(encoding='utf-8'), 'sentinel: ' + first.name + '\n')
            self.assertEqual((second / 'config.yaml').read_text(encoding='utf-8'), 'sentinel: ' + second.name + '\n')

    def test_authored_runtime_has_no_machine_paths_or_local_services(self):
        files = list((ROOT / 'dms-fast').rglob('*.py')) + [ROOT / 'install.py', ROOT / 'desktop-plugins/dms-fast-panel/plugin.js']
        forbidden = re.compile(r'\b[A-Za-z]:[\\/]|/Users/|/home/|127\.0\.0\.1|localhost|9222|vu\.lequang')
        for path in files:
            with self.subTest(file=str(path.relative_to(ROOT))):
                self.assertIsNone(forbidden.search(path.read_text(encoding='utf-8')))


if __name__ == '__main__':
    unittest.main()
