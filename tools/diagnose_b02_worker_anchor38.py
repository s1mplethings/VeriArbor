from pathlib import Path
import json,hashlib,re
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05');M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor');S=R/'state/iter132-promotion-studio/promotion-05'
request=json.loads((S/'provider_calls/58c218e5dd7a4b36ad1297f131eef6df/request.json').read_text(encoding='utf8'))
user=json.loads(request['request']['user']);source=(R/'candidate/main.py').read_text(encoding='utf8')
needle="# Browser payloads (base64 'data') go through the temp-file adapter;";rows=[]
def walk(x,path=''):
    if isinstance(x,dict):
        for key,value in x.items():walk(value,path+'/'+key)
    elif isinstance(x,list):
        for i,value in enumerate(x):walk(value,path+'/'+str(i))
    elif isinstance(x,str) and needle in x:
        normalized=re.sub(r'\r\n|\r|\n','\n',x);i=normalized.index(needle)
        rows.append({'context_path':path,'normalized_equals_current_full_source':normalized==source,'excerpt':normalized[i:i+200]})
walk(user)
report={'kind':'WorkerSourceContextDiagnostic','rows':rows,'request_identity':request['identity'],'source_sha256':hashlib.sha256((R/'candidate/main.py').read_bytes()).hexdigest(),'read_only':True}
(M/'B02_WORKER_CONTEXT_DIAGNOSTIC_38.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
