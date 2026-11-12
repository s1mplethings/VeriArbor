"""Focused reliability tests for M7/M8, worker concurrency and Bluesky dry-run.

All tests use local servers/fake credentials only.
"""

import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import promotion_publish as pp  # noqa: E402
import scheduler_worker  # noqa: E402
from bluesky_adapter import is_valid_rkey  # noqa: E402

from importlib.util import module_from_spec, spec_from_file_location  # noqa: E402

M8_PATH = os.path.join(ROOT, "milestones", "milestone_989800776c3d6229e431", "api.py")
_spec = spec_from_file_location("m8_reliability", M8_PATH)
M8 = module_from_spec(_spec)
_spec.loader.exec_module(M8)


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def _seed(data_dir, text="hello", revision=1, status="APPROVED"):
    _write_json(
        os.path.join(data_dir, "projects.json"),
        [{"id": "p1", "name": "P"}],
    )
    _write_json(
        os.path.join(data_dir, "content.json"),
        [
            {
                "id": "c1",
                "project_id": "p1",
                "campaign_id": "camp1",
                "channel": "x",
                "text": text,
                "claim_ids": [],
                "media_ids": [],
                "revision": revision,
                "status": status,
                "revisions": [],
            }
        ],
    )


class Platform:
    def __init__(self, data_dir):
        os.makedirs(data_dir, exist_ok=True)
        self.port = _free_port()
        self.url = "http://127.0.0.1:%d" % self.port
        self.thread = threading.Thread(
            target=pp.serve_platform,
            args=("127.0.0.1", self.port, data_dir),
            daemon=True,
        )
        self.thread.start()
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.2):
                    return
            except OSError:
                time.sleep(0.02)
        raise RuntimeError("platform did not start")


@pytest.fixture()
def data_dir(tmp_path):
    d = str(tmp_path / "data")
    os.makedirs(d)
    return d


@pytest.fixture()
def platform(tmp_path):
    return Platform(str(tmp_path / "platform"))


def _create_schedule(data_dir, platform_url, key, when="2030-01-01T00:00:00+00:00", **extra):
    payload = {
        "op": "schedule.create",
        "project_id": "p1",
        "content_id": "c1",
        "platform_url": platform_url,
        "when": when,
        "idempotency_key": key,
    }
    payload.update(extra)
    return M8.handle(data_dir, payload)


def test_schedule_create_is_idempotent(data_dir):
    _seed(data_dir)
    first = _create_schedule(data_dir, "http://127.0.0.1:1", "same-key")
    second = _create_schedule(data_dir, "http://127.0.0.1:1", "same-key")
    assert first["id"] == second["id"]
    schedules = M8.handle(data_dir, {"op": "schedule.list", "project_id": "p1"})["items"]
    assert len(schedules) == 1
    assert schedules[0]["content_snapshot"]["revision"] == 1


def test_schedule_create_conflicts_on_changed_content(data_dir):
    _seed(data_dir)
    _create_schedule(data_dir, "http://127.0.0.1:1", "conflict-key")
    _seed(data_dir, text="edited", revision=2)
    with pytest.raises(ValueError) as exc:
        _create_schedule(data_dir, "http://127.0.0.1:1", "conflict-key")
    assert "idempotency conflict" in str(exc.value)


def test_schedule_create_conflicts_on_changed_when(data_dir):
    _seed(data_dir)
    _create_schedule(data_dir, "http://127.0.0.1:1", "when-key")
    with pytest.raises(ValueError) as exc:
        _create_schedule(
            data_dir,
            "http://127.0.0.1:1",
            "when-key",
            when="2030-01-02T00:00:00+00:00",
        )
    assert "idempotency conflict" in str(exc.value)


def test_schedule_create_conflicts_on_changed_account(data_dir):
    _seed(data_dir)
    _create_schedule(data_dir, "bluesky://bsky.social", "account-key", account="alice")
    with pytest.raises(ValueError) as exc:
        _create_schedule(data_dir, "bluesky://bsky.social", "account-key", account="bob")
    assert "idempotency conflict" in str(exc.value)


