"""Strengthen independent analytics measurement; never grant product acceptance."""
from pathlib import Path
import ast, copy, hashlib, json

R = Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M = Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
old = R/'consumer-revisions/final-gui-complete-v9.py'
source = old.read_text(encoding='utf8')
needle = "                        page.get_by_role('button',name='Fetch analytics',exact=True).first.click()\n                        page.get_by_text('11',exact=False).first.wait_for(timeout=5000)"
replacement = """                        with page.expect_response(lambda r: r.url.endswith('/api/action') and 'analytics.fetch' in (r.request.post_data or '')) as pending:
                            page.get_by_role('button',name='Fetch analytics',exact=True).first.click()
                        response = pending.value
                        receipts = http_action(url,'M9','receipt.list',project_id=pid)['items']
                        assert_final_analytics(response.status,response.json(),receipts,remote)
                        page.get_by_text('11',exact=False).first.wait_for(timeout=5000)"""
assert source.count(needle) == 1
helper = '''
def assert_final_analytics(status, sample, receipts, remote):
    require(status == 200, 'Actual GUI analytics request failed')
    require(sample.get('metrics') == {'views':11,'impressions':23,'reactions':3,'comments':2},
            'GUI analytics must match actual platform metrics')
    matching = [r for r in receipts if r.get('id') == sample.get('receipt_id')]
    require(len(matching) == 1, 'Analytics must reference one actual receipt')
    receipt = matching[0]
    require(receipt.get('status') == 'PUBLISHED' and receipt.get('remote_id') == remote,
            'Analytics must reference the actual GUI publication')
    require(sample.get('revision') == receipt.get('revision') and
            sample.get('channel') == receipt.get('channel') and bool(sample.get('fetched_at')),
            'Analytics must retain published revision/channel and fetch timestamp')

'''
source = source.replace(needle, replacement)
source = source.replace('def browser_probe(entry,full):', helper+'def browser_probe(entry,full):')
ast.parse(source)
def require(condition, message):
    if not condition:
        raise AssertionError(message)
namespace = {'require': require}
exec(helper, namespace)
sample = {'metrics': {'views':11,'impressions':23,'reactions':3,'comments':2},
          'receipt_id':'receipt-actual','revision':2,'channel':'alpha','fetched_at':'2026-11-04T00:00:00Z'}
receipt = {'id':'receipt-actual','status':'PUBLISHED','remote_id':'remote-actual','revision':2,'channel':'alpha'}
cases = [('exact_metrics_and_binding', 200, sample, [receipt], True),
         ('http400_even_with_matching_numbers', 400, sample, [receipt], False),
         ('missing_metrics_uuid_contains11', 200, {'receipt_id':'uuid11'}, [receipt], False),
         ('wrong_metrics', 200, {**sample, 'metrics':{**sample['metrics'],'views':12}}, [receipt], False),
         ('foreign_receipt', 200, {**sample,'receipt_id':'other'}, [receipt], False),
         ('stale_revision', 200, {**sample,'revision':1}, [receipt], False),
         ('wrong_channel', 200, {**sample,'channel':'beta'}, [receipt], False),
         ('missing_timestamp', 200, {**sample,'fetched_at':''}, [receipt], False),
         ('unknown_receipt', 200, sample, [{**receipt,'status':'UNKNOWN'}], False),
         ('different_remote', 200, sample, [{**receipt,'remote_id':'other'}], False),
         ('ambiguous_receipt', 200, sample, [receipt,receipt], False)]
controls=[]
for name, status, value, receipts, expected in cases:
    try:
        namespace['assert_final_analytics'](status,copy.deepcopy(value),copy.deepcopy(receipts),'remote-actual')
        observed=True
    except AssertionError:
        observed=False
    assert observed == expected, name
    controls.append({'name':name,'kind':'positive' if expected else 'mutation','passed':True})
target=R/'consumer-revisions/final-gui-complete-v10.py'
with target.open('x',encoding='utf8') as f:
    f.write(source)
prior=json.loads((M/'M12_GUI_V9_QUALIFICATION.json').read_text(encoding='utf8'))
report={**prior,'kind':'ActualAnalyticsResponseBindingQualification',
        'checker_hash':hashlib.sha256(target.read_bytes()).hexdigest(),
        'previous_checker_hash':hashlib.sha256(old.read_bytes()).hexdigest(),
        'controls':prior['controls']+controls,
        'control_scope':'Eleven exact response/binding controls supplement existing 21 controls. Real browser diagnostic m12-gui-contracts-041a367e shows HTTP400 even though old native probe passed its first subtest.',
        'preserved_assertions':'All v9 assertions retained. Added actual analytics HTTP status, exact platform metrics, actual published receipt, remote ID, revision, channel and timestamp checks. No product acceptance granted.'}
with (M/'M12_GUI_V10_QUALIFICATION.json').open('x',encoding='utf8') as f:
    json.dump(report,f,indent=2)
print(json.dumps({'controls':len(report['controls']),'checker_hash':report['checker_hash'],'product_acceptance_granted':False}))
