"""Milestone M7: Local Publish and earliest usable GUI.

Provides persistent, idempotent local publication operations (send, get, list, reconcile, retry)
with a real threaded HTTP test platform in promotion_publish.py.
Reuses M1 project isolation, M5 content structures, and M6 approval status.
"""

import hashlib
import json
import os
import uuid
import time
import threading
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from runtime_lock import file_lock

MILESTONE_ID = "M7"
PLATFORM_LOCAL = "local-http"
PLATFORM_BLUESKY = "bluesky"


class PublishConflict(ValueError):
    """A definite conflict that must not be auto-retried."""

_PROJECTS_FILENAME = "projects.json"
_CONTENT_FILENAME = "content.json"
_RECEIPTS_FILENAME = "receipts.json"
_PUBLICATIONS_FILENAME = "publications.json"
_METRICS_FILENAME = "metrics.json"
_MEDIA_FILENAME = "media.json"

# Per-data_dir locks to serialize read-modify-write cycles on the shared JSON
# stores. Without this, concurrent publish.send calls each load the receipts
# list, append their own receipt, and save, so the last writer wins and the
# other receipts are lost -> "receipt not found" on later publish.get.
_LOCKS = {}
_LOCKS_GUARD = threading.Lock()


def _lock_for(data_dir):
    key = os.path.abspath(data_dir)
    with _LOCKS_GUARD:
        lock = _LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _LOCKS[key] = lock
        return lock


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
    # Use a unique temp file per write to avoid collisions between concurrent
    # writers (e.g. the threaded platform server and the API module) that would
    # otherwise share the same ".tmp" path and cause WinError 32 on replace.
    tmp_path = path + "." + uuid.uuid4().hex + ".tmp"
    try:
        # Ensure we write exactly one valid JSON document to the temp file
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        # Atomic replace ensures no partial writes or concatenated JSON objects remain.
        # Retry with backoff to tolerate transient locks (e.g. antivirus/indexer or
        # another handle briefly holding the destination on Windows).
        last_error = None
        for attempt in range(10):
            try:
                os.replace(tmp_path, path)
                last_error = None
                break
            except PermissionError as exc:
                last_error = exc
                time.sleep(0.01 * (attempt + 1))
        if last_error is not None:
            raise last_error
    finally:
        # Guarantee the temp file handle is closed and the temp file removed if
        # the replace never succeeded, so no stale locks remain.
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


def _find_content(content_items, project_id, content_id):
    if not isinstance(content_id, str) or not content_id:
        raise ValueError("content_id must be a non-empty string")
    for record in content_items:
        if record.get("id") == content_id:
            if record.get("project_id") != project_id:
                raise ValueError("content not found: %s" % content_id)
            return record
    raise ValueError("content not found: %s" % content_id)


def _validate_approval_status(data_dir, project_id, content_id):
    # Check if content is APPROVED via M6 logic (simplified check on content status field)
    # In the provided M6 code, approval updates content['status'] to 'APPROVED'
    content_items = _load_list(data_dir, _CONTENT_FILENAME)
    record = _find_content(content_items, project_id, content_id)
    if record.get("status") != "APPROVED":
        raise ValueError("content not approved: %s" % content_id)
    return record


def _get_receipt(receipts, receipt_id):
    for r in receipts:
        if r["id"] == receipt_id:
            return r
    return None


def _make_attempt(operation, status, started_at=None, ended_at=None):
    if started_at is None:
        started_at = time.time()
    if ended_at is None:
        ended_at = time.time()
    return {
        "operation": operation,
        "status": status,
        "started_at": started_at,
        "ended_at": ended_at
    }


def _public_receipt(record):
    """Ensure all mandatory fields are present in the returned receipt structure."""
    return {
        "id": record.get("id"),
        "project_id": record.get("project_id"),
        "content_id": record.get("content_id"),
        "revision": record.get("revision"),
        "channel": record.get("channel"),
        "text": record.get("text"),
        "status": record.get("status"),
        "remote_id": record.get("remote_id"),
        "remote_key": record.get("remote_key"),
        "cid": record.get("cid"),
        "account_did": record.get("account_did"),
        "platform": record.get("platform"),
        "idempotency_key": record.get("idempotency_key"),
        "request_ref": record.get("request_ref"),
        "response_ref": record.get("response_ref"),
        "attempts": record.get("attempts", []),
        "url": record.get("url"),
        "content_snapshot": record.get("content_snapshot"),
        "target": record.get("target"),
        "error": record.get("error"),
        "send_started_at": record.get("send_started_at"),
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at"),
    }


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _platform_kind(platform_url):
    value = (platform_url or "").strip().lower()
    if value.startswith("bluesky://"):
        return PLATFORM_BLUESKY
    return PLATFORM_LOCAL


