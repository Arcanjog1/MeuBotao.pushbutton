# -*- coding: utf-8 -*-
"""SECOES 86.6 e 86.10 de REGRAS_MODULACAO_BLOCOS.md - aproximacao do projeto
HUMANO BUTANTA R08_LT (1o pavimento, medicao somente-leitura de 2026-10-01).

86.6 (R6) - JAMBA FECHADA PELA SOBRA DA GRADE. Na janela a zona da jamba
continua a grade da fiada CHEIA de mesma paridade abaixo do peitoril; o pedaco
da peca da grade que a face da jamba corta (a SOBRA) fecha sempre com as mesmas
pecas, contadas a partir da face (compensador encostado no vao, B19 atras):

    0 nada (a peca da grade continua) | 4 C04 | 9 C09 | 14 C09+C04 (C09 na face)
    19 B19 | 24 C04+B19 | 29 C09+B19 | 34 B34

Humano 244/254 fiadas x jamba (96 %), o motor 103/126. PROIBIDO (REGRA
OBRIGATORIA da 85.8, falha dura `B34_PLUS_COMPENSATOR_WHERE_B39_FITS`):
compensador isolado colado num B34 onde o compensador menor + B39 fecha
(C09|B34 = C04|B39; C04|B34 = B39) - humano 0 casos, o motor 22. Pilarete de 54
entre janelas (W0 800-854 do humano): `B39 C04 C09` / `B19 B34` com o vazado
menor do B34 sobre a faixa (forma A, chave JAMB_HUMAN_A_FORM_ENABLED).
Orientacao do B34 encostado na jamba (humano 95/95, motor 37/37): vazado menor
para o vao quando a fiada vizinha tem faixa de compensador na jamba, para longe
quando ela tem B19.

86.10 (R10) - o humano poe 129/129 C09 da jamba com o +X local apontando para
LONGE do vao (o motor punha ao contrario); a pastilha C04 e' simetrica.

    py -3 -m pytest tests/test_jamb_remnant_catalog.py -q
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import test_jamb_compensator_alignment as J  # noqa: E402  (fixtures com as celulas REAIS)

m = J.m
R = J.R
ft, seg = J.ft, J.seg
LEN = {"B39": 39, "B34": 34, "B19": 19, "C09": 9, "C04": 4}


def _lay(seq, t0):
    """[(codigo, lo, hi, lado)] a partir de t0 com juntas de 1 cm; item = codigo ou (codigo, lado)."""
    out, t = [], t0
    for item in seq:
        code, side = item if isinstance(item, tuple) else (item, 0)
        out.append((code, t, t + LEN[code], side))
        t += LEN[code] + 1
    return out


def _from(row, t0):
    return [(code, a, b, s) for code, a, b, s in row if a >= t0 - 0.5]


# ------------------------------------------------------------------ o catalogo
def test_catalogo_da_sobra_e_o_do_humano():
    assert R.JAMB_REMNANT_CATALOG == {0: (), 4: ("C04",), 9: ("C09",), 14: ("C09", "C04"), 19: ("B19",),
                                      24: ("C04", "B19"), 29: ("C09", "B19"), 34: ("B34",)}
    for key, codes in R.JAMB_REMNANT_CATALOG.items():
        if codes:  # comprimento das pecas + juntas = sobra
            assert sum(LEN[c] for c in codes) + len(codes) - 1 == key
    assert R.JAMB_REMNANT_CATALOG_ENABLED and R.JAMB_B34_COMPENSATOR_GUARD_ENABLED
    assert R.JAMB_CATALOG_CANDIDATES_ENABLED and R.JAMB_HUMAN_A_FORM_ENABLED


@pytest.mark.parametrize("remnant", [0, 4, 9, 14, 19, 24, 29, 34])
def test_sobra_medida_na_fileira_cheia_de_referencia(remnant):
    """A sobra e' o pedaco da peca da grade do lado da alvenaria, nos dois sentidos."""
    ref = []
    for lo in range(0, 400, 40):
        s = R._Slot()
        s.lo, s.hi, s.code = float(lo), float(lo + 39), "B39"
        ref.append(s)
    # pecas ANTES da face (jamba esquerda do vao): face = inicio da peca + sobra
    edge = 200.0 + remnant if remnant else 199.0
    assert R._Wall._jamb_remnant(ref, edge, -1) == (remnant, "B39")
    # pecas DEPOIS da face (jamba direita do vao): face = fim da peca - sobra
    edge = 239.0 - remnant if remnant else 240.0
    assert R._Wall._jamb_remnant(ref, edge, 1) == (remnant, "B39")
    # fora do modulo de 5 cm: nada a exigir
    assert R._Wall._jamb_remnant(ref, 211.5, -1) is None


