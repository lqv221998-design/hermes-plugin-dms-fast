"""Install only authored files. Never grant MCP, restart Chrome or overwrite."""
import argparse
import hashlib
import os

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def install(home, include_panel=True):
    home = Path(home).resolve()
    if not home.is_dir() or not (home/'config.yaml').is_file():
        raise ValueError('Expected an existing Hermes profile home with config.yaml')
    pairs = [(ROOT/'dms-fast', home/'plugins'/'dms-fast')]
    if include_panel:
        pairs.append((ROOT/'desktop-plugins'/'dms-fast-panel', home/'desktop-plugins'/'dms-fast-panel'))
    for source, target in pairs:
        if not source.is_dir():
            raise ValueError('Missing authored source package')
        if target.exists():
            raise FileExistsError(f'Keep existing installation; refusing overwrite: {target}')
        if any(p.is_symlink() for p in source.rglob('*')):
            raise ValueError('Refusing symlink in source package')
    result = []
    for source, target in pairs:
        files = [p for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
        for file in files:
            destination = target/file.relative_to(source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as out:
                out.write(file.read_bytes())
            assert hashlib.sha256(destination.read_bytes()).digest() == hashlib.sha256(file.read_bytes()).digest()
        result.append(str(target))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', default=os.environ.get('HERMES_HOME'), help='Explicit current-profile Hermes home; no guessed user paths')
    parser.add_argument('--without-panel', action='store_true', help='Install backend and skill only; Desktop UI is optional')
    args = parser.parse_args()
    if not args.home:
        parser.error('Set HERMES_HOME or provide --home for the intended profile')
    for target in install(args.home, include_panel=not args.without_panel):
        print('Installed and byte-verified:', target)
    print('No config or browser changes. Enable agent plugin separately: hermes plugins enable dms-fast --no-allow-tool-override')
    print('MCP allowlist is deliberately NOT granted. Select this profile\'s MCP server and obtain permission separately.')
