import unittest
from itertools import combinations
from veriarbor.contract import schema_subset


class ContractProperties(unittest.TestCase):
    def test_enum_inclusion_exhaustive(self):
        subsets = [list(s) for n in range(1, 4) for s in combinations(['a', 'b', 'c'], n)]
        for left in subsets:
            for right in subsets:
                self.assertEqual(schema_subset({'type': 'string', 'enum': left},
                                               {'type': 'string', 'enum': right}), set(left) <= set(right))

    def test_range_transitivity(self):
        ranges = [{'type': 'integer', 'minimum': lo, 'maximum': hi}
                  for lo in range(3) for hi in range(lo, 4)]
        for a in ranges:
            for b in ranges:
                for c in ranges:
                    if schema_subset(a, b) and schema_subset(b, c):
                        self.assertTrue(schema_subset(a, c))
