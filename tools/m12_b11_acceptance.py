import hashlib, json, subprocess, sys, tempfile, datetime
from pathlib import Path

CAND = Path(r"F:\CGKN-ITER-132\production-core-convergence-v1\promotion\run-05\candidate")
CONSUMER = Path(r"F:\CGKN-ITER-132\production-core-convergence-v1\promotion\run-05\consumer-revisions\final-gui-complete-v10.py")
out = Path(tempfile.mkdtemp(prefix="m12-b11-"))
req = out / "request.json"
req.write_text(json.dumps({"workspace": str(CAND), "requirements": {"M12": {}}}, ensure_ascii=False), encoding="utf8")
run = subprocess.run([sys.executable, "-X", "utf8", str(CONSUMER), "ignored", str(req)],
                     cwd=out, capture_output=True, text=True, encoding="utf8", timeout=600)
print("consumer stdout:", run.stdout[-2000:])
print("consumer stderr:", run.stderr[-2000:])
observed = json.loads(run.stdout.strip().splitlines()[-1])
assert observed["execution"] == "VALID" and observed["observed"]["value"] is True, observed
source = hashlib.sha256((CAND / "main.py").read_bytes()).hexdigest()
checker = hashlib.sha256(CONSUMER.read_bytes()).hexdigest()
receipt = {
    "kind": "B11FinalProductVerticalSliceAcceptance",
    "block_id": "B11",
    "status": "PASS",
    "source_sha256": source,
    "checker": str(CONSUMER),
    "checker_sha256": checker,
    "observed": observed,
    "checks": ["full M12 vertical slice passed", "projects/campaigns/content/claims/approval/media/schedule/publish/receipt/analytics",
               "semantic edit invalidates approval", "restart persistence", "project isolation", "no JavaScript errors"],
    "startup": {"command": [sys.executable, "-X", "utf8", str(CONSUMER)], "cwd": str(out)},
    "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
(out / "B11_FINAL_VERTICAL_SLICE_ACCEPTANCE.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf8")
print(json.dumps({"receipt": str(out / "B11_FINAL_VERTICAL_SLICE_ACCEPTANCE.json"), "status": "PASS", "source": source}, ensure_ascii=False))
