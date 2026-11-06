"""Independent scoped media/browser acceptance; never edits product sources."""
from pathlib import Path
import base64, hashlib, json, os, re, shutil, socket, subprocess, sys, time
from playwright.sync_api import sync_playwright
from m12_b01_acceptance import preflight, require
from b02_upload_port_observer import concurrent_preview

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def adapter_edge_probe(snapshot,out,png):
    """Observe the real adapter->M11 call and cleanup, including backend failure."""
    code=r'''
import base64,hashlib,importlib.util,json,os,pathlib,sys,tempfile
workspace,out,png=map(pathlib.Path,sys.argv[1:]);sys.path.insert(0,str(workspace))
temp=out/'edge-temporary';temp.mkdir();os.environ['TEMP']=os.environ['TMP']=str(temp);tempfile.tempdir=None
spec=importlib.util.spec_from_file_location('edge_product',workspace/'main.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
data=out/'edge-data';data.mkdir();project=mod.handle(str(data),{'milestone':'M1','op':'project.create','name':'Adapter edge'})
original=mod.HANDLERS['M11'];seen=[];fail=False;raw=png.read_bytes()
def spy(folder,request):
    if request['op']=='media.import':
        path=pathlib.Path(request['path']);assert path.is_absolute() and path.is_file();assert path.resolve().is_relative_to(out.resolve());assert path.read_bytes()==raw
        seen.append(str(path))
        if fail:raise ValueError('injected downstream import failure')
    return original(folder,request)
mod.HANDLERS['M11']=spy;mod.m11_handle=spy
request={'milestone':'M11','op':'media.import','project_id':project['id'],'kind':'image','filename':'pixel.png','data':base64.b64encode(raw).decode()}
record=mod.handle(str(data),request);assert seen and not pathlib.Path(seen[-1]).exists();assert pathlib.Path(record['path']).read_bytes()==raw
fail=True
try:mod.handle(str(data),request)
except ValueError as error:assert 'injected downstream' in str(error)
else:raise AssertionError('backend error swallowed')
assert len(seen)==2 and not pathlib.Path(seen[-1]).exists()
fail=False;request['filename']='../qualification-escape.png'
try:mod.handle(str(data),request)
except ValueError:pass
assert all(not pathlib.Path(path).exists() for path in seen)
assert not list(temp.rglob('*.png'))
print(json.dumps({'status':'PASS','temporary_paths':seen,'checks':['real path passed to original M11','confined absolute temporary file','untrusted filename cannot escape','success cleanup','downstream failure cleanup','durable original M11 copy']}))
'''
    script=out/'edge_probe.py';script.write_text(code,encoding='utf8')
    p=subprocess.run([sys.executable,'-X','utf8',str(script),str(snapshot),str(out),str(png)],capture_output=True,text=True,encoding='utf8',timeout=30)
    require(p.returncode==0,'adapter edge probe: '+p.stderr[-1800:])
    return json.loads(p.stdout)

