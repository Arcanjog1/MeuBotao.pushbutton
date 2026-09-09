"""Offline diagnostic contracts. Requires tools/beta/requirements.txt."""
import unittest

from collision_stage_report import report
from compare_physical_snapshots import compare, collision_volume_delta


def snapshot():
    piece = {"wall_idx": 0, "logical_code": "B34", "origin_world": [0, 0, 0],
             "x_dir": [1, 0, 0], "y_dir": [0, 1, 0], "length_cm": 34, "width_cm": 14}
    return {"head": "a" * 40, "input_sha256": "same", "wall_keys": ["wall0"], "summary": {},
            "candidates": [piece, dict(piece)], "aggregate_collisions": [[0, 1], [0, 1]],
            "physical": {"0": {"collisions": [[0, 1]]}, "1": {"collisions": []}}}


class DiagnosticsTests(unittest.TestCase):
    def test_stage_report_keeps_multiplicity_distinct_from_physical_identity(self):
        a, b = snapshot(), snapshot()
        b["aggregate_collisions"].append([0, 1])
        data = report([a, b])
        self.assertEqual([2, 3], data["changed_pairs"]["aggregate"][0]["counts"])
        self.assertEqual([], data["changed_pairs"]["physical"])
        self.assertEqual(1, compare(a, b, False)["before_unique"])

    def test_different_inputs_rejected(self):
        a, b = snapshot(), snapshot()
        b["input_sha256"] = "other"
        with self.assertRaises(ValueError):
            report([a, b])

    def test_axis_reversal_changes_piece_identity_not_occupied_region(self):
        a, b = snapshot(), snapshot()
        for c in b["candidates"]:
            c["x_dir"], c["y_dir"] = [-1, 0, 0], [0, -1, 0]
        self.assertEqual(1, len(compare(a, b, True)["added"]))
        self.assertEqual(0, collision_volume_delta(a, b)[0]["new_cm2"])

    def test_new_region_cannot_be_approved_by_lower_total_area(self):
        a, b = snapshot(), snapshot()
        for c in b["candidates"]:
            c["origin_world"] = [1, 0, 0]
            c["length_cm"] = 4
        row = collision_volume_delta(a, b)[0]
        self.assertLess(row["after_cm2"], row["before_cm2"])
        self.assertGreater(row["new_cm2"], 0)


if __name__ == "__main__":
    unittest.main()
