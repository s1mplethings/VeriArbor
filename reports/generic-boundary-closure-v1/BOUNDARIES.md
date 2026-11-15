# Generic boundary audit — qualification remains open

Authority: `contract.json`, task `VERIARBOR_GENERIC_BOUNDARY_CLOSURE_V1`.
The explicit scope amendment replaces the previous ACFV completion conditions.
This inventory records inspected paths; it is not a claim of exhaustive entry coverage.

| Entry | Existing owner and path | Evidence / remaining issue |
| --- | --- | --- |
| `scripts/run_goal_driven.py` / `application.goal_driven.build_session` | ProjectSession → HostPlanningScope / Admission → ExecutionAuthority → DAGRunner → independent GoalAcceptance | `test_generic_gateway_chain.py`: domain-neutral execution, failed exact-byte observation, explicit repair, budget accounting, fresh Session resume without another call. Actual wire terminates at a loopback fixture. |
| `scripts/run_mvp_runtime.py` | Operator-declared local tree → explicit AdmissionPolicy → `admit_declared_tree` → existing authority → DAGRunner | File and local-action file writes stage candidates and publish only after independent checker success. Actual CLI execution and resume recorded in `local-demo/evidence.json`. Command/test executors retain their existing subprocess effect path. |
| `scripts/run_self_growth_v0.py` | Explicit local parse capability Admission → existing DAGRunner and registry | Public CLI regression proves parsed-object checking and second-run capability reuse, without Provider calls or kernel self-modification. |
| Agent / Worker Gateway requests | RecordedCompletionClient → GatewayCompletionClient → ContextPacker → concrete wire preflight → effect authority → existing Provider ledger | Default packing and final-wire checks remain active. Cache hits now carry packing receipts with `provider_dispatched=false`; exact cache reuse does not create a request. Agent/Worker are the two currently accepted ModelRoleConfig roles. |
| Protocol correction / semantic exchange | Existing exchange, ContextPacker, ContextReferenceResolver and executor effect authority | Migrated isolated executor tests use actual Admission/Permit scopes; schema/admission correction, input identity and usage assertions remain unchanged. No test helper grants artifact publication. |
| DAG resume / dependency inputs | Existing authority validates committed packet; existing successor-chain proof validates immutable attempts, publication journals, candidates, raw receipts and historical Host commits | Current-artifact validation still rejects stale execution epochs. Historical publication authentication is used only inside the complete causal-chain proof. Tampered versions and unrelated sibling writes remain rejected. |
| Legacy client, ArtifactModuleRunner, old Agent MVP and other Session adapters | Existing code rejects missing legacy permission, unmanaged trees or missing explicit admission policy | Full audit retains these failures. Their caller migration and complete compatibility classification are unfinished. No fallback or blanket permission was introduced. |
| Installed plugin / dynamic registration / standalone scripts | Candidate inventory from the preceding audit is retained as a lead only | Exhaustive registration, import constraints and mutation coverage remain unfinished; C02/C08 receive no PASS. |

ACFV / CharacterCut are excluded. Their three inherited adapter/documentation/test
differences are preserved byte-for-byte and listed separately in
`preserved-product-differences.json`. They are not generic completion evidence.

Open cross-cutting items include complete formal entry assembly, all-role dynamic
context acquisition beyond lossless folding, remaining historical fixture
migration, complete artifact-consumer coverage, and a trusted deduplicated reward
view over the existing evidence owners. No alternate planner, scheduler, graph,
state authority, runtime Gate or reward database was added.


Code-only entry changes (2026-11-12; not executed or qualified):

| Entry | Delegation in source | Qualification |
| --- | --- | --- |
| `run_goal_driven.py export-component` | `ComponentPackages.export` → current `ExecutionAuthority.validate_receipt` per artifact → Core `Block`/`Variant` portable envelope → existing FileRunStore immutable packet | Not run |
| `run_goal_driven.py import-component` | `ComponentPackages.import_candidate` → exact content/dependency/applicability checks → candidate files in FileRunStore; no promotion or execution | Not run |
| GoalComposer portable candidate catalog / `local.component@1` | content-bound dependency closure → current Port/Effects adapter → normal leaf admission → CommandExecutor → existing effect authority, candidate checker and publication/receipt chain | Wired in source; not run. v1 source-only; explicit v2 Python JSON stdio invocation required |
| Worker `run_tests` | LLMExecutor candidate → existing PythonTestExecutor → existing subprocess effect scope; observations return to same delegation; independent acceptance remains separate | Not run; no OS sandbox claim |
| Goal-driven Skill loading and `skill_trial` | operator-declared source authorities → existing SkillRegistry/SkillMatcher → current dependencies and strategy identity → common GoalComposer compiler / TreeEdit admission → strategy-bound Permit | Wired in source; not run. Trial grants no qualification |
| `run_goal_driven.py register-skill / export-skill / import-skill / requalify-skill` | existing session writer lock → GovernedSkillLifecycle → current receipt authority and existing SkillRegistry/promotion_check → recorded lineage; import enters NEEDS_REVALIDATION | Wired in source; not run. Requalification requires target-project receipts, not source PASS |


