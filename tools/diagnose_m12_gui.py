"""Exercise actual final GUI upload/edit and project-scoped state in isolation."""
from pathlib import Path
import base64, hashlib, json, shutil, socket, subprocess, time
from playwright.sync_api import sync_playwright
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
out=M/'m12-gui-650460ff';out.mkdir(exist_ok=False)
snapshot=out/'snapshot';snapshot.mkdir()
for p in (R/'candidate').glob('*.py'):shutil.copy2(p,snapshot/p.name)
shutil.copytree(R/'candidate/milestones',snapshot/'milestones',ignore=shutil.ignore_patterns('__pycache__'))
sha=hashlib.sha256((snapshot/'main.py').read_bytes()).hexdigest();assert sha.startswith('650460ff')
png=out/'pixel.png';png.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a4gAAAABJRU5ErkJggg=='))
source=out/'evidence';source.mkdir();(source/'README.md').write_text('Offline workflows are supported.',encoding='utf8')
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
url='http://127.0.0.1:'+str(port);log=(out/'server.log').open('wb')
proc=subprocess.Popen(['D:/anaconda/python.exe','-X','utf8',str(snapshot/'main.py'),'--serve','--port',str(port),'--data',str(out/'data')],cwd=snapshot,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
report={'kind':'ActualM12GuiDiagnostic','source_sha256':sha,'acceptance_authority':False,'host_business_patches':0}
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='msedge',headless=True)
  try:
   page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for _ in range(80):
    try:page.goto(url);break
    except Exception:time.sleep(.1)
   def call(tag,op,**kw):
    response=page.request.post(url+'/api/action',data={'milestone':tag,'op':op,**kw})
    assert response.ok,(op,response.status,response.text())
    return response.json()
   def click_request(selector,op):
    with page.expect_response(lambda r:r.url.endswith('/api/action') and op in (r.request.post_data or '')) as observed:
     page.locator(selector).click()
    page.wait_for_timeout(250)
    return observed.value
   page.get_by_label('Project name',exact=True).fill('Final GUI diagnostic')
   click_request('#create-project','project.create')
   pid=call('M1','project.list')['items'][0]['id']
   page.locator('#nav-media').click();page.locator('#media-file').set_input_files(str(png))
   uploaded=click_request('#import-media','media.import')
   report['actual_file_input_upload']={'status':uploaded.status,'body':uploaded.json(),'alert':page.locator('#alert').inner_text()}
   page.locator('#nav-campaigns').click()
   page.get_by_label('Campaign name',exact=True).fill('Final Campaign')
   page.get_by_label('Audience',exact=True).fill('Developers')
   page.get_by_label('Channels',exact=True).fill('alpha,beta')
   click_request('#create-campaign','campaign.create')
   evidence=call('M2','evidence.import',project_id=pid,path=str(source))
   claim=call('M3','claim.create',project_id=pid,text='Offline workflows are supported.',evidence_ids=[evidence['id']])
   page.locator('#nav-content').click();page.wait_for_timeout(300)
   page.get_by_label('Content text',exact=True).fill('Offline workflows are supported.')
   page.get_by_label('Channel',exact=True).select_option('alpha')
   page.get_by_label('Claims',exact=True).select_option(label=claim['text'])
   first=click_request('#save-content','content.create');assert first.ok
   initial=call('M5','content.list',project_id=pid)['items'];cid=initial[0]['id']
   reviewed=click_request('#review-action','approval.review');approved=click_request('#approve-action','approval.approve')
   report['initial_review_approval']={'review':reviewed.status,'approve':approved.status}
   page.get_by_label('Content text',exact=True).fill('Offline workflows are supported. Edited.')
   edited=click_request('#save-content','content.')
   contents=call('M5','content.list',project_id=pid)['items']
   report['save_existing_content']={'http_status':edited.status,'before_count':len(initial),'after_count':len(contents),'original_id':cid,'ids':[x['id'] for x in contents],'original_approval':call('M6','approval.status',project_id=pid,content_id=cid)}
   state=page.request.get(url+'/api/state',params={'project_id':pid})
   report['project_scoped_state']={'http_status':state.status,'body':state.json(),'actual_campaign_count':len(call('M4','campaign.list',project_id=pid)['items']),'actual_content_count':len(contents)}
   report['javascript_errors']=errors
   page.screenshot(path=str(out/'actual-gui.png'),full_page=True)
  finally:browser.close()
except Exception as e:
 report['probe_error']=type(e).__name__+': '+str(e)
 raise
finally:
 (out/'receipt.json').write_text(json.dumps(report,indent=2),encoding='utf8')
 print(json.dumps(report))
 proc.terminate()
 try:proc.wait(timeout=5)
 except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
 log.close()
