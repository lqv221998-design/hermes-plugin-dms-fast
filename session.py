"""Visible human-login lifecycle. Chrome owns credentials and browser sessions."""
import re
import time
from urllib.parse import urlsplit

from .core import BASE, ROUTES, parse_snapshot, validate_url
from .executor import execute
from .adapter import observe, CAPABILITIES, READ_SECTIONS, read_section, READ_MENUS, read_menu
from .transfer import continue_file
from .paths import checked_path

KEY = 'session_work'
TTL = 86400
VERSION = '0.5.5'


def pages(text):
    """Discard auth URLs immediately; return only IDs and safe classifications."""
    if not isinstance(text, str):
        raise ValueError('Unsupported page listing')
    sections = list(re.finditer(r'^## Pages[ \t]*\r?$', text, re.MULTILINE))
    if len(sections) != 1:
        raise ValueError('Unsupported page listing')
    result = []
    for line in text[sections[0].end():].splitlines():
        if line.startswith('## '):
            break  # Extension/service-worker sections are never candidate pages.
        match = re.fullmatch(r'(\d+): (?:(.*?) \((\S+)\)|(\S+))(?: \[selected\])?', line.strip())
        if not match:
            if line.strip():
                raise ValueError('Unexpected page-list format')
            continue
        title, raw = match[2] or '', match[3] or match[4]
        if raw in ('chrome://newtab/', 'chrome://new-tab-page/'):
            # An unrelated Chrome start tab is not a DMS failure. Never act on it.
            continue
        if raw != 'about:blank' and urlsplit(raw).scheme not in ('http', 'https'):
            raise ValueError('Unsupported page URL')
        try:
            canonical = validate_url(raw)
        except ValueError:
            canonical = None
        # Login titles identify a waiting tab only, never authorize browser actions.
        login = title.strip().casefold() in ('sign in to newtecons', 'đăng nhập - newtecons') or (urlsplit(raw).scheme == 'https' and urlsplit(raw).netloc == 'sso.newtecons.vn')
        result.append({'id': int(match[1]), 'url': canonical, 'login': login,
                       'dms': urlsplit(raw).scheme == 'https' and urlsplit(raw).netloc == urlsplit(BASE).netloc})
    return result


def validate_task(task):
    if not isinstance(task, dict):
        raise ValueError('A bounded task object is required')
    if task.get('kind') == 'search':
        if set(task) != {'kind', 'query'} or not isinstance(task.get('query'), str) or not task['query'].strip() or len(task['query']) > 120:
            raise ValueError('Search-only needs a bounded query and no download/source fields')
        return {'kind': 'search', 'query': task['query'].strip()}
    if task.get('kind') == 'search_download_one' and set(task) <= {'kind', 'query', 'url', 'expected_title', 'expected_code', 'output_dir'}:
        if not isinstance(task['query'], str) or not task['query'].strip() or len(task['query']) > 120:
            raise ValueError('Invalid search query')
        if set(task) != {'kind', 'query'}:
            from pathlib import Path
            if set(task) != {'kind', 'query', 'url', 'expected_title', 'expected_code', 'output_dir'}:
                raise ValueError('Download needs an exact source, title, code and explicit existing output directory')
            validate_url(task['url'])
            if '/document/detail/' not in task['url']:
                raise ValueError('Download needs a document source')
            for key in ('expected_title', 'expected_code', 'output_dir'):
                if not isinstance(task[key], str) or not task[key].strip() or len(task[key]) > 500:
                    raise ValueError('Invalid selected source/output')
            checked_path(task['output_dir'], must_exist=True, directory=True)
        return dict(task)
    if task.get('kind') == 'read' and set(task) <= {'kind', 'action', 'url', 'expected_code', 'expected_title'}:
        if task.get('action') != 'open':
            raise ValueError('Resumable reads need an exact canonical source URL')
        validate_url(task.get('url'))
        for key in ('expected_code', 'expected_title'):
            if key in task and (not isinstance(task[key], str) or not task[key].strip() or len(task[key]) > 300):
                raise ValueError('Invalid expected source identity')
        return dict(task)
    raise ValueError('Unsupported task; no arbitrary scripts, credentials or page IDs')


