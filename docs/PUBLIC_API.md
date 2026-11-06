# Public API (experimental)

All APIs are experimental in 0.1.0.dev0. No public object contains a fixed local
workspace path. JSON-compatible dictionaries and immutable references are the
exchange format. `stable_hash` uses sorted compact UTF-8 JSON, rejects NaN, and
also accepts bytes directly.

| Module | API | Caller obligation |
|---|---|---|
| model | Node, NodeKind, Status, Evidence, Event, Receipt, stable_hash | Authenticate evidence outside the library; declare required handoff IDs on nodes |
| graph | validate_graph, evaluate_graph | Frozen semantic edges, explicit checks; no execution topology ownership |
| verification | rollup, VerificationRollup | Explicit frozen handoffs, integration and current versions |
| verification | reduce_obligations | Compatibility-only trusted observation projection |
| verification | ready_frontier, verified_lineage | Unique IDs and admitted dependency edges |
| lifecycle | CapabilityCertificate | Recheck object/checker versions and revocations |
| lifecycle | BranchVitality, vitality, active_crown | Never remove required obligations |
| lifecycle | hydrate_archive | Access-checked host archive reader |
| learning | strategy_fingerprint, repeated_no_progress | Mechanism dimensions and actual evidence hashes |
| learning | LearnedNogood, minimize_conflict, backtrack | Qualified checker and bound decision checkpoints |
| learning | ProgressGuidedBacktracking, repair_progress | Actual observations; advice is not mutation |
| search | ProofCost, proof_cost, Candidate, pareto, allocate | Calibrated bounds; no acceptance inference |
| scheduling | ResourceClaim, conflicts, conflict_graph, parallel_batch | Canonical resource identities; existing runtime dispatches |
| review | ReviewKind, review_kind, evaluator_disposition, qualify_evaluator, review_needed | Actual model identity and control receipts |
| impact | plan_impact, ImpactPlan, ImpactedNode | Current Block/Port boundaries, explicit adapters, authenticated observations/key fingerprints, input producers |
| protocols | Archive, EvidenceStore, Acceptance, Executor, EventSink | Concrete implementations remain host-owned |

Dataclass certificates serialize with `as_dict()` and reconstruct with the
constructor. Graph/status enums serialize as strings. Proof estimates containing
infinity are calculation values; hosts must encode them explicitly when writing
strict JSON. They must not be passed to stable_hash as non-finite JSON numbers.
