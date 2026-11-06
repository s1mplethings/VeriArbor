"""Independent adapter dispatch/non-media concurrency probes with test handlers."""
import base64, concurrent.futures, importlib.util, json, pathlib, sys, threading

def probe(workspace,out):
    workspace=pathlib.Path(workspace);out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(workspace))
    spec=importlib.util.spec_from_file_location('bounded_dispatch_probe',workspace/'main.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    calls=[]
    def m1(folder,request):
        calls.append('M1')
        raise ValueError('original explicit M1 rejected unsupported media.import')
    def m11(folder,request):
        calls.append('M11')
        return {'id':'wrong-dispatch-sentinel'}
    module.HANDLERS['M1']=m1;module.HANDLERS['M11']=m11
    rejected=False;error=None
    try:module.handle(str(out),{'milestone':'M1','op':'media.import','project_id':'probe-project','kind':'image','filename':'probe.png','data':base64.b64encode(b'probe-bytes').decode()})
    except ValueError as e:rejected=True;error=str(e)
    dispatch=rejected and calls==['M1']
    barrier=threading.Barrier(2)
    def independent(folder,request):
        barrier.wait(timeout=2)
        return {'milestone':request['milestone']}
    module.HANDLERS['M1']=independent;module.HANDLERS['M4']=independent
    def invoke(milestone):
        try:return {'milestone':milestone,'result':module.handle(str(out),{'milestone':milestone,'op':'boundary.concurrent-probe'})}
        except Exception as e:return {'milestone':milestone,'error':type(e).__name__+': '+str(e)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(invoke,['M1','M4']))
    parallel_ok=all(row.get('result',{}).get('milestone')==row['milestone'] for row in rows)
    return {'status':'PASS' if dispatch and parallel_ok else 'FAIL','explicit_milestone_preserved':dispatch,'nonmedia_concurrency_preserved':parallel_ok,'dispatch_calls':calls,'dispatch_error':error,'concurrency':rows,'probe_scope':'Current adapter boundary with injected handlers; original backend source unchanged'}

if __name__=='__main__':
    result=probe(sys.argv[1],sys.argv[2]);print(json.dumps(result))
