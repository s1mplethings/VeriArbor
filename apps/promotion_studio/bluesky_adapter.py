"""Minimal Bluesky (AT Protocol) text-only publishing adapter.

Safety defaults:
  BLUESKY_DRY_RUN=1          no remote calls (default)
  BLUESKY_AUTH_CHECK=1       optional login-only check while dry-run is on
  BLUESKY_ALLOW_PUBLISH=1    required, together with publish_authorized=True,
                             before createRecord is ever called

Credentials are read only from environment variables. Tokens, app passwords
and Authorization headers are never logged or stored in receipts.
"""

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

MILESTONE_ID = "BLUESKY"
COLLECTION = "app.bsky.feed.post"
MAX_TEXT = 300  # Bluesky app-level text limit (conservative code-point check)
TID_ALPHABET = "234567abcdefghijklmnopqrstuvwxyz"


class BlueskyConfigError(Exception):
    pass


class BlueskyHTTPError(Exception):
    def __init__(self, status, payload=None, retry_after=None):
        self.status = status
        self.payload = payload or {}
        self.retry_after = retry_after
        error = self.payload.get("error") or ""
        message = self.payload.get("message") or ""
        super().__init__("HTTP %s %s %s" % (status, error, message))


class BlueskyNetworkError(Exception):
    pass


class AccountMismatch(Exception):
    pass


def tid_encode(value):
    """Encode a 64-bit value as a 13-character AT Protocol TID."""
    chars = []
    for _ in range(13):
        chars.append(TID_ALPHABET[value & 0x1F])
        value >>= 5
    return "".join(reversed(chars))


def make_rkey(idempotency_key):
    """Create a valid TID-shaped rkey. Persist it before the first send."""
    now_us = int(time.time() * 1_000_000)
    clock = int.from_bytes(
        hashlib.sha256(idempotency_key.encode("utf-8")).digest()[:2], "big"
    ) & 0x3FF
    value = ((now_us & ((1 << 53) - 1)) << 10) | clock
    return tid_encode(value)


def is_valid_rkey(value):
    return (
        isinstance(value, str)
        and len(value) == 13
        and all(c in TID_ALPHABET for c in value)
    )


def remote_url(did, rkey):
    return "https://bsky.app/profile/%s/post/%s" % (
        urllib.parse.quote(did, safe=":"),
        urllib.parse.quote(rkey, safe=""),
    )


def _result(status, **extra):
    data = {
        "status": status,
        "remote_id": None,
        "cid": None,
        "url": None,
        "account_did": None,
        "remote_key": None,
        "response": None,
        "error": None,
        "retry_after": None,
    }
    data.update(extra)
    return data


