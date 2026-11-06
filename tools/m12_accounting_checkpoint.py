"""Read-only ledger projection; estimates are not invoice totals."""
from pathlib import Path
from collections import Counter
import json,hashlib,datetime
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor');R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
ledger=Path('F:/CGKN-ITER-076/global-provider-budget.json');raw=ledger.read_bytes();data=json.loads(raw);base=json.loads((M/'M12_RESUME_BASELINE.json').read_text(encoding='utf8'))
rows=data['calls'][base['provider_calls_before']:]
report={'kind':'DerivedM12AccountingCheckpoint','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':base['checkpoint'],'baseline_rows':base['provider_calls_before'],'ledger_rows_observed':len(data['calls']),'new_rows':len(rows),'status_counts':dict(Counter(r['status'] for r in rows)),'ledger_model_counts':dict(Counter(r.get('model') for r in rows)),'numeric_total_tokens':sum(r['total_tokens'] for r in rows if type(r.get('total_tokens')) in (int,float)),'non_numeric_usage_rows':sum(type(r.get('total_tokens')) not in (int,float) for r in rows),'ledger_snapshot_sha256':hashlib.sha256(raw).hexdigest(),'ledger_writes_by_this_projection':False,'classification':'Pending REQUEST_STARTED is not UNKNOWN; final response/model provenance reconciliation remains required. No inference from ledger model alone.','estimated_cost_policy':'Retain original row estimates; no repricing or invoice claim','product_completion':False}
out=M/'accounting-checkpoints';out.mkdir(exist_ok=True);path=out/('m12-'+str(len(data['calls']))+'-'+report['ledger_snapshot_sha256'][:12]+'.json')
if not path.exists():path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report))
