from pathlib import Path
import hashlib,json,re,difflib
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor');R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05');S=R/'state/iter132-promotion-studio/promotion-05'
def read(p):return json.loads(p.read_text(encoding='utf8'))
text=(R/'candidate/main.py').read_text(encoding='utf8');source=hashlib.sha256((R/'candidate/main.py').read_bytes()).hexdigest();assert source.startswith('f269c86e')
a=read(S/'attempts/sem-node-0143/attempt-0037.json');assert 'ambiguous patch anchor' in a['error']['message']
response=read(S/'provider_calls/fe7583fe92444cd393220b71d19a7734/response.json');payload=json.loads(response['text'])['payload'];anchor=re.sub(r'\r\n|\r|\n','\n',payload[0]['find'])
assert text.count(anchor)==0
start=text.index("    if op == 'media.import':");end=text.index('def _media_import_adapter(data_dir, request):',start)+len('def _media_import_adapter(data_dir, request):')
actual=text[start:end];diff=list(difflib.unified_diff(anchor.splitlines(keepends=True),actual.splitlines(keepends=True),fromfile='rejected-find-anchor',tofile='actual-read-only-source'))
record={'attempt':'attempt-0037','verdict':'PATCH_SCOPE_EXCEEDED','anchor_matches':0,'ambiguous_message_means':'zero exact matches in this case, not duplicate matches','source_sha256':source,'source_unchanged':True,'applied':False,'browser_executed':False,'exact_read_only_source_fragment':actual,'anchor_only_diff':diff,'reason':'Worker find anchor inserted an extra blank line between two adjacent browser-payload comment lines. Existing mixed line spacing is valid and must be matched exactly; no replacement business code supplied.'}
with (M/'B02_ANCHOR_REJECTION_37.json').open('x',encoding='utf8') as stream:json.dump(record,stream,ensure_ascii=False,indent=2)
feedback=read(M/'continuation-feedback/veriarbor-100.json');f=feedback['feedback']
f['fresh_runtime_diagnosis']['anchor_rejection']=record
f['milestone_completion_request']+=' Attempt37 produced NO source delta: its exact find anchor had zero matches because it invented a blank line between adjacent comment lines. Fresh source excerpt is provided read-only in new evidence. Author new exact anchors from the current source, preferably small unique anchors without copying long unchanged comments. Do not normalize or assume blank-line spacing. No rejected replacement is supplied or manually applied.'
f['bounded_patch_policy']['acceptance_requirements'].append('All find strings must have exactly one match after universal-newline normalization; indentation and number of blank lines remain significant. Attempt37 source-only anchor diff proves mismatch. Preserve exact source spacing outside chosen changed ranges. No full-file rewrite; scope unchanged.')
f['redecision']={'strategy_revision':hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest(),'reason':'New concrete anchor mismatch evidence; use current exact source anchors, not reconstructed whitespace. Current159 native business failure remains valid because source unchanged.','evidence_refs':[str(M/'B02_ANCHOR_REJECTION_37.json'),str(S/'attempts/sem-node-0159/attempt-0001.json')]}
with (M/'continuation-feedback/veriarbor-101.json').open('x',encoding='utf8') as stream:json.dump(feedback,stream,ensure_ascii=False,indent=2)
print(json.dumps({'source':source,'anchor_matches':0,'anchor_only_diff':diff}))
