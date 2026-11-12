"""File-based reusable strategies. Registry contains no project acceptance state."""
from dataclasses import asdict, dataclass, field, replace
import json
import os
from pathlib import Path
import re
import tempfile

from .capability import CapabilityGateState
from .model import stable_hash

STATUSES = {'EXPERIMENTAL', 'CANDIDATE', 'VERIFIED', 'NEEDS_REVALIDATION', 'DEPRECATED'}
MAX_SKILL_LOAD = 3


@dataclass(frozen=True)
class SkillMetrics:
    planning_tokens_without_skill: int | None = None
    planning_tokens_with_skill: int | None = None
    execution_tokens: int | None = None
    provider_calls: int | None = None
    wall_clock: float | None = None
    success_rate: float | None = None
    acceptance_rate: float | None = None


@dataclass(frozen=True)
class SkillManifest:
    skill_id: str
    version: str
    task_family: str
    semantic_goal: str
    project_id: str
    scope: str = 'PROJECT'
    status: str = 'CANDIDATE'
    triggers: tuple[str, ...] = ()
    preconditions: dict = field(default_factory=dict)
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    strategy_steps: tuple[dict, ...] = ()
    block_refs: tuple[str, ...] = ()
    port_contract_refs: tuple[str, ...] = ()
    capability_contract_refs: tuple[str, ...] = ()
    acceptance_refs: tuple[str, ...] = ()
    known_failures: tuple[str, ...] = ()
    dependency_versions: dict[str, str] = field(default_factory=dict)
    dependency_contract_hashes: dict[str, str] = field(default_factory=dict)
    historical_metrics: dict = field(default_factory=dict)
    token_metrics: SkillMetrics = field(default_factory=SkillMetrics)
    created_from_evidence: tuple[str, ...] = ()
    created_from_tree_branch: str = ''
    private_assumptions: tuple[str, ...] = ()
    source_capability: str = ''
    source_receipts: tuple[str, ...] = ()
    checker_identities: dict = field(default_factory=dict)
    environment_identity: dict = field(default_factory=dict)
    schema_version: str = '2'

    def __post_init__(self):
        for value in (self.skill_id, self.version):
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', value):
                raise ValueError('invalid skill identity')
        if self.status not in STATUSES or self.scope not in {'PROJECT', 'SHARED'}:
            raise ValueError('invalid skill scope/status')
        if self.scope == 'PROJECT' and not self.project_id:
            raise ValueError('project skill needs project_id')
        if self.scope == 'SHARED' and (self.project_id or self.private_assumptions):
            raise ValueError('shared skill cannot carry private assumptions/project binding')
        for name in ('triggers', 'inputs', 'outputs', 'strategy_steps', 'block_refs',
                     'port_contract_refs', 'capability_contract_refs', 'acceptance_refs',
                     'known_failures', 'created_from_evidence', 'private_assumptions', 'source_receipts'):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        if isinstance(self.token_metrics, dict):
            object.__setattr__(self, 'token_metrics', SkillMetrics(**self.token_metrics))

    def as_dict(self):
        return asdict(self)

    @property
    def strategy_hash(self):
        # Lifecycle/measurements may change without changing the executable strategy.
        value = self.as_dict()
        for key in ('status', 'historical_metrics', 'token_metrics', 'created_from_evidence', 'source_receipts'):
            value.pop(key)
        for key in ('source_capability','checker_identities','environment_identity','schema_version'):
            if not value.get(key) or key=='schema_version':value.pop(key,None)
        return stable_hash(value)


@dataclass(frozen=True)
class SkillValidation:
    """Host-qualified execution/acceptance receipt, not a manifest self-claim."""
    run_id: str
    project_id: str
    context_id: str
    strategy_hash: str
    gates: CapabilityGateState
    evidence_refs: tuple[str, ...]
    qualified: bool = False
    interfaces_compatible: bool = False
    commit_receipt_id: str = ''
    checker_identities: dict = field(default_factory=dict)
    contract_hash: str = ''


