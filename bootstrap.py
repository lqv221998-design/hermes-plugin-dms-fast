"""Recipient setup helper. No change on import or audit; explicit phase approvals."""
import re
from pathlib import Path
import hashlib,importlib.util,json,os,platform,shutil,subprocess,sys,datetime,argparse
ROOT=Path(__file__).resolve().parent

def installer():
    spec=importlib.util.spec_from_file_location('_dms_bundle_install',ROOT/'install.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def verify_bundle(root=ROOT):
    root=Path(root)
    document=json.loads((root/'SHA256SUMS.json').read_text(encoding='utf-8'))
    files=document.get('files')
    if not isinstance(files,dict) or not 0<len(files)<=10000:raise ValueError('Invalid bundle manifest')
    for name,value in files.items():
        p=Path(name)
        if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name or name=='SHA256SUMS.json':raise ValueError('Unsafe manifest path')
        target=root/p
        for ancestor in [target,*target.parents]:
            if ancestor.is_symlink() or (hasattr(ancestor,'is_junction') and ancestor.is_junction()):raise ValueError('Linked bundle path')
            if ancestor==root:break
        if not re.fullmatch('[0-9a-f]{64}',value or '') or not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest()!=value:raise ValueError('Payload missing or changed: '+name)
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!='SHA256SUMS.json'}
    if actual!=set(files):raise ValueError('Unexpected/missing payload files')
    return len(files)

def node_supported(value):
    m=re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)',value.strip())
    if not m:return False
    v=tuple(map(int,m.groups()))
    return (v[0]==22 and v>=(22,12,0)) or v[0] in (24,26)

def plan_from_facts(facts):
    packages=[]
    if not facts.get('python_supported'):packages.append('python')
    if not node_supported(facts.get('node_version') or '') or not facts.get('npm_cli'):packages.append('node')
    if not facts.get('chrome'):packages.append('chromium')
    return {'pm_packages':packages,'requires_dependency_consent':True,'ready_to_use':False,
            'host_runtime_pending':not facts.get('python_supported') or not facts.get('hermes_api'),
            'pending':['operator consent','browser/native-chat acceptance','recipient DMS login/ACL','LLM data-policy acceptance']}

def connector_entry(home, facts):
    return {'command':facts['node'],'args':[facts['mcp_bin'],
        '--executable-path='+facts['chrome'],'--user-data-dir='+str(Path(home)/'browser-profiles/dms-fast-setup'),
        '--no-usage-statistics','--no-performance-crux','--no-javascript-evaluation','--no-source-maps',
        '--categoryInput=true','--categoryDebugging=true','--categoryEmulation=false','--categoryPerformance=false',
        '--categoryNetwork=false','--categoryMemory=false','--filesystem-root='+str(Path(home)/'cache/dms-fast-setup')],
        'enabled':True,'trust':'untrusted','timeout':30,'connect_timeout':30,'supports_parallel_tool_calls':False,
        'tools':{'include':['list_pages','new_page','take_snapshot','navigate_page','fill','press_key','click'],'resources':False,'prompts':False},
        'sampling':{'enabled':False},'elicitation':{'enabled':False}}

def command(argv,env=None,timeout=300):
    result=subprocess.run([str(a) for a in argv],capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=timeout,shell=False)
    if result.returncode:raise RuntimeError('Command failed (output withheld to avoid leaking profile data), exit='+str(result.returncode))
    return result.stdout.strip()

