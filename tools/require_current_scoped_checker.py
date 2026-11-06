from migrate_next import edit

def revisions(source):
    return source + '''

def required_scoped_checker_versions(gate, goals):
    """Current coverage for explicit scopes; raw historical receipts stay trusted.

    Legacy unscoped corrections retain their existing compatibility semantics.
    Once a requirement has a scoped qualification, its current PASS must use
    the latest applicable observer, including any subsequent global revision.
    """
    binding = gate.binding()
    revisions = binding.get('checker_revisions', {})
    scopes = {}
    for key, versions in revisions.items():
        scopes[key] = [(row, json.loads(gate.resolve(row['qualification_ref'])).get('requirement_scope'))
                       for row in sorted(versions.values(), key=lambda row: row['sequence'])]
    result = {}
    for goal in goals:
        required = set(goal.get('requirement_refs', ()))
        latest = None
        explicit_scope = False
        for row, scope in scopes.get(goal['checker'], ()):
            if scope is not None and not required.intersection(scope):
                continue
            latest = row['checker_version']
            explicit_scope = explicit_scope or scope is not None
        if explicit_scope:
            result[goal['id']] = latest
    return result
'''

def acceptance(source):
    old="        replacement_proofs, replacement_checkers = replacements(self, provenance_gate)"
    assert source.count(old)==1
    source=source.replace(old,old+"\n        from .checker_revision import required_scoped_checker_versions\n        required_versions = required_scoped_checker_versions(provenance_gate, plan['goals']) if provenance_gate else {}",1)
    old="            # A counterexample is not outvoted by a later independent PASS."
    assert source.count(old)==1
    source=source.replace(old,"""            required_version = required_versions.get(g['id'])
            if required_version:
                # A historical PASS remains authentic but does not cover newly
                # required scoped observations. Retain all counterexamples.
                effective = [r for r in effective if r['verdict'] != 'VERIFIED'
                             or r['observation'].get('checker_version') == required_version]
"""+old,1)
    old="        return {'obligations':obligations, 'hard_verdict':hard_verdict,"
    assert source.count(old)==1
    return source.replace(old,"        return {**({'required_checker_versions': required_versions} if required_versions else {}),\n                'obligations':obligations, 'hard_verdict':hard_verdict,",1)

def dedup(source):
    old="        checker = provenance.get('chain', {}).get('checker', {})"
    assert source.count(old)==1
    return source.replace(old,old+"\n        required_version = view.get('required_checker_versions', {}).get(goal['id'])\n        if required_version and checker.get('version') != required_version:\n            continue  # New scoped qualification is a new VerificationKey.",1)

edit('cgkn/state/checker_revision.py',revisions,'Resolve latest applicable scoped checker coverage while preserving historical authenticity and unrelated certificates')
edit('cgkn/state/acceptance.py',acceptance,'Current scoped coverage cannot be satisfied by older PASS; preserve counterexamples and raw history')
edit('cgkn/adapters/veriarbor/verification_adapter.py',dedup,'Allow new scoped checker VerificationKey without replaying an unchanged current measurement')
