from pathlib import Path
import json,hashlib,datetime
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
p=M/'M12_CURRENT_FAILURE_CONTEXT.json';raw=p.read_bytes();archive=M/'context-history'/('M12_CURRENT_FAILURE_CONTEXT-'+hashlib.sha256(raw).hexdigest()[:12]+'.json')
if not archive.exists():archive.write_bytes(raw)
ctx=read(p);ctx.update(updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),formal_current_failure={'path':'attempts/sem-node-0158/attempt-0001.json','receipt_hash':'86c12b1d71d9d43dc63d909532b9e900c6b4812d8a229cc16e31016aa79a0dde'},checker_identity='qualified-revision-10',bound_source_sha256='61bebcfedac3c0624cdb0bb1a65e208eeb05a95eb664488042b5b84ecb11bdd4',actual_current_failure='Sequential browser image/video flow passes 35 checks; 12 concurrent preview reads expose shared media.json.tmp collision. Original path imports and explicit milestone dispatch also regress. Full B02 requires 38 checks before certification.',latest_execution_failure=read(M/'B02_SCOPE_REJECTION_35.json'),next_action='Bounded attempt36 inside handle/media adapter only; require real source delta before local browser measurement.',active_continuation='veriarbor-98',source_writer_may_be_in_flight=True,previous_context_retained=str(archive))
ctx['invalidated_historical_strategies']=['B01 bootstrap complete and frozen','Old handler identity problems resolved','Threaded HTTP dispatch works; new distinct M11 shared temporary-file concurrency failure remains','Full-file rewrite forbidden','Attempt28/29 output without delta is not implementation','Media-serving-only implementation is not complete B02','Attempt35 out-of-region serving patch rejected; no product change']
write(p,ctx)
p=M/'M12_BLOCK_STATUS.json';status=read(p);status.update(authority='Derived view of canonical evidence; block certificates grant their own scopes only',active_continuation='veriarbor-98',latest_candidate_measurement='b02-concurrent-preview-61bebcfe/receipt.json',updated_at=ctx['updated_at']);write(p,status)
print('Updated derived current-context/status; historical context preserved.')
