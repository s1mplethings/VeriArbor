"""Current GUI contract repair guidance through the original Agent route."""
from pathlib import Path
import hashlib,json
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
S=R/'state/iter132-promotion-studio/promotion-05'
def read(p):return json.loads(p.read_text(encoding='utf8'))
assert not any(v['status']=='RUNNING' for v in read(S/'run_state.json')['nodes'].values())
c=next(c for c in reversed(read(S/'goal_acceptance.json')['checks']) if c['node_id']=='sem-node-0151')
assert c['attempt_id']=='attempt-0002' and c['verdict']=='FAILED'
assert read(S/'attempts/sem-node-0151/attempt-0002.json')['outputs']['goal_check']['checker_version']=='qualified-revision-7'
bound={'path':'attempts/sem-node-0151/attempt-0002.json','receipt_hash':c['receipt_hash']}
d=read(M/'continuation-feedback/veriarbor-70.json');f=d['feedback']
refs=[str(S/bound['path']),str(M/'M12_REMAINING_GUI_API_CONTRACTS_8DA2B883.json'),str(M/'m12-upload-8981690e/receipt.json'),str(M/'m12-generated-tests-8981690e/receipt.json')]
f['fresh_runtime_diagnosis']={
 'applicability':{'artifact_hashes':{'main.py':'8981690ec13e83042dc170ec62f202e67fb12b6ac4378a34a3cb1e0f36fe0afd'}},
 'current_owner':143,'attempt':14,
 'native_current_failure':{'bound_reference':bound,'reason':c['observation']['observed']['reason']},
 'resolved':'Native151a2 qualifiedrev7 now passes Claims, visiblePlatformURL and actual local HTTP publication/receipt. Fails Fetch analytics on Receipts/Analytics view. RealPNGupload200/hashbytesmatch and malformedbase64400 independently proven. Preserve these working paths, all11serverimports, ThreadingHTTPServer, existinghydration andbackends.',
 'current_failure_mechanism':'Fetch analytics exists only inside hidden schedule-view, not receipts-analytics-view. Even if clicked, it dispatches M11 analytics.fetch with content_id only, but actual M10 requires project_id, receipt_id, platform_url. loadAnalytics also calls nonexistent M11 analytics.list. This is real GUI wiring, not a checker locator defect.',
 'complete_next_gui_integration':[
  'Move the existing unique Fetch analytics action into Receipts/Analytics. Maintain an actual receipt selection (default the current PUBLISHED receipt when one exists), retain the platform URL used to publish across view transitions/reload, call M10 analytics.fetch(project_id,receipt_id,platform_url), then M10 analytics.history(project_id,receipt_id) and render returned metrics/history. Empty/UNKNOWN/nonpublished receipt must have a visible appropriate state, not a false empty success. Preserve actual remote IDs in receipt display.',
  'Correct Schedule/Publish operations to M8 (currently incorrectly M11). schedule.create needs project_id,content_id,platform_url,idempotency_key,when; cancel/reschedule need selected actual schedule_id, reschedule when. Provide actual schedule selection; select newly created record. Keep timezone-aware input and persistence. Share the configured Platform URL with Content publish and Receipts analytics; no stale blank duplicate fields.',
  'Make the working upload bridge discoverable: reachable Media navigation with Media file, Media kind, Import media controls, using the existing /api/action media.import base64-to-path adapter. Preserve Content media selection and linked image/video preview. Do not reimplement the already working backend bridge or alter M11.',
  'Save an existing selected content using M5 content.edit with current content_id; preserve hydration. Provide explicit New content to clear selection and create a distinct content/channel variant; after save select returned actual ID. Reload current approval/status after edit so semantic change becomes DRAFT and cannot publish on historical approval. Preserve original revision history.',
  'Fix /api/state?project_id explicitly: validate project through M1 project.get, return actual M4 campaigns, M5 contents, M9 receipts and M8 schedules for that project, do not swallow missing project errors as empty arrays. Unknown project returns400. No cross-project rows. Keep project list available for startup.'
 ],
 'atomic_protocol':'Original executor ends after first write. strategy.full_file_write=true enforces op2 only. Return one complete main.py addressing every listed integration branch, not a partial CSS/import/helper change. Raw JSON operation only, no prose/Markdown. Existing source and backend contracts are available in observations/read scope; use actual APIs.',
 'remaining_afterward':'Original frozen fullM12 still includes evidence/claim/Signals workflow, UNKNOWN reconcile, revision comparison, meaningful tests anddocs. Channelvariants use actualcontent.create onanotherchannel, no inventedcontent.variant op. Test144 has5PASS1knownfixturefailure self.server.port; original testowner must fix server_port andkeepPUBLISHEDassertion, scopedquery/validPNG. No productPASSuntilfull originalacceptance+delivery.',
 'evidence_refs':refs,
 'phase':'Current151a2 is observedfailure. Repair143 deps[] now; afternewsource measurecurrent151 beforefurtherrepair. PreserveM1-M11reuse.'
}
f['admission_correction']='Repair original143 dependencies[] from current151a2 failure. Use initial fullstrategy with full_file_write:true boolean and TOP-LEVEL hypothesis.falsifying_evidence='+json.dumps([bound])+'. Put the actual analytics receipt/URL contracts, M8 scheduler fields, existingcontent.edit/Newcontent, Media navigation andscopedstate mechanisms into the boundedWorker leaf goal/expected. Preserveworkingupload/publication/Claims. No anotherGUIwriter. Afternewsource, measureexisting151 currentkey, neverreplayunchangedchecks.'
f['redecision']={'strategy_revision':hashlib.sha256(b'151a2 rev7 actual publish works analytics unreachable actual M10 M8 edit state contracts integration v1').hexdigest(),'reason':'Qualified current151a2 passes actualpublication thenfailsFetchanalytics hiddenwrongview. ActualAPI audit identifies missingreceipt/URL andwrongmodule bindings, plus existingedit/scopedstate/media navigation gaps. CompleteGUIintegration underexistingfull-file policy, backendsfrozen.','evidence_refs':refs}
with (M/'continuation-feedback/veriarbor-71.json').open('x',encoding='utf8') as o:json.dump(d,o,indent=2,ensure_ascii=False)
with (M/'WORK_LOG.md').open('a',encoding='utf8') as o:o.write('\n-70:151a2qualifiedrev7 passesactualpublish thenfailsFetchanalytics unreachable inReceiptsview. CurrentgeneratedM12tests5PASS1knownplatformfixtureFAIL.71original143 fullwrite actualM10receipt/URLhistory+M8schedulecontract/editNewcontent/scopedstate/Mediaentry integration, preserveworkinguploadandpublish.\n')
print(json.dumps({'continuation':71,'failure':bound}))