2026-11-12 bounded follow-up (supersedes only the selected Not run statements above):

| Existing entry | Delegation / selected evidence |
| --- | --- |
| GoalComposer public protocol | executor_interfaces → prompt/schema/compiler; direct decide prepares the same public context. Offline actual-request capture passed. |
| local.component@1 planned implementation and Port bindings | declared Worker dependency → existing DAG readiness → current authority receipt/publication identity → ComponentPackages → CommandExecutor. Offline registration, consumption, semantic rejection, explicit scale adaptation and export/import passed; no inherited PASS. |
| Worker delegation | existing LLMExecutor, bounded file actions and PythonTestExecutor; request/context clock shares delegation deadline. Offline failed self-test → repair → passed self-test, empty internal file, retained input and protected path checks passed. |
| import-skill explicit unverified candidate | existing lifecycle integrity checks → SkillRegistry origin provenance → NEEDS_REVALIDATION; target receipt promotion unchanged. Offline explicit import and target-project receipt qualification checks passed. |
| Existing archive/restore | ExecutionAuthority archive validation → existing DAGRunState history; selected same-store restore and mandatory-goal protection checks passed. |

Evidence: reports/runlens-refactor-20261112/interface-small/results.json and referenced
JUnit files (12 unique scenarios; only affected cases rerun). No exhaustive boundary
qualification, actual model autonomy, full regression or OS sandbox claim is added.


2026-11-13 source-only registration: `goal_driven.build_session` accepts optional
`work_strategy` / `project_evolution` via `application.project_strategy`; this is
context preparation for the existing GoalComposer, not a new execution entry.
Proposals delegate to unchanged admission/Tree/DAGRunner and receipt authority.
Skill loading is on demand; qualification counts are explicit project policy,
with existing receipt/applicability authority retained. Portable implementation
sources may be any declared writing-contract producer; consumption still verifies
current committed artifacts. Static-only this round; prepared coverage and exact
migration notes are in `reports/runlens-refactor-20261112/REPORT.md`.


2026-11-14 opt-in continuation (partial qualification):

| Entry | Authority delegation | Evidence / limit |
| --- | --- | --- |
| `ProjectSession.run(campaign={campaign_id,budget_authority_ref})` | same session writer lock → CampaignJournal in FileRunStore → existing HostPlanningScope → common RecordedCompletionClient → existing Admission/DAGRunner/Worker/GoalAcceptance | `tests/project_agent/test_campaign_continuation.py`; finite decision-run segments share explicitly named execution lineage; no copied receipts, no new execution runtime. Full cross-execution-run successor migration and product E2E remain unqualified. |

Campaign completion forbids the `finish_when_verified` controller shortcut. Terminal
reuse delegates to existing DAG dependency/receipt verification. A decision bound
is distinct from Provider budget exhaustion; live Gateway campaigns bind the
configured ledger and limits, without resetting them.

2026-11-14 Phase 2 successor implementation (supersedes the fixed-execution-run
limit above; final qualification remains evidence-dependent):

| Formal entry | Existing authority delegation | Regression coverage |
| --- | --- | --- |
| Campaign continuation / legacy adoption | Session writer lock → immutable succession references → fresh run-scoped ExecutionAuthority Admission → existing DAGRunner | `test_campaign_continuation.py`: three distinct execution runs, predecessor receipt ownership, sealed authority, safe/unsafe adoption and process recovery |
| Agent Work Item | factual contract/Port/effect resolution → existing GoalComposer TreeEdit → LLMExecutor → independent Checker and GoalAcceptance | `test_campaign_work.py`: REUSE, COMPOSE, BUILD, Worker failure and return Observation |
| Strategy / experiment / candidate selection | Core canonical schema contract → immutable FileRunStore binding → existing Worker/Checker receipts → explicit Agent PROMOTE or ROLLBACK | Core `test_strategy.py`; Host experiment and selection controls |
| STOP / COMPLETE | explicit Agent decision → independent closed-effect/same-campaign Observation check or existing Final Checker | active-permit, stale-observation, original-goal protection and finalization rejection controls |
| Cross-run artifact consumers | exact old attempt, authority checkpoint and full publication-journal references → original receipt authority | cross-run writer chain and tamper rejection; no copied permit or receipt |

