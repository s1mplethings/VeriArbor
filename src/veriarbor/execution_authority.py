"""Node authority vocabulary. Host owns issuance and persistence, not workers.

Effect values reuse the host's declared domains; operation names below map to
those domains rather than introducing a second effect permission taxonomy.
"""
from dataclasses import dataclass, field, fields, asdict
from enum import StrEnum
from datetime import datetime, timezone
from collections.abc import Mapping


class ExecutionMode(StrEnum):
    GOVERNED = 'GOVERNED'
    IMPORTED_UNMANAGED = 'IMPORTED_UNMANAGED'
    LEGACY = 'LEGACY'


class PermitStatus(StrEnum):
    ACTIVE = 'ACTIVE'
    CONSUMED = 'CONSUMED'
    REVOKED = 'REVOKED'
    EXPIRED = 'EXPIRED'


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class FrozenDict(dict):
    def _blocked(self, *a, **kw):
        raise TypeError('immutable authority data')
    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = __ior__ = _blocked
    def __deepcopy__(self, memo):
        return self


def freeze(value):
    if isinstance(value, Mapping):
        return FrozenDict({k: freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(v) for v in value)
    return value


class ImmutableRecord:
    def __post_init__(self):
        for f in fields(self):
            object.__setattr__(self, f.name, freeze(getattr(self, f.name)))
    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class CriticalCheckSpec:
    check_id: str
    semantic_transform: str
    checker_id: str
    required: bool = True
    unknown_policy: str = 'BLOCK'
    description: str = ''
    expected_version: str | None = None
    minimum_version: str | None = None
    policy_hash: str | None = None
    schema_version: str = '1'
    def __post_init__(self):
        if not all((self.check_id, self.semantic_transform, self.checker_id)):
            raise ValueError('critical check identity required')
        if type(self.required) is not bool or self.unknown_policy not in {'BLOCK', 'ALLOW_WITH_WARNING'}:
            raise ValueError('invalid critical check policy')
        import re
        if any(v is not None and not re.fullmatch(r'\d+(\.\d+)*',v) for v in (self.expected_version,self.minimum_version)):
            raise ValueError('checker versions must be numeric dotted versions')


@dataclass(frozen=True)
class DecisionRecord(ImmutableRecord):
    decision_id: str
    semantic_transform: str
    strategy_id: str
    input_refs: tuple = ()
    output_value: object = None
    output_claim: str = ''
    evidence_refs: tuple = ()
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now)
    check_id: str | None = None
    claim_ref: str = ''
    schema_version: str = '1'


@dataclass(frozen=True)
class CriticalCheckResult(ImmutableRecord):
    check_id: str
    checker_id: str
    status: str
    reason: str = ''
    decision_ids: tuple = ()
    evidence_refs: tuple = ()
    checker_identity: dict = field(default_factory=dict)
    claim_relations: tuple = ()
    derivations: tuple = ()
    schema_version: str = '1'


@dataclass(frozen=True)
class NodeExecutionPermit(ImmutableRecord):
    permit_id: str
    run_id: str
    project_id: str
    node_id: str
    capability_id: str
    admission_id: str
    tree_version: int
    contract_hash: str
    input_bindings: dict
    input_hashes: dict
    allowed_effects: tuple
    budget_scope: dict
    executor_identity: str
    execution_epoch: int
    parent_permit_id: str | None = None
    issued_at: str = field(default_factory=utc_now)
    expires_at: str | None = None
    status: str = 'ACTIVE'
    resource_decision_id: str | None = None
    previous_permit_id: str | None = None
    checker_identities: dict = field(default_factory=dict)
    schema_version: str = '2'


@dataclass(frozen=True)
class NodeExecutionResult(ImmutableRecord):
    permit_id: str
    output_hashes: dict
    effects_used: tuple = ()
    decision_records: tuple = ()
    evidence_refs: tuple = ()
    resource_usage: dict = field(default_factory=dict)
    input_hashes: dict = field(default_factory=dict)
    consumed_inputs: tuple = ()
    claim_refs: tuple = ()
    schema_version: str = '2'


