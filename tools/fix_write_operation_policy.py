"""Enforce an explicitly declared full-file repair strategy at the Worker gate."""
from migrate_next import edit

def adapter(source):
    old="        snapshot=TableSnapshot({'paths':[{'path':p,'readable':True,'writable':p in writable,\n            **({'observed_content_sha256':observed[p]} if p in observed else {})} for p in sorted(readable)]})"
    new="""        table={'paths':[{'path':p,'readable':True,'writable':p in writable,
            **({'observed_content_sha256':observed[p]} if p in observed else {})} for p in sorted(readable)]}
        strategy=raw['config'].get('repair_contract',{}).get('strategy_semantics',{})
        if strategy.get('full_file_write') is True:
            table['allowed_write_operations']=[2]
        snapshot=TableSnapshot(table)"""
    assert old in source;source=source.replace(old,new,1)
    old='Operation IDs: 0 read file, 1 list files, 2 write full file, 3 exact patch.'
    assert old in source
    return source.replace(old,old+' Obey table.allowed_write_operations when present: [2] means the declared repair strategy requires a complete full-file write and partial patches are rejected.',1)

def compiler(source):
    old="    if op in (0,1) and row.get('readable') is not True:raise ContractError('UNAUTHORIZED_READ',fields=('path',))"
    new="""    write_operations=snapshot.document.get('allowed_write_operations',[2,3])
    if op in (2,3) and op not in write_operations:
        raise ContractError('WRITE_OPERATION_POLICY_VIOLATION',fields=('op','payload'),repair_class='R6',
            vector_key='semantic_contradictions',details={
                'allowed_values':{'op':[0,1,*write_operations],'payload':'Complete file content string for op2; omit for reads'},
                'instruction':'The admitted strategy explicitly restricts write operations. For full_file_write=true use op2 with the complete current file and every required change. Changing only the opcode of a patch is invalid. Read/list and explicit missing-prerequisite escalation remain available. No implementation is supplied or transformed by this gate.'})
"""+old
    assert old in source;return source.replace(old,new,1)

if __name__=='__main__':
    edit('cgkn/protocol/adapters.py',adapter,
         'Carry explicit boolean full_file_write repair strategy to immutable Worker operation table')
    edit('cgkn/protocol/compiler.py',compiler,
         'Enforce explicitly narrowed Worker write operations without changing path authority or acceptance')
