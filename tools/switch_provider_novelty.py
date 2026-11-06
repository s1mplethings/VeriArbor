"""Apply only at a settled controller boundary; no change to UNKNOWN recovery."""
from migrate_next import edit


def transform(source):
    old="""        logical = hashlib.sha256(json.dumps({'role':config['role'],'request':public},
            sort_keys=True,ensure_ascii=False).encode()).hexdigest()"""
    new="""        from cgkn.adapters.veriarbor.provider_novelty_adapter import request_novelty, novelty_disposition
        novelty = request_novelty(public, config['role'], execution)
        logical = hashlib.sha256(json.dumps(novelty, sort_keys=True, ensure_ascii=False).encode()).hexdigest()"""
    assert old in source
    source=source.replace(old,new,1)
    old="            for path in self.root.glob('*/request.json'):"
    new="            previous_novelty = []\n"+old
    assert old in source
    source=source.replace(old,new,1)
    old="                if prior.get('config',{}).get('role')!=config['role'] or prior.get('request')!=public:continue"
    new="""                if prior.get('config',{}).get('role') != config['role']:continue
                prior_error_path = path.with_name('error.json')
                prior_error = json.loads(prior_error_path.read_text(encoding='utf-8')) if prior_error_path.exists() else {}
                # A cooperative pre-dispatch hold consumed no upstream request.
                if prior_error.get('category') != 'controller_hold_before_dispatch':
                    old_novelty = prior.get('novelty') or request_novelty(prior['request'], config['role'], prior.get('execution_identity'))
                    previous_novelty.append(old_novelty)
                if prior.get('request') != public:continue"""
    assert old in source
    source=source.replace(old,new,1)
    old="            identity = uuid.uuid4().hex"
    new="""            if retry_admissions:
                # A verified local-effect reconciliation is new host evidence,
                # not a reset or replay of the upstream UNKNOWN receipt.
                novelty = {**novelty, 'evidence': hashlib.sha256(json.dumps(
                    {'request_evidence': novelty['evidence'], 'reconciliations': retry_admissions},
                    sort_keys=True, ensure_ascii=False).encode()).hexdigest()}
            if novelty_disposition(previous_novelty, novelty) == 'NO_NOVEL_DELTA':
                from cgkn.state import EventRecord
                self.store.append_event(EventRecord(uuid.uuid4().hex, self.project_id, self.run_id,
                    'PROVIDER_NOVELTY_DENIED', data={'scope': novelty['scope'], 'dimensions': novelty,
                    'reason': 'NO_NOVEL_DELTA', 'provider_dispatched': False}))
                raise GatewayCompletionError('NO_NOVEL_DELTA',
                    'No new variant, artifact, contract, evidence or checker qualification; original request retained')
            identity = uuid.uuid4().hex"""
    assert old in source
    source=source.replace(old,new,1)
    old="                'reconciled_retry_admissions': retry_admissions})"
    new="                'reconciled_retry_admissions': retry_admissions, 'novelty': novelty})"
    assert old in source
    return source.replace(old,new,1)


if __name__=='__main__':
    edit('cgkn/providers/recording.py',transform,
         'Every recorded Provider call binds novelty before dispatch; existing request log and UNKNOWN recovery remain authoritative')
