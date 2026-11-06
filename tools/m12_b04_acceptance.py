"""Independent B04 ContentRevisionCompare browser acceptance."""
import hashlib, json, os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

WS = Path(r"F:\CGKN-ITER-132\production-core-convergence-v1\promotion\run-05\candidate")


def require(value, message):
    if not value:
        raise AssertionError(message)


def main():
    out = Path(tempfile.mkdtemp(prefix="m12-b04-"))
    data = out / "data"
    subject = hashlib.sha256((WS / "main.py").read_bytes()).hexdigest()
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    log = (out / "server.log").open("wb")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.Popen([sys.executable, "-X", "utf8", str(WS / "main.py"), "--serve", "--port", str(port), "--data", str(data)],
                            cwd=WS, stdout=log, stderr=subprocess.STDOUT, env=env)
    result = {"kind": "B04ContentRevisionAcceptance", "block_id": "B04", "source_sha256": subject,
              "checks": [], "status": "FAIL"}
    page = None
    browser = None
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
            page.get_by_label("Project name", exact=True).fill("B04 Project")
            page.get_by_role("button", name="Create project", exact=True).click()
            page.wait_for_timeout(400)
            pid = page.evaluate("currentProjectId")
            page.get_by_role("button", name="Campaigns", exact=True).click()
            page.get_by_label("Campaign name", exact=True).fill("B04 Campaign")
            page.get_by_label("Audience", exact=True).fill("Dev")
            page.get_by_label("Channels", exact=True).fill("alpha,beta")
            page.get_by_role("button", name="Create campaign", exact=True).click()
            page.wait_for_timeout(500)
            page.get_by_role("button", name="Content", exact=True).click()
            page.wait_for_timeout(700)
            page.get_by_label("Content text", exact=True).fill("Revision one")
            page.get_by_label("Channel", exact=True).select_option("alpha")
            page.get_by_role("button", name="Save content", exact=True).click()
            page.wait_for_timeout(700)
            cid = page.evaluate("currentContentId")
            require(bool(cid), "content identity")
            page.get_by_label("Content text", exact=True).fill("Revision two edited")
            page.get_by_role("button", name="Save content", exact=True).click()
            page.wait_for_timeout(700)
            rows = page.request.post(url + "/api/action", data={"milestone":"M5","op":"content.list","project_id":pid}).json()["items"]
            require(len(rows) == 1 and rows[0]["id"] == cid and rows[0]["revision"] == 2 and rows[0]["text"] == "Revision two edited",
                    "edit preserves identity and advances revision")
            require(page.locator("#revision-list .item").count() >= 2, "revision history visible")
            page.get_by_label("Compare from revision", exact=True).select_option("1")
            page.get_by_label("Compare to revision", exact=True).select_option("2")
            page.get_by_role("button", name="Compare revisions", exact=True).click()
            page.wait_for_timeout(500)
            compare = page.locator("#compare-result").inner_text()
            require("Revision one" in compare and "Revision two edited" in compare, "compare shows both revisions")
            # Actual process restart.
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
            page.get_by_role("button", name="Content", exact=True).click()
            page.wait_for_timeout(600)
            require(page.get_by_label("Content text", exact=True).input_value() == "Revision two edited", "edit text persists after restart")
            require(page.locator("#revision-list .item").count() >= 2, "revision history persists after restart")
            require(not errors, "no JavaScript errors: " + repr(errors))
            result["checks"] = ["content created", "identity preserved and revision advanced", "revision history visible",
                                "revision compare shows before/after", "edited text persists after restart",
                                "revision history persists after restart", "no JavaScript errors"]
            result["status"] = "PASS"
            page.screenshot(path=str(out / "b04.png"), full_page=True)
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
        try:
            page.screenshot(path=str(out / "failure.png"), full_page=True)
        except Exception:
            pass
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
