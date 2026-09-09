"""Empty walls must survive finalization with explicit physical identity."""
import load_script
import pytest
from test_block_bonding import CATALOG, ft, seg

m = load_script.load()


def solve(length):
    walls = [(seg(0, 0, length, 0), ft(14), (False, False))]
    walls, junctions = m.extend_wall_ends_to_junctions(walls, 0.0)
    nodes, ends = m.build_wall_graph(walls, junctions)
    return m.solve_building_blocks_all_courses(
        nodes, walls, ends, [[]], CATALOG, 0.0, 2, arm_role_safe_repair=False)


def test_empty_wall_has_geometry_reason_and_manual_disposition():
    result = solve(197.943)
    assert not any(result["course_candidates"].values())
    record, = result["unmodulated_walls"]
    assert record["wall_idx"] == 0
    assert record["reason"] == "NON_MODULAR_SPANS"
    assert record["action"] == "MANUAL_REVIEW_KEEP_REFERENCE"
    assert abs(record["length_cm"] - 197.943) < 1e-9
    assert record["non_modular_spans"]
    report, _ok = m._format_block_solve_report(result, CATALOG)
    assert "retidas para revisao manual: 1" in report
    assert "197.943cm" in report


def test_valid_wall_is_not_marked_empty():
    result = solve(199)
    assert any(result["course_candidates"].values())
    assert result["unmodulated_walls"] == []


def test_partial_non_modular_wall_is_retained_even_when_every_planned_piece_exists():
    walls = [(seg(0, 0, 199, 0), ft(14), (False, False))]
    result = solve(199)
    result["num_courses"] = 2
    result["non_modular"] = [{"wall_idx": 0, "current_length_cm": 12.7, "course": "A"}]
    creation = {"created_instances": [
        {"course_index": ci, "candidate_key": id(c)}
        for ci, pcs in result["course_candidates"].items() for c in pcs]}
    m._record_incomplete_wall_creation(result, creation, walls)
    record, = creation["retained_walls"]
    assert record["reason"] == "NON_MODULAR_SPANS"
    assert record["has_physical_candidates"] is True
    assert creation["skipped_wall_idxs"] == [0]
    report, _ok = m._format_block_solve_report(result, CATALOG)
    assert "parcialmente nao modulaveis, retidas para revisao manual: 1" in report


def test_negative_reservations_are_not_mislabeled_as_plain_off_module():
    walls = [(seg(0, 0, 99.754, 0), ft(14), (False, False))]
    result = {"course_candidates": {0: []}, "non_modular": [
        {"wall_idx": 0, "current_length_cm": -2.586}]}
    m._record_unmodulated_walls(result, walls)
    assert result["unmodulated_walls"][0]["reason"] == "OVERLAPPING_RESERVATIONS"


def test_finalize_retains_empty_wall_even_if_creation_did_not_record_skips():
    import revit_stubs
    retained_id, valid_id = revit_stubs.ElementId(1), revit_stubs.ElementId(2)
    handler = m._PostCreationEventHandler()
    handler.solve_result = solve(197.943)
    handler.create_result = {"skipped_wall_idxs": []}
    handler.created_walls_by_axis = {0: [(retained_id, "cad")], 1: [(valid_id, "cad")]}
    handler.created_wall_ids_all = [retained_id, valid_id]

    class Document:
        deleted = []

        def GetElement(self, element_id):
            return element_id

        def Delete(self, element_id):
            self.deleted.append(element_id)

    doc = Document()
    handler._execute_delete(doc)
    assert retained_id not in doc.deleted
    assert valid_id in doc.deleted
    assert handler.create_result["kept_wall_count_no_blocks"] == 1


