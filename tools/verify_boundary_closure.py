"""Offline Windows boundary profiles. A failed profile never grants closure."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys, time

ROOT=Path(__file__).resolve().parents[1]
HOST=Path('F:/CGKN-LeanLoop-V1-20261101')
GATEWAY=Path('D:/cgkn-provider-api-lab')

def identity():
    rows={}
    for label,root,folders in [('core',ROOT,['src','tests','tools']),('host',HOST,['cgkn','tests','config','scripts','experiments','tools','contracts','governance']),('gateway',GATEWAY,['src','tests'])]:
        for folder in folders:
            for path in sorted((root/folder).rglob('*')):
                if path.is_file() and '__pycache__' not in path.parts and path.suffix in {'.py','.json','.toml','.yaml','.yml','.ps1','.sh'}:
                    rows[label+'/'+path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
        for name in ['AGENTS.md','pyproject.toml','pytest.ini','conftest.py']:
            path=root/name
            if path.is_file():rows[label+'/'+name]=hashlib.sha256(path.read_bytes()).hexdigest()
    for path in [ROOT/'.agents/skills/veriarbor-boundary-closure/SKILL.md',ROOT/'reports/generic-boundary-closure-v1/contract.json']:
        rows['core/'+path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    return rows

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=['request','full'],default='request')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    before=identity();(out/'source-identity.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
    env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join(map(str,[ROOT/'src',HOST]))
    env['PATH']='D:/anaconda;D:/anaconda/Library/bin;D:/anaconda/Scripts;'+env['PATH']
    env['CGKN_PYTEST_PROGRESS']='0'
    request=['tests/providers/test_default_request_packing.py','tests/providers/test_gateway_client.py','tests/providers/test_text_wire_preflight.py','tests/protocol/test_adaptive_context.py']
    host=request if args.profile=='request' else ['tests/providers','tests/protocol','tests/agent','tests/project_agent','tests/runtime','tests/state','tests/executors','tests/execution','tests/architecture','tests/test_provider_api_budget.py','tests/application/test_goal_driven.py']
    host=[*host,'tests/application/test_generic_gateway_chain.py']
    if args.profile=='full':
        host += ['tests/application/software_project','tests/test_artifact_driven_kernel.py',
                 'tests/test_provider_transport.py','tests/project_isolation','tests/experiments',
                 'tests/test_leanloop.py','tests/test_veriarbor_substitution_provenance.py']
        # The normal full profile must execute every registered behavioral proof,
        # including proofs located outside the conventional kernel directories.
        mappings=json.loads((HOST/'governance/test_coverage_manifest.json').read_text(encoding='utf-8'))
        mapped=sorted({case['nodeid'] for row in mappings['sources'].values() for case in row['test_cases']})
        for nodeid in mapped:
            filename=nodeid.split('::',1)[0]
            if not any(filename==target or filename.startswith(target.rstrip('/')+'/') for target in host):
                host.append(nodeid)
    commands=[('host',HOST,['D:/anaconda/python.exe','-m','pytest',*host,'--run-profile-marked','-m','not live_provider and not provider and not stress and not soak and not benchmark and not longrun and not long_journey','-q']),
        ('core',ROOT,[str(ROOT/'.venv/Scripts/python.exe'),'-m','pytest','tests','-q'])]
    if args.profile=='full':
        commands.append(('gateway',GATEWAY,['D:/anaconda/python.exe','-m','pytest','tests','-q','-p','no:pytest-qt','-p','no:opik','-p','no:langsmith','-p','no:dash']))
        commands.append(('product-direction',HOST,['D:/anaconda/python.exe','scripts/product_direction_gate.py']))
    results=[]
    for label,cwd,cmd in commands:
        if label!='product-direction':cmd += ['--junitxml='+str(out/(label+'.xml'))]
        print('Running',label,flush=True);started=time.time()
        with (out/(label+'.log')).open('w',encoding='utf-8') as log:
            code=subprocess.call(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
        results.append(dict(component=label,cwd=str(cwd),command=cmd,exit_code=code,seconds=time.time()-started))
        print(label,code,flush=True)
    unchanged=identity()==before
    receipt=dict(task='VERIARBOR_GENERIC_BOUNDARY_CLOSURE_V1',profile=args.profile,commands=results,source_unchanged=unchanged,
        source_identity_sha256=hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),
        passed=unchanged and all(r['exit_code']==0 for r in results),
        closure_qualification='NOT_GRANTED: test profile alone does not establish C01-C10')
    (out/'TestReceipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    return 0 if receipt['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
