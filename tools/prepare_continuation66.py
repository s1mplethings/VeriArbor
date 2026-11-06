"""Provide bounded runtime evidence to the original Agent, not product code."""
import json,hashlib
from pathlib import Path
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
S=R/'state/iter132-promotion-studio/promotion-05'
def read(p):return json.loads(p.read_text(encoding='utf8'))
source='8da2b8839f19ab62297a5ea4df7b2b1b7cb875ee77cedf80185456ceddf6018f'
assert hashlib.sha256((R/'candidate/main.py').read_bytes()).hexdigest()==source
assert not any(v['status']=='RUNNING' for v in read(S/'run_state.json')['nodes'].values())
c=next(c for c in reversed(read(S/'goal_acceptance.json')['checks']) if c['node_id']=='sem-node-0150')
assert c['verdict']=='FAILED' and 'Platform URL' in c['observation']['observed']['reason']
bound={'path':'attempts/sem-node-0150/attempt-0001.json','receipt_hash':c['receipt_hash']}
d=read(M/'continuation-feedback/veriarbor-65.json');f=d['feedback']
refs=[str(S/bound['path']),str(M/'m12-upload-8da2b883/receipt.json'),str(M/'M12_143A11_DELTA.txt'),str(M/'m12-dispatch-8da2b883/receipt.json')]
f['fresh_runtime_diagnosis']={
 'applicability':{'artifact_hashes':{'main.py':source}},
 'current_owner':143,'attempt':11,
 'native_current_failure':{'bound_reference':bound,'reason':c['observation']['observed']['reason']},
 'resolved':'Content nav nowactually invokes loadClaims/loadMedia/loadContents. Native150 proceeds pastClaims to hiddenPlatformURL. All11serverroutes andactualprojectcreatePASS; keepimports/ThreadingHTTPServer/backendmodules unchanged. hydrateContentForm alreadyexistsandiscalled byloadContents/select; do not falselyclaimabsent.',
 'actual_delta':'143a11 adds onlyContentnavrefresh plusfrontendfileinput/ImportMedia handler. NoPythonuploadbridge, noexistingcontent.edit, noscopedstatefix, noJSschedulemapfix. Exactdiff preserved.',
 'bounded_next_leaf':'Same writer143, main.py only. Close TWO concrete connectedGUIgaps atomically: (1) visible reachable Platform URL and Publish afterReview/Approve inContent workflow, keeping actualapprovalreadiness anduniqueDOMIDs; (2) completeactualmediaimport UI-to-server-toM11path bridge. Existingdata base64payload goes straighttoM11 andreturns400 path mustbe nonempty. Add actualserverowned boundedtemporaryfile adaptation beforecallingunchangedM11media.import; ensurecleanupafterM11copiesbytes; validatebadbase64/empty/project/kind throughnormal400errors, donotuseclientfilenameaswritepath. Provide reachableMedia navigation and labeledMedia file/Media kind/Import media controls; preserveContentmedia selection/actualimagevideo previews andnavrefresh. This is a bounded implementation slice, not a reductionof finalM12acceptance. Do notclaimfullM12PASSafterit.',
 'required_worker_handoff':'Put both complete mechanisms in leaf_goal, expected_delta andstrategy soWorker receives executable requirements. Worker must return rawJSONONLY, nointro/Markdown/codefences; previous readcommandwithprosewas INVALID_OUTPUT. Preserve existingbehavior andallcorrectimports; do not replacewholeappwithsimplifiedplaceholder.',
 'remaining_after_slice':'CurrentSavealwayscontent.create, noNewcontentmode; /api/state ignoresprojectquery andswallowsmissingIDs; scheduleJS usesM11 insteadM8, analyticsM11insteadM10; receipts needactualM9contract; reconcile/variants/compare remain. These stillmustbe completed underfrozenM12contract, but do not describe themasimplemented by143a11. Tests144server.portfixture/docs145146 debtsalsoopen.',
 'evidence_refs':refs,
 'phase':'Current150FAILED alreadymeasured. Repair143 twoboundedgaps withdeps[]; aftersourcechanges expires, thenmeasurecurrentkey using150 ifready, notoldsourcefailure.'}
f['admission_correction']='Currentmain8da2b883 has trustednative150a1FAILED hiddenPlatformURL andrealGUIuploadHTTP400. Repair original143deps:[]; use full initialstrategy and TOP-LEVEL hypothesis (not inside strategy), falsifying_evidence ARRAY '+json.dumps([bound])+'. Retain existingstrategy dimensions required byconstraints, exactcorrectmodulebindings/preservationflags. gui_event_paths must describe actualreachableContentworkflowPlatformURL/Publish visibility plusMediafile/FileReader->servertemporarypath->unchangedM11media.import->preview, notjustfrontendbutton. Outputformat rawJSONonly. Only these two concreteintegrationgaps fornextboundedleaf, retainingallotherfinalobligations. Oncehashchanges thisfailure isold; measure150currentbeforefurtherbusinessrepair. Nevercreateanothermain.pywriter.'
f['cost_policy']='QwenFlashAgent7000/Worker24000 only, noPro/Max. NineupstreamUNKNOWN preserved. Thisnewsource/currentnativefailure/actualGUIuploadcounterexample is newevidence; noreplayofoldrequests.'
f['redecision']={'strategy_revision':hashlib.sha256(b'143a11 real claims progress and150 platform visibility plus actual upload400 bounded atomic integration v1').hexdigest(),'reason':'143a11 fixesClaimsrefresh butonlyadds frontendupload; native150 nowfailsPlatformURLvisibility andactualfilebuttonreturns400missingpath. Narrow nextboundedleaf to completevisibility+uploadadapter, preservecorrectrouting/threading. Finalcontractunchanged; otherremainingdebtsretained.','evidence_refs':refs}
with (M/'continuation-feedback/veriarbor-66.json').open('x',encoding='utf8') as out:json.dump(d,out,indent=2,ensure_ascii=False)
with (M/'WORK_LOG.md').open('a',encoding='utf8') as out:out.write('\n-65:143a10invalidJSONprose/read rejected;143a11Qwencompleted8da2b883, Claimsnavrefresh realprogress andfrontenduploadonly. All11routes/staticDOMPASS. Realfileinput+button upload400missingpath. Native150a1qualifiedrev6FAILED hiddenPlatformURL, pastClaims. Safeheldaftermeasurement.66boundednextleaf actualpublishvisibility+serveruploadpathadapter, existinghydrationpreserved, remainingedit/scopedstate/schedule/docs/testsdebtsretained. No businesssourcepatchbyhost.\n')
print(json.dumps({'feedback':66,'current_failure':bound}))
