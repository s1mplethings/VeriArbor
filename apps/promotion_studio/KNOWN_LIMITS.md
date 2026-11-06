# Known Limits

- Local-only data; no cloud sync or multi-user collaboration.
- M12-scoped GUI tests pass; this preview is not a formal acceptance or final delivery.
- Historical generated milestone tests outside the release suite are not rerun here.
- Analytics uses the local/synthetic platform only and is labeled as such.
- Bluesky support is text-only and disabled/dry-run by default. Media, facets,
  threads and Bluesky analytics are not implemented.
- Bluesky live publishing requires `BLUESKY_DRY_RUN=0`, `BLUESKY_ALLOW_PUBLISH=1`
  and `publish_authorized: true` on the request/schedule.
- The scheduler worker must be started manually or by Windows Task Scheduler;
  the GUI does not start a background scheduler.
- A `PENDING` receipt whose send started is reconciled before any retry. If the
  remote outcome cannot be confirmed, it remains `UNKNOWN` for manual reconcile.
- The local simulated platform remains the default for `http://` platform URLs.
