# Capability gates and reusable skills

The Project Agent remains the planning authority. A project owns its own
CapabilityTree, TreeVersion, evidence, acceptance, UNKNOWN reconciliation and
budget. A shared SkillRegistry shares strategies, never project PASS or state.

## Contracts and admission

`veriarbor.capability.CapabilityContract` declares semantic intent, input/output
signatures, parent goal, forbidden implementation capability IDs, acceptance
metrics, invariants, positive/negative controls, failure conditions and evidence
requirements. Metrics support `>=`, `<=`, `==` with finite numeric or boolean
values. There is no universal capability score.

The existing host `ProjectProposal` carries `target_capability_id`,
`target_gap_id`, `strategy_capabilities` and optional exploration fields. Host
Admission resolves implementation IDs from the catalog as well as the proposal;
a claim of satisfying speaker attribution cannot hide a registered vocabulary
correction implementation. No natural-language classifier is involved.

In a governed project, AdmissionPolicy holds the project ID, frozen contracts,
known gaps and input evidence bindings. Admission rejects unknown contracts,
unmeasurable critical capabilities, non-falsifiable definitions, forbidden
substitutes, absent goal links, inadmissible evidence and blocked budgets before
the existing leaf/effect/tree checks. Threshold metrics and negative controls
are themselves falsifiable; otherwise declare explicit failure conditions.

An OPEN GoalGap must explicitly list the proposal's target capability ID.
Merely naming an unrelated gap is insufficient. Exploration instead needs a
reason, finite positive budget and a measurable result. Actual budget reservation
and execution limits remain the host's existing responsibility. Gap priority is
normalized directional shortfall × root impact × evidence confidence × severity;
UNKNOWN measurements are not fabricated as zero. This is advisory ordering for
the Project Agent, not a second planner.

Legacy admission callers with no capability policy retain the prior structural
path. New/critical projects enable `require_capability_contract=True` and supply
contracts and gaps. Claiming a target capability activates the semantic check
even if the legacy policy flag was omitted. Existing projects must explicitly
register their contracts; this change does not invent business acceptance rules.

## Independent stages and evidence

CapabilityGateState stores implemented, execution, semantic, utility and
generalization status separately. Each is PASS, FAIL, UNKNOWN, NOT_TESTED or
BLOCKED. A successful artifact scan or execution establishes at most G0/G1.
Legacy ACCEPTED loads with `legacy_imported=True` and no inferred quality PASS.

`evaluate_capability` evaluates current host-qualified Observation receipts.
Every receipt must bind PROJECT, CAPABILITY, object versions, checker versions,
evidence refs and the current capability contract hash. A failed declared
negative control fails semantics. A worsening human ranking delta can produce
G0/G1/G2 PASS and G3 FAIL. A parent needs its own contract and own outcome
observations: there is no child-execution-to-parent-utility reduction.
Generalization additionally requires the contract's frozen context bindings.
Missing tests remain NOT_TESTED; unqualified/stale/mismatched receipts become
UNKNOWN. A passing upper-stage test with an unpassed prerequisite is BLOCKED.

Evidence extends the existing receipt type with source_type, confidence,
scope, usable_for, forbidden_for, producer, producer_version and context.
Scope uses generic key/value identities, including PROJECT, CAPABILITY, CREATOR,
STREAM, DATASET and HELDOUT. These are project-independent vocabulary, not ACFV
types. Explicit denial wins over an allow-list. Required metadata/scope and
context must match before use; `required_context_hash` binds `context.artifact_hash`.

Port has an optional evidence_policy and `validate_evidence`. Policy changes are
breaking boundaries unless explicitly adapted; an empty policy preserves the
historical Port fingerprint. Existing Evidence constructors remain compatible.
Missing evidence for an explicitly required binding is rejected.

The library cannot authenticate a receipt, inspect an arbitrary executor's hidden
file reads or establish that a claimed metric is truthful. The host supplies
qualified measurements and immutable actual-input bindings. Worker outputs and
Agent config are never promoted directly to capability-quality PASS. Enforcement
applies to declared bindings; callers must register every sensitive input.

## Host integration and closure

The migrated host is `F:/CGKN-LeanLoop-V1-20261101`, as recorded by the existing
VeriArbor migration tools. Its thin capability_adapter stores a project/run
projection in the existing FileRunStore (`capability_governance.json`) using its
writer locks and atomic replacement. It does not introduce another database,
tree, scheduler or run authority.

Runtime phases are PROPOSED, ADMITTED, EXECUTING, EXECUTED and GATED. The existing
Proposal and node events provide admission/execution history. `record_phase`
provides the current phase. Runner dispatch and cached reuse both check evidence
bindings. Re-execution clears previous quality gates for the node, dependent
consumers and structural ancestors. Execution commits only technical status.

