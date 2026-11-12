# VERIARBOR_CORE_GOVERNANCE_V1

Status: **FEATURE FROZEN — BUGFIX / WIRING ONLY** (2026-11-10).

Completion evidence: [completion report](../reports/core-governance-completion-v1/VERIARBOR_CORE_GOVERNANCE_V1_REPORT.md).
The offline qualification contains 250 passing tests, no skips, and a separate three-node governed records project. No real Provider was called.

Frozen protocol roles and semantics:

- CapabilityTree and Project Agent architecture.
- DAGRunner scheduling and one-frontier growth semantics.
- Five-layer Gates; no sixth Gate.
- ExecutionAuthority / Permit / Receipt protocol.
- ClaimEvidenceRelation base protocol.
- EvidenceDerivation and independence protocol.
- EvaluationScope base protocol.
- Resource closure and repair lineage protocol.
- Skill lifecycle protocol.
- Explicit LEGACY policy.
- Authority integrity protocol.

Allowed subsequent work: bug fixes, wiring fixes, backward-compatible public API ergonomics, and project-specific contracts/checkers. A protocol redesign requires concrete production evidence of a protocol defect.

The guarantee applies to declared governed inputs, registered checkers, standard Host effect adapters and receipt-qualified state. It is not an OS sandbox, an automatic semantic oracle, a statistical correction system, or a substitute for business algorithms. No existing business project was automatically migrated.
