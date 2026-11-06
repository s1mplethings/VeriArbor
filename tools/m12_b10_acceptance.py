"""Independent B10 FinalNavigationStartupDocs acceptance."""
import hashlib, json, os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

WS = Path(r"F:\CGKN-ITER-132\production-core-convergence-v1\promotion\run-05\candidate")
sys.path.insert(0, r"D:\VeriArbor_\tools")


def require(value, message):
    if not value:
        raise AssertionError(message)


def main():
    out = Path(tempfile.mkdtemp(prefix="m12-b10-"))
    data = out / "data"
    html = (WS / "main.py").read_text(encoding="utf8")
    subject = hashlib.sha256((WS / "main.py").read_bytes()).hexdigest()
    readme = (WS / "README.md").read_text(encoding="utf8")
    plan = (WS / "TEST_PLAN.md").read_text(encoding="utf8")
    test_source = (WS / "tests" / "test_promotion_gui.py").read_text(encoding="utf8")
    from m12_b01_acceptance import preflight
    pre = preflight(html, out)
    for label in ("Projects", "Signals", "Campaigns", "Content", "Schedule/Publish", "Receipts/Analytics", "Media"):
        require(label in html, "navigation label " + label)
    for token in ("--serve", "--port", "--data", "http://localhost", "Signals", "Reconcile", "Analytics history"):
        require(token in readme, "README missing " + token)
    for token in ("M12", "Signals", "Content", "Receipts/Analytics", "Schedule/Publish", "restart"):
        require(token in plan, "TEST_PLAN missing " + token)
    require("self.server.server_port" in test_source and "self.server.port" not in test_source, "server_port fixture")
    require((WS / "tests" / "test_promotion_gui.py").is_file(), "test suite file")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    log = (out / "server.log").open("wb")
    proc = subprocess.Popen([sys.executable, "-X", "utf8", str(WS / "main.py"), "--serve", "--port", str(port), "--data", str(data)],
                            cwd=WS, stdout=log, stderr=subprocess.STDOUT,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    result = {"kind": "B10FinalNavigationStartupDocsAcceptance", "block_id": "B10", "source_sha256": subject,
              "checks": [], "preflight": pre, "status": "FAIL"}
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
            status = page.request.post(url + "/api/action", data={"op": "product.status"}).json()
            require(status.get("status") == "ready" and "M12" in status.get("milestones", []), "product status")
            for label in ("Projects", "Signals", "Campaigns", "Content", "Schedule/Publish", "Receipts/Analytics", "Media"):
                page.get_by_role("button", name=label, exact=True).click()
                page.wait_for_timeout(250)
                require(page.locator(".view.active").count() == 1, "one active view for " + label)
                require(page.locator(".view.active").inner_text().strip() != "", "active view content for " + label)
            require(not errors, "no JavaScript errors: " + repr(errors))
            result["checks"] = ["HTML/JS parse and DOM ID uniqueness", "all navigation labels present",
                                "startup command/config/URL documented", "README describes current GUI workflows",
                                "TEST_PLAN covers M12 and restart", "server_port test fixture corrected",
                                "required test suite file exists", "product.status ready with M12",
                                "all seven views navigate with content", "no JavaScript errors"]
            result["status"] = "PASS"
            page.screenshot(path=str(out / "b10.png"), full_page=True)
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
        if browser:
            try: browser.close()
            except Exception: pass
    result["cleanup"] = {"server_stopped": proc.poll() is not None}
    (out / "receipt.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
