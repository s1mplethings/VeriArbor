from migrate_next import edit


def project(source):
    old = "        document['dependency_owner_repairs']=owner_rows"
    new = "        from cgkn.adapters.veriarbor.verification_adapter import goal_verification_keys\n        document['verification_dedup']=goal_verification_keys(context.goal_acceptance)\n" + old
    assert old in source
    return source.replace(old, new, 1)


def guard(source):
    old = "            edit('retry_node',node_id,{})"
    new = "            from cgkn.adapters.veriarbor.verification_adapter import reject_duplicate_measurement\n            reject_duplicate_measurement(snapshot.document, node_id=node_id)\n" + old
    assert old in source
    source = source.replace(old, new, 1)
    old = "            paths=[s['path'] for s in scopes]"
    new = "            if kind in (4,5):\n                from cgkn.adapters.veriarbor.verification_adapter import reject_duplicate_measurement\n                reject_duplicate_measurement(snapshot.document, goal_id=cap.get('config',{}).get('goal_id'))\n" + old
    assert old in source
    return source.replace(old, new, 1)


if __name__ == '__main__':
    edit('cgkn/agent/composer.py', project, 'Project current authenticated VerificationKeys; retain original GoalAcceptance authority')
    edit('cgkn/protocol/compiler.py', guard, 'Reject duplicate independent measurement ADD/RETRY with no novel delta before DAG creation/execution')
