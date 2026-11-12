# VeriArbor

Python library for certified Block substitution, explicit Port and Effect
contracts, local verification and deterministic verification deduplication. Version
`0.1.0.dev0`; Python 3.11+. Production code uses only the standard library.

The host supplies authenticated, current evidence and retains its execution,
storage, acceptance and accounting authorities. A successful execution is not
proof of acceptance. Selection estimates cannot grant a VERIFIED verdict.

## Positioning

VeriArbor is a governance and capability-growth kernel, not another monolithic
coding agent. A replaceable Project Agent (OpenCode, Codex, a SuperAgent or the
embedded planner fallback) proposes project operations. VeriArbor decides
whether a proposal may enter the capability tree, whether it is executable,
which consumer must prove it, whether progress is real, and whether the result
may become reusable evidence. The design direction is revised; end-to-end
benefit still requires production evidence.

V1 centers on `Block`, `Port`, `Contract`, `EffectContract`, `Variant`,
`Certificate` and `Adapter`. Identical replacements need a newly certified
Block; compatible boundaries add edge checks; adapters require local composition;
breaking boundaries expand only one hop before being assessed again.

Legacy textual host contracts are opaque and exact. They are not inferred JSON
schemas. Unknown compatibility fails closed. The search, learning and global
graph modules remain optional compatibility/experimental APIs, not V1 readiness
gates. The host's default slot selection no longer imports the search allocator.

See `docs/PORT_COMPATIBILITY.md` and `docs/SUBSTITUTION.md` for limits. Library
tests and substitution proofs do not assert completion of Promotion Studio.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Public APIs and integration boundaries are described in `docs/PUBLIC_API.md`
and `docs/ARCHITECTURE.md`. Migration records are projections of existing
evidence, not replacement databases. No publication is implied by local tests.

See `MIGRATION_RECEIPT.json` and the host's `migration/veriarbor/` directory for
actual switch, shadow, rollback and regression evidence.