def run(workspace, out):
    workspace=Path(workspace);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    snapshot=out/'snapshot';snapshot.mkdir()
    for p in workspace.glob('*.py'):shutil.copy2(p,snapshot/p.name)
    shutil.copytree(workspace/'milestones',snapshot/'milestones',ignore=shutil.ignore_patterns('__pycache__'))
    subjects={p.relative_to(snapshot).as_posix():digest(p) for p in snapshot.rglob('*.py')};source=subjects['main.py'];data=out/'data';temp=out/'temporary';temp.mkdir()
    png=out/'pixel.png';png.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a4gAAAABJRU5ErkJggg=='))
    video=out/'clip.mp4'
    fixture=subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=32x32:d=0.3','-an','-c:v','libx264','-pix_fmt','yuv420p',str(video)],capture_output=True,timeout=30)
    require(fixture.returncode==0,'real video fixture generation failed')
    result={'subject_hashes':subjects,'checker_dependencies':{'B01_preflight':digest(Path(__file__).with_name('m12_b01_acceptance.py')),'B02_concurrency':digest(Path(__file__).with_name('b02_upload_port_observer.py'))},'kind':'B02BrowserUploadAcceptance','block_id':'B02','source_sha256':source,'checker_sha256':digest(__file__),'checks':[],'network':[],'console':[],'javascript_errors':[],'host_business_patches':0}
    process=None;log=(out/'server.log').open('wb')
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    url='http://127.0.0.1:'+str(port)
    command=[sys.executable,'-X','utf8',str(snapshot/'main.py'),'--serve','--port',str(port),'--data',str(data)]
    def start():
        p=subprocess.Popen(command,cwd=snapshot,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'TEMP':str(temp),'TMP':str(temp),'PYTHONDONTWRITEBYTECODE':'1'},creationflags=subprocess.CREATE_NO_WINDOW)
        for _ in range(100):
            try:
                with socket.create_connection(('127.0.0.1',port),timeout=.2):return p
            except OSError:time.sleep(.1)
        p.terminate();raise AssertionError('server startup timeout')
    def stop(p):
        p.terminate()
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
    def check(name,value):require(value,name);result['checks'].append(name)
    try:
        process=start()
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='msedge',headless=True);result['browser']=browser.version
            page=browser.new_page();page.set_default_timeout(8000)
            page.on('pageerror',lambda e:result['javascript_errors'].append(str(e)))
            page.on('console',lambda e:result['console'].append({'type':e.type,'text':e.text}))
            def capture_response(response):
                item={'url':response.url,'status':response.status,'method':response.request.method}
                if response.status>=400:
                    try:item['error_body']=response.text()[:1000]
                    except Exception:pass
                result['network'].append(item)
            page.on('response',capture_response)
            try:
                page.goto(url,wait_until='networkidle');result['preflight']=preflight(page.content(),out)
                page.get_by_label('Project name',exact=True).fill('Upload acceptance project')
                with page.expect_response(lambda r:'project.create' in (r.request.post_data or '')) as pending:page.get_by_role('button',name='Create project',exact=True).click()
                pid=pending.value.json()['id'];page.get_by_text('Upload acceptance project',exact=True).filter(visible=True).first.wait_for()
                def action(op,**args):return page.request.post(url+'/api/action',data={'op':op,**args})
                foreign=action('project.create',milestone='M1',name='Foreign media project').json()['id']
                nav=page.get_by_role('button',name='Media',exact=True)
                (nav if nav.count() else page.get_by_role('button',name='Content',exact=True)).click()
                field=page.get_by_label('Media file',exact=True)
                if not field.count():field=page.get_by_label('Upload media',exact=True)
                button=page.get_by_role('button',name=re.compile('^Import media$',re.I))
                button.click();page.wait_for_timeout(150)
                check('missing browser file visibly rejected',any(re.search(r'file|choose|select|文件',text,re.I) for text in page.locator('[role="alert"]:visible').all_text_contents()))
                imported=[]
                for kind,path in [('image',png),('video',video)]:
                    page.get_by_label('Media kind',exact=True).select_option(kind);field.set_input_files(str(path))
                    with page.expect_response(lambda r:r.request.method=='POST' and ('media.import' in (r.request.post_data or '') or '/api/media/upload' in r.url)) as pending:button.click()
                    response=pending.value;record=response.json();result[kind+'_response']={'status':response.status,'body':record}
                    check(kind+' browser import HTTP200',response.status==200)
                    check(kind+' real identity/hash/project binding',bool(record.get('id')) and record.get('project_id')==pid and record.get('sha256')==digest(path))
                    tag='img' if kind=='image' else 'video'
                    preview=page.locator(tag+':visible')
                    preview.first.wait_for(state='visible')
                    check(kind+' visible preview',preview.count()>0)
                    if kind=='image':page.wait_for_function('Array.from(document.images).some(e=>e.complete&&e.naturalWidth>0&&e.getBoundingClientRect().width>0)')
                    else:page.wait_for_function('Array.from(document.querySelectorAll("video")).some(e=>e.readyState>=1&&e.videoWidth>0&&e.getBoundingClientRect().width>0)')
                    check(kind+' browser decodes preview',True)
                    asset=page.request.get(url+'/media/'+record['id'],params={'project_id':pid})
                    check(kind+' served bytes exact',asset.status==200 and asset.body()==path.read_bytes())
                    check(kind+' correct MIME',asset.headers.get('content-type','').startswith(kind+'/'))
                    denied=page.request.get(url+'/media/'+record['id'],params={'project_id':foreign})
                    check(kind+' foreign project cannot read media',denied.status in (400,403,404))
                    owned=Path(record['path']);check(kind+' durable owned copy',owned.is_file() and owned.resolve().is_relative_to(data.resolve()) and owned.read_bytes()==path.read_bytes())
                    imported.append((record,path));check(kind+' temporary files cleaned',not [p for p in temp.rglob('*') if p.is_file()]); check(kind+' no duplicate temporary media in data',not [p for p in data.rglob('*') if p.is_file() and p.suffix.lower() not in ('.json','.db','.sqlite','.sqlite3') and not p.resolve().is_relative_to((data/'media_storage').resolve())])
                direct=action('media.import',milestone='M11',project_id=pid,kind='image',path=str(png))
                check('existing server-path import port remains supported',direct.status==200 and direct.json().get('sha256')==digest(png))
                wrong=action('media.import',milestone='M1',project_id=pid,kind='image',filename='pixel.png',data=base64.b64encode(png.read_bytes()).decode())
                check('browser adapter cannot bypass explicit milestone dispatch',wrong.status==400)
                image_record=imported[0][0]
                result['concurrent_preview']=concurrent_preview(url+'/media/'+image_record['id']+'?project_id='+pid,image_record['sha256'])
                check('concurrent media previews preserve exact bytes without storage collisions',result['concurrent_preview']['passed'])
                # Same browser transport, explicit negative boundary controls.
                for name,payload in [('empty',''),('broken',base64.b64encode(b'broken media').decode()),('malformed','not-base64!!!')]:
                    bad=action('media.import',milestone='M11',project_id=pid,kind='image',filename='bad.png',data=payload)
                    check(name+' upload HTTP400',bad.status==400)
                    check(name+' upload cleanup',not [p for p in temp.rglob('*') if p.is_file()])
                check('original fixtures unchanged',digest(png)==imported[0][0]['sha256'] and digest(video)==imported[1][0]['sha256'])
                page.screenshot(path=str(out/'uploaded.png'),full_page=True)
                stop(process);process=start();page.reload(wait_until='networkidle')
                for record,path in imported:
                    got=action('media.get',milestone='M11',project_id=pid,media_id=record['id'])
                    asset=page.request.get(url+'/media/'+record['id'],params={'project_id':pid})
                    check(record['kind']+' restart durable identity/bytes',got.status==200 and got.json()['id']==record['id'] and asset.status==200 and asset.body()==path.read_bytes())
                # Real library reload and project switching, not only direct API reads.
                page.get_by_role('button',name='Media',exact=True).click()
                for record,_ in imported:
                    tag='img' if record['kind']=='image' else 'video'
                    item=page.locator(tag+'[src*="'+record['id']+'"]')
                    item.wait_for(state='visible')
                    item.evaluate('(e)=>new Promise((resolve,reject)=>{if((e.tagName==="IMG"&&e.complete&&e.naturalWidth>0)||(e.tagName==="VIDEO"&&e.readyState>=1&&e.videoWidth>0))return resolve();e.addEventListener(e.tagName==="IMG"?"load":"loadedmetadata",resolve,{once:true});e.addEventListener("error",()=>reject(Error("restored preview failed")),{once:true});setTimeout(()=>reject(Error("restored preview timeout")),7000)})')
                    check(record['kind']+' library preview restored after restart',True)
                page.get_by_role('button',name='Projects',exact=True).click()
                page.get_by_text('Foreign media project',exact=True).filter(visible=True).first.click()
                with page.expect_response(lambda r:'media.list' in (r.request.post_data or '') and foreign in (r.request.post_data or '')):
                    page.get_by_role('button',name='Media',exact=True).click()
                check('switch to foreign project clears old previews',page.locator('img:visible,video:visible').count()==0)
                check('no JavaScript errors',not result['javascript_errors'])
                result['adapter_edge']=adapter_edge_probe(snapshot,out,png)
                check('real adapter composition and cleanup on both outcomes',result['adapter_edge']['status']=='PASS')
                boundary_checker=Path(__file__).with_name('b02_dispatch_boundary_probe.py')
                result['checker_dependencies']['B02_dispatch']=digest(boundary_checker)
                boundary=subprocess.run([sys.executable,str(boundary_checker),str(snapshot),str(out/'dispatch-boundary')],capture_output=True,text=True,encoding='utf8',timeout=30)
                require(boundary.returncode==0,boundary.stderr)
                result['dispatch_boundary']=json.loads(boundary.stdout)
                check('explicit dispatch and unrelated milestone concurrency preserved',result['dispatch_boundary']['status']=='PASS')
                result['status']='PASS';result['project_id']=pid
            except Exception as e:
                result.update(status='FAIL',error=type(e).__name__+': '+str(e));page.screenshot(path=str(out/'failure.png'),full_page=True)
            finally:browser.close()
    finally:
        if process is not None:stop(process)
        log.close()
    require(all(digest(workspace/name)==expected for name,expected in subjects.items()),'candidate changed during block check')
    result.update(startup={'command':command,'url':url,'data_dir':str(data)},cleanup={'server_stopped':process.poll() is not None},fixture_hashes={'png':digest(png),'video':digest(video)})
    (out/'receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    return result

if __name__=='__main__':
    result=run(sys.argv[1],sys.argv[2]);print(json.dumps({k:v for k,v in result.items() if k!='network'},ensure_ascii=False))
