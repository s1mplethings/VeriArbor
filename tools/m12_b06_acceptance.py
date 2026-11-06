"""Independent B06 Approval UI browser acceptance."""
import base64, hashlib, json, os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

WS = Path(r"F:\CGKN-ITER-132\production-core-convergence-v1\promotion\run-05\candidate")


def require(value, message):
    if not value:
        raise AssertionError(message)


def main():
    out = Path(tempfile.mkdtemp(prefix="m12-b06-"))
    data = out / "data"
    png = out / "pixel.png"
    png.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a4gAAAABJRU5ErkJggg=="))
    subject = hashlib.sha256((WS / "main.py").read_bytes()).hexdigest()
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    log = (out / "server.log").open("wb")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.Popen([sys.executable, "-X", "utf8", str(WS / "main.py"), "--serve", "--port", str(port), "--data", str(data)],
                            cwd=WS, stdout=log, stderr=subprocess.STDOUT, env=env)
    result = {"kind": "B06ApprovalUIAcceptance", "block_id": "B06", "source_sha256": subject,
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
            page.get_by_label("Project name", exact=True).fill("B06 Project")
            page.get_by_role("button", name="Create project", exact=True).click()
            page.wait_for_timeout(400)
            pid = page.evaluate("currentProjectId")
            page.get_by_role("button", name="Campaigns", exact=True).click()
            page.get_by_label("Campaign name", exact=True).fill("B06 Campaign")
            page.get_by_label("Audience", exact=True).fill("Dev")
            page.get_by_label("Channels", exact=True).fill("alpha")
            page.get_by_role("button", name="Create campaign", exact=True).click()
            page.wait_for_timeout(500)
            source = out / "evidence"; source.mkdir(); (source / "README.md").write_text("Release facts.\n", encoding="utf8")
            ev = page.request.post(url + "/api/action", data={"milestone":"M2","op":"evidence.import","project_id":pid,"path":str(source)}).json()
            claim = page.request.post(url + "/api/action", data={"milestone":"M3","op":"claim.create","project_id":pid,"text":"Release facts.","evidence_ids":[ev["id"]]}).json()
            media = page.request.post(url + "/api/action", data={"milestone":"M11","op":"media.import","project_id":pid,"kind":"image","path":str(png)}).json()
            page.get_by_role("button", name="Content", exact=True).click()
            page.wait_for_timeout(700)
            page.get_by_label("Content text", exact=True).fill("Approval copy")
            page.get_by_label("Channel", exact=True).select_option("alpha")
            page.get_by_label("Claims", exact=True).select_option(label="Release facts.")
            page.get_by_label("Media", exact=True).select_option(media["id"])
            page.get_by_role("button", name="Save content", exact=True).click()
            page.wait_for_timeout(700)
            cid = page.evaluate("currentContentId")
            require(bool(cid), "content identity")
            require(not page.eval_on_selector("#review-button", "e=>e.disabled"), "review enabled for DRAFT")
            require(page.eval_on_selector("#approve-button", "e=>e.disabled"), "approve disabled before review")
            page.get_by_role("button", name="Review", exact=True).click()
            page.wait_for_timeout(700)
            require(page.eval_on_selector("#approve-button", "e=>!e.disabled"), "approve enabled after review")
            page.get_by_role("button", name="Approve", exact=True).click()
            page.wait_for_timeout(700)
            approval = page.request.post(url + "/api/action", data={"milestone":"M6","op":"approval.status","project_id":pid,"content_id":cid}).json()
            require(approval["status"] == "APPROVED", "approved")
            require(page.eval_on_selector("#publish-content-button", "e=>!e.disabled"), "publish enabled after approval")
            # Semantic edit invalidates approval.
            page.get_by_label("Content text", exact=True).fill("Approval copy edited")
            page.get_by_role("button", name="Save content", exact=True).click()
            page.wait_for_timeout(700)
            approval = page.request.post(url + "/api/action", data={"milestone":"M6","op":"approval.status","project_id":pid,"content_id":cid}).json()
            require(approval["status"] == "DRAFT", "semantic edit invalidates approval")
            require(not page.eval_on_selector("#review-button", "e=>e.disabled"), "review re-enabled after edit")
            require(page.eval_on_selector("#publish-content-button", "e=>e.disabled"), "publish disabled after edit")
            # Re-review and re-approve.
            page.get_by_role("button", name="Review", exact=True).click()
            page.wait_for_timeout(600)
            page.get_by_role("button", name="Approve", exact=True).click()
            page.wait_for_timeout(600)
            approval = page.request.post(url + "/api/action", data={"milestone":"M6","op":"approval.status","project_id":pid,"content_id":cid}).json()
            require(approval["status"] == "APPROVED", "re-approval")
            # Missing media blocks approval on a new content item.
            page.get_by_role("button", name="New content", exact=True).click()
            page.wait_for_timeout(200)
            page.get_by_label("Content text", exact=True).fill("Broken media copy")
            page.get_by_label("Channel", exact=True).select_option("alpha")
            page.get_by_label("Claims", exact=True).select_option(label="Release facts.")
            page.get_by_label("Media", exact=True).select_option(media["id"])
            page.get_by_role("button", name="Save content", exact=True).click()
            page.wait_for_timeout(600)
            broken_id = page.evaluate("currentContentId")
            page.get_by_role("button", name="Review", exact=True).click()
            page.wait_for_timeout(500)
            Path(media["path"]).unlink()
            page.get_by_role("button", name="Approve", exact=True).click()
            page.wait_for_timeout(700)
            approval = page.request.post(url + "/api/action", data={"milestone":"M6","op":"approval.status","project_id":pid,"content_id":broken_id}).json()
            require(approval["status"] == "REVIEW", "missing media blocks approval")
            require("media" in page.locator("#content-error").inner_text().lower(), "media approval error visible")
            require(not errors, "no JavaScript errors: " + repr(errors))
            result["checks"] = ["review enabled for DRAFT", "approve disabled before review", "review then approve succeeded",
                                "publish enabled after approval", "semantic edit invalidates approval",
                                "review re-enabled and publish disabled after edit", "re-review and re-approve",
                                "missing media blocks approval with visible error", "no JavaScript errors"]
            result["status"] = "PASS"
            page.screenshot(path=str(out / "b06.png"), full_page=True)
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
