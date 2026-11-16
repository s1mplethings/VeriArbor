# Architecture

## Project Agent boundary

VeriArbor does not attempt to be the strongest general-purpose planner. A
replaceable Project Agent supplies proposals; VeriArbor supplies admission,
contracts, effects, execution progress, evidence, acceptance, impact and
lifecycle. The boundary is:

```
Project Agent -> ProjectProposal -> Admission -> TreeEdit -> CapabilityTree
```

A Project Agent can propose an operation, a repair strategy and a resource
preference. It cannot mutate the authoritative tree, declare acceptance, or
mark an unimplemented node as a reusable capability. The embedded planner is a
fallback Project Agent and uses the same admission path.

A roadmap is not an active capability tree. Only the current frontier and its
obligations enter the authoritative tree; later capabilities are admitted when
new evidence activates them.

Dependency direction: CGKN -> thin conversion adapters -> VeriArbor. VeriArbor
never imports CGKN, Promotion, a provider, a concrete store, or experiment code.

V1 production policy centers on `block`, `port`, `contract`, `effects`, `variant`,
`certificate`, `adapter`, `compatibility`, `expansion`, `dedup` and `substitution`.
A leaf is a replaceable Block. Parent composition and execution remain in CGKN.
The replacement boundary is input + output + effects, not a module hash.
Verification proceeds Block -> Edge -> Local Composition; milestone slices
remain for new capability completion and final independent acceptance.
`impact.plan_impact` composes those policies into a change plan: affected
downstream consumers, changed input-side producer supply, explicit adapter
scope, one-hop breaking expansion and reuse decisions from host-authenticated
verification-key fingerprints. Structural `IDENTICAL` alone never authorizes
consumer reuse: the changed block must have a current authenticated PASS, the
host must prove the external context unchanged, and each reused consumer needs
its own scope proof covering the relevant behavior. It does not execute or
authenticate checks.

The following older APIs remain compatibility/optional experiments, not V1
completion gates. `model` carries generic serializable inputs. `graph` validates and reduces the
semantic obligation graph, including optional versus required children.
`verification` reduces qualified
evidence and computes readiness. `learning` normalizes strategy identities,
matches scoped nogoods, minimizes checker-reproducible conflicts and recommends
an earlier relevant checkpoint. `lifecycle` manages certificate validity and
bounded active projections. `search` estimates proof costs and selects probes.
`scheduling` builds resource conflicts and chooses independent batches. `review`
classifies actual model identities and evaluator controls. `protocols` defines
ports for host implementations.

There is no executor implementation, planner, scheduler runtime, project
database, accounting ledger or Corpus in this library. The host is responsible
for locks, durable transactions, path normalization, provider identity, actual
version checks, UNKNOWN reconciliation and external-effect approval.

The compatibility obligation reducer receives already-authenticated goal rows;
it preserves the previous host semantics. The richer `rollup` API requires
explicit integration, acceptance and declared handoff evidence. Merely moving
the compatibility reducer does not prove the host has supplied every possible
hierarchical check. Such claims must be backed by product acceptance.

Certificates are rebuilt from current acceptance, with original receipt and
provenance hashes. Their serialized projections are not authoritative state.
Active Crown never drops mandatory obligations to meet a context limit: the
host must expand the limit or apply backpressure. Cold Archive hydration checks
the supplied immutable hash before returning historical bytes.

V1 does not introduce a global semantic graph, clause store or search scheduler.
Default host slot allocation is deterministic admission order. Existing DAG
resource conflict checks still prevent overlapping writers and side effects.

Capability semantics and strategy reuse now add `capability` and `skills` pure
policy APIs. The host's existing Proposal Admission, ProjectSession, DAGRunner
and FileRunStore integrate five independent quality gates, scoped input evidence,
goal-linked proposals and lazy Skill reuse. Parent quality needs its own outcome
contract; historical ACCEPTED and reusable strategies grant no current Utility
PASS. See [Capability gates and skills](CAPABILITY_GATES_AND_SKILLS.md) for the
contract, lifecycle, project-isolation rules and migration boundary.


## Documents, context and agent handoff

