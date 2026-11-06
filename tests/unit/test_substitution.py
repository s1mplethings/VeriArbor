import unittest
from dataclasses import replace
from unit.test_block_core import block, cert
from veriarbor.substitution import CertifiedReplacement, substitution_cover


class SubstitutionTests(unittest.TestCase):
    def test_certified_dependency_delta_stops_at_boundary(self):
        old, new = block(), block('new')
        proof = CertifiedReplacement(cert(old), new, cert(new), True)
        kwargs = dict(dependency_artifacts=['api'], replacements=[proof], checkers={'checker': 'hash'})
        cover = substitution_cover({'consumer': 'same', 'api': 'old'}, {'consumer': 'same', 'api': 'new'}, **kwargs)
        self.assertEqual(set(cover), {'api'})
        self.assertIsNone(substitution_cover({'consumer': 'same', 'api': 'old'}, {'consumer': 'changed', 'api': 'new'}, **kwargs))
        self.assertIsNone(substitution_cover({'api': 'old'}, {'api': 'unknown'}, **kwargs))
        kwargs['replacements'] = [replace(proof, evidence_authenticated=False)]
        self.assertIsNone(substitution_cover({'api': 'old'}, {'api': 'new'}, **kwargs))

    def test_effect_delta_never_carries(self):
        from veriarbor.effects import EffectContract
        old, new = block(), replace(block('new'), effect_contract=EffectContract(writes=('external',)))
        proof = CertifiedReplacement(cert(old), new, cert(new), True)
        self.assertIsNone(substitution_cover({'api': 'old'}, {'api': 'new'}, dependency_artifacts=['api'],
                          replacements=[proof], checkers={'checker': 'hash'}))