def test_run_due_blocks_content_changed_after_scheduling(data_dir, platform):
    _seed(data_dir)
    _create_schedule(
        data_dir,
        platform.url,
        "changed-content-key",
        when="2029-01-01T00:00:00+00:00",
    )
    _seed(data_dir, text="edited after scheduling", revision=2)
    result = M8.handle(data_dir, {
        "op": "schedule.run_due",
        "project_id": "p1",
        "now": "2030-01-01T00:00:00+00:00",
    })
    assert result["items"][0]["status"] == "FAILED"
    assert result["items"][0]["result_status"] == "CONFLICT"
    platform_data = os.path.join(os.path.dirname(data_dir), "platform")
    pubs = pp._load_list(platform_data, "publications.json")
    assert len([p for p in pubs if p["idempotency_key"] == "changed-content-key"]) == 0


def _seed_receipt(data_dir, key, status, send_started=True):
    receipt = {
        "id": "receipt-" + key,
        "project_id": "p1",
        "content_id": "c1",
        "revision": 1,
        "channel": "x",
        "text": "hello",
        "status": status,
        "remote_id": None,
        "idempotency_key": key,
        "request_ref": None,
        "response_ref": None,
        "attempts": [],
        "url": None,
        "send_started_at": time.time() if send_started else None,
    }
    _write_json(os.path.join(data_dir, "receipts.json"), [receipt])
    return receipt


def test_crash_before_send_can_safely_send(data_dir, platform):
    _seed(data_dir)
    _seed_receipt(data_dir, "crash-before", "PENDING", send_started=False)
    receipt = pp.handle(data_dir, {
        "op": "publish.send",
        "project_id": "p1",
        "content_id": "c1",
        "platform_url": platform.url,
        "idempotency_key": "crash-before",
    })
    assert receipt["status"] == "PUBLISHED"
    assert receipt["remote_id"]
    platform_data = os.path.join(os.path.dirname(data_dir), "platform")
    pubs = pp._load_list(platform_data, "publications.json")
    assert len([p for p in pubs if p["idempotency_key"] == "crash-before"]) == 1


