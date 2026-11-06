"""Qualify visible-field lookup; preserve hidden/ambiguous negative behavior."""
from pathlib import Path
import ast,hashlib,json
from playwright.sync_api import sync_playwright
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
old=R/'consumer-revisions/final-gui-complete-v8.py'
source=old.read_text(encoding='utf8')
needle="page.get_by_label('Platform URL',exact=True)"
assert source.count(needle)==2
source=source.replace(needle,needle+'.filter(visible=True)')
ast.parse(source)
controls=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(channel='msedge',headless=True)
 try:
  page=browser.new_page()
  cases=[('single_visible',[True],True),('visible_and_hidden',[True,False],True),('hidden_before_visible',[False,True],True),('all_hidden',[False,False],False),('two_visible',[True,True],False)]
  for name,visibility,expected in cases:
   page.set_content(''.join('<section'+('' if visible else ' style="display:none"')+'><label for="p'+str(i)+'">Platform URL</label><input id="p'+str(i)+'"></section>' for i,visible in enumerate(visibility)))
   locator=page.get_by_label('Platform URL',exact=True).filter(visible=True)
   try:locator.fill('http://127.0.0.1:8001',timeout=300);ok=True
   except Exception:ok=False
   assert ok==expected
   controls.append({'name':name,'kind':'positive' if expected else 'negative','passed':ok==expected})
  tree=ast.parse((R/'candidate/main.py').read_text(encoding='utf8'))
  html=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='INDEX_HTML' for t in n.targets))
  page.set_content(html)
  page.evaluate("document.querySelectorAll('.view').forEach(e=>e.classList.remove('active'));document.querySelector('#content-view').classList.add('active')")
  assert page.get_by_label('Platform URL',exact=True).count()==2
  page.get_by_label('Platform URL',exact=True).filter(visible=True).fill('http://127.0.0.1:8001')
  controls.append({'name':'actual143a14_content_dom_visible_platform','kind':'positive','passed':True})
 finally:browser.close()
target=R/'consumer-revisions/final-gui-complete-v9.py'
with target.open('x',encoding='utf8') as f:f.write(source)
prior=json.loads((M/'M12_GUI_V8_QUALIFICATION.json').read_text(encoding='utf8'))
report={**prior,'kind':'VisiblePlatformLocatorQualification','checker_hash':hashlib.sha256(target.read_bytes()).hexdigest(),'previous_checker_hash':hashlib.sha256(old.read_bytes()).hexdigest(),'controls':prior['controls']+controls,'control_scope':'Six real browser controls include actual candidate DOM. Visible field selected despite hidden same-name field; no visible field and two visible matches still fail. No business assertions removed.','preserved_assertions':'All v8 business assertions retained; only two Platform URL field lookups filter visible elements. Existing historical failure retained; no product acceptance granted.'}
with (M/'M12_GUI_V9_QUALIFICATION.json').open('x',encoding='utf8') as f:json.dump(report,f,indent=2)
print(json.dumps({'controls':len(report['controls']),'checker_hash':report['checker_hash'],'product_acceptance_granted':False}))
