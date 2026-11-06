import unittest
from dataclasses import replace

from veriarbor.adapter import Adapter
from veriarbor.block import Block
from veriarbor.contract import Contract
from veriarbor.dedup import VerificationKey
from veriarbor.effects import EffectContract
from veriarbor.impact import plan_impact
from veriarbor.port import Port
from veriarbor.variant import Variant


def contract(fields, *, required=None, open_=False, semantic="stable meaning"):
    return Contract.create({
        "type": "object",
        "properties": {field: {"type": "string"} for field in fields},
        "required": list(fields) if required is None else list(required),
        "additionalProperties": open_,
    }, semantic)


def out_port(fields=("value",), *, required=None, open_=False,
             semantic="stable meaning", port_id="out"):
    return Port(port_id, "1", "output",
                contract(fields, required=required, open_=open_, semantic=semantic))


def in_port(fields=("value",), *, required=None, open_=False,
            semantic="stable meaning", port_id="in"):
    return Port(port_id, "1", "input",
                contract(fields, required=required, open_=open_, semantic=semantic))


def block(artifact="old", *, output=None, inputs=(), effect=None):
    output = output or out_port()
    stable = out_port(("id",), port_id="stable")
    return Block("b", "cap", tuple(inputs), (output, stable), effect or EffectContract(),
                 (Variant("v", (("api", artifact),)),), "v")


def key(node, value, *, acceptance="a", checker="checker", neighbors=()):
    return VerificationKey(node, value.active_variant, *value.boundary_hashes,
                           acceptance, checker, neighbors, value.variant.artifacts)


def rows(value, status="PASS", authenticated=True):
    return [{"key": value.fingerprint, "status": status, "authenticated": authenticated}]


def safe_gate(new, *, authenticated=None, observations=None):
    changed = key("b", new)
    return {
        "new_keys": {"b": changed},
        "authenticated_keys": {"b": changed.fingerprint, **(authenticated or {})},
        "observations": {"b": rows(changed), **(observations or {})},
        "external_context_unchanged": True,
    }