def audit_environment(home):
    facts={'os':platform.system(),'arch':platform.machine(),'python':platform.python_version(),'python_executable':sys.executable,
        'python_supported':sys.version_info[:2]==(3,14),'hermes_api':False,'node':None,'node_version':None,'npm_cli':None,'chrome':None,'mcp_bin':None}
    try:
        from hermes_cli.plugins import PluginContext
        import mcp
        facts['hermes_api']=all(hasattr(PluginContext,n) for n in ('call_mcp','get_config','register_tool','register_hook','register_command','register_skill'))
    except ImportError:pass
    try:
        import pm
        node=pm.installed_package('node');chrome=pm.installed_package('chromium')
        if node and node.binary and node.binary.is_file():facts['node']=str(node.binary)
        if chrome and chrome.binary and chrome.binary.is_file():facts['chrome']=str(chrome.binary);facts['managed_browser_version']=chrome.version
    except (ImportError,ValueError,AttributeError,OSError):pass
    facts['node']=facts['node'] or shutil.which('node')
    if facts['node']:
        try:facts['node_version']=command([facts['node'],'--version'],timeout=20).lstrip('v')
        except (RuntimeError,OSError,subprocess.TimeoutExpired):pass
        node=Path(facts['node']).resolve()
        for candidate in [node.parent/'node_modules/npm/bin/npm-cli.js',node.parent.parent/'lib/node_modules/npm/bin/npm-cli.js',Path('/usr/share/nodejs/npm/bin/npm-cli.js')]:
            if candidate.is_file():facts['npm_cli']=str(candidate);break
    if not facts['chrome']:
        candidates=[shutil.which('google-chrome'),shutil.which('google-chrome-stable'),'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']
        for key in ('PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA'):
            if os.environ.get(key):candidates.append(str(Path(os.environ[key])/'Google/Chrome/Application/chrome.exe'))
        facts['chrome']=next((str(p) for p in candidates if p and Path(p).is_file()),None)
    package=Path(home)/'plugin-tools/dms-fast-setup/node_modules/chrome-devtools-mcp/package.json'
    if package.is_file():
        data=json.loads(package.read_text(encoding='utf-8'))
        if data.get('version')=='1.10.1':
            name=data['bin']['chrome-devtools-mcp'];p=Path(name)
            if not p.is_absolute() and '..' not in p.parts:
                binary=package.parent/p
                if binary.is_file():facts['mcp_bin']=str(binary)
    return facts

def install_dependencies(home):
    safe=installer();home=safe.checked_path(home,must_exist=True,directory=True)
    facts=audit_environment(home)
    if not facts['python_supported'] or not facts['hermes_api']:raise RuntimeError('Rerun using supported Hermes Python 3.14 runtime; repair through installation owner, not pip')
    packages=[name for name in plan_from_facts(facts)['pm_packages'] if name!='python']
    if packages:
        command([sys.executable,'-m','pm.cli','install',*packages],timeout=900)
        facts=audit_environment(home)
    if not node_supported(facts['node_version'] or '') or not facts['npm_cli'] or not facts['chrome']:raise RuntimeError('Tool prerequisites still unavailable; inspect explicit PM diagnostics; no fallback')
    prefix=safe.checked_path(home/'plugin-tools/dms-fast-setup',directory=True)
    req=json.loads((ROOT/'requirements.json').read_text(encoding='utf-8'))['mcp']
    new_prefix=not prefix.exists()
    if new_prefix:
        prefix.mkdir(parents=True);safe.checked_path(prefix,must_exist=True,directory=True)
        cache=safe.checked_path(home/'cache/dms-fast-npm',directory=True);cache.mkdir(parents=True,exist_ok=True)
        env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','HOME','USERPROFILE','LOCALAPPDATA','APPDATA','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','LANG','LC_ALL'}}
        for kind in ('user','global'):
            f=prefix/('npm-'+kind+'.config');f.write_text('',encoding='utf-8');env['NPM_CONFIG_'+kind.upper()+'CONFIG']=str(f)
        env.update({'NPM_CONFIG_CACHE':str(cache),'TEMP':str(cache),'TMP':str(cache),'TMPDIR':str(cache),'CI':'1'})
        command([facts['node'],facts['npm_cli'],'install','--prefix',prefix,'--ignore-scripts','--no-audit','--no-fund',
            '--registry=https://registry.npmjs.org','--save-exact',req['name']+'@'+req['version']],env=env,timeout=900)
    receipt=safe.checked_path(prefix/'installed-integrity.json',directory=False)
    hashes={}
    for file in prefix.rglob('*'):
        if file==receipt or not file.is_file():continue
        if file.is_symlink():
            if not file.resolve().is_relative_to(prefix):raise ValueError('Npm payload symlink escapes prefix')
        hashes[file.relative_to(prefix).as_posix()]=hashlib.sha256(file.read_bytes()).hexdigest()
    if not new_prefix:
        if not receipt.is_file() or json.loads(receipt.read_text(encoding='utf-8')).get('files')!=hashes:raise ValueError('Previously installed package bytes changed or ownership receipt missing; stop before execution')
    lock=safe.checked_path(prefix/'package-lock.json',must_exist=True,directory=False)
    data=json.loads(lock.read_text(encoding='utf-8'))
    pinned=data.get('packages',{}).get('node_modules/chrome-devtools-mcp',{})
    if pinned.get('version')!=req['version'] or pinned.get('integrity')!=req['integrity']:raise ValueError('Package pin/integrity mismatch or interrupted install; keep files, stop')
    if new_prefix:receipt.write_text(json.dumps({'files':hashes},indent=2),encoding='utf-8')
    facts=audit_environment(home)
    if not facts['mcp_bin']:raise ValueError('Installed MCP entry point missing')
    safe.checked_path(facts['mcp_bin'],must_exist=True,directory=False)
    observed=command([facts['node'],facts['mcp_bin'],'--version'],timeout=30)
    if req['version'] not in observed:raise ValueError('MCP CLI version does not match pin')
    return {'status':'dependencies_installed_not_browser_verified','mcp_version':req['version'],'integrity_verified':True,'lock_sha256':hashlib.sha256(lock.read_bytes()).hexdigest(),'facts':facts,'ready_to_use':False}

