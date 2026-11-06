from migrate_next import edit


def projection(source):
    old="                        if verified['status']!='TRUSTED':row['verdict']='INSUFFICIENT_EVIDENCE'"
    new=old+"\n                        else:row['verdict']=verified['chain']['verdict']"
    assert old in source
    return source.replace(old,new,1)


def provenance(source):
    old="""            report=self.verify_check(result,goal,{k:view['subject_identities'][k] for k in goal['subject_refs']})
            if report['status']!='TRUSTED':raise ProvenanceError(report['status'],report['reason'])
            chains.append(report['chain'])"""
    new="""            current_subjects={k:view['subject_identities'][k] for k in goal['subject_refs']}
            effective_subjects=evidence.get('effective_subjects')
            if evidence.get('certified_substitutions'):
                from cgkn.adapters.veriarbor.substitution_adapter import replacements, reuse_cover
                with self.read_binding_snapshot():
                    proofs, checkers = replacements(acceptance, self)
                    cover = reuse_cover(goal, evidence, current_subjects, proofs, checkers)
                if not cover or cover != evidence['certified_substitutions'] or effective_subjects != current_subjects:
                    raise ProvenanceError('STALE','certified replacement no longer covers current dependencies')
                report=self.verify_check(result,goal,evidence['subjects'])
                if report['status']=='TRUSTED':
                    report['chain']={**report['chain'],'certified_substitutions':cover,
                                     'effective_subjects':current_subjects}
            else:
                report=self.verify_check(result,goal,current_subjects)
            if report['status']!='TRUSTED':raise ProvenanceError(report['status'],report['reason'])
            chains.append(report['chain'])"""
    assert old in source
    return source.replace(old,new,1)


def adapter(source):
    old="    return proof\n\n\n"
    new="    return {**proof, 'checked_at': raw['ended_at']}\n\n\n"
    assert old in source
    source=source.replace(old,new,1)
    source=source.replace("('sha256:' + row['receipt_hash'],), 'original-check:' + row['attempt_id'])",
                          "('sha256:' + row['receipt_hash'],), proof['checked_at'])",1)
    old="""        historical = [r for r in rows if r['verdict'] == 'VERIFIED' and r['subjects'] != wanted
                      and all(r['subjects'].get(p) == wanted.get(p) for p in dependencies)]"""
    new="""        own = set(goal['subject_refs']) - dependencies
        historical = [r for r in rows if r['verdict'] == 'VERIFIED'
                      and any(r['subjects'].get(p) != wanted.get(p) for p in own)]"""
    assert old in source
    source=source.replace(old,new,1)
    old="""                # Do not infer equivalence when the owner's own dependencies
                # also changed; that needs a separate local composition proof.
                if any(old_row['subjects'].get(p) != wanted.get(p) for p in dependencies):
                    continue"""
    new="""                # Both original and new native independent checks cover the
                # entire frozen owner+dependency subject set. The new native
                # check is also its current local-composition witness; a derived
                # owner check is never accepted as a new replacement root."""
    assert old in source
    return source.replace(old,new,1)


if __name__=='__main__':
    edit('cgkn/state/acceptance.py',projection,
         'Authenticated raw checker verdict overrides mutable cached verdict labels')
    edit('cgkn/state/provenance.py',provenance,
         'Final provenance authenticates original receipt plus freshly derived replacement certificate chain')
    edit('cgkn/adapters/veriarbor/substitution_adapter.py',adapter,
         'Bind certificate creation to actual check time; native full owner+dependency acceptance witnesses local composition')