def promotion_check(manifest, validations, minimum_success_count=2, *, execution_mode='GOVERNED', receipt_validator=None):
    from .execution_authority import ExecutionMode
    mode = ExecutionMode(execution_mode)
    if mode == ExecutionMode.IMPORTED_UNMANAGED:
        return False
    if mode == ExecutionMode.LEGACY:
        from .governance import require_legacy
        require_legacy(project_id=manifest.project_id)
        import warnings
        warnings.warn('LEGACY Skill promotion has no node receipt lineage',RuntimeWarning)
    else:
        if (not manifest.source_capability or not manifest.source_receipts or not manifest.checker_identities
                or not manifest.dependency_contract_hashes.get(manifest.source_capability)):return False
        if receipt_validator is None:return False
        try:
            validations = tuple(v for v in validations if v.commit_receipt_id in manifest.source_receipts
                and v.checker_identities==manifest.checker_identities
                and v.contract_hash==manifest.dependency_contract_hashes[manifest.source_capability]
                and receipt_validator(v))
        except (ValueError, KeyError):
            return False
    if minimum_success_count < 2:
        raise ValueError('minimum_success_count must be >= 2')
    if (not manifest.semantic_goal.strip() or not manifest.strategy_steps or not manifest.block_refs
            or not manifest.port_contract_refs or not manifest.capability_contract_refs
            or not manifest.acceptance_refs or not manifest.created_from_tree_branch):
        return False
    if (any(not manifest.dependency_versions.get(ref) for ref in manifest.block_refs)
            or any(not manifest.dependency_contract_hashes.get(ref)
                   for ref in (*manifest.port_contract_refs, *manifest.capability_contract_refs))):
        return False
    valid = [v for v in validations if v.qualified and v.evidence_refs and v.interfaces_compatible
             and v.strategy_hash == manifest.strategy_hash
             and v.gates.semantic_status == v.gates.utility_status == 'PASS'
             and v.gates.implemented_status == v.gates.execution_status == 'PASS'
             and (manifest.scope == 'SHARED' or v.project_id == manifest.project_id)]
    if len({(v.project_id, v.run_id) for v in valid}) < minimum_success_count:
        return False
    if len({tuple(sorted(v.evidence_refs)) for v in valid}) < minimum_success_count:
        return False
    if manifest.scope == 'SHARED':
        return (len({v.context_id for v in valid if v.context_id}) >= 2
                and all(v.gates.generalization_status == 'PASS' for v in valid)
                and not manifest.private_assumptions)
    return True


class SkillCandidateGenerator:
    def __init__(self, minimum_success_count=2, *, execution_mode='GOVERNED', receipt_validator=None):
        self.minimum_success_count = minimum_success_count
        self.authority_options=dict(execution_mode=execution_mode,receipt_validator=receipt_validator)

    def generate(self, manifest, validations, destination):
        if not promotion_check(manifest, validations, self.minimum_success_count, **self.authority_options):
            raise ValueError('SKILL_PROMOTION_REJECT')
        candidate = replace(manifest, status='CANDIDATE', created_from_evidence=tuple(sorted(
            {ref for v in validations for ref in v.evidence_refs})))
        # Evidence refs do not embed source-project evidence or acceptance objects.
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)
        _write(destination / 'skill.json', candidate.as_dict())
        _write_text(destination / 'SKILL.md', render_instructions(candidate))
        return candidate


def render_instructions(manifest):
    steps = '\n'.join(f'{i}. {step.get("operation", "execute")} {step.get("node_id", "")}'
                      for i, step in enumerate(manifest.strategy_steps, 1))
    return (f'---\nname: {manifest.skill_id}\ndescription: {json.dumps(manifest.semantic_goal)}\n---\n\n'
            f'# {manifest.skill_id}\n\n{manifest.semantic_goal}\n\n{steps}\n\n'
            'Instantiate in the current project. Recheck capability, ports, effects and budget. '
            'Execute and collect current acceptance evidence; historical success grants no PASS.\n')


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.skill-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _write(path, value):
    _write_text(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))