class BlueskyAdapter:
    def __init__(
        self,
        handle=None,
        app_password=None,
        pds="https://bsky.social",
        dry_run=True,
        auth_check=False,
        allow_publish=False,
        timeout=15,
    ):
        self.handle = handle
        self.app_password = app_password
        self.pds = (pds or "https://bsky.social").rstrip("/")
        self.dry_run = bool(dry_run)
        self.auth_check = bool(auth_check)
        self.allow_publish = bool(allow_publish)
        self.timeout = timeout
        self.did = None
        self.access_jwt = None
        self.refresh_jwt = None

    @classmethod
    def from_env(cls):
        return cls(
            handle=os.environ.get("BLUESKY_HANDLE"),
            app_password=os.environ.get("BLUESKY_APP_PASSWORD"),
            pds=os.environ.get("BLUESKY_PDS", "https://bsky.social"),
            dry_run=os.environ.get("BLUESKY_DRY_RUN", "1") != "0",
            auth_check=os.environ.get("BLUESKY_AUTH_CHECK", "0") == "1",
            allow_publish=os.environ.get("BLUESKY_ALLOW_PUBLISH", "0") == "1",
        )

    # -- transport -----------------------------------------------------
    def _http_json(self, method, url, body=None, token=None):
        data = None
        headers = {"Content-Type": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        if token:
            headers["Authorization"] = "Bearer " + token
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                return resp.getcode(), (json.loads(raw) if raw else {})
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            try:
                payload = json.loads(raw) if raw else {}
            except ValueError:
                payload = {}
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            raise BlueskyHTTPError(exc.code, payload, retry_after)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            # Never include request headers here (they can contain JWTs).
            raise BlueskyNetworkError(str(exc))

    # -- session -------------------------------------------------------
    def _remember_session(self, payload):
        self.did = payload.get("did") or self.did
        self.handle = payload.get("handle") or self.handle
        self.access_jwt = payload.get("accessJwt") or self.access_jwt
        self.refresh_jwt = payload.get("refreshJwt") or self.refresh_jwt
        did_doc = payload.get("didDoc") or {}
        for service in did_doc.get("service") or []:
            if str(service.get("id", "")).endswith("#atproto_pds"):
                endpoint = service.get("serviceEndpoint")
                if endpoint:
                    self.pds = endpoint.rstrip("/")

    def login(self):
        if not self.handle or not self.app_password:
            raise BlueskyConfigError(
                "BLUESKY_HANDLE and BLUESKY_APP_PASSWORD are required"
            )
        _, payload = self._http_json(
            "POST",
            self.pds + "/xrpc/com.atproto.server.createSession",
            body={"identifier": self.handle, "password": self.app_password},
        )
        if not payload.get("accessJwt") or not payload.get("did"):
            raise BlueskyConfigError("createSession response missing accessJwt/did")
        self._remember_session(payload)
        return payload

    def refresh(self):
        if not self.refresh_jwt:
            raise BlueskyConfigError("no refresh token")
        _, payload = self._http_json(
            "POST",
            self.pds + "/xrpc/com.atproto.server.refreshSession",
            token=self.refresh_jwt,
        )
        self._remember_session(payload)
        return payload

    def _ensure_session(self):
        if not self.access_jwt:
            self.login()

    def _authed(self, method, endpoint, body=None):
        self._ensure_session()
        try:
            return self._http_json(
                method, self.pds + endpoint, body=body, token=self.access_jwt
            )
        except BlueskyHTTPError as exc:
            if exc.status != 401:
                raise
            self.refresh()
            return self._http_json(
                method, self.pds + endpoint, body=body, token=self.access_jwt
            )

    def verify_account(self, account_ref):
        if not account_ref:
            return
        ref = str(account_ref).strip().lstrip("@").lower()
        did = (self.did or "").lower()
        handle = (self.handle or "").lower()
        if ref not in (did, handle):
            raise AccountMismatch(
                "target account mismatch: configured session is %s, requested %s"
                % (self.handle or self.did, account_ref)
            )

    # -- records -------------------------------------------------------
    def get_record(self, rkey):
        query = urllib.parse.urlencode(
            {
                "repo": self.did,
                "collection": COLLECTION,
                "rkey": rkey,
            }
        )
        try:
            _, payload = self._authed(
                "GET", "/xrpc/com.atproto.repo.getRecord?" + query
            )
            return payload
        except BlueskyHTTPError as exc:
            name = str(exc.payload.get("error", "")).lower()
            message = str(exc.payload.get("message", "")).lower()
            if exc.status == 400 and (
                "recordnotfound" in name
                or "could not locate record" in message
                or "not found" in message
            ):
                return None
            raise

    def create_record(self, text, rkey):
        body = {
            "repo": self.did,
            "collection": COLLECTION,
            "rkey": rkey,
            "record": {
                "$type": COLLECTION,
                "text": text,
                "createdAt": datetime.now(timezone.utc)
                .isoformat(timespec="seconds")
                .replace("+00:00", "Z"),
            },
        }
        _, payload = self._authed(
            "POST", "/xrpc/com.atproto.repo.createRecord", body=body
        )
        if not payload.get("uri") or not payload.get("cid"):
            raise BlueskyConfigError("createRecord response missing uri/cid")
        return payload

    def _published(self, record, text, rkey):
        value = record.get("value") or {}
        remote_text = value.get("text")
        uri = record.get("uri")
        cid = record.get("cid")
        if remote_text != text:
            return _result(
                "CONFLICT",
                remote_id=uri,
                cid=cid,
                url=remote_url(self.did, rkey),
                account_did=self.did,
                remote_key=rkey,
                response={"uri": uri, "cid": cid},
                error="remote record exists with different content",
            )
        return _result(
            "PUBLISHED",
            remote_id=uri or ("at://%s/%s/%s" % (self.did, COLLECTION, rkey)),
            cid=cid,
            url=remote_url(self.did, rkey),
            account_did=self.did,
            remote_key=rkey,
            response={"uri": uri, "cid": cid},
        )

    # -- public operations --------------------------------------------
    def validate_text(self, text):
        if not isinstance(text, str) or not text.strip():
            return "text must be a non-empty string"
        if len(text) > MAX_TEXT:
            return "text exceeds %d characters" % MAX_TEXT
        if "\x00" in text:
            return "text contains a NUL character"
        return None

    def auth_check_only(self):
        """Explicit login-only check; no record is created."""
        try:
            self.login()
            return _result(
                "DRY_RUN",
                account_did=self.did,
                response={"account": self.handle, "did": self.did},
            )
        except (BlueskyConfigError, BlueskyHTTPError, BlueskyNetworkError) as exc:
            return _result("FAILED", error=str(exc))

    def publish(self, text, rkey, account_ref=None, publish_authorized=False):
        problem = self.validate_text(text)
        if problem:
            return _result("FAILED", error=problem, remote_key=rkey)
        if not is_valid_rkey(rkey):
            return _result("FAILED", error="invalid rkey", remote_key=rkey)

        if self.dry_run:
            if self.auth_check:
                result = self.auth_check_only()
                result["remote_key"] = rkey
                return result
            return _result(
                "DRY_RUN",
                remote_key=rkey,
                response={"dry_run": True, "remote_calls": 0},
            )

        if not (publish_authorized and self.allow_publish):
            return _result(
                "BLOCKED",
                remote_key=rkey,
                error="real publishing is not authorized (publish_authorized + BLUESKY_ALLOW_PUBLISH)",
            )

        try:
            self.login()
            self.verify_account(account_ref)
            existing = self.get_record(rkey)
            if existing:
                return self._published(existing, text, rkey)
            try:
                created = self.create_record(text, rkey)
            except BlueskyHTTPError as exc:
                # A concurrent writer may have created the same rkey between
                # our preflight GET and createRecord. Resolve it explicitly.
                if exc.status == 400:
                    existing = self.get_record(rkey)
                    if existing:
                        return self._published(existing, text, rkey)
                raise
            return _result(
                "PUBLISHED",
                remote_id=created["uri"],
                cid=created["cid"],
                url=remote_url(self.did, rkey),
                account_did=self.did,
                remote_key=rkey,
                response={"uri": created["uri"], "cid": created["cid"]},
            )
        except AccountMismatch as exc:
            return _result("CONFLICT", remote_key=rkey, error=str(exc))
        except BlueskyHTTPError as exc:
            if exc.status == 429:
                return _result(
                    "RATE_LIMITED",
                    remote_key=rkey,
                    error=str(exc),
                    retry_after=exc.retry_after,
                )
            if exc.status == 401:
                return _result(
                    "FAILED",
                    remote_key=rkey,
                    error="authentication failed after refresh",
                )
            if 500 <= exc.status <= 599:
                return _result("UNKNOWN", remote_key=rkey, error=str(exc))
            return _result("FAILED", remote_key=rkey, error=str(exc))
        except (BlueskyConfigError, BlueskyNetworkError, TimeoutError, OSError) as exc:
            return _result("UNKNOWN", remote_key=rkey, error=str(exc))

    def reconcile(self, rkey, expected_text, account_did=None, account_ref=None):
        if not rkey:
            return _result("UNKNOWN", error="missing rkey")
        if self.dry_run:
            return _result(
                "UNKNOWN", remote_key=rkey, error="cannot reconcile while dry-run is enabled"
            )
        try:
            self.login()
            ref = account_did or account_ref
            self.verify_account(ref)
            record = self.get_record(rkey)
            if record is None:
                return _result("ABSENT", remote_key=rkey, account_did=self.did)
            return self._published(record, expected_text, rkey)
        except AccountMismatch as exc:
            return _result("CONFLICT", remote_key=rkey, account_did=self.did, error=str(exc))
        except BlueskyHTTPError as exc:
            if 500 <= exc.status <= 599:
                return _result("UNKNOWN", remote_key=rkey, error=str(exc))
            return _result("UNKNOWN", remote_key=rkey, error=str(exc))
        except (BlueskyConfigError, BlueskyNetworkError, TimeoutError, OSError) as exc:
            return _result("UNKNOWN", remote_key=rkey, error=str(exc))


def is_bluesky_platform(platform_url):
    if not isinstance(platform_url, str):
        return False
    return platform_url.strip().lower().startswith("bluesky://")
