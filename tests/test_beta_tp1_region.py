"""The first beta region is a fresh two-wall solve, never a full-plan crop."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "nuvem"))

from benchmark import solver_bridge
from benchmark.extract.from_solver import project_from_solver
from benchmark.runner import evaluate_project


def test_tp1_75_81_fresh_region_has_no_physical_or_normative_findings():
    directory = ROOT / "nuvem/benchmark/projects/torre_easy_lo_r00_tp1"
    data = json.loads((directory / "input.json").read_text(encoding="utf-8"))
    data["walls"] = [data["walls"][i] for i in (75, 81)]
    assert all(not wall.get("openings") for wall in data["walls"])
    result, walls, nodes, openings, catalog, base, courses, notes = solver_bridge.run_solver(data)
    result["num_courses"] = courses
    assert sorted(node["kind"] for node in nodes) == ["FREE_END", "FREE_END", "L_CORNER"]
    assert sum(len(pieces) for pieces in result["course_candidates"].values()) == 187
    assert not result.get("intersection_failures")
    assert not result.get("non_modular")
    assert not result["unmodulated_walls"]
    assert all(audit["ok"] for audit in result["wall_bond_audits"].values())
    gate = solver_bridge.engine().controlled_beta_preflight(result, walls, openings, catalog, base)
    assert gate["ok"], gate
    project = project_from_solver("tp1_beta_75_81", result, walls, nodes, openings,
                                  catalog, base, courses, metadata={"solver_notes": notes})
    reference = json.loads((directory / "reference.json").read_text(encoding="utf-8"))
    findings, score, _comparison = evaluate_project(project, reference)
    assert not score["validator_errors"]
    assert not findings, findings