# ------------------------------------------------------------------ janela: as 8 sobras
WINDOW_HI = 325.0  # jamba direita fixa (sobras 34 / 14 ja' no catalogo)
# fiada cheia de referencia: pares B39 a partir de 0, impares B19 + B39 a partir de 20 (20 cm de
# amarracao). Jamba esquerda em A = 200 + r -> sobra r nas pares e r + 20 (ou 0) nas impares
WRONG = {4: (["B34", "C09"], ["B39", "C04", "B19"]),      # C09|B34 onde C04|B39 fecha; C04 atras do B19
         9: (["C09", "B39"], ["B39", "C09", "B19"]),      # C09 fora da jamba; C09 atras do B19
         14: (["C09", "B39", "C04"], ["B34", "B39"]),     # faixa partida; B34 longe da jamba
         19: (["B19", "B39"], ["B39", "B34", "C04"])}     # B19 no miolo; C04|B34 onde B39 fecha
EXPECTED = {4: (["B39", "C04"], ["B39", "B19", "C04"]),
            9: (["B39", "C09"], ["B39", "B19", "C09"]),
            14: (["B39", "C04", "C09"], ["B39", ("B34", 1)]),
            19: (["B39", "B19"], ["B39", "B39"])}


def _grid(parity, length):
    if parity == 0:
        return [("B39", t, t + 39, 0) for t in range(0, int(length), 40) if t + 39 <= length]
    return [("B19", 0, 19, 0)] + [("B39", t, t + 39, 0) for t in range(20, int(length), 40) if t + 39 <= length]


def _cut_right(row, b):
    """fileira cortada pelo vao que termina em `b`, com o fechamento do catalogo nessa face."""
    out = []
    for code, lo, hi, s in row:
        if hi <= b + 0.5:
            continue
        if lo < b - 0.5:
            out.extend(_lay(R.JAMB_REMNANT_CATALOG[int(round(hi - b))], b))
            continue
        out.append((code, lo, hi, s))
    return out


def _window_rows(r, wrong=True):
    a = 200.0 + r
    rows = {}
    for c in range(4):
        rows[c] = _grid(c % 2, 600.0)
    for c in range(4, 8):
        zone = 160.0 if c % 2 == 0 else 140.0
        left = [x for x in _grid(c % 2, 600.0) if x[2] <= zone - 0.5]
        seq = (WRONG if wrong else EXPECTED)[r][c % 2]
        rows[c] = left + _lay(seq, zone) + _cut_right(_grid(c % 2, 600.0), WINDOW_HI)
        assert rows[c][len(left) + len(seq) - 1][2] == a  # a corrida errada fecha na face
    return rows, a


_CACHE = {}  # cenario -> resultado (os testes so' leem; poupa ~30 s de recalculo)


def _window(r):
    if ("window", r) not in _CACHE:
        rows, a = _window_rows(r)
        cc, walls, openings, p0, d, cat = J._wall_rows(rows, 600.0, [(a, WINDOW_HI)])
        summary = J._arrange_real(cc, walls, openings, cat, [])
        _CACHE[("window", r)] = (cc, p0, d, a, summary)
    return _CACHE[("window", r)]