@dataclass(frozen=True)
class NodeCommitReceipt(ImmutableRecord):
    receipt_id: str
    permit_id: str
    run_id: str
    project_id: str
    node_id: str
    capability_id: str
    tree_version: int
    contract_hash: str
    input_hashes: dict
    output_hashes: dict
    effects_used: tuple
    critical_check_results: tuple
    evidence_refs: tuple
    gate_snapshot: dict
    execution_epoch: int
    authority_id: str
    issued_at: str = field(default_factory=utc_now)
    checker_identities: dict = field(default_factory=dict)
    claim_relations: tuple = ()
    derivation_summary: dict = field(default_factory=dict)
    input_manifest: tuple = ()
    resource_decision_id: str | None = None
    authority_checkpoint: dict = field(default_factory=dict)
    schema_version: str = '1'

    @property
    def schema_status(self):
        return 'CURRENT' if self.schema_version=='2' else 'LEGACY_RECEIPT_SCHEMA'


@dataclass(frozen=True)
class NodeRuntimeRecord(ImmutableRecord):
    """Materialized event projection; never an independent acceptance store."""
    run_id: str
    project_id: str
    node_id: str
    capability_id: str | None = None
    tree_version: int | None = None
    execution_mode: str = 'GOVERNED'
    admission_id: str | None = None
    permit_id: str | None = None
    permit_status: str | None = None
    state: str = 'ADMITTED'
    inputs: dict = field(default_factory=dict)
    input_hashes: dict = field(default_factory=dict)
    executor: str | None = None
    effects_authorized: tuple = ()
    effects_used: tuple = ()
    budget_authorized: dict = field(default_factory=dict)
    budget_used: dict = field(default_factory=dict)
    decision_records: tuple = ()
    critical_check_results: tuple = ()
    evidence_refs: tuple = ()
    gate_status: dict = field(default_factory=dict)
    violations: tuple = ()
    warnings: tuple = ()
    output_refs: dict = field(default_factory=dict)
    commit_receipt_id: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    output_state: str = 'UNCOMMITTED'
    goal: str = ''
    execution_epoch: int = 0
    governed_execution: bool = True
    checker_identities: dict = field(default_factory=dict)
    claim_relations: tuple = ()
    input_manifest: tuple = ()
    derivation_summary: dict = field(default_factory=dict)
    evaluation_scope_refs: tuple = ()
    resource_decision: dict = field(default_factory=dict)
    repair_lineage: dict = field(default_factory=dict)
    skill_state: dict = field(default_factory=dict)
    authority_integrity_state: str = 'NOT_RECORDED'
    effect_operations: tuple = ()
    schema_version: str = '2'


@dataclass(frozen=True)
class CheckerIdentity(ImmutableRecord):
    checker_id: str
    checker_version: str
    implementation_hash: str
    policy_hash: str
    registry_revision: str = ''
    runtime_identity: str = ''
    schema_version: str = '1'


