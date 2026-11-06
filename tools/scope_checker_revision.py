from migrate_next import edit

def qualify(source):
    needle="    for control in controls:\n"
    insert="""    scope = proof.get('requirement_scope')
    if scope is not None and (not isinstance(scope, list) or not scope
            or any(not isinstance(item, str) or not item for item in scope)
            or len(set(scope)) != len(scope)
            or not set(scope) <= set(gate.binding()['requirements'])):
        raise ProvenanceError('INVALID_PROVENANCE', 'invalid qualified checker requirement scope')
"""
    # Do not recursively load binding while the revision lineage is loading.
    insert=insert.replace("\n            or not set(scope) <= set(gate.binding()['requirements'])", "")
    assert source.count(needle)==1
    return source.replace(needle,insert+needle)

def execute(source):
    needle='        self.checker_revision_ref = None\n'
    source=source.replace(needle,needle+'        self._revision_scope = None\n        self._previous_executor = None\n',1)
    needle="                self.consumer_path = store.root/qualified_revision['source_ref']['path']"
    insert="""                gate = ProvenanceGate(store, session_acceptance.project_id, session_acceptance.run_id)
                qualification = gate.resolve(qualified_revision['qualification_ref'], 'CheckerRevisionQualification')
                scope = qualification.get('requirement_scope')
                if scope is not None:
                    if not set(scope) <= set(binding['requirements']):
                        raise ValueError('checker scope contains unknown requirements')
                    self._revision_scope = frozenset(scope)
                    previous = next((row for row in binding.get('checker_revisions', {}).get(
                        qualified_revision['checker_key'], {}).values()
                        if row['checker_hash'] == qualified_revision['previous_checker_hash']
                        and row['sequence'] < qualified_revision['sequence']), None)
                    if previous is None and qualified_revision['previous_checker_hash'] != self.consumer['sha256']:
                        raise ValueError('scoped checker previous version missing')
                    self._previous_executor = ExternalAcceptanceExecutor(self.project_root,
                        self.acceptance_root, session_acceptance=session_acceptance,
                        consumer=dict(self.consumer), qualified_revision=previous)
"""
    assert source.count(needle)==1;source=source.replace(needle,insert+needle)
    needle="            if a.checkers[goal['checker']]!=self.descriptor.executor_ref:"
    insert="""            if self._revision_scope is not None and not self._revision_scope.intersection(goal['requirement_refs']):
                # Scope is authenticated qualification metadata, never supplied by a Worker.
                # Keep the original checker identity for unrelated unchanged predicates.
                return self._previous_executor.execute(request)
"""
    assert source.count(needle)==1
    return source.replace(needle,insert+needle)

edit('cgkn/state/checker_revision.py',qualify,'Validate optional explicit requirement scope on authenticated checker qualifications')
edit('cgkn/application/software_project/acceptance.py',execute,'Apply qualified observer revision only to its declared requirements; preserve previous checker identity outside scope')
