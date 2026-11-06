"""Append migration evidence to the existing Corpus in bounded batches.

Run only after the original product controller has stopped. This is archival,
not a new project witness or acceptance route. Historical catalog rows persist.
"""
import hashlib
import importlib.util
import json
import sqlite3
import subprocess
import sys
import types
from pathlib import Path
from capture_baseline import H, V, P

def read(path): return json.loads(path.read_text(encoding='utf8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def put(path, value):
    with path.open('x', encoding='utf8') as stream: json.dump(value, stream, ensure_ascii=False, indent=2)

label = sys.argv[1]
assert label and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in label)
root = P / 'promotion/run-05'
state = root / 'state/iter132-promotion-studio/promotion-05'
assert not any(n['status'] == 'RUNNING' for n in read(state/'run_state.json')['nodes'].values())
ledger_path = P.parents[1]/'CGKN-ITER-076/global-provider-budget.json'
ledger = read(ledger_path)
baseline = read(root/'continuations/veriarbor-01/accounting-before.json')
assert ledger['calls'][:len(baseline['calls'])] == baseline['calls']
assert all(c['status'] not in {'REQUEST_STARTED','RESERVED'} for c in ledger['calls'][len(baseline['calls']):])
control = types.ModuleType('control'); control.sha=sha; control.read=read; control.OUT=P; control.ROOT=H
sys.modules['control'] = control
spec = importlib.util.spec_from_file_location('veriarbor_corpus_loader', P.parents[1]/'CGKN-ITER-126/cleanup-migration-closure-v1/archive126.py')
loader = importlib.util.module_from_spec(spec); spec.loader.exec_module(loader)
contracts, module, pins = loader.load()
corpus = module.ProjectCorpus(P.parents[1]/'CGKN-ITER-060/project-corpus')
out = P/'corpus'/label; out.mkdir(parents=True, exist_ok=False)
tables = ('attempts','snapshots','files','events','failures','tests')
def catalog():
    with sqlite3.connect('file:' + (corpus.root/'catalog.sqlite3').as_posix() + '?mode=ro', uri=True) as db:
        return {t:{hashlib.sha256(json.dumps(row,ensure_ascii=False).encode()).hexdigest() for row in db.execute('SELECT * FROM '+t)} for t in tables}
before = catalog()
excluded=[]; redactions=[]; chunks=[]; batches=[]; pending={}; size=0; total=0
version=sha(V/'REGRESSION.json')
def flush():
    global pending, size
    if not pending:return
    identity=label+'-'+str(len(batches)+1).zfill(4)
    receipt=corpus.capture_attempt(family_id='production-core-convergence-v1',attempt_id=identity,
        run_id='ITER-132',source_version=version,generator_version='existing-project-session-veriarbor-migration',
        status='PARTIAL',provenance='generated_original',split='QUARANTINE',
        public_packet={'task':'Preserve VeriArbor migration, original Promotion continuation, failures, UNKNOWNs and source-bound evidence',
                       'scope':'One archival batch of the same original project; not a new witness, formal score or product PASS'},
        snapshots=[{'stage':'FINAL','files':pending}],
        metadata={'classification':'QUALIFICATION_ONLY','not_independent_project':True,'product_complete':False,
                  'old_verdicts_not_upgraded':True,'batch':len(batches)+1,'batch_label':label},tests=[],failures=[])
    value=receipt.as_dict();assert value['status']=='PASS',value
    manifest=corpus.show(value['corpus_entry_id'])
    snaps=[corpus._load_snapshot(x['snapshot_id']) for x in manifest['snapshot_refs']]
    contracts.AttemptManifest.from_dict(manifest,snapshots=snaps)
    checked={}
    for snap in snaps:
        for obj in snap.files:
            raw=corpus._object_path(obj.content_hash).read_bytes()
            assert raw==pending[obj.path] and obj.content_hash=='sha256:'+hashlib.sha256(raw).hexdigest()
            checked[obj.path]=obj.content_hash
    assert set(checked)==set(pending), 'Corpus scan quarantined a source; inspect preserved redaction evidence'
    batches.append({'entry':value['corpus_entry_id'],'objects':len(checked),'bytes':size,'receipt':value})
    put(out/(identity+'.json'),batches[-1]);print(json.dumps({'batch':identity,'objects':len(checked),'bytes':size}),flush=True)
    pending={};size=0
def add(name, raw):
    global size,total
    if size+len(raw)>24*1024*1024:flush()
    assert name not in pending
    pending[name]=raw;size+=len(raw);total+=1
roots=[('VeriArbor',V),('CGKN-migration',H/'migration/veriarbor'),('Promotion-run05',root)]
for prefix, source in roots:
    result=subprocess.run(['rg','--files','--hidden','--no-ignore',str(source)],capture_output=True,text=True,encoding='utf8',check=True)
    for path in sorted(Path(line) for line in result.stdout.splitlines()):
        relative=path.relative_to(source);parts=set(relative.parts)
        if path.is_symlink() or parts.intersection({'.git','.venv','venv','node_modules','__pycache__','.pytest_cache','scratch','consumer_scratch','gateway-private'}) or path.suffix in {'.pyc','.lock'}:
            excluded.append({'root':prefix,'path':relative.as_posix(),'reason':'Runtime/private/cache/dependency scratch or symlink; original retained locally'});continue
        raw=path.read_bytes();before_hash=hashlib.sha256(raw).hexdigest()
        try:safe=module._redact_text(raw.decode('utf-8-sig')).encode('utf8')
        except UnicodeDecodeError:safe=raw
        assert sha(path)==before_hash, 'Source changed during archival: '+str(path)
        name=prefix+'/'+relative.as_posix()
        if safe!=raw:redactions.append({'path':name,'original_sha256':before_hash,'archived_sha256':hashlib.sha256(safe).hexdigest()})
        if len(safe)>8*1024*1024:
            refs=[]
            for i,start in enumerate(range(0,len(safe),8*1024*1024)):
                part=safe[start:start+8*1024*1024];part_name=name+'.part'+str(i).zfill(4)
                add(part_name,part);refs.append({'path':part_name,'sha256':hashlib.sha256(part).hexdigest()})
            chunks.append({'path':name,'parts':refs,'sha256':hashlib.sha256(safe).hexdigest()})
        else:add(name,safe)
add('Accounting/global-provider-budget.json',module._redact_text(ledger_path.read_text(encoding='utf8')).encode())
for name,value in [('exclusions',excluded),('redactions',redactions),('chunks',chunks)]:
    put(out/(name+'.json'),value);add('Archive-index/'+name+'.json',(out/(name+'.json')).read_bytes())
flush()
after=catalog();preservation={t:{'old_rows':len(before[t]),'new_rows':len(after[t]),'old_rows_missing_or_changed':len(before[t]-after[t])} for t in tables}
assert all(v['old_rows_missing_or_changed']==0 for v in preservation.values());put(out/'append-only-check.json',preservation)
passes=[]
for _ in range(2):
    hashes={};bytes_checked=0
    for batch in batches:
        manifest=corpus.show(batch['entry']);snaps=[corpus._load_snapshot(x['snapshot_id']) for x in manifest['snapshot_refs']]
        contracts.AttemptManifest.from_dict(manifest,snapshots=snaps)
        for snap in snaps:
            for obj in snap.files:
                raw=corpus._object_path(obj.content_hash).read_bytes();assert obj.content_hash=='sha256:'+hashlib.sha256(raw).hexdigest()
                assert obj.path not in hashes;hashes[obj.path]=obj.content_hash;bytes_checked+=len(raw)
    passes.append({'objects':len(hashes),'bytes_checked':bytes_checked,'reconstruction_sha256':hashlib.sha256(json.dumps(hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()})
assert passes[0]==passes[1]
receipt={'storage_status':'PASS','experiment_status':'PARTIAL','business_acceptance_not_inferred':True,
    'canonical_corpus_root':str(corpus.root),'batches':batches,'implementation_hashes':pins,
    'old_catalog_rows_preserved':True,'readonly_rebuilds':passes,'rebuilds_consistent':True,'provider_calls':0}
put(out/'receipt.json',receipt);put(V/'governance/CORPUS_RECEIPT.json',receipt)
print(json.dumps({'storage_status':'PASS','experiment_status':'PARTIAL','batches':len(batches),'objects':total,'rebuilds_consistent':True}),flush=True)