The acceptance authority calls `record_acceptance` with authenticated
observations and current versions. It writes gates and closes matching
ResourceDecision and FailureRepairTrace rows in one atomic snapshot. Resource
rows receive acceptance_result, utility_result and failure_attribution; repairs
receive artifact_after, acceptance_delta and final_result. Missing deltas stay
null, never invented. Existing append-only repair event history is retained.
The adapter's `record_feedback` records stable-ID pending rows; `bind_inputs`
freezes consumer requirements. Rebinding a frozen requirement is rejected.

ProjectSession's finish gate requires every registered critical contract's own
semantic and utility PASS, including parent contracts. Normal GoalAcceptance
checks remain in force. The session exposes contracts, gate summaries and ranked
gaps to dynamic planning; capability claims travel through the existing public
decision_audit schema. No direct artifact-to-ACCEPTED path was found in this
library/host mainline.

## Skill lifecycle

Skill != Capability: a capability defines what must be accomplished.
Skill != Block: a Block provides the concrete executable boundary.
Skill != Project Tree: a skill is a reusable strategy; the tree decides when it
is appropriate and continues exploring unknown work.

SkillManifest is the machine-readable truth (`skill.json`). It records scope,
status, signatures, triggers/preconditions, strategy steps, Block/Port/Capability
references, acceptance refs, known failures, dependency versions/hashes, source
branch and evidence references, and optional historical resource metrics.
Unknown token/call/time values are null, not zero. The companion SKILL.md is a
short deterministic operational rendering with name/description front matter.

SkillCandidateGenerator requires qualified semantic + utility PASS, compatible
interfaces and at least two distinct run receipts/evidence sets by default. It
always emits CANDIDATE. A single success, duplicate receipt or mere implementation
and execution cannot promote a strategy. Changing strategy/dependencies changes
its strategy hash, so old validation receipts cannot promote the new strategy.

Status lifecycle: EXPERIMENTAL → CANDIDATE → VERIFIED; changed dependencies cause
NEEDS_REVALIDATION; DEPRECATED is excluded from automatic matching. Registering or
updating to VERIFIED needs matching host-qualified validation receipts, not a
manifest self-claim. PROJECT skills can only match their originating project.
SHARED skills have no project binding/private assumptions and additionally need
G4 PASS and at least two independent context identities with compatible interfaces.
Source evidence is referenced, never copied as another project's acceptance.
This is a simple promotion gate, not proof that arbitrary private assumptions
have been semantically detected.

## Matching, invalidation and cost

SkillMatcher uses task family, capability, exact input/output signatures,
preconditions, project scope, VERIFIED status and dependency snapshots. It reads
short registry metadata first and loads at most MAX_SKILL_LOAD=3 manifests and
bodies. Automatic matching never loads NEEDS_REVALIDATION as VERIFIED.
Explicit `invalidate` accepts a full dependency snapshot; matching invalidates
only applicable skills so a partial task snapshot cannot invalidate unrelated
projects' strategies. Registry writes use atomic files; the embedding host must
serialize registry writers (single coordinator or its existing lock).

ProjectSession can receive a SkillMatcher and host-selected task specification.
A compatible skill becomes existing TreeEdits/AgentDecision and traverses the
same capability/leaf/Port/effect/budget checks and DAGRunner. It creates no fresh
PASS. No compatible strategy falls back to the existing composer. A strategy
whose add-node IDs already exist also falls back rather than repeatedly applying
the same branch. Instantiation uses explicit node IDs from a bounded strategy;
parameterized template expansion is outside this iteration.

The default Agent context contains only short index rows, not all SKILL.md
bodies. The intended savings come from avoiding repeated planning and loading
only matching strategies. `tools/verify_capability_consolidation.py` reports a
20-skill synthetic context-size comparison, including index cost. Its token
estimates are characters/4, not tokenizer measurements or production savings.
Real provider cost, wall-clock improvement and cross-project effectiveness remain
to be measured in future authorized production work.

## Offline verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tools/verify_capability_consolidation.py
```

The latter runs bounded host tests and the host product-direction gate, then
reproduces four known old scheduler/worker-test mismatches against the original
committed library in a temporary directory, disabling the newly inserted adapter
hooks only in that baseline subprocess. It preserves the real nonzero test exit code;
see the report for baseline comparison. It never resets source, runs video,
downloads media or invokes a Provider. The Anny fixture contains illustrative
numbers for the user-reported regression pattern, not production measurements.
