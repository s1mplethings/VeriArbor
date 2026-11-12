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
