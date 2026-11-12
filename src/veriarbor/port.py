from dataclasses import dataclass, field
from .contract import Contract
from .model import stable_hash


@dataclass(frozen=True)
class Port:
    port_id: str
    version: str
    direction: str
    contract: Contract
    required: bool = True
    default_json: str = 'null'
    compatibility_policy: str = 'structural-v1'
    evidence_policy: dict = field(default_factory=dict)

    def validate_evidence(self, evidence):
        from .capability import validate_evidence
        return validate_evidence(evidence, consumer=self.port_id, **self.evidence_policy)

    def __post_init__(self):
        from .contract import canonical
        import json
        if not self.port_id or not self.version or self.direction not in {'input', 'output'}:
            raise ValueError('invalid port identity/direction')
        object.__setattr__(self, 'default_json', canonical(json.loads(self.default_json)))

    @property
    def fingerprint(self):
        from dataclasses import asdict
        value = asdict(self)
        # Empty opt-in policy preserves historical certificates and boundary hashes.
        if not self.evidence_policy:
            value.pop('evidence_policy')
        return stable_hash(value)
