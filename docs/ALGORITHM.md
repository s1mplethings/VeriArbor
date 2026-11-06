# Algorithms and limits

AND requires every declared child plus parent acceptance, integration and
handoffs. OR requires a verified alternative plus its composite checks. Missing,
stale or unqualified evidence cannot establish VERIFIED. Current failed evidence
takes precedence for an AND obligation. Execution SUCCEEDED is not VERIFIED.

Dependency readiness checks the full verified ancestor chain, blocked resources,
unknown references and cycles. A cached verified intermediate node cannot hide
an invalid ancestor. Unrelated verified siblings remain valid.

Proof cost: AND sums child proof costs plus integration and takes the minimum
disproof cost; OR takes the minimum proof cost and sums disproof costs. A proved
node is (0, infinity), a disproved strategy (infinity, 0). Empty unproven sets
remain unknown. These are estimates only.

Pareto comparison maximizes acceptance gain and evidence novelty, minimizes cost,
regression risk, side-effect risk and uncertainty. Hard eligibility gates precede
comparison. Allocation favors bounded low-sample probes, then UCB after the
minimum sample count. Hosts define resource units and must supply calibrated
costs. The current CGKN adapter allocates executor slots; this is not a claim
that every token/model-tier policy has migrated.

Resource conflict uses read/write, write/write, shared effects and contract
mutation. Parallelism requires explicit opt-in. Greedy selection uses descending
weight and stable identity tie-breaking, excludes conflicts with running work,
and honors slots/class limits. It is deterministic, not an optimal maximum
independent-set solver. Hosts canonicalize aliases and directory-level scopes.

Nogoods require qualified counterexamples, matching scope, strategy family,
conditions, versions and freshness. An invalid evaluator cannot teach one.
Conflict minimization is deterministic deletion minimization (1-minimal, not
necessarily globally smallest). Backtracking returns the earliest checkpoint
that introduced a conflict assumption; it performs no rollback itself. The host
adapter currently uses exact failed strategy identities, not inferred causal
claims about natural-language assumptions.

Same actual model is SELF_CRITIQUE. Unknown model identity is unqualified.
Cross-model review does not grant independent business acceptance. Evaluator
qualification binds contract, object, checker, collection and positive/negative
controls; the legacy API additionally requires mutation evidence when applicable.
