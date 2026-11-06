"""Exercise real file-input upload on a completed source snapshot, no acceptance grant."""
from pathlib import Path
import base64,hashlib,json,re,shutil,socket,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
S=R/'state/iter132-promotion-studio/promotion-05'
label,expected=sys.argv[1:]
out=M/label
assert out.parent==M and not out.exists()
state=json.loads((S/'run_state.json').read_text(encoding='utf8'))
assert state['nodes']['sem-node-0143']['status']!='RUNNING'
source=hashlib.sha256((R/'candidate/main.py').read_bytes()).hexdigest()
assert source==expected
out.mkdir();snapshot=out/'snapshot';snapshot.mkdir()
for p in (R/'candidate').glob('*.py'):shutil.copy2(p,snapshot/p.name)
shutil.copytree(R/'candidate/milestones',snapshot/'milestones',ignore=shutil.ignore_patterns('__pycache__'))
assert hashlib.sha256((snapshot/'main.py').read_bytes()).hexdigest()==source
png=out/'pixel.png';png.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a4gAAAABJRU5ErkJggg=='))
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
url='http://127.0.0.1:'+str(port)
report={'kind':'ActualGuiFileUploadDiagnostic','source_sha256':source,'acceptance_authority':False,'host_business_patches':0,'diagnostic_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
log=(out/'server.log').open('wb')
proc=subprocess.Popen(['D:/anaconda/python.exe','-X','utf8',str(snapshot/'main.py'),'--serve','--port',str(port),'--data',str(out/'data')],cwd=snapshot,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='msedge',headless=True)
  try:
   page=browser.new_page();page.set_default_timeout(8000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for _ in range(80):
    try:page.goto(url,wait_until='networkidle');break
    except Exception:time.sleep(.1)
   page.get_by_label('Project name',exact=True).fill('Actual upload diagnostic')
   with page.expect_response(lambda r:r.url.endswith('/api/action') and 'project.create' in (r.request.post_data or '')):
    page.get_by_role('button',name='Create project',exact=True).click()
   page.wait_for_timeout(200)
   pid=page.request.post(url+'/api/action',data={'milestone':'M1','op':'project.list'}).json()['items'][0]['id']
   nav=page.get_by_role('button',name='Media',exact=True)
   (nav if nav.count() else page.get_by_role('button',name='Content',exact=True)).click()
   kind=page.get_by_label('Media kind',exact=True)
   if kind.count():kind.select_option('image')
   field=page.get_by_label('Media file',exact=True)
   if not field.count():field=page.get_by_label('Upload media',exact=True)
   field.set_input_files(str(png))
   with page.expect_response(lambda r:r.request.method=='POST' and ('media.import' in (r.request.post_data or '') or r.url.endswith('/api/media/upload'))) as pending:
    page.get_by_role('button',name=re.compile('^Import media$',re.I)).click()
   response=pending.value;record=response.json();page.wait_for_timeout(250)
   report.update(upload_http_status=response.status,upload_response=record,request_path=response.url.removeprefix(url),visible_alerts=page.locator('[role="alert"]').all_text_contents(),page_errors=errors)
   if response.ok:
    assert record['sha256']==hashlib.sha256(png.read_bytes()).hexdigest(),'Uploaded SHA mismatch'
    asset=page.request.get(url+'/media/'+record['id'],params={'project_id':pid})
    assert asset.ok and asset.body()==png.read_bytes(),'Served media bytes differ'
    report['served_bytes_match']=True
    previews=page.locator('img:visible')
    report['visible_library_preview_count']=previews.count()
    if previews.count():
     page.wait_for_function('Array.from(document.images).some(e=>e.complete && e.naturalWidth>0 && e.getBoundingClientRect().width>0)')
     report['visible_image_decoded']=True
    bad=page.request.post(url+'/api/action',data={'milestone':'M11','op':'media.import','project_id':pid,'kind':'image','filename':'invalid.png','data':'not-base64!!!'})
    report['invalid_upload_http_status']=bad.status
    assert bad.status==400,'Malformed upload must fail with HTTP400'
   report['diagnostic_passed']=response.ok and report.get('served_bytes_match',False) and report.get('invalid_upload_http_status')==400 and not errors
   report['limitations']='Attached-content image/video preview and full publication are checked separately; absence of a library thumbnail is not a product failure.'
   page.screenshot(path=str(out/'upload.png'),full_page=True)
  finally:browser.close()
except Exception as e:report.update(diagnostic_passed=False,error_type=type(e).__name__,error=str(e))
finally:
 proc.terminate()
 try:proc.wait(timeout=5)
 except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
 log.close()
 (out/'receipt.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
 print(json.dumps(report,ensure_ascii=False))
