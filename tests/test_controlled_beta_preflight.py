"""Beta creation is fail-closed without changing the raw solver or benchmark."""
import pytest
import load_script
from test_block_bonding import CATALOG, ft, seg

m = load_script.load()


def piece(x=40, y=0, wall=0):
    return {"wall_idx": wall, "logical_code": "B34", "length_cm": 34,
            "width_cm": 14, "course": "A", "course_variant": 0,
            "origin_world": m.XYZ(ft(x), ft(y), 0),
            "x_dir": m.XYZ(1, 0, 0), "y_dir": m.XYZ(0, 1, 0),
            "node_index": 5, "placement_reason": "T_INTERSECTION_DEGRADED_L"}


def fixture(pieces=None, opening=(30, 80, 0, 210)):
    pieces = [piece()] if pieces is None else pieces
    result = {"num_courses": 1, "candidates": pieces, "course_candidates": {0: pieces}}
    walls = [(seg(0, 0, 199, 0), ft(14), (False, False))]
    openings = [[tuple(ft(v) for v in opening)]] if opening else [[]]
    return result, walls, openings


def check(result, walls, openings):
    return m.controlled_beta_preflight(result, walls, openings, CATALOG, 0.0)


def test_real_door_intrusion_blocks_without_mutating_candidates():
    result, walls, openings = fixture()
    before = [(id(c), dict(c)) for c in result["candidates"]]
    gate = check(result, walls, openings)
    assert not gate["ok"]
    record, = gate["opening_violations"]
    assert record["course_index"] == 0
    assert record["opening_index"] == 0
    assert record["overlap_cm"] > 0
    assert [(id(c), dict(c)) for c in result["candidates"]] == before


def test_unused_aggregate_variant_cannot_block_physical_course():
    result, walls, openings = fixture([piece(140)])
    result["candidates"] = result["candidates"] + [piece(40)]
    assert check(result, walls, openings)["ok"]


def test_window_only_blocks_courses_intersecting_its_actual_height():
    result, walls, openings = fixture(opening=(30, 80, 100, 210))
    assert check(result, walls, openings)["ok"]
    result["num_courses"] = 12
    result["course_candidates"] = {ci: result["candidates"] for ci in range(12)}
    gate = check(result, walls, openings)
    assert not gate["ok"]
    assert all(v["z_cm"][1] > 100 and v["z_cm"][0] < 210 for v in gate["opening_violations"])
    assert 0 not in {v["course_index"] for v in gate["opening_violations"]}
    assert 11 not in {v["course_index"] for v in gate["opening_violations"]}


def test_opening_checks_geometry_even_without_owner_or_secondary_link():
    result, walls, openings = fixture([piece(wall=1)])
    walls.append((seg(0, 200, 199, 200), ft(14), (False, False)))
    openings.append([])
    assert not check(result, walls, openings)["ok"]


def test_beta_does_not_exempt_two_colliding_pieces_of_same_node():
    result, walls, openings = fixture([piece(40), piece(45)], opening=None)
    assert m.validate_same_course_collision(result["candidates"]) == []
    gate = check(result, walls, openings)
    assert not gate["ok"]
    assert len(gate["collisions"]) == 1


def test_distinct_physical_courses_do_not_collide_with_each_other():
    result, walls, openings = fixture([piece(40), piece(40)], opening=None)
    result["num_courses"] = 2
    result["course_candidates"] = {0: [result["candidates"][0]], 1: [result["candidates"][1]]}
    assert check(result, walls, openings)["ok"]


@pytest.mark.parametrize("damage", ["missing_course", "missing_openings", "solver_error"])
def test_incomplete_result_fails_closed(damage):
    result, walls, openings = fixture(opening=None)
    if damage == "missing_course":
        result["course_candidates"] = {}
    elif damage == "missing_openings":
        openings = []
    else:
        result["error"] = "rebuild failed"
    assert not check(result, walls, openings)["ok"]


def test_blocked_recalculation_cannot_delete_previous_batch_or_references():
    result, walls, openings = fixture()
    handler = m._PostCreationEventHandler()
    handler.controlled_beta = True
    handler.solve_result = result
    handler.walls_to_create, handler.openings_per_wall, handler.catalog = walls, openings, CATALOG
    previous = {"created_count": 1, "created_instances": [{"id": 99}]}
    handler.create_result = previous

    class UntouchableDocument:
        def __getattr__(self, name):
            pytest.fail("Preflight must run before ANY document access: " + name)

    with pytest.raises(ValueError, match="BETA BLOQUEADO"):
        handler._execute_create(UntouchableDocument())
    assert handler.create_result is previous
    assert not handler.solve_result["beta_preflight"]["ok"]
    with pytest.raises(ValueError, match="BETA BLOQUEADO"):
        handler._execute_delete(UntouchableDocument())


def test_empty_wall_is_explicitly_retained_without_blocking_other_valid_walls():
    result, walls, openings = fixture([], opening=None)
    m._record_unmodulated_walls(result, walls)
    assert result["unmodulated_walls"][0]["action"] == "MANUAL_REVIEW_KEEP_REFERENCE"
    assert check(result, walls, openings)["ok"]


@pytest.mark.parametrize("damage", ["nan", "negative", "axis"])
def test_invalid_piece_geometry_cannot_pass_safety_gate(damage):
    c = piece()
    if damage == "nan":
        c["origin_world"] = m.XYZ(float("nan"), 0, 0)
    elif damage == "negative":
        c["length_cm"] = -34
    else:
        c["y_dir"] = c["x_dir"]
    result, walls, openings = fixture([c], opening=None)
    gate = check(result, walls, openings)
    assert not gate["ok"]
    assert gate["errors"]
