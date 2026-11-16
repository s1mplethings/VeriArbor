"""Evidence-bound failure constraints and non-chronological recommendations."""
from dataclasses import dataclass, replace
from .model import stable_hash


class StrategyError(ValueError):
    pass


def strategy_fingerprint(strategy):
    if not isinstance(strategy, dict) or not strategy.get('problem') or len(strategy) < 3:
        raise StrategyError('SEMANTIC_STRATEGY_REQUIRED')

    def normalize(value):
        if isinstance(value, str):
            return ' '.join(value.casefold().split())
        if isinstance(value, dict):
            return {str(k).casefold(): normalize(v) for k, v in value.items()}
        if isinstance(value, list):
            return [normalize(v) for v in value]
        if value is None or type(value) in (bool, int, float):
            return value
        raise StrategyError('INVALID_STRATEGY_DIMENSION')

    normalized = normalize(strategy)
    if any(k in normalized for k in ('prompt', 'code', 'rationale', 'timestamp')):
        raise StrategyError('STRATEGY_MUST_DESCRIBE_MECHANISM')
    return stable_hash(normalized)


def repeated_no_progress(strategy, failure, evidence_hashes, history):
    return any(row.get('strategy_fingerprint') == strategy
               and row.get('failure_fingerprint') == failure
               and row.get('status') in {'REPAIR_NO_PROGRESS', 'REPAIR_REGRESSION'}
               and set(row.get('failure_evidence_hashes', ())) == set(evidence_hashes)
               for row in history)


@dataclass(frozen=True)
class LearnedNogood:
    scope: str
    forbidden_conditions: tuple[str, ...]
    consequence: str
    failure_fingerprint: str
    strategy_family: str
    versions: dict[str, str]
    evidence_refs: tuple[str, ...]
    confidence: str = 'UNQUALIFIED'
    evaluator_status: str = 'INVALID_EVALUATOR'
    activity: float = 0
    reuse_count: int = 0
    expires_at: float | None = None

    def matches(self, *, scope, conditions, versions, strategy_family, now):
        return (self.confidence == 'VERIFIED_COUNTEREXAMPLE' and self.evaluator_status == 'QUALIFIED'
                and bool(self.evidence_refs) and bool(self.forbidden_conditions)
                and self.scope == scope and self.strategy_family == strategy_family
                and (self.expires_at is None or now < self.expires_at)
                and all(versions.get(k) == v for k, v in self.versions.items())
                and set(self.forbidden_conditions) <= set(conditions))


def minimize_conflict(assumptions, reproduces):
    """Deterministic deletion minimization; returns a 1-minimal conflict.

    The host supplies a frozen, qualified deterministic checker. This is not
    a global minimum proof and never invokes an executor/provider itself.
    """
    current = tuple(sorted(set(assumptions)))
    if not reproduces(current):
        raise ValueError('initial assumptions do not reproduce failure')
    changed = True
    while changed:
        changed = False
        for item in current:
            candidate = tuple(x for x in current if x != item)
            if reproduces(candidate):
                current, changed = candidate, True
                break
    return current


@dataclass(frozen=True)
class DecisionCheckpoint:
    id: str
    sequence: int
    introduced_conditions: tuple[str, ...]
    rollback_ref: str
    affected_nodes: tuple[str, ...] = ()


def backtrack(conflict, checkpoints):
    """Earliest relevant introduction; no state mutation or sibling invalidation."""
    conflict = set(conflict)
    candidates = [c for c in checkpoints if conflict.intersection(c.introduced_conditions)]
    return min(candidates, key=lambda c: (c.sequence, c.id)) if candidates else None


