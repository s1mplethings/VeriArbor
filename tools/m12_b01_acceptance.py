"""Independent B01 browser check on an isolated, frozen candidate snapshot.

No product writes. A local result is not a complete M12 acceptance verdict.
"""
from pathlib import Path
import ast, hashlib, json, re, shutil, socket, subprocess, sys, time
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright

R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')

def require(value,message):
    if not value:raise AssertionError(message)

def preflight(html,out):
    class Parser(HTMLParser):
        def __init__(self):super().__init__();self.ids=[]
        def handle_starttag(self,tag,attrs):
            value=dict(attrs).get('id')
            if value:self.ids.append(value)
    parser=Parser();parser.feed(html)
    duplicates=[k for k,v in Counter(parser.ids).items() if v>1]
    require(not duplicates,'duplicate DOM IDs: '+str(duplicates))
    scripts=re.findall(r'<script[^>]*>(.*?)</script>',html,re.S|re.I)
    require(bool(scripts),'missing JavaScript')
    script=out/'rendered.js';script.write_text('\n'.join(scripts),encoding='utf8')
    result=subprocess.run(['node','--check',str(script)],capture_output=True,text=True,encoding='utf8',timeout=20)
    require(result.returncode==0,'JS parse: '+result.stderr)
    refs=set(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)",script.read_text(encoding='utf8')))
    require(refs<=set(parser.ids),'dangling literal DOM references: '+str(refs-set(parser.ids)))
    return {'html_parsed':True,'js_parse':True,'duplicate_ids':duplicates,'literal_dom_references_resolved':True}

def browser_check(page,url,out):
    network=[];errors=[];console=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('console',lambda msg:console.append({'type':msg.type,'text':msg.text}))
    def response(r):
        item={'url':r.url,'method':r.request.method,'status':r.status}
        if r.request.post_data:item['request_body']=r.request.post_data
        network.append(item)
    page.on('response',response);page.set_default_timeout(8000)
    report={'checks':[],'network':network,'javascript_errors':errors,'console':console}
    def check(name,value):require(value,name);report['checks'].append(name)
    try:
        page.goto(url,wait_until='networkidle')
        report['preflight']=preflight(page.content(),out)
        # User-visible empty state; input placeholders alone are not evidence.
        check('visible empty state',bool(re.search(r'no projects|no project yet|create (?:your |a |the )?first project|暂无项目|还没有项目',page.locator('body').inner_text(),re.I)))
        page.get_by_label('Project name',exact=True).fill('Browser Created Project')
        with page.expect_response(lambda r:r.request.method=='POST' and 'project.create' in (r.request.post_data or '')) as pending:
            page.get_by_role('button',name='Create project',exact=True).click()
        response=pending.value;created=response.json();pid=created.get('id')
        check('project.create HTTP200',response.status==200)
        check('real nonempty project identity',isinstance(pid,str) and bool(pid))
        page.get_by_text('Browser Created Project',exact=True).filter(visible=True).first.wait_for()
        check('created project name visible',True)
        page.wait_for_function('(id) => typeof currentProjectId !== "undefined" && currentProjectId === id',arg=pid)
        check('created identity selected',True)
        page.wait_for_function('() => document.readyState === "complete"')
        page.wait_for_timeout(250)
        state_requests=lambda:[x for x in network if urlparse(x['url']).path=='/api/state']
        check('selected state fetched by UI',any(parse_qs(urlparse(x['url']).query).get('project_id')==[pid] and x['status']==200 for x in state_requests()))
        state=page.request.get(url+'/api/state',params={'project_id':pid})
        check('selected state available',state.status==200 and state.json().get('project',{}).get('id')==pid)
        page.screenshot(path=str(out/'created.png'),full_page=True)
        prior=len(network);page.reload(wait_until='networkidle')
        page.get_by_text('Browser Created Project',exact=True).filter(visible=True).first.wait_for()
        check('name remains visible after refresh',True)
        page.wait_for_function('(id) => typeof currentProjectId !== "undefined" && currentProjectId === id',arg=pid)
        check('selection remains after refresh',True)
        page.wait_for_timeout(250)
        check('refresh fetches selected state',any(urlparse(x['url']).path=='/api/state' and parse_qs(urlparse(x['url']).query).get('project_id')==[pid] and x['status']==200 for x in network[prior:]))
        check('never requests state without identity',all(parse_qs(urlparse(x['url']).query).get('project_id',[''])[0] for x in state_requests()))
        check('no JavaScript initialization errors',not errors)
        check('no unexpected HTTP failures',not [x for x in network if x['status']>=400 and urlparse(x['url']).path!='/favicon.ico'])
        page.screenshot(path=str(out/'refreshed.png'),full_page=True)
        report.update(status='PASS',project_id=pid)
    except Exception as error:
        report.update(status='FAIL',error=type(error).__name__+': '+str(error))
        try:page.screenshot(path=str(out/'failure.png'),full_page=True)
        except Exception:pass
    return report

def main():
    out=M/sys.argv[1];assert out.parent==M and not out.exists();out.mkdir()
    state=json.loads((R/'state/iter132-promotion-studio/promotion-05/run_state.json').read_text(encoding='utf8'))
    require(not any(x['status']=='RUNNING' for x in state['nodes'].values()),'candidate is not frozen')
    snapshot=out/'snapshot';snapshot.mkdir()
    for p in (R/'candidate').glob('*.py'):shutil.copy2(p,snapshot/p.name)
    shutil.copytree(R/'candidate/milestones',snapshot/'milestones',ignore=shutil.ignore_patterns('__pycache__'))
    source_hash=hashlib.sha256((snapshot/'main.py').read_bytes()).hexdigest()
    ast.parse((snapshot/'main.py').read_text(encoding='utf8'))
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    url='http://127.0.0.1:'+str(port);log=(out/'server.log').open('wb')
    command=['D:/anaconda/python.exe','-X','utf8',str(snapshot/'main.py'),'--serve','--port',str(port),'--data',str(out/'data')]
    process=subprocess.Popen(command,cwd=snapshot,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='msedge',headless=True)
            for _ in range(80):
                try:
                    with socket.create_connection(('127.0.0.1',port),timeout=.2):break
                except OSError:time.sleep(.1)
            page=browser.new_page();result=browser_check(page,url,out);version=browser.version;browser.close()
    finally:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
        log.close()
    result.update(kind='B01ProjectBootstrapAcceptance',block_id='B01',source_sha256=source_hash,
        checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),browser=version,
        startup={'command':command,'url':url,'data_dir':str(out/'data')},cleanup={'server_stopped':process.poll() is not None},
        authority='Independent local block evidence; not full M12 GoalAcceptance',host_business_patches=0)
    require(source_hash==hashlib.sha256((R/'candidate/main.py').read_bytes()).hexdigest(),'candidate changed during check')
    (out/'receipt.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['network','console']},ensure_ascii=False))

if __name__=='__main__':main()
