"""Independent B08 ReceiptUnknownReconcile browser acceptance."""
import hashlib, json, os, socket, subprocess, sys, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

WS = Path(r"F:\CGKN-ITER-132\production-core-convergence-v1\promotion\run-05\candidate")


def require(value, message):
    if not value:
        raise AssertionError(message)


class MockPlatform(BaseHTTPRequestHandler):
    attempts = {}
    records = {}

    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length).decode("utf8"))
        key = payload["idempotency_key"]
        self.attempts[key] = self.attempts.get(key, 0) + 1
        if self.attempts[key] == 1:
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return
        remote_id = "remote-" + key[:12]
        self.records[key] = {"id": remote_id, "remote_id": remote_id,
                             "url": "http://127.0.0.1:%d/publications/%s" % (self.server.server_port, remote_id)}
        raw = json.dumps(self.records[key]).encode("utf8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path.startswith("/publications"):
            key = self.path.split("key=", 1)[1] if "key=" in self.path else ""
            if key in self.records:
                raw = json.dumps(self.records[key]).encode("utf8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            else:
                self.send_response(404)
                self.end_headers()
            return
        self.send_response(404)
        self.end_headers()


def main():
    out = Path(tempfile.mkdtemp(prefix="m12-b08-"))
    data = out / "data"
    subject = hashlib.sha256((WS / "main.py").read_bytes()).hexdigest()
    platform = ThreadingHTTPServer(("127.0.0.1", 0), MockPlatform)
    threading.Thread(target=platform.serve_forever, daemon=True).start()
    platform_url = "http://127.0.0.1:%d" % platform.server_port
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    log = (out / "server.log").open("wb")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.Popen([sys.executable, "-X", "utf8", str(WS / "main.py"), "--serve", "--port", str(port), "--data", str(data)],
                            cwd=WS, stdout=log, stderr=subprocess.STDOUT, env=env)
    result = {"kind": "B08ReceiptUnknownReconcileAcceptance", "block_id": "B08", "source_sha256": subject,
              "checks": [], "status": "FAIL"}
    page = None; browser = None
    try:
        for _ in range(100):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=.2):
                    break
            except OSError:
                time.sleep(.1)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page(); page.set_default_timeout(10000)
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(url, wait_until="networkidle")
            page.get_by_label("Project name", exact=True).fill("B08 Project")
            page.get_by_role("button", name="Create project", exact=True).click()
            page.wait_for_timeout(400)
            pid = page.evaluate("currentProjectId")
            page.get_by_role("button", name="Campaigns", exact=True).click()
            page.get_by_label("Campaign name", exact=True).fill("B08 Campaign")
            page.get_by_label("Audience", exact=True).fill("Dev")
            page.get_by_label("Channels", exact=True).fill("alpha")
            page.get_by_role("button", name="Create campaign", exact=True).click()
            page.wait_for_timeout(500)
            source = out / "evidence"; source.mkdir(); (source / "README.md").write_text("Receipt facts.\n", encoding="utf8")
            ev = page.request.post(url + "/api/action", data={"milestone":"M2","op":"evidence.import","project_id":pid,"path":str(source)}).json()
            page.request.post(url + "/api/action", data={"milestone":"M3","op":"claim.create","project_id":pid,"text":"Receipt facts.","evidence_ids":[ev["id"]]})

            def create_approved(text):
                page.get_by_role("button", name="Content", exact=True).click()
                page.wait_for_timeout(600)
                page.get_by_role("button", name="New content", exact=True).click()
                page.wait_for_timeout(200)
                page.get_by_label("Content text", exact=True).fill(text)
                page.get_by_label("Channel", exact=True).select_option("alpha")
                page.get_by_role("button", name="Save content", exact=True).click()
                page.wait_for_timeout(600)
                page.get_by_role("button", name="Review", exact=True).click()
                page.wait_for_timeout(500)
                page.get_by_role("button", name="Approve", exact=True).click()
                page.wait_for_timeout(500)
                page.get_by_label("Platform URL", exact=True).filter(visible=True).fill(platform_url)
                page.get_by_role("button", name="Publish", exact=True).first.click()
                page.wait_for_timeout(800)
                rows = page.request.post(url + "/api/action", data={"milestone":"M9","op":"receipt.list","project_id":pid}).json()["items"]
                require(bool(rows), "receipt created")
                return rows[-1]

            first = create_approved("UNKNOWN receipt one")
            require(first["status"] == "UNKNOWN", "first receipt UNKNOWN")
            page.get_by_role("button", name="Receipts/Analytics", exact=True).click()
            page.wait_for_timeout(700)
            require("UNKNOWN" in page.locator("#receipts-list").inner_text(), "UNKNOWN receipt visible")
            page.select_option("#rec-receipt-select", first["id"])
            page.wait_for_timeout(500)
            require(first["id"] in page.locator("#receipt-detail").inner_text(), "receipt detail visible")
            page.get_by_role("button", name="Reconcile", exact=True).click()
            page.wait_for_timeout(700)
            reconciled = page.request.post(url + "/api/action", data={"milestone":"M9","op":"receipt.get","project_id":pid,"receipt_id":first["id"]}).json()
            require(reconciled["status"] == "ABSENT", "reconcile absent")
            page.get_by_role("button", name="Retry", exact=True).click()
            page.wait_for_timeout(800)
            retried = page.request.post(url + "/api/action", data={"milestone":"M9","op":"receipt.get","project_id":pid,"receipt_id":first["id"]}).json()
            require(retried["status"] == "PUBLISHED", "retry published after reconcile")
            require(any(a.get("operation") == "POST_RETRY" and a.get("status") == "SUCCESS" for a in retried.get("attempts", [])), "retry lineage")
            require(any(a.get("operation") == "GET_RECONCILE" for a in retried.get("attempts", [])), "reconcile lineage")

            second = create_approved("UNKNOWN receipt two")
            require(second["status"] == "UNKNOWN", "second receipt UNKNOWN")
            page.get_by_role("button", name="Receipts/Analytics", exact=True).click()
            page.wait_for_timeout(700)
            page.select_option("#rec-receipt-select", second["id"])
            page.wait_for_timeout(500)
            page.get_by_role("button", name="Retry", exact=True).click()
            page.wait_for_timeout(500)
            require("explicit retry confirmation" in page.locator("#rec-error").inner_text().lower(), "blind UNKNOWN retry blocked")
            still = page.request.post(url + "/api/action", data={"milestone":"M9","op":"receipt.get","project_id":pid,"receipt_id":second["id"]}).json()
            require(still["status"] == "UNKNOWN", "blind retry did not send")
            page.check("#explicit-unknown-retry")
            page.get_by_role("button", name="Retry", exact=True).click()
            page.wait_for_timeout(800)
            second_done = page.request.post(url + "/api/action", data={"milestone":"M9","op":"receipt.get","project_id":pid,"receipt_id":second["id"]}).json()
            require(second_done["status"] == "PUBLISHED", "explicit UNKNOWN retry")
            # Restart persistence.
            proc.terminate(); proc.wait(timeout=5)
            proc = subprocess.Popen([sys.executable, "-X", "utf8", str(WS / "main.py"), "--serve", "--port", str(port), "--data", str(data)],
                                    cwd=WS, stdout=log, stderr=subprocess.STDOUT, env=env)
            for _ in range(100):
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=.2):
                        break
                except OSError:
                    time.sleep(.1)
            page.reload(wait_until="networkidle")
            page.get_by_role("button", name="Receipts/Analytics", exact=True).click()
            page.wait_for_timeout(700)
            require("PUBLISHED" in page.locator("#receipts-list").inner_text(), "receipts persist after restart")
            require(not errors, "no JavaScript errors: " + repr(errors))
            result["checks"] = ["UNKNOWN receipt visible", "receipt detail visible", "reconcile to ABSENT",
                                "retry after reconcile published", "retry/reconcile lineage retained",
                                "blind UNKNOWN retry blocked", "explicit UNKNOWN retry published",
                                "receipts persist after restart", "no JavaScript errors"]
            result["status"] = "PASS"
            page.screenshot(path=str(out / "b08.png"), full_page=True)
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
        try: page.screenshot(path=str(out / "failure.png"), full_page=True)
        except Exception: pass
    finally:
        try:
            proc.terminate(); proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait(timeout=5)
        log.close()
        platform.shutdown(); platform.server_close()
        if browser:
            try: browser.close()
            except Exception: pass
    result["cleanup"] = {"server_stopped": proc.poll() is not None}
    (out / "receipt.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
