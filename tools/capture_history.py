"""Bounded, link-safe historical inventory with parallel read-only hashing."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import subprocess
from capture_baseline import P, H, write

EXCLUDES = ('scratch', '__pycache__', '.git', '.venv', 'venv', 'node_modules', '.pytest_cache')


def inspect(name):
    path = P / name
    if not path.resolve().is_relative_to(P.resolve()) or path.is_symlink():
        return name, None
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return path.relative_to(P).as_posix(), {'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


if __name__ == '__main__':
    argv = ['rg', '--files', '--hidden', '--no-ignore']
    for name in EXCLUDES:
        argv += ['-g', '!**/' + name + '/**']
    argv += ['-g', '!*.pyc', '-g', '!*.lock']
    listed = subprocess.run(argv, cwd=P, capture_output=True, text=True, encoding='utf-8', check=True)
    names = listed.stdout.splitlines()
    print('SELECTED_FILES', len(names), flush=True)
    rows, links = {}, []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for index, (name, value) in enumerate(pool.map(inspect, names), 1):
            if value is None:
                links.append(name)
            else:
                rows[name] = value
            if index % 2000 == 0:
                print('HASHED', index, flush=True)
    write(H / 'migration/veriarbor/HISTORY_PROTECTION.json', {
        'root': str(P), 'files': rows,
        'excluded_unmodified_directory_names': EXCLUDES,
        'links_not_followed': True, 'outside_root_or_link_entries_excluded': links,
        'policy': 'Selected historical bytes retained. No UNKNOWN resubmission or ledger reset. Temporary/dependency exclusions are not byte-verified claims.'})
    print('DONE', len(rows), flush=True)
