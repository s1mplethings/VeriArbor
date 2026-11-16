# Pre-real-project experiment baseline — 2026-11-16

This is a source freeze, not a production release. No runtime, Core rule, prompt,
checker, Admission rule or test threshold was changed during freezing.

Core: 68 targeted tests pass. Host: 42 targeted tests pass on the isolated current
tree and on the sanitized local snapshot. The three known regressions still fail;
see TEST_RESULTS.json and KNOWN_FAILURES.json. Offline fixtures exercise the real
Host chain; they do not establish real LLM decision ability. Network dispatch was
guarded; real Provider calls: zero.

The original eight Core dirty files are included. Three historical auxiliary files
with local-user paths are omitted from this release tree only. Original files and
existing Git history remain unchanged. SOURCE_SHA256.json distinguishes captured
working bytes from Git-normalized LF bytes. FILES.txt lists the complete tree;
the enclosing Git commit identifies metadata without self-referential hashes.

Host remains independent. Its 1200-file sanitized snapshot, complete file hashes,
and exclusions are recorded here; the ZIP itself stays in the local freeze report
directory. It includes the existing ProjectSession, GoalComposer, WorkResolution,
Admission, TreeEdit, DAGRunner, ContextPacker, Worker, software-project generation,
acceptance, packaging and test dependencies. Excluded unrelated business modules
and historical payloads are listed explicitly; do not infer their functionality.

Host upload is blocked: its tracked historical migration/evidence tree includes
runtime/media/private-path material. The existing sole publication authority
classifies 1485 required release exclusions as UNKNOWN and cannot admit that
filtered tree. It was not bypassed or changed. The configured target is known:
s1mplethings/covenant-graph-nexus-kernel. No new public repository was created.

To reproduce, check out this commit, install Core into an isolated Python 3.11+
environment, obtain the local Host ZIP matching host-local-freeze.json, and verify
every entry against host-sanitized-manifest.json before extraction/use. Put
tools/offline_guard, Core src, and the extracted Host on PYTHONPATH; set
CGKN_OFFLINE_GUARD_PATH to the guard directory. Run the exact pytest targets listed
in TEST_RESULTS.json from their respective roots with a fresh temporary directory.
Do not infer permission for paid calls from this freeze. Start subsequent work on
a new branch; preserve this baseline.
