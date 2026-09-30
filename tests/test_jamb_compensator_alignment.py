# -*- coding: utf-8 -*-
"""SECOES 84/85 de REGRAS_MODULACAO_BLOCOS.md - faixa de compensacao na JAMBA
(correcao do usuario, 2026-09-28) e recomposicao da lateral com o PRISMA pela
area livre comum real primeiro (correcao do usuario, 2026-09-29).

Compensador (C09) e pastilha (C04) junto de porta/janela ficam ENCOSTADOS no vao
e na MESMA faixa vertical em todas as fiadas da lateral - em vez de alternar entre
"junto do vao" e "20 cm para dentro" - preservando o prisma dos vazados de 39/19
pela geometria REAL das celulas. So' permutacao das pecas moveis da corrida
jamba -> primeira peca fixa: nenhuma peca criada ou removida.

Fixture = o trecho REAL da parede W1 do 'butanta testes' (porta com jamba em
t = 79 cm, T no inicio do eixo): o solver assentava a fiada par
`B34(no') | B34 | C09 | vao` e a impar `B34 | C09 | B19 | vao` - o C09 alternando
entre 0 e 20 cm do vao. Secao 84 (so' permutacao) dava `B34 | B19 | C09 | vao`
na impar; secao 85 (prisma primeiro, composicao de mesmo comprimento com +-1 peca)
da' `B39 | B19 | C04 | vao` na impar e `B34(no') | B39 | C04 | vao` na par - a
faixa de compensacao continua encostada e alinhada (C04 [75,79] nas duas) e as
celulas dos vazados passam a se sobrepor com largura comum >= 8.99 cm.

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
# secao 85: o que a lateral vira (prisma pela area primeiro, faixa encostada)
ODD_85 = [("B39", 15.0, 54.0), ("B19", 55.0, 74.0), ("C04", 75.0, 79.0)]
EVEN_85 = [("B34", 0.0, 34.0), ("B39", 35.0, 74.0), ("C04", 75.0, 79.0)]
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
        assert _codes_near_jamb(cc, c, p0, d) == ODD_85
    for c in range(0, N_COURSES, 2):
        assert _codes_near_jamb(cc, c, p0, d) == EVEN_85
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
        assert _codes_near_jamb(cc, c, p0, d) == ODD_85


# ------------------------------------------------------------------ invariantes
def test_mesmas_pontas_mesma_contagem_no_e_vao_intactos():
    cc, walls, openings, p0, d = _setup()
    before = dict((c, _row(cc, c, p0, d)) for c in cc)
    _arrange(cc, walls, openings)
    for c in cc:
        after = _row(cc, c, p0, d)
        # secao 85: composicao de mesmo comprimento, sem peca a mais nesta lateral
        assert len(after) == len(before[c])
        comps = lambda row: sum(1 for x in row if x[2] in ("C09", "C04"))  # noqa: E731
        assert comps(after) <= comps(before[c])  # nenhum compensador novo
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


def test_um_compensador_por_fiada_na_lateral():
    cc, walls, openings, p0, d = _setup()
    _arrange(cc, walls, openings)
    for c in range(N_COURSES):
        after = [x[2] for x in _row(cc, c, p0, d, t_max=DOOR[0])]
        assert after.count("C09") + after.count("C04") == 1


def test_faixa_isenta_so_a_junta_do_compensador_encostado():
    cc, walls, openings, p0, d = _setup()
    _arrange(cc, walls, openings)
    rows = R._collect_rows(cc, walls)
    wall = R._Wall(0, rows[0], walls, openings, REAL, 1.5, jamb_alignment=True)
    for f in wall.fam:
        faces = [round(x, 3) for x in wall._jamb_strip_faces(f)]
        # C04 [75,79] encostado no vao: so' as duas faces da junta 74|75
        assert faces == [74.0, 75.0], faces


# ------------------------------------------------------------------ secao 85 (2026-09-29)
def _wall_from(rows_by_course, length, openings_cm, node_codes=()):
    """Parede reta [0, length] com as fileiras dadas: {fiada: [(codigo, lo, hi)]}.
    Pecas cujo intervalo esta' em `node_codes` viram peca de no' (fixa)."""
    walls = [(seg(0, 0, length, 0), ft(14.0), (False, False))]
    p0, direction = m.XYZ(0.0, 0.0, 0.0), m.XYZ(1.0, 0.0, 0.0)
    openings = [[(ft(a), ft(b), 0.0, ft(221.0)) for a, b in openings_cm]]
    cc = {}
    for c, layout in rows_by_course.items():
        pieces = []
        for code, a, b in layout:
            if (code, a, b) in node_codes:
                pieces.extend(m._place_pier_layout([(code, a, b)], REAL, p0, direction, c, 0, node_index=7,
                                                   placement_reason="T_INTERSECTION_MAIN"))
            else:
                pieces.extend(m._place_pier_layout([(code, a, b)], REAL, p0, direction, c, 0))
        cc[c] = pieces
    return cc, walls, openings, p0, direction


def test_b19_no_miolo_ou_so_encostado_em_no_nao_e_fechamento():
    """Pedido do usuario: B19 so' em fechamento (jamba ativa, ponta livre, ou
    logo atras da faixa de compensacao encostada no vao). Encostar num B54 de
    no' NAO basta, e nenhuma excecao automatica devolve B19 ao miolo."""
    row = [("B39", 0, 39), ("B19", 40, 59), ("B39", 60, 99), ("B19", 100, 119), ("B54", 120, 174),
           ("B39", 175, 214), ("B19", 215, 234), ("C09", 235, 244)]
    node = (("B54", 120, 174),)
    cc, walls, openings, _p0, _d = _wall_from(dict((c, row) for c in range(4)), 300.0, [(245.0, 300.0)], node)
    rows = R._collect_rows(cc, walls)
    wall = R._Wall(0, rows[0], walls, openings, REAL, 1.5, ties=[147.0], jamb_alignment=True)
    f = wall.course_fam[0]
    verdict = dict((round(s.lo), wall._half_block_admissible(f, i))
                   for i, s in enumerate(wall.fam[f]) if s.code == "B19")
    assert verdict == {40: False, 100: False, 215: True}, verdict
    assert wall._half_blocks_misplaced(f) == 2