class CriticalCheckRegistry:
    """Host registers checkers. Contracts and worker results carry IDs only."""
    def __init__(self):
        self._checkers = {}
    def register(self, checker_id, checker, *, version='1', policy=None, role='CRITICAL', registry_revision=''):
        import re
        if not re.fullmatch(r'\d+(\.\d+)*',version) or role not in {'CRITICAL','OUTCOME'}:
            raise ValueError('invalid checker version/role')
        if not checker_id or not callable(checker) or checker_id in self._checkers:
            raise ValueError('invalid or duplicate critical checker')
        self._checkers[checker_id] = dict(callable=checker,version=version,policy=freeze(policy or {}),
                                         role=role,registry_revision=registry_revision)
        self.identity(checker_id)  # Reject opaque/non-replayable callables at registration.

    def identity(self, checker_id):
        import ast,inspect,textwrap,platform,json
        from .model import stable_hash
        row=self._checkers[checker_id];checker=row['callable']
        source=ast.dump(ast.parse(textwrap.dedent(inspect.getsource(checker))),include_attributes=False)
        closure={k:v for k,v in inspect.getclosurevars(checker).nonlocals.items()}
        closure['__defaults__']=checker.__defaults__
        closure['__kwdefaults__']=checker.__kwdefaults__
        dependencies={}
        for name,value in inspect.getclosurevars(checker).globals.items():
            if inspect.isfunction(value):
                dependencies[name]=ast.dump(ast.parse(textwrap.dedent(inspect.getsource(value))),include_attributes=False)
            elif not inspect.ismodule(value) and not inspect.isclass(value):
                json.dumps(value,sort_keys=True,allow_nan=False)
                closure['global:'+name]=value
        # No repr(), memory addresses, or filename-based implementation identity.
        json.dumps(closure,sort_keys=True,allow_nan=False)
        return CheckerIdentity(checker_id,row['version'],stable_hash({'source':source,'dependencies':dependencies}),
            stable_hash({'policy':row['policy'],'closure':closure}),row['registry_revision'],platform.python_implementation()+' '+platform.python_version())

    def identities(self):
        return {key:self.identity(key).as_dict() for key in self._checkers}

    def audit_identities(self, historical):
        return [{'checker_id':key,'status':'MATCH' if key in self._checkers and self.identity(key).as_dict()==identity
                 else 'HISTORICAL_CHECKER_VERSION_MISMATCH','historical':identity,
                 'current':self.identity(key).as_dict() if key in self._checkers else None}
                for key,identity in historical.items()]

    def invoke(self, checker_id, decisions, context, *, role):
        row=self._checkers.get(checker_id)
        if not row or row['role']!=role:raise ValueError('REQUIRED_CHECKER_MISSING')
        return row['callable'](tuple(decisions),freeze({**context,'checker_policy':row['policy']}))
    def evaluate(self, spec, decisions, context):
        selected = tuple(d for d in decisions if d.check_id == spec.check_id
                         and d.semantic_transform == spec.semantic_transform)
        checker = self._checkers.get(spec.checker_id)
        identity=self.identity(spec.checker_id).as_dict() if checker else {}
        relations=();derivations=()
        reason = ''
        if checker is None:
            status, reason = 'UNKNOWN', 'CHECKER_MISSING'
        elif ((spec.expected_version and spec.expected_version!=identity['checker_version'])
              or (spec.minimum_version and tuple(int(n) for n in identity['checker_version'].split('.')) < tuple(int(n) for n in spec.minimum_version.split('.')))
              or (spec.policy_hash and spec.policy_hash!=identity['policy_hash'])):
            status,reason='UNKNOWN','CHECKER_IDENTITY_MISMATCH'
        elif not selected:
            status, reason = 'UNKNOWN', 'DECISION_MISSING'
        else:
            try:
                status = self.invoke(spec.checker_id,selected,context,role='CRITICAL')
                if isinstance(status,dict):
                    from .governance import ClaimEvidenceRelation,EvidenceDerivation
                    relations=tuple(ClaimEvidenceRelation(**{**r,'checker_identity':identity}).as_dict()
                                    for r in status.get('claim_relations',()))
                    derivations=tuple(EvidenceDerivation(**r).as_dict() for r in status.get('derivations',()))
                    status=status.get('status','UNKNOWN')
                if status not in {'PASS', 'FAIL', 'UNKNOWN'}:
                    status, reason = 'UNKNOWN', 'INVALID_CHECKER_RESULT'
            except Exception as exc:
                status, reason = 'UNKNOWN', 'CHECKER_ERROR:' + type(exc).__name__
        return CriticalCheckResult(spec.check_id, spec.checker_id, status, reason,
                                   tuple(d.decision_id for d in selected),
                                   tuple(ref for d in selected for ref in d.evidence_refs),identity,relations,derivations)


EFFECT_OPERATIONS = {
    'PROVIDER_CALL': 'external_network',
    'PERSISTENT_ARTIFACT_WRITE': 'filesystem',
    'PERSISTENT_LIBRARY_WRITE': 'filesystem',
    'KNOWLEDGE_PROMOTION': 'filesystem',
    'PROFILE_PROMOTION': 'filesystem',
    'PRODUCT_EXPORT': 'filesystem',
    'EXTERNAL_SUBPROCESS_EFFECT': 'local_process',
    'EXTERNAL_SUBPROCESS': 'local_process',
    'ACCEPTANCE_WRITE': 'receipt_authority',
    'SKILL_PROMOTION': 'receipt_authority',
}

StandardEffect=StrEnum('StandardEffect',{name:name for name in EFFECT_OPERATIONS})