Operator effect/budget, configured behavior and Checker identities are immutable
for a Campaign. Budget context projects the existing Provider ledger, including
UNKNOWN reservations; successors cannot issue new budget authorization. Details:
`reports/long-horizon/20261114-closure/DESIGN/phase2-boundary-entries.md`.
The final complete profile and source identity in that closure report determine
qualification; this registration alone grants none.

2026-11-15 Context adaptation (qualification in reports/context-adaptation):

| Existing entry | Delegation |
| --- | --- |
| ProjectSession.run continuation_feedback.context_adaptation | Existing session writer lock → CampaignJournal.prepare_adaptation → Core ContextDescriptor; verified FileRunStore references and existing receipt authority |
| Campaign Agent context / decision_audit.context_adaptation | Stateless bounded diff/routing/shortlist → original Project Agent through unchanged HostPlanningScope and common request packing; audit is advisory |
| WORK_ITEM research metadata | Existing work resolution, contract/Port/effect admission and Worker; fresh exact-question/context/source evidence can resolve without dispatch; original goal acceptance is not waived |
| STRATEGY portfolio / PROMOTE and ROLLBACK context_scope | Same strategy declarations, experiment results and independent receipt validation; scoped preferences in existing campaign state, default preserved |
| Contextual performance outcome | Existing verified experiment Worker and Checker results → immutable evidence references in FileRunStore; no new promotion authority |

No new runtime entry, store, registry, scheduler, model role or paid authorization.

Context adaptation materials are hash-verified FileRunStore references projected
into the existing `retrieved_knowledge.public_artifacts` snapshot. GoalComposer
preserves this catalog; existing public_context_view / ContextReferenceResolver
inline small material or serve explicit bounded fetches through the same request
preparation. Tests assert actual Agent requests contain history and brief content,
and deferred fetch preserves exact values. Consumer routing remains reference-only.

2026-11-15 Project evidence / preference integration (qualification tracked in
reports/project-evidence-preference; source registration is not a PASS claim):

| Formal entry | Delegation and proof |
| --- | --- |
| FileRunStore project records / project metadata archive and restore | Same path containment, immutable_json, atomic_json and OS locks; project-scoped hash-linked records; restore preserves same-project lineage and never grants missing execution receipt validity |
| ProjectSession continuation_feedback.project_evidence / decision_audit.project_evidence | Existing session lock, original Agent/HostPlanningScope and shared request preparation; bounded Goal-linked metadata, scoped pending observations, idempotent acknowledgement; no alternate planner |
| Existing WORK_ITEM / Experiment / Outcome | Evidence specs are bounded Host-verified input snapshots; relevant preference refs bind existing experiment input identity and contextual route identity; original Worker/Checker/receipt and promotion checks remain mandatory |
| Local GET /projects/{project_id}/preferences and /state | Fixed schema renderer and evidence projection; authenticated project token for data, no execution-run lifetime or private provider context |
| Local POST /projects/{project_id}/preferences/evidence | Project-bound server authority → declared-field validation → serialized FileRunStore immutable human evidence and supersession; no strategy mutation |
| Local POST /projects/{project_id}/preferences/reevaluate | Durable pending observation → optionally Host-bound existing Session callback; same-request completion prevents duplicate callback; UI cannot select or promote |
| python -m cgkn.application.preference_surface | Loopback-only stdlib adapter, operator-provided access token, Windows exclusive port binding; no second database/backend ownership or runtime engine |

Proof matrix: tests/project_agent/test_project_evidence_preference.py includes
actual browser polling/refresh/XSS, cross-project access rejection, interrupted
pointer commit, two real governed E2Es with process exit after human submission,
original Session restart through the UI callback, original receipt-bound proxy
calibration, and objective-check failure despite HIGH preference. Weak/misaligned
proxies cannot become blocking evidence; preferences never mint VERIFIED receipts.
