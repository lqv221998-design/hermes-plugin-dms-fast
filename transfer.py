"""Continue a verified two-stage file link, never repeat the list-opening click."""
import re
import time
from pathlib import Path
from .core import parse_snapshot, validate_url
from .adapter import observe
from .files import finish
from .paths import checked_path


def continue_file(ctx, task, page_id, text, call, work_id, filename):
    key = 'download_' + work_id
    saved = ctx.state.get(key)
    server = ctx.get_config('mcp_server', default='chrome_dms')
    if not saved or saved.get('server') != server or saved.get('task') != task or not saved.get('attempted'):
        return {'status': 'download_continuation_conflict', 'download_attempted': False}
    if ctx.state.get('quota_latch'):
        return {'status': 'awaiting_quota', 'download_attempted': True}
    page = parse_snapshot(text)
    validate_url(page['url'])
    if page['login_required'] or page['permission_denied'] or page['url'] != task['url']:
        return {'status': 'source_mismatch', 'download_attempted': True}
    if 'Đã quá số lượng tải văn bản trong ngày' in text:
        ctx.state.set('quota_latch', {'server': server, 'source': saved['source'], 'observed_at': time.time(), 'daily_limit': 5})
        return {'status': 'awaiting_quota', 'download_attempted': True}
    if saved.get('file_transfer_attempted') or saved.get('completed'):
        return finish(ctx, key, saved, task, wait_seconds=0)
    source = saved.get('source', {})
    if any(not source.get(k) for k in ('url', 'title', 'code', 'revision', 'effective_date')):
        return {'status': 'revision_unverified', 'download_attempted': True}
    names = [h for h in page['headings'] if re.search(r'\.(?:docx?|xlsx?|pdf|zip)$', h, re.I)]
    uids = re.findall(r'^\s*uid=(\S+) link "Tải về Download"(?: url="[^"\n]*")?', text, re.MULTILINE)
    code_match = re.search(r'(?<![A-Za-z0-9])' + re.escape(task['expected_code']) + r'(?![A-Za-z0-9])', filename, re.I)
    if names != [filename] or len(uids) != 1 or not code_match or task['expected_title'] not in page['headings']:
        return {'status': 'file_selection_unverified', 'download_attempted': True, 'ui_observation': observe(text)}
    directory = checked_path(saved['download_dir'], must_exist=True, directory=True)
    saved['transfer_before'] = {p.name: [p.stat().st_size, p.stat().st_mtime_ns] for p in directory.iterdir() if p.is_file() and not p.is_symlink()}
    saved['file_transfer_attempted'] = True
    saved['selected_file_name'] = filename
    saved['transfer_started_at'] = time.time()
    ctx.state.set(key, saved)
    call('click', {'pageId': page_id, 'uid': uids[0]})
    after = call('take_snapshot', {'pageId': page_id})
    checked = parse_snapshot(after)
    if checked['url'] != page['url'] or checked['login_required'] or checked['permission_denied']:
        return {'status': 'download_outcome_uncertain', 'download_attempted': True}
    if 'Đã quá số lượng tải văn bản trong ngày' in after:
        ctx.state.set('quota_latch', {'server': server, 'source': source, 'observed_at': time.time(), 'daily_limit': 5})
        return {'status': 'awaiting_quota', 'download_attempted': True}
    return finish(ctx, key, saved, task)
