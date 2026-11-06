"""Exercise the current real file-input route in an isolated candidate snapshot."""
from pathlib import Path
import base64, hashlib, json, shutil, socket, subprocess, time
from playwright.sync_api import sync_playwright

R = Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M = Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
out = M/'gui-upload-5c7e0f19-v2'
out.mkdir(exist_ok=False)
snapshot = out/'snapshot'
snapshot.mkdir()
for p in (R/'candidate').glob('*.py'): shutil.copy2(p, snapshot/p.name)
shutil.copytree(R/'candidate/milestones', snapshot/'milestones', ignore=shutil.ignore_patterns('__pycache__'))
sha = hashlib.sha256((snapshot/'early_main.py').read_bytes()).hexdigest()
assert sha.startswith('5c7e0f19')
png = out/'pixel.png'
png.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a4gAAAABJRU5ErkJggg=='))
with socket.socket() as sock:
    sock.bind(('127.0.0.1',0)); port = sock.getsockname()[1]
url = 'http://127.0.0.1:'+str(port)
log = (out/'server.log').open('wb')
proc = subprocess.Popen(['D:/anaconda/python.exe','-X','utf8',str(snapshot/'early_main.py'),'--serve','--port',str(port),'--data',str(out/'data')], cwd=snapshot, stdout=log, stderr=subprocess.STDOUT, creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge',headless=True)
        try:
            page = browser.new_page()
            for _ in range(80):
                try: page.goto(url); break
                except Exception: time.sleep(.1)
            page.get_by_label('Project name',exact=True).fill('Upload diagnostic')
            page.get_by_role('button',name='Create project',exact=True).click()
            page.wait_for_timeout(600)
            navigation_count = page.locator('#main-nav button[data-view="media-view"]').count()
            visible_imports = page.locator('#import-media:visible').count()
            projects = page.request.post(url+'/api/action',data={'milestone':'M1','op':'project.list'}).json()['items']
            response = page.request.post(url+'/api/action',data={'milestone':'M11','op':'media.import','project_id':projects[0]['id'],'kind':'image','filename':png.name,'data':base64.b64encode(png.read_bytes()).decode()})
            page.wait_for_timeout(300)
            page.screenshot(path=str(out/'upload.png'),full_page=True)
            report = {'kind':'RealGuiUploadRouteDiagnostic','source_sha256':sha,'media_navigation_count':navigation_count,'visible_import_controls':visible_imports,'upload_probe_method':'HTTP request with exact payload shape of existing file-input handler; actual GUI controls are unreachable, not claimed clicked','http_status':response.status,'response':response.json(),'visible_alert':page.locator('[role="alert"]').all_text_contents(),'required_behavior':'Chosen real PNG must import via existing path-based M11 API after GUI server bridges uploaded bytes; do not change M11 public contract. Existing Save also uses content.create unconditionally; edit existing identity through content.edit.','acceptance_authority':False,'host_business_patches':0}
            (out/'receipt.json').write_text(json.dumps(report,indent=2),encoding='utf8')
            print(json.dumps(report))
        finally: browser.close()
finally:
    proc.terminate()
    try: proc.wait(timeout=5)
    except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=5)
    log.close()
