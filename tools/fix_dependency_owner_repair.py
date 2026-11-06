"""Expose existing owners of authenticated failed-integration subjects."""
from migrate_next import edit

def transform(source):
    old="""        declarations = [a for c in contracts.values() for a in c['design']['artifacts']]
        documents = [c['registry'] for c in contracts.values()]"""
    new="""        # A failed integration may implicate a verified dependency. Expose its
        # original owner contract, never a fresh implementation or a rewritten
        # acceptance predicate. Only authenticated, current tested subjects qualify.
        identities=context.goal_acceptance.get('subject_identities',{})
        repair_paths={};repair_owners={};owner_rows=[]
        if context.goal_acceptance.get('evidence_mode')=='production_provenance':
            for failed in selected:
                evidence=failed.get('evidence') or {}
                if (failed.get('verdict')!='FAILED' or not evidence.get('receipt_hash')
                        or not evidence.get('node_id') or not evidence.get('attempt_id')
                        or evidence.get('provenance',{}).get('status')!='TRUSTED'):
                    continue
                failed_contract=failed.get('milestone_contract',{})
                subjects=evidence.get('subjects',{})
                bound={p for p in failed_contract.get('dependency_artifacts',[])
                       if p in failed.get('subject_refs',[]) and subjects.get(p)
                       and subjects[p]==identities.get(p)}
                for owner in goals:
                    if (owner['id'] not in failed_contract.get('dependency_goal_ids',[])
                            or owner.get('verdict')!='VERIFIED' or not owner.get('milestone_contract')):
                        continue
                    contract=owner['milestone_contract']
                    artifacts=[a for a in contract['design']['artifacts'] if a['path'] in bound]
                    if not artifacts:continue
                    key=contract['compilation']['milestone_id']
                    repair_owners[key]=contract
                    for artifact in artifacts:
                        path=artifact['path']
                        repair_paths.setdefault(failed['id'],set()).add(path)
                        owner_rows.append({'owner_goal_id':owner['id'],'path':path,
                            'subject_identity':subjects[path],'failed_goal_id':failed['id'],
                            'failure_receipt_hash':evidence['receipt_hash']})
        all_contracts={**repair_owners,**contracts}
        declarations = [a for c in contracts.values() for a in c['design']['artifacts']]
        repair_scope={p for paths in repair_paths.values() for p in paths}
        seen={a['path'] for a in declarations}
        for contract in repair_owners.values():
            for artifact in contract['design']['artifacts']:
                if artifact['path'] in repair_scope and artifact['path'] not in seen:
                    declarations.append(artifact);seen.add(artifact['path'])
        documents = [c['registry'] for c in all_contracts.values()]"""
    assert old in source;source=source.replace(old,new,1)
    old="            paths=[a['path'] for a in goal['milestone_contract']['design']['artifacts']]"
    assert old in source
    source=source.replace(old,old+"\n            paths=sorted(set(paths)|repair_paths.get(goal['id'],set()))",1)
    old="        document = snapshot.document\n        document['verified_frontier']="
    new="""        document = snapshot.document
        document['dependency_owner_repairs']=owner_rows
        document['dependency_owner_repair_policy']='Only current authenticated failed-integration subjects are exposed. Repair the existing owner with explicit evidence and its original contract; do not bypass it with a new writer or runtime monkeypatch. Unrelated subjects and owner tests remain read-only unless independently covered. This changes no acceptance verdict. Successful integration-source producers may be selected as bounded read dependencies where needed; preserve the original owner public contract.'
        document['verified_frontier']="""
    assert old in source;source=source.replace(old,new,1)
    old="        for contract in contracts.values():\n            dependency_paths="
    new="        for contract in all_contracts.values():\n            dependency_paths="
    assert old in source;return source.replace(old,new,1)

if __name__=='__main__':
    edit('cgkn/agent/composer.py',transform,
         'Expose original dependency owner scopes only for current provenance-authenticated failed integration subjects')
