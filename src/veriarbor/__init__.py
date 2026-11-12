"""Certified Block boundaries. Hosts retain execution and evidence authority."""
__version__ = "0.1.0a1"

from .block import Block
from .port import Port
from .contract import Contract
from .effects import EffectContract
from .variant import Variant, VariantStatus
from .certificate import Certificate, can_substitute
from .adapter import Adapter
from .compatibility import PortCompatibility, compare_ports, compare_effects, compare_blocks
from .dedup import VerificationKey
from .impact import ImpactPlan, ImpactedNode, plan_impact
from .capability import CapabilityContract, CapabilityGateState, AcceptanceMetric, GoalGap
from .skills import SkillManifest, SkillCandidateGenerator, SkillRegistry, SkillMatcher

__all__ = ['Block', 'Port', 'Contract', 'EffectContract', 'Variant', 'VariantStatus',
           'Certificate', 'Adapter', 'PortCompatibility', 'VerificationKey',
           'ImpactPlan', 'ImpactedNode', 'plan_impact',
           'can_substitute', 'compare_ports', 'compare_effects', 'compare_blocks',
           'CapabilityContract', 'CapabilityGateState', 'AcceptanceMetric', 'GoalGap',
           'SkillManifest', 'SkillCandidateGenerator', 'SkillRegistry', 'SkillMatcher',
           'ExecutionMode', 'NodeExecutionPermit', 'NodeExecutionResult', 'NodeCommitReceipt',
           'NodeRuntimeRecord', 'DecisionRecord', 'CriticalCheckSpec', 'CriticalCheckResult', 'CriticalCheckRegistry']

from .execution_authority import (ExecutionMode, NodeExecutionPermit, NodeExecutionResult,
    NodeCommitReceipt, NodeRuntimeRecord, DecisionRecord, CriticalCheckSpec,
    CriticalCheckResult, CriticalCheckRegistry)
from .execution_authority import CheckerIdentity, StandardEffect
from .governance import (ClaimEvidenceRelation, EvidenceDerivation, InputBinding, EvaluationScope,
    LegacyPolicy, legacy_scope, count_independent, independence_summary, GovernanceError, ErrorCode)
__all__ += ['CheckerIdentity','StandardEffect','ClaimEvidenceRelation','EvidenceDerivation','InputBinding',
            'EvaluationScope','LegacyPolicy','legacy_scope','count_independent','independence_summary',
            'GovernanceError','ErrorCode']
