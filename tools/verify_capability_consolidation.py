"""Reproduce bounded offline checks and context-size fixture. No provider route."""
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
HOST = Path(os.environ.get('VERIARBOR_HOST', r'F:\CGKN-LeanLoop-V1-20261101'))
sys.path.insert(0, str(ROOT / 'tests' / 'unit'))
from test_capability_skills import manifest, validations
from veriarbor.skills import SkillRegistry, SkillMatcher, render_instructions


def run(name, arguments, cwd, library_root=None):
    started = time.perf_counter()
    env = dict(os.environ, PYTHONPATH=os.pathsep.join((str(library_root or ROOT / 'src'), str(HOST))))
    result = subprocess.run([sys.executable, *arguments], cwd=cwd, env=env,
                            capture_output=True, text=True, encoding='utf-8', timeout=180)
    log = ROOT / 'reports' / (name + '.txt')
    log.write_text(result.stdout + result.stderr, encoding='utf-8')
    return {'name': name, 'command': [sys.executable, *arguments], 'cwd': str(cwd),
            'exit_code': result.returncode, 'seconds': round(time.perf_counter() - started, 3),
            'log': str(log)}


def size_fixture():
    with tempfile.TemporaryDirectory() as folder:
        registry = SkillRegistry(folder)
        manifests = []
        for i in range(20):
            m = manifest(i, 'media_ingest' if i < 5 else 'other')
            registry.register(replace(m, status='VERIFIED'), validations(m))
            manifests.append(m)
        loaded = SkillMatcher(registry).load(project_id='p', task_family='media_ingest', capability_id='ingest',
            inputs=('media',), outputs=('segments',), dependency_versions={'ingest@1': '1'},
            dependency_contract_hashes={'media.port': 'A', 'ingest': 'A'})
        index = json.dumps(registry.index(), ensure_ascii=False)
        before = json.dumps([{'manifest': m.as_dict(), 'instructions': render_instructions(m)} for m in manifests])
        after = index + json.dumps([{'manifest': m.as_dict(), 'instructions': body} for m, body in loaded])
        return {'kind': 'synthetic_context_size_only', 'registry_skills': 20, 'compatible_skills': 5,
                'loaded_skills': len(loaded), 'max_skill_load': 3,
                'skill_index_bytes': len(index.encode('utf-8')),
                'before_all_manifests_and_bodies_bytes': len(before.encode('utf-8')),
                'after_index_and_top_k_manifests_and_bodies_bytes': len(after.encode('utf-8')),
                'approx_tokens_before': (len(before) + 3) // 4,
                'approx_tokens_after': (len(after) + 3) // 4,
                'token_estimator': 'ceil(characters / 4); not a model tokenizer or production benchmark',
                'provider_calls': 0, 'production_token_saving': None}


def main():
    checks = [run('capability_core_tests', ['-m', 'unittest', 'discover', '-s', 'tests', '-v'], ROOT)]
    if HOST.exists():
        checks.append(run('capability_host_tests', ['-m', 'pytest',
            'tests/project_agent', 'tests/runtime/test_event_frontier.py',
            'tests/runtime/test_execution_continuity.py', 'tests/runtime/test_graph_commit.py',
            'tests/runtime/test_executor_context.py',
            'tests/test_veriarbor_block_adapter.py', 'tests/test_veriarbor_integration.py',
            'tests/agent/test_project_session.py', '-q'], HOST))
        checks.append(run('capability_targeted_host_tests', ['-m', 'pytest',
            'tests/project_agent/test_capability_gates_skills.py', '-q'], HOST))
        checks.append(run('capability_product_direction', ['scripts/product_direction_gate.py'], HOST))
        # Reproduce the known scheduler-expectation mismatch against the original
        # committed library in isolation; never reset or replace the working tree.
        with tempfile.TemporaryDirectory() as baseline:
            files = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', 'HEAD', 'src/veriarbor'],
                                            cwd=ROOT, text=True).splitlines()
            for name in files:
                destination = Path(baseline) / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT))
            legacy_tests = [
                'tests/test_veriarbor_integration.py::test_low_sample_slot_policy_remains_bounded_and_respects_conflicts',
                'tests/runtime/test_execution_continuity.py::test_no_delta_is_failed_deliverable_and_next_decision_feedback',
                'tests/runtime/test_execution_continuity.py::test_readonly_evidence_not_false_no_progress',
                'tests/runtime/test_execution_continuity.py::test_progress_is_received_by_next_canonical_planner_decision']
            # The host working tree predates this task and has many unrelated
            # changes. Disable only the newly inserted adapter hooks in this
            # disposable subprocess, retaining its pre-existing worker policy.
            baseline_code = (
                'import sys, types; '
                'adapter=types.ModuleType("cgkn.adapters.veriarbor.capability_adapter"); '
                'adapter.record_phase=lambda *a, **kw: None; '
                'adapter.validate_inputs=lambda *a, **kw: "VALID"; '
                'sys.modules[adapter.__name__]=adapter; '
                'import pytest; sys.exit(pytest.main(' + repr([*legacy_tests, '-q']) + '))')
            checks.append(run('capability_legacy_baseline', ['-c', baseline_code], HOST, Path(baseline) / 'src'))
    receipt = {'checks': checks, 'context_fixture': size_fixture(),
               'provider_calls': 0, 'long_runs': False}
    (ROOT / 'reports/CAPABILITY_GATES_SKILL_TEST_RECEIPT.json').write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return int(any(check['exit_code'] for check in checks))


if __name__ == '__main__':
    raise SystemExit(main())
