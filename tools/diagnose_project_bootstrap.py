"""Snapshot-only browser diagnosis; no candidate writes or acceptance authority."""
from pathlib import Path
import hashlib, importlib.util, json, sys, threading
from playwright.sync_api import sync_playwright

m = Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
out = m / sys.argv[1]
assert out.parent == m and not out.exists()
snapshot = m/(sys.argv[2] if len(sys.argv) > 2 else 'm12-product-143a28')/'snapshot'
assert snapshot.parent.parent == m
source = snapshot/'main.py'
out.mkdir()
sys.path.insert(0, str(snapshot))
spec = importlib.util.spec_from_file_location('bootstrap_diagnostic', source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
server = module.ThreadedHTTPServer('127.0.0.1', 0, str(out/'data'))
threading.Thread(target=server.serve_forever, daemon=True).start()
report = {'kind':'ProjectBootstrapBrowserDiagnostic','acceptance_authority':False,
          'host_business_patches':0,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page()
        failures = []; errors = []
        page.on('response', lambda response: failures.append({'url':response.url, 'status':response.status}) if response.status >= 400 else None)
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://127.0.0.1:'+str(server.server_port), wait_until='networkidle')
        page.get_by_label('Project name', exact=True).fill('Browser Created Project')
        with page.expect_response(lambda response: response.request.method=='POST' and 'project.create' in (response.request.post_data or '')) as pending:
            page.get_by_role('button', name='Create project', exact=True).click()
        response = pending.value
        page.wait_for_timeout(600)
        report.update(create_status=response.status, create_result=response.json(),
            visible_project_names=page.get_by_text('Browser Created Project', exact=True).filter(visible=True).count(),
            failed_http=failures, javascript_errors=errors, body=page.locator('body').inner_text())
        browser.close()
finally:
    server.shutdown(); server.server_close()
    (out/'receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
