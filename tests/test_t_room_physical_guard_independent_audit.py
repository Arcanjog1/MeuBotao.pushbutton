# -*- coding: utf-8 -*-
"""AUDITORIA ADVERSARIAL INDEPENDENTE da guarda de ESPACO FISICO do no' T.

Objetivo declarado: tentar REFUTAR a tese de que o motor so' forca a
amarracao especial (B54 na principal + B34 na boneca) quando o espaco
fisico existe de verdade, e de que as tolerancias envolvidas sao ruido de
calculo, nunca licenca para invadir vao.

Independencia: as constantes fisicas (B54 = 54cm, portanto 27cm para cada
lado do no'; B34 = 34cm; tolerancia fisica = 0,05cm) sao REDIGITADAS aqui
a partir da fisica do bloco. Nenhum numero e' lido do motor para depois
ser comparado consigo mesmo - se o motor mudar uma constante, estes testes
quebram, que e' exatamente o que se quer de uma auditoria.

A geometria e' montada em COORDENADAS DE MUNDO e so' depois convertida
para o parametro `t` de cada parede (medido desde `p0`, em pes - ver
`_t_of_point_on_wall`). E' isso que torna a inversao de pontas um teste de
verdade: o obstaculo fisico continua no mesmo lugar do mundo e muda so' a
parametrizacao da parede.

Ver docs/AUDITORIA_INDEPENDENTE_GUARDA_ESPACO_T.md para o relatorio e o
veredito. Ferramenta equivalente, rodavel fora do pytest:
tests/audit_t_room_physical_guard.py.
"""

import itertools
import math
import random

import load_script
import revit_stubs

XYZ = revit_stubs.XYZ
Line = revit_stubs.Line
m = load_script.load()
F = m.FEET_PER_METER

from core.engine import modulation_math as mm  # noqa: E402
from core.engine import tolerances as tol  # noqa: E402
from core.engine import wall_stepper as ws  # noqa: E402

# ------------------------------------------------- a fisica, redigitada
B54_CM = 54.0
B34_CM = 34.0
B54_HALF_ROOM_CM = B54_CM / 2.0      # 27cm para CADA lado do no'
PHYSICAL_TOL_CM = 0.05               # ruido de calculo aceito na jamba
WALL_THICKNESS_CM = 14.0
DOOR_CM = 15.0


def ft(cm):
    return cm / 100.0 * F


def to_cm(value_ft):
    return value_ft / F * 100.0


def seg(x0, y0, x1, y1):
    return Line.CreateBound(XYZ(ft(x0), ft(y0), 0.0), XYZ(ft(x1), ft(y1), 0.0))


# ------------------------------------------------------------- cenarios
def t_scene(gap_right_cm=200.0, gap_left_cm=200.0, inc_cm=200.0,
            node_x=200.0, main_len=1000.0, theta=0.0, ox=0.0, oy=0.0,
            flip_main=False, flip_inc=False, order=(0, 1)):
    """UM no' T isolado com os TRES espacos fisicos controlados um a um.

    `gap_right_cm`/`gap_left_cm`: vao livre em MUNDO a partir do no', para
    +X e -X do eixo local (antes do giro); `inc_cm`: comprimento da boneca.
    `theta`/`ox`/`oy` giram e transladam a cena inteira; `flip_*` inverte as
    pontas dos segmentos; `order` permuta os indices das duas paredes.
    """
    c, s = math.cos(theta), math.sin(theta)

    def R(x, y):
        return (ox + x * c - y * s, oy + x * s + y * c)

    x0, x1, xn = 0.0, main_len, node_x

    # Obstaculos fisicos (portas), em coordenada de MUNDO local (pre-giro).
    world_spans = []
    if xn + gap_right_cm + DOOR_CM <= x1:
        world_spans.append((xn + gap_right_cm, xn + gap_right_cm + DOOR_CM))
    if xn - gap_left_cm - DOOR_CM >= x0:
        world_spans.append((xn - gap_left_cm - DOOR_CM, xn - gap_left_cm))

    if flip_main:
        pa, pb = R(x1, 0.0), R(x0, 0.0)
        to_t = lambda xw: x1 - xw  # noqa: E731
    else:
        pa, pb = R(x0, 0.0), R(x1, 0.0)
        to_t = lambda xw: xw - x0  # noqa: E731
    main = (seg(pa[0], pa[1], pb[0], pb[1]), ft(WALL_THICKNESS_CM), (False, False))

    ops_main = []
    for (wa, wb) in world_spans:
        ta, tb = sorted((to_t(wa), to_t(wb)))
        ops_main.append((ft(ta), ft(tb), ft(0.0), ft(210.0)))

    if flip_inc:
        qa, qb = R(xn, -inc_cm), R(xn, 0.0)
    else:
        qa, qb = R(xn, 0.0), R(xn, -inc_cm)
    inc = (seg(qa[0], qa[1], qb[0], qb[1]), ft(WALL_THICKNESS_CM), (False, False))

    mi, ii = order
    walls = [None, None]
    walls[mi], walls[ii] = main, inc
    ops = [None, None]
    ops[mi], ops[ii] = ops_main, []
    pn = R(xn, 0.0)
    node = {"point": XYZ(ft(pn[0]), ft(pn[1]), 0.0),
            "main_wall_idx": mi, "incoming_wall_idx": ii}
    return node, walls, ops


