# Promotion Studio

Promotion Studio is a standalone local-first application for projects,
campaigns, content revisions, approval, scheduling, local/simulated publishing,
receipts, and a text-only Bluesky adapter.

This is a **Research Preview / Alpha**. It is not a production service and does
not include real credentials or real user data. The GUI binds to
`127.0.0.1` by default.

## Requirements

- Windows 10/11 (the scheduler worker also runs on other Python platforms)
- Python 3.11+ (tested with Python 3.12)
- No third-party runtime dependencies

## Create a clean environment

```powershell
cd apps\promotion_studio
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

`requirements.txt` intentionally contains no runtime packages. `requirements-dev.txt`
adds `pytest` for the test suite.

## Start the GUI

```powershell
.\start.ps1
```

Equivalent explicit command:

```powershell
.\.venv\Scripts\python.exe -X utf8 main.py --serve --port 8080 --data .\local-data
```

Open <http://127.0.0.1:8080/>.

## Local simulated publishing platform

In a second terminal:

```powershell
.\.venv\Scripts\python.exe -X utf8 serve_platform.py --port 8090 --data .\local-platform-data
```

Then use `http://127.0.0.1:8090` as the Platform URL in the GUI or schedule.
This platform is simulated; it does not contact a real social network.

## Scheduler worker

Process due schedules once:

```powershell
.\.venv\Scripts\python.exe -X utf8 scheduler_worker.py --once --data .\local-data
```

The worker takes a non-blocking lock, so overlapping runs are safe. It logs
schedule IDs, statuses, and error reasons without credentials.

To run every minute, create a Windows Task Scheduler task manually:

- Program: `.venv\Scripts\python.exe` (absolute path recommended)
- Arguments: `-X utf8 scheduler_worker.py --once --data local-data`
- Start in: the `apps\promotion_studio` directory
- Trigger: every 1 minute
- Settings: "Do not start a new instance"

Do not install the task automatically.

## Data location

All persistent data is under the `--data` directory, by default `local-data/`:
`projects.json`, `campaigns.json`, `content.json`, `receipts.json`,
`schedules.json`, `analytics_samples.json`, and optional `media_storage/`.
Never commit that directory.

## Bluesky text-only adapter

The adapter is offline-tested and **dry-run by default**. It does not create a
real post unless all three conditions are true:

1. `BLUESKY_DRY_RUN=0`
2. `BLUESKY_ALLOW_PUBLISH=1`
3. The request or schedule carries `publish_authorized: true`

Configuration is read from environment variables in the server/worker process:

```powershell
$env:BLUESKY_HANDLE = "your-handle.bsky.social"
$env:BLUESKY_APP_PASSWORD = "app-password-from-bluesky-settings"
$env:BLUESKY_PDS = "https://bsky.social"
$env:BLUESKY_DRY_RUN = "1"          # default
$env:BLUESKY_AUTH_CHECK = "0"       # set 1 for login-only check
$env:BLUESKY_ALLOW_PUBLISH = "0"    # live publishing gate
```

Use `bluesky://bsky.social` as the Platform URL. Use a Bluesky **App Password**,
not the account password. Tokens and App Passwords are never stored in receipts
or logs.

For a safe authentication check, keep `BLUESKY_DRY_RUN=1` and set
`BLUESKY_AUTH_CHECK=1`; the adapter logs in and returns the account DID without
creating a post.

Media, facets, threads, and Bluesky Analytics are not implemented.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_publish.py tests\test_milestone_989800776c3d6229e431.py tests\test_bluesky_adapter.py tests\test_publish_reliability.py tests\test_promotion_gui.py -q
```

The release-scoped suite covers local publish/receipt behavior, M8 scheduling,
the Bluesky adapter, reliability/concurrency, and the GUI. Full test discovery
also includes four pre-existing M10 Analytics fixture failures; see
`KNOWN_LIMITS.md` and the repository `docs/KNOWN_FAILURES.md`.

## Shutdown and restart

Stop the GUI with `Ctrl+C` in its terminal. Restart with `.\start.ps1`; data is
reloaded from the `--data` directory. Do not delete the data directory while the
application is running.

## Offline demo

1. Start the GUI and local simulated platform.
2. Create a project and campaign.
3. Create content, submit for review, and approve it.
4. Schedule or publish to `http://127.0.0.1:8090`.
5. Open Receipts/Analytics and confirm the local receipt.
6. Run the scheduler worker once with `--once`.

No real social account is required for this demo.

## License and provenance

See `LICENSE` and `PROVENANCE.md` in this directory. No real credentials or
local-data are included in the release source package.