class ProgressGuidedBacktracking:
    """Compare Host-authenticated snapshots; never grant acceptance.

    `verified`/`failed` are technical checks. `acceptance` contains satisfied
    Root Goal obligations, and `gaps` maps IDs to GoalGap measurements derived
    from qualified outcome/utility evidence (not proxy scores). Missing baseline
    measurements are not improvements. The Host owns authentication and binding.
    """
    @staticmethod
    def assess(before, after, previous_attempts=()):
        verified_before=set(before.get('acceptance',[]));verified_after=set(after.get('acceptance',[]))
        failed_before=set(before.get('failed',[]));failed_after=set(after.get('failed',[]))
        before_gaps, after_gaps = before.get('gaps', {}), after.get('gaps', {})
        improved, worsened = [], []
        for key in before_gaps.keys() & after_gaps.keys():
            old, new = before_gaps[key], after_gaps[key]
            # A changed target, scope or weighting is not a comparable experiment.
            if (old.current is None or new.current is None or old.root_impact <= 0 or old.evidence_confidence <= 0 or
                    replace(old, current=None, status='OPEN') != replace(new, current=None, status='OPEN')):
                continue
            delta = (new.current-old.current if old.comparison == '>=' else
                     old.current-new.current if old.comparison == '<=' else
                     abs(old.target-old.current)-abs(new.target-new.current))
            if delta > 0: improved.append(key)
            if delta < 0: worsened.append(key)
        diagnostic = sorted(key for key, gap in after_gaps.items() if gap.requires_diagnosis)
        if verified_before-verified_after or failed_after-failed_before or worsened or after.get('contract_drift'):
            status,operation='REGRESSION','AFFECTED_SUBGRAPH_REPLAN'
        elif verified_after-verified_before or improved:
            status,operation='PROGRESS','CONTINUE'
        elif (before_gaps != after_gaps or failed_before-failed_after
              or set(after.get('verified',[]))-set(before.get('verified',[]))
              or (after.get('artifact_delta_validated') and not before.get('artifact_delta_validated'))
              or set(after.get('evidence',[]))-set(before.get('evidence',[]))):
            status,operation='INFORMATION_GAIN','INSPECT'
        else:
            status,operation='NO_PROGRESS','INSPECT' if diagnostic else 'LOCAL_STRATEGY_SWITCH'
        if (status in {'NO_PROGRESS','INFORMATION_GAIN'} and previous_attempts
                and previous_attempts[-1].get('status') in {'NO_PROGRESS','INFORMATION_GAIN','REGRESSION'}):
            operation='AFFECTED_SUBGRAPH_REPLAN'
        return {'status':status,'next_operation':operation,
                'goal_progress':status=='PROGRESS', 'diagnostic_gap_ids':diagnostic,
                'improved_gap_ids':sorted(improved), 'regressed_gap_ids':sorted(worsened),
                'acceptance_frontier_before':sorted(verified_before),
                'acceptance_frontier_after':sorted(verified_after),
                'newly_verified':sorted(verified_after-verified_before),
                'invalidated':sorted(verified_before-verified_after),
                'authority':'Agent advice only; no mutation, rollback, or acceptance grant'}


def repair_progress(previous,current,strategy_fingerprint,previous_attempts=(),*,verified=()):
    """Missing failures are not repaired: require explicit qualified rechecks.

    REPAIR_PROGRESS concerns the supplied checks, never Root Goal improvement.
    The caller must use assess() with outcome evidence for that separate claim.
    """
    before=set(previous);after=set(current);resolved=(before-after)&set(verified);regressed=after-before
    status=('REPAIR_REGRESSION' if regressed else 'REPAIR_PROGRESS' if resolved else
            'REPAIR_INFORMATION_GAIN' if before-after else 'REPAIR_NO_PROGRESS')
    repeated=bool(previous_attempts and status!='REPAIR_PROGRESS' and
        previous_attempts[-1].get('status') in {'REPAIR_NO_PROGRESS','REPAIR_INFORMATION_GAIN','REPAIR_REGRESSION'})
    return {'failed_before':sorted(before),'failed_after':sorted(after),'newly_verified_ids':sorted(resolved),
        'regressions':sorted(regressed),'status':status,'strategy_fingerprint':strategy_fingerprint,
        'next_operation':('CHANGE_STRATEGY_OR_INSPECT_OR_REPLAN' if repeated else
                          'INSPECT' if status=='REPAIR_INFORMATION_GAIN' else 'CONTINUE'),
        'code':'REPEATED_REPAIR_NO_PROGRESS' if repeated else status}
