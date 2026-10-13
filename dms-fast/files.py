"""Local completed-file checks; never fetch, execute or extract downloaded content."""
import hashlib
import json
import re
import shutil
import time
import zipfile
from pathlib import Path, PurePosixPath


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def inspect_file(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
        raise ValueError('Missing/empty/symlink file')
    if path.stat().st_size > 512 * 1024 * 1024:
        raise ValueError('One-file pilot size limit exceeded')
    with path.open('rb') as stream:
        magic = stream.read(8)
    if magic.startswith(b'PK'):
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if not entries or len(entries) > 10000 or sum(e.file_size for e in entries) > 1024 * 1024 * 1024:
                raise ValueError('Empty/oversized archive')
            for entry in entries:
                p = PurePosixPath(entry.filename.replace('\\', '/'))
                if p.is_absolute() or '..' in p.parts or ':' in entry.filename or (entry.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('Unsafe archive name/symlink')
            if archive.testzip() is not None:
                raise ValueError('Archive CRC mismatch')
            return {'format': 'zip', 'entries': len(entries), 'crc_verified': True}
    if magic.startswith(b'%PDF-'):
        with path.open('rb') as stream:
            stream.seek(max(0, path.stat().st_size - 2048))
            if b'%%EOF' not in stream.read():
                raise ValueError('PDF incomplete')
        return {'format': 'pdf', 'eof_verified': True, 'semantic_validation': False}
    raise ValueError('Unsupported file format; no success from HTML/login/unknown bytes')


def finish(ctx, key, saved, task, *, wait_seconds=None):
    if saved.get('completed'):
        result = saved['completed']
        p = Path(result['file']['path'])
        inspect_file(p)
        if digest(p) != result['file']['sha256']:
            raise ValueError('Previously delivered bytes changed')
        return dict(result, reused_local=True)
    directory = Path(saved['download_dir'])
    wait = ctx.get_config('download_wait_seconds', default=2) if wait_seconds is None else wait_seconds
    if type(wait) is not int or not 0 <= wait <= 60:
        raise ValueError('Invalid bounded download wait')
    deadline = time.monotonic() + wait
    while True:
        baseline = saved.get('transfer_before', saved['before'])
        changed = [p for p in directory.iterdir() if p.is_file() and not p.is_symlink() and baseline.get(p.name) != [p.stat().st_size, p.stat().st_mtime_ns]]
        partial = [p for p in changed if p.suffix.lower() in ('.crdownload', '.part', '.tmp')]
        ready = [p for p in changed if p not in partial]
        if len(ready) > 1:
            return {'status': 'ambiguous_downloads', 'source': saved['source'], 'download_attempted': True}
        if len(ready) == 1 and not partial:
            source = ready[0]
            signature = (source.stat().st_size, source.stat().st_mtime_ns)
            time.sleep(0.2)
            if signature == (source.stat().st_size, source.stat().st_mtime_ns):
                break
        if time.monotonic() >= deadline:
            return {'status': 'download_unconfirmed', 'source': saved['source'], 'download_attempted': True,
                    'instruction': 'No verified completed file; resume checks only, never repeats the download click.'}
        time.sleep(min(0.5, max(0, deadline - time.monotonic())))
    check = inspect_file(source)
    code = saved['source']['code']
    # Binding is conservative: require the exact document code in the browser filename.
    if not re.search(r'(?<![A-Za-z0-9])' + re.escape(code) + r'(?![A-Za-z0-9])', source.stem, re.I):
        return {'status': 'file_source_unverified', 'source': saved['source'], 'download_attempted': True,
                'instruction': 'File name does not bind the selected document code; do not claim source identity.'}
    output = Path(task['output_dir']).resolve()
    name = re.sub(r'[^A-Za-z0-9_.-]', '_', key + '-' + code + '-R' + saved['source']['revision']) + source.suffix.lower()
    target = output / name
    receipt = output / (name + '.source.json')
    if target.exists() or receipt.exists():
        return {'status': 'destination_conflict', 'source': saved['source'], 'download_attempted': True}
    before_hash = digest(source)
    with source.open('rb') as incoming, target.open('xb') as outgoing:
        shutil.copyfileobj(incoming, outgoing, 1024 * 1024)
    if digest(target) != before_hash or digest(source) != before_hash:
        raise ValueError('Copy/source hash mismatch')
    result = {'status': 'completed', 'source': saved['source'], 'source_mcp_server': saved['server'],
              'file': {'path': str(target), 'bytes': target.stat().st_size, 'sha256': before_hash, 'checks': check},
              'receipt_path': str(receipt), 'download_attempted': True, 'reused_local': False,
              'full_document_read': False, 'acceptance': 'pending_user', 'source_binding': 'exact_ui_source_revision_and_code_in_filename'}
    with receipt.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    if json.loads(receipt.read_text(encoding='utf-8')) != result:
        raise ValueError('Receipt readback mismatch')
    saved['completed'] = result
    ctx.state.set(key, saved)
    ledger = ctx.state.get('deliveries', [])
    ctx.state.set('deliveries', (ledger + [result])[-200:])
    return result
