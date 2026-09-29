# -*- coding: utf-8 -*-
"""SECAO 84 de REGRAS_MODULACAO_BLOCOS.md - faixa de compensacao na JAMBA
(correcao do usuario, 2026-09-28).

Compensador (C09) e pastilha (C04) junto de porta/janela ficam ENCOSTADOS no vao
e na MESMA faixa vertical em todas as fiadas da lateral - em vez de alternar entre
"junto do vao" e "20 cm para dentro" - preservando o prisma dos vazados de 39/19
pela geometria REAL das celulas. So' permutacao das pecas moveis da corrida
jamba -> primeira peca fixa: nenhuma peca criada ou removida.

Fixture = o trecho REAL da parede W1 do 'butanta testes' (porta com jamba em
t = 79 cm, T no inicio do eixo): o solver assentava a fiada par
`B34(no') | B34 | C09 | vao` e a impar `B34 | C09 | B19 | vao` - o C09 alternando
entre 0 e 20 cm do vao. Esperado na impar: `B34 | B19 | C09 | vao`.

Catalogo com as celulas MEDIDAS nas familias do documento (Revit, 2026-09-28) - o
CATALOG aproximado de tests/solver_bench.py esconde desalinhamentos de ~1 cm.

    py -3 -m pytest tests/test_jamb_compensator_alignment.py -q
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import solver_bench as sb  # noqa: E402

m = sb.m
ft, seg = sb.ft, sb.seg
from core.engine import b34_run_arrangement as R  # noqa: E402

FT_PER_CM = 1.0 / 30.48


def _cell(center_cm, size_cm):
    return {"center_local": (center_cm * FT_PER_CM, 0.0), "size_local": (size_cm * FT_PER_CM, 8.0 * FT_PER_CM)}


def _block(code, length_cm, cells):
    return {"symbol": None, "logical_code": code, "length_cm": float(length_cm), "height_cm": 19.0,
            "width_cm": 14.0, "cells_local": cells, "is_special_bond": code in ("B34", "B54"),
            "is_compensator": code in ("C09", "C04"), "source_instance_id": None}


# celulas reais (centro, largura em cm) lidas das familias do 'butanta testes'
REAL = {
    "B39": _block("B39", 39, [_cell(-9.1135, 15.758), _cell(9.1135, 15.758)]),
    "B34": _block("B34", 34, [_cell(-9.1135, 10.759), _cell(6.614, 15.758)]),
    "B54": _block("B54", 54, [_cell(-16.612, 15.758), _cell(0.0, 12.497), _cell(16.612, 15.758)]),
    "B19": _block("B19", 19, [_cell(0.0, 13.99)]),
    "C09": _block("C09", 9, []),
    "C04": _block("C04", 4, []),
}
LENGTH = 369.0
DOOR = (79.0, 170.0)
N_COURSES = 10
EVEN = [("B34", 35, 69), ("C09", 70, 79)]
EVEN_NODE = [("B34", 0, 34)]
ODD = [("B34", 15, 49), ("C09", 50, 59), ("B19", 60, 79)]
EVEN_AFTER = [("B39", 170, 209), ("B39", 210, 249), ("B39", 250, 289), ("B39", 290, 329), ("B39", 330, 369)]
ODD_AFTER = [("B19", 170, 189), ("B39", 190, 229), ("B39", 230, 269), ("B39", 270, 309), ("B39", 310, 349),
             ("B19", 350, 369)]


def _setup(reverse=False, even=EVEN, odd=ODD, even_node=EVEN_NODE, door=DOOR):
    if reverse:
        walls = [(seg(LENGTH, 0, 0, 0), ft(14.0), (False, False))]
        p0, direction = m.XYZ(ft(LENGTH), 0.0, 0.0), m.XYZ(-1.0, 0.0, 0.0)
    else:
        walls = [(seg(0, 0, LENGTH, 0), ft(14.0), (False, False))]
        p0, direction = m.XYZ(0.0, 0.0, 0.0), m.XYZ(1.0, 0.0, 0.0)
    openings = [[(ft(door[0]), ft(door[1]), 0.0, ft(221.0))]]
    cc = {}
    for c in range(N_COURSES):
        layout = (list(even) + EVEN_AFTER) if c % 2 == 0 else (list(odd) + ODD_AFTER)
        pieces = m._place_pier_layout(layout, REAL, p0, direction, c, 0)
        if c % 2 == 0:
            for code, a, b in even_node:
                pieces.extend(m._place_pier_layout([(code, a, b)], REAL, p0, direction, c, 0, node_index=2,
                                                   placement_reason="T_INTERSECTION_MAIN"))
        cc[c] = pieces
    return cc, walls, openings, p0, direction


def _row(cc, course, p0, direction, t_max=LENGTH + 1):
    out = []
    for cand in cc[course]:
        lo, hi = m._candidate_extent_on_wall_axis(cand, p0, direction)
        if hi <= t_max + 1e-6:
            out.append((round(lo, 1), round(hi, 1), cand["logical_code"], cand.get("node_index")))
    return sorted(out)


def _codes_near_jamb(cc, course, p0, direction):
    return [(code, lo, hi) for lo, hi, code, _n in _row(cc, course, p0, direction, t_max=DOOR[0])]


def _arrange(cc, walls, openings, on=True):
    return R.arrange_b34_runs(cc, walls, openings, REAL, jamb_compensator_alignment=on)


def _prism_misaligned(cc, walls, p0, direction, t_lo, t_hi):
    """Regua INDEPENDENTE do passe: vazados (cells_world) de cada fiada que caem
    sobre compensador, sobre junta ou a mais de 2 cm de um vazado da vizinha."""
    rows = {}
    for c, lst in cc.items():
        items = []
        for cand in lst:
            lo, hi = m._candidate_extent_on_wall_axis(cand, p0, direction)
            cells = [((cell["point"].X - p0.X) * direction.X + (cell["point"].Y - p0.Y) * direction.Y) * 30.48
                     for cell in cand.get("cells_world") or []]
            items.append((lo, hi, cells))
        rows[c] = sorted(items)
    bad = 0
    for c in sorted(rows):
        for d in (c - 1, c + 1):
            if d not in rows:
                continue
            for lo, hi, cells in rows[c]:
                for t in cells:
                    if not (t_lo <= t <= t_hi):
                        continue
                    cover = [r for r in rows[d] if r[0] - 1e-6 <= t <= r[1] + 1e-6]
                    if not cover:
                        bad += 1
                        continue
                    if not cover[0][2] or min(abs(t - q) for q in cover[0][2]) > 2.0:
                        bad += 1
    return bad


# ------------------------------------------------------------------ o caso do usuario
def test_red_sem_a_regra_o_compensador_alterna_entre_as_fiadas():
    cc, walls, openings, p0, d = _setup()
    census = R.jamb_strip_census(cc, walls, openings, REAL)
    assert census["alternating"] == 1 and census["touching_all"] == 0
    assert _codes_near_jamb(cc, 1, p0, d) == [("B34", 15.0, 49.0), ("C09", 50.0, 59.0), ("B19", 60.0, 79.0)]


def test_green_compensador_encosta_no_vao_em_todas_as_fiadas():
    cc, walls, openings, p0, d = _setup()
    summary = _arrange(cc, walls, openings)
    assert summary["jamb_sides_changed"] == 1
    for c in range(1, N_COURSES, 2):
        assert _codes_near_jamb(cc, c, p0, d) == [("B34", 15.0, 49.0), ("B19", 50.0, 69.0), ("C09", 70.0, 79.0)]
    for c in range(0, N_COURSES, 2):
        assert _codes_near_jamb(cc, c, p0, d) == [("B34", 0.0, 34.0), ("B34", 35.0, 69.0), ("C09", 70.0, 79.0)]
    census = R.jamb_strip_census(cc, walls, openings, REAL)
    assert census["alternating"] == 0 and census["touching_all"] == 1


def test_prisma_dos_vazados_melhora_pela_geometria_real():
    cc, walls, openings, p0, d = _setup()
    before = _prism_misaligned(cc, walls, p0, d, 0.0, DOOR[0])
    _arrange(cc, walls, openings)
    after = _prism_misaligned(cc, walls, p0, d, 0.0, DOOR[0])
    assert after < before, (before, after)


def test_espelhado_da_o_mesmo_resultado_ao_longo_do_eixo():
    cc, walls, openings, p0, d = _setup(reverse=True)
    _arrange(cc, walls, openings)
    for c in range(1, N_COURSES, 2):
        assert _codes_near_jamb(cc, c, p0, d) == [("B34", 15.0, 49.0), ("B19", 50.0, 69.0), ("C09", 70.0, 79.0)]


# ------------------------------------------------------------------ invariantes
def test_mesmas_pecas_mesmas_pontas_no_e_vao_intactos():
    cc, walls, openings, p0, d = _setup()
    before = dict((c, _row(cc, c, p0, d)) for c in cc)
    _arrange(cc, walls, openings)
    for c in cc:
        after = _row(cc, c, p0, d)
        assert sorted(x[2] for x in after) == sorted(x[2] for x in before[c])  # nenhuma peca criada/removida
        assert [x for x in after if x[3] is not None] == [x for x in before[c] if x[3] is not None]  # no' fixo
        for lo, hi, _code, _n in after:
            assert hi <= DOOR[0] + 1e-6 or lo >= DOOR[1] - 1e-6  # nada dentro do vao
        for (a_lo, a_hi, _x, _n1), (b_lo, _b_hi, _y, _n2) in zip(after, after[1:]):
            assert b_lo - a_hi >= 1.0 - 1e-6  # sem sobreposicao; juntas de 1 cm
        # fora da faixa da jamba nada muda
        assert [x for x in after if x[0] >= DOOR[1] - 1e-6] == [x for x in before[c] if x[0] >= DOOR[1] - 1e-6]


def test_nao_cria_compensadores_encostados():
    cc, walls, openings, p0, d = _setup()
    _arrange(cc, walls, openings)
    for c in cc:
        row = _row(cc, c, p0, d)
        for (_a, a_hi, x, _n1), (b_lo, _b, y, _n2) in zip(row, row[1:]):
            assert not (x in ("C09", "C04") and y in ("C09", "C04") and b_lo - a_hi <= 1.6)


def test_idempotente_e_deterministico():
    cc, walls, openings, p0, d = _setup()
    _arrange(cc, walls, openings)
    snap = dict((c, _row(cc, c, p0, d)) for c in cc)
    again = _arrange(cc, walls, openings)
    assert again["jamb_sides_changed"] == 0
    assert dict((c, _row(cc, c, p0, d)) for c in cc) == snap
    cc2, walls2, openings2, p02, d2 = _setup()
    _arrange(cc2, walls2, openings2)
    assert dict((c, _row(cc2, c, p02, d2)) for c in cc2) == snap


def test_chave_desligada_nao_muda_nada():
    cc, walls, openings, p0, d = _setup()
    before = dict((c, _row(cc, c, p0, d)) for c in cc)
    summary = _arrange(cc, walls, openings, on=False)
    assert "jamb_sides_changed" not in summary
    assert dict((c, _row(cc, c, p0, d)) for c in cc) == before


# ------------------------------------------------------------------ o que NAO fecha fica registrado
def test_compensador_atras_de_peca_de_no_fica_registrado_sem_mexer():
    even = [("B19", 0, 19), ("C04", 20, 24)]
    node = [("B34", 25, 59)]
    odd = [("B39", 0, 39), ("B19", 40, 59)]
    door = (59.0, 170.0)
    cc, walls, openings, p0, d = _setup(even=even, odd=odd, even_node=node, door=door)
    before = dict((c, _row(cc, c, p0, d)) for c in cc)
    summary = _arrange(cc, walls, openings)
    assert dict((c, _row(cc, c, p0, d)) for c in cc) == before
    conflicts = [x for lst in summary["jamb_conflicts_by_wall"].values() for x in lst]
    assert any("FIXED_PIECE_BETWEEN" in x["reasons"] and x["codes"] == ["C04"] for x in conflicts), conflicts


def test_familia_sem_compensador_continua_sem_compensador():
    cc, walls, openings, p0, d = _setup()
    _arrange(cc, walls, openings)
    for c in range(0, N_COURSES, 2):
        after = [x[2] for x in _row(cc, c, p0, d, t_max=DOOR[0])]
        assert after.count("C09") == 1 and "C04" not in after


def test_faixa_isenta_so_a_junta_do_compensador_encostado():
    cc, walls, openings, p0, d = _setup()
    _arrange(cc, walls, openings)
    rows = R._collect_rows(cc, walls)
    wall = R._Wall(0, rows[0], walls, openings, REAL, 1.5, jamb_alignment=True)
    for f in wall.fam:
        faces = [round(x, 3) for x in wall._jamb_strip_faces(f)]
        # C09 [70,79] encostado no vao: so' as duas faces da junta 69|70
        assert faces == [69.0, 70.0], faces