def session_run(ctx, args, settings, lock, reader):
    calls = 0
    started = time.perf_counter()
    acquired = False
    listing_diagnostic = None
    last_mcp_tool = None

    def call(name, payload):
        nonlocal calls, last_mcp_tool
        calls += 1
        last_mcp_tool = name
        response = ctx.call_mcp(server, name, payload, timeout=15)
        if not response.get('ok') or response.get('truncated'):
            raise RuntimeError('Transport/access failure; no retry or fallback')
        return response.get('result')

    def response(status, task=None, **extra):
        return {'ok': True, 'status': status, 'plugin_version': VERSION, 'work_id': work_id, 'pending_task': task,
                'mcp_calls': calls, 'elapsed_ms': round((time.perf_counter() - started) * 1000), 'credentials_stored': False, **extra}

    def pending_guidance(saved):
        now = time.time()
        expired = now - saved['created_at'] > TTL or saved['created_at'] > now
        safe_new_read = expired and saved['task']['kind'] in ('read', 'search') and saved['server'] == server
        return {'pending_work_expired': expired, 'work_ttl_seconds': TTL,
                'next_action': 'prepare' if safe_new_read else 'status',
                'next_work_id': work_id if safe_new_read else saved['work_id'],
                'instruction': ('Use prepare with the currently requested bounded read/search; its normal TTL handling releases expired session work. Do not cancel, replay downloads or clear attempts/quota.'
                                if safe_new_read else 'Read status for the active work before any change. Do not replace unfamiliar/live work, switch server or replay an uncertain download; cancellation requires permission.')}

    try:
        if not isinstance(args, dict) or set(args) - {'action', 'work_id', 'task', 'wait_seconds', 'section', 'expected_file_name', 'menu'}:
            raise ValueError('Invalid session input fields')
        action, work_id = args.get('action'), args.get('work_id')
        if action not in ('prepare', 'resume', 'resume_after_quota', 'cancel', 'status', 'inspect', 'capabilities', 'continue_download') or not isinstance(work_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', work_id):
            raise ValueError('Invalid action/work ID')
        wait = args.get('wait_seconds', 0)
        if type(wait) is not int or not 0 <= wait <= 60:
            raise ValueError('Wait must be an integer from 0 to 60 seconds')
        if action != 'prepare' and 'task' in args:
            raise ValueError('Only prepare accepts a new task')
        if 'section' in args and (action != 'inspect' or args['section'] not in READ_SECTIONS):
            raise ValueError('Only inspect accepts a known read section')
        if 'menu' in args and (action != 'inspect' or args['menu'] not in READ_MENUS or 'section' in args):
            raise ValueError('Only inspect accepts one known read menu')
        if action == 'continue_download':
            filename = args.get('expected_file_name')
            if not isinstance(filename, str) or not filename.strip() or len(filename) > 300 or any(c in filename for c in ('/', '\\', '\n', '\r', ':')):
                raise ValueError('Explicit observed filename required for file continuation')
        elif 'expected_file_name' in args:
            raise ValueError('Filename only accepted for file continuation')
        task = validate_task(args.get('task')) if action == 'prepare' else None
        if action == 'capabilities':
            return response('capabilities', capabilities=CAPABILITIES)
        server = settings(ctx)['mcp_server']
        acquired = lock.acquire(blocking=False)
        if not acquired:
            return response('busy')
        saved = ctx.state.get(KEY)
        if saved is not None and (not isinstance(saved, dict) or set(saved) != {'work_id', 'server', 'task', 'created_at'}):
            raise ValueError('Invalid stored work')
        if saved:
            validate_task(saved['task'])
            if type(saved['created_at']) not in (int, float) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', saved['work_id']):
                raise ValueError('Invalid stored identity/timestamp')
        if action == 'status':
            if saved and (saved['work_id'] != work_id or saved['server'] != server):
                return response('pending_work_conflict', saved['task'], active_work_id=saved['work_id'], **pending_guidance(saved))
            attempt = ctx.state.get('download_' + work_id) or {}
            return response('pending_work' if saved else 'no_pending_work', saved['task'] if saved else None,
                            download_attempted=bool(attempt.get('attempted')),
                            file_transfer_attempted=bool(attempt.get('file_transfer_attempted')),
                            download_phase=('delivered' if attempt.get('completed') else 'transfer_attempted' if attempt.get('file_transfer_attempted') else attempt.get('phase', 'legacy_attempt' if attempt.get('attempted') else 'not_attempted')),
                            quota_pending=bool(ctx.state.get('quota_latch')),
                            delivered=bool(attempt.get('completed')),
                            **(pending_guidance(saved) if saved else {'pending_work_expired': False, 'work_ttl_seconds': TTL}))
        if 'menu' in args and saved:
            return response('pending_work_conflict', saved['task'], active_work_id=saved['work_id'], **pending_guidance(saved))
        if saved and action != 'inspect':
            if time.time() - saved['created_at'] > TTL or saved['created_at'] > time.time():
                ctx.state.set(KEY, None)
                saved = None
                if action == 'resume':
                    return response('expired')
        if saved and (saved['work_id'] != work_id or saved['server'] != server):
            return response('pending_work_conflict', saved['task'], active_work_id=saved['work_id'], **pending_guidance(saved))
        if action == 'cancel':
            ctx.state.set(KEY, None)
            return response('cancelled')
        if action == 'prepare':
            if saved and saved['task'] != task:
                return response('pending_work_conflict', saved['task'], active_work_id=saved['work_id'], **pending_guidance(saved))
            if not saved:
                saved = {'work_id': work_id, 'server': server, 'task': task, 'created_at': time.time()}
                ctx.state.set(KEY, saved)
        elif not saved and action != 'inspect':
            return response('no_pending_work')
        task = saved['task'] if saved else None
        if action != 'inspect' and task and task['kind'] == 'search_download_one' and task.get('url'):
            from pathlib import Path
            directory = ctx.get_config('download_dir', default='')
            if not isinstance(directory, str) or not directory.strip():
                return response('configuration_required', task, missing_fields=['download_dir'], instruction='Operator must configure this profile\'s actual Chrome download directory. No OS/user-home guess.')
            path = Path(directory)
            wait_file = ctx.get_config('download_wait_seconds', default=2)
            if not path.is_absolute() or not path.is_dir() or path.is_symlink() or type(wait_file) is not int or not 0 <= wait_file <= 60:
                return response('configuration_invalid', task, instruction='Use an existing absolute nonsymlink Chrome download directory and integer wait 0–60.')
        if action == 'resume_after_quota':
            quota = ctx.state.get('quota_latch')
            attempt = ctx.state.get('download_' + work_id)
            if not quota or not attempt or attempt.get('server') != server or quota.get('server') != server or attempt.get('source') != quota.get('source'):
                return response('quota_resume_conflict', task)
            # This action requires an explicit NEW user authorization; no inferred reset clock.
            ctx.state.set('quota_resume_audit', {'work_id': work_id, 'acknowledged_at': time.time(), 'previous_notice': quota})
            ctx.state.set('quota_latch', None)
            ctx.state.set('download_' + work_id, None)
        deadline = time.monotonic() + wait
        opened = False
        while True:
            raw_listing = call('list_pages', {})
            listing_diagnostic = {
                'type': type(raw_listing).__name__,
                'pages_section': isinstance(raw_listing, str) and bool(re.search(r'^## Pages\s*$', raw_listing, re.MULTILINE)),
                'starts_with_pages': isinstance(raw_listing, str) and raw_listing.startswith('## Pages'),
                'note_prefix': isinstance(raw_listing, str) and raw_listing.startswith('Note:')}
            listing = pages(raw_listing)
            candidates = [p for p in listing if p['dms'] or p['login']]
            if len(candidates) > 1:
                return response('ambiguous_tabs', task, instruction='Keep exactly one DMS/login tab for this operation; no tab closed automatically.')
            if not candidates:
                if action == 'inspect':
                    return response('browser_not_ready', task, reason='no_dms_or_login_tab',
                                    next_action='prepare' if saved is None else 'resume',
                                    suggested_task={'kind': 'read', 'action': 'open', 'url': ROUTES['home']} if saved is None else task,
                                    instruction='inspect is observation-only and never opens a tab. Use prepare for the requested home/source/search when no work is active. Resume only familiar authorized pending work; no raw browser fallback.')
                if opened:
                    return response('browser_not_ready', task)
                call('new_page', {'url': ROUTES['home'], 'background': False, 'timeout': 10000})
                opened = True
                continue
            page = candidates[0]
            if page['url']:
                text = call('take_snapshot', {'pageId': page['id']})
                if not isinstance(text, str):
                    raise ValueError('Unsupported snapshot')
                root = re.search(r'RootWebArea "[^"]*" url="([^"]+)"', text)
                try:
                    validate_url(root[1] if root else None)
                except ValueError:
                    # A redirect raced the page listing: never echo or retain the snapshot.
                    return response('awaiting_login', task, instruction='Log in directly in Chrome, then resume this work ID.')
                observed = parse_snapshot(text)
                if observed['permission_denied']:
                    return response('access_denied', task, instruction='Stop; do not retry or bypass access controls.')
                logout_link = re.search(r'uid=\S+ link "Đăng xuất" url="https://dms\.newtecons\.vn/baseview/logout(?:\?[^"\n]*)?"', text)
                if not observed['login_required'] and logout_link and observed['title'].strip():
                    if action == 'inspect':
                        if 'section' in args:
                            text = read_section(text, args['section'], page['id'], call, task)
                        if 'menu' in args:
                            text = read_menu(text, args['menu'], page['id'], call)
                        return response('observed', task, ui_observation=observe(text))
                    if task is None:
                        raise ValueError('A saved task is required')
                    if action == 'continue_download':
                        if task['kind'] != 'search_download_one' or not task.get('url'):
                            return response('download_continuation_conflict', task)
                        outcome = continue_file(ctx, task, page['id'], text, call, work_id, args['expected_file_name'])
                        status = outcome.pop('status')
                        if status == 'completed':
                            ctx.state.set(KEY, None)
                            return response(status, None, **outcome)
                        return response(status, task, **outcome)
                    if task['kind'] == 'read':
                        # Release the same shared controller lock before invoking the reader.
                        lock.release()
                        acquired = False
                        result = reader(ctx, {k: v for k, v in task.items() if k != 'kind'} | {'page_id': page['id']})
                        if result.get('ok'):
                            ctx.state.set(KEY, None)
                            return response('completed', None, result=result)
                        return response('read_stopped', task, result=result)
                    outcome = execute(ctx, task, page['id'], text, call, work_id)
                    status = outcome.pop('status')
                    if status == 'completed':
                        ctx.state.set(KEY, None)
                        return response(status, None, **outcome)
                    return response(status, task, **outcome)
            elif page['dms'] and not page['login']:
                return response('unsupported_dms_route', task)
            if time.monotonic() >= deadline:
                return response('awaiting_login', task, instruction='Log in directly in Chrome. This is a normal pending state, not a failed task. Resume with the same work ID; cancel is available.')
            time.sleep(min(2, max(0, deadline - time.monotonic())))
    except (PermissionError, TimeoutError, RuntimeError) as exc:
        return {'ok': False, 'status': 'browser_unavailable_or_refused', 'error_type': type(exc).__name__,
                'plugin_version': VERSION, 'failed_mcp_tool': last_mcp_tool,
                'mcp_calls': calls, 'retried': False, 'instruction': 'Check the configured Chrome MCP and host permission. No browser restart, credentials or fallback attempted.'}
    except Exception as exc:
        # Emit only fixed diagnostic identifiers, never raw transport/auth data.
        safe_codes = {'Unsupported page listing': 'unsupported_page_listing',
                      'Unexpected page-list format': 'unexpected_page_list_format',
                      'Unsupported page URL': 'unsupported_page_url',
                      'Unsupported snapshot': 'unsupported_snapshot',
                      'Missing semantic page root': 'missing_semantic_page_root',
                      'Read menu ambiguous or unavailable': 'read_menu_unavailable_or_ambiguous',
                      'Read menu target differs from evidenced route': 'read_menu_target_mismatch',
                      'Guide menu target not verified': 'guide_target_unverified',
                      'Guide content unverified': 'guide_content_unverified',
                      'Read menu destination/access changed': 'read_menu_destination_unverified'}
        return {'ok': False, 'status': 'invalid_input_or_host_failure', 'error_type': type(exc).__name__,
                'error_code': safe_codes.get(str(exc), 'invalid_input_or_host_failure'), 'mcp_calls': calls, 'retried': False,
                'listing_diagnostic': listing_diagnostic}
    finally:
        if acquired:
            lock.release()


def register_session(ctx, settings, lock, reader):
    import json

    def handler(args, **kwargs):
        return json.dumps(session_run(ctx, args, settings, lock, reader), ensure_ascii=False)

    ctx.register_tool(
        name='dms_fast_session', toolset='dms_fast', handler=handler,
        schema={'name': 'dms_fast_session', 'description': 'DMS entry: use prepare with the requested canonical read URL or bounded search; for site mapping use a read of https://dms.newtecons.vn/. Reuses this profile\'s visible Chrome and opens one home tab if absent. inspect only observes an existing tab; it does not bootstrap Chrome. Expired/live pending diagnostics supply the next safe step without cancellation or quota reset. Human login is normal pending. No raw browser fallback or refusal retry. Load dms-fast:reading first.',
                'parameters': {'type': 'object', 'properties': {
                    'action': {'type': 'string', 'enum': ['prepare', 'resume', 'resume_after_quota', 'cancel', 'status', 'inspect', 'capabilities', 'continue_download'], 'description': 'continue_download needs explicit permission and exact observed filename; clicks the inner file link once, never the list opener again. capabilities reports implementation limits. inspect reads UI without replacing work; optional section changes only a known read tab. status uses zero browser calls. Quota recheck always needs NEW permission.'},
                    'work_id': {'type': 'string', 'pattern': '^[A-Za-z0-9_-]{1,64}$'},
                    'expected_file_name': {'type': 'string', 'minLength': 1, 'maxLength': 300, 'description': 'continue_download only: exact filename heading observed in the live file listing; do not infer from document title.'},
                    'section': {'type': 'string', 'enum': list(READ_SECTIONS), 'description': 'inspect only: open a known read tab and read back the same document. Original-view metadata is not fulltext/render proof.'},
                    'menu': {'type':'string','enum':list(READ_MENUS),'description':'inspect only, no pending task: click one exact live read-menu link and read back. Booking view is not creating a reservation; guides view is not download permission. Does not click writes/logout or supply form values.'},
                    'wait_seconds': {'type': 'integer', 'minimum': 0, 'maximum': 60, 'description': 'Bounded wait; default 0 returns a resumable pending state. Use resume to wait again.'},
                    'task': {'type': 'object', 'properties': {
                        'kind': {'type': 'string', 'enum': ['read', 'search', 'search_download_one']},
                        'query': {'type': 'string', 'minLength': 1, 'maxLength': 120},
                        'output_dir': {'type': 'string', 'minLength': 1, 'maxLength': 500, 'description': 'Selected one-file download only: explicitly approved absolute existing project output directory; never overwrite.'},
                        'action': {'type': 'string', 'enum': ['open']},
                        'url': {'type': 'string'},
                        'expected_code': {'type': 'string', 'minLength': 1, 'maxLength': 300},
                        'expected_title': {'type': 'string', 'minLength': 1, 'maxLength': 300}},
                        'required': ['kind'], 'additionalProperties': False}},
                    'required': ['action', 'work_id'], 'additionalProperties': False}},
        description='Visible human login, bounded wait and task resume', emoji='🌐')