def test_pilar_de_referencia_do_usuario_nao_e_recomposto():
    """Pilar direito da janela central do 'butanta testes' (imagem 7 do
    usuario), jamba em t = 90: impar `B39 | B39 | C09 | encontro`, par
    `B19 | B39 | C09 | B54(no')`, igual as fiadas cheias abaixo e acima. A celula
    do B39 [130,169] cruza a do B54 do no' com 4 cm - quebra do ENCONTRO, que
    existe igual nas fiadas cheias: trocar a lateral so' mudaria a quebra de
    lugar (a versao anterior da secao 85 trocava por `B34|C09|B39|C04`)."""
    odd_full = [("B39", 10, 49), ("B39", 50, 89), ("B39", 90, 129), ("B39", 130, 169), ("C09", 170, 179),
                ("B39", 195, 234), ("B39", 235, 274)]
    even_full = [("B39", 30, 69), ("B39", 70, 109), ("B39", 110, 149), ("C09", 150, 159), ("B54", 160, 214),
                 ("B39", 215, 254), ("B19", 255, 274)]
    odd_win = [p for p in odd_full if p[1] >= 90]
    even_win = [("B19", 90, 109)] + [p for p in even_full if p[1] >= 110]
    rows = {}
    for c in range(11):
        window = 3 <= c <= 8
        rows[c] = (odd_win if window else odd_full) if c % 2 else (even_win if window else even_full)
    cc, walls, openings, p0, d = _wall_from(rows, 274.0, [(0.0, 90.0)], (("B54", 160, 214),))
    # a janela so' corta as fiadas 3..8: abaixo e acima as fileiras sao cheias;
    # o encontro: parede que cruza em [179,195] nas impares, B54 do no' nas pares
    before = dict((c, _row(cc, c, p0, d)) for c in cc)
    summary = R.arrange_b34_runs(cc, walls, openings, REAL, tie_positions_by_wall={0: [187.0]},
                                 jamb_compensator_alignment=True)
    assert dict((c, _row(cc, c, p0, d)) for c in cc) == before
    conflicts = [x for lst in summary["jamb_conflicts_by_wall"].values() for x in lst]
    # C09 encostado no encontro e' fechamento, nao pastilha fora da jamba
    assert not any("COMPENSATOR_NOT_AT_JAMB" in x["reasons"] for x in conflicts), conflicts


