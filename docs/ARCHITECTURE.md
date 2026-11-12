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
