"""Synthetic positive/mutation controls for B01; never product implementation."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import hashlib,json,threading
from playwright.sync_api import sync_playwright
from m12_b01_acceptance import browser_check,M

OUT=M/'B01_CHECKER_QUALIFICATION';OUT.mkdir(exist_ok=False)
HTML='''<!doctype html><html><body>
<label for="name">Project name</label><input id="name"><button onclick="createProject()">Create project</button>
<div id="projects"></div><script>
let currentProjectId='';const mode=MODE;
async function list(){let r=await fetch('/api/action',{method:'POST',body:JSON.stringify({op:'project.list'})});let d=await r.json();
 document.getElementById('projects').textContent=d.items.length?d.items[0].name:(mode==='no_empty'?'':'No projects');
 if(mode==='hidden_name')document.getElementById('projects').hidden=true;
 if(d.items.length&&mode!=='lost_selection'){currentProjectId=d.items[0].id;await fetch('/api/state?project_id='+currentProjectId);}
 if(mode==='state_without_id')await fetch('/api/state');
}
async function createProject(){await fetch('/api/action',{method:'POST',body:JSON.stringify({op:'project.create',name:document.getElementById('name').value})});await list();}
list();if(mode==='js_error')setTimeout(()=>{throw new Error('qualification mutation');},10);
</script></body></html>'''

results=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True)
    for mode in ['positive','no_empty','create_error','hidden_name','lost_selection','state_without_id','js_error','duplicate_id']:
        rows=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def reply(self,status,data,content_type='application/json'):
                self.send_response(status);self.send_header('Content-Type',content_type);self.end_headers()
                self.wfile.write(data.encode() if isinstance(data,str) else json.dumps(data).encode())
            def do_GET(self):
                if self.path=='/':
                    html=HTML.replace('MODE',json.dumps(mode))
                    if mode=='duplicate_id':html=html.replace('</body>','<div id="projects"></div></body>')
                    return self.reply(200,html,'text/html')
                if self.path.startswith('/api/state'):return self.reply(200,{'project':rows[0] if rows else {}})
                self.reply(404,{})
            def do_POST(self):
                data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if data['op']=='project.create':
                    if mode=='create_error':return self.reply(400,{'error':'mutated failure'})
                    rows.append({'id':'qualification-project','name':data['name']});return self.reply(200,rows[-1])
                self.reply(200,{'items':rows})
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        folder=OUT/mode;folder.mkdir();context=browser.new_context()
        try:result=browser_check(context.new_page(),'http://127.0.0.1:'+str(server.server_port),folder)
        finally:context.close();server.shutdown();server.server_close()
        (folder/'receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
        results.append({'control':mode,'expected':'PASS' if mode=='positive' else 'FAIL','observed':result['status'],'error':result.get('error')})
        print(json.dumps(results[-1]),flush=True)
    browser.close()
passed=all(x['expected']==x['observed'] for x in results)
receipt={'kind':'IndependentCheckerQualification','status':'PASS' if passed else 'FAIL','controls':results,
 'checker_sha256':hashlib.sha256(Path(__file__).with_name('m12_b01_acceptance.py').read_bytes()).hexdigest(),
 'product_acceptance':'NOT_GRANTED','provider_calls':0,'host_business_patches':0}
(OUT/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
assert passed,results
