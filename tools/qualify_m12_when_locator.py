"""Correct observer label coupling without dropping any business assertion."""
from pathlib import Path
import ast, hashlib, json, re
from playwright.sync_api import sync_playwright
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
old=R/'consumer-revisions/final-gui-complete-v7.py'
source=old.read_text(encoding='utf8')
needle="page.get_by_label('When (ISO8601)',exact=True)"
assert source.count(needle)==2
source=source.replace(needle,"page.get_by_label(re.compile(r'^When(?: \\(ISO8601\\))?$'))")
source=source.replace('def final_gui_integrity_probe():\n    import base64','def final_gui_integrity_probe():\n    import base64, re')
ast.parse(source)
controls=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True)
    try:
        page=browser.new_page()
        for label,expected in (('When',True),('When (ISO8601)',True),('Unrelated field',False)):
            page.set_content('<label for="input">'+label+'</label><input id="input">')
            locator=page.get_by_label(re.compile(r'^When(?: \(ISO8601\))?$'))
            found=locator.count()==1
            if found:locator.fill('2026-11-05T10:00:00+08:00');assert locator.input_value().endswith('+08:00')
            controls.append({'name':'actual_browser_label_'+label,'kind':'positive' if expected else 'negative','passed':found==expected})
    finally:browser.close()
assert all(c['passed'] for c in controls)
target=R/'consumer-revisions/final-gui-complete-v8.py'
with target.open('x',encoding='utf8') as f:f.write(source)
prior=json.loads((M/'M12_GUI_V7_QUALIFICATION.json').read_text(encoding='utf8'))
report={**prior,'kind':'GuiObserverLabelCompatibilityQualification',
 'checker_hash':hashlib.sha256(target.read_bytes()).hexdigest(),
 'previous_checker_hash':hashlib.sha256(old.read_bytes()).hexdigest(),
 'controls':prior['controls']+controls,
 'control_scope':'Prior12 controls retained plus3 actualbrowser selector controls. Accepts frozen When label and earlier When (ISO8601); rejects unrelated input. No business assertion weakened, no product acceptance granted.',
 'preserved_assertions':'All v7 assertions retained. Only schedule time locator accepts both observed contract-compatible accessible labels.'}
with (M/'M12_GUI_V8_QUALIFICATION.json').open('x',encoding='utf8') as f:json.dump(report,f,indent=2)
print(json.dumps({'checker_hash':report['checker_hash'],'controls':len(report['controls']),'product_acceptance_granted':False}))
