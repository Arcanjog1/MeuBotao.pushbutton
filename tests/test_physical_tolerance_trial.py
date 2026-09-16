# -*- coding: utf-8 -*-
"""Tolerancias fisicas com TENTATIVA por parede (regra 30.8 e ruido de jamba,
2026-09-15) e fusao de compensadores iguais encostados (regra #2, complemento).

Defeitos medidos (TGD V1, benchmark oficial) com a 30.8 ligada sem tentativa:
- parede com vao dentro do trecho entre nos: a absorcao deslocava as pecas e o
  recorte da porta deixava a sobra fora do modulo (B19 perdido em 5 fiadas);
- parede curta com a mesma peca de no nas duas fiadas: as duas familias
  enchiam contra a MESMA face do no (16 juntas continuas).
Com a tolerancia de jamba ligada sem tentativa: duas paredes do TGD perdiam
221 e 75 cm assentados. As fixtures abaixo sao sinteticas (sem ElementId).

    python3 -m pytest tests/test_physical_tolerance_trial.py -q
"""
import contextlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import solver_bench as sb  # noqa: E402

m = sb.m
from core.engine import continuous_modulation as cm  # noqa: E402
from core.engine import wall_stepper as ws  # noqa: E402


@contextlib.contextmanager
def switches(residual, jamb):
    before = (ws.RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED, cm.JAMB_SEGMENT_NOISE_TOLERANCE_ENABLED)
    ws.RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED = residual
    cm.JAMB_SEGMENT_NOISE_TOLERANCE_ENABLED = jamb
    try:
        yield
    finally:
        ws.RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED, cm.JAMB_SEGMENT_NOISE_TOLERANCE_ENABLED = before


def _fill(placed_cm, non_modular_cm=0.0, conflicts=0, absorptions=0):
    return {
        "candidates": [{"length_cm": placed_cm}] if placed_cm else [],
        "non_modular": [{"current_length_cm": non_modular_cm}] if non_modular_cm else [],
        "alignment_conflicts": [{}] * conflicts,
        "residual_absorptions": [{"residual_cm": 1.0}] * absorptions,
    }


class _Residual(object):
    """solve_fn falso: devolve `with_` quando a absorcao esta ativa."""

    def __init__(self, with_, without):
        self.with_, self.without, self.calls = with_, without, 0

    def __call__(self):
        self.calls += 1
        return dict(self.without if ws._RESIDUAL_ABSORPTION_SUPPRESSED[0] else self.with_)


def test_off_by_default_solves_once():
    fn = _Residual(_fill(100, absorptions=1), _fill(0, 64))
    with switches(False, False):
        out = ws.physical_tolerance_trial(fn)
    assert fn.calls == 1 and "physical_tolerance_trial" not in out


def test_residual_kept_when_it_lays_more_wall_without_new_conflict():
    fn = _Residual(_fill(122, absorptions=2), _fill(0, 130))
    with switches(True, False):
        out = ws.physical_tolerance_trial(fn)
    assert out["candidates"][0]["length_cm"] == 122
    assert out["physical_tolerance_trial"][0]["accepted"] is True


def test_residual_rejected_when_it_loses_laid_wall():
    """Padrao W131: com a absorcao a porta derruba o B19 da sobra."""
    fn = _Residual(_fill(31, 120, absorptions=5), _fill(50, 1))
    with switches(True, False):
        out = ws.physical_tolerance_trial(fn)
    assert out["candidates"][0]["length_cm"] == 50
    assert out["physical_tolerance_trial"][0]["accepted"] is False


def test_residual_rejected_when_it_creates_joint_coincidence():
    """Padrao W151: enche a parede mas as duas familias param na mesma face."""
    fn = _Residual(_fill(148, 0, conflicts=1, absorptions=4), _fill(0, 149))
    with switches(True, False):
        out = ws.physical_tolerance_trial(fn)
    assert not out["candidates"]
    assert out["physical_tolerance_trial"][0]["alignment_conflicts_with"] == 1


def test_residual_equal_laid_length_needs_less_non_modular():
    fn = _Residual(_fill(80, 0, absorptions=1), _fill(80, 3))
    with switches(True, False):
        assert ws.physical_tolerance_trial(fn)["physical_tolerance_trial"][0]["accepted"] is True
    fn = _Residual(_fill(80, 3, absorptions=1), _fill(80, 3))
    with switches(True, False):
        assert ws.physical_tolerance_trial(fn)["physical_tolerance_trial"][0]["accepted"] is False


class _Jamb(object):
    def __init__(self, with_, without, uses=True):
        self.with_, self.without, self.uses, self.calls = with_, without, uses, 0

    def __call__(self):
        self.calls += 1
        if cm.JAMB_SEGMENT_NOISE_SUPPRESSED[0]:
            return dict(self.without)
        if self.uses:
            cm.JAMB_SEGMENT_NOISE_USES[0] += 1
        return dict(self.with_)


def test_jamb_tolerance_only_tried_when_it_decided_a_segment():
    fn = _Jamb(_fill(40), _fill(10), uses=False)
    with switches(False, True):
        out = ws.physical_tolerance_trial(fn)
    assert fn.calls == 1 and "physical_tolerance_trial" not in out


def test_jamb_tolerance_rejected_when_wall_loses_laid_length():
    fn = _Jamb(_fill(232), _fill(453))
    with switches(False, True):
        out = ws.physical_tolerance_trial(fn)
    assert out["candidates"][0]["length_cm"] == 453
    assert out["physical_tolerance_trial"][0]["tolerance"] == "JAMB_SEGMENT_NOISE"