@pytest.mark.parametrize("r", [4, 9, 14, 19])
def test_jamba_de_janela_fecha_pela_sobra_da_grade(r):
    """r nas pares e r + 20 nas impares (19 -> 0): as oito sobras do catalogo. O fechamento sai da
    fiada cheia de baixo, a partir da face (compensador encostado no vao), a grade continua atras."""
    cc, p0, d, a, summary = _window(r)
    assert summary["jamb_sides_changed"] >= 1
    even_want, odd_want = EXPECTED[r]
    for c in range(4, 8):
        zone = 160.0 if c % 2 == 0 else 140.0
        got = _from(J._sided_row(cc, c, p0, d, zone, a), zone)
        want = _lay(even_want if c % 2 == 0 else odd_want, zone)
        if any(code == "B34" for code, _a, _b, _s in want):
            assert got == want, (c, got)  # o lado do B34 tambem (vazado menor sobre a faixa)
        else:
            assert [x[:3] for x in got] == [x[:3] for x in want], (c, got)
        assert got[-1][2] == a  # encostado na face
    # as fiadas cheias (a referencia e as fiadas-ponte logo abaixo do peitoril) nao mudam
    for c in range(4):
        assert [x[:3] for x in J._sided_row(cc, c, p0, d, 100, 330)] == \
            [x[:3] for x in _grid(c % 2, 600.0) if x[2] >= 99.5 and x[1] <= 330.5]


def test_jamba_pela_sobra_e_deterministica():
    rows, a = _window_rows(19)
    cc, walls, openings, p0, d, cat = J._wall_rows(rows, 600.0, [(a, WINDOW_HI)])
    J._arrange_real(cc, walls, openings, cat, [])
    cc2, p02, d2, _a, _s = _window(19)
    fresh = dict((c, J._sided_row(cc, c, p0, d, 0, 600)) for c in cc)
    assert fresh == dict((c, J._sided_row(cc2, c, p02, d2, 0, 600)) for c in cc2)


def test_janela_ja_no_catalogo_nao_muda():
    rows, a = _window_rows(14, wrong=False)
    cc, walls, openings, p0, d, cat = J._wall_rows(rows, 600.0, [(a, WINDOW_HI)])
    before = dict((c, J._sided_row(cc, c, p0, d, 0, 600)) for c in cc)
    J._arrange_real(cc, walls, openings, cat, [])
    assert dict((c, J._sided_row(cc, c, p0, d, 0, 600)) for c in cc) == before


# ------------------------------------------------------------------ proibicao C09|B34
def _wall_of(rows, length, openings):
    cc, walls, ops, _p0, _d, cat = J._wall_rows(rows, length, openings)
    return R._Wall(0, R._collect_rows(cc, walls)[0], walls, ops, cat, 1.5, jamb_alignment=True)


def test_compensador_isolado_mais_b34_onde_b39_fecha_e_contado():
    rows = {0: [("B39", 0, 39, 0), ("B34", 40, 74, 0), ("C09", 75, 84, 0)],      # C09|B34 = C04|B39
            1: [("B39", 0, 39, 0), ("B34", 40, 74, 0), ("C04", 75, 79, 0)],      # C04|B34 = B39
            2: [("B19", 0, 19, 0), ("B34", 20, 54, 0), ("C04", 55, 59, 0), ("C09", 60, 69, 0)],  # par C04+C09
            3: [("B39", 0, 39, 0), ("C04", 40, 44, 0), ("B39", 45, 84, 0)]}      # C04|B39: certo
    wall = _wall_of(rows, 200.0, [])
    count = dict((c, wall._b34_comp_where_b39_fits(wall.course_fam[c], None)) for c in rows)
    assert count == {0: 1, 1: 1, 2: 0, 3: 0}, count


def test_falha_dura_quando_a_troca_cria_compensador_mais_b34():
    base = {"sv": 0, "comps": 1, "offjamb": 0, "paths": 1, "colbroken": 0, "column": 4, "prism": 0, "b19": 0,
            "cp": 0, "ht": 0, "ex": 0, "joints": set(), "stacks": 0, "strips": 0, "b34c": 0}
    worse = dict(base, b34c=1)
    assert "B34_PLUS_COMPENSATOR_WHERE_B39_FITS" in R._Wall._jamb_failures(worse, base)
    assert "B34_PLUS_COMPENSATOR_WHERE_B39_FITS" not in R._Wall._jamb_failures(base, worse)
    assert "B34_PLUS_COMPENSATOR_WHERE_B39_FITS" in R.JAMB_INTRINSIC_FAILURES


