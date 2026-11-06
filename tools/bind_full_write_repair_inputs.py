"""Keep full-file repairs grounded in existing scoped source, not filename guesses."""
from migrate_next import edit

def executor(source):
    old='''            for _ in range(self.max_rounds):
                raw_prompt = json.dumps({**prompt, "observations": observations}, ensure_ascii=False, sort_keys=True)
'''
    new='''            repair=context['node_config'].get('repair_contract',{})
            if (context['node_config'].get('action_version')==2
                    and repair.get('strategy_semantics',{}).get('full_file_write') is True):
                # A complete replacement needs the current scoped target as a
                # real input. Existing bounds and path confinement still apply.
                for name in sorted(contract.get('target_scope',())):
                    target=self.actions._path(name)
                    if not target.exists():
                        continue  # New targets have no prior implementation.
                    raw=target.read_bytes()
                    try:content=raw.decode('utf-8')
                    except UnicodeDecodeError as exc:
                        raise PermissionError('repair target is not UTF-8 text') from exc
                    import hashlib
                    observations.append({'action':'read_file','path':name,'content':content,
                        'sha256':hashlib.sha256(raw).hexdigest(),'input_origin':'existing_repair_target'})
            for _ in range(self.max_rounds):
                raw_prompt = json.dumps({**prompt, "observations": observations}, ensure_ascii=False, sort_keys=True)
'''
    assert source.count(old)==1
    return source.replace(old,new,1)

def projection(source):
    old="""    if config.get('action_version')!=2 or not config.get('repair_contract'):
        return raw
    observations=[];refs=list(raw.get('verified_dependency_refs',[]))
"""
    new="""    if config.get('action_version')!=2 or not config.get('repair_contract'):
        return raw
    if config['repair_contract'].get('strategy_semantics',{}).get('full_file_write') is True:
        # Complete replacement must preserve declared dependency interfaces.
        # Retain the already hash-verified inputs; do not hide them behind
        # references and invite reconstruction from opaque filenames.
        # The normal context envelope remains the size/admission authority.
        return raw
    observations=[];refs=list(raw.get('verified_dependency_refs',[]))
"""
    assert source.count(old)==1
    return source.replace(old,new,1)

edit('cgkn/executors/llm.py',executor,'Supply current scoped UTF-8 target before declared full-file repair; preserve path confinement and validation')
edit('cgkn/protocol/context_pack.py',projection,'Retain verified declared dependency contents for full-file repair; unchanged context budget and one executor authority')
