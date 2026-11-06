# Architecture

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
verification-key fingerprints. It does not execute or authenticate checks.

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
