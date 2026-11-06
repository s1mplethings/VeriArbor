"""Run checks with immutable logs and exact commands; never manufacture PASS."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    label, cwd, *command = sys.argv[1:]
    out = ROOT / 'governance/checks' / label
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONUTF8='1')
    with (out / 'output.log').open('wb') as stream:
        result = subprocess.run(command, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT)
    receipt = {'argv': command, 'cwd': cwd, 'exit_code': result.returncode,
               'status': 'PASS' if result.returncode == 0 else 'FAIL',
               'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'seconds': time.monotonic() - started,
               'log_sha256': hashlib.sha256((out / 'output.log').read_bytes()).hexdigest()}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt))
    print((out / 'output.log').read_text(encoding='utf-8', errors='replace')[-6000:])
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