def _default_account(platform_url):
    if _platform_kind(platform_url) == PLATFORM_BLUESKY:
        return os.environ.get("BLUESKY_HANDLE") or None
    return None


def _content_snapshot(record):
    text = record.get("text") or ""
    return {
        "content_id": record.get("id"),
        "campaign_id": record.get("campaign_id"),
        "revision": record.get("revision"),
        "channel": record.get("channel"),
        "text": text,
        "text_sha256": _sha256_text(text),
    }


def _target_snapshot(platform_url, account):
    return {
        "platform_url": platform_url,
        "platform": _platform_kind(platform_url),
        "account": account or _default_account(platform_url),
    }


def _validate_receipt_intent(receipt, content_record, platform_url, account):
    """Reject a reused key whose content/target differs from the stored intent."""
    snapshot = receipt.get("content_snapshot")
    if snapshot:
        checks = [
            ("content_id", snapshot.get("content_id"), content_record.get("id")),
            ("revision", snapshot.get("revision"), content_record.get("revision")),
            ("channel", snapshot.get("channel"), content_record.get("channel")),
            (
                "text_sha256",
                snapshot.get("text_sha256"),
                _sha256_text(content_record.get("text") or ""),
            ),
        ]
        for name, expected, actual in checks:
            if expected != actual:
                raise PublishConflict(
                    "publish conflict: reused idempotency_key has different %s" % name
                )
    else:
        # Legacy receipts have no snapshot; compare the fields they do carry.
        if receipt.get("content_id") != content_record.get("id"):
            raise PublishConflict(
                "publish conflict: reused idempotency_key has different content_id"
            )
        if receipt.get("revision") != content_record.get("revision"):
            raise PublishConflict(
                "publish conflict: reused idempotency_key has different revision"
            )
        if receipt.get("channel") != content_record.get("channel"):
            raise PublishConflict(
                "publish conflict: reused idempotency_key has different channel"
            )
        if (receipt.get("text") or "") != (content_record.get("text") or ""):
            raise PublishConflict(
                "publish conflict: reused idempotency_key has different text"
            )

    target = receipt.get("target")
    if target:
        if target.get("platform_url") != platform_url:
            raise PublishConflict(
                "publish conflict: reused idempotency_key has different platform_url"
            )
        expected_account = target.get("account")
        actual_account = account or _default_account(platform_url)
        if (
            expected_account
            and actual_account
            and str(expected_account).lower() != str(actual_account).lower()
        ):
            raise PublishConflict(
                "publish conflict: reused idempotency_key has different target account"
            )


def _new_receipt(project_id, content_record, platform_url, idempotency_key, account):
    remote_key = None
    if _platform_kind(platform_url) == PLATFORM_BLUESKY:
        from bluesky_adapter import make_rkey

        remote_key = make_rkey(idempotency_key)
    now = _now_iso()
    return {
        "id": uuid.uuid4().hex,
        "project_id": project_id,
        "content_id": content_record.get("id"),
        "revision": content_record.get("revision"),
        "channel": content_record.get("channel"),
        "text": content_record.get("text"),
        "status": "PENDING",
        "remote_id": None,
        "remote_key": remote_key,
        "cid": None,
        "account_did": None,
        "platform": _platform_kind(platform_url),
        "idempotency_key": idempotency_key,
        "request_ref": None,
        "response_ref": None,
        "attempts": [],
        "url": None,
        "content_snapshot": _content_snapshot(content_record),
        "target": _target_snapshot(platform_url, account),
        "send_started_at": None,
        "created_at": now,
        "updated_at": now,
        "error": None,
    }


def _persist_receipt(data_dir, receipt):
    receipts = _load_list(data_dir, _RECEIPTS_FILENAME)
    for i, item in enumerate(receipts):
        if item.get("id") == receipt.get("id"):
            receipts[i] = receipt
            break
    else:
        receipts.append(receipt)
    _save_list(data_dir, _RECEIPTS_FILENAME, receipts)


