"""Measure actual GUI server handling of normal browser preconnected sockets."""
from pathlib import Path
import hashlib, importlib.util, json, socket, sys, threading, time, urllib.request
from http.server import ThreadingHTTPServer

M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
snapshot=M/'m12-final-product-143a2-selection-corrected/snapshot'
out=M/'m12-idle-connection-5f467864';out.mkdir(exist_ok=False)
sys.path.insert(0,str(snapshot))
spec=importlib.util.spec_from_file_location('tested_gui',snapshot/'main.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
rows=[]
for control in (False, True):
    data=out/('control-data' if control else 'actual-data');data.mkdir()
    if control:
        server=ThreadingHTTPServer(('127.0.0.1',0),module.RequestHandler)
        server.data_dir=str(data)
    else:
        server=module.ThreadedHTTPServer('127.0.0.1',0,str(data))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    idle=socket.create_connection(('127.0.0.1',server.server_port),timeout=2)
    time.sleep(.15);start=time.monotonic()
    try:
        with urllib.request.urlopen('http://127.0.0.1:'+str(server.server_port)+'/health',timeout=2) as response:
            value=json.load(response);result={'responded':True,'body':value}
    except Exception as error:
        result={'responded':False,'error':type(error).__name__+': '+str(error)}
    elapsed=time.monotonic()-start
    idle.close()
    try:
        with urllib.request.urlopen('http://127.0.0.1:'+str(server.server_port)+'/health',timeout=3) as response:
            recovered=json.load(response)
    finally:
        server.shutdown();server.server_close();thread.join(3)
    rows.append({'mode':'independent threaded control' if control else 'actual candidate server class',
                 'result':result,'seconds':elapsed,'after_idle_close':recovered})
report={'kind':'BrowserIdleConnectionDiagnostic','source_sha256':hashlib.sha256((snapshot/'main.py').read_bytes()).hexdigest(),
        'acceptance_authority':False,'host_business_patches':0,'observations':rows,
        'scope':'Normal idle preconnection plus concurrent /health, not load or performance stress. Control uses standard library threaded server with same handler outside candidate.'}
(out/'receipt.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report))
