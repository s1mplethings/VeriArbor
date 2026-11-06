"""Bind the existing complete-write policy to the current M12 repair."""
from pathlib import Path
import hashlib,json
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
S=R/'state/iter132-promotion-studio/promotion-05'
def read(p):return json.loads(p.read_text(encoding='utf8'))
source='c4368fee6981b386d28c6cd0ba6def72cbeac090cea5e5b70cb35d06a0ae1342'
assert hashlib.sha256((R/'candidate/main.py').read_bytes()).hexdigest()==source
assert not any(v['status']=='RUNNING' for v in read(S/'run_state.json')['nodes'].values())
c=next(c for c in reversed(read(S/'goal_acceptance.json')['checks']) if c['node_id']=='sem-node-0150')
assert c['attempt_id']=='attempt-0002' and c['verdict']=='FAILED'
bound={'path':'attempts/sem-node-0150/attempt-0002.json','receipt_hash':c['receipt_hash']}
refs=[str(S/bound['path']),str(M/'M12_143A13_DELTA.txt'),str(M/'m12-full-write-policy-qualification/pytest.log'),str(M/'m12-upload-8da2b883/receipt.json')]
policy={'scope_paths':['main.py'],'required_dimensions':['full_file_write'],'dimension_types':{'full_file_write':'boolean'},'forbidden_patterns':[{'full_file_write':False}],'evidence_refs':refs}
f={
 'cost_policy':'Use Qwen Flash Agent 7000 and DeepSeek Flash Worker 20000. No Pro/Max. Preserve all historical calls and nine new upstream UNKNOWNs. Do not replay old requests.',
 'milestone_completion_request':'Finish original M12, generated tests and documentation, actual browser/product validation, then the original packaging/delivery gate, accounting/provenance/Corpus and reports. Reuse verified M1-M11. Never grant product PASS from a successful source write. main.py has one owner: 143. Keep the frozen full M12 contract and all documented test debts. For the next bounded source task, implement the two concrete integration mechanisms below completely in one write. Remaining edit/new-content, project state, schedule/analytics, evidence/claim creation, reconciliation/revision comparison and test/documentation debts remain open after this slice.',
 'fresh_runtime_diagnosis':{
  'applicability':{'artifact_hashes':{'main.py':source}},
  'current_owner':143,'attempt':13,
  'native_current_failure':{'bound_reference':bound,'reason':c['observation']['observed']['reason']},
  'actual_last_change':'143a13 added only .hidden { display: none !important; }. It did not change the publish event path or the server upload handler. Full diff is recorded. Current native 150a2 still fails. Previous real GUI file selection and Import Media click returned HTTP400: path must be a non-empty string. The upload handler was not changed by a13.',
  'preserve':'All 11 server imports/handlers are correct. ThreadingHTTPServer is correct. Content navigation now refreshes Claims successfully. hydrateContentForm already exists and is invoked. Keep these and all backend modules unchanged.',
  'two_complete_changes':[
   'Make the existing unique Platform URL input and Publish button reachable from the Content workflow after Review/Approve, without requiring an extra navigation step. Move or reveal the actual controls; do not invent a nonexistent wrapper or merely add a CSS/helper declaration. Keep approval readiness based on the current content/revision. Preserve Schedule/Publish navigation.',
   'Complete real media upload end to end. Existing FileReader sends base64 data, filename, kind and project_id to POST /api/action with milestone M11 and op media.import. Add the GUI server adapter on that actual path: validate/decode bytes, use an owned bounded temporary file, call the existing M11 handler with its unchanged path-based contract, and clean the temporary file after the module has copied it. Do not use client filename as the storage destination. Invalid base64/empty bytes/project/kind must fail visibly via the existing HTTP error handling. Provide reachable Media navigation with Media file, Media kind and Import media controls; keep actual linked image/video previews and Content media selection. Do not add a disconnected alternate endpoint.'
  ],
  'atomic_execution_rule':'The existing executor ENDS THE DELEGATION after the first write or patch. A CSS-only patch cannot be followed by more writes in this task. Set strategy.full_file_write=true. The existing semantic adapter then allows only op 2 and rejects op 3. Return one complete main.py containing both changes, preserving all other code. The file is already supplied in context observations; do not reread it unnecessarily. Return exactly one raw JSON operation object, no prose or Markdown.',
  'remaining_contract_reference':str(M/'M12_REMAINING_GUI_API_CONTRACTS_8DA2B883.json'),
  'phase':'150a2 is the current canonical failure. Repair 143 with dependencies []. When main.py changes, this diagnosis expires. Measure the new source with existing 150 before any further source repair. Do not remeasure unchanged keys.',
  'evidence_refs':refs
 },
 'gui_writer_policy':'Only original node 143 writes main.py. Backend files and early_main.py remain unchanged. No parallel GUI writers. Host business patches remain zero.',
 'admission_correction':'Use a full initial repair decision with strategy and a TOP-LEVEL hypothesis. The exact current falsifying_evidence array is '+json.dumps([bound])+'. For main.py the only additional representation requirement is strategy.full_file_write=true (boolean). Other semantic strategy dimensions remain yours to express normally. Put the two complete runtime mechanisms and the one-write termination rule into the leaf goal/expected delta/strategy passed to the Worker. Do not retain obsolete claims-refresh failures or old 150a1 references. After a new write, request existing 150 on the new artifact before repairing again.',
 'strategy_constraints':[policy],
 'redecision':{'strategy_revision':hashlib.sha256(b'143a13 CSS-only incomplete repair actual one-write runtime full-file policy existing nine tests v1').hexdigest(),'reason':'Current a13 adds only CSS and native150a2 still fails. Existing full_file_write policy was not enabled for final main.py. Enable that original policy so a single partial patch cannot terminate this two-mechanism task. Nine existing operation-policy/constraint tests pass; no kernel, parser or product checker change. Remove obsolete whole-GUI strategy field representation constraints.','evidence_refs':refs}
}
with (M/'continuation-feedback/veriarbor-69.json').open('x',encoding='utf8') as o:json.dump({'expected_gui_sha256':'5c7e0f19981eb939cc7430b05ac5cd5ace03c2747dbdf9cbb7cf5c9e66e2e19b','feedback':f},o,indent=2,ensure_ascii=False)
with (M/'WORK_LOG.md').open('a',encoding='utf8') as o:o.write('\n-68:143a13 DeepSeek wrote only CSS .hidden rule, sourcec4368fee; actual upload/publish paths unchanged.150a2 current nativeFAILED.69 binds existing full_file_write=true policy (semantic allowed operations[2]) to main.py, preventing premature partial-patch completion. Nine existing policy/constraint testsPASS. No kernel/parser/checker changes; obsolete strategy field spelling constraints removed. Clear bounded two-mechanism guidance, all remaining obligations preserved.\n')
print(json.dumps({'continuation':69,'bound_current_failure':bound}))
