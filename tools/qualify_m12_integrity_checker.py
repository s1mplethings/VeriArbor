from pathlib import Path
import ast, copy, hashlib, json
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
checker=R/'consumer-revisions/final-gui-integrity-v6.py'
scope={};tree=ast.parse(checker.read_text(encoding='utf8'))
names={'require','assert_final_upload','assert_final_edit','assert_final_state'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(checker),'exec'),scope)
before=[{'id':'content-1','revision':1,'text':'Original'}]
after=[{'id':'content-1','revision':2,'text':'Edited'}]
approval={'content_id':'content-1','revision':2,'status':'DRAFT'}
upload={'id':'media-1','status':'VALID','sha256':'a'*64}
expected={'campaigns':[{'id':'campaign-1'}],'contents':after,'receipts':[],'schedules':[]}
cases=[
 ('valid_uploaded_bytes','positive','assert_final_upload',(200,upload,'a'*64),True),
 ('actual_upload_400','negative','assert_final_upload',(400,{'error':'path must be a non-empty string'},'a'*64),False),
 ('wrong_uploaded_identity','mutation','assert_final_upload',(200,upload,'b'*64),False),
 ('same_content_revision_advanced','positive','assert_final_edit',(before,after,approval,'Edited'),True),
 ('duplicate_content_save','negative','assert_final_edit',(before,before+after,approval,'Edited'),False),
 ('stale_approval','mutation','assert_final_edit',(before,after,{**approval,'status':'APPROVED','revision':1},'Edited'),False),
 ('wrong_edited_identity','mutation','assert_final_edit',(before,[{**after[0],'id':'new-content'}],approval,'Edited'),False),
 ('actual_scoped_state','positive','assert_final_state',(copy.deepcopy(expected),expected),True),
 ('false_empty_state','negative','assert_final_state',({k:[] for k in expected},expected),False),
 ('cross_project_state','mutation','assert_final_state',({**expected,'campaigns':[{'id':'foreign'}]},expected),False),
]
rows=[]
for name,kind,function,args,expected_pass in cases:
 try:scope[function](*args);observed=True;error=''
 except AssertionError as e:observed=False;error=str(e)
 rows.append({'name':name,'kind':kind,'expected':expected_pass,'observed':observed,'passed':observed==expected_pass,'error':error})
assert all(row['passed'] for row in rows)
report={'kind':'FinalGuiIntegrationObserverControls','status':'PASS','controls':rows,
 'checker_hash':hashlib.sha256(checker.read_bytes()).hexdigest(),
 'previous_checker_hash':hashlib.sha256((R/'consumer-revisions/media-gui-v5.py').read_bytes()).hexdigest(),
 'scope':['M12'],'qualification_only':True,'product_acceptance_granted':False,
 'control_scope':'Deterministic observer predicate controls; actual browser driver executes against the product only in native M12 checks. These are not claims that a positive product exists.',
 'actual_negative_evidence':str(M/'m12-gui-650460ff/receipt.json'),
 'preserved_assertions':'All previous M12 browser and other milestone assertions remain; new probe adds actual file input, media attachment, same-record semantic edit, approval invalidation, scoped state, foreign-media rejection and process restart.'}
with (M/'M12_GUI_V6_QUALIFICATION.json').open('x',encoding='utf8') as out:json.dump(report,out,indent=2)
print(json.dumps({'controls_passed':len(rows),'checker_hash':report['checker_hash'],'product_acceptance_granted':False}))
