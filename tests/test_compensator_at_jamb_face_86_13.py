# -*- coding: utf-8 -*-
"""SECAO 86.13 de REGRAS_MODULACAO_BLOCOS.md - correcao do usuario de 2026-10-05 (prints do Revit da
recriacao da secao 86): "algumas pastilhas nao estao alinhadas perto de aberturas".

REGRA OBRIGATORIA (reafirma as secoes 84 e 86.6): compensador (C04/C09) ao alcance da jamba fica ENCOSTADO
no vao, na MESMA faixa vertical em todas as fiadas da lateral, e o B19 vai ATRAS dele - desenho do usuario
`B54 | B19 | C09 | vao`, nunca `B54 | C09 | B19 | vao`. O prisma continua falha dura contra o estado de
partida: sem solucao que preserve os dois, a lateral fica e o caso e' registrado
(COMPENSATOR_NOT_AT_JAMB_FACE).

Fixtures = fileiras REAIS: W0 2175-2244 e W2 1069-1160 lidas de volta do Revit (readback da secao 86),
W6 469 = o estado que chega ao recompositor no calculo (mini-planta com as paredes que cruzam, 13 fiadas -
a ultima ainda de BLOCO, so' depois vira cinta de topo), W27 (shaft de 115 cm) e um pilarete de 64 cm
sintetico com a alternancia do print do usuario (`B19 | C04 | B39` / `C04 | B39 | B19`).

    py -3 -m pytest tests/test_compensator_at_jamb_face_86_13.py -q
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import test_jamb_compensator_alignment as J  # noqa: E402  (fixtures com as celulas REAIS)

R = J.R
m = J.m


def _build(rows, length, openings, node_codes=("B54",)):
    """`J._wall_rows` (celulas REAIS) aceitando tambem a canaleta cortada da verga ("UCUT", comprimento livre)
    e pecas sem o lado: {fiada: [(codigo, lo, hi[, lado])]}."""
    catalog = dict(J.REAL)
    for code, length_cm in (("CHANNEL_U_39", 39), ("CHANNEL_U_34", 34), ("CHANNEL_U_19", 19)):
        catalog[code] = dict(J._block(code, length_cm, []), is_channel=True)
    walls = [(J.seg(0, 0, length, 0), J.ft(14.0), (False, False))]
    p0, direction = m.XYZ(0.0, 0.0, 0.0), m.XYZ(1.0, 0.0, 0.0)
    ops = [[(J.ft(a), J.ft(b), 0.0, J.ft(221.0)) for a, b in openings]]
    cc = {}
    for c, layout in rows.items():
        pieces = []
        for item in layout:
            code, a, b = item[:3]
            side = item[3] if len(item) > 3 else 0
            code = ("CHANNEL_U_" + code[1:]) if code.startswith("U") else code
            entry = catalog[code] if code != "CHANNEL_U_CUT" else dict(J._block(code, b - a, []), is_channel=True)
            node = code in node_codes
            x_dir = m.XYZ(-1.0, 0.0, 0.0) if (code == "B34" and side > 0) else direction
            pieces.append(m._make_block_candidate(
                code, entry, c, p0 + direction * J.ft((a + b) / 2.0), x_dir,
                "T_INTERSECTION_MAIN" if node else "STANDARD_FILL", node_index=(7 if node else None), wall_idx=0))
        cc[c] = pieces
    return cc, walls, ops, p0, direction, catalog


def _run(rows, length, openings, ties, node_codes=("B54",), on=True):
    """Fixture literal -> recompositor real (catalogo do solve: so' blocos, sem CHANNEL_*)."""
    cc, walls, ops, p0, d, cat = _build(rows, length, openings, node_codes=node_codes)
    engine_cat = dict((k, v) for k, v in cat.items() if not k.startswith("CHANNEL"))
    old = R.JAMB_COMPENSATOR_AT_FACE_ENABLED
    R.JAMB_COMPENSATOR_AT_FACE_ENABLED = on
    try:
        summary = J._arrange_real(cc, walls, ops, engine_cat, ties)
    finally:
        R.JAMB_COMPENSATOR_AT_FACE_ENABLED = old
    return {"cc": cc, "p0": p0, "d": d, "summary": summary, "walls": walls, "ops": ops, "cat": engine_cat,
            "ties": ties}


def _codes(res, course, lo, hi):
    return [(x[0], x[1], x[2]) for x in J._sided_row(res["cc"], course, res["p0"], res["d"], lo, hi)]


def _broken_cells(res):
    """Regua da trava de prisma (86.6): celulas QUEBRADAS da parede inteira (`_trace_column`)."""
    wall = R._Wall(0, R._collect_rows(res["cc"], res["walls"])[0], res["walls"], res["ops"], res["cat"], 1.5,
                   ties=res["ties"], jamb_alignment=True)
    return wall.wall_broken_cells()


def _conflicts(res):
    return [x for lst in res["summary"]["jamb_conflicts_by_wall"].values() for x in lst]


_CACHE = {}


def _cached(key, fn):
    if key not in _CACHE:
        _CACHE[key] = fn()
    return _CACHE[key]


# ------------------------------------------------------------------ chave e falha dura
def test_regra_ligada_falha_dura_intrinseca_e_ranking_do_estagio_a():
    assert R.JAMB_COMPENSATOR_AT_FACE_ENABLED
    assert "COMPENSATOR_NOT_AT_JAMB_FACE" in R.JAMB_INTRINSIC_FAILURES
    assert R.JAMB_TRANSPARENT_MONOTONE_FAILURES == ("NEW_COINCIDENT_JOINT", "SMALL_VOID_WOULD_MISALIGN",
                                                    "PRISM_WOULD_BREAK")
    base = {"sv": 0, "comps": 1, "offjamb": 0, "paths": 1, "colbroken": 0, "column": 4, "prism": 0, "b19": 0,
            "cp": 0, "ht": 0, "ex": 0, "joints": set(), "stacks": 0, "strips": 0, "b34c": 0, "face": 0}
    assert "COMPENSATOR_NOT_AT_JAMB_FACE" in R._Wall._jamb_failures(dict(base, face=1), base)
    assert "COMPENSATOR_NOT_AT_JAMB_FACE" not in R._Wall._jamb_failures(base, dict(base, face=1))
    # medida sem o termo (codigo anterior) continua valendo
    assert "COMPENSATOR_NOT_AT_JAMB_FACE" not in R._Wall._jamb_failures(
        dict((k, v) for k, v in base.items() if k != "face"), base)


# ------------------------------------------------------------------ a regua `_face_defects`
DOOR = [(0.0, 100.0)]
FORMS = {
    # desenho do usuario e o contrario dele (B19 entre o compensador e a face, C09 contra o no')
    "b19_atras_da_faixa": ([("C09", 100, 109, 0), ("B19", 110, 129, 0), ("B54", 130, 184, 0)], 0),
    "compensador_atras_do_b19": ([("B19", 100, 119, 0), ("C09", 120, 129, 0), ("B54", 130, 184, 0)], 1),
    "pastilha_atras_do_b19_no_encontro": ([("B19", 100, 119, 0), ("C04", 120, 124, 0), ("B54", 125, 179, 0)], 1),
    # pastilha solta atras de bloco inteiro (nao fecha contra encontro)
    "pastilha_solta": ([("B39", 100, 139, 0), ("C09", 140, 149, 0), ("B39", 150, 189, 0)], 1),
    # fechamento de ENCONTRO atras de bloco inteiro (W1 `vao | B39 | C04 | B54`): nao e' o defeito
    "fechamento_de_encontro": ([("B39", 100, 139, 0), ("C04", 140, 144, 0), ("B54", 145, 199, 0)], 0),
    # faixa encostada (forma A, C09 na face) e compensador fora do alcance (60 cm)
    "faixa_c09_c04": ([("C09", 100, 109, 0), ("C04", 110, 114, 0), ("B34", 115, 149, -1)], 0),
    "fora_do_alcance": ([("B39", 100, 139, 0), ("B19", 140, 159, 0), ("C04", 160, 164, 0), ("B39", 165, 204, 0)],
                        0),
}


def test_regua_conta_compensador_fora_da_face_ao_alcance_da_jamba():
    names = sorted(FORMS)
    rows = dict((c, FORMS[n][0]) for c, n in enumerate(names))
    cc, walls, ops, _p0, _d, cat = J._wall_rows(rows, 300.0, DOOR)
    wall = R._Wall(0, R._collect_rows(cc, walls)[0], walls, ops, cat, 1.5, ties=[157.0], jamb_alignment=True)
    edges = [(100.0, 1)]
    got = dict((n, wall._face_defects(wall.course_fam[c], edges)) for c, n in enumerate(names))
    assert got == dict((n, FORMS[n][1]) for n in names), got
    # B19 logo atras da faixa encostada e' fechamento ADMISSIVEL (84/85.2)
    f = wall.course_fam[names.index("b19_atras_da_faixa")]
    assert [wall._half_block_admissible(f, i) for i, s in enumerate(wall.fam[f]) if s.code == "B19"] == [True]
    # chave desligada: a regua vale 0
    old = R.JAMB_COMPENSATOR_AT_FACE_ENABLED
    R.JAMB_COMPENSATOR_AT_FACE_ENABLED = False
    try:
        assert all(wall._face_defects(wall.course_fam[c], edges) == 0 for c in range(len(names)))
    finally:
        R.JAMB_COMPENSATOR_AT_FACE_ENABLED = old


def test_compensador_da_grade_nao_conta():
    """Janela: a fileira CHEIA de mesma paridade abaixo do peitoril tem a pastilha no mesmo lugar - a grade
    continua (86.6); sem ela a mesma pastilha e' solta."""
    jamb = [("B39", 100, 139, 0), ("C04", 140, 144, 0), ("B39", 145, 184, 0)]
    full = [("B39", 20, 59, 0), ("B39", 60, 99, 0)] + jamb
    other = [("B39", 0, 39, 0), ("B39", 40, 79, 0), ("B39", 80, 119, 0), ("B39", 120, 159, 0), ("B39", 160, 199, 0)]
    rows = {0: full, 1: other, 2: jamb, 3: [("B39", 100, 139, 0)]}
    cc, walls, ops, _p0, _d, cat = J._wall_rows(rows, 300.0, [(20.0, 100.0)])
    wall = R._Wall(0, R._collect_rows(cc, walls)[0], walls, ops, cat, 1.5, jamb_alignment=True)
    edges = [(100.0, 1)]
    assert wall._face_defects(wall.course_fam[2], edges) == 0
    rows[0] = [("B39", 20, 59, 0), ("B39", 60, 99, 0), ("B39", 100, 139, 0), ("B39", 140, 179, 0)]
    cc, walls, ops, _p0, _d, cat = J._wall_rows(rows, 300.0, [(20.0, 100.0)])
    wall = R._Wall(0, R._collect_rows(cc, walls)[0], walls, ops, cat, 1.5, jamb_alignment=True)
    assert wall._face_defects(wall.course_fam[2], edges) == 1


# ------------------------------------------------------------------ W6: porta 469 com T (B54 385-439)
# estado que CHEGA ao recompositor no calculo (mini-planta 6,9,16,13,30,0 com aberturas, 13 fiadas): as
# pares ja' sao o desenho do usuario, as impares fecham o C09 contra a parede que cruza (405-419); a
# fiada 12 ainda e' de BLOCO (5 x B34 sobre a porta - a cinta de topo, 86.7, vem depois)
W6_EVEN = [("B39", 310, 349, 0), ("B34", 350, 384, 1), ("B54", 385, 439, 0), ("B19", 440, 459, 0),
           ("C09", 460, 469, 0), ("B19", 560, 579, 0), ("B34", 580, 614, -1), ("B54", 615, 669, 0)]
W6_ODD = [("B39", 330, 369, 0), ("B34", 370, 404, -1), ("C09", 420, 429, 0), ("B39", 430, 469, 0),
          ("B34", 560, 594, 1), ("B39", 595, 634, 0), ("B39", 650, 689, 0)]
W6_ROWS = dict([(c, W6_EVEN if c % 2 == 0 else W6_ODD) for c in range(11)] + [
    (11, [("B39", 330, 369, 0), ("B34", 370, 404, -1), ("U34", 420, 454, 0), ("U34", 455, 489, 0),
          ("U34", 490, 524, 0), ("U34", 525, 559, 0), ("U34", 560, 594, 0), ("B39", 595, 634, 0),
          ("B39", 650, 689, 0)]),
    (12, [("B39", 310, 349, 0), ("B34", 350, 384, 1), ("B54", 385, 439, 0), ("B34", 440, 474, -1),
          ("B34", 475, 509, -1), ("B34", 510, 544, -1), ("B34", 545, 579, -1), ("B34", 580, 614, -1),
          ("B54", 615, 669, 0)])])
W6_ARGS = (999.0, [(469.0, 560.0)], [412.0, 642.0])


def _w6(on):
    return _cached(("w6", on), lambda: _run(W6_ROWS, *W6_ARGS, on=on))


def test_w6_red_sem_a_regra_o_recompositor_tira_o_c09_da_face():
    """Causa provada: com o percurso obrigatorio antes da faixa no objetivo, o recompositor TROCAVA o
    desenho do usuario por `B54 | C09 | B19 | vao` (o percurso da jamba so' passava pela fiada 12 de bloco
    com o B19 na face) - exatamente o que o Revit mostrou nas fiadas 0/2/4/6/8/10."""
    res = _w6(False)
    for c in range(0, 11, 2):
        assert _codes(res, c, 385, 469) == [("B54", 385, 439), ("C09", 440, 449), ("B19", 450, 469)], c


def test_w6_green_desenho_do_usuario_e_c09_alinhado_em_todas_as_fiadas():
    res = _w6(True)
    for c in range(0, 11, 2):
        assert _codes(res, c, 385, 469) == [("B54", 385, 439), ("B19", 440, 459), ("C09", 460, 469)], c
    for c in range(1, 11, 2):
        assert _codes(res, c, 420, 469) == [("B39", 420, 459), ("C09", 460, 469)], c
    # a outra jamba da porta e o resto da parede nao mudam
    for c in range(11):
        assert _codes(res, c, 560, 700) == [x[:3] for x in W6_ROWS[c] if x[1] >= 560], c


def _start(rows, args, node_codes=("B54",)):
    """O estado de partida (sem recompor) com a mesma regua."""
    cc, walls, ops, p0, d, cat = _build(rows, args[0], args[1], node_codes=node_codes)
    return {"cc": cc, "walls": walls, "ops": ops, "ties": args[2], "p0": p0, "d": d,
            "cat": dict((k, v) for k, v in cat.items() if not k.startswith("CHANNEL"))}


def test_w6_prisma_nao_piora():
    start = _start(W6_ROWS, W6_ARGS)
    res = _w6(True)
    assert _broken_cells(res) <= _broken_cells(start)
    assert J._prism_misaligned(res["cc"], res["walls"], res["p0"], res["d"], 384.0, 470.0) <= \
        J._prism_misaligned(start["cc"], start["walls"], start["p0"], start["d"], 384.0, 470.0)


# ------------------------------------------------------------------ W0: pilarete de 69 entre janelas
# fileiras lidas de volta do Revit (readback da secao 86), janelas [2054,2175] e [2244,2385] (peitoril 100),
# pilarete 2000-2054 a esquerda; nas fiadas 6/8/10 o C09 ficava 20 cm para dentro, atras do B19
W0_ROWS = {
    0: [("B39", 1990, 2029, 0), ("B39", 2030, 2069, 0), ("B39", 2070, 2109, 0), ("B39", 2110, 2149, 0),
        ("B39", 2150, 2189, 0), ("B39", 2190, 2229, 0), ("B39", 2230, 2269, 0), ("B39", 2270, 2309, 0),
        ("B34", 2310, 2344, 1), ("B34", 2345, 2379, 1), ("B34", 2380, 2414, 1)],
    1: [("B39", 2010, 2049, 0), ("B39", 2050, 2089, 0), ("B39", 2090, 2129, 0), ("B39", 2130, 2169, 0),
        ("B39", 2170, 2209, 0), ("B39", 2210, 2249, 0), ("B39", 2250, 2289, 0), ("B39", 2290, 2329, 0),
        ("B34", 2330, 2364, -1), ("B34", 2365, 2399, -1), ("B34", 2400, 2434, -1)],
    4: [("B19", 2000, 2019, 0), ("U34", 2020, 2054, 0), ("U39", 2055, 2094, 0), ("U39", 2095, 2134, 0),
        ("U39", 2135, 2174, 0), ("U39", 2175, 2214, 0), ("U39", 2215, 2254, 0), ("U39", 2255, 2294, 0),
        ("U39", 2295, 2334, 0), ("U39", 2335, 2374, 0), ("U39", 2375, 2414, 0)],
    5: [("B34", 2000, 2034, 1), ("B19", 2035, 2054, 0), ("B19", 2175, 2194, 0), ("B39", 2195, 2234, 0),
        ("C09", 2235, 2244, 0), ("C09", 2385, 2394, 0), ("B39", 2395, 2434, 0)],
    6: [("B19", 2000, 2019, 0), ("B34", 2020, 2054, -1), ("B39", 2175, 2214, 0), ("C09", 2215, 2224, 0),
        ("B19", 2225, 2244, 0), ("C09", 2385, 2394, 0), ("B19", 2395, 2414, 0)],
    11: [("U39", 2000, 2039, 0), ("U39", 2040, 2079, 0), ("U39", 2080, 2119, 0), ("U39", 2120, 2159, 0),
         ("U39", 2160, 2199, 0), ("U39", 2200, 2239, 0), ("U39", 2240, 2279, 0), ("U39", 2280, 2319, 0),
         ("U34", 2320, 2354, 0), ("U39", 2355, 2394, 0), ("U39", 2395, 2434, 0)],
    12: [("U39", 1990, 2029, 0), ("U39", 2030, 2069, 0), ("U39", 2070, 2109, 0), ("U39", 2110, 2149, 0),
         ("U39", 2150, 2189, 0), ("U39", 2190, 2229, 0), ("U39", 2230, 2269, 0), ("U39", 2270, 2309, 0),
         ("U34", 2310, 2344, 0), ("U34", 2345, 2379, 0), ("U34", 2380, 2414, 0)],
}
W0_ROWS[2] = list(W0_ROWS[0])
W0_ROWS[3] = [("U39", 2010, 2049, 0)] + W0_ROWS[1][1:]
for _c in (7, 9):
    W0_ROWS[_c] = list(W0_ROWS[5])
for _c in (8, 10):
    W0_ROWS[_c] = list(W0_ROWS[6])
W0_ARGS = (2929.0, [(1849.0, 2000.0), (2054.0, 2175.0), (2244.0, 2385.0)], [2442.0])
# 86.6: P = 69 do humano em W0 2175-2244: `B19 B39 C09` / `B39 B19 C09` (C09 na mesma jamba)
W0_ODD_HUMAN = [("B19", 2175, 2194), ("B39", 2195, 2234), ("C09", 2235, 2244)]
W0_EVEN_HUMAN = [("B39", 2175, 2214), ("B19", 2215, 2234), ("C09", 2235, 2244)]


def _w0(on):
    return _cached(("w0", on), lambda: _run(W0_ROWS, *W0_ARGS, node_codes=(), on=on))


def test_w0_red_sem_a_regra_a_forma_certa_nao_chega_ao_estagio_b():
    """Causa provada: a forma do humano (prisma 0, colunas 57 -> 78) era medida no estagio A mas ficava em
    6o - as 3 sementes tinham as duas paridades iguais (junta a prumo entre fiadas da jamba, que a ponte
    nunca conserta) e nenhuma passava no estagio B: lateral inalterada."""
    res = _w0(False)
    for c in range(6, 11, 2):
        assert _codes(res, c, 2174, 2245) == [("B39", 2175, 2214), ("C09", 2215, 2224), ("B19", 2225, 2244)], c


def test_w0_green_pilarete_de_69_como_o_humano():
    res = _w0(True)
    for c in range(5, 11, 2):
        assert _codes(res, c, 2174, 2245) == W0_ODD_HUMAN, c
    for c in range(6, 11, 2):
        assert _codes(res, c, 2174, 2245) == W0_EVEN_HUMAN, c
    assert not [x for x in _conflicts(res) if x["edges_cm"] == [2175.0, 2244.0]
                and "COMPENSATOR_NOT_AT_JAMB_FACE" in x["reasons"]]


def test_w0_prisma_nao_piora():
    start = _start(W0_ROWS, W0_ARGS, node_codes=())
    res = _w0(True)
    assert _broken_cells(res) < _broken_cells(start)
    lo, hi = 2175.0, 2244.0
    assert J._prism_misaligned(res["cc"], res["walls"], res["p0"], res["d"], lo, hi) < \
        J._prism_misaligned(start["cc"], start["walls"], start["p0"], start["d"], lo, hi)


# ------------------------------------------------------------------ W2: porta 1069-1160 com T (B54 1165-1219)
# estado que CHEGA ao recompositor no calculo (mini-planta 2,5,10,14,15,23,0 com aberturas, 13 fiadas):
# pares `vao | C04 | B54(no')`, impares `vao | B19 | C04 | parede que cruza (1185-1199)` - a pastilha alterna
W2_EVEN = [("C04", 1160, 1164), ("B54", 1165, 1219), ("B39", 1220, 1259), ("B39", 1260, 1299), ("B39", 1300, 1339)]
W2_ODD = [("B19", 1160, 1179), ("C04", 1180, 1184), ("B39", 1200, 1239), ("B39", 1240, 1279), ("B39", 1280, 1319),
          ("B39", 1320, 1359)]
W2_ROWS = dict([(c, W2_EVEN if c % 2 == 0 else W2_ODD) for c in range(11)] + [
    (11, [("U39", 1135, 1174), ("UCUT", 1175, 1184), ("B39", 1200, 1239), ("B39", 1240, 1279), ("B39", 1280, 1319),
          ("B39", 1320, 1359)]),
    (12, [("B39", 1125, 1164), ("B54", 1165, 1219), ("B39", 1220, 1259), ("B39", 1260, 1299), ("B39", 1300, 1339)])])
W2_ARGS = (1629.0, [(1069.0, 1160.0)], [1192.0])


def _w2(on):
    return _cached(("w2", on), lambda: _run(W2_ROWS, *W2_ARGS, on=on))


def test_w2_sem_solucao_que_preserve_o_prisma_fica_e_e_registrado():
    """`vao | C04 | B19 | encontro` nas impares (o C04 na face nas 11 fiadas) poe a coluna do B19 (e a do
    vazado do B54 de baixo) sobre a junta entre as canaletas da verga (U39 1135-1174 | U 1175-1184, junta em
    1174,5): 10 celulas quebradas e o percurso obrigatorio da jamba perdido. O prisma prevalece (pedido do
    usuario): a lateral fica e sai registrada com o motivo."""
    res = _w2(True)
    for c in range(11):
        assert _codes(res, c, 1160, 1359) == [x[:3] for x in W2_ROWS[c] if x[1] >= 1160], c
    regs = [x for x in _conflicts(res) if "COMPENSATOR_NOT_AT_JAMB_FACE" in x["reasons"]]
    assert regs and all(x["edges_cm"] == [1160.0] for x in regs), _conflicts(res)
    assert any(x["courses"] == [1, 3, 5, 7, 9] and "PRISM_COLUMN_WOULD_BREAK" in x["reasons"] for x in regs), regs
    assert _broken_cells(res) == _broken_cells(_start(W2_ROWS, W2_ARGS))
    # a causa: com o C04 na face a coluna do B19 cai na junta das canaletas da verga
    face = dict(W2_ROWS)
    for c in range(1, 11, 2):
        face[c] = [("C04", 1160, 1164), ("B19", 1165, 1184)] + W2_ODD[2:]
    for rows, ok in ((W2_ROWS, True), (face, False)):
        cc, walls, ops, _p0, _d, cat = _build(rows, *W2_ARGS[:2])
        wall = R._Wall(0, R._collect_rows(cc, walls)[0], walls, ops, cat, 1.5, ties=W2_ARGS[2], jamb_alignment=True)
        b19 = [s for s in wall.fam[wall.course_fam[1]] if s.code == "B19"][0]
        assert wall._trace_column(1, wall._cell_intervals(b19)[0])[0] is ok, rows[1]


# ------------------------------------------------------------------ pilarete de 64 do print do usuario
# duas janelas, pilarete 250-314: `B19 | C04 | B39` (pares) / `C04 | B39 | B19` (impares) - o C04 ora na
# face, ora atras do B19. Fileiras cheias com a grade de 40 (pares a partir de 35, impares de 15): sobra
# 24 / 0 nas pares e 4 / 19 nas impares - o catalogo da 86.6 e' `C04 B19 B39` / `C04 B39 B19`
def _grid(start, lo, hi, channel=False):
    out = []
    if start > lo:
        out.append(("U19" if channel else "B19", start - 20, start - 1, 0))
    t = start
    while t + 39 <= hi:
        out.append(("U39" if channel else "B39", t, t + 39, 0))
        t += 40
    if t + 19 <= hi:
        out.append(("U19" if channel else "B19", t, t + 19, 0))
    return out


P64_EVEN_FULL = _grid(35, 15, 634)
P64_ODD_FULL = _grid(15, 15, 634)
P64_WINDOWS = [(95.0, 250.0), (314.0, 475.0)]


def _p64_rows(even_pil, odd_pil):
    # jambas de fora: pares `B19 | vao` (sobra 19) e `vao | B39` (sobra 0); impares o contrario
    even_jamb = ([("B19", 15, 34, 0), ("B39", 35, 74, 0), ("B19", 75, 94, 0)] + list(even_pil)
                 + [p for p in P64_EVEN_FULL if p[1] >= 474.5])
    odd_jamb = ([p for p in P64_ODD_FULL if p[2] <= 94.5] + list(odd_pil) + [("B19", 475, 494, 0)]
                + [p for p in P64_ODD_FULL if p[1] >= 494.5])
    rows = {}
    for c in range(4):
        rows[c] = list(P64_EVEN_FULL if c % 2 == 0 else P64_ODD_FULL)
    rows[4] = _grid(35, 15, 634, channel=True)  # contraverga
    for c in range(5, 11):
        rows[c] = list(even_jamb if c % 2 == 0 else odd_jamb)
    rows[11] = _grid(15, 15, 634, channel=True)  # verga
    rows[12] = list(P64_EVEN_FULL)  # ultima fiada (ainda de bloco no recompositor)
    return rows


P64_EVEN_PRINT = [("B19", 250, 269, 0), ("C04", 270, 274, 0), ("B39", 275, 314, 0)]
P64_ODD_PRINT = [("C04", 250, 254, 0), ("B39", 255, 294, 0), ("B19", 295, 314, 0)]


def _p64(on):
    return _cached(("p64", on), lambda: _run(_p64_rows(P64_EVEN_PRINT, P64_ODD_PRINT), 640.0, P64_WINDOWS, [],
                                             node_codes=(), on=on))


def test_pilarete_do_print_c04_na_mesma_face_em_todas_as_fiadas():
    """Com a grade de baixo coerente o catalogo da 86.6 ja' levava a esta forma (a chave desligada tambem
    chega nela); o teste trava que a regua nova nao a desfaz: C04 encostado na mesma jamba nas 6 fiadas e o
    B19 atras dele (pares) ou na outra jamba (impares)."""
    res = _p64(True)
    for c in range(5, 11):
        row = _codes(res, c, 249, 315)
        assert row[0] == ("C04", 250, 254), (c, row)  # mesma faixa, encostada no vao
        assert sum(1 for x in row if x[0] in ("C04", "C09")) == 1, (c, row)
    for c in range(6, 11, 2):
        assert _codes(res, c, 249, 315) == [("C04", 250, 254), ("B19", 255, 274), ("B39", 275, 314)], c
    for c in range(5, 11, 2):
        assert _codes(res, c, 249, 315) == [("C04", 250, 254), ("B39", 255, 294), ("B19", 295, 314)], c


# ------------------------------------------------------------------ sem solucao: registra e mantem o prisma
W27_ROWS = {
    0: [("B34", 0, 34, -1), ("B39", 36, 74, 0), ("C04", 76, 80, 0), ("B34", 81, 115, 1)],
    1: [("U39", 16, 54, 0), ("U39", 56, 94, 0)],
    2: [("C09", 0, 9, 0), ("C09", 10, 20, 0), ("B19", 86, 105, 0), ("C09", 106, 115, 0)],
    3: [("C04", 16, 20, 0), ("C09", 86, 95, 0), ("C04", 96, 100, 0)],
    12: [("B34", 0, 34, -1), ("U39", 36, 74, 0), ("B34", 81, 115, 1)],
}
W27_ROWS[4] = list(W27_ROWS[2])
for _c in range(5, 12):
    W27_ROWS[_c] = (list(W27_ROWS[0]) if _c % 2 == 0 else
                    [("B39", 16, 54, 0), ("B39", 56, 94, 0), ("C04", 96, 100, 0)])


def test_shaft_w27_sem_solucao_fica_e_e_registrado():
    """W27 (115 cm, janela 19,5-85,5): o C09 na face poe o B19 junto da amarracao do canto
    (HALF_BLOCK_NEAR_TIE, regra #2) - nada muda e a lateral sai registrada."""
    args = (115.0, [(19.51, 85.51)], [7.0, 108.0])
    res = _run(W27_ROWS, *args, node_codes=("B34",))
    start = _start(W27_ROWS, args, node_codes=("B34",))
    for c in sorted(W27_ROWS):
        assert _codes(res, c, -1, 116) == _codes(start, c, -1, 116), c
    assert _broken_cells(res) == _broken_cells(start)
    regs = [x for x in _conflicts(res) if "COMPENSATOR_NOT_AT_JAMB_FACE" in x["reasons"]]
    assert regs and all(x["edges_cm"] == [85.5] for x in regs), _conflicts(res)
    assert any(x["courses"] == [2, 4] for x in regs), regs


# ------------------------------------------------------------------ chave desligada, determinismo
def test_chave_desligada_volta_ao_comportamento_anterior():
    """Desligada: nenhuma regua nova, o ranking do estagio A como antes - W0 inalterada, W6 com o C09 tirado
    da face e W2 com a pastilha atras do B19 (os testes `red` acima), sem registro novo."""
    for res in (_w0(False), _w6(False), _w2(False)):
        assert not [x for x in _conflicts(res) if "COMPENSATOR_NOT_AT_JAMB_FACE" in x["reasons"]]
        assert all("face_defects_before" not in (x.get("detail") or {}) for x in _conflicts(res))


def test_deterministico_e_idempotente():
    first = _w0(True)
    again = _run(W0_ROWS, *W0_ARGS, node_codes=(), on=True)
    snap = dict((c, _codes(first, c, 1990, 2440)) for c in first["cc"])
    assert dict((c, _codes(again, c, 1990, 2440)) for c in again["cc"]) == snap
    # rodar de novo sobre o resultado nao muda nada nessa lateral
    rows = dict((c, [(code, lo, hi, side) for code, lo, hi, side in
                     J._sided_row(first["cc"], c, first["p0"], first["d"], 1990, 2440)]) for c in first["cc"])
    second = _run(rows, *W0_ARGS, node_codes=(), on=True)
    for c in range(5, 11):
        assert _codes(second, c, 2174, 2245) == _codes(first, c, 2174, 2245), c