def _apply_result(receipt, result, operation="POST"):
    status = result.get("status") or "UNKNOWN"
    receipt["status"] = status
    for field in ("remote_id", "cid", "url"):
        if result.get(field) is not None:
            receipt[field] = result.get(field)
    receipt["remote_key"] = result.get("remote_key") or receipt.get("remote_key")
    receipt["account_did"] = result.get("account_did") or receipt.get("account_did")
    receipt["error"] = result.get("error")
    if result.get("retry_after") is not None:
        receipt["retry_after"] = result.get("retry_after")
    response = result.get("response")
    if response is not None:
        receipt["response_ref"] = json.dumps(response, ensure_ascii=False, sort_keys=True)
    elif result.get("error"):
        receipt["response_ref"] = json.dumps(
            {"error": result["error"]}, ensure_ascii=False
        )
    attempt_status = {
        "PUBLISHED": "SUCCESS",
        "RATE_LIMITED": "RATE_LIMITED",
        "UNKNOWN": "UNKNOWN",
        "CONFLICT": "CONFLICT",
        "DRY_RUN": "DRY_RUN",
        "BLOCKED": "BLOCKED",
    }.get(status, status)
    receipt.setdefault("attempts", []).append(_make_attempt(operation, attempt_status))
    receipt["updated_at"] = _now_iso()


def _local_send(receipt, platform_url):
    payload = {
        "idempotency_key": receipt["idempotency_key"],
        "project_id": receipt["project_id"],
        "content_id": receipt["content_id"],
        "revision": receipt["revision"],
        "channel": receipt["channel"],
        "text": receipt["text"],
    }
    url = platform_url.rstrip("/") + "/publish"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        response = urllib.request.urlopen(req, timeout=10)
        resp_code = response.getcode()
        resp_body = response.read().decode("utf-8")
        if resp_code == 200:
            resp_json = json.loads(resp_body)
            remote_id = resp_json.get("remote_id", resp_json.get("id"))
            if remote_id is None:
                return {
                    "status": "UNKNOWN",
                    "error": "platform response missing remote_id",
                }
            return {
                "status": "PUBLISHED",
                "remote_id": remote_id,
                "url": resp_json.get("url"),
                "response": resp_json,
            }
        return {"status": "FAILED", "error": "unexpected HTTP %s" % resp_code}
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            return {
                "status": "RATE_LIMITED",
                "error": "HTTP 429",
                "retry_after": exc.headers.get("Retry-After") if exc.headers else None,
            }
        return {"status": "FAILED", "error": "HTTP %s" % exc.code}
    except Exception as exc:
        return {"status": "UNKNOWN", "error": str(exc)}


def _local_reconcile(receipt, platform_url):
    key = urllib.parse.quote(receipt["idempotency_key"])
    url = platform_url.rstrip("/") + "/publications?key=" + key
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            body = response.read().decode("utf-8")
            payload = json.loads(body) if body else {}
            return {
                "status": "PUBLISHED",
                "remote_id": payload.get("id") or payload.get("remote_id"),
                "url": payload.get("url"),
                "response": payload,
            }
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"status": "ABSENT", "error": "remote publication not found"}
        return {"status": "UNKNOWN", "error": "HTTP %s" % exc.code}
    except Exception as exc:
        return {"status": "UNKNOWN", "error": str(exc)}


def _bluesky_send(receipt, publish_authorized):
    from bluesky_adapter import BlueskyAdapter

    adapter = BlueskyAdapter.from_env()
    target = receipt.get("target") or {}
    return adapter.publish(
        receipt.get("text") or "",
        receipt.get("remote_key"),
        account_ref=target.get("account"),
        publish_authorized=publish_authorized,
    )


def _bluesky_reconcile(receipt):
    from bluesky_adapter import BlueskyAdapter

    adapter = BlueskyAdapter.from_env()
    target = receipt.get("target") or {}
    return adapter.reconcile(
        receipt.get("remote_key"),
        receipt.get("text") or "",
        account_did=receipt.get("account_did"),
        account_ref=target.get("account"),
    )


def _reconcile_receipt(receipt, platform_url):
    if _platform_kind(platform_url) == PLATFORM_BLUESKY:
        if not receipt.get("remote_key"):
            return {"status": "UNKNOWN", "error": "missing persisted rkey"}
        return _bluesky_reconcile(receipt)
    return _local_reconcile(receipt, platform_url)


