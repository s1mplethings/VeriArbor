"""Install generic, caller-authorized patch policy in the existing executor."""
from migrate_next import edit

HELPER = r'''
def plan_bounded_patches(actions, root, policy):
    """Pure preflight; no effects until every patch satisfies the frozen policy."""
    import difflib, hashlib, io, re
    if not isinstance(policy, Mapping) or policy.get('mode') != 'patch_only':
        raise ProposalError('INVALID_PATCH_POLICY')
    specs = policy.get('files', {})
    if not isinstance(specs, Mapping) or not specs:
        raise ProposalError('INVALID_PATCH_POLICY')
    planned = {}; receipts = []
    for action in actions:
        if action['action'] in {'read_file', 'list_files'}:
            continue
        name = BoundedFileActions(root)._path(action['path']).relative_to(root).as_posix()
        if action['action'] != 'patch_file' or name not in specs:
            raise ProposalError('PATCH_SCOPE_EXCEEDED: only authorized patch_file actions')
        planned.setdefault(name, []).append(action)
    if not planned:
        raise ProposalError('NO_IMPLEMENTATION_DELTA: no patch actions')
    outputs = {}
    for name, patches in planned.items():
        raw = (root / name).read_bytes(); original = raw.decode('utf8')
        before_hash = hashlib.sha256(raw).hexdigest(); spec = specs[name]
        if before_hash != spec.get('source_sha256'):
            raise ProposalError('OBJECT_VERSION_MISMATCH: patch policy source changed')
        # Universal-newline view matches read_file; map every character back to
        # original bytes so an exact patch cannot rewrite unrelated line endings.
        normalized = []; offsets = []; position = 0
        for match in re.finditer(r'\r\n|\r|\n|[^\r\n]', original):
            offsets.append(match.start())
            normalized.append('\n' if match.group() in {'\r\n','\r','\n'} else match.group())
        offsets.append(len(original)); text = ''.join(normalized)
        ranges = spec.get('ranges', [])
        if not ranges or any(not isinstance(r, (list,tuple)) or len(r)!=2
                or any(type(x) is not int for x in r) or not 0<=r[0]<r[1]<=len(text) for r in ranges):
            raise ProposalError('INVALID_PATCH_POLICY: source-bound character ranges required')
        changes = []
        for action in patches:
            find = io.StringIO(action['find'], newline=None).read()
            replacement = io.StringIO(action['replace'], newline=None).read()
            if not find or text.count(find) != 1:
                raise ProposalError('PATCH_SCOPE_EXCEEDED: ambiguous patch anchor')
            start = text.index(find); end = start + len(find)
            if not any(a<=start and end<=b for a,b in ranges):
                raise ProposalError('PATCH_SCOPE_EXCEEDED: patch outside authorized region')
            if find == replacement:
                raise ProposalError('NO_IMPLEMENTATION_DELTA: unchanged patch')
            if any(start < old_end and old_start < end for old_start,old_end,_ in changes):
                raise ProposalError('PATCH_SCOPE_EXCEEDED: overlapping patches')
            changes.append((start,end,replacement))
        changed_chars = sum((end-start)+len(replacement) for start,end,replacement in changes)
        limit = spec.get('max_changed_chars')
        if type(limit) is not int or limit<=0 or changed_chars>limit:
            raise ProposalError('PATCH_SCOPE_EXCEEDED: change budget exceeded')
        result = original
        newline = '\r\n' if '\r\n' in original else '\n'
        for start,end,replacement in sorted(changes,reverse=True):
            result = result[:offsets[start]] + replacement.replace('\n',newline) + result[offsets[end]:]
        result = result.encode('utf8')
        after_hash = hashlib.sha256(result).hexdigest()
        if after_hash == before_hash:
            raise ProposalError('NO_IMPLEMENTATION_DELTA')
        outputs[name] = result
        receipts.append({'path':name,'before_sha256':before_hash,'after_sha256':after_hash,
            'policy_source_sha256':spec['source_sha256'],'changed_ranges':[
                {'start_char':start,'end_char':end,'start_line':text.count('\n',0,start)+1,
                 'end_line':text.count('\n',0,end)+1,'replacement_sha256':hashlib.sha256(replacement.encode()).hexdigest()}
                for start,end,replacement in changes], 'verdict':'BOUNDED_PATCH_WITH_SOURCE_DELTA'})
    return outputs, receipts

'''

def transform(source):
    anchor='class LLMExecutor:'
    assert anchor in source
    source=source.replace(anchor,HELPER+'\n'+anchor,1)
    source=source.replace('semantic_protocol=False, protocol_trace=None):','semantic_protocol=False, protocol_trace=None, patch_policy=None):',1)
    anchor='        self.max_rounds = max_rounds'
    source=source.replace(anchor,anchor+'\n        self.patch_policy = patch_policy',1)
    anchor="            repair=context['node_config'].get('repair_contract',{})"
    source=source.replace(anchor,"            if self.patch_policy:\n                context['bounded_patch_policy'] = self.patch_policy\n"+anchor,1)
    # A patch policy supplies existing target inputs without requiring a false
    # full_file_write strategy. Scope and hashes remain controller-owned.
    source=source.replace("and repair.get('strategy_semantics',{}).get('full_file_write') is True):",
        "and (repair.get('strategy_semantics',{}).get('full_file_write') is True or self.patch_policy)):",1)
    anchor="            results = list(observations)\n            try:\n                for action in proposal['actions']: results.append(self.actions.apply(action))"
    replacement="""            results = list(observations)
            bounded_receipts = []
            bounded_outputs = None
            if self.patch_policy:
                bounded_outputs, bounded_receipts = plan_bounded_patches(proposal['actions'], self.actions.root, self.patch_policy)
            try:
                if bounded_outputs is not None:
                    for name, content in bounded_outputs.items():
                        self.actions._path(name).write_bytes(content)
                        results.append({'action':'patch_file','path':name,'bytes':len(content)})
                else:
                    for action in proposal['actions']: results.append(self.actions.apply(action))"""
    assert anchor in source;source=source.replace(anchor,replacement,1)
    anchor='metadata={"proposal": proposal,**finish_disposition(completion.raw_finish_reason)})'
    assert anchor in source
    source=source.replace(anchor,'metadata={"proposal": proposal,"bounded_patch_receipts":bounded_receipts,**finish_disposition(completion.raw_finish_reason)})',1)
    return source

if __name__=='__main__':
    edit('cgkn/executors/llm.py',transform,'Generic source-bound patch-only scope and no-delta gate before candidate writes')
    def wire(s):
        old='execution_registry.register(LLMExecutor(root,client,worker,max_rounds=4,semantic_protocol=True,protocol_trace=trace))'
        assert old in s
        return s.replace(old,'execution_registry.register(LLMExecutor(root,client,worker,max_rounds=4,semantic_protocol=True,protocol_trace=trace,\n            patch_policy=(continuation_feedback or {}).get("bounded_patch_policy")))',1)
    edit('cgkn/application/software_project/service.py',wire,'Caller-authorized bounded patch policy passed to original executor; no replacement authority')
