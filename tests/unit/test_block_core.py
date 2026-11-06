import unittest
from dataclasses import replace
from veriarbor.contract import Contract, schema_subset
from veriarbor.port import Port
from veriarbor.block import Block
from veriarbor.variant import Variant
from veriarbor.effects import EffectContract
from veriarbor.compatibility import PortCompatibility as C, compare_ports, compare_blocks, compare_effects
from veriarbor.adapter import Adapter, adapter_lifecycle
from veriarbor.certificate import Certificate, can_substitute
from veriarbor.expansion import progressive_boundary_expansion, next_hop
from veriarbor.dedup import VerificationKey, verification_disposition, provider_disposition


def port(name='value', direction='input', extra=False, required=True):
    props = {name: {'type': 'string'}}
    if extra:
        props['extra'] = {'type': 'string', 'default': ''}
    return Port('p', '1', direction, Contract.create({'type': 'object', 'properties': props,
        'required': [name] if required else [], 'additionalProperties': False}, 'stable meaning'))


def block(digest='old'):
    return Block('b', 'cap', (port(),), (), EffectContract(), (Variant('v', (('api', digest),)),), 'v')


def cert(b):
    return Certificate(b.block_id, b.active_variant, *b.boundary_hashes, ('a',),
                       b.variant.artifacts, (('checker', 'hash'),), (), ('receipt',), '2026-11-04T00:00:00Z')


