from pathlib import Path
import json,hashlib
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
d=read(M/'continuation-feedback/veriarbor-44.json');f=d['feedback']
diag=read(M/'gui-media-dispatch-0e6de644/receipt.json');current=read(M/'GUI_MEDIA_CURRENT_API_4E3.json')
assert sha(R/'candidate/early_main.py')==diag['gui_source_sha256']==current['gui_sha256']
refs=[str(M/'gui-media-dispatch-0e6de644/receipt.json'),str(M/'GUI_MEDIA_CURRENT_API_4E3.json')]
f['fresh_runtime_diagnosis']={'applicability':{'artifact_hashes':{'early_main.py':diag['gui_source_sha256']}},
    'actual_failure_owner':91,'actual_failure_path':'early_main.py',
    'exact_http_response':diag['gui_media_import'],
    'actual_api_control':current,
    'diagnosis':'GUI HTTP POST M11 media.import/get returns400 {error:Unknown milestone:M11}; direct canonical media API import on current4e3 source returnsVALID and stores correct bytes. The GUI HANDLERS only registersM1-M7 and it contains noactualimage/video preview. This is91GUI request routing/preview, NOT117media path/signature/import. Rewriting117 cannot register a GUIhandler. Prior133 completed backend guard/idempotency then failed at GUI HTTPdispatch.117a7 was an unnecessary whitespace/unusedvariable rewrite; do not repeat or restore it without new APIcounterexample.',
    'evidence_refs':refs,
    'scope':'Diagnosis remains applicable only while GUI0e6 is unchanged. Use current canonical measurement for admission after117bytechange; no APIrepair inference from HTTP400. Once real GUIchanges this guidance expires automatically.'}
f['admission_correction']='Current source117 changed incidentally after133; if canonicalM11 evidence is missing, reuse existing133 or122 once with unchangedpredicate againstcurrentbytes. If currentM11 fails at GUIHTTP400, repair91-owned early_main.py with writer_target_ids-matched scope. Do not choose117 just because scope0 belongs toM11API. Preserve91 original dependencies; declare existingM11 file asboundedread, notcyclic117dependency. No duplicatecurrentmeasurement; afterGUIartifactdelta useactualnextfailure. CurrentM1-M10 remainfrozen/reusable.'
f['gui_writer_policy']='91 is the onlyGUIwriter. It must implement actualM11dispatch and mediaassetserving/preview; keep existingM7 workflow.89c3 nowguardslivebytes;86fa correctresolver;117current4e3 works. None shouldberewritten for Unknownmilestone:M11 fromGUIrouter. Testfixturedebtsremain fororiginaltestowners.'
f['redecision']={'strategy_revision':hashlib.sha256(b'GUI0e6 actualHTTP400 Unknown milestoneM11 directcurrent4e3APIvalid owner91 not117').hexdigest(),'reason':'Actual local HTTP response and directAPIcontrol identify the unchangedGUIrouter asfailure owner. PrioraggregateHTTPErrorwasmisattributed to117; boundedguidance now binds solely toGUIhash and expiresafterGUIchange. No olddiagnosis reused as proof of APIbug.','evidence_refs':refs}
with (M/'continuation-feedback/veriarbor-45.json').open('x',encoding='utf8') as out:json.dump(d,out,indent=2)
print('45 prepared with actualGUIHTTPerror andcurrentAPIpositivecontrol')
