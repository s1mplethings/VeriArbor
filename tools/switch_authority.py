"""Bounded, hash-guarded source migration with byte-exact rollback snapshots."""
from pathlib import Path
import ast
import hashlib
import json
from capture_baseline import H, V

OUT = H / 'migration/veriarbor'


def replace_function(source, name, replacement):
    tree = ast.parse(source)
    matches = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(matches) != 1:
        raise ValueError('ambiguous function ' + name)
    node = matches[0]
    start = min([node.lineno] + [n.lineno for n in node.decorator_list]) - 1
    lines = source.splitlines(keepends=True)
    return ''.join(lines[:start]) + replacement + '\n\n' + ''.join(lines[node.end_lineno:])


def edit(rel, transform, authority):
    path = H / rel
    before = path.read_bytes()
    expected = json.loads((V / 'governance/SOURCE_MANIFEST.json').read_text())['files'][rel]
    assert hashlib.sha256(before).hexdigest() == expected, 'Source changed since P0: ' + rel
    source = before.decode('utf-8').replace('\r\n', '\n')
    updated = transform(source)
    ast.parse(updated)
    backup = OUT / 'rollback' / rel
    backup.parent.mkdir(parents=True, exist_ok=True)
    with backup.open('xb') as stream:
        stream.write(before)
    path.write_text(updated, encoding='utf-8', newline='\n')
    after = hashlib.sha256(path.read_bytes()).hexdigest()
    with (OUT / 'AUTHORITY_SWITCH_RECEIPTS.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'file': rel, 'authority': authority, 'before_sha256': expected,
                                'after_sha256': after, 'rollback': str(backup),
                                'shadow': 'SHADOW_RESULTS.json', 'status': 'SWITCHED_PENDING_REGRESSION'}) + '\n')


def acceptance(source):
    begin = source.index('        obligations = {}', source.index('    def _view('))
    end = source.index('        complete = ', begin)
    return source[:begin] + '''        from cgkn.adapters.veriarbor.acceptance_adapter import obligation_rollup
        reduction = obligation_rollup(self.requirements, rows)
        obligations = reduction['obligations']
        completion = reduction['completion']
        coverage = reduction['evidence_coverage']
        hard_verdict = reduction['hard_verdict']
        total = sum(r['weight'] for r in obligations.values())
''' + source[end:]


def readiness(source):
    for name in ('dependency_ready_goals', 'task_readiness_projection'):
        source = replace_function(source, name, f'from cgkn.adapters.veriarbor.tree_adapter import {name}')
    return source


def progress(source):
    # Host semantic repair diagnostics remain host-owned. Only normalization
    # and hashing move; the validation branch retains exact structured errors.
    begin = source.index('    def normalize(value):', source.index('def strategy_fingerprint('))
    end = source.index('\n\ndef admit_progress(', begin)
    source = source[:begin] + '''    from veriarbor.learning import strategy_fingerprint as fingerprint, StrategyError
    try:
        return fingerprint(strategy)
    except StrategyError as error:
        raise ContractError(str(error)) from error
''' + source[end:]
    begin = source.index('    for previous in reversed(history):')
    end = source.index("    return {'strategy_fingerprint'", begin)
    source = source[:begin] + '''    from veriarbor.learning import repeated_no_progress
    if repeated_no_progress(strategy, fingerprint, available, history):
        raise ContractError('REPEATED_REPAIR_NO_PROGRESS', fields=('strategy',), repair_class='R6',
                            details={'next_operation': 'LOCAL_STRATEGY_SWITCH',
                                     'correction_path_terminated': True})
''' + source[end:]
    return source


def main():
    assert json.loads((OUT / 'SHADOW_RESULTS.json').read_text())['status'] == 'PASS'
    edit('cgkn/state/acceptance.py', acceptance, 'VerificationRollup compatibility reduction')
    edit('cgkn/protocol/context_pack.py', readiness, 'Task readiness/frontier')
    edit('cgkn/protocol/progress.py', progress, 'Strategy fingerprint and repeated no-progress')


if __name__ == '__main__':
    main()