def room_ok(**kw):
    node, walls, ops = t_scene(**kw)
    return ws._t_intersection_room_ok(node, walls, ops)


def measured(**kw):
    """(direita, esquerda, boneca) em cm de MUNDO - ja' desfeita a troca de
    papel que a inversao da principal provoca em room_plus/room_minus."""
    node, walls, ops = t_scene(**kw)
    a = ws._t_intersection_room_assessment(node, walls, ops)
    plus, minus = to_cm(a["room_plus_ft"]), to_cm(a["room_minus_ft"])
    if kw.get("flip_main"):
        plus, minus = minus, plus
    return (plus, minus, to_cm(a["room_incoming_ft"]))


def physics_says_ok(gap_right_cm, gap_left_cm, inc_cm):
    """A resposta correta, calculada AQUI, sem olhar para o motor."""
    return (min(gap_right_cm, gap_left_cm) >= B54_HALF_ROOM_CM
            and inc_cm >= B34_CM)


# ========================================== 1. conversoes e constantes
def test_conversoes_cm_pes_e_tolerancia_fisica():
    """1 pe' = 30,48cm por definicao, e o round-trip cm->pes->cm erra
    ordens de grandeza MENOS que a propria tolerancia fisica - sem isso a
    guarda de 0,05cm seria indistinguivel de ruido de ponto flutuante."""
    assert abs(ws._ft_to_cm(1.0) - 30.48) < 1e-9
    assert abs(ws._cm_to_ft(30.48) - 1.0) < 1e-12

    worst = 0.0
    v = 0.0
    while v <= 2000.0:
        worst = max(worst, abs(ws._ft_to_cm(ws._cm_to_ft(v)) - v))
        v += 0.25
    assert worst < PHYSICAL_TOL_CM / 1000.0, worst

    # Um unico significado de FEET_PER_METER no motor inteiro.
    assert abs(tol.FEET_PER_METER - 1.0 / 0.3048) < 1e-12
    assert mm.FEET_PER_METER == tol.FEET_PER_METER
    assert ws.FEET_PER_METER == tol.FEET_PER_METER

    # A guarda FISICA e' a mais apertada das duas; a de FIT e' maior de
    # proposito (decide composicao, nao posicao).
    assert mm.PIER_PHYSICAL_FIT_TOLERANCE_CM == PHYSICAL_TOL_CM
    assert mm.PIER_PHYSICAL_FIT_TOLERANCE_CM < mm.PIER_FIT_TOLERANCE_CM

    # As duas exigencias do no' T, reconstruidas da fisica do bloco.
    assert abs(to_cm(ws.T_INTERSECTION_B54_HALF_ROOM_FT) - B54_HALF_ROOM_CM) < 1e-9
    assert abs(to_cm(ws.CORNER_B34_ROOM_FT) - B34_CM) < 1e-9


