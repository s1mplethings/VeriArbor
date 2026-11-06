"""Materialize an honest checkpoint report from current canonical evidence."""
import datetime
import hashlib
import json
import subprocess
import sys
from capture_baseline import H, V, P

def read(p): return json.loads(p.read_text(encoding='utf8'))
sys.path.insert(0, str(H))
from cgkn.state import FileRunStore
from cgkn.state.acceptance import GoalAcceptance

root = P / 'promotion/run-05'
profile = read(root / 'profile.json')
run = root / 'state' / profile['project_id'] / profile['run_id']
data = read(run / 'goal_acceptance.json')
view = GoalAcceptance(FileRunStore(root / 'state'), profile['project_id'], profile['run_id'], data['requirements'], data['checker_bindings']).view()
ledger = read(P.parents[1] / 'CGKN-ITER-076/global-provider-budget.json')
before = read(root / 'continuations/veriarbor-01/accounting-before.json')
calls = ledger['calls'][len(before['calls']):]
assert ledger['calls'][:len(before['calls'])] == before['calls']
models = {m: sum(c['model'] == m for c in calls) for m in sorted({c['model'] for c in calls})}
states = {s: sum(c['status'] == s for c in calls) for s in sorted({c['status'] for c in calls})}
head = subprocess.check_output(['git', '-c', 'safe.directory=D:/VeriArbor', '-C', str(V), 'rev-parse', 'HEAD'], text=True).strip()
switches = [json.loads(line) for line in (H / 'migration/veriarbor/AUTHORITY_SWITCH_RECEIPTS.jsonl').read_text().splitlines()]
checks = read(V / 'REGRESSION.json')['checks']
milestones = '\n'.join(f"| {k} | {v['verdict']} |" for k, v in view['obligations'].items())
last = max((root / 'continuations').glob('veriarbor-*/started.json'), key=lambda p:p.stat().st_mtime).parent
result = read(last / 'result.json') if (last / 'result.json').exists() else {}
blocker = result.get('result', {}).get('escalation_reason', 'See latest continuation execution-error/controller-interruption evidence')
dogfood = read(root / 'DOGFOOD_MVP/receipt.json') if (root / 'DOGFOOD_MVP/receipt.json').exists() else {}
report = f'''# VeriArbor / CGKN / Promotion execution report

Generated {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()} (Asia/Shanghai).
This report records actual completion and outstanding work; its filename does not certify success.
This is an in-progress checkpoint report while the requested continuation is still running.
It must be regenerated at actual closeout; an in-flight ledger row is not a completed call.

**Library: VERIARBOR_BLOCK_CORE_PARTIAL. Product: PRODUCT_NOT_READY.**
Pure policies are extracted and tested, and host core callsites delegate to the package.
The complete requested integration/product gates are not yet satisfied.

The user's Block/Port V1 request supersedes advanced search completion gates.
Core objects, directional compatibility, explicit rename/default adapters,
certificate substitution, one-hop impact policy and verification keys are implemented.
Default slot selection no longer imports the experimental Pareto/Bandit allocator.
Original Planner, DAGRunner, FileRunStore, GoalAcceptance, Budget/UNKNOWN and Corpus
remain the only authorities. Legacy textual contracts are opaque and exact;
they are not falsely advertised as structurally inferred schemas.

V1 evidence: 37 standalone library tests, 961 protocol/Agent checks, 138 runtime
checks, 46 focused projection checks and 74 novelty/provenance checks passed in their recorded scopes (overlap;
do not sum). The first new host run failed17/passed944 due to an empty-plan bug;
the identical command passed961 after the guard fix. Original failure is retained.
Initial real-state shadow:88 goals, zero verdict differences.
`BLOCK_V1_REAL_SUBSTITUTION_FA6720FA.json` records an actual M6 replacement followed
by reuse of M7-M10 original receipts with independent replacement evidence,
without re-executing those four milestone checks. This is scoped evidence,
not a claim of lower total Provider cost. Runtime terminal stale observers retire
without replay; unknown effects and stale producers still fail closed.

The recorded Provider gateway now requires deterministic request novelty before
dispatch; unchanged attempts/models alone are rejected. This does not prove
natural-language equivalence. An old escalation test expected a later rejection;
its updated test also directly verifies consumed grants cannot be reused.
The broad historical Provider suite remains FAIL (16 failures, 14 errors, 356
passes): missing archived fixtures, retired lifecycle assumptions, installed
plugin and streaming error expectations are retained outside the minimum V1 gate.
Its failure is not relabeled PASS; see OUT_OF_SCOPE_CHECK_FAILURES.json.

The M11 independent observer now adds valid-media publication/idempotency and
mutation/deletion before any explicit media.get. Six observer controls passed;
earlier publication variants failed this stronger check, and those failures remain.
The original publisher subsequently added live file hashing and its missing
import. Current c3d9f891 passes four local approval/publication negative cases.
An additional M11-scoped revision checks real browser media dispatch and visible
image/video bytes against imported hashes; its six real-browser observer controls
passed. These controls are not product acceptance. GUI completion is still required.
Authenticated requirement scope applies this revision only to M11, preserving
the previous checker identity for M1-M10. Scoped routing/provenance tests:24 PASS.
Initial two new fixture tests incorrectly mutated immutable bindings; their
failure is retained and the fixture now declares its registry before freezing.
Eight bounded-guidance/context tests passed: source-specific operational advice
expires after its bound artifact or goal receipt changes, while general task
requirements and original history remain intact. An initial wrong test-path
invocation exited before running tests; the corrected invocation is recorded.
Eight milestone-novelty/recorded-dispatch tests passed after an actual M12
declaration was incorrectly denied: declaration-specific public requirements
and dependency contracts now participate in novelty. Repeated declarations
with unchanged contracts and new attempt IDs remain denied. This host fix
does not change any product verdict or erase the failed continuation.
The library wheel is recorded under dist/block-port-v1/receipt.json; all packaged
source bytes match and isolated import passed. No package publication occurred.

M11 native140 passed the scoped media/backend and actual preview workflow.
Final main.py source650460ff exists, but an actual M12 browser probe found upload400,
duplicate creation on edit, and false empty project-state lists. Legacy native147
passed a narrower workflow and is not evidence that those gaps were fixed.
The M12-scoped qualified observer v6 adds actual upload/attachment/edit/approval
invalidation/scoped-state/foreign-media/restart checks; ten deterministic observer
controls passed, not ten product browser cases. Current scoped coverage is enforced
by23 focused tests: old PASS remains trusted history but cannot satisfy the required
new observer; old counterexamples and unrelated milestone certificates remain.
An initial wrong test filename caused exit4/no tests; corrected invocation passed.
Four current files' historical Worker origins were registered through the existing
ProvenanceGate import interface after later blocked attempts obscured authorship.
No product bytes, old receipts, Provider usage or acceptance verdicts were fabricated.
M12 generated tests initially passed4/failed2. The publication fixture uses a
nonexistent server.port attribute; isolated correction to server_port returns200
instead of500. The original test owner still must repair it without removing assertions.

Remaining V1 limitations: legacy DAG retry execution closures remain conservative; adapter
enum/wrapper/split/merge transforms are not implemented; actual product witnesses
for compatible/adaptable/breaking boundary changes remain outstanding. BLOCK_MAP
currently describes goal-boundary projections rather than every execution leaf. These
must not be confused with the completed synthetic compatibility cases.

M6 media loader was repaired by its original Provider owner. Local approval
negative cases pass; publication guard and GUI preview remain separate work.
An obsolete continuation instruction caused an unnecessary additional M6 loader
discovery change; that mistake and its extra calls remain recorded, not hidden.
The latest authenticated milestone table below takes precedence over all
historical baseline counts and over earlier-source substitution observations.

| Milestone | Current authenticated verdict |
| --- | --- |
{milestones}

Canonical hard verdict: {view['hard_verdict']}. Latest continuation: `{last.name}`.
Latest controller reason: `{blocker}`.

1. Startup cwd was `D:/VeriArbor`, the requested library root. No nested VB/VeriArbor repository was created.
2. Existing Git repository and MIT license were preserved. Origin: https://github.com/s1mplethings/VeriArbor.git; initial/current committed HEAD `{head}`. Changes remain uncommitted.
3. `F:/CGKN-LeanLoop-V1-20261101` and `F:/CGKN-ITER-132/production-core-convergence-v1` passed fresh read/write probes. Earlier permission denial remains recorded; it no longer blocks this work.
4. The package is independent: production imports are standard-library or local VeriArbor modules, with no CGKN/provider/runtime/database dependency. Direction is CGKN -> VeriArbor.
5. Integration is an editable installation in `D:/VeriArbor/.venv`. The frozen original Python process loads it through an explicit process-local bootstrap. No global installation or Python identity replacement occurred. A local wheel and SHA-256 identities are also retained.
6. No library implementation was copied into CGKN. Public compatibility imports/adapters replace extracted functions. Offline rollback snapshots are evidence, not a second live implementation.
7. Extracted policies include verification reduction, readiness/frontier/lineage, strategy normalization and repeated-no-progress detection, progress assessment, repair-progress projection, review classification, resource conflicts/batching and bounded slot allocation. `SYMBOL_EXTRACTION_MAP.json` identifies symbols/callers and dynamic-analysis limitations.
8. CGKN retains ProjectSession/Agent decisions, CapabilityTree/ExecutionDAG, executor admission/runtime, FileRunStore, provenance, GoalAcceptance authentication, Provider routing, budget ledger and Corpus. They depend on business/runtime state and are not duplicated in the library.
9. No second planner, state authority, execution runtime, ledger or Corpus was introduced. There are {len(switches)} source-change receipts, including later protocol-context fixes; these are not all distinct library authority migrations.
10. Shadow results: 323 finite synthetic comparisons plus 84 current goal rows, zero differences. This is scoped evidence, not a universal correctness proof.
11. `AUTHORITY_MAP_AFTER.json`, `ENTRYPOINT_MAP_AFTER.json`, `DELETION_RECEIPTS.jsonl` and byte-exact `rollback/` snapshots enumerate switched callsites, removed bodies, metrics and retained imports. The full rollback hash chain is verified without altering live history.
12. Obligation nodes are not pruned. Strategy pruning requires qualified counterevidence in the generic policy; no live product obligations were discarded.
13. 83 M1-M6 certificates were reconstructed from authenticated receipts, current artifact/checker versions and provenance. Two read-only rebuilds matched. Context exposes certificate identities; original GoalAcceptance remains the acceptance authority.
14. Exact-strategy repeated-no-progress matching is live. General learned nogood matching is library-tested, not claimed as complete host causal learning. No measured reduction in repeated calls is established; this run itself exposed and preserved repeated admission failures.
15. Non-chronological backtracking produces an earliest matching reversible-checkpoint recommendation. It does not automatically rewind state, and exact strategy identity is not a proof of causal minimality.
16. Active Crown is bounded in the library and rejects mandatory-obligation overflow. Complete live Trunk/Crown/Cold Archive context integration is not finished.
17. Conflict graphs control host admitted parallel batches. Same GUI writer conflicts are excluded. No throughput improvement is claimed for this single-writer product repair.
18. Default V1 slot allocation is deterministic. Historical Pareto/probe/UCB code remains optional/experimental and is not a V1 completion gate. The host still owns actual resource accounting.
19. Same-model review is SELF_CRITIQUE; unknown identity is UNQUALIFIED_REVIEW. Neither review grants independent acceptance. The temporary Qwen/Qwen route does not count as cross-family review.
20. M1-M6 baseline artifacts and witnesses were preserved and reused. Later M11 integration required original-owner M6/M7 source repairs; newly checked identical boundaries now allow dependent certificate reuse with authenticated replacement chains. A helper-only repair regressed M6 and remains recorded. Current verdicts above supersede baseline certificate counts. Historical witnesses retain their original matched artifacts/checkers; derived reuse explicitly records replacement proofs.
21. M7 and M8-M12 states are in the table above. DOGFOOD checkpoint: `{dogfood.get('status', 'NOT_EXECUTED')}`; canonical packaging: `{dogfood.get('canonical_packager_status', 'NOT_EXECUTED')}`; additional test counts: `{dogfood.get('additional_test_counts', {})}`. A runnable local preview does not grant public delivery approval. No qualifying final delivery is asserted by this report.
22. New accounted requests by model: `{json.dumps(models)}`; by state: `{json.dumps(states)}`. New Max calls: 0; new Pro calls: 0. Historical Pro/UNKNOWN usage remains in the unchanged original ledger prefix.
23. Known estimated-cost increment: {ledger['totals']['estimated_cost'] - before['totals']['estimated_cost']:.6f}, using original operator estimates input20/output60 per million. These are not verified current prices or settled invoices. Unknown usage/cost remains unknown, never zero.
24. No causal context-cost or repeated-call improvement is established. Protocol repair now preserves task semantics; tests are evidence of boundary behavior, not a production performance claim.
25. Host-authored product business patches: 0. All intended candidate changes remain Provider-owned bounded executor work. Host changes concern generic policy integration and protocol correctness.
26. Corpus final append/rebuild status must be read from a new migration archive receipt when present; old Corpus rebuilds do not prove this run's final archive. Existing canonical root is `F:/CGKN-ITER-060/project-corpus`.
27. No Git push, PyPI/package publication or real external promotion occurred. Temporary local test platforms are not public publishing.
28. The earlier permission failure stopped before source/Provider effects. Fresh P0 restarted successfully; this is not a read-only Phase A result. Remaining gaps are integration/product completion, not filesystem permissions.

Validation receipts are in `D:/VeriArbor/governance/checks`. Counts overlap and must not be summed.
Before Block/Port V1, the standalone library suite passed 21 tests and a protocol/Agent slice passed 954 tests
(`metadata-refresh-integration-regression`, including earlier owner/contract/write-policy regressions).
Metadata-only reads now use canonical reload instead of unused full verdict views; all actual
view/record authentication remains active. Initial overbroad test guards and their correction
are retained in metadata-refresh-qualification; corrected tests fail3/pass1 on original source
and pass4 on updated source. One read-only unchanged-subject refresh measured15.328s before
and0.687s after; this is not an end-to-end throughput or Provider cost improvement claim.
The isolated-Python UTF-8/test-evidence slice passed 33 tests after a preserved failed regression
and its hash-bound repair. Initial `-I` ignored PYTHONUTF8; explicit UTF-8 flags also required
fixing positional pytest detection to retain JUnit and owned temporary-directory evidence.
Other recorded host slices cover acceptance/recovery, scheduler, adapters and original-interpreter integration.
One exploratory broader test process was interrupted and is explicitly NOT_COMPLETED; no full-repository PASS is claimed.

Protected history inventory contains 158,247 selected files, with explicit scratch/cache/dependency exclusions.
Legitimate mutable run projections change during continuation; immutable old attempts, requests, failure receipts and ledger rows are preserved.
UNKNOWN recovery inspected bounded local effects and appended canonical NOT_APPLIED receipts; it never upgraded upstream cost or business acceptance.
One controller stop raced with dispatch and caused a new UNKNOWN; this mistake remains recorded.
Continuation29 also suffered a native Python312.dll access violation during the first new native
stack dump. Windows records and post-exit reconciliation retain the single settled planner call,
unchanged candidate and zero new UNKNOWNs. Causality is unproven; that instrumentation was removed.
Continuation30 correctly refused a consumed recovery revision before any new call. Continuation31
preserved bounded admission exhaustion; receipt20 fixes misleading missing-strategy-field feedback
while keeping task/evidence immutable and genuinely forbidden strategies rejected.
A broad recovery operation also temporarily changed five legacy orphan ledger rows. Their exact
before/after values were retained and the five rows were restored byte-for-value; subsequent
reconciliation is scoped to the owned process. Historical prefix equality above verifies the
current restored state, not a claim that those rows were never touched.
Read-only derived call correlations are in `governance/call-correlations`; their exact request
hashes link the original requests to the canonical ledger without creating another authority.
DOGFOOD receipts preserve both the initial packaging-test failure and the later canonical
packager result. The original independent M7 checker passed on the frozen snapshot; the
additional 118-test suite had 64 PASS and 54 FAIL. These failures were not silently discarded,
and final packaging remains blocked until they are resolved or properly qualified.
The first test runner lost decoded stdout/stderr through UnicodeDecodeError; original raw
streams were not captured. Its structured raw JUnit report survived. The later run retains
new output correctly and still reports 64/54; it is not reconstruction of the missing streams.

Evidence roots:
- `D:/VeriArbor/governance`, `REGRESSION.json`, `MIGRATION_RECEIPT.json`, `WORK_LOG.md`
- `F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor`
- `F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05/continuations`
'''
for path in (V / 'FINAL_REPORT.md', H / 'migration/veriarbor/FINAL_REPORT.md'):
    path.write_text(report, encoding='utf8')
print(json.dumps({'library':'VERIARBOR_BLOCK_CORE_PARTIAL','product':'PRODUCT_NOT_READY','latest_continuation':last.name,'models':models,'states':states,'report_sha256':hashlib.sha256(report.encode()).hexdigest()}))
