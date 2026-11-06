from migrate_next import edit
def transform(source):
    old="        subjects={**self.acceptance.view()['subject_identities'],**observed}\n        if subjects!=self.acceptance.view()['subject_identities']:\n            self.acceptance.bind_subjects(subjects)"
    new="""        # Only canonical subject metadata is needed here. Verdict consumers
        # still call view(), and record() still authenticates each new witness.
        # Reload validates immutable requirements/checker bindings; no cache or
        # acceptance certificate is trusted merely because metadata was read.
        self.acceptance._reload()
        current_subjects=dict(self.acceptance.data['subjects'])
        subjects={**current_subjects,**observed}
        if subjects!=current_subjects:
            self.acceptance.bind_subjects(subjects)"""
    assert old in source;source=source.replace(old,new,1)
    old="        self.acceptance.view()  # reload current canonical plan and subjects"
    new="        self.acceptance._reload()  # metadata only; record() authenticates every recovered witness"
    assert old in source;return source.replace(old,new,1)
if __name__=='__main__':
    edit('cgkn/agent/project_loop.py',transform,'Reload canonical metadata without unused global verdict rebuilds; preserve all actual view/record provenance checks')
