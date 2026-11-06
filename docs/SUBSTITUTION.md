# Certified substitution

A Certificate binds Block and Variant identity, input/output/effect hashes,
acceptance IDs, artifact and checker hashes, original evidence, time and limits.
The library never authenticates external evidence or persists acceptance state.
The host must authenticate it using its existing authority on every reuse.

An identical boundary replacement requires a new independently verified
certificate covering the old acceptance IDs. The old certificate stays bound
to the old implementation. `substitution_cover` covers dependency artifact
changes only; own artifact changes, missing proof, effects changes or changed
checker identities cannot be carried across. New counterexamples dominate PASS.

CGKN uses its existing GoalAcceptance, immutable attempts and ProvenanceGate.
Derived views can attach `certified_substitutions` and `effective_subjects` to an
old checked result; its original `subjects`, receipt and observation remain
unchanged. Exact legacy contracts remain opaque. Simultaneous owner dependency
changes require local composition evidence. A new native independent check of
the complete owner and dependency subject set supplies that evidence; a derived
check cannot become a new replacement root. Certificate timestamps come from
the immutable original check's completion time.

VerificationKey includes the requested boundary fields plus artifact identities
and checker qualification identity. Current authenticated PASS/RUNNING is reused;
an unchanged FAIL cannot be re-executed. The compiler rejects duplicate current
independent measurement nodes. The original recorded Provider gateway also
requires a new variant, artifact, contract, evidence or checker qualification
before dispatch. Attempt IDs and model changes alone do not qualify. Verified
NOT_APPLIED reconciliation is new evidence while the original UNKNOWN remains
unchanged. This is deterministic structured-request normalization, not proof of
natural-language equivalence.

ProgressiveBoundaryExpansion computes only the current one-hop bubble. Stable
boundaries stop expansion; each further hop requires an explicit BREAKING result.
No second scheduler, test tree, state store or planner is introduced. Runtime
UNKNOWN protections and independent final acceptance remain active.

Current runtime limitation: historical DAG retry closures still conservatively
invalidate execution dependencies. Terminal stale observers are retired without
replay; the certificate layer prevents unrelated milestone evidence from being
discarded solely for a certified dependency replacement. Further runtime scope
reduction must not bypass raw-data dependency or unknown-effect protections.