def test_regua_por_area_usa_largura_comum_real():
    """B39 [930,969] x B54 [960,1014]: centros das celulas a 11.8 cm, largura
    comum 4.0 cm < 8.99 (menor celula) -> estreita; B39 x B39 alinhados -> ok."""
    from core.engine import prism_free_area as PF
    cc, walls, _openings, p0, d = _wall_from({0: [("B39", 930, 969)], 1: [("C09", 950, 959), ("B54", 960, 1014)],
                                              2: [("B39", 930, 969)]}, 1100.0, [])
    rows = PF.wall_rows(cc, walls, 0)
    right_cell = rows[0][0][3][1]
    status, width, _area = PF.cell_continuity(right_cell, rows[1])
    assert status in ("narrow", "interrupted") and abs(width - 4.0) < 0.05, (status, width)
    status, width, _area = PF.cell_continuity(right_cell, rows[2])
    assert status == "ok" and width >= PF.PRISM_MIN_COMMON_WIDTH_CM


def _door_with_lintel_rows():
    """Porta [0,90] com as fiadas 0..8 cortadas e duas fiadas CHEIAS acima (9 e
    10) - as fiadas-ponte da secao 85. Pilar a direita ate' t = 180."""
    odd_door = [("B39", 90, 129), ("B39", 130, 169), ("C09", 170, 179)]
    even_door = [("B19", 90, 109), ("B39", 110, 149), ("B39", 150, 189)]
    odd_full = [("B39", 10, 49), ("B39", 50, 89)] + odd_door
    even_full = [("B39", 30, 69), ("B39", 70, 109), ("B39", 110, 149), ("B39", 150, 189)]
    rows = {}
    for c in range(11):
        door = c <= 8
        rows[c] = (odd_door if door else odd_full) if c % 2 else (even_door if door else even_full)
    return rows


def test_percurso_obrigatorio_da_jamba_sobre_compensador_quebra():
    """SECAO 85: a coluna de vazados junto da jamba e' percurso de graute; sobre
    peca macica ela quebra (composicao invalida)."""
    rows = {0: [("C09", 90, 99), ("B39", 100, 139)], 1: [("B19", 90, 109), ("B39", 110, 149)],
            2: [("C09", 90, 99), ("B39", 100, 139)], 3: [("B19", 90, 109), ("B39", 110, 149)]}
    cc, walls, openings, _p0, _d = _wall_from(rows, 200.0, [(0.0, 90.0)])
    wall = R._Wall(0, R._collect_rows(cc, walls)[0], walls, openings, REAL, 1.5, jamb_alignment=True)
    ok, width = wall._jamb_path(90.0, 1)
    # B19 [90,109] cell 92.5-106.5 sobre o B39 [100,139] (celula 100.8-116.6): 5,7 cm < 8,99
    assert not ok and width < R.PRISM_FULL_COLUMN_WIDTH_CM


