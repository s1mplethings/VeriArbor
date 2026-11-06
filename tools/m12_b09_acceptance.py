"""Independent B09 AnalyticsHistory browser acceptance."""
import hashlib, json, os, socket, subprocess, sys, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

WS = Path(r"F:\CGKN-ITER-132\production-core-convergence-v1\promotion\run-05\candidate")


def require(value, message):
    if not value:
        raise AssertionError(message)


class Platform(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length).decode("utf8"))
        key = payload["idempotency_key"]
        remote_id = "remote-" + key[:12]
        raw = json.dumps({"id": remote_id, "remote_id": remote_id,
                          "url": "http://127.0.0.1:%d/publications/%s" % (self.server.server_port, remote_id)}).encode("utf8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path.startswith("/metrics"):
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            remote_id = query.get("remote_id", [""])[0]
            raw = json.dumps({"remote_id": remote_id, "views": 11, "impressions": 23, "reactions": 3, "comments": 2}).encode("utf8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        self.send_response(404)
        self.end_headers()


def main():
    out = Path(tempfile.mkdtemp(prefix="m12-b09-"))
    data = out / "data"
    subject = hashlib.sha256((WS / "main.py").read_bytes()).hexdigest()
    platform = ThreadingHTTPServer(("127.0.0.1", 0), Platform)
    threading.Thread(target=platform.serve_forever, daemon=True).start()
    platform_url = "http://127.0.0.1:%d" % platform.server_port
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    log = (out / "server.log").open("wb")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.Popen([sys.executable, "-X", "utf8", str(WS / "main.py"), "--serve", "--port", str(port), "--data", str(data)],
                            cwd=WS, stdout=log, stderr=subprocess.STDOUT, env=env)
    result = {"kind": "B09AnalyticsHistoryAcceptance", "block_id": "B09", "source_sha256": subject,
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
            page.get_by_label("Project name", exact=True).fill("B09 Project")
            page.get_by_role("button", name="Create project", exact=True).click()
            page.wait_for_timeout(400)
            pid = page.evaluate("currentProjectId")
            page.get_by_role("button", name="Campaigns", exact=True).click()
            page.get_by_label("Campaign name", exact=True).fill("B09 Campaign")
            page.get_by_label("Audience", exact=True).fill("Dev")
            page.get_by_label("Channels", exact=True).fill("alpha")
            page.get_by_role("button", name="Create campaign", exact=True).click()
            page.wait_for_timeout(500)
            source = out / "evidence"; source.mkdir(); (source / "README.md").write_text("Analytics facts.\n", encoding="utf8")
            ev = page.request.post(url + "/api/action", data={"milestone":"M2","op":"evidence.import","project_id":pid,"path":str(source)}).json()
            page.request.post(url + "/api/action", data={"milestone":"M3","op":"claim.create","project_id":pid,"text":"Analytics facts.","evidence_ids":[ev["id"]]})
            page.get_by_role("button", name="Content", exact=True).click()
            page.wait_for_timeout(600)
            page.get_by_label("Content text", exact=True).fill("Analytics copy")
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
            receipts = page.request.post(url + "/api/action", data={"milestone":"M9","op":"receipt.list","project_id":pid}).json()["items"]
            require(len(receipts) == 1 and receipts[0]["status"] == "PUBLISHED", "published receipt")
            rid = receipts[0]["id"]
            page.get_by_role("button", name="Receipts/Analytics", exact=True).click()
            page.wait_for_timeout(700)
            page.select_option("#rec-receipt-select", rid)
            page.wait_for_timeout(400)
            page.get_by_role("button", name="Analytics history", exact=True).click()
            page.wait_for_timeout(500)
            require("No analytics history" in page.locator("#analytics-history").inner_text(), "empty history state")
            page.get_by_role("button", name="Fetch analytics", exact=True).click()
            page.wait_for_timeout(700)
            analytics = page.locator("#analytics-result").inner_text()
            print("DEBUG analytics-result:", analytics)
            print("DEBUG rec-error:", page.locator("#rec-error").inner_text())
            print("DEBUG receipt select:", page.eval_on_selector("#rec-receipt-select", "e=>e.value"))
            print("DEBUG platform inputs:", page.evaluate("({content: document.getElementById('content-platform-url').value, schedule: document.getElementById('platform-url').value, receipt: m12ReceiptPlatformUrl})"))
            require("Local/synthetic" in analytics and "\"views\": 11" in analytics, "metrics fetched")
            require(rid in page.locator("#analytics-result").inner_text() or rid in page.locator("#receipt-detail").inner_text(), "receipt identity binding")
            page.get_by_role("button", name="Analytics history", exact=True).click()
            page.wait_for_timeout(500)
            history = page.locator("#analytics-history").inner_text()
            require("views 11" in history and "impressions 23" in history, "history metrics visible")
            require("T" in history and ("+" in history or "Z" in history), "fetched_at visible")
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
            page.select_option("#rec-receipt-select", rid)
            page.wait_for_timeout(400)
            page.get_by_role("button", name="Analytics history", exact=True).click()
            page.wait_for_timeout(500)
            require("views 11" in page.locator("#analytics-history").inner_text(), "history persists after restart")
            require(not errors, "no JavaScript errors: " + repr(errors))
            result["checks"] = ["published receipt exists", "empty analytics history state", "metrics fetched from local platform",
                                "local/synthetic label", "receipt identity binding", "history metrics visible",
                                "fetched_at visible", "history persists after restart", "no JavaScript errors"]
            result["status"] = "PASS"
            page.screenshot(path=str(out / "b09.png"), full_page=True)
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
