from migrate_next import edit

def change(source):
    old = "'allowed_read_paths', 'allowed_write_paths'))"
    assert source.count(old) == 1
    source = source.replace(old, "'allowed_read_paths', 'allowed_write_paths',\n        'current_requirements', 'dependency_contracts'))", 1)
    old = "'error', 'rejection', 'invalid_payload', 'failed_acceptance_ids', 'expansions'))"
    assert source.count(old) == 1
    return source.replace(old, "'error', 'rejection', 'invalid_payload', 'failed_acceptance_ids', 'expansions',\n        'verified_state', 'unresolved_acceptance', 'failure_details'))", 1)

edit('cgkn/adapters/veriarbor/provider_novelty_adapter.py', change,
     'Retain current milestone public requirements/dependency contracts and acceptance evidence in request novelty; different milestone contracts must not collide')
