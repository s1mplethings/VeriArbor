"""Advance only from the current authenticated GUI counterexample."""
from pathlib import Path
import json,hashlib
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
S=R/'state/iter132-promotion-studio/promotion-05'
def read(p):return json.loads(p.read_text(encoding='utf8'))
assert not any(v['status']=='RUNNING' for v in read(S/'run_state.json')['nodes'].values())
c=next(c for c in reversed(read(S/'goal_acceptance.json')['checks']) if c['node_id']=='sem-node-0153')
assert c['verdict']=='FAILED'
bound={'path':'attempts/sem-node-0153/attempt-0001.json','receipt_hash':c['receipt_hash']}
d=read(M/'continuation-feedback/veriarbor-72.json');f=d['feedback']
refs=[str(S/bound['path']),str(M/'m12-gui-contracts-041a367e/receipt.json'),str(M/'M12_143A18_DELTA.txt'),str(M/'m12-dispatch-143a18/receipt.json')]
f['cost_policy']='QwenFlash Agent7000/Worker24000 only, noPro/Max. Preserve10newUNKNOWNs. New143a18artifact/currentnativefailure andactualbrowsercounterexamples justify next boundedrepair.'
f['fresh_runtime_diagnosis']={
 'applicability':{'artifact_hashes':{'main.py':'041a367eaaaf2b318ecd380f26a5227019733457bce918de5d224286dd35e8cb'}},
 'current_owner':143,'attempt':18,'native_current_failure':{'bound_reference':bound,'reason':c['observation']['observed']['reason']},
 'preserve_proven_behaviors':'Actual browser uploadedPNG/video, decodedattachedvideo, publishedoverrealHTTP, verifiedreceipt/mediarevisionbinding andidempotency, restartedprocessandreadreceipt/media, editedSAMEcontentID rev1->2 withapprovalDRAFT, blockedunapprovededit andchanged/missingmedia beforePOST. NoJSerrors. All11serverroutes/staticDOMPASS. Do notrewritebackend, removeedit/Newcontent, breakuploadbridge/publishcontrols/Claimsrefresh/threading.',
 'remaining_actual_mechanisms':[
  'Analytics button is now reachable and calls M10, but it reads receipt.platform_url. ACTUAL receipt has NO platform_url: browser request sends emptystring andreturns400. Preserve configured Platform URL from actualinput in state/localStorage, synchronize Content andSchedule inputs onchange, reuse it for analytics. Alternatively parse actual receipt.request_ref which is the original platform /publish URL, not receipt.url (remote item URL). Analytics fetch requires project_id,receipt_id,platform_url; history requires project_id AND receipt_id (currently missing). Use same actual selected/current PUBLISHED receipt for both and render returned metrics. Preserve receipts remoteIDs.',
  'Schedule usesM8 now, but createpayload contains onlyproject_id/content_id/when. Actualclick400 platform_url required. Add shared configured platform_url AND idempotency_key, then select returned schedule.id soCancel/Reschedule are usable; currentstate.scheduleId neverassigned. loadSchedules must restore/display actualselection. No APIbackendchange.',
  '_serve_state still ignoresproject_idquery; eachproject-boundlist calledwithoutID anderrorsswallowed. ActualGETwithproject_id returns emptycontents/receipts despitepublishedcontent. Passparsedquery tostatehandler; validate requestedproject viaM1project.get then call M4campaign.list,M5content.list,M9receipt.list,M8schedule.list with project_id. Unknownproject400, foreignprojectonlyownrows. No blank200 maskingerrors. Startupprojectlistwithoutselectedproject mayreturnprojects+emptyprojectboundarrays explicitly.',
  'Mediauploadworks but remainsonlyContent Uploadmedia/ImportMedia with noMedia nav. Provide reachableMedia nav/section with labelMedia file, labelMedia kind and buttonImport media, connectedtoexistingbase64serverbridge. PreserveContentmedia selectandactuallinkedpreview. UseuniqueDOMIDs and navshowView includesnewsection; no unusedhelper.'
 ],
 'atomic_protocol':'One original143 full-file write: strategy.full_file_write=true, rawJSONop2 only, no prose/Markdown/XML toolcalls. Include all four concrete mechanisms inleafgoal/expected passedtoWorker. These are missingarguments/state/visiblecontrols, notbackenddefects. Do not change onlymodule tags again; alreadycorrect.',
 'next':'Repair143deps[] fromcurrent153failure. Afternewsource measurecurrent153key beforeanotherrepair. NoM1-M11checks. Original test/docs debts remain; contentcompare/reconcile/Signals fullworkflow stillrequired forfinalproduct.',
 'evidence_refs':refs
}
f['admission_correction']='Current143a18 main041a367e has native153a1failure andrealbrowseranalytics400/schedule400/scopedemptycounterexamples. Repair original143deps[] withstrategy.full_file_write:true andTOP-LEVELhypothesis.falsifying_evidence='+json.dumps([bound])+'. Pass all four concrete mechanisms above toWorker; preserve all measuredworkingflows. Actualreceipt hasrequest_ref, NOTplatform_url. Newsource thenmeasure153 currentkey; no newduplicatewriter, no oldfailure repair. RawJSONonly.'
f['redecision']={'strategy_revision':hashlib.sha256(b'143a18 actual browser receipt missing platformurl scheduleargs state scope Media nav v1').hexdigest(),'reason':'143a18 nowprovesrealvideo/publication/restart/editinvalidation, butactualrequestsprove missingplatformURL/idempotency/receiptID/projectscope andMediaentry. Concretecurrentbrowser+nativecounterexamples supportcompleteGUIargument/state closure, verifiedbackends unchanged.','evidence_refs':refs}
with (M/'continuation-feedback/veriarbor-73.json').open('x',encoding='utf8') as o:json.dump(d,o,indent=2,ensure_ascii=False)
with (M/'WORK_LOG.md').open('a',encoding='utf8') as o:o.write('\n-72:143a17XMLtoolcall INVALID_OUTPUT;143a18Qwen fullwrite041a367e. RealbrowserPNG/video/attacheddecode/localpublish/idempotency/restartreceiptmedia/editSAMEIDapprovalDRAFT/changedmissingmediarejectPASS. Actualschedule400missingURL/key, analytics400absentreceipt.platform_url, historymissingreceiptID, scopedstatefalseempty. Mediaentrymissing.153currentnativeFAIL;73completefourargument/state/navigationmechanisms, preserveprovenflows.\n')
print(json.dumps({'continuation':73,'failure':bound}))