def test_fiadas_ponte_acima_da_porta_entram_na_unidade_da_jamba():
    cc, walls, openings, _p0, _d = _wall_from(_door_with_lintel_rows(), 190.0, [(0.0, 90.0)])
    wall = R._Wall(0, R._collect_rows(cc, walls)[0], walls, openings, REAL, 1.5, jamb_alignment=True)
    units, _blocked = wall._jamb_units()
    key = [k for k in units if any(abs(e - 90.0) < 1.0 and d == 1 for e, d in k)][0]
    courses = sorted(c for f, _sp, _es in units[key] for c in wall._courses_of(f))
    assert 9 in courses and 10 in courses, courses  # as duas fiadas cheias acima da verga
    # prioridade: pilarete (2 jambas) antes de lateral simples; corrida curta antes
    assert wall._unit_priority(((1.0, 1), (2.0, -1)), units[key])[0] < wall._unit_priority(key, units[key])[0]


def test_resumo_lista_percursos_obrigatorios():
    cc, walls, openings, _p0, _d = _setup()
    summary = _arrange(cc, walls, openings)
    rp = summary["required_paths"]
    assert rp["total"] == 2 and rp["ok_after"] >= rp["ok_before"]
    assert all(set(item) >= {"wall_idx", "edge_cm", "side", "common_width_cm"} for item in rp["broken"])


# ------------------------------------------------------------------ secao 85.8 (correcoes de 2026-09-30)
def test_canaleta_u34_com_pastilha_vira_u39():
    """Verga da W2 (porta 8079009): `U34 [415-449] | U39 x4 | C04 [610-614] | B54` ocupa 200 cm = 5 x U39
    exatas - a canaleta 34 com pastilha onde cabem U39 e' erro (correcao do usuario)."""
    catalog = dict(REAL)
    catalog["CHANNEL_U_39"] = dict(_block("CHANNEL_U_39", 39, []), is_channel=True)
    catalog["CHANNEL_U_34"] = dict(_block("CHANNEL_U_34", 34, []), is_channel=True)
    walls = [(seg(0, 0, 800.0, 0), ft(14.0), (False, False))]
    p0, direction = m.XYZ(0.0, 0.0, 0.0), m.XYZ(1.0, 0.0, 0.0)
    layout = [("CHANNEL_U_34", 415, 449), ("CHANNEL_U_39", 450, 489), ("CHANNEL_U_39", 490, 529),
              ("CHANNEL_U_39", 530, 569), ("CHANNEL_U_39", 570, 609), ("C04", 610, 614)]
    cc = {11: m._place_pier_layout(layout, catalog, p0, direction, 11, 0)}
    cc[11].extend(m._place_pier_layout([("B54", 615, 669)], catalog, p0, direction, 11, 0, node_index=3,
                                       placement_reason="T_INTERSECTION_MAIN"))
    out = R.cleanup_channel_runs(cc, walls, catalog)
    assert out["runs"] == 1
    row = _row(cc, 11, p0, direction, t_max=900.0)
    assert [(lo, hi, code) for lo, hi, code, _n in row] == [
        (415.0, 454.0, "CHANNEL_U_39"), (455.0, 494.0, "CHANNEL_U_39"), (495.0, 534.0, "CHANNEL_U_39"),
        (535.0, 574.0, "CHANNEL_U_39"), (575.0, 614.0, "CHANNEL_U_39"), (615.0, 669.0, "B54")]


def test_canaleta_que_nao_fecha_exata_fica():
    catalog = dict(REAL)
    catalog["CHANNEL_U_39"] = dict(_block("CHANNEL_U_39", 39, []), is_channel=True)
    catalog["CHANNEL_U_34"] = dict(_block("CHANNEL_U_34", 34, []), is_channel=True)
    walls = [(seg(0, 0, 800.0, 0), ft(14.0), (False, False))]
    p0, direction = m.XYZ(0.0, 0.0, 0.0), m.XYZ(1.0, 0.0, 0.0)
    layout = [("CHANNEL_U_34", 415, 449), ("CHANNEL_U_39", 450, 489), ("CHANNEL_U_39", 490, 529)]
    cc = {11: m._place_pier_layout(layout, catalog, p0, direction, 11, 0)}
    before = _row(cc, 11, p0, direction, t_max=900.0)
    assert R.cleanup_channel_runs(cc, walls, catalog)["runs"] == 0
    assert _row(cc, 11, p0, direction, t_max=900.0) == before