| Boundary | Responsibility |
| --- | --- |
| Core | Pure admission, progress and evidence policy; frozen protocols, no document runtime |
| Host | Bind current state, prepare bounded context, enforce effects, persist receipts and resume |
| Project Agent | Choose decomposition, research, capability proposals and revisions |
| Worker | Implement the current leaf goal inside its admitted contract |
| Project | Independent goal, tree, authority, evidence and budget lineage |
| Contract | Formal interfaces, read/write scope, effects and execution constraints |
| Document | Human-readable intent, assumptions and design rationale; advisory only |
| Evidence | Version-bound observed facts authenticated by existing authority |

The goal-driven Host uses `GoalComposer.project_context` to project current
GoalAcceptance, leaf contracts and recent admitted DecisionRecords into existing
task feedback. Worker uses the same projection with its actual current leaf goal.
No handoff database is introduced. Reasons are public decision summaries, not
hidden chain-of-thought. Resume reads committed state and existing records;
old prompts and Markdown cannot overwrite the active leaf contract.

`ContextPacker.documents` selects explicitly declared workspace references with
role/task bindings, full/snippet/hash-bound summary/reference modes, file and
UTF-8 byte limits, path checks and omission reasons. Required formal inputs are
still verified and supplied through the existing Worker contract path. The
independent Checker receives its frozen definition, not this advisory context.
Final requests remain visible in existing provider-call records; source bytes,
selected document bytes and final system+user bytes are different measurements.
No token usage or cost is inferred from byte counts.

Goal-driven configuration may reuse an existing `project_document` (workspace
relative). Otherwise a derived PROJECT.md is placed under the existing
`inputs/runtime-results/project-<identity>/` projection area. This is readable
context, not a delivered artifact or a second truth store. `project_notes` holds
mutable assumptions/design notes; confirmed requirements remain formal config
and GoalAcceptance. Generated-document version conflicts are reported and the
changed text is not silently substituted for requirements. Free-form external
Markdown agreement is explicitly unverified; no semantic oracle is claimed.

Optional `context_documents` entries declare `path`, `roles` (`agent`, `worker`),
`task_refs` (node IDs), `mode`, optional `sha256`, `line_ranges` (inclusive,
one-based), and a hash-bound `summary`. Workers receive text only with an explicit
task binding. Selection defaults to four files / 12,000 material bytes, with a
1 MiB per-source read limit. Documents cannot grant file access, change effects,
remove requirements or replace the frozen Checker. Agent requests for further
public context continue through the existing scoped resolver and call budget.

Ordinary edits to the derived projection area do not change workspace identity.
A document deliberately bound as a formal input remains version-sensitive;
there is no blanket Markdown exemption. Internal algorithm replacement follows
ordinary Proposal / Admission / TreeEdit and existing invalidation. Significant
changes retain requirements and public reasons in existing decisions/reports;
no mandatory ADR, new Gate, Agent, runtime or registry is required.


Complete-project delivery is distinct from the goal-driven runtime projection.
The existing `SoftwareProjectGenerationService.run_profile` accepts
`delivery_kind: "project"`. Its operator-owned requirements must declare
PROJECT.md and AGENTS.md in existing `artifact_layout.support`; absent declarations
are rejected, not silently granted write scope. The original Agent/Worker path
produces these files as governed candidates. The original provenance check,
post-build finalizer, local packager and canonical manifest include their exact
bytes. The Host does not write unreceipted documentation into a verified product.
Profiles without this declaration retain their existing scope; single-file
outputs are not automatically expanded into repositories.

The Worker receives original intent, current formal requirements, source hashes
and run/contract references through the existing project-context hook, including
semantic worker packing. Declared public outcomes are not proof that a user
confirmed an inferred story. Existing/custom or externally modified project
documents are preserved: automatic resume requires the current bytes to match
an authenticated successful Worker result. Otherwise explicit adoption through
the existing source/revision authority is required; no inferred authorization.
The same-run requirement API adds requirements only. A replacement uses a new
authorized run/version and retains old evidence without inheriting old PASS.

A context document may be marked `required: true` with explicit dependent
`task_refs`. If its requested text is missing, stale, reference-only or over
budget, the context audit reports `missing_required`. GoalComposer rejects edits
to those tasks and LLMExecutor stops their dispatch before calling a Provider.
Unrelated work remains admissible. Existing hash-bound summaries can supply the
needed portion; formal read_subjects remain mandatory and separately verified.
The existing public resolver has no filesystem loader: an unserved required
file is a scoped missing prerequisite, never silently treated as supplied.
