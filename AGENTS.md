# VeriArbor development entry

Read [project purpose](docs/PROJECT_OVERVIEW_ZH.md) and the relevant section of
[architecture](docs/ARCHITECTURE.md) before changing product behavior. Veri is
an independent, goal-driven project capability system; no central Forest,
fixed virtual team, mandatory phase pipeline or second planner/runtime.

Read only what the task needs:
- Core protocol or authority: [frozen governance](docs/CORE_GOVERNANCE_V1.md).
- Capability proposal, quality or reuse: [contracts and skills](docs/CAPABILITY_GATES_AND_SKILLS.md).
- Host context, documents or handoff: the document/context section of ARCHITECTURE.md,
  then actual callers in the Host workspace. Core contains no production executor.
- A specific regression: its current test and relevant report. Reports are historical
  evidence, not a new authority; do not load every report into each task.

Current local source, dirty changes and authenticated execution evidence take
precedence over a public commit or an old completion summary. Preserve existing
work. Verify what is wired before claiming behavior. Distinguish Core policy,
Host integration, offline fixtures and real Provider capability.

Internal algorithms may change within admitted goals, interfaces and effects.
For a design replacement, retain requirements and record the replaced decision,
reason, affected contracts and required checks in existing decisions/reports.
Goal, permission or checker changes require the existing authorization path.
Do not add a framework layer to solve a local bug. Markdown is explanatory;
contracts and receipt-qualified state remain authoritative.

## Boundary maintenance

For changes to entry points, clients, formal stores, consumers or recovery, read
`.agents/skills/veriarbor-boundary-closure/SKILL.md`. Check shared authority paths
and their architecture regressions. Register new formal entries and prove
delegation. Use common dynamic request preparation; verify successful artifact
identities on reuse. Never silently fall back to LEGACY.