def test_recompositor_nao_cria_pastilha_nem_poe_pastilha_atras_do_b19():
    """85.8: `B39 | B19 | vao` nunca vira `B34 | C04 | B19 | vao` para alinhar vazado menor."""
    even = [("B19", 0, 19), ("C04", 20, 24)]
    node = [("B34", 25, 59)]
    odd = [("B39", 0, 39), ("B19", 40, 59)]
    cc, walls, openings, p0, d = _setup(even=even, odd=odd, even_node=node, door=(59.0, 170.0))
    _arrange(cc, walls, openings)
    for c in range(1, N_COURSES, 2):
        codes = [x[2] for x in _row(cc, c, p0, d, t_max=59.0)]
        assert "C04" not in codes and "C09" not in codes, codes


# ------------------------------------------------------------------ secao 85.9 (desenho do usuario, 2026-09-30)
def _wall_rows(rows_by_course, length, openings_cm, node_codes=("B54",)):
    """Parede reta com fileiras literais {fiada: [(codigo, lo, hi, lado)]}: U39/U34
    = canaleta, lado do B34 = +1 vazado menor para t crescente, B54 = no'."""
    catalog = dict(REAL)
    for code, length_cm in (("CHANNEL_U_39", 39), ("CHANNEL_U_34", 34), ("CHANNEL_U_19", 19)):
        catalog[code] = dict(_block(code, length_cm, []), is_channel=True)
    walls = [(seg(0, 0, length, 0), ft(14.0), (False, False))]
    p0, direction = m.XYZ(0.0, 0.0, 0.0), m.XYZ(1.0, 0.0, 0.0)
    openings = [[(ft(a), ft(b), 0.0, ft(221.0)) for a, b in openings_cm]]
    cc = {}
    for c, layout in rows_by_course.items():
        pieces = []
        for code, a, b, side in layout:
            code = ("CHANNEL_U_" + code[1:]) if code.startswith("U") else code
            node = code in node_codes
            # B34 real: vazado menor em x local -9,11 -> x_dir invertido poe o menor em t crescente
            x_dir = m.XYZ(-1.0, 0.0, 0.0) if (code == "B34" and side > 0) else direction
            pieces.append(m._make_block_candidate(
                code, catalog[code], c, p0 + direction * ft((a + b) / 2.0), x_dir,
                "T_INTERSECTION_MAIN" if node else "STANDARD_FILL", node_index=(7 if node else None), wall_idx=0))
        cc[c] = pieces
    return cc, walls, openings, p0, direction, catalog


def _sided_row(cc, course, p0, direction, lo, hi):
    """[(codigo curto, lo, hi, lado)] da fiada no trecho - lado pela celula menor real."""
    out = []
    for cand in cc[course]:
        a, b = m._candidate_extent_on_wall_axis(cand, p0, direction)
        if b < lo - 0.5 or a > hi + 0.5:
            continue
        side = 0
        cells = cand.get("cells_world") or []
        if cand["logical_code"] == "B34" and cells:
            small = min(cells, key=lambda cl: float(cl["size_local"][0]))
            t = ((small["point"].X - p0.X) * direction.X + (small["point"].Y - p0.Y) * direction.Y) * 30.48
            side = 1 if t > (a + b) / 2.0 else -1
        out.append((cand["logical_code"].replace("CHANNEL_U_", "U"), int(round(a)), int(round(b)), side))
    return sorted(out, key=lambda x: x[1])


def _arrange_real(cc, walls, openings, catalog, ties):
    return R.arrange_b34_runs(cc, walls, openings, catalog, tie_positions_by_wall={0: ties},
                              half_block_code="B19", half_block_tie_gap_cm=m.HALF_BLOCK_TIE_ADJACENCY_CM,
                              joint_identity_guard=True, jamb_compensator_alignment=True)


