"""Proof estimates and multiobjective filtering; never acceptance truth."""
from dataclasses import dataclass
from math import inf, isfinite, log, sqrt


@dataclass(frozen=True)
class ProofCost:
    proof: float
    disproof: float


def proof_cost(operator, children, *, verified=False, disproved=False, integration_cost=0):
    if verified and disproved:
        raise ValueError('contradictory proof state')
    if not isfinite(integration_cost) or integration_cost < 0:
        raise ValueError('invalid integration cost')
    if verified:
        return ProofCost(0, inf)
    if disproved:
        return ProofCost(inf, 0)
    children = tuple(children)
    if not children:
        return ProofCost(inf, inf)
    if any(c.proof < 0 or c.disproof < 0 or c.proof != c.proof or c.disproof != c.disproof for c in children):
        raise ValueError('invalid child estimate')
    if operator == 'AND':
        return ProofCost(sum(c.proof for c in children) + integration_cost, min(c.disproof for c in children))
    if operator == 'OR':
        return ProofCost(min(c.proof for c in children), sum(c.disproof for c in children))
    raise ValueError('unknown connective')


@dataclass(frozen=True)
class Candidate:
    id: str
    gain: float
    novelty: float
    cost: float
    regression_risk: float
    side_effect_risk: float
    uncertainty: float
    qualified: bool = True
    samples: int = 0
    reward: float = 0

    def __post_init__(self):
        if not self.id or any(not isfinite(v) or v < 0 for v in
                              (self.gain, self.novelty, self.cost, self.regression_risk, self.side_effect_risk, self.uncertainty)):
            raise ValueError('invalid candidate dimensions')
        if type(self.samples) is not int or self.samples < 0 or not isfinite(self.reward):
            raise ValueError('invalid observations')

    @property
    def minimized(self):
        return (-self.gain, -self.novelty, self.cost, self.regression_risk, self.side_effect_risk, self.uncertainty)


def pareto(candidates):
    candidates = tuple(candidates)
    if len({c.id for c in candidates}) != len(candidates):
        raise ValueError('duplicate candidate')
    return tuple(sorted((c for c in candidates if not any(
        all(a <= b for a, b in zip(d.minimized, c.minimized))
        and any(a < b for a, b in zip(d.minimized, c.minimized)) for d in candidates)), key=lambda c: c.id))


def allocate(candidates, *, budget, blocked=(), max_risk=1, min_samples=3):
    """Hard gates -> Pareto -> bounded probe; optional UCB only after samples.

    Budget is in host-defined resource units. No calls or model selection are
    performed here. Probe estimates are upper bounds supplied by the host.
    """
    if not isfinite(budget) or budget < 0 or type(min_samples) is not int or min_samples < 1:
        raise ValueError('invalid allocation bounds')
    eligible = pareto(c for c in candidates if c.qualified and c.id not in blocked
                      and c.regression_risk <= max_risk and c.side_effect_risk <= max_risk and c.cost <= budget)
    total = sum(c.samples for c in eligible)
    def priority(c):
        if c.samples < min_samples:
            return (0, c.samples, c.cost, c.id)
        ucb = c.reward / c.samples + sqrt(2 * log(max(total, 1)) / c.samples)
        return (1, -ucb, c.cost, c.id)
    result = []
    for c in sorted(eligible, key=priority):
        if c.cost <= budget:
            result.append({'id': c.id, 'units': c.cost, 'mode': 'PROBE' if c.samples < min_samples else 'EXPAND'})
            budget -= c.cost
    return tuple(result)
