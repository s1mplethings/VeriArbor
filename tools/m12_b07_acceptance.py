"""Independent B07 Scheduler UI browser acceptance."""
import datetime, hashlib, json, os, re, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

WS = Path(r"F:\CGKN-ITER-132\production-core-convergence-v1\promotion\run-05\candidate")


def require(value, message):
    if not value:
        raise AssertionError(message)


def main():
    out = Path(tempfile.mkdtemp(prefix="m12-b07-"))
    data = out / "data"
    subject = hashlib.sha256((WS / "main.py").read_bytes()).hexdigest()
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    log = (out / "server.log").open("wb")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.Popen([sys.executable, "-X", "utf8", str(WS / "main.py"), "--serve", "--port", str(port), "--data", str(data)],
                            cwd=WS, stdout=log, stderr=subprocess.STDOUT, env=env)
    result = {"kind": "B07SchedulerUIAcceptance", "block_id": "B07", "source_sha256": subject,
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
            page.get_by_label("Project name", exact=True).fill("B07 Project")
            page.get_by_role("button", name="Create project", exact=True).click()
            page.wait_for_timeout(400)
            pid = page.evaluate("currentProjectId")
            page.get_by_role("button", name="Campaigns", exact=True).click()
            page.get_by_label("Campaign name", exact=True).fill("B07 Campaign")
            page.get_by_label("Audience", exact=True).fill("Dev")
            page.get_by_label("Channels", exact=True).fill("alpha")
            page.get_by_role("button", name="Create campaign", exact=True).click()
            page.wait_for_timeout(500)
            source = out / "evidence"; source.mkdir(); (source / "README.md").write_text("Scheduler facts.\n", encoding="utf8")
            ev = page.request.post(url + "/api/action", data={"milestone":"M2","op":"evidence.import","project_id":pid,"path":str(source)}).json()
            page.request.post(url + "/api/action", data={"milestone":"M3","op":"claim.create","project_id":pid,"text":"Scheduler facts.","evidence_ids":[ev["id"]]})
            page.get_by_role("button", name="Content", exact=True).click()
            page.wait_for_timeout(700)
            page.get_by_label("Content text", exact=True).fill("Scheduled copy")
            page.get_by_label("Channel", exact=True).select_option("alpha")
            page.get_by_role("button", name="Save content", exact=True).click()
            page.wait_for_timeout(600)
            page.get_by_role("button", name="Review", exact=True).click()
            page.wait_for_timeout(500)
            page.get_by_role("button", name="Approve", exact=True).click()
            page.wait_for_timeout(500)
            page.get_by_role("button", name="Schedule/Publish", exact=True).click()
            page.wait_for_timeout(700)
            page.get_by_label("Platform URL", exact=True).filter(visible=True).fill("http://127.0.0.1:9")
            when = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)).isoformat()
            later = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2)).isoformat()
            page.get_by_label(re.compile(r"^When(?: \(ISO8601\))?$")).fill(when)
            page.get_by_role("button", name="Schedule", exact=True).click()
            page.wait_for_timeout(700)
            schedules = page.request.post(url + "/api/action", data={"milestone":"M8","op":"schedule.list","project_id":pid}).json()["items"]
            require(len(schedules) == 1 and schedules[0]["status"] == "PENDING", "schedule created")
            sid = schedules[0]["id"]
            require(sid[:8] in page.locator("#schedules-list").inner_text(), "schedule visible")
            page.get_by_label(re.compile(r"^When(?: \(ISO8601\))?$")).fill(later)
            page.get_by_role("button", name="Reschedule", exact=True).click()
            page.wait_for_timeout(600)
            schedules = page.request.post(url + "/api/action", data={"milestone":"M8","op":"schedule.list","project_id":pid}).json()["items"]
            require(schedules[0]["when"] == later, "reschedule persisted")
            page.get_by_role("button", name="Cancel", exact=True).click()
            page.wait_for_timeout(600)
            schedules = page.request.post(url + "/api/action", data={"milestone":"M8","op":"schedule.list","project_id":pid}).json()["items"]
            require(schedules[0]["status"] == "CANCELLED", "cancel persisted")
            # Canceled schedule must not execute on run_due.
            page.request.post(url + "/api/action", data={"milestone":"M8","op":"schedule.run_due","project_id":pid,"now":later})
            schedules = page.request.post(url + "/api/action", data={"milestone":"M8","op":"schedule.list","project_id":pid}).json()["items"]
            receipts = page.request.post(url + "/api/action", data={"milestone":"M9","op":"receipt.list","project_id":pid}).json()["items"]
            require(schedules[0]["status"] == "CANCELLED" and not receipts, "canceled schedule does not execute")
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
            page.get_by_role("button", name="Schedule/Publish", exact=True).click()
            page.wait_for_timeout(700)
            require(sid[:8] in page.locator("#schedules-list").inner_text() and "CANCELLED" in page.locator("#schedules-list").inner_text(), "schedule persists after restart")
            require(not errors, "no JavaScript errors: " + repr(errors))
            result["checks"] = ["approved content scheduled", "schedule visible", "reschedule persisted",
                                "cancel persisted", "canceled schedule not executed by run_due",
                                "schedule persists after restart", "no JavaScript errors"]
            result["status"] = "PASS"
            page.screenshot(path=str(out / "b07.png"), full_page=True)
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