def test_c09_b34_na_jamba_vira_c04_b39():
    """Sobra 4: `B34 | C09 | vao` (C09 encostado, B34 atras) -> `B39 | C04 | vao`, a grade de baixo."""
    cc, p0, d, a, _summary = _window(4)
    for c in range(4, 8, 2):
        codes = [x[0] for x in J._sided_row(cc, c, p0, d, 150, a)]
        assert codes[-2:] == ["B39", "C04"], (c, codes)
    rows = R._collect_rows(cc, [(seg(0, 0, 600, 0), ft(14.0), (False, False))])
    assert rows  # a parede continua com pecas
    wall = R._Wall(0, rows[0], [(seg(0, 0, 600, 0), ft(14.0), (False, False))],
                   [[(ft(a), ft(WINDOW_HI), 0.0, ft(221.0))]], J.REAL, 1.5, jamb_alignment=True)
    assert sum(wall._b34_comp_where_b39_fits(f, None) for f in wall.fam) == 0


# ------------------------------------------------------------------ pilarete de 54
def _pilaster(rows_jamb_even, rows_jamb_odd, ref_even, ref_odd, openings, length):
    rows = {}
    for c in range(4):
        rows[c] = list(ref_even if c % 2 == 0 else ref_odd)
    for c in range(4, 10):
        # pecas longe do pilarete so' para as fiadas pares e impares serem familias diferentes,
        # como na parede inteira
        far = [("B39", 20, 59, 0)] if c % 2 == 0 else [("B39", 0, 39, 0)]
        rows[c] = far + list(rows_jamb_even if c % 2 == 0 else rows_jamb_odd)
    cc, walls, ops, p0, d, cat = J._wall_rows(rows, length, openings)
    return cc, walls, ops, p0, d, cat


# W0 800-854 do humano (janelas [649,800] e [854,975]), deslocado para t = 200: grade B39 nas fiadas
# cheias (pares a partir de 0, impares a partir de 20) - a jamba esquerda cai na junta das pares
# (sobra 0) e corta 19 cm das impares; a direita corta 14 cm das pares e 34 das impares.
P54_REF_EVEN = [("B39", t, t + 39, 0) for t in range(0, 480, 40)]
P54_REF_ODD = [("B39", t, t + 39, 0) for t in range(20, 480, 40)]
P54_START = [("C09", 200, 209, 0), ("B39", 210, 249, 0), ("C04", 250, 254, 0)]  # 85.6: igual nas duas


def _p54(form_a=True):
    if ("p54", form_a) not in _CACHE:
        _CACHE[("p54", form_a)] = _p54_run(form_a)
    return _CACHE[("p54", form_a)]


def _p54_run(form_a):
    old = R.JAMB_HUMAN_A_FORM_ENABLED
    R.JAMB_HUMAN_A_FORM_ENABLED = form_a
    try:
        cc, walls, ops, p0, d, cat = _pilaster(P54_START, P54_START, P54_REF_EVEN, P54_REF_ODD,
                                               [(100.0, 200.0), (254.0, 354.0)], 500.0)
        J._arrange_real(cc, walls, ops, cat, [])
    finally:
        R.JAMB_HUMAN_A_FORM_ENABLED = old
    return cc, p0, d


def test_pilarete_de_54_como_o_humano():
    """85.6 resolvida pelo catalogo: `B39 | C04 | C09` nas pares e `B19 | B34` nas impares, o B34 com o
    vazado menor voltado para a jamba da faixa (sobre o C09/C04) - W0 800-854 do humano."""
    cc, p0, d = _p54()
    for c in range(4, 10, 2):
        assert J._sided_row(cc, c, p0, d, 200, 254) == [("B39", 200, 239, 0), ("C04", 240, 244, 0),
                                                         ("C09", 245, 254, 0)], c
    for c in range(5, 10, 2):
        assert J._sided_row(cc, c, p0, d, 200, 254) == [("B19", 200, 219, 0), ("B34", 220, 254, 1)], c


