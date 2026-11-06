"""Retain registry provenance without treating sibling growth as owner drift."""
from migrate_next import edit

def transform(source):
    old="    before=plain(before);after=plain(after);changes=[]\n    def walk(a,b,path):"
    new="""    before=plain(before);after=plain(after);changes=[]
    # select() binds an exact contract slice to its containing registry. Adding
    # a different owner changes that container hash, not these immutable entries.
    # Compare every byte-valued entry field first; never ignore nested fields,
    # versions, source decisions, evidence, or an actual contract change.
    if (isinstance(before,dict) and isinstance(after,dict)
            and set(before)==set(after)=={'registry_hash','entries'}
            and isinstance(before['entries'],list) and before['entries']
            and before['entries']==after['entries']):
        return {'changes':[],'drift_count':0,'semantic_equivalence':'UNCHANGED',
                'removed_requirements':[],'added_requirements':[],'possible_weakening':[],
                'registry_context_change':({'before':before['registry_hash'],'after':after['registry_hash']}
                    if before['registry_hash']!=after['registry_hash'] else None)}
    def walk(a,b,path):"""
    assert old in source;return source.replace(old,new,1)

if __name__=='__main__':
    edit('cgkn/protocol/repair.py',transform,
         'Preserve exact scoped public contract identity across unrelated registry-owner additions; retain changed container provenance')