class SkillRegistry:
    """Single-coordinator file registry. Hosts provide their existing writer lock."""
    def __init__(self, root, *, execution_mode='GOVERNED', receipt_validator=None, lineage_recorder=None, manifest_validator=None):
        self.authority_options=dict(execution_mode=execution_mode,receipt_validator=receipt_validator)
        self.lineage_recorder=lineage_recorder
        self.manifest_validator=manifest_validator
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, skill_id, version):
        for value in (skill_id, version):
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', value):
                raise ValueError('invalid skill identity')
        return self.root / skill_id / version / 'skill.json'

    def register(self, manifest, validations=()):
        if manifest.status == 'VERIFIED' and not promotion_check(manifest, validations, **self.authority_options):
            raise ValueError('SKILL_PROMOTION_REJECT')
        self._authorize(manifest,validations)
        path = self._path(manifest.skill_id, manifest.version)
        if path.exists():
            raise ValueError('skill version already registered')
        _write(path, manifest.as_dict())
        _write_text(path.with_name('SKILL.md'), render_instructions(manifest))
        self._index()

    def _authorize(self,manifest,validations):
        if self.authority_options['execution_mode']=='LEGACY':
            from .governance import require_legacy
            require_legacy(project_id=manifest.project_id)
        elif self.authority_options['execution_mode']=='GOVERNED':
            if (not manifest.source_receipts or not manifest.source_capability or not manifest.checker_identities
                    or not callable(self.lineage_recorder)):
                raise ValueError('COMMIT_RECEIPT_REQUIRED: skill lineage')
            self.lineage_recorder(manifest)
        else:raise ValueError('IMPORTED_UNMANAGED_CANNOT_PROMOTE')

    def import_candidate(self, manifest, origin, *, source_validator):
        """Import changes applicability, never promotes or copies source authority."""
        if manifest.status!='NEEDS_REVALIDATION' or manifest.source_receipts:
            raise ValueError('import must discard execution qualification')
        if not source_validator(origin):raise ValueError('SKILL_ORIGIN_REJECT')
        path=self._path(manifest.skill_id,manifest.version)
        if path.exists():raise ValueError('skill version already registered')
        _write(path,manifest.as_dict())
        _write(path.with_name('origin.json'),origin)
        _write_text(path.with_name('SKILL.md'),render_instructions(manifest))
        self._index()
        return manifest

    def requalify(self, manifest, validations):
        current=self.lookup(manifest.skill_id,manifest.version)
        if current.status not in {'NEEDS_REVALIDATION','CANDIDATE'}:
            raise ValueError('skill is not awaiting qualification')
        if current.strategy_hash!=manifest.strategy_hash:
            raise ValueError('strategy changed; import a new explicit version before trials')
        if not promotion_check(manifest,validations,**self.authority_options):
            raise ValueError('SKILL_PROMOTION_REJECT')
        verified=replace(manifest,status='VERIFIED')
        self._authorize(verified,validations)
        path=self._path(verified.skill_id,verified.version)
        _write(path,verified.as_dict());_write_text(path.with_name('SKILL.md'),render_instructions(verified))
        self._index()
        return verified

    def lookup(self, skill_id, version):
        return SkillManifest(**json.loads(self._path(skill_id, version).read_text(encoding='utf-8')))

    def _index(self):
        rows = []
        for path in sorted(self.root.glob('*/*/skill.json')):
            m = SkillManifest(**json.loads(path.read_text(encoding='utf-8')))
            rows.append({key: m.as_dict()[key] for key in (
                'skill_id', 'version', 'task_family', 'scope', 'project_id', 'status',
                'inputs', 'outputs', 'capability_contract_refs', 'preconditions',
                'dependency_versions', 'dependency_contract_hashes','checker_identities','environment_identity')})
            rows[-1].update(summary=m.semantic_goal[:160],
                            estimated_prompt_tokens=(len(render_instructions(m)) + 3) // 4)
        _write(self.root / 'index.json', rows)

    def index(self):
        path = self.root / 'index.json'
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else []

    def update_status(self, skill_id, version, status, validations=()):
        m = self.lookup(skill_id, version)
        if status not in STATUSES:
            raise ValueError('invalid skill status')
        if status == 'VERIFIED' and not promotion_check(m, validations, **self.authority_options):
            raise ValueError('SKILL_PROMOTION_REJECT')
        m = replace(m, status=status)
        self._authorize(m,validations)
        _write(self._path(skill_id, version), m.as_dict())
        self._index()
        return m

    def invalidate(self, versions, hashes, *, checker_identities=None, environment_identity=None):
        for row in self.index():
            if row['status'] == 'VERIFIED' and not dependencies_match(row, versions, hashes,checker_identities,environment_identity):
                self.update_status(row['skill_id'], row['version'], 'NEEDS_REVALIDATION')


def dependencies_match(row, versions, hashes, checker_identities=None, environment_identity=None):
    return (all(versions.get(k) == v and v for k, v in row['dependency_versions'].items())
            and all(hashes.get(k) == v and v for k, v in row['dependency_contract_hashes'].items())
            and (not row.get('checker_identities') or row['checker_identities']==checker_identities)
            and (not row.get('environment_identity') or row['environment_identity']==environment_identity))


class SkillMatcher:
    def __init__(self, registry, max_skill_load=MAX_SKILL_LOAD):
        if type(max_skill_load) is not int or max_skill_load < 1:
            raise ValueError('max_skill_load must be positive')
        self.registry, self.max_skill_load = registry, max_skill_load

    def load(self, *, project_id, task_family, capability_id, inputs, outputs,
             dependency_versions, dependency_contract_hashes, context=None, checker_identities=None, environment_identity=None):
        matched = []
        # Only short metadata is inspected before selecting Top-K.
        for row in self.registry.index():
            if (row['status'] == 'VERIFIED' and row['task_family'] == task_family
                    and capability_id in row['capability_contract_refs']
                    and tuple(row['inputs']) == tuple(inputs) and tuple(row['outputs']) == tuple(outputs)
                    and (row['scope'] == 'SHARED' or row['project_id'] == project_id)
                    and all((context or {}).get(k) == v for k, v in row['preconditions'].items())):
                if not dependencies_match(row, dependency_versions, dependency_contract_hashes,checker_identities,environment_identity):
                    self.registry.update_status(row['skill_id'], row['version'], 'NEEDS_REVALIDATION')
                    continue
                matched.append(row)
        loaded = []
        for row in sorted(matched, key=lambda r: (r['scope'] != 'PROJECT', r['skill_id'], r['version']))[:self.max_skill_load]:
            m = self.registry.lookup(row['skill_id'], row['version'])
            # Recheck authoritative manifest in case index is stale.
            if (m.status != 'VERIFIED' or m.scope == 'PROJECT' and m.project_id != project_id
                    or not dependencies_match(m.as_dict(), dependency_versions, dependency_contract_hashes,checker_identities,environment_identity)):
                continue
            if not all((context or {}).get(k)==v for k,v in m.preconditions.items()):continue
            if self.registry.manifest_validator is not None:
                self.registry.manifest_validator(m)
            body = render_instructions(m)
            loaded.append((m, body))
        return loaded
