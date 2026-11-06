"""Subsequent migration slices, guarded against concurrent user edits."""
import ast
import hashlib
import json
import sys
from capture_baseline import H, V
from switch_authority import replace_function

OUT = H / 'migration/veriarbor'


def edit(rel, transform, authority):
    rows = [json.loads(line) for line in (OUT / 'AUTHORITY_SWITCH_RECEIPTS.jsonl').read_text().splitlines()]
    previous = next((row for row in reversed(rows) if row['file'] == rel), None)
    baseline = json.loads((V / 'governance/SOURCE_MANIFEST.json').read_text())['files']
    # Newly introduced adapters can have a qualified regression identity even
    # though they did not exist at P0. Never infer expected identity from live bytes.
    expected = previous['after_sha256'] if previous else baseline.get(rel)
    if expected is None:
        expected = json.loads((OUT / 'REGRESSION.json').read_text())['host_sources'][rel]
    path = H / rel
    before = path.read_bytes()
    assert hashlib.sha256(before).hexdigest() == expected, 'Concurrent source change: ' + rel
    source = before.decode('utf-8').replace('\r\n', '\n')
    updated = transform(source)
    ast.parse(updated)
    backup = OUT / 'rollback' / ('step-' + str(len(rows) + 1)) / rel
    backup.parent.mkdir(parents=True, exist_ok=True)
    with backup.open('xb') as stream:
        stream.write(before)
    path.write_text(updated, encoding='utf-8', newline='\n')
    with (OUT / 'AUTHORITY_SWITCH_RECEIPTS.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'file': rel, 'authority': authority, 'before_sha256': expected,
                                'after_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'rollback': str(backup),
                                'status': 'SWITCHED_PENDING_REGRESSION'}) + '\n')


def certificates(source):
    target = "    obligations=goal_state.get('obligations',{})"
    source = source.replace(target, target + "\n    from cgkn.adapters.veriarbor.certificate_adapter import certificates\n    reusable_certificates=certificates(goal_state)", 1)
    target = "'receipt_hash':(g.get('evidence') or {}).get('receipt_hash')}"
    assert target in source
    return source.replace(target, "'receipt_hash':(g.get('evidence') or {}).get('receipt_hash'),\n            'capability_certificate':reusable_certificates[g['id']].fingerprint if g['id'] in reusable_certificates else None}", 1)


def progress(source):
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ProgressGuidedBacktracking')
    lines = source.splitlines(keepends=True)
    return ''.join(lines[:node.lineno - 1]) + 'from veriarbor.learning import ProgressGuidedBacktracking\n' + ''.join(lines[node.end_lineno:])


def scheduler(source):
    source = replace_function(source, '_compatible', '''    @staticmethod
    def _compatible(left, right) -> bool:
        from cgkn.adapters.veriarbor.dag_adapter import compatible
        return compatible(left, right)''')
    old = '''                    if any(not self._compatible(self._effective_config(node), self._effective_config(dag.by_id[other]))
                           for other in inflight.values()):
                        continue'''
    new = '''                    from cgkn.adapters.veriarbor.dag_adapter import select_batch
                    candidates = {key: self._effective_config(dag.by_id[key]) for key in pending
                                  if all(state.nodes[d].status == 'SUCCEEDED' for d in dag.by_id[key].depends_on)
                                  and not any(sum(dag.by_id[n].config.get('capacity_claims', {}).get(k, 0)
                                                  for n in inflight.values()) + value > self.resource_limits[k]
                                              for k, value in dag.by_id[key].config.get('capacity_claims', {}).items())}
                    chosen = select_batch(candidates, slots=self.max_parallel,
                                          running=[(other, self._effective_config(dag.by_id[other])) for other in inflight.values()])
                    if node_id not in chosen:
                        continue'''
    assert old in source
    return source.replace(old, new, 1)


