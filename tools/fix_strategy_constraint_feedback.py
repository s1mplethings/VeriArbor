from migrate_next import edit

def transform(source):
    marker='def check_strategy_constraints(strategy, paths, constraints):'
    helper='''def _strategy_constraint_correction(rule, **detail):
    return {'admission_status':'REPAIRABLE_SEMANTIC', **detail,
        'allowed_values':{k:rule.get(k,[] if k!='dimension_types' else {}) for k in
                          ('required_dimensions','dimension_types','forbidden_patterns')},
        'semantic_patch_policy':{'allowed_paths':[['strategy']],
            'immutable_paths':[['action'],['target'],['task_kind'],['goal'],['scope'],['deps'],
                               ['capability'],['expected'],['accept'],['hypothesis']]},
        'instruction':'Replace only strategy, preserving its existing valid mechanism dimensions and adding or correcting the explicitly required dimensions with the declared JSON types. Obey forbidden_patterns. Return the requested patches object; do not change task, scope, dependencies, hypothesis, acceptance or evidence. The host supplies constraints only, never a product implementation, and revalidates the entire proposal.'}


'''
    assert marker in source;source=source.replace(marker,helper+marker,1)
    old="raise ContractError('STRATEGY_DIMENSIONS_REQUIRED',fields=('strategy',),repair_class='R6',\n                                details={'required_dimensions':rule.get('required_dimensions',[])})"
    new="raise ContractError('STRATEGY_DIMENSIONS_REQUIRED',fields=('strategy',),repair_class='R5',\n                                details=_strategy_constraint_correction(rule, required_dimensions=rule.get('required_dimensions',[])))"
    assert old in source;source=source.replace(old,new,1)
    old="raise ContractError('STRATEGY_DIMENSION_TYPE',fields=('strategy',),repair_class='R6',details={'dimension':key,'required_type':kind})"
    new="raise ContractError('STRATEGY_DIMENSION_TYPE',fields=('strategy',),repair_class='R5',details=_strategy_constraint_correction(rule, dimension=key, required_type=kind))"
    assert old in source;return source.replace(old,new,1)

if __name__=='__main__':
    edit('cgkn/protocol/progress.py',transform,'Correct missing/mistyped explicit strategy dimensions through exact strategy-only bounded patch; retain falsified strategy rejection')