# ================================= 2/3. a tolerancia REAL da guarda do T
def test_guarda_do_no_t_nao_absorve_005_cm():
    """ACHADO que a auditoria registra explicitamente: a guarda do no' T
    NAO usa PIER_PHYSICAL_FIT_TOLERANCE_CM. Ela compara em PES com folga
    1e-6 (= 3,05e-5 cm), quatro ordens de grandeza mais apertada. Uma
    falta de 0,05cm - e ate' de 0,001cm - JA' REPROVA. Sao guardas
    diferentes, de perguntas diferentes: aqui e' "cabe?", na jamba e'
    "o que ja' foi materializado invade?"."""
    eps_cm = to_cm(1e-6)
    assert eps_cm < PHYSICAL_TOL_CM / 1000.0, eps_cm

    for d in (0.001, 0.049, 0.05, 0.051, 0.10):
        assert room_ok(gap_right_cm=B54_HALF_ROOM_CM - d) is False, d
        assert room_ok(gap_left_cm=B54_HALF_ROOM_CM - d) is False, d
        assert room_ok(inc_cm=B34_CM - d) is False, d
        assert room_ok(gap_right_cm=B54_HALF_ROOM_CM + d) is True, d
        assert room_ok(inc_cm=B34_CM + d) is True, d


def test_sweep_fino_menos_010_a_mais_010_cm():
    """Varredura de 0,001 em 0,001cm de -0,10 a +0,10cm em torno de CADA
    limite: exatamente uma transicao, e no lugar certo. Nenhuma faixa em
    que faltar espaco aprova, nenhuma em que sobrar espaco reprova."""
    for kw, req in (("gap_right_cm", B54_HALF_ROOM_CM),
                    ("gap_left_cm", B54_HALF_ROOM_CM),
                    ("inc_cm", B34_CM)):
        flips = []
        prev = None
        d = -0.10
        while d <= 0.10 + 1e-12:
            r = room_ok(**{kw: req + d})
            if d < -1e-9:
                assert r is False, (kw, d)
            elif d > 1e-9:
                assert r is True, (kw, d)
            if prev is not None and r != prev:
                flips.append(d)
            prev = r
            d = round(d + 0.001, 6)
        assert len(flips) == 1, (kw, flips)
        assert abs(flips[0]) <= 0.001 + 1e-9, (kw, flips)


