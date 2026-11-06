# Known Test Failures and Scope

This preview keeps known failures visible rather than deleting tests or
rewriting assertions to make the suite look completely green.

## M10 Analytics fixture failures

Four tests in
`apps/promotion_studio/tests/test_milestone_af427946c6dea418047a.py`
(`TestM10Analytics.test_fetch_success`, `test_history`,
`test_recommend_high_confidence`, `test_recommend_low_confidence`) fail because
the test's mock platform implements `/metrics` but not `/publish`. The publish
step therefore does not create the PUBLISHED receipt that these tests expect.

The same failure was reproduced against the original pre-release working copy,
so it is a pre-existing test-fixture limitation, not a regression introduced by
the reliability work. The production local platform does implement `/publish`;
the application-level publish and receipt tests pass.

These tests are not used to claim Analytics readiness. Promotion Studio
Analytics remains local/synthetic only, and Bluesky analytics is not
implemented.

## Scope notes

- Historical generated milestone tests outside the release test set are not
  re-run here.
- `OFFLINE_TESTED` does not mean `LIVE_VERIFIED`.
- P11 formal trust anchor, independent signing, and final trusted delivery
  remain paused and are not part of this preview.
- Host scheduling remains SHADOW_ONLY; no production retest-reduction claim is
  made.
