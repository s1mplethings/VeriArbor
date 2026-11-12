"""Minimal scheduler worker for Promotion Studio.

Recommended usage (Windows Task Scheduler, every minute):
  python -X utf8 scheduler_worker.py --once --data C:\\...\\local-data

The worker takes a non-blocking data-dir lock, so overlapping Task Scheduler
instances are safe: one runs, the others log a skip.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime_lock import file_lock
from milestones.milestone_989800776c3d6229e431.api import handle as m8_handle


def _log(data_dir, message):
    stamp = datetime.now(timezone.utc).isoformat()
    line = "%s %s" % (stamp, message)
    print(line, flush=True)
    try:
        os.makedirs(data_dir, exist_ok=True)
        with open(os.path.join(data_dir, "scheduler.log"), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        # Logging must never break scheduling.
        pass


def _load_projects(data_dir):
    path = os.path.join(data_dir, "projects.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if not text.strip():
        return []
    data = json.loads(text)
    return data if isinstance(data, list) else []


def run_once(data_dir, now=None):
    data_dir = os.path.abspath(data_dir)
    now = now or datetime.now(timezone.utc).isoformat()
    lock_path = os.path.join(data_dir, ".scheduler.lock")
    with file_lock(lock_path, blocking=False) as acquired:
        if not acquired:
            _log(data_dir, "worker skip: another scheduler worker is running")
            return {"skipped": True, "projects": 0, "published": 0, "errors": 0}

        projects = _load_projects(data_dir)
        published = 0
        errors = 0
        for project in projects:
            project_id = project.get("id")
            if not project_id:
                continue
            try:
                result = m8_handle(data_dir, {
                    "op": "schedule.run_due",
                    "project_id": project_id,
                    "now": now,
                })
            except Exception as exc:
                errors += 1
                _log(data_dir, "project=%s run_due error=%s" % (project_id, exc))
                continue

            if result.get("skipped"):
                _log(data_dir, "project=%s run_due skipped (busy)" % project_id)
                continue

            for item in result.get("items", []):
                if item.get("status") == "PUBLISHED":
                    published += 1
                _log(
                    data_dir,
                    "schedule=%s status=%s result=%s error=%s"
                    % (
                        item.get("id"),
                        item.get("status"),
                        item.get("result_status"),
                        item.get("last_error") or "",
                    ),
                )
            for err in result.get("errors", []):
                if err.get("schedule_id"):
                    errors += 1
                    _log(
                        data_dir,
                        "schedule=%s error=%s"
                        % (err.get("schedule_id"), err.get("error")),
                    )
        return {
            "skipped": False,
            "projects": len(projects),
            "published": published,
            "errors": errors,
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Promotion Studio scheduler worker")
    parser.add_argument("--data", default="./local-data", help="Data directory")
    parser.add_argument("--once", action="store_true", help="Run a single pass")
    parser.add_argument("--interval", type=int, default=0, help="Loop interval seconds")
    parser.add_argument("--now", default=None, help="Override now (ISO8601, tests only)")
    args = parser.parse_args(argv)

    if args.interval and not args.once:
        while True:
            run_once(args.data, now=args.now)
            time.sleep(max(1, args.interval))
    else:
        run_once(args.data, now=args.now)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
