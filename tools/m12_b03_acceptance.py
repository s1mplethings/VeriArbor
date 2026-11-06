"""Independent B03 SignalsEvidence browser acceptance."""
import hashlib, json, os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

WS = Path(r"F:\CGKN-ITER-132\production-core-convergence-v1\promotion\run-05\candidate")


def require(value, message):
    if not value:
        raise AssertionError(message)


def main():
    out = Path(tempfile.mkdtemp(prefix="m12-b03-"))
    data = out / "data"
    source = out / "evidence"
    source.mkdir()
    (source / "README.md").write_text("Release supports offline local workflows.\n", encoding="utf8")
    subject = hashlib.sha256((WS / "main.py").read_bytes()).hexdigest()
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    log = (out / "server.log").open("wb")
    proc = subprocess.Popen([sys.executable, "-X", "utf8", str(WS / "main.py"), "--serve", "--port", str(port), "--data", str(data)],
                            cwd=WS, stdout=log, stderr=subprocess.STDOUT,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    result = {"kind": "B03SignalsEvidenceAcceptance", "block_id": "B03", "source_sha256": subject,
              "checks": [], "status": "FAIL"}
    try:
        for _ in range(100):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=.2):
                    break
            except OSError:
                time.sleep(.1)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page()
            page.set_default_timeout(10000)
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("dialog", lambda d: d.accept("unsupported signal"))
            page.goto(url, wait_until="networkidle")
            page.get_by_label("Project name", exact=True).fill("B03 Project")
            page.get_by_role("button", name="Create project", exact=True).click()
            page.wait_for_timeout(400)
            pid = page.evaluate("currentProjectId")
            require(bool(pid), "project identity")
            page.get_by_role("button", name="Signals", exact=True).click()
            page.wait_for_timeout(400)
            page.get_by_label("Evidence path", exact=True).fill(str(source))
            page.get_by_role("button", name="Import evidence", exact=True).click()
            page.wait_for_timeout(500)
            require(page.locator("#evidence-list .item").count() >= 1, "evidence visible")
            require(page.locator("#signal-evidence-select option").count() >= 2, "evidence selectable")
            page.get_by_label("Signal text", exact=True).fill("Review new release facts")
            page.get_by_role("button", name="Create signal", exact=True).click()
            page.wait_for_timeout(500)
            require(page.get_by_text("Review new release facts", exact=False).count() >= 1, "signal visible")
            require("OPEN" in page.locator("#signals-list").inner_text(), "signal OPEN")
            # Create a supported claim through M3, then reload Signals to show reference.
            evidence_id = page.eval_on_selector("#signal-evidence-select", "e=>e.value")
            claim = page.request.post(url + "/api/action", data={
                "milestone": "M3", "op": "claim.create", "project_id": pid,
                "text": "Release supports offline local workflows.", "evidence_ids": [evidence_id]
            }).json()
            require(claim.get("status") == "SUPPORTED", "supported claim")
            page.reload(wait_until="networkidle")
            page.get_by_role("button", name="Signals", exact=True).click()
            page.wait_for_timeout(500)
            require(page.get_by_text("Review new release facts", exact=False).count() >= 1, "signal persists")
            require(page.get_by_text("Release supports offline local workflows.", exact=False).count() >= 1, "claim visible")
            require("SUPPORTED" in page.locator("#claims-list").inner_text(), "claim status visible")
            # Reject signal through real UI prompt.
            page.locator("#signals-list button", has_text="Reject").first.click()
            page.wait_for_timeout(500)
            require("REJECTED" in page.locator("#signals-list").inner_text(), "signal rejected")
            require("unsupported signal" in page.locator("#signals-list").inner_text(), "reject reason visible")
            # Refresh persistence.
            page.reload(wait_until="networkidle")
            page.get_by_role("button", name="Signals", exact=True).click()
            page.wait_for_timeout(500)
            require("REJECTED" in page.locator("#signals-list").inner_text(), "rejected signal persists")
            require(not errors, "no JavaScript errors: " + repr(errors))
            result["checks"] = ["project created", "evidence imported and visible", "evidence selectable",
                                "signal created and visible", "signal OPEN", "supported claim visible with reference",
                                "signal rejected with reason", "signals/claims persist after refresh",
                                "no JavaScript errors"]
            result["status"] = "PASS"
            page.screenshot(path=str(out / "b03.png"), full_page=True)
            browser.close()
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
        try:
            page.screenshot(path=str(out / "failure.png"), full_page=True)
        except Exception:
            pass
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait(timeout=5)
        log.close()
    result["cleanup"] = {"server_stopped": proc.poll() is not None}
    (out / "receipt.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
