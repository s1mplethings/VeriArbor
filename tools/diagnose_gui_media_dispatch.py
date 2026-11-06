from pathlib import Path
import base64,hashlib,importlib.util,json,socket,subprocess,time,urllib.request,urllib.error
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
snapshot=M/'media-publish-edges-attempt40/snapshot'
out=M/'gui-media-dispatch-0e6de644';out.mkdir(exist_ok=False)
data=out/'data';image=out/'pixel.png'
image.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a4gAAAABJRU5ErkJggg=='))
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
url='http://127.0.0.1:'+str(port)
argv=['D:/anaconda/python.exe','-X','utf8',str(snapshot/'early_main.py'),'--serve','--port',str(port),'--data',str(data)]
log=(out/'server.log').open('wb');proc=subprocess.Popen(argv,cwd=snapshot,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
def call(tag,op,**kwargs):
    request=urllib.request.Request(url+'/api/action',json.dumps({'milestone':tag,'op':op,**kwargs}).encode(),{'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=5) as r:return {'status':r.status,'body':json.load(r)}
    except urllib.error.HTTPError as e:return {'status':e.code,'body':e.read().decode('utf8')}
try:
    for _ in range(50):
        try:urllib.request.urlopen(url+'/health',timeout=.2).close();break
        except OSError:time.sleep(.1)
    else:raise RuntimeError('GUI startup failed')
    project=call('M1','project.create',name='Media dispatch diagnosis');assert project['status']==200,project
    pid=project['body']['id'];via_gui=call('M11','media.import',project_id=pid,path=str(image),kind='image')
    path=snapshot/'milestones/milestone_dbb8341c8910593063a8/api.py'
    spec=importlib.util.spec_from_file_location('independent_media',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    direct=mod.handle(str(data),{'op':'media.import','project_id':pid,'path':str(image),'kind':'image'})
    assert direct['status']=='VALID' and direct['sha256']==hashlib.sha256(image.read_bytes()).hexdigest()
    get_via_gui=call('M11','media.get',project_id=pid,media_id=direct['id'])
    report={'kind':'ActualGuiMediaDispatchDiagnostic','gui_source_sha256':hashlib.sha256((snapshot/'early_main.py').read_bytes()).hexdigest(),'media_api_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'snapshot_identity_ref':str(M/'media-publish-edges-attempt40/receipt.json'),'gui_project_create_status':project['status'],'gui_media_import':via_gui,'gui_media_get':get_via_gui,'direct_media_api':{'status':direct['status'],'sha256':direct['sha256'],'actual_stored_bytes_match':Path(direct['path']).read_bytes()==image.read_bytes()},'scope':'GUI request dispatch failure, not media signature/path implementation failure. Original GUI writer91; media API117 stays read-only.','acceptance_authority':False,'host_business_patches':0}
    (out/'receipt.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
finally:
    proc.terminate()
    try:proc.wait(timeout=5)
    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
    log.close()
