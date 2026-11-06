from migrate_next import edit


def transform(source):
    old = """                    if (retry_contract.get('task_kind') in measurement_kinds
                            and contract['task_kind'] in measurement_kinds
                            and set(contract['target_scope']) & set(retry_contract['target_scope'])
                            and set(downstream_closure(dag, {node_id})) == {node_id}):"""
    new = """                    if (contract['task_kind'] in measurement_kinds
                            and set(downstream_closure(dag, {node_id})) == {node_id}):"""
    assert old in source
    source = source.replace(old, new, 1)
    source = source.replace("                    retry_contract = dag.by_id[retry_node].config['leaf_contract'] if retry_node else {}\n", '', 1)
    source = source.replace("                    # An explicit measurement retry must not deadlock against\n                    # another stale leaf measurement of the same object. Retire\n                    # its live success without executing it: it still requires\n                    # its own Agent retry and keeps every historical receipt.",
        "                    # A stale terminal observer is historical evidence, not\n                    # reusable current execution. Retire it without dispatching\n                    # another checker or blocking a bounded source repair.\n                    # Producer/consumer nodes still require their version proof.", 1)
    return source


if __name__ == '__main__':
    edit('cgkn/runtime/dag_runner.py', transform,
         'Retire stale terminal measurements without replay; preserve original evidence and reject stale producers/consumers')
