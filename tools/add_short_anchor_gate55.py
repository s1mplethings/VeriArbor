from migrate_next import edit
def transform(source):
    old="            replacement = io.StringIO(action['replace'], newline=None).read()\n            if not find or text.count(find) != 1:"
    new="""            replacement = io.StringIO(action['replace'], newline=None).read()
            anchor_limit = spec.get('max_anchor_chars')
            if anchor_limit is not None:
                if type(anchor_limit) is not int or anchor_limit <= 0:
                    raise ProposalError('INVALID_PATCH_POLICY: positive anchor limit required')
                if len(find) > anchor_limit:
                    raise ProposalError('PATCH_SCOPE_EXCEEDED: anchor length budget exceeded')
            if not find or text.count(find) != 1:"""
    assert source.count(old)==1
    return source.replace(old,new)
edit('cgkn/executors/llm.py',transform,'Optional source-bound short-anchor budget; reject oversized anchors atomically without changing match semantics')
