"""AST inventory with explicit unknowns; static references are not dynamic proof."""
from pathlib import Path
import ast
import json
from capture_baseline import H, V, write

extract = {
    'cgkn/state/acceptance.py': ['GoalAcceptance._view'],
    'cgkn/protocol/context_pack.py': ['dependency_ready_goals', 'task_readiness_projection'],
    'cgkn/protocol/progress.py': ['strategy_fingerprint', 'ProgressGuidedBacktracking.assess'],
    'cgkn/protocol/review_policy.py': ['review_kind', 'evaluator_disposition', 'qualify_evaluator', 'review_needed'],
    'cgkn/protocol/repair.py': ['repair_progress'],
    'cgkn/runtime/dag_runner.py': ['DAGRunner._compatible'],
}


def main():
    modules, symbols, refs = [], [], {}
    paths = sorted(set(H.glob('cgkn/**/*.py')) | set(H.glob('scripts/**/*.py')) | set(H.glob('contracts/**/*.py')))
    for path in paths:
        rel = path.relative_to(H).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        except (SyntaxError, UnicodeError) as error:
            modules.append({'file': rel, 'classification': 'UNKNOWN', 'reason': str(error)})
            continue
        names = [node.name for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))]
        category = 'MIGRATE_TO_ADAPTER' if rel in extract else 'KEEP_IN_CGNK_CORE'
        modules.append({'file': rel, 'classification': category,
                        'symbols': names, 'reason': 'Mixed host boundary and extractable policies' if rel in extract else 'Retain existing behavior; not authorized for speculative deletion'})
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ''
                refs.setdefault(name, []).append({'file': rel, 'line': node.lineno})
    for rel, names in extract.items():
        for name in names:
            symbols.append({'file': rel, 'symbol': name, 'classification': 'EXTRACT_TO_VERIARBOR',
                            'callers_static': refs.get(name.split('.')[-1], []),
                            'dynamic_entrypoints': 'UNRESOLVED until shadow and targeted regression',
                            'state_ownership': 'CGNK FileRunStore', 'execution_ownership': 'CGNK DAGRunner',
                            'compatibility': 'Preserve host public signature, errors, persisted hashes and verdicts',
                            'destination': 'veriarbor pure modules via cgkn/adapters/veriarbor',
                            'required_tests': ['differential', 'historical replay', 'targeted host regression'],
                            'rollback': 'Restore byte-exact pre-edit source after post-edit hash check'})
    out = H / 'migration/veriarbor'
    write(out / 'MODULE_CLASSIFICATION.json', {'scope': ['cgkn', 'scripts', 'contracts'], 'modules': modules,
          'outside_scope': 'Legacy/experimental/generated artifacts retained; no deletion approved by this inventory'})
    write(out / 'SYMBOL_EXTRACTION_MAP.json', symbols)
    (out / 'DYNAMIC_ENTRYPOINT_AUDIT.md').write_text(
        '# Dynamic entrypoint audit\n\nStatic AST callsites are recorded separately. Attribute calls may be ambiguous. '
        'Public import paths remain compatibility adapters. No dynamic entrypoint is declared removed until its switch receipt and tests exist. '
        'Provider, runtime, storage, provenance, UNKNOWN recovery and delivery remain host-owned.\n', encoding='utf-8')
    print(json.dumps({'modules': len(modules), 'extraction_symbols': len(symbols)}))


if __name__ == '__main__':
    main()