@pytest.mark.parametrize("missing_course", [0, 1, None])
def test_reference_is_retained_until_every_physical_course_was_created(missing_course):
    walls = [(seg(0, 0, 199, 0), ft(14), (False, False))]
    result = solve(199)
    result["num_courses"] = 2
    created = [{"course_index": ci, "candidate_key": id(c)}
               for ci, pcs in result["course_candidates"].items() for c in pcs
               if ci != missing_course]
    creation = {"created_instances": created}
    m._record_incomplete_wall_creation(result, creation, walls)
    assert creation["skipped_wall_idxs"] == ([] if missing_course is None else [0])
    if missing_course is not None:
        record, = creation["retained_walls"]
        assert record["reason"] == "INCOMPLETE_CREATION"
        assert record["missing_count"] == len(result["course_candidates"][missing_course])


def test_empty_failed_solve_retains_all_references():
    walls = [(seg(0, 0, 199, 0), ft(14), (False, False))]
    creation = {"created_instances": [], "failures": ["invalid height"]}
    m._record_incomplete_wall_creation({"num_courses": 0}, creation, walls)
    assert creation["skipped_wall_idxs"] == [0]


def test_beta_new_solve_does_not_finalize_using_old_instances():
    import revit_stubs
    handler = m._PostCreationEventHandler()
    handler.controlled_beta = True
    old = solve(199)
    handler.create_result = {"created_instances": [
        {"course_index": ci, "candidate_key": id(c)}
        for ci, pcs in old["course_candidates"].items() for c in pcs]}
    handler.solve_result = solve(199)
    handler.solve_result.update(num_courses=2, beta_preflight={"ok": True})
    handler.walls_to_create = [(seg(0, 0, 199, 0), ft(14), (False, False))]
    wall_id = revit_stubs.ElementId(1)
    handler.created_walls_by_axis = {0: [(wall_id, "cad")]}
    handler.created_wall_ids_all = [wall_id]
    handler.solve_result["beta_input_signature"] = handler._beta_input_signature()

    class Document:
        def GetElement(self, _eid):
            pytest.fail("Old instances cannot authorize finalizing the new solve")

    handler._execute_delete(Document())
    assert handler.create_result["skipped_wall_idxs"] == [0]
    assert handler.create_result["kept_wall_count_no_blocks"] == 1


def test_real_99754_wall_preserves_overlapping_reservation_diagnosis():
    import json
    from pathlib import Path
    from benchmark import solver_bridge as bridge

    source = Path(__file__).resolve().parents[1] / "nuvem/benchmark/projects/torre_easy_lo_r00_tgd/input.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    nodes, walls, ends, openings = bridge.plan_from_input(data)
    engine = bridge.engine()
    catalog, _cells, _dropped = bridge.catalog_from_input(data)
    # Select by exact source geometry, not a mutable W label or list position.
    wi, = [i for i, wall in enumerate(data["walls"])
           if wall["start_cm"] == [1813.625, -244.618] and wall["end_cm"] == [1807.181, -145.072]]
    junctions = engine._wall_junction_nodes_and_ts_ft(walls, nodes, wi)
    assert sorted(n["kind"] for n, _t in junctions) == ["AMBIGUOUS", "X_INTERSECTION", "X_INTERSECTION"]
    ties = engine.solve_all_intersections(nodes, walls, catalog, openings, ends)["candidates"]
    by_end = engine._index_node_candidates_by_wall_end(nodes, ties, walls, ends)
    midspan = engine._index_node_candidates_midspan(nodes, ties, walls, ends)
    result = engine.solve_wall_free_fill(wi, walls, nodes, ends, openings, by_end, midspan, catalog)
    assert not result["candidates"]
    assert any(s["current_length_cm"] == pytest.approx(-2.5864347014) for s in result["non_modular"])
    result["course_candidates"] = {0: [], 1: []}
    engine._record_unmodulated_walls(result, walls)
    record, = [w for w in result["unmodulated_walls"] if w["wall_idx"] == wi]
    assert record["reason"] == "OVERLAPPING_RESERVATIONS"
    assert record["length_cm"] == pytest.approx(99.7543545516)