def test_response_lost_reconciles_without_resend(data_dir, platform):
    _seed(data_dir)
    # Remote publication exists, but the local response was lost.
    payload = json.dumps({
        "idempotency_key": "lost-response",
        "project_id": "p1",
        "content_id": "c1",
        "revision": 1,
        "channel": "x",
        "text": "hello",
    }).encode("utf-8")
    req = urllib.request.Request(
        platform.url + "/publish",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        remote = json.loads(resp.read().decode("utf-8"))

    _seed_receipt(data_dir, "lost-response", "PENDING", send_started=True)
    receipt = pp.handle(data_dir, {
        "op": "publish.send",
        "project_id": "p1",
        "content_id": "c1",
        "platform_url": platform.url,
        "idempotency_key": "lost-response",
    })
    assert receipt["status"] == "PUBLISHED"
    assert receipt["remote_id"] == remote["remote_id"]

    platform_data = os.path.join(os.path.dirname(data_dir), "platform")
    pubs = pp._load_list(platform_data, "publications.json")
    assert len([p for p in pubs if p["idempotency_key"] == "lost-response"]) == 1


def test_pending_absent_stays_unknown_and_is_not_resent(data_dir, platform):
    _seed(data_dir)
    _seed_receipt(data_dir, "lost-none", "PENDING", send_started=True)
    first = pp.handle(data_dir, {
        "op": "publish.send",
        "project_id": "p1",
        "content_id": "c1",
        "platform_url": platform.url,
        "idempotency_key": "lost-none",
    })
    assert first["status"] == "UNKNOWN"
    second = pp.handle(data_dir, {
        "op": "publish.send",
        "project_id": "p1",
        "content_id": "c1",
        "platform_url": platform.url,
        "idempotency_key": "lost-none",
    })
    assert second["status"] == "UNKNOWN"
    platform_data = os.path.join(os.path.dirname(data_dir), "platform")
    pubs = pp._load_list(platform_data, "publications.json")
    assert len([p for p in pubs if p["idempotency_key"] == "lost-none"]) == 0


def test_manual_retry_of_unknown_reconciles_then_sends(data_dir, platform):
    _seed(data_dir)
    _seed_receipt(data_dir, "unknown-manual", "UNKNOWN", send_started=True)
    receipt = pp.handle(data_dir, {
        "op": "publish.retry",
        "project_id": "p1",
        "receipt_id": "receipt-unknown-manual",
        "platform_url": platform.url,
    })
    assert receipt["status"] == "PUBLISHED"
    platform_data = os.path.join(os.path.dirname(data_dir), "platform")
    pubs = pp._load_list(platform_data, "publications.json")
    assert len([p for p in pubs if p["idempotency_key"] == "unknown-manual"]) == 1


def test_bluesky_dry_run_persists_stable_rkey(data_dir, monkeypatch):
    _seed(data_dir)
    monkeypatch.setenv("BLUESKY_DRY_RUN", "1")
    monkeypatch.setenv("BLUESKY_HANDLE", "alice.test")
    req = {
        "op": "publish.send",
        "project_id": "p1",
        "content_id": "c1",
        "platform_url": "bluesky://bsky.social",
        "idempotency_key": "bsky-dry-key",
    }
    first = pp.handle(data_dir, req)
    second = pp.handle(data_dir, req)
    assert first["status"] == "DRY_RUN"
    assert first["id"] == second["id"]
    assert is_valid_rkey(first["remote_key"])
    assert first["remote_key"] == second["remote_key"]
    assert first["target"]["account"] == "alice.test"
    assert first["content_snapshot"]["revision"] == 1
    stored = pp._load_list(data_dir, "receipts.json")[0]
    assert stored["remote_key"] == first["remote_key"]
    assert "super-secret" not in json.dumps(first)
    assert "jwt" not in json.dumps(first).lower()


def test_bluesky_live_requires_authorization(data_dir, monkeypatch):
    _seed(data_dir)
    monkeypatch.setenv("BLUESKY_DRY_RUN", "0")
    monkeypatch.setenv("BLUESKY_ALLOW_PUBLISH", "0")
    monkeypatch.setenv("BLUESKY_HANDLE", "alice.test")
    monkeypatch.setenv("BLUESKY_APP_PASSWORD", "fake-app-password")
    receipt = pp.handle(data_dir, {
        "op": "publish.send",
        "project_id": "p1",
        "content_id": "c1",
        "platform_url": "bluesky://bsky.social",
        "idempotency_key": "bsky-blocked",
        "publish_authorized": True,
    })
    assert receipt["status"] == "BLOCKED"
    assert is_valid_rkey(receipt["remote_key"])


def test_two_workers_publish_only_once(data_dir, platform):
    _seed(data_dir)
    _create_schedule(
        data_dir,
        platform.url,
        "worker-key",
        when="2029-01-01T00:00:00+00:00",
    )
    cmd = [
        sys.executable,
        os.path.join(ROOT, "scheduler_worker.py"),
        "--once",
        "--data",
        data_dir,
        "--now",
        "2030-01-01T00:00:00+00:00",
    ]
    p1 = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p2 = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out1, err1 = p1.communicate(timeout=30)
    out2, err2 = p2.communicate(timeout=30)
    assert p1.returncode == 0, (out1, err1)
    assert p2.returncode == 0, (out2, err2)

    platform_data = os.path.join(os.path.dirname(data_dir), "platform")
    pubs = pp._load_list(platform_data, "publications.json")
    assert len([p for p in pubs if p["idempotency_key"] == "worker-key"]) == 1
    receipts = pp._load_list(data_dir, "receipts.json")
    assert len([r for r in receipts if r["idempotency_key"] == "worker-key"]) == 1
    schedules = M8.handle(data_dir, {"op": "schedule.list", "project_id": "p1"})["items"]
    assert schedules[0]["status"] == "PUBLISHED"