class ImpactPlanTests(unittest.TestCase):
    def test_internal_change_without_proof_blocks_consumer_reuse(self):
        old, new = block("old"), block("new")
        old_consumer = key("c1", old)
        other_consumer = key("c2", old)
        plan = plan_impact(
            "b", old, new,
            consumers={"c1": ("out",), "c2": ("stable",)},
            old_keys={"c1": old_consumer, "c2": other_consumer},
            authenticated_keys={"c1": old_consumer.fingerprint,
                                "c2": other_consumer.fingerprint},
            observations={"c1": rows(old_consumer), "c2": rows(other_consumer)},
        )
        self.assertEqual(plan.block_relation, "IDENTICAL")
        self.assertEqual([node.node_id for node in plan.impacted], ["b"])
        self.assertEqual(plan.unaffected, ("c1", "c2"))
        self.assertEqual(dict(plan.reuse)["c1"], "EXECUTE")
        self.assertEqual(dict(plan.reuse)["c2"], "EXECUTE")
        self.assertEqual(plan.retest(), ("b", "c1", "c2"))
        self.assertFalse(plan.consumer_reuse_allowed)
        self.assertEqual(plan.reuse_gate, "BLOCKED_UNPROVEN_UPSTREAM")

    def test_internal_change_with_proof_reuses_consumers(self):
        old, new = block("old"), block("new")
        old_consumer = key("c1", old)
        other_consumer = key("c2", old)
        plan = plan_impact(
            "b", old, new,
            consumers={"c1": ("out",), "c2": ("stable",)},
            old_keys={"c1": old_consumer, "c2": other_consumer},
            **safe_gate(new, authenticated={
                "c1": old_consumer.fingerprint,
                "c2": other_consumer.fingerprint,
            }, observations={
                "c1": rows(old_consumer),
                "c2": rows(other_consumer),
            }),
        )
        self.assertEqual(dict(plan.reuse)["c1"], "REUSE_PASS")
        self.assertEqual(dict(plan.reuse)["c2"], "REUSE_PASS")
        self.assertEqual(plan.retest(), ())
        self.assertTrue(plan.consumer_reuse_allowed)

    def test_compatible_output_retests_direct_consumer_only(self):
        old = block("old", output=out_port(open_=True))
        new = block("new", output=out_port(("value", "extra"),
                                           required=("value",), open_=False))
        consumer = key("c2", old)
        plan = plan_impact(
            "b", old, new,
            consumers={"c1": ("out",), "c2": ("stable",)},
            old_keys={"c2": consumer},
            **safe_gate(new, authenticated={"c2": consumer.fingerprint},
                        observations={"c2": rows(consumer)}),
        )
        self.assertEqual(plan.block_relation, "COMPATIBLE")
        by_id = {node.node_id: node for node in plan.impacted}
        self.assertEqual(by_id["c1"].relation, "COMPATIBLE")
        self.assertEqual(by_id["c1"].checks, ("block", "edge"))
        self.assertEqual(by_id["c1"].reuse, "EXECUTE")
        self.assertNotIn("c2", by_id)
        self.assertEqual(dict(plan.reuse)["c2"], "REUSE_PASS")
        self.assertEqual(plan.required_adapters, ())

    def test_adapter_scope_is_explicit(self):
        old = block("old", output=out_port(("value",)))
        new = block("new", output=out_port(("value2",)))
        adapter = Adapter("rename", old.output_ports[0], new.output_ports[0],
                          (("value", "value2"),), semantic_mapping=(("value", "value2"),))
        plan = plan_impact(
            "b", old, new,
            consumers={"c1": ("out",)},
            adapters={"c1": (adapter,)},
        )
        node = next(item for item in plan.impacted if item.node_id == "c1")
        self.assertEqual(node.relation, "ADAPTABLE")
        self.assertEqual(node.adapter_ids, ("rename",))
        self.assertEqual(plan.required_adapters, ("rename",))
        self.assertIn("adapter", node.checks)
        self.assertEqual(plan.expanded, ())

    def test_breaking_boundary_expands_exactly_one_hop(self):
        old = block("old", output=out_port(("value",)))
        new = block("new", output=out_port(("value2",)))
        plan = plan_impact(
            "b", old, new,
            consumers={"c1": ("out",)},
            adjacency={"c1": ("c2", "c3"), "c2": ("c4",)},
        )
        ids = {node.node_id for node in plan.impacted}
        self.assertEqual(ids, {"b", "c1", "c2", "c3"})
        self.assertNotIn("c4", ids)
        self.assertEqual(plan.breaking, ("c1",))
        self.assertEqual(plan.expanded, ("c2", "c3"))
        for node in plan.impacted:
            if node.node_id in {"c1", "c2", "c3"}:
                self.assertEqual(node.relation, "BREAKING")
                self.assertIn("local_composition", node.checks)

    def test_evidence_reuse_requires_authenticated_exact_key(self):
        old, new = block("old"), block("new")
        consumer = key("c1", old)
        changed_key = key("b", new)
        base = dict(
            changed="b", old_block=old, new_block=new,
            consumers={"c1": ("out",)}, old_keys={"c1": consumer},
            new_keys={"b": changed_key},
            authenticated_keys={"b": changed_key.fingerprint,
                                "c1": consumer.fingerprint},
            external_context_unchanged=True,
        )
        self.assertEqual(
            dict(plan_impact(**base, observations={
                "b": rows(changed_key), "c1": rows(consumer),
            }).reuse)["c1"],
            "REUSE_PASS")
        self.assertEqual(
            dict(plan_impact(**base, observations={
                "b": rows(changed_key), "c1": rows(consumer, authenticated=False),
            }).reuse)["c1"],
            "EXECUTE")
        self.assertEqual(
            dict(plan_impact(**base, observations={
                "b": rows(changed_key), "c1": rows(consumer, status="FAIL"),
            }).reuse)["c1"],
            "NO_NOVEL_DELTA")
        self.assertEqual(plan_impact(**base, observations={
            "b": rows(changed_key), "c1": rows(consumer),
        }).impacted[0].reuse, "REUSE_PASS")

    def test_affected_consumer_stale_key_is_not_reused(self):
        old = block("old", output=out_port(open_=True))
        new = block("new", output=out_port(("value", "extra"),
                                           required=("value",), open_=False))
        consumer = key("c1", old)
        plan = plan_impact(
            "b", old, new,
            consumers={"c1": ("out",)},
            old_keys={"c1": consumer}, new_keys={"c1": consumer},
            authenticated_keys={"c1": consumer.fingerprint},
            observations={"c1": rows(consumer)},
        )
        self.assertEqual(dict(plan.reuse)["c1"], "EXECUTE")

    def test_unchanged_block_can_reuse_current_key(self):
        old = block("old")
        same = block("old")
        current = key("b", old)
        plan = plan_impact(
            "b", old, same,
            new_keys={"b": current},
            authenticated_keys={"b": current.fingerprint},
            observations={"b": rows(current)},
        )
        self.assertEqual(plan.block_relation, "IDENTICAL")
        self.assertEqual(plan.impacted[0].reuse, "REUSE_PASS")

    def test_mixed_adapter_and_breaking_ports_keep_residual_obligation(self):
        old = Block("b", "cap", (), (out_port(("value",)),
                                     out_port(("other",), port_id="other")),
                    EffectContract(), (Variant("v", (("api", "old"),)),), "v")
        new = Block("b", "cap", (), (out_port(("value2",)),
                                     out_port(("other2",), port_id="other")),
                    EffectContract(), (Variant("v", (("api", "new"),)),), "v")
        adapter = Adapter("rename", old.output_ports[0], new.output_ports[0],
                          (("value", "value2"),), semantic_mapping=(("value", "value2"),))
        plan = plan_impact(
            "b", old, new,
            consumers={"c1": ("out", "other")},
            adapters={"c1": (adapter,)},
        )
        node = next(item for item in plan.impacted if item.node_id == "c1")
        self.assertEqual(node.relation, "BREAKING")
        self.assertEqual(node.adapter_ids, ("rename",))
        self.assertEqual(node.unresolved_ports, ("other",))
        self.assertEqual(plan.unresolved, ("c1:other",))
        self.assertEqual(plan.required_adapters, ("rename",))

    def test_input_producer_incompatible_is_affected(self):
        old = block("old", inputs=(in_port(("value",)),))
        new = block("new", inputs=(in_port(("value", "extra"),
                                             required=("value", "extra")),))
        producer = out_port(("value",), port_id="in")
        plan = plan_impact(
            "b", old, new,
            input_producers={"in": "p1"},
            producer_ports={"p1": {"in": producer}},
        )
        node = next(item for item in plan.impacted if item.node_id == "p1")
        self.assertEqual(node.relation, "BREAKING")
        self.assertEqual(node.unresolved_ports, ("in",))
        self.assertEqual(plan.unresolved, ("p1:in",))
        self.assertEqual(plan.unmapped_inputs, ())

    def test_compatible_input_producer_is_reused_not_retested(self):
        old = block("old", inputs=(in_port(("value",)),))
        new = block("new", inputs=(in_port(("value", "extra"),
                                             required=("value",)),))
        producer = out_port(("value",), port_id="in")
        producer_key = key("p1", old)
        plan = plan_impact(
            "b", old, new,
            input_producers={"in": "p1"},
            producer_ports={"p1": {"in": producer}},
            old_keys={"p1": producer_key},
            **safe_gate(new, authenticated={"p1": producer_key.fingerprint},
                        observations={"p1": rows(producer_key)}),
        )
        self.assertEqual(plan.unaffected, ("p1",))
        self.assertEqual(dict(plan.reuse)["p1"], "REUSE_PASS")
        self.assertNotIn("p1", {item.node_id for item in plan.impacted})

    def test_unmapped_input_is_reported(self):
        old = block("old", inputs=(in_port(("value",)),))
        new = block("new", inputs=(in_port(("value", "extra"),
                                             required=("value", "extra")),))
        plan = plan_impact("b", old, new)
        self.assertEqual(plan.unmapped_inputs, ("in",))

    def test_observation_alone_is_not_key_authentication(self):
        old, new = block("old"), block("new")
        consumer = key("c1", old)
        gate = safe_gate(new)
        gate["observations"] = {**gate["observations"], "c1": rows(consumer)}
        plan = plan_impact(
            "b", old, new,
            consumers={"c1": ("stable",)},
            old_keys={"c1": consumer},
            **gate,
        )
        self.assertEqual(dict(plan.reuse)["c1"], "UNVERIFIED")

    def test_missing_output_port_is_breaking(self):
        old, new = block("old"), block("new")
        plan = plan_impact("b", old, new, consumers={"c1": ("missing",)})
        node = next(item for item in plan.impacted if item.node_id == "c1")
        self.assertEqual(node.relation, "BREAKING")
        self.assertEqual(plan.breaking, ("c1",))
        self.assertEqual(plan.required_adapters, ())

    def test_missing_key_never_implies_reuse(self):
        old, new = block("old"), block("new")
        plan = plan_impact("b", old, new, consumers={"c1": ("stable",)})
        self.assertEqual(dict(plan.reuse)["c1"], "EXECUTE")
        self.assertEqual(plan.impacted[0].reuse, "EXECUTE")
        self.assertIn("c1", plan.retest())

    def test_effect_change_keeps_consumers_in_scope(self):
        old = block("old")
        new = replace(block("new"), effect_contract=EffectContract(
            external_effects=("publish",)))
        plan = plan_impact("b", old, new, consumers={"c1": ("out",)})
        self.assertEqual(plan.block_relation, "BREAKING")
        node = next(item for item in plan.impacted if item.node_id == "c1")
        self.assertEqual(node.relation, "BREAKING")
        self.assertIn("c1", plan.retest())

    def test_unmapped_consumer_blocks_reuse(self):
        old, new = block("old"), block("new")
        consumer = key("c1", old)
        plan = plan_impact(
            "b", old, new,
            consumers={"c1": ("stable",)},
            old_keys={"c1": consumer},
            unmapped_consumers=("c1",),
            **safe_gate(new, authenticated={"c1": consumer.fingerprint},
                        observations={"c1": rows(consumer)}),
        )
        self.assertEqual(plan.unmapped_consumers, ("c1",))
        self.assertEqual(plan.reuse_gate, "BLOCKED_UNMAPPED_CONSUMERS")
        self.assertEqual(dict(plan.reuse)["c1"], "EXECUTE")
        self.assertIn("c1", plan.retest())

    def test_external_context_must_be_proven(self):
        old, new = block("old"), block("new")
        consumer = key("c1", old)
        changed = key("b", new)
        base = dict(
            changed="b", old_block=old, new_block=new,
            consumers={"c1": ("stable",)},
            old_keys={"c1": consumer},
            new_keys={"b": changed},
            authenticated_keys={"b": changed.fingerprint,
                                "c1": consumer.fingerprint},
            observations={"b": rows(changed), "c1": rows(consumer)},
        )
        self.assertEqual(dict(plan_impact(**base).reuse)["c1"], "EXECUTE")
        self.assertEqual(
            dict(plan_impact(**base, external_context_unchanged=True).reuse)["c1"],
            "REUSE_PASS")

    def test_identity_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            plan_impact("other", block("old"), block("new"))

    def test_plan_serializes(self):
        old, new = block("old"), block("new")
        plan = plan_impact("b", old, new)
        payload = plan.as_dict()
        self.assertEqual(payload["changed"], "b")
        self.assertEqual(payload["impacted"][0]["node_id"], "b")
        self.assertEqual(payload["reuse"], (("b", "EXECUTE"),))


if __name__ == "__main__":
    unittest.main()