# ============================ 3b. a guarda onde os 0,05cm DE FATO valem
def test_guarda_de_jamba_no_limite_de_005_cm():
    """`_layout_fitted_to_physical_span` e' onde PIER_PHYSICAL_FIT_TOLERANCE_CM
    realmente decide. Fronteira medida: excesso <= 0,05cm e' ruido e o
    layout passa intacto; ACIMA disso o trecho e' remontado - e o
    remontado nunca pode invadir mais que a propria tolerancia."""
    def layout_for_span(span_cm):
        n = int(span_cm // 5.0) * 5.0
        return [("X", 0.0, n)] if n > 0 else None

    for excess in (0.0, 0.01, 0.049, 0.05):
        layout = [("X", 0.0, 100.0 + excess)]
        out = ws._layout_fitted_to_physical_span(
            layout, 100.0, {"trailing_open": True}, layout_for_span)
        assert out is layout, excess

    for excess in (0.0500001, 0.051, 0.10, 0.30):
        layout = [("X", 0.0, 100.0 + excess)]
        out = ws._layout_fitted_to_physical_span(
            layout, 100.0, {"trailing_open": True}, layout_for_span)
        assert out is not layout, excess
        if out is not None:
            assert ws._layout_physical_end_cm(out) - 100.0 <= PHYSICAL_TOL_CM + 1e-9

    # Ponta COM junta de argamassa: a junta cede, a guarda nao age.
    for excess in (0.051, 0.30, 1.00):
        layout = [("X", 0.0, 100.0 + excess)]
        out = ws._layout_fitted_to_physical_span(
            layout, 100.0, {"trailing_open": False}, layout_for_span)
        assert out is layout, excess


def test_guarda_de_jamba_e_monotona_no_espaco_fisico():
    """Trecho fisico MAIOR para o mesmo layout nunca pode passar de
    aceito para rejeitado."""
    def layout_for_span(span_cm):
        n = int(span_cm // 5.0) * 5.0
        return [("X", 0.0, n)] if n > 0 else None

    layout = [("X", 0.0, 100.0)]
    seen_kept = False
    pier = 95.0
    while pier <= 105.0 + 1e-9:
        out = ws._layout_fitted_to_physical_span(
            layout, pier, {"trailing_open": True}, layout_for_span)
        if out is layout:
            seen_kept = True
        else:
            assert not seen_kept, pier
        pier = round(pier + 0.01, 6)


# ==================================================== 5. monotonicidade
def test_mais_espaco_fisico_nunca_piora_room_ok():
    """A propriedade que mais importa: a guarda tem que ser MONOTONA. Se
    ela aprovasse um no' apertado e reprovasse o mesmo no' com folga, o
    solver estaria decidindo por ruido, nao por fisica."""
    for kw in ("gap_right_cm", "gap_left_cm", "inc_cm"):
        seen_true = False
        v = 5.0
        while v <= 120.0 + 1e-9:
            r = room_ok(**{kw: v})
            if r:
                seen_true = True
            else:
                assert not seen_true, (kw, v)
            v = round(v + 0.05, 6)

    # Monotonicidade CONJUNTA: se todo espaco de B e' >= o de A, entao
    # room_ok(B) >= room_ok(A).
    grid = (10.0, 26.5, 27.0, 27.5, 33.5, 34.0, 60.0)
    pts = list(itertools.product(grid, grid, grid))
    res = {}
    for p in pts:
        res[p] = room_ok(gap_right_cm=p[0], gap_left_cm=p[1], inc_cm=p[2])
    for a in pts:
        if not res[a]:
            continue
        for b in pts:
            if all(bi >= ai for ai, bi in zip(a, b)):
                assert res[b], (a, b)


# ===================== 6. equivalentes geometricos com ruido +/- 
def test_ruido_positivo_e_negativo_em_torno_do_limite():
    """O MESMO no' fisico com ruido de sinal oposto: o lado seguro aprova,
    o lado inseguro reprova. E longe do limite, o sinal do ruido nao muda
    nada - nao existe faixa cinzenta dependente de sinal."""
    for base, kw in ((B54_HALF_ROOM_CM, "gap_right_cm"), (B34_CM, "inc_cm")):
        for noise in (0.001, 0.01, 0.03, 0.05, 0.1):
            assert room_ok(**{kw: base + noise}) is True, (kw, noise)
            assert room_ok(**{kw: base - noise}) is False, (kw, noise)

    for noise in (-0.1, -0.05, -0.01, 0.0, 0.01, 0.05, 0.1):
        assert room_ok(gap_right_cm=B54_HALF_ROOM_CM + 1.0 + noise,
                       gap_left_cm=B54_HALF_ROOM_CM + 1.0 - noise,
                       inc_cm=B34_CM + 1.0 + noise) is True, noise


# =========================================== 7. faltas REAIS de projeto
def test_faltas_reais_de_4_15_e_20_cm_continuam_reprovando():
    """Os casos que motivaram a guarda (porta perto do no', boneca curta):
    faltas grandes tem que reprovar mesmo com ruido favoravel somado."""
    for falta in (4.0, 15.0, 20.0):
        assert room_ok(gap_right_cm=B54_HALF_ROOM_CM - falta) is False, falta
        assert room_ok(gap_left_cm=B54_HALF_ROOM_CM - falta) is False, falta
        assert room_ok(inc_cm=B34_CM - falta) is False, falta
        # ruido favoravel de uma tolerancia fisica inteira nao salva
        assert room_ok(
            gap_right_cm=B54_HALF_ROOM_CM - falta + PHYSICAL_TOL_CM) is False, falta
        assert room_ok(inc_cm=B34_CM - falta + PHYSICAL_TOL_CM) is False, falta

    # casos historicos da suite (2026-08-21)
    assert room_ok(gap_right_cm=5.0) is False
    assert room_ok(inc_cm=20.0) is False


# ============ 8. inversao de pontas, translacao, rotacao e permutacao
def _probes():
    out = []
    for p in (10.0, 26.95, 27.0, 27.05, 50.0):
        for q in (10.0, 27.0, 50.0):
            for i in (20.0, 33.95, 34.0, 34.05, 60.0):
                out.append({"gap_right_cm": p, "gap_left_cm": q, "inc_cm": i})
    return out


def test_invariancia_a_inversao_translacao_e_permutacao():
    """Nenhuma dessas transformacoes muda UM MILIMETRO de alvenaria - e
    por isso nenhuma pode mudar o veredito nem a medicao."""
    variants = [
        {"flip_main": True},
        {"flip_inc": True},
        {"flip_main": True, "flip_inc": True},
        {"order": (1, 0)},
        {"ox": 777.0},
        {"ox": -313.0},
        {"oy": 505.0},
        {"ox": 421.0, "oy": -97.0, "flip_main": True, "flip_inc": True,
         "order": (1, 0)},
    ]
    for kw in variants:
        for p in _probes():
            assert room_ok(**p) == room_ok(**dict(p, **kw)), (p, kw)
            base, var = measured(**p), measured(**dict(p, **kw))
            for x, y in zip(base, var):
                assert abs(x - y) < 1e-6, (p, kw, base, var)


def test_invariancia_a_rotacao_e_fuzz_contra_a_fisica():
    """Fuzz: paredes fora dos eixos, origem arbitraria, pontas invertidas e
    indices permutados. O veredito tem que bater com a fisica recalculada
    aqui, caso a caso."""
    rng = random.Random(20260917)
    angles = [0.0, math.pi / 6, math.pi / 4, math.pi / 3, math.pi / 2,
              2.1, 3.0, -0.7, -1.9]

    for _ in range(1200):
        gr = round(rng.uniform(1.0, 90.0), 4)
        gl = round(rng.uniform(1.0, 90.0), 4)
        ic = round(rng.uniform(1.0, 90.0), 4)
        got = room_ok(gap_right_cm=gr, gap_left_cm=gl, inc_cm=ic,
                      theta=rng.choice(angles),
                      ox=round(rng.uniform(-500.0, 500.0), 2),
                      oy=round(rng.uniform(-500.0, 500.0), 2),
                      flip_main=rng.choice((False, True)),
                      flip_inc=rng.choice((False, True)),
                      order=rng.choice(((0, 1), (1, 0))))
        assert got is physics_says_ok(gr, gl, ic), (gr, gl, ic, got)


# ============================================ 9. legado / strategy=None
def test_legado_e_ausencia_de_estrategia():
    """`openings_per_wall=None` (chamador antigo) nunca bloqueia; lista
    VAZIA nao e' a mesma coisa e a guarda continua ativa. E a guarda nao
    recebe estrategia nenhuma: e' puramente geometrica, entao nenhuma
    variacao de estrategia do solver pode mover esta fronteira."""
    import inspect

    node, walls, _ops = t_scene(gap_right_cm=1.0, inc_cm=1.0)
    assert ws._t_intersection_room_ok(node, walls, None) is True

    bad = {"point": XYZ(ft(200.0), 0.0, 0.0), "main_wall_idx": None,
           "incoming_wall_idx": 1}
    assert ws._t_intersection_room_ok(bad, walls, [[], []]) is True
    assert ws._t_intersection_room_assessment(bad, walls, [[], []]) is None

    n2, w2, _ = t_scene(inc_cm=20.0)
    assert ws._t_intersection_room_ok(n2, w2, [[], []]) is False

    assert "strategy" not in inspect.signature(ws._t_intersection_room_ok).parameters
    assert "strategy" not in inspect.signature(
        ws._t_intersection_room_assessment).parameters