def test_pilarete_de_54_idempotente_e_deterministico():
    cc, walls, ops, p0, d, cat = _pilaster(P54_START, P54_START, P54_REF_EVEN, P54_REF_ODD,
                                           [(100.0, 200.0), (254.0, 354.0)], 500.0)
    assert J._arrange_real(cc, walls, ops, cat, [])["jamb_sides_changed"] == 1
    snap = dict((c, J._sided_row(cc, c, p0, d, 0, 500)) for c in cc)
    assert J._arrange_real(cc, walls, ops, cat, [])["jamb_sides_changed"] == 0
    assert dict((c, J._sided_row(cc, c, p0, d, 0, 500)) for c in cc) == snap
    cc2, p02, d2 = _p54()
    assert dict((c, J._sided_row(cc2, c, p02, d2, 0, 500)) for c in cc2) == snap


def test_pilarete_de_54_sem_a_forma_a_nao_usa_o_par_c04_c09():
    """A chave JAMB_HUMAN_A_FORM_ENABLED (CONFLITO com 84 item 3 / 85.8) e' o que libera a forma A: sem
    ela o par C04+C09 encostado (compensadores encostados) e o vazado menor do B34 sobre a faixa
    continuam falhas duras e o pilarete sai por outro fechamento (medido: `B34 B19` / `B19 B34`, com as
    fiadas-ponte de baixo viradas grade de B34)."""
    cc, p0, d = _p54(form_a=False)
    for c in range(4, 10):
        codes = [x[0] for x in J._sided_row(cc, c, p0, d, 200, 254)]
        assert codes != ["B39", "C04", "C09"] and "C04" not in codes, (c, codes)


# W0 2000-2054 do humano: grade de B34 nas fiadas cheias - pares `B19 | B34<`, impares `B34> | B19`
# (nenhuma pastilha; o B19 alterna de jamba).
P54B_REF_EVEN = ([("B39", t, t + 39, 0) for t in (70, 110)] + [("B34", 150, 184, -1), ("B34", 185, 219, -1),
                                                                ("B34", 220, 254, -1)]
                 + [("B39", t, t + 39, 0) for t in range(255, 420, 40)])
P54B_REF_ODD = ([("B39", t, t + 39, 0) for t in (80, 120, 160)] + [("B34", 200, 234, 1)]
                + [("B39", t, t + 39, 0) for t in range(235, 420, 40)])


def _p54b():
    if "p54b" not in _CACHE:
        cc, walls, ops, p0, d, cat = _pilaster(P54_START, P54_START, P54B_REF_EVEN, P54B_REF_ODD,
                                               [(100.0, 200.0), (254.0, 354.0)], 500.0)
        J._arrange_real(cc, walls, ops, cat, [])
        _CACHE["p54b"] = (cc, p0, d)
    return _CACHE["p54b"]


def test_pilarete_de_54_com_grade_de_b34_como_o_humano():
    cc, p0, d = _p54b()
    for c in range(4, 10, 2):
        assert J._sided_row(cc, c, p0, d, 200, 254) == [("B19", 200, 219, 0), ("B34", 220, 254, -1)], c
    for c in range(5, 10, 2):
        assert J._sided_row(cc, c, p0, d, 200, 254) == [("B34", 200, 234, 1), ("B19", 235, 254, 0)], c


# ------------------------------------------------------------------ orientacao do B34 na jamba
def _b34_at_jamb_ok(cc, p0, d, courses, faces):
    """Invariante (humano 95/95): B34 encostado na face da jamba tem o vazado menor voltado para o vao
    quando a fiada vizinha tem compensador encostado na mesma face, e para longe quando tem B19."""
    checked = 0
    for c in courses:
        row = J._sided_row(cc, c, p0, d, -1, 10000)
        for code, a, b, side in row:
            if code != "B34":
                continue
            for face, toward in faces:  # toward = +1: o vao fica em t crescente
                if abs((b if toward > 0 else a) - face) > 1:
                    continue
                for nb in (c - 1, c + 1):
                    if nb not in cc:
                        continue
                    first = [x for x in J._sided_row(cc, nb, p0, d, -1, 10000)
                             if abs((x[2] if toward > 0 else x[1]) - face) <= 1]
                    if not first:
                        continue
                    if first[0][0] in ("C04", "C09"):
                        assert side == toward, (c, code, a, b, side, first)
                        checked += 1
                    elif first[0][0] == "B19":
                        assert side == -toward, (c, code, a, b, side, first)
                        checked += 1
    return checked


