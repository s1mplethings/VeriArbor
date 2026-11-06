"""Export authenticated milestone views; original GoalAcceptance stays authoritative."""
import datetime
import hashlib
import json
import sys
from pathlib import Path

H=Path(r'F:\CGKN-LeanLoop-V1-20261101')
R=Path(r'F:\CGKN-ITER-132\production-core-convergence-v1\promotion\run-05')
sys.path.insert(0,str(H))
from cgkn.state import FileRunStore
from cgkn.state.acceptance import GoalAcceptance
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

profile=read(R/'profile.json');run=R/'state'/profile['project_id']/profile['run_id']
authority=run/'goal_acceptance.json';before=sha(authority);data=read(authority)
view=GoalAcceptance(FileRunStore(R/'state'),profile['project_id'],profile['run_id'],data['requirements'],data['checker_bindings']).view()
assert before==sha(authority), 'Acceptance changed during export; retry read-only snapshot'
tags=sys.argv[1:] or sorted(view['obligations'])
for tag in tags:
    assert tag in view['obligations']
    goals=[g for g in view['goals'] if tag in g.get('requirement_refs',[])]
    record={'kind':'AuthenticatedAcceptanceCheckpoint','milestone':tag,
        'verdict':view['obligations'][tag]['verdict'],
        'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'authority':str(authority),'authority_sha256':before,
        'obligation':view['obligations'][tag],'authenticated_goals':goals,
        'is_new_acceptance_authority':False,'final_product_complete':view.get('complete',False)}
    payload=json.dumps(record,ensure_ascii=False,indent=2)
    for base in (H/'migration/veriarbor',R):
        history=base/'acceptance-checkpoints';history.mkdir(exist_ok=True)
        archive=history/(tag+'-'+hashlib.sha256(payload.encode('utf8')).hexdigest()+'.json')
        if not archive.exists(): archive.write_text(payload,encoding='utf8')
        target=base/(tag+'_ACCEPTANCE.json')
        if target.exists():
            previous=read(target)
            assert previous['kind']=='AuthenticatedAcceptanceCheckpoint' and previous['milestone']==tag
            old=history/(tag+'-export-'+sha(target)+'.json')
            if not old.exists():old.write_bytes(target.read_bytes())
        target.write_text(payload,encoding='utf8')
    print(json.dumps({'milestone':tag,'verdict':record['verdict'],'source_sha256':before}))
