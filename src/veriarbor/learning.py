"""Evidence-bound failure constraints and non-chronological recommendations."""
from dataclasses import dataclass
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
    """Compare bounded observations and suggest the existing Agent's next action."""
    @staticmethod
    def assess(before, after):
        verified_before=set(before.get('verified',[]));verified_after=set(after.get('verified',[]))
        failed_before=set(before.get('failed',[]));failed_after=set(after.get('failed',[]))
        if verified_before-verified_after or failed_after-failed_before or after.get('contract_drift'):
            status,operation='REGRESSION','AFFECTED_SUBGRAPH_REPLAN'
        elif (verified_after-verified_before or failed_before-failed_after
              or after.get('artifact_delta_validated')
              or set(after.get('evidence',[]))-set(before.get('evidence',[]))):
            status,operation='PROGRESS','CONTINUE'
        else:
            status,operation='NO_PROGRESS','LOCAL_STRATEGY_SWITCH'
        return {'status':status,'next_operation':operation,
                'acceptance_frontier_before':sorted(verified_before),
                'acceptance_frontier_after':sorted(verified_after),
                'newly_verified':sorted(verified_after-verified_before),
                'invalidated':sorted(verified_before-verified_after),
                'authority':'Agent advice only; no mutation, rollback, or acceptance grant'}


def repair_progress(previous,current,strategy_fingerprint,previous_attempts=()):
    before=set(previous);after=set(current);verified=before-after;regressed=after-before
    status='REPAIR_REGRESSION' if regressed else 'REPAIR_PROGRESS' if verified else 'REPAIR_NO_PROGRESS'
    repeated=bool(previous_attempts and status!='REPAIR_PROGRESS' and
        previous_attempts[-1].get('status')!='REPAIR_PROGRESS' and
        previous_attempts[-1].get('strategy_fingerprint')==strategy_fingerprint)
    return {'failed_before':sorted(before),'failed_after':sorted(after),'newly_verified_ids':sorted(verified),
        'regressions':sorted(regressed),'status':status,'strategy_fingerprint':strategy_fingerprint,
        'next_operation':'CHANGE_STRATEGY_OR_INSPECT_OR_REPLAN' if repeated else 'CONTINUE',
        'code':'REPEATED_REPAIR_NO_PROGRESS' if repeated else status}
