from migrate_next import edit


def transform(source):
    old="        subjects = evidence.get('subjects') or {}"
    new="""        substitutions = evidence.get('certified_substitutions') or {}
        subjects = (evidence.get('effective_subjects') if substitutions else evidence.get('subjects')) or {}
        replacement_refs = tuple(sorted({ref for proof in substitutions.values()
                                         for ref in proof.get('evidence_refs', ())}))"""
    assert old in source
    source=source.replace(old,new,1)
    old="            ('sha256:' + evidence['receipt_hash'],), ('sha256:' + stable_hash(provenance),),"
    new="            ('sha256:' + evidence['receipt_hash'],) + replacement_refs, ('sha256:' + stable_hash(provenance), 'sha256:' + stable_hash(substitutions)),"
    assert old in source
    return source.replace(old,new,1)


if __name__=='__main__':
    edit('cgkn/adapters/veriarbor/certificate_adapter.py',transform,
         'Project authenticated effective boundary certificates with original and replacement evidence refs')
