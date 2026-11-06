from pathlib import Path
import json, hashlib
V=Path('D:/VeriArbor'); M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x): p.write_text(json.dumps(x,indent=2),encoding='utf-8')
r=read(V/'governance/REPAIRED_REGRESSIONS.json')
failed='strategy-constraint-feedback';replacement=failed+'-v2'
assert not any(x['failed_check']==failed for x in r['repairs'])
rows=[json.loads(x) for x in (M/'AUTHORITY_SWITCH_RECEIPTS.jsonl').read_text().splitlines()]
assert len(rows)==20
r['repairs'].append({'failed_check':failed,'replacement':replacement,
 'failed_receipt_sha256':sha(V/'governance/checks'/failed/'receipt.json'),
 'replacement_receipt_sha256':sha(V/'governance/checks'/replacement/'receipt.json'),
 'reason':'Missing or mistyped declared strategy dimensions were reported as forbidden fields and forced whole-decision replanning. Exact constraints now accompany a bounded strategy-only correction; falsified families remain R6 and all task/evidence fields remain immutable. Preserved2FAIL1PASS, identical3testsPASS.',
 'source_change_receipts':rows[-1:]})
put(V/'governance/REPAIRED_REGRESSIONS.json',r)
prior=read(M/'continuation-feedback/veriarbor-31.json')
f=prior['feedback']
# Retain old diagnostic receipts by reference, not contradictory stale inline source descriptions.
f['fresh_runtime_diagnosis']={'current_source':'350e97b959d7ec3fee8f88d4a7961e09e044a6fa61b57718d34a4cb378a1e666',
 'current_observations':{'import_path':'fixed','get_list':'two remaining _public_media callers omit data_dir',
 'canonical_M11_failure':'Expected ValueError for invalid or foreign input',
 'selftests':'34 cases,29PASS5FAIL; four real missing/broken approval/publication failures plus missing early GUI preview'},
 'evidence_refs':[str(M/'m11-diagnostic-350e97b9/receipt.json'),str(M/'m11-generated-tests-350e97b9/receipt.json')],
 'retained_old_test_debts':[str(M/'ADDITIONAL_TEST_DEBT_TRIAGE.json'),str(M/'TEST_DEBT_CONTRACT_QUALIFICATION.json'),str(M/'M10_M11_DIAGNOSTIC_TRIAGE.json')],
 'previous_feedback_archive':str(M/'continuation-feedback/veriarbor-31.json')}
f['admission_correction']='Initial full decision MUST include strategy.full_file_write=true as JSON boolean for the M11 API repair; preserve meaningful problem and other mechanism dimensions. If missing/type error, exact bounded patch correction now asks to replace only strategy, not whole decision. For target117 preserve deps=[];118 is downstream. Use original current owner targets and exact current scope IDs for M6/M7/GUI separately. hypothesis.falsifying_evidence is an ARRAY of exact current bound evidence-ref objects. Do not repeatedly resend rejected fields.'
refs=[str(V/'governance/checks/strategy-constraint-feedback-v2/receipt.json'),str(M/'AUTHORITY_SWITCH_RECEIPTS.jsonl')]
f['redecision']={'strategy_revision':hashlib.sha256(b'exact strategy constraint correction receipt20 source350e97b9').hexdigest(),
 'reason':'Prior missing full_file_write strategy was correctly rejected but feedback incorrectly called it forbidden and did not permit bounded correction. Fixed exact type/required constraints plus strategy-only patch, unchanged false-pattern rejection and unchanged business failure; no source/evidence waiver.', 'evidence_refs':refs}
destination=M/'continuation-feedback/veriarbor-32.json';assert not destination.exists();put(destination,prior)
with (M/'WORK_LOG.md').open('a',encoding='utf-8') as f:
 f.write('\n\nContinuation29 native Python312.dll0xc0000005 at first new faulthandler dump, causal link unproven; native instrumentation removed. Windows event and after-exit reconciliation preserve1settled planner call, identical candidate,0newUNKNOWN. Continuation30 reused revision correctly blocked beforecalls.31 completed2planner calls but bounded admission exhausted missing full_file_write, no product writes. Receipt20 corrects malformed strategy constraint feedback with a strategy-only patch; genuine false strategy remains rejected. Historical failure/cost retained.\n')
print(destination)