def _recover_pending(data_dir, receipt, platform_url):
    """Resolve a PENDING receipt that may have reached the remote side."""
    result = _reconcile_receipt(receipt, platform_url)
    if result.get("status") == "ABSENT":
        result = {
            "status": "UNKNOWN",
            "error": "pending outcome not found; manual reconcile/retry required",
            "remote_key": receipt.get("remote_key"),
        }
    _apply_result(receipt, result, "RECONCILE")
    _persist_receipt(data_dir, receipt)
    return _public_receipt(receipt)


def _send_receipt(data_dir, receipt, platform_url, publish_authorized):
    kind = _platform_kind(platform_url)
    if kind == PLATFORM_BLUESKY and not receipt.get("remote_key"):
        from bluesky_adapter import make_rkey

        receipt["remote_key"] = make_rkey(receipt["idempotency_key"])
    if kind == PLATFORM_BLUESKY:
        pds = os.environ.get("BLUESKY_PDS", "https://bsky.social")
        receipt["request_ref"] = pds.rstrip("/") + "/xrpc/com.atproto.repo.createRecord"
    else:
        receipt["request_ref"] = platform_url.rstrip("/") + "/publish"
    receipt["send_started_at"] = time.time()
    receipt["updated_at"] = _now_iso()
    _persist_receipt(data_dir, receipt)

    if kind == PLATFORM_BLUESKY:
        result = _bluesky_send(receipt, publish_authorized)
    else:
        result = _local_send(receipt, platform_url)

    with _lock_for(data_dir):
        _apply_result(receipt, result)
        _persist_receipt(data_dir, receipt)
    return _public_receipt(receipt)


def _do_send(
    data_dir,
    project_id,
    content_id,
    platform_url,
    idempotency_key,
    account=None,
    publish_authorized=False,
):
    if not isinstance(platform_url, str) or not platform_url.strip():
        raise ValueError("platform_url must be a non-empty string")
    if not isinstance(idempotency_key, str) or not idempotency_key:
        raise ValueError("idempotency_key must be a non-empty string")
    platform_url = platform_url.strip()
    content_record = _validate_approval_status(data_dir, project_id, content_id)

    # M11 media validation: every referenced media_id must exist and be VALID.
    media_ids = content_record.get("media_ids") or []
    if media_ids:
        media_items = _load_list(data_dir, _MEDIA_FILENAME)
        for media_id in media_ids:
            found = None
            for m in media_items:
                if m.get("id") == media_id:
                    found = m
                    break
            if found is None:
                raise ValueError("media not found: %s" % media_id)
            if found.get("project_id") != project_id:
                raise ValueError("media not found: %s" % media_id)
            if found.get("status") == "BROKEN":
                raise ValueError("media is BROKEN: %s" % media_id)
            stored_sha = found.get("sha256")
            stored_path = found.get("path") or found.get("stored_path")
            if stored_sha and stored_path:
                if not os.path.isabs(stored_path):
                    stored_path = os.path.join(data_dir, stored_path)
                if not os.path.exists(stored_path):
                    raise ValueError("media is BROKEN: %s" % media_id)
                try:
                    with open(stored_path, "rb") as mf:
                        current_bytes = mf.read()
                except OSError:
                    raise ValueError("media is BROKEN: %s" % media_id)
                if hashlib.sha256(current_bytes).hexdigest() != stored_sha:
                    raise ValueError("media is BROKEN: %s" % media_id)

    # One cross-process publish lock serializes intent checks, remote calls and
    # receipt updates. This is intentionally coarse but reliable for a local app.
    with file_lock(os.path.join(data_dir, ".publish.lock")):
        with _lock_for(data_dir):
            receipts = _load_list(data_dir, _RECEIPTS_FILENAME)
            existing = None
            for r in receipts:
                if r.get("idempotency_key") == idempotency_key:
                    existing = r
                    break

            if existing:
                _validate_receipt_intent(
                    existing, content_record, platform_url, account
                )
                if existing.get("status") != "PENDING":
                    return _public_receipt(existing)
                if _platform_kind(platform_url) == PLATFORM_BLUESKY:
                    existing.setdefault(
                        "target", _target_snapshot(platform_url, account)
                    )
                    existing.setdefault("platform", PLATFORM_BLUESKY)
                if existing.get("send_started_at"):
                    return _recover_pending(data_dir, existing, platform_url)
                receipt = existing
            else:
                receipt = _new_receipt(
                    project_id,
                    content_record,
                    platform_url,
                    idempotency_key,
                    account,
                )
                receipts.append(receipt)
                _save_list(data_dir, _RECEIPTS_FILENAME, receipts)

        return _send_receipt(data_dir, receipt, platform_url, publish_authorized)