if __name__ == '__main__':
    phase = sys.argv[1]
    if phase == 'certificates':
        edit('cgkn/protocol/context_pack.py', certificates, 'Current authenticated certificate lookup in bounded context')
    elif phase == 'backtracking':
        edit('cgkn/protocol/progress.py', progress, 'Progress/backtracking recommendation')
        edit('cgkn/protocol/repair.py', lambda s: replace_function(s, 'repair_progress', 'from veriarbor.learning import repair_progress'), 'Repair progress policy')
    elif phase == 'parallel':
        edit('cgkn/runtime/dag_runner.py', scheduler, 'Conflict graph parallel batch selection')
    elif phase == 'review':
        edit('cgkn/protocol/review_policy.py', lambda s: '"""Compatibility imports; generic policy lives in VeriArbor."""\nfrom veriarbor.review import review_kind, evaluator_disposition, qualify_evaluator, review_needed\n', 'Review classification and evaluator qualification')
    elif phase == 'backjump':
        def add_recommendation(source):
            target = "            history[-1]['progress_backtracking']=ProgressGuidedBacktracking.assess(before,after)"
            assert target in source
            return source.replace(target, target + "\n            from cgkn.adapters.veriarbor.backtracking_adapter import recommendation\n            history[-1]['non_chronological_backtracking']=recommendation(context.tree, contract['strategy_fingerprint'])", 1)
        edit('cgkn/protocol/repair.py', add_recommendation, 'Exact-fingerprint non-chronological checkpoint recommendation')
    elif phase == 'evidence-shape':
        def evidence_shape(source):
            old = "'allowed_evidence_refs':[ref for f in failures for ref in f.get('evidence_refs',[])],"
            assert old in source
            source = source.replace(old, old + "\n            'expected_type':'array', 'minimum_items':1,", 1)
            old = 'In hypothesis.falsifying_evidence copy at least one exact allowed_evidence_refs value, including its path and receipt_hash/sha256 fields.'
            new = 'Set hypothesis.falsifying_evidence to a JSON ARRAY containing at least one exact allowed_evidence_refs value, including its path and receipt_hash/sha256 fields. Even one reference must be wrapped in an array; a bare object is invalid. In a patches response the replacement value must be that array.'
            assert old in source
            return source.replace(old, new, 1)
        edit('cgkn/protocol/progress.py', evidence_shape, 'Explicit nested evidence-array correction contract; no inference or weakened admission')
    elif phase == 'semantic-anchor':
        def anchor(source):
            old = "                    'allowed_patches':fragments,"
            assert old in source
            return source.replace(old, old + "\n                    'task_anchor':{key:copy.deepcopy(patch_base[key]) for key in ('goal','expected','strategy','hypothesis') if key in patch_base},\n                    'task_anchor_policy':'Read-only original task semantics. Correct the listed fields for this task, not the planning protocol. Patch authority is unchanged.',", 1)
        edit('cgkn/protocol/exchange.py', anchor, 'Preserve read-only original task semantics during bounded field correction')
        def missing_hypothesis(source):
            old = "raise ContractError('FALSIFIED_HYPOTHESIS_REQUIRED', fields=('hypothesis',), repair_class='R6')"
            assert old in source
            return source.replace(old, """raise ContractError('FALSIFIED_HYPOTHESIS_REQUIRED', fields=('hypothesis',), repair_class='R5', details={
            'admission_status':'REPAIRABLE_SEMANTIC',
            'required_properties':list(required),
            'allowed_evidence_refs':[ref for f in failures for ref in f.get('evidence_refs',[])],
            'semantic_patch_policy':{'allowed_paths':[['hypothesis']],
                'immutable_paths':[['action'],['target'],['goal'],['scope'],['deps'],['strategy'],['expected'],['accept']]},
            'instruction':'Supply only the missing or incomplete hypothesis for the unchanged original task. Include previous, new, expected_novel_delta and falsifying_evidence. Previous and new must differ meaningfully. falsifying_evidence must be a nonempty JSON array of exact allowed_evidence_refs. The host will revalidate all bindings and no-progress constraints; no implementation or acceptance changes.'})""", 1)
        edit('cgkn/protocol/progress.py', missing_hypothesis, 'Bounded Provider-authored missing hypothesis correction, retaining strict evidence and no-progress validation')
    else:
        raise ValueError(phase)