def test_b34_vazado_menor_sobre_vazado_menor_passa_com_a_tolerancia_geometrica():
    """85.9: dois B34 em amarracao (20 cm), um virado para cada lado: 10,759 - 1,773 = 8,986 cm livres
    - 0,04 mm abaixo de 8,99. Com a tolerancia de 0,5 mm a coluna do vazado menor passa."""
    from core.engine import prism_free_area as PF
    cc, walls, _o, _p0, _d, _cat = _wall_rows({0: [("B34", 945, 979, 1)], 1: [("B34", 965, 999, -1)]},
                                              1100.0, [])
    rows = PF.wall_rows(cc, walls, 0)
    small = min(rows[0][0][3], key=lambda iv: iv[1] - iv[0])
    status, width, _area = PF.cell_continuity(small, rows[1])
    assert status == "ok" and 8.95 < width <= 8.99, (status, width)


# W4 do 'butanta testes', pilarete a direita da porta 8078996 [804,945] ate' o T (B54 1015-1069; a parede
# que cruza passa em 1035-1049 nas impares) - fileiras REAIS do lote 20260929-155403 (leitura do Revit)
W4_LOTE1 = dict(
    [(c, [("B39", 725, 764, 0), ("B39", 765, 804, 0), ("B19", 945, 964, 0), ("B39", 965, 1004, 0),
          ("C09", 1005, 1014, 0), ("B54", 1015, 1069, 0)]) for c in range(0, 11, 2)] +
    [(c, [("B39", 705, 744, 0), ("B39", 745, 784, 0), ("B19", 785, 804, 0), ("B39", 945, 984, 0),
          ("B39", 985, 1024, 0), ("C09", 1025, 1034, 0)]) for c in range(1, 11, 2)] +
    [(11, [("B39", 705, 744, 0), ("B39", 745, 784, 0), ("U39", 785, 824, 0), ("U39", 825, 864, 0),
           ("U39", 865, 904, 0), ("U39", 905, 944, 0), ("U39", 945, 984, 0), ("B39", 985, 1024, 0),
           ("C09", 1025, 1034, 0)]),
     (12, [("B39", 725, 764, 0), ("B39", 765, 804, 0), ("B39", 805, 844, 0), ("B39", 845, 884, 0),
           ("B39", 885, 924, 0), ("B39", 925, 964, 0), ("B39", 965, 1004, 0), ("C09", 1005, 1014, 0),
           ("B54", 1015, 1069, 0)]),
     (13, [("B39", 705, 744, 0), ("B39", 745, 784, 0), ("B39", 785, 824, 0), ("B39", 825, 864, 0),
           ("B39", 865, 904, 0), ("B39", 905, 944, 0), ("B39", 945, 984, 0), ("B39", 985, 1024, 0),
           ("C09", 1025, 1034, 0)])])


def test_grade_de_b34_do_desenho_do_usuario_na_w4():
    """85.9 (desenho do usuario no Revit, 2026-09-30): no lugar de `B19 | B39 | C09 | B54` /
    `B39 | B39 | C09 | encontro`, a grade de B34 com os vazados casados - pares `B34 B34` (menor para o
    no'), impares `B19 B34 B34` (menor para a porta) - e a MESMA grade acima da porta: verga com U34,
    fiadas 12 e 13 com 6 x B34. Nenhuma pastilha no pilarete."""
    cc, walls, openings, p0, d, cat = _wall_rows(W4_LOTE1, 1100.0, [(804.0, 945.0)])
    _arrange_real(cc, walls, openings, cat, [1042.0])
    for c in range(0, 11, 2):
        row = _sided_row(cc, c, p0, d, 940, 1070)
        assert row == [("B34", 945, 979, 1), ("B34", 980, 1014, 1), ("B54", 1015, 1069, 0)], (c, row)
    for c in range(1, 11, 2):
        row = _sided_row(cc, c, p0, d, 940, 1070)
        assert row == [("B19", 945, 964, 0), ("B34", 965, 999, -1), ("B34", 1000, 1034, -1)], (c, row)
    assert _sided_row(cc, 11, p0, d, 826, 1040) == [
        ("U34", 825, 859, 0), ("U34", 860, 894, 0), ("U34", 895, 929, 0), ("U34", 930, 964, 0),
        ("U34", 965, 999, 0), ("B34", 1000, 1034, -1)], _sided_row(cc, 11, p0, d, 826, 1040)
    assert [x[0] for x in _sided_row(cc, 12, p0, d, 806, 1013)] == ["B34"] * 6
    assert [x[0] for x in _sided_row(cc, 13, p0, d, 826, 1033)] == ["B34"] * 6