class BlockCoreTests(unittest.TestCase):
    def test_round_trip_and_immutable_contract(self):
        b = block()
        self.assertEqual(Block.from_dict(b.as_dict()), b)
        schema = b.input_ports[0].contract.schema
        schema['required'] = []
        self.assertEqual(b.input_ports[0].contract.schema['required'], ['value'])

    def test_internal_change_identical_boundary(self):
        self.assertEqual(compare_blocks(block(), block('new')), C.IDENTICAL)
        bubble = progressive_boundary_expansion('b', ['c', 'd'], C.IDENTICAL)
        self.assertEqual(bubble.verification, ('block',))
        self.assertEqual(bubble.direct_neighbors, ())

    def test_optional_input_compatible_required_breaking(self):
        self.assertEqual(compare_ports(port(), port(extra=True)), C.COMPATIBLE)
        p = port(extra=True)
        schema = p.contract.schema
        schema['required'].append('extra')
        required = replace(p, contract=Contract.create(schema, p.contract.semantic))
        self.assertEqual(compare_ports(port(), required), C.BREAKING)

    def test_directional_output(self):
        old = port(direction='output')
        schema = old.contract.schema
        schema['additionalProperties'] = True
        open_old = replace(old, contract=Contract.create(schema, old.contract.semantic))
        self.assertEqual(compare_ports(open_old, port(direction='output', extra=True)), C.COMPATIBLE)
        self.assertEqual(compare_ports(old, port(direction='output', extra=True)), C.BREAKING)
        self.assertEqual(compare_ports(old, port(direction='output', required=False)), C.BREAKING)

    def test_enum_and_range_variance(self):
        a = Port('p', '1', 'input', Contract.create({'type': 'integer', 'minimum': 1, 'maximum': 3}, 'n'))
        b = replace(a, contract=Contract.create({'type': 'integer', 'minimum': 0, 'maximum': 4}, 'n'))
        self.assertEqual(compare_ports(a, b), C.COMPATIBLE)
        self.assertEqual(compare_ports(b, a), C.BREAKING)
        self.assertFalse(schema_subset({'type': 'string'}, {'type': 'string', 'enum': ['a']}))

    def test_unknown_semantics_effects_defaults_fail_closed(self):
        p = port()
        self.assertEqual(compare_ports(p, replace(p, contract=Contract.create(p.contract.schema, 'different'))), C.BREAKING)
        self.assertEqual(compare_effects(EffectContract(), EffectContract(external_effects=('publish',))), C.BREAKING)
        self.assertFalse(schema_subset({'type': 'string', 'pattern': 'x'}, {'type': 'string'}))
        self.assertFalse(schema_subset({'type': 'string', 'default': 'a'}, {'type': 'string', 'default': 'b'}))

    def test_explicit_adapter_and_no_hidden_missing_field(self):
        a = Adapter('rename', port('old'), port('new'), (('old', 'new'),), semantic_mapping=(('old', 'new'),))
        self.assertEqual(compare_ports(a.source, a.target, a), C.ADAPTABLE)
        self.assertEqual(a.transform({'old': 'x'}), {'new': 'x'})
        for value in ({}, {'old': 1}, {'old': 'x', 'secret': 'y'}):
            with self.assertRaises(ValueError):
                a.transform(value)
        with self.assertRaises(ValueError):
            Adapter('guess', port('old'), port('new'), (('old', 'new'),))
        self.assertEqual(adapter_lifecycle(consumer_count=0, usage_count=5), 'ARCHIVE_REMOVE_FROM_PRODUCTION')

    def test_default_adapter(self):
        a = Adapter('default', port(), port(extra=True), defaults_json='{"extra":""}')
        self.assertEqual(a.transform({'value': 'x'}), {'value': 'x', 'extra': ''})
        with self.assertRaises(ValueError):
            Adapter('bad', port(), port(extra=True), defaults_json='{"extra":4}')

    def test_certificate_replacement_requires_current_proof(self):
        old, new = block(), block('new')
        kwargs = dict(checkers={'checker': 'hash'}, evidence_authenticated=True)
        self.assertTrue(can_substitute(cert(old), new, replacement_certificate=cert(new), **kwargs))
        self.assertFalse(can_substitute(cert(old), new, replacement_certificate=cert(old), **kwargs))
        self.assertFalse(cert(new).matches(new, {'checker': 'changed'}, evidence_authenticated=True))
        self.assertFalse(cert(new).matches(new, {'checker': 'hash'}, evidence_authenticated=False))
        self.assertFalse(replace(cert(new), invalidated=True).matches(new, {'checker': 'hash'}, evidence_authenticated=True))

    def test_expansion_one_hop_then_stops(self):
        bubble = progressive_boundary_expansion('b', ['c'], C.BREAKING)
        self.assertEqual(bubble.direct_neighbors, ('c',))
        self.assertEqual(next_hop(bubble, {'c': C.COMPATIBLE}, {'c': ['d'], 'd': ['e']}), ())
        self.assertEqual(next_hop(bubble, {'c': C.BREAKING}, {'c': ['d'], 'd': ['e']}), ('d',))
        with self.assertRaises(ValueError):
            next_hop(bubble, {'e': C.BREAKING}, {})

    def test_verification_key_fail_running_pass_and_artifact_delta(self):
        b = block()
        key = VerificationKey('b', 'v', *b.boundary_hashes, 'a', 'checker', (), b.variant.artifacts)
        rows = [{'key': key.fingerprint, 'status': 'PASS', 'authenticated': True}]
        self.assertEqual(verification_disposition(key, rows), 'REUSE_PASS')
        rows.append({'key': key.fingerprint, 'status': 'FAIL', 'authenticated': True})
        self.assertEqual(verification_disposition(key, rows), 'NO_NOVEL_DELTA')
        rows.append({'key': key.fingerprint, 'status': 'RUNNING', 'authenticated': True})
        self.assertEqual(verification_disposition(key, rows), 'REUSE_RUNNING')
        self.assertEqual(verification_disposition(replace(key, artifact_hashes=(('api', 'new'),)), rows), 'EXECUTE')
        self.assertEqual(verification_disposition(key, [{'key': key.fingerprint, 'status': 'PASS', 'authenticated': False}]), 'EXECUTE')

    def test_provider_delta(self):
        candidate = dict(variant='v', artifacts='a', contracts='c', evidence='e', checker_qualification='q')
        self.assertEqual(provider_disposition([candidate], candidate), 'NO_NOVEL_DELTA')
        self.assertEqual(provider_disposition([candidate], {**candidate, 'evidence': 'new'}), 'EXECUTE')
        self.assertEqual(provider_disposition([], {}), 'NO_NOVEL_DELTA')