def test_orientacao_do_b34_encostado_na_jamba_e_invariante():
    cc, p0, d = _p54()
    assert _b34_at_jamb_ok(cc, p0, d, range(4, 10), [(200.0, -1), (254.0, 1)]) >= 3
    cc, p0, d = _p54b()
    assert _b34_at_jamb_ok(cc, p0, d, range(4, 10), [(200.0, -1), (254.0, 1)]) >= 6
    cc, p0, d, a, _summary = _window(14)
    assert _b34_at_jamb_ok(cc, p0, d, range(4, 8), [(a, 1)]) >= 2


# ------------------------------------------------------------------ 86.10: orientacao do C09
def _comp(center_cm, length_cm, code, x_dir=(1.0, 0.0, 0.0)):
    return {"wall_idx": 0, "origin_world": m.XYZ(ft(center_cm), 0.0, 0.0), "x_dir": m.XYZ(*x_dir),
            "y_dir": m.XYZ(0.0, 1.0, 0.0), "length_cm": length_cm, "width_cm": 14.0, "course": "A",
            "logical_code": code}


def test_c09_na_jamba_com_o_mais_x_para_longe_do_vao_como_o_humano():
    """86.10: o +X local FINAL (x_dir, invertido pelo espelhamento de plano normal = x_dir) aponta para
    LONGE do vao nas duas jambas e com x_dir nos dois sentidos (humano 129/129)."""
    assert m.COMPENSATOR_ORIENTATION_FROM_HUMAN_R08 is True
    assert m.COMPENSATOR_CLOSED_SIDE_IS_PLUS_X_WHEN_UNMIRRORED is False
    walls = [(seg(0, 0, 400, 0), ft(14.0), (False, False))]
    openings = [[(ft(100.0), ft(150.0), 0.0, ft(210.0))]]
    catalog = {"C09": {"is_compensator": True, "length_cm": 9.0}, "C04": {"is_compensator": True, "length_cm": 4.0}}
    cases = []
    for center, to_opening in ((95.5, 1.0), (154.5, -1.0)):  # C09 [91,100] e [150,159]
        for xd in (1.0, -1.0):
            cases.append((_comp(center, 9.0, "C09", x_dir=(xd, 0.0, 0.0)), to_opening, xd))
    m.orient_compensator_candidates([c for c, _t, _x in cases], walls, openings, catalog)
    for cand, to_opening, xd in cases:
        final_x = -xd if cand["mirrored"] else xd
        assert final_x * to_opening < 0, (cand["origin_world"].X, xd, cand["mirrored"])


def test_pastilha_c04_e_simetrica_e_nao_e_espelhada():
    walls = [(seg(0, 0, 400, 0), ft(14.0), (False, False))]
    openings = [[(ft(100.0), ft(150.0), 0.0, ft(210.0))]]
    p0, _p1, wall_dir, _len, _t = m._wall_axis_and_length(walls, 0)
    catalog = {"C04": {"is_compensator": True, "length_cm": 4.0}}
    pieces = [_comp(98.0, 4.0, "C04"), _comp(152.0, 4.0, "C04"), _comp(98.0, 4.0, "C04", x_dir=(-1.0, 0.0, 0.0))]
    for p in pieces:
        p["mirrored"] = True  # valor antigo: tem de ser recalculado
        assert m._compensator_required_mirror(p, [(100.0, 150.0)], p0, wall_dir) is None
    m.orient_compensator_candidates(pieces, walls, openings, catalog)
    assert all(p["mirrored"] is False for p in pieces)
