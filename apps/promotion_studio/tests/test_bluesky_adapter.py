"""Offline tests for the Bluesky adapter. No real network or credentials."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bluesky_adapter import (  # noqa: E402
    BlueskyAdapter,
    BlueskyHTTPError,
    BlueskyNetworkError,
    is_valid_rkey,
    make_rkey,
)


def _session(did="did:plc:alice", handle="alice.test", access="jwt-access"):
    return {
        "did": did,
        "handle": handle,
        "accessJwt": access,
        "refreshJwt": "jwt-refresh",
        "didDoc": {
            "service": [
                {
                    "id": "#atproto_pds",
                    "serviceEndpoint": "https://pds.test",
                }
            ]
        },
    }


def _record(text="hello", uri="at://did:plc:alice/app.bsky.feed.post/rkey1"):
    return {"uri": uri, "cid": "bafy-cid", "value": {"text": text}}


def _adapter(handler, dry_run=False, allow_publish=True, auth_check=False):
    adapter = BlueskyAdapter(
        handle="alice.test",
        app_password="super-secret-app-password",
        pds="https://pds.test",
        dry_run=dry_run,
        auth_check=auth_check,
        allow_publish=allow_publish,
    )
    adapter._http_json = handler
    return adapter


def test_tid_rkey_is_valid():
    rkey = make_rkey("idem-1")
    assert is_valid_rkey(rkey)
    assert len(rkey) == 13


def test_dry_run_never_calls_remote():
    calls = []

    def handler(*args, **kwargs):
        calls.append(args)
        raise AssertionError("remote call in dry-run")

    adapter = BlueskyAdapter(handle="alice.test", app_password="x", dry_run=True)
    adapter._http_json = handler
    result = adapter.publish("hello", make_rkey("dry"), publish_authorized=True)
    assert result["status"] == "DRY_RUN"
    assert calls == []


def test_auth_check_mode_logs_in_only():
    calls = []

    def handler(method, url, body=None, token=None):
        calls.append((method, url))
        if url.endswith("createSession"):
            return 200, _session()
        raise AssertionError("unexpected call: %s" % url)

    adapter = _adapter(handler, dry_run=True, auth_check=True)
    result = adapter.publish("hello", make_rkey("auth-check"), publish_authorized=True)
    assert result["status"] == "DRY_RUN"
    assert result["account_did"] == "did:plc:alice"
    assert len(calls) == 1


def test_live_requires_explicit_authorization():
    calls = []
    adapter = _adapter(lambda *a, **k: calls.append(a), allow_publish=False)
    result = adapter.publish("hello", make_rkey("blocked"), publish_authorized=True)
    assert result["status"] == "BLOCKED"
    assert calls == []


def test_live_publish_success_and_no_secrets_in_result():
    def handler(method, url, body=None, token=None):
        if url.endswith("createSession"):
            return 200, _session()
        if "getRecord" in url:
            raise BlueskyHTTPError(
                400, {"error": "RecordNotFound", "message": "Could not locate record"}
            )
        if url.endswith("createRecord"):
            return 200, {
                "uri": "at://did:plc:alice/app.bsky.feed.post/rkey1",
                "cid": "bafy-cid",
            }
        raise AssertionError(url)

    adapter = _adapter(handler)
    result = adapter.publish(
        "hello", make_rkey("live"), account_ref="alice.test", publish_authorized=True
    )
    assert result["status"] == "PUBLISHED"
    assert result["remote_id"].startswith("at://")
    assert result["cid"] == "bafy-cid"
    assert result["account_did"] == "did:plc:alice"
    assert "/post/" in result["url"]
    dumped = json.dumps(result)
    assert "super-secret-app-password" not in dumped
    assert "jwt-access" not in dumped
    assert "jwt-refresh" not in dumped


def test_remote_same_rkey_same_content_is_published():
    calls = []

    def handler(method, url, body=None, token=None):
        calls.append(url)
        if url.endswith("createSession"):
            return 200, _session()
        if "getRecord" in url:
            return 200, _record(text="hello")
        raise AssertionError("must not create a duplicate")

    result = _adapter(handler).publish(
        "hello", "234567abcdefg", publish_authorized=True
    )
    assert result["status"] == "PUBLISHED"
    assert not any("createRecord" in u for u in calls)


def test_remote_same_rkey_different_content_conflicts():
    def handler(method, url, body=None, token=None):
        if url.endswith("createSession"):
            return 200, _session()
        if "getRecord" in url:
            return 200, _record(text="different remote text")
        raise AssertionError("must not create")

    result = _adapter(handler).publish(
        "hello", "234567abcdefg", publish_authorized=True
    )
    assert result["status"] == "CONFLICT"
    assert "different content" in result["error"]


def test_create_race_same_rkey_is_resolved():
    state = {"get": 0}

    def handler(method, url, body=None, token=None):
        if url.endswith("createSession"):
            return 200, _session()
        if "getRecord" in url:
            state["get"] += 1
            if state["get"] == 1:
                raise BlueskyHTTPError(400, {"error": "RecordNotFound"})
            return 200, _record(text="hello")
        if url.endswith("createRecord"):
            raise BlueskyHTTPError(400, {"error": "RecordAlreadyExists"})
        raise AssertionError(url)

    result = _adapter(handler).publish(
        "hello", "234567abcdefg", publish_authorized=True
    )
    assert result["status"] == "PUBLISHED"


def test_429_maps_to_rate_limited():
    def handler(method, url, body=None, token=None):
        if url.endswith("createSession"):
            return 200, _session()
        if "getRecord" in url:
            raise BlueskyHTTPError(400, {"error": "RecordNotFound"})
        if url.endswith("createRecord"):
            raise BlueskyHTTPError(429, {"error": "RateLimitExceeded"})
        raise AssertionError(url)

    result = _adapter(handler).publish(
        "hello", "234567abcdefg", publish_authorized=True
    )
    assert result["status"] == "RATE_LIMITED"


def test_401_refreshes_once():
    calls = []

    def handler(method, url, body=None, token=None):
        calls.append((url, token))
        if url.endswith("createSession"):
            return 200, _session(access="access-1")
        if "getRecord" in url:
            raise BlueskyHTTPError(400, {"error": "RecordNotFound"})
        if url.endswith("refreshSession"):
            return 200, _session(access="access-2")
        if url.endswith("createRecord"):
            if token == "access-1":
                raise BlueskyHTTPError(401, {"error": "ExpiredToken"})
            return 200, {"uri": "at://did:plc:alice/app.bsky.feed.post/rkey1", "cid": "cid"}
        raise AssertionError(url)

    result = _adapter(handler).publish(
        "hello", "234567abcdefg", publish_authorized=True
    )
    assert result["status"] == "PUBLISHED"
    assert any("refreshSession" in u for u, _ in calls)


def test_5xx_and_network_errors_are_unknown():
    def handler_500(method, url, body=None, token=None):
        if url.endswith("createSession"):
            return 200, _session()
        if "getRecord" in url:
            raise BlueskyHTTPError(400, {"error": "RecordNotFound"})
        raise BlueskyHTTPError(503, {"error": "Unavailable"})

    result = _adapter(handler_500).publish(
        "hello", "234567abcdefg", publish_authorized=True
    )
    assert result["status"] == "UNKNOWN"

    def handler_net(method, url, body=None, token=None):
        if url.endswith("createSession"):
            raise BlueskyNetworkError("connection reset")
        raise AssertionError(url)

    result = _adapter(handler_net).publish(
        "hello", "234567abcdefg", publish_authorized=True
    )
    assert result["status"] == "UNKNOWN"


def test_text_too_long_is_rejected_without_remote_calls():
    calls = []
    adapter = _adapter(lambda *a, **k: calls.append(a))
    result = adapter.publish("x" * 301, "234567abcdefg", publish_authorized=True)
    assert result["status"] == "FAILED"
    assert "300" in result["error"]
    assert calls == []


def test_pds_is_learned_from_did_document():
    def handler(method, url, body=None, token=None):
        return 200, _session()

    adapter = _adapter(handler)
    adapter.login()
    assert adapter.did == "did:plc:alice"
    assert adapter.pds == "https://pds.test"


def test_reconcile_absent_same_and_conflict():
    def absent(method, url, body=None, token=None):
        if url.endswith("createSession"):
            return 200, _session()
        raise BlueskyHTTPError(400, {"error": "RecordNotFound"})

    result = _adapter(absent).reconcile("234567abcdefg", "hello")
    assert result["status"] == "ABSENT"

    def same(method, url, body=None, token=None):
        if url.endswith("createSession"):
            return 200, _session()
        return 200, _record(text="hello")

    result = _adapter(same).reconcile("234567abcdefg", "hello")
    assert result["status"] == "PUBLISHED"

    def different(method, url, body=None, token=None):
        if url.endswith("createSession"):
            return 200, _session()
        return 200, _record(text="other")

    result = _adapter(different).reconcile("234567abcdefg", "hello")
    assert result["status"] == "CONFLICT"
