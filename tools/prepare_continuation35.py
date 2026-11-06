from pathlib import Path
import json,hashlib
V=Path('D:/VeriArbor');M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,d):p.write_text(json.dumps(d,indent=2),encoding='utf-8')
rows=[json.loads(x) for x in (M/'AUTHORITY_SWITCH_RECEIPTS.jsonl').read_text().splitlines()];assert len(rows)==21
r=read(V/'governance/REPAIRED_REGRESSIONS.json')
qualification=M/'metadata-refresh-qualification/receipt.json';assert qualification.exists()
for failed in ('metadata-only-refresh','metadata-only-refresh-v2'):
 assert not any(x['failed_check']==failed for x in r['repairs'])
 replacement='metadata-only-refresh-v3'
 r['repairs'].append({'failed_check':failed,'replacement':replacement,
  'failed_receipt_sha256':sha(V/'governance/checks'/failed/'receipt.json'),
  'replacement_receipt_sha256':sha(V/'governance/checks'/replacement/'receipt.json'),
  'reason':'Removed unused global verdict views at metadata-only callsites. Initial test guard was overbroad: it also prohibited mandatory save/render views, so first fixed-code run stillfailed. Preserve original test, allow only original render calls, and re-qualify corrected test against original source:3FAIL1PASS vsupdated4PASS. No evidence check removed. Same read-only real subject refresh15.328s before/0.687s after, one sample; not end-to-end claim.',
  'test_revision_qualification':{'path':str(qualification),'sha256':sha(qualification)},'source_change_receipts':rows[-1:]})
put(V/'governance/REPAIRED_REGRESSIONS.json',r)
d=read(M/'continuation-feedback/veriarbor-34.json');f=d['feedback']
refs=[str(M/'m6-diagnostic-2fe4fa28/receipt.json'),str(R/'state/iter132-promotion-studio/promotion-05/attempts/sem-node-0087/attempt-0006.json')]
f['milestone_completion_request']='M6 source86 is now2fe4fa28 and has a concrete regression: _validate_media_present signature requires3arguments but approval.approve still passes1, so approvals fail TypeError. New helper also dynamically loads milestone_9165a990eed5b9c8801e/api.py, which is NOT M11 media. The actual existing M11 media API is milestones/milestone_dbb8341c8910593063a8/api.py. M11 source117e4737c44 remains complete for public paths; preserve it. If no CURRENT canonical M6 failure is recorded yet, measure current M6 through its original registered independent checker, binding source86. Existing88 is blocked behind failed test87; use an admissible independent measurement without regenerating test87 just to obtain source evidence. Do not add duplicate observers if a suitable current one already exists. Once current M6 failure is recorded, repair ORIGINAL86 only with a coherent full-file operation: connect complete validation mechanism to actual approval path, use correct media module/API, preserve valid no-media approval and all existing claims/revision/project isolation. strategy.full_file_write MUST be booleantrue, now enforced for M6 API too. Never fix this by weakening tests or writing M6 behavior intoM11.87a6 returned malformed JSON, so staged output was rejected and old valid test file remains; later let original test owner correct its actual output separately, never replay old responses. Re-measure M6 and all actually affected M7-M10 dependencies using original checkers before continuing M11 missing/broken publication/realGUIpreview, M12, retained finaltest debts and canonical delivery/accounting/Corpus. A once-needed source measurement must not recur after current FAILED evidence is available.'
f['fresh_runtime_diagnosis']={'M6_source_sha256':'2fe4fa288e027f32fc2411364dc9ca8207f39aebc58e3b268f51991c7f1ef060',
 'frozen_M6_result':'1/2; TypeError _validate_media_present missing project_id and media_ids',
 'source_observations':{'helper_definition_line':128,'unmodified_callsite_line':180,'wrong_loader_path_line':121,'correct_media_module':'milestones/milestone_dbb8341c8910593063a8/api.py'},
 'test87_attempt6':'INVALID_OUTPUT / INVALID_OR_INCOMPLETE_JSON; provider completed6073outputtokens, no upstreamUNKNOWN; candidate test stillold valid20df669d',
 'evidence_refs':refs,'retained_old_debts':str(M/'continuation-feedback/veriarbor-33.json'),'upstream_unknowns':6}
f['strategy_constraints'].append({'scope_paths':['milestones/milestone_33270fed0c9054f5ae04/api.py'],
 'required_dimensions':['full_file_write'],'dimension_types':{'full_file_write':'boolean'},
 'forbidden_patterns':[{'full_file_write':False}],'evidence_refs':refs})
f['admission_correction']='M6 current-source measurement only if current failure is missing; after it exists, repair86 with exactly its current declared API scope, originaldeps, full_file_write=true and hypothesis array of exact current bound failure refs. Preserve successful117 and unrelated verified modules. Do not retry stale source87 UNKNOWN (there is none;87a6 is known invalid JSON). Any repair_action patch changes only listed fields. Revalidate affected dependency goals; no ordinary defect can justify Pro/Max.'
f['gui_writer_policy']='Do not rewrite117 or89/91 to fix M6 approval. Original86 owns current regression. Later89 owns publicationmedia guard and91 actual GUIpreview. Old unrelated artifacts preserved.'
f['cost_policy']='Qwen3.8Flash Agent and Worker for new requests after DeepSeek partial-helper regression and malformedJSON testoutput. Cheap-family substitution only, no Pro/Max, not acceptance evidence. Same-model review SELF_CRITIQUE. Preserve6upstreamUNKNOWNs and all failed responses; no exact replay.'
f['redecision']={'strategy_revision':hashlib.sha256(b'2fe4fa28 actual M6 signature regression fullfile coherent repair cheap worker family switch').hexdigest(),
 'reason':'Actual originalowner86 helper-only patch broke existing call signature and chose wrong module. Frozen M6 checker exposes TypeError;87testresponse was malformed and rejected. Fullfile constraint now scopes M6, cheap Worker family changes for a new complete repair; preserve failedsource/cost and original acceptance.', 'evidence_refs':refs}
dest=M/'continuation-feedback/veriarbor-35.json';assert not dest.exists();put(dest,d)
with (M/'WORK_LOG.md').open('a',encoding='utf-8') as f:
 f.write('\n\n34: originalowner86a2 source2fe4fa28 regresses M6 via unconnected3arghelper andwrongM11loaderpath. Frozen originalM6 diagnostic1/2TypeError preserved.87a6 completed6073outputtokens butINVALID_OR_INCOMPLETE_JSON rejectedbeforepublication, originaltestunchanged, no newUNKNOWN. Current M6-M11 are not claimedVERIFIED. Startup profile8views107.692of132.658seconds; receipt21 replaces metadata-only views with canonical_reload, still validates bindings and authenticatesrecord/view. Test guard qualification retains initialoverbroadtest failure and correctedtest original3FAIL/current4PASS. Read-only real no-op metadata refresh1sample15.328s->0.687s, noendtoendclaim.35usescheapQwenWorker andrequiresM6fullfilewithactualcallsiteclosure; nohostbusinesssourcepatch.\n')
print(dest)
