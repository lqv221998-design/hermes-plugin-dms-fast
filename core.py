"""Local DMS navigation policy. No browser connection or network client."""
import re

BASE = 'https://dms.newtecons.vn'
DOC_PATTERN = r'/document/detail/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
ROUTES = {'home': BASE+'/', 'list': BASE+'/document/list', 'dept': BASE+'/document/dept', 'site': BASE+'/document/site', 'booking': BASE+'/schedule/booking'}

def validate_url(value):
    if not isinstance(value, str) or not (value in ROUTES.values() or re.fullmatch(re.escape(BASE)+DOC_PATTERN, value)):
        raise ValueError('Only exact HTTPS DMS read routes and canonical lowercase document UUID URLs are allowed; no query, fragment or credentials.')
    return value


def parse_snapshot(text):
    root = re.search(r'RootWebArea "([^"]*)" url="([^"]+)"', text)
    if not root:
        raise ValueError('Missing semantic page root')
    documents = {}
    for uid, title, url in re.findall(r'uid=(\S+) link "([^"]*)" url="([^"]+)"', text):
        if re.fullmatch(re.escape(BASE)+DOC_PATTERN, url):
            documents.setdefault(url, {'title': title, 'url': url, 'uid': uid})
    values = re.findall(r'StaticText "([^"\n]*)"', text)
    fields = {'Số hiệu', 'Mã hiệu', 'Nơi ban hành', 'Loại văn bản', 'Lần ban hành', 'Người ký', 'Ngày hiệu lực', 'Ngày hết hiệu lực', 'Tình trạng'}
    metadata = {}
    for i, value in enumerate(values):
        if value in fields and re.fullmatch(re.escape(BASE)+DOC_PATTERN, root[2]):
            metadata[value] = values[i+1] if i+1 < len(values) and values[i+1] not in fields else ''
    tabs = {}
    for uid, label in re.findall(r'uid=(\S+) link "(Thông tin|Văn bản gốc)" url="javascript:;"', text):
        tabs.setdefault(label, []).append(uid)
    headings = re.findall(r'^\s*uid=\S+ heading "([^"\n]+)"', text, re.MULTILINE)
    return {'title': root[1], 'url': root[2], 'headings': headings, 'metadata': metadata, 'tabs': tabs, 'documents': list(documents.values()),
            'full_document_read': False, 'inventory_complete': False,
            'login_required': 'Đăng xuất' not in text,
            'permission_denied': any(s in text.lower() for s in ['không có quyền', 'access denied', 'không được phép'])}