# W5, pilarete 230-314 entre as portas [109,230] e [314,610] - estado de partida medido no calculo
# offline (C09 em zigue-zague entre as duas jambas, 54 vazados quebrados na janela)
W5_ZIGUE = dict(
    [(c, [("B34", 230, 264, -1), ("B39", 265, 304, 0), ("C09", 305, 314, 0)]) for c in range(0, 11, 2)] +
    [(c, [("C09", 230, 239, 0), ("B39", 240, 279, 0), ("B34", 280, 314, 1)]) for c in range(1, 11, 2)] +
    [(11, [("U39", 95, 134, 0), ("U39", 135, 174, 0), ("U39", 175, 214, 0), ("U39", 215, 254, 0),
           ("B39", 255, 294, 0), ("U39", 295, 334, 0), ("U39", 335, 374, 0), ("U39", 375, 414, 0)]),
     (12, [("B39", 115, 154, 0), ("B39", 155, 194, 0), ("B39", 195, 234, 0), ("B39", 235, 274, 0),
           ("B39", 275, 314, 0), ("B39", 315, 354, 0), ("B39", 355, 394, 0)]),
     (13, [("B39", 95, 134, 0), ("B39", 135, 174, 0), ("B39", 175, 214, 0), ("B39", 215, 254, 0),
           ("B39", 255, 294, 0), ("B39", 295, 334, 0), ("B39", 335, 374, 0), ("B39", 375, 414, 0)])])


def test_pilarete_da_w5_como_o_usuario_corrigiu():
    """85.8 item 1 + 85.9: `C04 | B39 | B39` numa paridade e `C04 | B19 | B39 | B19` na outra (C04 sempre
    na mesma jamba, 4 colunas de 14 cm, juntas a 20 cm). So' falhava em NEW_COINCIDENT_JOINT contra as
    pontas das vergas da fiada 11 - a junta do B19 de fechamento e' isenta (11.8), mas B19 sobre B19 nao
    (as duas paridades iguais seriam a prumo). Qual paridade leva qual composicao e' desempate (a que
    continua igual nas fiadas 12-13 acima da verga e' a mais continua)."""
    cc, walls, openings, p0, d, cat = _wall_rows(W5_ZIGUE, 620.0, [(109.0, 230.0), (314.0, 610.0)])
    _arrange_real(cc, walls, openings, cat, [])
    a = [("C04", 230, 234), ("B39", 235, 274), ("B39", 275, 314)]
    b = [("C04", 230, 234), ("B19", 235, 254), ("B39", 255, 294), ("B19", 295, 314)]
    odd = set(tuple(x[:3] for x in _sided_row(cc, c, p0, d, 229, 315)) for c in range(1, 11, 2))
    even = set(tuple(x[:3] for x in _sided_row(cc, c, p0, d, 229, 315)) for c in range(0, 11, 2))
    assert len(odd) == 1 and len(even) == 1, (odd, even)
    assert set([odd.pop(), even.pop()]) == set([tuple(a), tuple(b)])