def configuration_recipe(home,server,facts):
    if not re.fullmatch(r'[A-Za-z0-9_]{1,64}',server):raise ValueError('Use an unambiguous unused underscore-only server key')
    if any(not facts.get(n) for n in ('node','chrome','mcp_bin')):raise ValueError('Run approved deps first; cannot emit usable paths while prerequisites are missing')
    return {'status':'recipe_only_not_applied','home':str(home),'server_key':server,
        'connector':connector_entry(home,facts),'plugin_settings':{'mcp_server':server,'mcp_allowlist':[server]},
        'create_after_consent':[str(Path(home)/'browser-profiles/dms-fast-setup'),str(Path(home)/'cache/dms-fast-setup')],
        'gates':['keep existing server/plugin untouched; resolve collision before writing','private config backup','explicit connector/config/allowlist consent','explicit plugin enable consent','read back exact target and whole unrelated configuration','native chat reload/approval and own DMS login'],
        'ready_to_use':False}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['audit','deps','install','recipe'],nargs='?',default='audit')
    parser.add_argument('--home',required=True)
    parser.add_argument('--approve-dependencies',action='store_true')
    parser.add_argument('--approve-install',action='store_true')
    parser.add_argument('--include-panel',action='store_true')
    parser.add_argument('--server',default='chrome_dms_setup')
    args=parser.parse_args(argv)
    if args.phase=='deps' and not args.approve_dependencies:raise PermissionError('Requires --approve-dependencies after recipient consent')
    if args.phase=='install' and not args.approve_install:raise PermissionError('Requires --approve-install after recipient consent')
    verify_bundle(ROOT)
    safe=installer()
    home=safe.checked_path(args.home,must_exist=True,directory=True)
    if not (home/'config.yaml').is_file():raise ValueError('Select existing recipient Hermes profile, not a new/guessed home')
    if args.phase=='install':
        result={'status':'installed_disabled','copied':safe.install(home,include_panel=args.include_panel),'config_unchanged':True,'ready_to_use':False}
        print(json.dumps(result,ensure_ascii=False,indent=2));return result
    facts=audit_environment(home)
    if args.phase=='audit':
        result={'status':'audit_only','bundle_files_verified':verify_bundle(ROOT),'facts':facts,'plan':plan_from_facts(facts),'config_unchanged':True}
        print(json.dumps(result,ensure_ascii=False,indent=2));return result
    if args.phase=='deps':
        result=install_dependencies(home);print(json.dumps(result,ensure_ascii=False,indent=2));return result
    if args.phase=='recipe':
        result=configuration_recipe(home,args.server,facts);print(json.dumps(result,ensure_ascii=False,indent=2));return result

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,RuntimeError,PermissionError,subprocess.TimeoutExpired) as exc:
        print('STOP:',type(exc).__name__,str(exc),file=sys.stderr);raise SystemExit(1)
