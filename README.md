# VeriArbor

**Growing reusable capabilities around real project goals.**

[中文完整项目简介](docs/PROJECT_OVERVIEW_ZH.md) ·
[Architecture](docs/ARCHITECTURE.md) ·
[Experimental API](docs/PUBLIC_API.md)

VeriArbor is a research project exploring an agent system that develops
capabilities as a project evolves. Its goal is to identify missing capabilities,
construct and compose executable components, assign work to suitable models and
tools across providers, and use actual acceptance results to guide repair,
reuse, and future decisions.

VeriArbor 探索让系统能力随真实项目持续生长：围绕目标构筑、组合、替换和复用能力，
为不同工作选择合适且完整成本合理的模型与工具，并用实际验收约束执行方向。

**Research Preview / Alpha.** The current public package is the pure Python
policy foundation for this direction: certified Block substitution, explicit
Port/Effect contracts, local verification policy, and deterministic verification
deduplication. It is not the complete autonomous project runtime. Full capability
growth and production-driven model selection remain research and integration
goals, not demonstrated end-to-end benefits of this release.

This preview also includes **Promotion Studio**, a standalone local GUI and
Bluesky text adapter. It is not production-ready and is not a formally
signed/trust-anchored delivery.

- Download: <https://github.com/s1mplethings/VeriArbor/releases>
- First-batch goals: [docs/FIRST_BATCH_PLATFORM_GOALS.md](docs/FIRST_BATCH_PLATFORM_GOALS.md)
- Promotion Studio: [apps/promotion_studio/README.md](apps/promotion_studio/README.md)
- Known failures: [docs/KNOWN_FAILURES.md](docs/KNOWN_FAILURES.md)

## Project direction

The long-term goal connects three parts of the same project lifecycle:

| Direction | Intended behavior |
|---|---|
| Capability growth | Discover gaps, construct or compose capabilities, and replace, prune, or reuse them as requirements change. Growth is measured by useful capability, not by node count. |
| Task-aware model selection | Choose models or existing tools using task requirements, language, model version, uncertainty, and the full cost of acceptable delivery, including verification and repair. |
| Evidence-guided correction | Use producer-consumer checks and independent acceptance to detect drift, identify affected work, and preserve only results whose evidence remains applicable. |

The capability tree expresses goals and decomposition. Execution dependencies
may form a DAG, and shared capabilities can serve several branches. The design
centers on replaceable leaf Blocks with explicit inputs, outputs, and effects;
a stable interface shape alone does not establish unchanged behavior.

Each real production task should primarily produce a useful deliverable. Normal
validation, bounded repair, and recovery remain part of that task. Learning from
production must retain failed attempts and uncertainty; observing one model
does not establish how an unselected model would have performed.

The intended optimization target is total acceptable-delivery cost. Cross-model
agreement is a review signal, not a substitute for business acceptance. Useful
capabilities should accumulate without allowing unnecessary branches, stale
evidence, or repeated model calls to accumulate with them.

For the complete motivation, lifecycle, examples, current implementation boundary,
and research roadmap, read the
[Chinese project overview](docs/PROJECT_OVERVIEW_ZH.md).

## What is in this preview

- `src/veriarbor/` — the pure policy library, standard library only.
- `tests/` — library unit, property, and integration tests.
- `apps/promotion_studio/` — the current M12 application, standalone and
  independent of the VeriArbor library and the private host repository.
- `docs/` — architecture, API limits, platform goals, and known failures.

The application does **not** import `veriarbor` and does not require the private
host repository. It uses Python's standard library at runtime.

The policy library does not execute or authenticate checks. The host remains
responsible for planning, execution, durable state, provider calls, accounting,
and external effects. See [Architecture](docs/ARCHITECTURE.md) and
[Certified substitution](docs/SUBSTITUTION.md) for these boundaries.

## Quick start: library

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Python 3.11+ is required. A clean install uses only the standard library at
runtime.

## Quick start: Promotion Studio

```powershell
cd apps\promotion_studio
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\start.ps1
```

Then open <http://127.0.0.1:8080/>. The GUI binds to loopback by default and
uses an independent local data directory.

For the local simulated publishing platform, scheduler worker, Bluesky
configuration, and safety defaults, see
[apps/promotion_studio/README.md](apps/promotion_studio/README.md).

## Status and boundaries

- The current public VeriArbor package is a pure policy library. Host scheduling
  remains **SHADOW_ONLY**; no production retest-reduction claim is made.
- Promotion Studio inherits M12 and adds local scheduler reliability and a
  Bluesky **offline-tested** text adapter. Bluesky live posting is not verified.
- Reddit and YouTube are first-batch manual experiment plans, not implemented
  automatic integrations.
- P11 formal trust anchor and independent signing are not deployed. The
  security hold remains in place.
- Known M10 Analytics fixture failures are documented in
  [docs/KNOWN_FAILURES.md](docs/KNOWN_FAILURES.md).

## License

The VeriArbor library is released under the repository [MIT License](LICENSE).
Promotion Studio has a separate [license and provenance
notice](apps/promotion_studio/LICENSE); no third-party runtime code or assets
are bundled. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