def handle(data_dir, request):
    if not isinstance(data_dir, str) or not data_dir:
        raise ValueError("data_dir must be a non-empty string")
    if not isinstance(request, dict):
        raise ValueError("request must be a dict")

    op = request.get("op")
    if not isinstance(op, str) or not op:
        raise ValueError("request must contain a non-empty 'op' string")

    project_id = request.get("project_id")
    _require_project(data_dir, project_id)

    lock = _lock_for(data_dir)

    if op == "publish.send":
        content_id = request.get("content_id")
        platform_url = request.get("platform_url")
        idempotency_key = request.get("idempotency_key")
        return _do_send(
            data_dir,
            project_id,
            content_id,
            platform_url,
            idempotency_key,
            account=request.get("account"),
            publish_authorized=bool(request.get("publish_authorized", False)),
        )

    if op == "publish.get":
        receipt_id = request.get("receipt_id")
        if not isinstance(receipt_id, str) or not receipt_id:
            raise ValueError("receipt_id must be a non-empty string")

        with lock:
            receipts = _load_list(data_dir, _RECEIPTS_FILENAME)
            target = _get_receipt(receipts, receipt_id)
            if not target:
                raise ValueError("receipt not found: %s" % receipt_id)
            if target["project_id"] != project_id:
                raise ValueError("receipt belongs to different project")
            return _public_receipt(target)

    if op == "publish.list":
        with lock:
            receipts = _load_list(data_dir, _RECEIPTS_FILENAME)
            items = [_public_receipt(r) for r in receipts if r["project_id"] == project_id]
            return {"items": items}

    if op == "publish.reconcile":
        receipt_id = request.get("receipt_id")
        platform_url = request.get("platform_url")

        if not isinstance(receipt_id, str) or not receipt_id:
            raise ValueError("receipt_id must be a non-empty string")
        if not isinstance(platform_url, str) or not platform_url:
            raise ValueError("platform_url must be a non-empty string")
        platform_url = platform_url.strip()

        with file_lock(os.path.join(data_dir, ".publish.lock")):
            with lock:
                receipts = _load_list(data_dir, _RECEIPTS_FILENAME)
                target = _get_receipt(receipts, receipt_id)
                if not target:
                    raise ValueError("receipt not found: %s" % receipt_id)
                if target["project_id"] != project_id:
                    raise ValueError("receipt belongs to different project")

            if _platform_kind(platform_url) == PLATFORM_BLUESKY:
                target["request_ref"] = (
                    os.environ.get("BLUESKY_PDS", "https://bsky.social").rstrip("/")
                    + "/xrpc/com.atproto.repo.getRecord"
                )
                result = _bluesky_reconcile(target)
            else:
                target["request_ref"] = (
                    platform_url.rstrip("/")
                    + "/publications?key="
                    + urllib.parse.quote(target["idempotency_key"])
                )
                result = _local_reconcile(target, platform_url)

            with lock:
                _apply_result(target, result, "RECONCILE")
                _persist_receipt(data_dir, target)
            return _public_receipt(target)

    if op == "publish.retry":
        receipt_id = request.get("receipt_id")
        platform_url = request.get("platform_url")

        if not isinstance(receipt_id, str) or not receipt_id:
            raise ValueError("receipt_id must be a non-empty string")
        if not isinstance(platform_url, str) or not platform_url:
            raise ValueError("platform_url must be a non-empty string")
        platform_url = platform_url.strip()

        with file_lock(os.path.join(data_dir, ".publish.lock")):
            with lock:
                receipts = _load_list(data_dir, _RECEIPTS_FILENAME)
                target = _get_receipt(receipts, receipt_id)
                if not target:
                    raise ValueError("receipt not found: %s" % receipt_id)
                if target["project_id"] != project_id:
                    raise ValueError("receipt belongs to different project")

            if target.get("status") in ("PUBLISHED", "CONFLICT"):
                return _public_receipt(target)

            # A pending/unknown outcome must be reconciled before an explicit
            # retry is allowed to send. If the outcome is still unknown, keep it.
            if target.get("status") in ("PENDING", "UNKNOWN"):
                if target.get("send_started_at"):
                    result = _reconcile_receipt(target, platform_url)
                    if result.get("status") in ("PUBLISHED", "CONFLICT", "UNKNOWN"):
                        with lock:
                            _apply_result(target, result, "RECONCILE")
                            _persist_receipt(data_dir, target)
                        return _public_receipt(target)
                    # ABSENT: explicit retry may safely send using the same key/rkey.

            with lock:
                if _platform_kind(platform_url) == PLATFORM_BLUESKY:
                    target["target"] = target.get("target") or _target_snapshot(
                        platform_url, request.get("account")
                    )
                _persist_receipt(data_dir, target)
            return _send_receipt(
                data_dir,
                target,
                platform_url,
                bool(request.get("publish_authorized", False)),
            )

    raise ValueError("unknown operation: %s" % op)


class PlatformHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _read_json(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        return json.loads(body.decode('utf-8'))

    def _send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_POST(self):
        if self.path == '/publish':
            try:
                payload = self._read_json()
                idem_key = payload.get('idempotency_key')
                if not idem_key:
                    self._send_json(400, {"error": "missing idempotency_key"})
                    return

                lock = _lock_for(self.server.data_dir)
                with lock:
                    # Load publications store
                    pubs = _load_list(self.server.data_dir, _PUBLICATIONS_FILENAME)

                    # Check idempotency
                    for pub in pubs:
                        if pub.get('idempotency_key') == idem_key:
                            # Already processed
                            self._send_json(200, {"id": pub['id'], "url": pub['url'], "remote_id": pub['id']})
                            return

                    # Create new publication
                    pub_id = uuid.uuid4().hex
                    url = "http://localhost:%d/publications/%s" % (self.server.port, pub_id)
                    new_pub = {
                        "id": pub_id,
                        "idempotency_key": idem_key,
                        "project_id": payload.get('project_id'),
                        "content_id": payload.get('content_id'),
                        "revision": payload.get('revision'),
                        "channel": payload.get('channel'),
                        "text": payload.get('text'),
                        "url": url
                    }
                    pubs.append(new_pub)
                    _save_list(self.server.data_dir, _PUBLICATIONS_FILENAME, pubs)

                    # Update metrics
                    metrics = _load_list(self.server.data_dir, _METRICS_FILENAME)
                    metric_entry = {
                        "remote_id": pub_id,
                        "count": 1,
                        "views": 0,
                        "impressions": 0,
                        "reactions": 0,
                        "comments": 0
                    }
                    found = False
                    for m in metrics:
                        if m["remote_id"] == pub_id:
                            m["count"] += 1
                            found = True
                            break
                    if not found:
                        metrics.append(metric_entry)
                    _save_list(self.server.data_dir, _METRICS_FILENAME, metrics)

                self._send_json(200, {"id": pub_id, "url": url, "remote_id": pub_id})

            except Exception as e:
                self._send_json(500, {"error": str(e)})
        else:
            self._send_json(404, {"error": "not found"})

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/publications':
            params = urllib.parse.parse_qs(parsed.query)
            key = params.get('key', [None])[0]
            if not key:
                self._send_json(400, {"error": "missing key"})
                return

            lock = _lock_for(self.server.data_dir)
            with lock:
                pubs = _load_list(self.server.data_dir, _PUBLICATIONS_FILENAME)
                for pub in pubs:
                    if pub.get('idempotency_key') == key:
                        self._send_json(200, {"id": pub['id'], "remote_id": pub['id'], "url": pub['url']})
                        return
            self._send_json(404, {"error": "not found"})

        elif parsed.path == '/metrics':
            params = urllib.parse.parse_qs(parsed.query)
            remote_id = params.get('remote_id', [None])[0]
            if not remote_id:
                self._send_json(400, {"error": "missing remote_id"})
                return

            lock = _lock_for(self.server.data_dir)
            with lock:
                metrics = _load_list(self.server.data_dir, _METRICS_FILENAME)
                for m in metrics:
                    if m["remote_id"] == remote_id:
                        self._send_json(200, {
                            "remote_id": remote_id,
                            "count": m.get("count", 1),
                            "views": m.get("views", 0),
                            "impressions": m.get("impressions", 0),
                            "reactions": m.get("reactions", 0),
                            "comments": m.get("comments", 0)
                        })
                        return
            self._send_json(404, {"error": "not found"})
        else:
            self._send_json(404, {"error": "not found"})


def serve_platform(host, port, data_dir):
    server = ThreadingHTTPServer((host, port), PlatformHandler)
    server.data_dir = data_dir
    server.port = port
    print("Platform serving on %s:%d" % (host, port))
    server.serve_forever()
