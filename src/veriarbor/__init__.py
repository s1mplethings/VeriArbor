"""Certified Block boundaries. Hosts retain execution and evidence authority."""
__version__ = "0.1.0.dev0"

from .block import Block
from .port import Port
from .contract import Contract
from .effects import EffectContract
from .variant import Variant, VariantStatus
from .certificate import Certificate, can_substitute
from .adapter import Adapter
from .compatibility import PortCompatibility, compare_ports, compare_effects, compare_blocks
from .dedup import VerificationKey

__all__ = ['Block', 'Port', 'Contract', 'EffectContract', 'Variant', 'VariantStatus',
           'Certificate', 'Adapter', 'PortCompatibility', 'VerificationKey',
           'can_substitute', 'compare_ports', 'compare_effects', 'compare_blocks']
