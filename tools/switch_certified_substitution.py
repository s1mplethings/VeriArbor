from migrate_next import edit


def integrate(source):
    old = "        rows = []\n        for g in plan['goals']:"
    new = """        from cgkn.adapters.veriarbor.substitution_adapter import replacements, reuse_cover
        replacement_proofs, replacement_checkers = replacements(self, provenance_gate)
        rows = []
        for g in plan['goals']:"""
    assert old in source
    source = source.replace(old, new, 1)
    old = """            matching = [r for r in self.data['checks'] if r['goal_id'] == g['id']
                        and r['subjects'] == subjects and r['condition_hash'] == identity(g['acceptance'])]"""
    new = """            matching = []
            for historical in self.data['checks']:
                if historical['goal_id'] != g['id'] or historical['condition_hash'] != identity(g['acceptance']):
                    continue
                if historical['subjects'] == subjects:
                    matching.append(historical)
                    continue
                peers = [r for r in self.data['checks'] if r['goal_id'] == g['id']
                         and r['subjects'] == historical['subjects']
                         and r['condition_hash'] == historical['condition_hash']]
                superseded_peers = {h for r in peers for h in r.get('supersedes_receipts', ())}
                if historical['receipt_hash'] in superseded_peers or any(r['verdict'] != 'VERIFIED'
                        for r in peers if r['receipt_hash'] not in superseded_peers):
                    continue
                cover = reuse_cover(g, historical, subjects, replacement_proofs, replacement_checkers)
                if cover:
                    matching.append({**historical, 'certified_substitutions': cover,
                                     'effective_subjects': subjects})"""
    assert old in source
    source = source.replace(old, new, 1)
    old = "                        verified=gate.verify_check(BlockExecutionResult.from_dict(raw),g,subjects)"
    new = "                        verified=gate.verify_check(BlockExecutionResult.from_dict(raw),g,row['subjects'])"
    assert old in source
    return source.replace(old, new, 1)


if __name__ == '__main__':
    edit('cgkn/state/acceptance.py', integrate,
         'Certified identical dependency substitution; authenticate original receipt and independent replacement; preserve original subjects and failure dominance')