def test_switches_are_restored_even_if_solver_raises():
    def boom():
        if ws._RESIDUAL_ABSORPTION_SUPPRESSED[0]:
            raise RuntimeError("x")
        return _fill(10, absorptions=1)
    with switches(True, True):
        try:
            ws.physical_tolerance_trial(boom)
        except RuntimeError:
            pass
    assert ws._RESIDUAL_ABSORPTION_SUPPRESSED[0] is False and cm.JAMB_SEGMENT_NOISE_SUPPRESSED[0] is False


def test_region_segment_counts_noise_use_only_when_tolerance_decides():
    region = {"lo": 0.0, "hi": 3.99 + 1.0, "left_anchor_is_block": True, "right_anchor_is_block": False,
              "opening_indexes": []}
    with switches(False, True):
        before = cm.JAMB_SEGMENT_NOISE_USES[0]
        plan = cm.region_solid_subsegments(region, [])
        assert plan["segments"] and cm.JAMB_SEGMENT_NOISE_USES[0] == before + 1
    with switches(False, False):
        plan = cm.region_solid_subsegments(region, [])
        assert not plan["segments"]


# ---------------- fusao de compensadores iguais encostados ----------------

def _wall():
    return m.XYZ(0.0, 0.0, 0.0), m.XYZ(1.0, 0.0, 0.0)


def _pieces(layout, node_index=None, variant=0):
    p0, d = _wall()
    placed = m._place_pier_layout(layout, sb.CATALOG, p0, d, "A", 0, node_index=node_index)
    for c in placed:
        c["course_variant"] = variant
    return placed


def _extents(cands):
    p0, d = _wall()
    return [(c["logical_code"], round(a, 2), round(b, 2)) for c, (a, b) in
            zip(cands, ws._candidate_extents_on_wall(cands, p0, d))]


def test_fusion_c04_c04_becomes_c09_same_span():
    cands = _pieces([("B39", 0.0, 39.0)]) + _pieces([("C04", 40.0, 44.0), ("C04", 45.0, 49.0)])
    p0, d = _wall()
    assert ws.fuse_adjacent_equal_compensators(cands, 0, p0, d, sb.CATALOG) == 1
    assert _extents(cands) == [("B39", 0.0, 39.0), ("C09", 40.0, 49.0)]
    assert cands[1]["fused_from"] == ["C04", "C04"]


def test_fusion_never_touches_node_pieces_mixed_codes_wide_gaps_or_non_compensator_targets():
    p0, d = _wall()
    node = _pieces([("C04", 0.0, 4.0)], node_index=3) + _pieces([("C04", 5.0, 9.0)])
    assert ws.fuse_adjacent_equal_compensators(node, 0, p0, d, sb.CATALOG) == 0
    mixed = _pieces([("C04", 0.0, 4.0), ("C09", 5.0, 14.0)])
    assert ws.fuse_adjacent_equal_compensators(mixed, 0, p0, d, sb.CATALOG) == 0
    gap = _pieces([("C04", 0.0, 4.0), ("C04", 7.0, 11.0)])
    assert ws.fuse_adjacent_equal_compensators(gap, 0, p0, d, sb.CATALOG) == 0
    # C09 + 1 + C09 = 19 = B19, que NAO e compensador: fica com
    # `_merge_adjacent_compensator_pairs` e a guarda de ponta aberta (secao 2)
    nines = _pieces([("C09", 0.0, 9.0), ("C09", 10.0, 19.0)])
    assert ws.fuse_adjacent_equal_compensators(nines, 0, p0, d, sb.CATALOG) == 0


def test_fusion_respects_start_index_and_course_variant():
    p0, d = _wall()
    cands = _pieces([("C04", 0.0, 4.0)]) + _pieces([("C04", 5.0, 9.0)])
    assert ws.fuse_adjacent_equal_compensators(cands, 1, p0, d, sb.CATALOG) == 0
    cands = _pieces([("C04", 0.0, 4.0)], variant=0) + _pieces([("C04", 5.0, 9.0)], variant=1)
    assert ws.fuse_adjacent_equal_compensators(cands, 0, p0, d, sb.CATALOG) == 0


def test_residual_rejected_when_opposite_family_stays_open_in_same_segment():
    """Padrao TGD (4 paredes V2, 6 V1): fiadas impares fecham, pares vazias."""
    with_ = _fill(64, absorptions=0)
    with_["residual_absorptions"] = [{"course": "B", "seg_start_cm": 10.0, "seg_end_cm": 74.0, "residual_cm": 1.0}]
    with_["non_modular"] = [{"course": "A", "seg_start_cm": 5.0, "seg_end_cm": 79.5, "current_length_cm": 74.5}]
    without = _fill(0)
    without["non_modular"] = [{"course": "A", "seg_start_cm": 5.0, "seg_end_cm": 79.5, "current_length_cm": 74.5},
                              {"course": "B", "seg_start_cm": 9.5, "seg_end_cm": 74.5, "current_length_cm": 65.0}]
    fn = _Residual(with_, without)
    with switches(True, False):
        out = ws.physical_tolerance_trial(fn)
    assert out["physical_tolerance_trial"][0]["opposite_family_left_open"] is True
    assert not out["candidates"]


def test_opposite_family_opening_conflict_does_not_block_absorption():
    with_ = _fill(64)
    with_["residual_absorptions"] = [{"course": "B", "seg_start_cm": 10.0, "seg_end_cm": 74.0, "residual_cm": 1.0}]
    with_["non_modular"] = [{"course": "A", "seg_start_cm": 5.0, "seg_end_cm": 79.5, "current_length_cm": 74.5,
                             "conflict": "ABERTURA_NAO_COMPATIVEL"}]
    fn = _Residual(with_, _fill(0, 140))
    with switches(True, False):
        out = ws.physical_tolerance_trial(fn)
    assert out["physical_tolerance_trial"][0]["accepted"] is True
