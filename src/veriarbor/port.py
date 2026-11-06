from dataclasses import dataclass
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

    def __post_init__(self):
        from .contract import canonical
        import json
        if not self.port_id or not self.version or self.direction not in {'input', 'output'}:
            raise ValueError('invalid port identity/direction')
        object.__setattr__(self, 'default_json', canonical(json.loads(self.default_json)))

    @property
    def fingerprint(self):
        from dataclasses import asdict
        return stable_hash(asdict(self))
