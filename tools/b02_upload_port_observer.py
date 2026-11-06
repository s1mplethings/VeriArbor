"""Narrow independent observation for admission; NOT full B02 certification."""
import base64, hashlib, json, os, re, socket, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

def concurrent_preview(url,expected_hash):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from urllib.request import urlopen
    from urllib.error import HTTPError
    barrier=Barrier(4)
    def fetch(index):
        barrier.wait(timeout=10)
        try:
            with urlopen(url,timeout=10) as response:
                return {'index':index,'status':response.status,'sha256':hashlib.sha256(response.read()).hexdigest()}
        except HTTPError as error:return {'index':index,'status':error.code,'error':error.read().decode('utf8')[:700]}
    with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(fetch,range(12)))
    return {'passed':all(r['status']==200 and r.get('sha256')==expected_hash for r in rows),'requests':rows}

def observe(workspace,out):
    workspace=Path(workspace);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    raw=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a4gAAAABJRU5ErkJggg==')
    png=out/'pixel.png';png.write_bytes(raw)
    source=hashlib.sha256((workspace/'main.py').read_bytes()).hexdigest()
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    url='http://127.0.0.1:'+str(port);log=(out/'server.log').open('wb')
    command=[sys.executable,'-X','utf8',str(workspace/'main.py'),'--serve','--port',str(port),'--data',str(out/'data')]
    p=subprocess.Popen(command,cwd=workspace,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    report={'source_sha256':source,'checks':[],'scope':'Browser image upload port only; not B02/M12 completion'}
    def check(name,value):
        if not value:raise AssertionError(name)
        report['checks'].append(name)
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='msedge',headless=True);report['browser']=browser.version
            page=browser.new_page();page.set_default_timeout(8000)
            try:
                for _ in range(100):
                    try:page.goto(url,wait_until='networkidle');break
                    except Exception:time.sleep(.1)
                page.get_by_label('Project name',exact=True).fill('Upload port control')
                with page.expect_response(lambda r:'project.create' in (r.request.post_data or '')) as pending:page.get_by_role('button',name='Create project',exact=True).click()
                pid=pending.value.json()['id'];page.get_by_text('Upload port control',exact=True).filter(visible=True).first.wait_for()
                nav=page.get_by_role('button',name='Media',exact=True)
                (nav if nav.count() else page.get_by_role('button',name='Content',exact=True)).click()
                kind=page.get_by_label('Media kind',exact=True)
                if kind.count():kind.select_option('image')
                field=page.get_by_label('Media file',exact=True)
                if not field.count():field=page.get_by_label('Upload media',exact=True)
                field.set_input_files(str(png))
                with page.expect_response(lambda r:r.request.method=='POST' and ('media.import' in (r.request.post_data or '') or '/api/media/upload' in r.url)) as pending:
                    page.get_by_role('button',name=re.compile('^Import media$',re.I)).click()
                response=pending.value;record=response.json();report['upload']={'status':response.status,'body':record}
                check('browser image upload HTTP200',response.status==200)
                check('real identity',isinstance(record.get('id'),str) and bool(record['id']))
                check('project and bytes binding',record.get('project_id')==pid and record.get('sha256')==hashlib.sha256(raw).hexdigest())
                media=page.request.get(url+'/media/'+record['id'],params={'project_id':pid})
                check('owned preview bytes',media.status==200 and media.body()==raw)
                report['concurrent_preview']=concurrent_preview(url+'/media/'+record['id']+'?project_id='+pid,hashlib.sha256(raw).hexdigest())
                check('concurrent owned preview reads return exact bytes',report['concurrent_preview']['passed'])
                bad=page.request.post(url+'/api/action',data={'milestone':'M11','op':'media.import','project_id':pid,'kind':'image','filename':'invalid.png','data':'not-base64!!!'})
                check('invalid browser payload rejected',bad.status==400)
                report['status']='PASS'
            except Exception as e:report.update(status='FAIL',error=type(e).__name__+': '+str(e))
            finally:page.screenshot(path=str(out/'browser.png'),full_page=True);browser.close()
    finally:
        p.terminate()
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
        log.close()
    check('source unchanged',source==hashlib.sha256((workspace/'main.py').read_bytes()).hexdigest())
    report['startup']={'command':command,'url':url};report['cleanup']={'server_stopped':p.poll() is not None}
    (out/'receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return report

if __name__=='__main__':print(json.dumps(observe(sys.argv[1],sys.argv[2]),ensure_ascii=False))
