from pathlib import Path
import ast,base64,hashlib,json,subprocess,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
out=M/'media-gui-v5-controls';out.mkdir(exist_ok=False)
png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a4gAAAABJRU5ErkJggg==')
video=out/'clip.mp4'
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-f','lavfi','-i','color=c=blue:s=32x32:d=0.25','-pix_fmt','yuv420p',str(video)],check=True,capture_output=True)
mp4=video.read_bytes();checker=R/'consumer-revisions/media-gui-v5.py'
scope={'hashlib':hashlib};tree=ast.parse(checker.read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'require','assert_media_preview'}],type_ignores=[]),str(checker),'exec'),scope)
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        value,kind=({'/image.png':(png,'image/png'),'/video.mp4':(mp4,'video/mp4'),'/':(b'<html><body></body></html>','text/html')}).get(self.path,(b'','text/plain'))
        self.send_response(200 if value else 404);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(value)));self.end_headers();self.wfile.write(value)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
url='http://127.0.0.1:'+str(server.server_port)
image='<img src="'+url+'/image.png">';clip='<video controls src="'+url+'/video.mp4"></video>'
rows=[]
try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        try:
            page=browser.new_page();page.goto(url)
            for name,kind,html,expected,ih in [
                ('real_image_video','positive',image+clip,True,hashlib.sha256(png).hexdigest()),
                ('text_placeholders','negative','<p>image video media</p>',False,hashlib.sha256(png).hexdigest()),
                ('hidden_image','negative','<div hidden>'+image+'</div>'+clip,False,hashlib.sha256(png).hexdigest()),
                ('wrong_content_identity','mutation',image+clip,False,'0'*64),
                ('no_video_controls','mutation',image+clip.replace(' controls',''),False,hashlib.sha256(png).hexdigest()),
                ('broken_image','mutation',image.replace('/image.png','/missing.png')+clip,False,hashlib.sha256(png).hexdigest())]:
                page.set_content(html,wait_until='networkidle')
                try:scope['assert_media_preview'](page,ih,hashlib.sha256(mp4).hexdigest());observed=True;error=''
                except Exception as e:observed=False;error=type(e).__name__+': '+str(e)
                rows.append({'name':name,'kind':kind,'expected':expected,'observed':observed,'passed':observed==expected,'error':error})
                if name=='real_image_video':page.screenshot(path=str(out/'positive.png'))
        finally:browser.close()
finally:server.shutdown();server.server_close();thread.join(3)
report={'kind':'IndependentMediaGuiCheckerControls','status':'PASS' if all(r['passed'] for r in rows) else 'FAIL','controls':rows,'previous_checker_hash':hashlib.sha256((R/'consumer-revisions/media-integrity-v4.py').read_bytes()).hexdigest(),'checker_hash':hashlib.sha256(checker.read_bytes()).hexdigest(),'scope':['M11'],'qualification_only':True,'product_acceptance_granted':False,'host_business_patches':0}
(out/'receipt.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report));assert report['status']=='PASS'
