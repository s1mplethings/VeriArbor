# Release Test Summary

Date: 2026-11-07
Platform: Windows, Python 3.12.3, clean virtual environment
Source: this release worktree (not the original Anaconda environment)

## Library

```text
python -m unittest discover -s tests -v
Ran 59 tests
OK
```

## Application

```text
python -m pytest tests/test_publish.py tests/test_milestone_989800776c3d6229e431.py tests/test_bluesky_adapter.py tests/test_publish_reliability.py tests/test_promotion_gui.py -q
89 passed
```

The application suite covers local publish/receipt behavior, M8 schedule
idempotency and recovery, Bluesky adapter offline behavior, worker concurrency,
and GUI regression.

## Clean smoke

Using empty data directories and free loopback ports:

- GUI started and returned HTTP 200.
- Local simulated publish produced `PUBLISHED`.
- Worker `--once` processed a due schedule and produced `PUBLISHED`.
- Restart recovered the project from disk.
- Bluesky request returned `DRY_RUN` and did not create a remote post.

## Known failures

Four pre-existing M10 Analytics fixture tests fail because their mock platform
does not implement `/publish`. See [KNOWN_FAILURES.md](KNOWN_FAILURES.md). They
are outside the release-scoped pass result and are not claimed as green.

## Not verified

- Real Bluesky authentication or posting.
- Real Reddit or YouTube actions.
- Windows Task Scheduler installation.
- Any production/trust-anchored delivery claim.
