# VeriArbor

**Research Preview / Alpha.** VeriArbor is a pure Python policy library for
certified Block substitution, explicit Port/Effect contracts, local
verification, and deterministic verification deduplication.

This preview also includes **Promotion Studio**, a standalone local GUI and
Bluesky text adapter. It is not production-ready and is not a formally
signed/trust-anchored delivery.

- Download: <https://github.com/s1mplethings/VeriArbor/releases>
- First-batch goals: [docs/FIRST_BATCH_PLATFORM_GOALS.md](docs/FIRST_BATCH_PLATFORM_GOALS.md)
- Promotion Studio: [apps/promotion_studio/README.md](apps/promotion_studio/README.md)
- Known failures: [docs/KNOWN_FAILURES.md](docs/KNOWN_FAILURES.md)

## What is in this preview

- `src/veriarbor/` — the pure policy library, standard library only.
- `tests/` — library unit, property, and integration tests.
- `apps/promotion_studio/` — the current M12 application, standalone and
  independent of the VeriArbor library and the private host repository.
- `docs/` — architecture, API limits, platform goals, and known failures.

The application does **not** import `veriarbor` and does not require the private
host repository. It uses Python's standard library at runtime.

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

- VeriArbor is a pure policy library. Host scheduling remains **SHADOW_ONLY**;
  no production retest-reduction claim is made.
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
