"""Milestone M8: Scheduler.

Provides persistent, project-isolated scheduling of approved content for
publication. Reuses M1 project isolation, M5 content structures, M6 approval
status and M7 publication (promotion_publish).

Operations: schedule.create, schedule.list, schedule.cancel,
schedule.reschedule, schedule.run_due.
"""

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone

MILESTONE_ID = "M8"

_PROJECTS_FILENAME = "projects.json"
_CONTENT_FILENAME = "content.json"
_SCHEDULES_FILENAME = "schedules.json"


def _path(data_dir, filename):
    return os.path.join(data_dir, filename)


def _load_list(data_dir, filename):
    path = _path(data_dir, filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if not content.strip():
        return []
    data = json.loads(content)
    if not isinstance(data, list):
        return []
    return data


def _save_list(data_dir, filename, items):
    os.makedirs(data_dir, exist_ok=True)
    path = _path(data_dir, filename)
    tmp_path = path + "." + uuid.uuid4().hex + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def _require_project(data_dir, project_id):
    if not isinstance(project_id, str) or not project_id:
        raise ValueError("project_id must be a non-empty string")
    for record in _load_list(data_dir, _PROJECTS_FILENAME):
        if record.get("id") == project_id:
            return record
    raise ValueError("project not found: %s" % project_id)


def _find_content(data_dir, project_id, content_id):
    if not isinstance(content_id, str) or not content_id:
        raise ValueError("content_id must be a non-empty string")
    for record in _load_list(data_dir, _CONTENT_FILENAME):
        if record.get("id") == content_id:
            if record.get("project_id") != project_id:
                raise ValueError("content not found: %s" % content_id)
            return record
    raise ValueError("content not found: %s" % content_id)


def _parse_when(value, field_name="when"):
    """Parse an ISO8601 timestamp that must carry an explicit timezone offset."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty ISO8601 string" % field_name)
    text = value.strip()
    # Reject naive timestamps: require an explicit offset (Z or +/-HH:MM).
    normalized = text
    if normalized.endswith("Z") or normalized.endswith("z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        raise ValueError("%s must be a valid ISO8601 timestamp" % field_name)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("%s must be timezone-aware (include an offset)" % field_name)
    return parsed


def _find_schedule(schedules, project_id, schedule_id):
    if not isinstance(schedule_id, str) or not schedule_id:
        raise ValueError("schedule_id must be a non-empty string")
    for record in schedules:
        if record.get("id") == schedule_id:
            if record.get("project_id") != project_id:
                raise ValueError("schedule not found: %s" % schedule_id)
            return record
    raise ValueError("schedule not found: %s" % schedule_id)


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _content_snapshot(record):
    text = record.get("text") or ""
    return {
        "content_id": record.get("id"),
        "campaign_id": record.get("campaign_id"),
        "revision": record.get("revision"),
        "channel": record.get("channel"),
        "text": text,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def _target_snapshot(platform_url, account):
    return {"platform_url": platform_url, "account": account}


def _public_schedule(record):
    return {
        "id": record["id"],
        "project_id": record["project_id"],
        "content_id": record["content_id"],
        "content_revision": record.get("content_revision"),
        "channel": record.get("channel"),
        "platform_url": record["platform_url"],
        "idempotency_key": record["idempotency_key"],
        "when": record["when"],
        "status": record["status"],
        "publish_authorized": bool(record.get("publish_authorized", False)),
        "receipt_id": record.get("receipt_id"),
        "result_status": record.get("result_status"),
        "content_snapshot": record.get("content_snapshot"),
        "target": record.get("target"),
        "last_error": record.get("last_error"),
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at"),
        "history": list(record.get("history", [])),
    }


def _validate_schedule_snapshot(data_dir, record):
    snapshot = record.get("content_snapshot")
    if not snapshot:
        return
    content = _find_content(data_dir, record["project_id"], record["content_id"])
    text = content.get("text") or ""
    checks = [
        ("content_id", snapshot.get("content_id"), content.get("id")),
        ("revision", snapshot.get("revision"), content.get("revision")),
        ("channel", snapshot.get("channel"), content.get("channel")),
        (
            "text_sha256",
            snapshot.get("text_sha256"),
            hashlib.sha256(text.encode("utf-8")).hexdigest(),
        ),
    ]
    for name, expected, actual in checks:
        if expected != actual:
            raise ValueError(
                "schedule conflict: content changed since scheduling (%s)" % name
            )


def _run_due(data_dir, project_id, now_value):
    _require_project(data_dir, project_id)
    now_dt = _parse_when(now_value, "now")

    schedules = _load_list(data_dir, _SCHEDULES_FILENAME)
    publish_handle = _publish_handle()
    processed = []
    errors = []

    for record in schedules:
        if record.get("project_id") != project_id:
            continue
        if record.get("status") != "PENDING":
            continue
        try:
            due_dt = _parse_when(record.get("when"), "when")
        except ValueError:
            continue
        if due_dt > now_dt:
            continue

        if record.get("receipt_id") and record.get("result_status") == "PUBLISHED":
            continue

        try:
            _validate_schedule_snapshot(data_dir, record)
        except ValueError as exc:
            record["status"] = "FAILED"
            record["result_status"] = "CONFLICT"
            record["last_error"] = str(exc)
            record["updated_at"] = _now_iso()
            errors.append({"schedule_id": record["id"], "error": str(exc)})
            processed.append(_public_schedule(record))
            _save_list(data_dir, _SCHEDULES_FILENAME, schedules)
            continue

        try:
            receipt = publish_handle(data_dir, {
                "op": "publish.send",
                "project_id": project_id,
                "content_id": record["content_id"],
                "platform_url": record["platform_url"],
                "idempotency_key": record["idempotency_key"],
                "publish_authorized": bool(record.get("publish_authorized", False)),
                "account": (record.get("target") or {}).get("account"),
            })
        except ValueError as exc:
            record["last_error"] = str(exc)
            record["updated_at"] = _now_iso()
            if str(exc).startswith("publish conflict:"):
                record["status"] = "FAILED"
                record["result_status"] = "CONFLICT"
                processed.append(_public_schedule(record))
            errors.append({"schedule_id": record["id"], "error": str(exc)})
            _save_list(data_dir, _SCHEDULES_FILENAME, schedules)
            continue

        receipt_id = receipt.get("id")
        result_status = receipt.get("status")
        record["receipt_id"] = receipt_id
        record["result_status"] = result_status
        record["last_error"] = receipt.get("error")
        record["updated_at"] = _now_iso()
        if result_status == "PUBLISHED":
            record["status"] = "PUBLISHED"
        elif result_status == "RATE_LIMITED":
            record["status"] = "RATE_LIMITED"
        elif result_status == "UNKNOWN":
            record["status"] = "UNKNOWN"
        elif result_status == "PENDING":
            # A send may have started; keep the task recoverable instead of
            # turning a timeout into a false FAILED.
            record["status"] = "PENDING"
            errors.append({
                "schedule_id": record["id"],
                "error": "PENDING outcome requires reconcile",
            })
        elif result_status == "DRY_RUN":
            record["status"] = "DRY_RUN"
        elif result_status == "BLOCKED":
            record["status"] = "BLOCKED"
        elif result_status == "CONFLICT":
            record["status"] = "FAILED"
            record["result_status"] = "CONFLICT"
            errors.append({
                "schedule_id": record["id"],
                "error": receipt.get("error") or "remote conflict",
            })
        else:
            record["status"] = "FAILED"
        processed.append(_public_schedule(record))
        # Persist after every item so a crash cannot leave a published remote
        # post with an un-updated local schedule.
        _save_list(data_dir, _SCHEDULES_FILENAME, schedules)

    return {"items": processed, "errors": errors}


def _publish_handle():
    try:
        from promotion_publish import handle as publish_handle
    except ImportError:
        raise ValueError("M7 publication module not found")
    return publish_handle


def handle(data_dir, request):
    if not isinstance(data_dir, str) or not data_dir:
        raise ValueError("data_dir must be a non-empty string")
    if not isinstance(request, dict):
        raise ValueError("request must be a dict")

    op = request.get("op")
    if not isinstance(op, str) or not op:
        raise ValueError("request must contain a non-empty 'op' string")

    if op == "schedule.create":
        project_id = request.get("project_id")
        _require_project(data_dir, project_id)

        content_id = request.get("content_id")
        content_record = _find_content(data_dir, project_id, content_id)
        if content_record.get("status") != "APPROVED":
            raise ValueError("content not approved: %s" % content_id)

        platform_url = request.get("platform_url")
        if not isinstance(platform_url, str) or not platform_url.strip():
            raise ValueError("platform_url must be a non-empty string")

        idempotency_key = request.get("idempotency_key")
        if not isinstance(idempotency_key, str) or not idempotency_key.strip():
            raise ValueError("idempotency_key must be a non-empty string")

        when = request.get("when")
        _parse_when(when, "when")

        account = request.get("account")
        publish_authorized = bool(request.get("publish_authorized", False))
        content_snapshot = _content_snapshot(content_record)
        target = _target_snapshot(platform_url, account)
        schedules = _load_list(data_dir, _SCHEDULES_FILENAME)

        # The same key must identify exactly one publish intent. Repeating the
        # identical request returns the existing schedule; changing content,
        # revision, target or time is a conflict rather than a new task.
        for existing in schedules:
            if existing.get("idempotency_key") != idempotency_key:
                continue
            same = (
                existing.get("project_id") == project_id
                and existing.get("content_id") == content_id
                and existing.get("content_revision") == content_snapshot["revision"]
                and existing.get("channel") == content_snapshot["channel"]
                and existing.get("platform_url") == platform_url
                and existing.get("when") == when
                and bool(existing.get("publish_authorized", False))
                == publish_authorized
                and (existing.get("target") or {}).get("account") == account
            )
            if not same:
                raise ValueError(
                    "schedule idempotency conflict: key reused with different intent"
                )
            return _public_schedule(existing)

        now = _now_iso()
        record = {
            "id": uuid.uuid4().hex,
            "project_id": project_id,
            "content_id": content_id,
            "content_revision": content_snapshot["revision"],
            "channel": content_snapshot["channel"],
            "platform_url": platform_url,
            "idempotency_key": idempotency_key,
            "when": when,
            "status": "PENDING",
            "publish_authorized": publish_authorized,
            "receipt_id": None,
            "result_status": None,
            "content_snapshot": content_snapshot,
            "target": target,
            "last_error": None,
            "created_at": now,
            "updated_at": now,
            "history": [],
        }
        schedules.append(record)
        _save_list(data_dir, _SCHEDULES_FILENAME, schedules)
        return _public_schedule(record)

    if op == "schedule.list":
        project_id = request.get("project_id")
        _require_project(data_dir, project_id)
        schedules = _load_list(data_dir, _SCHEDULES_FILENAME)
        items = [_public_schedule(r) for r in schedules if r.get("project_id") == project_id]
        return {"items": items}

    if op == "schedule.cancel":
        project_id = request.get("project_id")
        _require_project(data_dir, project_id)
        schedule_id = request.get("schedule_id")
        schedules = _load_list(data_dir, _SCHEDULES_FILENAME)
        record = _find_schedule(schedules, project_id, schedule_id)
        record["status"] = "CANCELLED"
        record["updated_at"] = _now_iso()
        _save_list(data_dir, _SCHEDULES_FILENAME, schedules)
        return _public_schedule(record)

    if op == "schedule.reschedule":
        project_id = request.get("project_id")
        _require_project(data_dir, project_id)
        schedule_id = request.get("schedule_id")
        when = request.get("when")
        _parse_when(when, "when")
        schedules = _load_list(data_dir, _SCHEDULES_FILENAME)
        record = _find_schedule(schedules, project_id, schedule_id)
        if not isinstance(record.get("history"), list):
            record["history"] = []
        record["history"].append({"when": record["when"], "status": record["status"]})
        record["when"] = when
        record["updated_at"] = _now_iso()
        _save_list(data_dir, _SCHEDULES_FILENAME, schedules)
        return _public_schedule(record)

    if op == "schedule.run_due":
        from runtime_lock import file_lock

        lock_path = os.path.join(data_dir, ".schedule.lock")
        with file_lock(lock_path, blocking=False) as acquired:
            if not acquired:
                return {
                    "items": [],
                    "skipped": True,
                    "errors": [{"error": "schedule.run_due already in progress"}],
                }
            return _run_due(data_dir, request.get("project_id"), request.get("now"))

    raise ValueError("unknown operation: %s" % op)
