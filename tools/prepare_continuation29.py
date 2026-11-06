from pathlib import Path
import json, hashlib

V=Path('D:/VeriArbor')
H=Path('F:/CGKN-LeanLoop-V1-20261101')
M=H/'migration/veriarbor'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def put(p,x): p.write_text(json.dumps(x,indent=2),encoding='utf-8')

failed='explicit-write-operation'; replacement=failed+'-v2'
r=read(V/'governance/REPAIRED_REGRESSIONS.json')
assert not any(x['failed_check']==failed for x in r['repairs'])
rows=[json.loads(x) for x in (M/'AUTHORITY_SWITCH_RECEIPTS.jsonl').read_text().splitlines()]
assert len(rows)==19
assert read(V/'governance/checks'/replacement/'receipt.json')['exit_code']==0
r['repairs'].append({'failed_check':failed,'replacement':replacement,
 'failed_receipt_sha256':sha(V/'governance/checks'/failed/'receipt.json'),
 'replacement_receipt_sha256':sha(V/'governance/checks'/replacement/'receipt.json'),
 'reason':'An explicitly declared full_file_write=true strategy was not enforced in the Worker table/compiler. Carry that boolean to immutable allowed operations and reject partial patches without transforming product code. Defaults and read/path authority unchanged. Preserved reproduction2FAIL4PASS; identical command6PASS.',
 'source_change_receipts':rows[-2:]})
put(V/'governance/REPAIRED_REGRESSIONS.json',r)
previous=read(M/'continuation-feedback/veriarbor-28.json')
f=previous['feedback']
refs=[str(M/'m11-diagnostic-350e97b9/receipt.json'),str(M/'m11-generated-tests-350e97b9/receipt.json')]
f['milestone_completion_request']='Current M1-M10 VERIFIED; M11 fails genuine missing/broken media rejection. Source117 now350e97b9 fixed import path but media.get/list still omit data_dir. First close those remaining two real callsites in original writer117, deps=[] and current M11 API scope, preserving complete file. The explicit full_file_write boolean must be TRUE in strategy and leaf must use op2, now mechanically enforced. Then address actual failed integration through ORIGINAL dependency owners: M6 owner86 must reject missing/broken referenced media at approval; M7 owner89 must reject it at publication, without relying on a prior media.get call. Current owner scope expansion exposes these original dependency artifacts; choose each matching owner, scope and contract separately, not M11-owned rewrites of M6/M7 and not monkeypatching. Use current evidence refs, preserve all public predicates. Original early GUI owner91 also lacks actual image/video previews: implement real preview interaction at its authorized original owner, never merely insert the word media to satisfy a weak selftest. Existing original observers119-122: refresh stale122 explicitly with retry action3, do not create more duplicates. Re-measure affected old milestones after dependency changes. Preserve meaningful34-case M11 tests, including all4 missing/broken approval/publication negatives and GUI requirement; improve weak preview assertion through real browser verification, never waive it. Continue M12 and all retained test debts through original Provider-owned source/test tasks and canonical finalization, delivery, accounting/provenance and Corpus. No host-authored business implementation.'
f['fresh_runtime_diagnosis']['current_M11_350e97b9']={'evidence_refs':refs,'import_path':'fixed and frozen checker progressed','get_list_paths':'both still omit data_dir in _public_media call','frozen_checker':'Expected ValueError for invalid or foreign input','additional_tests':'34 cases, 5 failed: missing/broken media approval+publication and early GUI media controls; no skipped failures','diagnostic_only':True}
f['strategy_constraints']=[{'scope_paths':['milestones/milestone_dbb8341c8910593063a8/api.py'],'required_dimensions':['full_file_write'],'dimension_types':{'full_file_write':'boolean'},'forbidden_patterns':[{'full_file_write':False}],'evidence_refs':refs}]
f['redecision']={'strategy_revision':hashlib.sha256(b'M11 source350e97b9 remaining callers with enforced fullfile write and original dependency-owner negative validation').hexdigest(),'reason':'Import path progressed but get/list remain disconnected and real integration fails missing/broken media. Prior prose-only write mode was dropped; explicitly admitted boolean strategy is now enforced by Worker operations. Preserve original failures, owners and acceptance.', 'evidence_refs':refs}
p=M/'continuation-feedback/veriarbor-29.json'
assert not p.exists()
put(p,previous)
with (M/'WORK_LOG.md').open('a',encoding='utf-8') as stream:
 stream.write('\n\nContinuation28 held at safe next-call boundary, no new UNKNOWN. M11 import projection fixed350e97b9; original checker advances to missing ValueError, selftests34/5fail preserve real dependency and GUI failures. Receipts18/19 enforce explicitly declared optional full-file Worker write strategy; failed reproduction retained, identical6tests pass. Read-only acceptance profile11.375seconds/43.5MB shows provenance checks dominate; controller29 adds periodic Python stacks without changing acceptance/evidence. No business source authored by host.\n')
print(p)
