"""Bounded UI search. No hidden APIs, external browser or source instructions."""
import re
import time
from pathlib import Path
from .core import parse_snapshot, validate_url
from .files import finish
from .adapter import observe, file_candidates
from .paths import checked_path

QUOTA = 'Đã quá số lượng tải văn bản trong ngày'


def checked(text):
    page = parse_snapshot(text)
    validate_url(page['url'])
    if page['permission_denied'] or page['login_required']:
        raise ValueError('Access/login changed')
    return page


def execute(ctx, task, page_id, text, call, work_id):
    if 'url' not in task:
        boxes = re.findall(r'uid=(\S+) searchbox "Bạn muốn tìm gì\?"', text)
        if len(boxes) != 1:
            return {'status': 'search_ui_changed', 'page_id': page_id}
        call('fill', {'pageId': page_id, 'uid': boxes[0], 'value': task['query']})
        call('press_key', {'pageId': page_id, 'key': 'Enter'})
        observed = checked(call('take_snapshot', {'pageId': page_id}))
        # The UI may briefly clear rows while search renders. Only read again;
        # never resubmit Enter, retry a refused call or wait without a bound.
        for _ in range(2):
            if observed['documents']:
                break
            time.sleep(0.25)
            observed = checked(call('take_snapshot', {'pageId': page_id}))
        candidates = [{'title': d['title'], 'url': d['url']} for d in observed['documents']]
        if not candidates:
            return {'status': 'search_result_unverified', 'operation': 'search', 'query': task['query'],
                    'candidates': [], 'inventory_complete': False, 'download_attempted': False,
                    'instruction': 'No canonical result links observed. This does not prove zero search results; preserve work for a fresh UI check.'}
        return {'status': 'completed' if task['kind'] == 'search' else 'source_selection_required',
                'operation': 'search', 'query': task['query'], 'candidates': candidates,
                'inventory_complete': False, 'download_attempted': False,
                'instruction': 'Only observed source links are returned. No download has been attempted.'}
    key = 'download_' + work_id
    server = ctx.get_config('mcp_server', default='chrome_dms')
    saved = ctx.state.get(key)
    if saved and (saved.get('task') != task or saved.get('server') != server):
        return {'status': 'pending_work_conflict', 'download_attempted': False}
    quota = ctx.state.get('quota_latch')
    if quota and quota.get('server') != server:
        return {'status': 'pending_work_conflict', 'download_attempted': False}
    if saved and saved.get('completed'):
        live = checked(text)
        if live['url'] != task['url']:
            call('navigate_page', {'pageId': page_id, 'type': 'url', 'url': task['url'], 'timeout': 10000, 'handleBeforeUnload': 'dismiss'})
            live = checked(call('take_snapshot', {'pageId': page_id}))
        current_source = {'url': live['url'], 'title': task['expected_title'] if task['expected_title'] in live['headings'] else None,
                          'code': live['metadata'].get('Số hiệu'), 'revision': live['metadata'].get('Lần ban hành'),
                          'effective_date': live['metadata'].get('Ngày hiệu lực')}
        if current_source != saved['source']:
            return {'status': 'source_revision_changed', 'download_attempted': False, 'instruction': 'Live source differs from the delivered revision; preserve the previous file and seek a new scoped selection.'}
        return finish(ctx, key, saved, task)
    if ctx.state.get('quota_latch'):
        return {'status': 'awaiting_quota', 'source': saved.get('source') if saved else None,
                'daily_limit': 5, 'remaining': None, 'reset_at': None, 'download_attempted': False,
                'instruction': 'Explicit DMS quota notice retained. Preserve login; do not retry. Request operator-approved quota reset before another attempt.'}
    if saved and saved.get('attempted'):
        # The session already captured fresh UI. A delayed quota notice must
        # stop file waiting, without another click or a browser recheck.
        checked(text)
        if QUOTA in text:
            ctx.state.set('quota_latch', {'server': server, 'source': saved['source'], 'observed_at': time.time(), 'daily_limit': 5})
            return {'status': 'awaiting_quota', 'source': saved['source'], 'daily_limit': 5,
                    'remaining': None, 'reset_at': None, 'download_attempted': True}
        outcome: dict = finish(ctx, key, saved, task, wait_seconds=0)
        outcome['ui_observation'] = observe(text)
        return outcome
    if 'url' in task:
        # An explicitly selected canonical source needs fresh identity verification,
        # not a repeat of the search that selected it. Never infer from its URL.
        detail = text
        if checked(text)['url'] != task['url']:
            call('navigate_page', {'pageId': page_id, 'type': 'url', 'url': task['url'], 'timeout': 10000, 'handleBeforeUnload': 'dismiss'})
            detail = call('take_snapshot', {'pageId': page_id})
        page = checked(detail)
        if page['url'] != task['url'] or task['expected_title'] not in page['headings'] or page['metadata'].get('Số hiệu') != task['expected_code']:
            return {'status': 'source_mismatch', 'download_attempted': False}
        source = {'url': page['url'], 'title': task['expected_title'], 'code': task['expected_code'],
                  'revision': page['metadata'].get('Lần ban hành'), 'effective_date': page['metadata'].get('Ngày hiệu lực')}
        if not source['revision'] or not source['effective_date']:
            return {'status': 'revision_unverified', 'source': source, 'download_attempted': False}
        for previous in ctx.state.get('deliveries', []):
            if previous.get('source_mcp_server') == server and previous.get('source') == source and Path(previous['file']['path']).parent == Path(task['output_dir']).resolve():
                verified = finish(ctx, key, {'completed': previous}, task)
                verified['download_attempted'] = False
                return verified
        buttons = re.findall(r'uid=(\S+) link "Tải về" url="javascript:;"', detail)
        if len(buttons) != 1:
            return {'status': 'download_ui_changed', 'source': source, 'download_attempted': False}
        download_dir = checked_path(ctx.get_config('download_dir', default=''), must_exist=True, directory=True)
        before = {p.name: [p.stat().st_size, p.stat().st_mtime_ns] for p in download_dir.iterdir() if p.is_file() and not p.is_symlink()}
        saved = {'server': server, 'source': source, 'task': dict(task), 'before': before, 'started_at': time.time(), 'download_dir': str(download_dir), 'attempted': True}
        # Persist intent BEFORE clicking; uncertain outcomes never auto-click again.
        ctx.state.set(key, saved)
        call('click', {'pageId': page_id, 'uid': buttons[0]})
        after = call('take_snapshot', {'pageId': page_id})
        checked(after)
        if QUOTA in after:
            ctx.state.set('quota_latch', {'server': server, 'source': source, 'observed_at': time.time(), 'daily_limit': 5})
            return {'status': 'awaiting_quota', 'source': source, 'daily_limit': 5, 'remaining': None, 'reset_at': None, 'download_attempted': True}
        candidates = file_candidates(after)
        if candidates and re.search(r'link "Tải về Download"', after):
            saved['phase'] = 'file_selection'
            ctx.state.set(key, saved)
            return {'status': 'download_selection_required', 'source': source, 'file_candidates': candidates,
                    'download_attempted': True, 'file_transfer_attempted': False, 'ui_observation': observe(after),
                    'instruction': 'List opened, not a completed transfer. Select the exact filename and explicitly authorize continue_download; never click the list opener again.'}
        return finish(ctx, key, saved, task)

