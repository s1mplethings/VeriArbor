import unittest

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


def block(artifact="old", *, output=None, effect=None):
    output = output or out_port()
    stable = out_port(("id",), port_id="stable")
    return Block("b", "cap", (), (output, stable), effect or EffectContract(),
                 (Variant("v", (("api", artifact),)),), "v")


def key(node, value, *, acceptance="a", checker="checker", neighbors=()):
    return VerificationKey(node, value.active_variant, *value.boundary_hashes,
                           acceptance, checker, neighbors, value.variant.artifacts)


def rows(value, status="PASS", authenticated=True):
    return [{"key": value.fingerprint, "status": status, "authenticated": authenticated}]


class ImpactPlanTests(unittest.TestCase):
    def test_internal_change_stops_at_changed_block(self):
        old, new = block("old"), block("new")
        old_consumer = key("c1", old)
        plan = plan_impact(
            "b", old, new,
            consumers={"c1": ("out",), "c2": ("stable",)},
            old_keys={"c1": old_consumer, "c2": key("c2", old)},
            new_keys={"b": key("b", new)},
            observations={"c1": rows(old_consumer), "c2": rows(key("c2", old))},
        )
        self.assertEqual(plan.block_relation, "IDENTICAL")
        self.assertEqual([node.node_id for node in plan.impacted], ["b"])
        self.assertEqual(plan.unaffected, ("c1", "c2"))
        self.assertEqual(dict(plan.reuse)["c1"], "REUSE_PASS")
        self.assertEqual(plan.retest(), ("b",))

    def test_compatible_output_retests_direct_consumer_only(self):
        old = block("old", output=out_port(open_=True))
        new = block("new", output=out_port(("value", "extra"),
                                           required=("value",), open_=False))
        plan = plan_impact(
            "b", old, new,
            consumers={"c1": ("out",), "c2": ("stable",)},
            old_keys={"c2": key("c2", old)},
            observations={"c2": rows(key("c2", old))},
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
        base = dict(changed="b", old_block=old, new_block=new,
                    consumers={"c1": ("out",)}, old_keys={"c1": consumer})
        self.assertEqual(
            dict(plan_impact(**base, observations={"c1": rows(consumer)}).reuse)["c1"],
            "REUSE_PASS")
        self.assertEqual(
            dict(plan_impact(**base, observations={"c1": rows(consumer, authenticated=False)}).reuse)["c1"],
            "EXECUTE")
        self.assertEqual(
            dict(plan_impact(**base, observations={"c1": rows(consumer, status="FAIL")}).reuse)["c1"],
            "NO_NOVEL_DELTA")
        changed_key = key("b", new)
        plan = plan_impact(
            **base,
            new_keys={"b": changed_key},
            observations={"c1": rows(consumer), "b": rows(changed_key)},
        )
        self.assertEqual(plan.impacted[0].reuse, "REUSE_PASS")

    def test_affected_consumer_stale_key_is_not_reused(self):
        old = block("old", output=out_port(open_=True))
        new = block("new", output=out_port(("value", "extra"),
                                           required=("value",), open_=False))
        consumer = key("c1", old)
        plan = plan_impact(
            "b", old, new,
            consumers={"c1": ("out",)},
            old_keys={"c1": consumer}, new_keys={"c1": consumer},
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
            observations={"b": rows(current)},
        )
        self.assertEqual(plan.block_relation, "IDENTICAL")
        self.assertEqual(plan.impacted[0].reuse, "REUSE_PASS")

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
        self.assertEqual(dict(plan.reuse)["c1"], "UNVERIFIED")
        self.assertEqual(plan.impacted[0].reuse, "EXECUTE")

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
