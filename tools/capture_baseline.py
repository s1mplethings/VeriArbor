"""Capture immutable migration inputs. Never reset or modify source evidence."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys
import uuid

V = Path(__file__).resolve().parents[1]
H = Path(r'F:\CGKN-LeanLoop-V1-20261101')
P = Path(r'F:\CGKN-ITER-132\production-core-convergence-v1')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)


def git(root, *args):
    result = subprocess.run(['git', '-c', 'safe.directory=' + root.as_posix(), '-C', str(root), *args], capture_output=True, text=True, encoding='utf-8')
    return {'exit_code': result.returncode, 'output': result.stdout.strip(), 'error': result.stderr.strip()}


def probe(root):
    path = root / ('.veriarbor-probe-' + uuid.uuid4().hex)
    try:
        with path.open('x') as stream:
            stream.write('probe')
        assert path.read_text() == 'probe'
        path.unlink()
        return {'read': True, 'write': True}
    except OSError as error:
        return {'read': root.exists(), 'write': False, 'error': str(error)}


def main():
    assert Path.cwd().resolve() == V, 'Run from the bound library root'
    access = {str(root): probe(root) for root in (V, H, P)}
    assert all(row['write'] for row in access.values()), access
    write(V / 'governance/WORKSPACE_BINDING.json', {
        'VERIARBOR_ROOT': str(V), 'CGNK_ROOT': str(H), 'PROMOTION_ROOT': str(P),
        'cwd': os.getcwd(), 'python': sys.executable, 'virtual_env': os.getenv('VIRTUAL_ENV'),
        'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'initial_contents_before_tools': ['.git', 'LICENSE', 'README.md'],
        'no_nested_repository': True})
    write(V / 'governance/HOST_ACCESS_CHECK.json', access)
    commands = {'head': ['rev-parse', 'HEAD'], 'branch': ['branch', '--show-current'],
                'remote': ['remote', '-v'], 'dirty_manifest': ['status', '--porcelain=v1', '--untracked-files=all']}
    write(V / 'governance/INITIAL_REPOSITORY.json', {key: git(V, *args) for key, args in commands.items()})
    destination = H / 'migration/veriarbor'
    write(destination / 'CGNK_BASELINE.json', {key: git(H, *args) for key, args in commands.items()})
    arch = json.loads((H / 'governance/current_architecture.json').read_text(encoding='utf-8'))
    write(destination / 'AUTHORITY_MAP_BEFORE.json', arch)
    write(destination / 'ENTRYPOINT_MAP_BEFORE.json', {'declared': arch['declared_authorities'], 'compatibility': arch['compatibility_entrypoints']})
    files = {}
    for top in ['cgkn', 'scripts', 'contracts', 'config', 'governance', 'tests']:
        for path in (H / top).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix in {'.py', '.json', '.yaml', '.toml'}:
                files[path.relative_to(H).as_posix()] = digest(path)
    write(V / 'governance/SOURCE_MANIFEST.json', {'root': str(H), 'files': files,
          'manifest_hash': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()})
    protected = {}
    excluded = []
    for directory, directories, files in os.walk(P):
        root = Path(directory)
        for name in list(directories):
            if name in {'scratch', '__pycache__', '.git', '.venv', 'node_modules', '.pytest_cache'}:
                excluded.append((root / name).relative_to(P).as_posix())
                directories.remove(name)
        for name in files:
            path = root / name
            if path.suffix not in {'.pyc', '.lock'}:
                protected[path.relative_to(P).as_posix()] = {'sha256': digest(path), 'bytes': path.stat().st_size}
    write(destination / 'HISTORY_PROTECTION.json', {'root': str(P), 'files': protected,
          'excluded_unmodified_temporary_or_dependency_directories': excluded,
          'policy': 'Existing evidence immutable; no UNKNOWN resubmit; no ledger reset.'})
    print(json.dumps({'source_files': len(files), 'protected_files': len(protected), 'baseline': str(destination)}))


if __name__ == '__main__':
    main()
