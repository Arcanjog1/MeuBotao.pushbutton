# -*- coding: utf-8 -*-
"""ETAPA 2I - laboratorio do CR-2F-E (CENTERLINE_ARGUMENT_ASYMMETRY).

SOMENTE LEITURA de `nuvem/core/**`. Nenhum arquivo do motor e' alterado
por esta etapa - as alternativas de eixo sao definidas AQUI e injetadas em
memoria (`patched()`), do mesmo jeito que a Etapa 2G fez com os predicados
do par.

O recorte e' o do pedido da 2I:

    par geometrico JA' ACEITO  ->  eixo da parede

`find_wall_pairs` (predicados CR-2F-B + desempate CR-2F-C) fica CONGELADO:
nenhuma funcao daqui toca ranking, thickness_rank, E_ovl, chave de
desempate, conjunto de candidatos ou selecao gulosa.

Vocabulario usado em todos os relatorios desta etapa:

  ARGUMENT ORDER   create_centerline(A, B)  x  create_centerline(B, A)
  ENDPOINT DIR     Line(p0,p1)              x  Line(p1,p0)

Sao invariancias DIFERENTES e sao medidas separadamente (itens 6 e 7).

Estrategias de eixo:

  cur   producao atual (ancora em l1.p0, intervalo ancorado em l1) - baseline
  S1    CANONICAL_ARGUMENT_ORDER: ordena (l1,l2) por chave geometrica
        canonica antes de chamar o `cur` intocado
  S2    LONGEST_REFERENCE: a linha mais LONGA e' sempre a referencia
  S3    SYMMETRIC_BISECTOR: frame sem lado (bissetriz), intervalo = uniao
        das quatro pontas projetadas, clamp na uniao dos dois comprimentos
  S4    MUTUAL_OVERLAP_CENTERLINE: frame sem lado, intervalo = so' o trecho
        em que as duas faces realmente se encaram
  S5    ENDPOINT_AVERAGING: frame sem lado, intervalo = media simetrica dos
        dois intervalos projetados
  S6    SYMMETRIC_UNION_CLAMPED: como S3, mas o clamp de extensao e'
        simetrico (aplicado sobre a INTERSECAO dos dois intervalos, com o
        mesmo teto max_extension_ft para cada lado)
  S7    SYMMETRIC_LONGEST_SPAN: frame sem lado + intervalo = UNIAO das duas
        faces, com o teto `max_extension_ft` medido a partir do intervalo da
        face MAIS LONGA (a que o proprio docstring de `create_centerline`
        diz que deve prevalecer). E' a leitura literal da INTENCAO declarada
        da funcao, escrita de forma simetrica - reproduz `cur` exatamente
        sempre que `l1` ja' era a face mais longa.
"""
import hashlib
import json
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_2F = os.path.abspath(os.path.join(_HERE, "..", "diagnostics_2f"))
_2G = os.path.abspath(os.path.join(_HERE, "..", "diagnostics_2g"))
for _p in (_2F, _2G):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import lib2f as L  # noqa: E402

STRATEGIES = ("cur", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8")
SYMMETRIC_CLAIM = ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8")

SEEDS = [1, 2, 3, 10, 42]
WATCH = ("W001", "W010", "W037", "W053", "W054", "W068", "W074")
OP_WATCH = "6558457"


def out_path(name):
    return os.path.join(_HERE, name)


def dump(name, obj):
    p = out_path(name)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
    print("-> " + p)


def cm(ft):
    return L.cm(ft)


def ft(v_cm):
    return v_cm * L.load()["F"] / 100.0


# ==========================================================================
# GEOMETRIA DE APOIO (float puro, 2D - nunca um XYZ intermediario)
# ==========================================================================
def xy(line):
    """((x0,y0),(x1,y1)) em PES, na ordem em que a Line foi construida."""
    p0, p1 = line.GetEndPoint(0), line.GetEndPoint(1)
    return (p0.X, p0.Y), (p1.X, p1.Y)


def zof(line):
    return line.GetEndPoint(0).Z


def unit(ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    n = math.hypot(dx, dy)
    return (dx / n, dy / n, n) if n > 1e-12 else (1.0, 0.0, 0.0)


def mkline_ft(x0, y0, x1, y1, z=0.0):
    mod = L.load()["mod"]
    return mod.Line.CreateBound(mod.XYZ(x0, y0, z), mod.XYZ(x1, y1, z))


def reversed_line(line):
    (a, b) = xy(line)
    return mkline_ft(b[0], b[1], a[0], a[1], zof(line))


# --- comparacao GEOMETRICA de dois segmentos ------------------------------
def seg_canon(line, nd=6):
    """Chave canonica de um segmento em CM: ponta menor primeiro (logo,
    Line(p0,p1) e Line(p1,p0) dao a MESMA chave - inverter o sentido NAO e'
    'eixo diferente')."""
    if line is None:
        return None
    (a, b) = xy(line)
    ka = (round(cm(a[0]), nd) + 0.0, round(cm(a[1]), nd) + 0.0)
    kb = (round(cm(b[0]), nd) + 0.0, round(cm(b[1]), nd) + 0.0)
    return (ka, kb) if ka <= kb else (kb, ka)


def _pt_seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    if L2 < 1e-18:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * vx + (py - ay) * vy) / L2
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return math.hypot(px - (ax + vx * t), py - (ay + vy * t))


def seg_hausdorff_cm(l1, l2):
    """Distancia de Hausdorff (em cm) entre os dois SEGMENTOS - metrica
    geometrica, insensivel ao sentido dos endpoints. Para segmentos retos,
    max sobre as 4 pontas basta (o maximo de uma funcao convexa por trecho
    esta' sempre num extremo)."""
    (a0, a1) = xy(l1)
    (b0, b1) = xy(l2)
    d = 0.0
    for (px, py) in (a0, a1):
        d = max(d, _pt_seg_dist(px, py, b0[0], b0[1], b1[0], b1[1]))
    for (px, py) in (b0, b1):
        d = max(d, _pt_seg_dist(px, py, a0[0], a0[1], a1[0], a1[1]))
    return cm(d)


def seg_endpoint_delta_cm(l1, l2):
    """(delta_origem, delta_destino) em cm, ja' casando as pontas na
    correspondencia mais proxima (mesma ideia de `_xy_deviation_ft`)."""
    (a0, a1) = xy(l1)
    (b0, b1) = xy(l2)

    def dist(p, q):
        return cm(math.hypot(p[0] - q[0], p[1] - q[1]))
    same = (dist(a0, b0), dist(a1, b1))
    flip = (dist(a0, b1), dist(a1, b0))
    return same if max(same) <= max(flip) else flip


def seg_len_cm(line):
    (a, b) = xy(line)
    return cm(math.hypot(b[0] - a[0], b[1] - a[1]))


def seg_angle_deg(line):
    (a, b) = xy(line)
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0


def classify(c1, c2, tol_cm=1e-4):
    """Classificacao GEOMETRICA da diferenca entre dois eixos calculados
    para o MESMO par. Categorias do item 6 do pedido."""
    if c1 is None and c2 is None:
        return "ambos_degenerados"
    if c1 is None or c2 is None:
        return "um_degenerado"
    if seg_canon(c1, 6) == seg_canon(c2, 6):
        return "identicos"
    # mesmo conjunto de pontas, so' a ordem muda -> mesmo segmento
    if seg_hausdorff_cm(c1, c2) <= tol_cm:
        return "so_direcao_endpoints"

    a1, a2 = seg_angle_deg(c1), seg_angle_deg(c2)
    dang = abs(a1 - a2) % 180.0
    dang = min(dang, 180.0 - dang)
    colinear = dang <= 0.05 and _perp_offset_cm(c1, c2) <= 0.05
    l1, l2 = seg_len_cm(c1), seg_len_cm(c2)
    if colinear:
        return "mesma_reta_extensao_diferente"
    if dang <= 0.05:
        return "deslocamento_paralelo"
    if abs(l1 - l2) > 0.05 * max(l1, l2):
        return "eixo_diferente_comprimento"
    return "eixo_completamente_diferente"


def _perp_offset_cm(c1, c2):
    """Maior afastamento PERPENDICULAR das pontas de c2 em relacao a' RETA
    de c1 (em cm)."""
    (a0, a1) = xy(c1)
    ux, uy, n = unit(a0[0], a0[1], a1[0], a1[1])
    if n <= 1e-12:
        return float("inf")
    out = 0.0
    for (px, py) in xy(c2):
        out = max(out, abs(-(px - a0[0]) * uy + (py - a0[1]) * ux))
    return cm(out)


# ==========================================================================
# FRAME SIMETRICO DO PAR - a MESMA construcao ja' usada em producao por
# `_pair_frame_cached` (CR-2F-B), reescrita aqui em float puro sobre as
# Line (a de producao trabalha sobre o cache do par). Trocar l1<->l2 devolve
# o mesmo frame ou o mesmo com os dois eixos negados.
# ==========================================================================
def pair_frame(l1, l2):
    (p0, p1) = xy(l1)
    (q0, q1) = xy(l2)
    d1x, d1y, len1 = unit(p0[0], p0[1], p1[0], p1[1])
    d2x, d2y, len2 = unit(q0[0], q0[1], q1[0], q1[1])
    s = 1.0 if (d1x * d2x + d1y * d2y) >= 0.0 else -1.0
    bx, by = d1x + d2x * s, d1y + d2y * s
    nb = math.hypot(bx, by)
    if nb < 1e-9:
        bx, by = d1x, d1y
    else:
        bx, by = bx / nb, by / nb
    nx, ny = -by, bx
    m1 = ((p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5)
    m2 = ((q0[0] + q1[0]) * 0.5, (q0[1] + q1[1]) * 0.5)
    ox, oy = (m1[0] + m2[0]) * 0.5, (m1[1] + m2[1]) * 0.5
    return bx, by, nx, ny, ox, oy, len1, len2


def _proj(fr, p):
    bx, by, nx, ny, ox, oy = fr[:6]
    dx, dy = p[0] - ox, p[1] - oy
    return (bx * dx + by * dy, nx * dx + ny * dy)


def _interval(fr, line):
    (a, b) = xy(line)
    ta, sa = _proj(fr, a)
    tb, sb = _proj(fr, b)
    return (ta, tb) if ta <= tb else (tb, ta), (sa if ta <= tb else sb,
                                                sb if ta <= tb else sa)


def _mean_s(fr, line):
    """Coordenada perpendicular MEDIA da linha no frame (para linhas
    exatamente paralelas a' bissetriz e' constante; com desvio angular
    pequeno a media das duas pontas e' o valor no ponto medio)."""
    (a, b) = xy(line)
    return (_proj(fr, a)[1] + _proj(fr, b)[1]) * 0.5


def _emit(fr, t_lo, t_hi, s_axis, z):
    """Constroi a Line do eixo a partir do intervalo [t_lo, t_hi] e do
    afastamento perpendicular `s_axis`, no frame `fr`."""
    bx, by, nx, ny, ox, oy = fr[:6]
    x0 = ox + bx * t_lo + nx * s_axis
    y0 = oy + by * t_lo + ny * s_axis
    x1 = ox + bx * t_hi + nx * s_axis
    y1 = oy + by * t_hi + ny * s_axis
    if math.hypot(x1 - x0, y1 - y0) < 0.01:
        return None
    # orientacao canonica das pontas: ponta lexicograficamente menor
    # primeiro -> ENDPOINT DIR do resultado nao depende de nada da entrada.
    if (x1, y1) < (x0, y0):
        x0, y0, x1, y1 = x1, y1, x0, y0
    return mkline_ft(x0, y0, x1, y1, z)


# ==========================================================================
# ESTRATEGIAS
# ==========================================================================
def cl_cur(l1, l2, ext):
    return L.load()["mod"].create_centerline(l1, l2, ext)


def _ident(line, nd=2):
    (a, b) = xy(line)
    ka = (round(cm(a[0]), nd) + 0.0, round(cm(a[1]), nd) + 0.0)
    kb = (round(cm(b[0]), nd) + 0.0, round(cm(b[1]), nd) + 0.0)
    return (ka, kb) if ka <= kb else (kb, ka)


def cl_S1(l1, l2, ext):
    """CANONICAL_ARGUMENT_ORDER - nao muda NADA da formula: so' fixa qual
    das duas linhas entra como `l1`, pela mesma chave geometrica canonica
    do CR-2F-C. Invariante a' ORDEM DOS ARGUMENTOS por construcao; NAO
    invariante ao SENTIDO dos endpoints (a ancora continua sendo `p0` da
    linha escolhida)."""
    return cl_cur(l1, l2, ext) if _ident(l1) <= _ident(l2) else cl_cur(l2, l1, ext)


def cl_S2(l1, l2, ext):
    """LONGEST_REFERENCE - a linha mais LONGA e' a referencia (desempate
    pela chave canonica, senao duas linhas do mesmo comprimento voltam a
    depender da ordem)."""
    (a0, a1), (b0, b1) = xy(l1), xy(l2)
    la = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
    lb = math.hypot(b1[0] - b0[0], b1[1] - b0[1])
    if la > lb:
        return cl_cur(l1, l2, ext)
    if lb > la:
        return cl_cur(l2, l1, ext)
    return cl_S1(l1, l2, ext)


def _axis_s(fr, l1, l2):
    """Afastamento perpendicular do EIXO no frame: meio caminho entre as
    duas faces. Simetrico por construcao (media)."""
    return (_mean_s(fr, l1) + _mean_s(fr, l2)) * 0.5


def cl_S3(l1, l2, ext):
    """SYMMETRIC_BISECTOR - intervalo = UNIAO das quatro pontas projetadas,
    limitada a `ext` alem da INTERSECAO dos dois intervalos (o trecho em que
    as duas faces se encaram - o unico trecho 'certo' sem lado)."""
    fr = pair_frame(l1, l2)
    (ai, zi), _ = _interval(fr, l1)
    (aj, zj), _ = _interval(fr, l2)
    lo_u, hi_u = min(ai, aj), max(zi, zj)
    lo_c, hi_c = max(ai, aj), min(zi, zj)
    if hi_c <= lo_c:            # sem trecho comum: nao ha base simetrica
        lo_c, hi_c = lo_u, hi_u
    t_lo = max(lo_u, lo_c - ext)
    t_hi = min(hi_u, hi_c + ext)
    return _emit(fr, t_lo, t_hi, _axis_s(fr, l1, l2), zof(l1))


def cl_S4(l1, l2, ext):
    """MUTUAL_OVERLAP_CENTERLINE - so' o trecho em que as duas faces
    realmente se encaram. Nenhuma extensao."""
    fr = pair_frame(l1, l2)
    (ai, zi), _ = _interval(fr, l1)
    (aj, zj), _ = _interval(fr, l2)
    lo, hi = max(ai, aj), min(zi, zj)
    if hi <= lo:
        return None
    return _emit(fr, lo, hi, _axis_s(fr, l1, l2), zof(l1))


def cl_S5(l1, l2, ext):
    """ENDPOINT_AVERAGING - cada ponta do eixo e' a MEDIA das pontas
    correspondentes dos dois intervalos projetados."""
    fr = pair_frame(l1, l2)
    (ai, zi), _ = _interval(fr, l1)
    (aj, zj), _ = _interval(fr, l2)
    return _emit(fr, (ai + aj) * 0.5, (zi + zj) * 0.5,
                 _axis_s(fr, l1, l2), zof(l1))


def cl_S6(l1, l2, ext):
    """SYMMETRIC_UNION_CLAMPED - a INTENCAO declarada do `cur` (uniao do
    alcance das duas faces: 'em cada ponta usa a mais longa das duas'),
    com o teto de extensao aplicado de forma SIMETRICA. No `cur` o teto e'
    medido a partir do intervalo de `l1`; aqui e' medido a partir do
    intervalo de CADA linha e vale a permissao mais restritiva - identico
    para as duas ordens.

    Diferenca para S3: S3 mede o teto a partir da INTERSECAO; S6 mede a
    partir do intervalo de cada linha e toma o MENOR alcance permitido -
    e' a leitura literal 'cada face pode puxar a outra ate' ext'."""
    fr = pair_frame(l1, l2)
    (ai, zi), _ = _interval(fr, l1)
    (aj, zj), _ = _interval(fr, l2)
    lo_u, hi_u = min(ai, aj), max(zi, zj)
    lo_lim = min(max(ai, aj - ext), max(aj, ai - ext))
    hi_lim = max(min(zi, zj + ext), min(zj, zi + ext))
    t_lo = max(lo_u, lo_lim)
    t_hi = min(hi_u, hi_lim)
    if t_hi <= t_lo:
        t_lo, t_hi = max(ai, aj), min(zi, zj)
    return _emit(fr, t_lo, t_hi, _axis_s(fr, l1, l2), zof(l1))


def cl_S7(l1, l2, ext):
    """SYMMETRIC_LONGEST_SPAN - o intervalo e' a UNIAO dos dois intervalos
    projetados, limitada a `ext` alem do intervalo da face MAIS LONGA.

    Por que a face mais longa e' a referencia geometrica legitima (e nao uma
    regra lexicografica arbitraria): e' a propria regra que o docstring de
    `create_centerline` ja' declara - "em cada ponta, usa a que for MAIS
    LONGA das duas faces pareadas... a face mais longa sempre prevalece,
    entao a parede chega ate' o ponto de conexao correto em vez de deixar um
    recuo/mordida no canto". O `cur` implementa isso ancorado em `l1` (a
    posicao na lista), e por isso so' acerta quando `l1` ja' era a mais
    longa. Aqui a escolha e' pela GEOMETRIA (comprimento), nao pela ordem.

    O teto `ext` continua fazendo o mesmo trabalho de sempre: impedir que
    um pareamento equivocado (uma linha bem mais longa que apenas passa
    perto) faca o eixo disparar - so' que agora medido a partir da face
    longa, para as duas ordens.

    Empate de comprimento (<= 1e-9 ft): desempate pela chave geometrica
    canonica - so' entao a lexicografia entra, e apenas para escolher entre
    dois intervalos IDENTICOS em extensao."""
    fr = pair_frame(l1, l2)
    (ai, zi), _ = _interval(fr, l1)
    (aj, zj), _ = _interval(fr, l2)
    li, lj = zi - ai, zj - aj
    if abs(li - lj) <= 1e-9:
        ref_first = _ident(l1) <= _ident(l2)
    else:
        ref_first = li > lj
    a_ref, z_ref = (ai, zi) if ref_first else (aj, zj)
    t_lo = max(min(ai, aj), a_ref - ext)
    t_hi = min(max(zi, zj), z_ref + ext)
    return _emit(fr, t_lo, t_hi, _axis_s(fr, l1, l2), zof(l1))


# folga aceita entre a face e a "faixa" da parede, alem da propria
# semi-espessura: a MESMA tolerancia com que o motor ja' aceita uma linha
# como face de parede (WALL_DETECTION_TOLERANCE_M = 2,5 cm). Nao e' um
# parametro novo desta etapa.
def _band_tol_ft():
    return L.load()["mod"].WALL_DETECTION_TOLERANCE_FT


def cl_S8(l1, l2, ext):
    """SYMMETRIC_BANDED_SPAN - S7 com a GUARDA GEOMETRICA que falta.

    S7 (e a regra "face mais longa" em geral) supoe que a face mais longa e'
    de fato uma face DAQUELA parede. Quando nao e' - uma linha longa que
    apenas passa perto, com um pequeno desvio angular - o eixo dispara.
    O teste geometrico que distingue os dois casos ja' existe na propria
    definicao de parede: uma face real fica a MEIA ESPESSURA do eixo ao
    longo de todo o trecho. Entao o eixo so' pode acompanhar uma face ate'
    onde essa face continua dentro da faixa
    [meia_espessura +- WALL_DETECTION_TOLERANCE] - a mesma tolerancia com
    que `find_wall_pairs` ja' aceita a linha como face.

    Para faces exatamente paralelas (o caso normal) a faixa nunca aperta e
    S8 == S7. So' aperta onde ha' desvio angular - exatamente onde S7 erra.

    Nenhum limiar novo: `ext` e `WALL_DETECTION_TOLERANCE_FT` ja' existem.
    """
    fr = pair_frame(l1, l2)
    (ai, zi), _ = _interval(fr, l1)
    (aj, zj), _ = _interval(fr, l2)
    s_axis = _axis_s(fr, l1, l2)
    tol = _band_tol_ft()

    # semi-espessura medida SO' no trecho em que as duas faces se encaram
    lo_c, hi_c = max(ai, aj), min(zi, zj)
    if hi_c > lo_c:
        tm = (lo_c + hi_c) * 0.5
        h = abs(_s_at(fr, l1, tm) - _s_at(fr, l2, tm)) * 0.5
    else:
        h = abs(_mean_s(fr, l1) - _mean_s(fr, l2)) * 0.5

    li, lj = zi - ai, zj - aj
    if abs(li - lj) <= 1e-9:
        ref_first = _ident(l1) <= _ident(l2)
    else:
        ref_first = li > lj
    a_ref, z_ref = (ai, zi) if ref_first else (aj, zj)

    lo, hi = min(ai, aj), max(zi, zj)
    lo = max(lo, a_ref - ext)
    hi = min(hi, z_ref + ext)
    # recorte pela FAIXA: cada face so' arrasta o eixo enquanto ela mesma
    # continua a meia espessura (+- tol) dele.
    for ln, (a, z) in ((l1, (ai, zi)), (l2, (aj, zj))):
        blo, bhi = _band_span(fr, ln, a, z, s_axis, h + tol)
        if blo is None:
            continue
        # a faixa da face `ln` so' pode limitar o trecho que vem DELA
        lo = max(lo, min(blo, max(ai, aj)))
        hi = min(hi, max(bhi, min(zi, zj)))
    if hi <= lo:
        lo, hi = max(ai, aj), min(zi, zj)
    return _emit(fr, lo, hi, s_axis, zof(l1))


def _s_at(fr, line, t):
    """Coordenada perpendicular da reta de `line` no frame, no parametro t
    (interpolacao linear entre as duas pontas projetadas)."""
    (a, b) = xy(line)
    ta, sa = _proj(fr, a)
    tb, sb = _proj(fr, b)
    if abs(tb - ta) < 1e-12:
        return (sa + sb) * 0.5
    return sa + (sb - sa) * (t - ta) / (tb - ta)


def _band_span(fr, line, a, z, s_axis, band):
    """Trecho [t_lo, t_hi] em que a reta de `line` fica a no maximo `band`
    do eixo (que esta' em s_axis, constante). Devolve (None, None) se a
    reta nunca entra na faixa."""
    sa = _s_at(fr, line, a)
    sz = _s_at(fr, line, z)
    if abs(z - a) < 1e-12:
        return (a, z) if abs(sa - s_axis) <= band else (None, None)
    k = (sz - sa) / (z - a)
    if abs(k) < 1e-15:
        return (a, z) if abs(sa - s_axis) <= band else (None, None)
    t1 = a + (s_axis + band - sa) / k
    t2 = a + (s_axis - band - sa) / k
    return (min(t1, t2), max(t1, t2))


IMPL = {"cur": cl_cur, "S1": cl_S1, "S2": cl_S2, "S3": cl_S3,
        "S4": cl_S4, "S5": cl_S5, "S6": cl_S6, "S7": cl_S7, "S8": cl_S8}


class patched(object):
    """Injeta a estrategia de eixo DENTRO do `find_wall_pairs` real, pelo
    dict de globais de `core.engine.wall_pairing` (mesma tecnica da 2G).
    Nenhum arquivo do motor e' tocado; o estado e' restaurado na saida."""

    def __init__(self, strat):
        self.strat = strat
        self.g = L.load()["mod"].find_wall_pairs.__globals__

    def __enter__(self):
        self.old = self.g["create_centerline"]
        if self.strat != "cur":
            self.g["create_centerline"] = IMPL[self.strat]
        return self

    def __exit__(self, *a):
        self.g["create_centerline"] = self.old
        return False


# ==========================================================================
# ESPIAO: quais pares find_wall_pairs realmente aceitou, e com que eixo
# ==========================================================================
class spy(object):
    def __init__(self, ids):
        self.ids = ids
        self.g = L.load()["mod"].find_wall_pairs.__globals__
        self.calls = []
        self.axes = {}

    def __enter__(self):
        self.old = self.g["create_centerline"]
        real = self.old

        def wrapper(l1, l2, ext):
            out = real(l1, l2, ext)
            a, b = self.ids[id(l1)], self.ids[id(l2)]
            self.calls.append((a, b))
            self.axes[frozenset((a, b))] = seg_canon(out, 6)
            return out
        self.g["create_centerline"] = wrapper
        return self

    def __exit__(self, *a):
        self.g["create_centerline"] = self.old
        return False

    def pairs(self):
        return set(frozenset(p) for p in self.calls)


def accepted_pairs(lines, strat="cur"):
    """Conjunto de pares (i, j) ACEITOS por find_wall_pairs, na ordem de
    producao, com a estrategia de eixo `strat` injetada."""
    ids = L.line_ids(lines)
    with patched(strat):
        with spy(ids) as sp:
            L.run_pairs(lines)
    return sorted(tuple(sorted(p)) for p in sp.pairs()), dict(sp.axes)


# ==========================================================================
# DOWNSTREAM
# ==========================================================================
def excess_len_cm(walls, tol_perp=6.0, tol_ang=3.0, margin=20.0):
    """Comprimento de eixo (cm) que NAO cai sobre nenhuma parede do
    gabarito - o custo de uma parede que "dispara" alem do desenho. Mede o
    complemento de `coverage`, do lado do RESULTADO (a cobertura do
    benchmark mede do lado do gabarito, e por isso nao ve excesso)."""
    S = L.load()
    R = [L.Ax(w["start_cm"][0], w["start_cm"][1], w["end_cm"][0], w["end_cm"][1])
         for w in S["ref"]["walls"]]
    total = 0.0
    for w in walls:
        x0, y0, x1, y1 = L.wall_xy(w)
        A = L.Ax(x0, y0, x1, y1)
        segs = []
        for B in R:
            if L.adiff(A.a, B.a) > tol_ang:
                continue
            # projeta a parede de referencia sobre o eixo A
            t0 = A.proj(B.x0, B.y0)
            t1 = A.proj(B.x1, B.y1)
            if abs(A.perp(B.x0, B.y0)) > tol_perp or abs(A.perp(B.x1, B.y1)) > tol_perp:
                continue
            lo, hi = sorted((t0, t1))
            lo, hi = max(0.0, lo - margin), min(A.L, hi + margin)
            if hi > lo:
                segs.append((lo, hi))
        if not segs:
            total += A.L
            continue
        segs.sort()
        cov = 0.0
        cl, ch = segs[0]
        for lo, hi in segs[1:]:
            if lo > ch:
                cov += ch - cl
                cl, ch = lo, hi
            else:
                ch = max(ch, hi)
        cov += ch - cl
        total += max(0.0, A.L - cov)
    return total


def axis_centering_error_cm(lines, pairs, strat, ext):
    """Autoverificacao GEOMETRICA do proprio motor (`_axis_offset_error_ft`):
    o eixo ficou realmente equidistante das duas faces? Independe do
    gabarito - mede se o ALGORITMO calculou o eixo certo."""
    mod = L.load()["mod"]
    worst = 0.0
    acc = 0.0
    n = 0
    over = 0
    for (a, b) in pairs:
        c = IMPL[strat](lines[a], lines[b], ext)
        if c is None:
            continue
        e = cm(mod._axis_offset_error_ft(c, lines[a], lines[b]))
        worst = max(worst, e)
        acc += e
        n += 1
        if e > cm(mod.AXIS_OFFSET_WARNING_FT):
            over += 1
    return dict(worst_cm=worst, mean_cm=acc / max(n, 1), n=n, over_warning=over)


def snap(res):
    S = L.load()
    gm = L.gabarito_metrics(res["walls"])
    covered = set()
    for k, c in enumerate(gm["covs"]):
        if c >= 0.85:
            covered.add(S["ref"]["walls"][k].get("id") or ("REF%03d" % k))
    unass = set()
    for o in res["open_diag"]["unassigned_openings"]:
        unass.add(str(o.get("element_id") if isinstance(o, dict) else o))
    wfp, _ = L.wall_fp(res["walls"])
    return dict(accepted=res["accepted"], walls=len(res["walls"]),
                cobertas=len(covered), covered=sorted(covered),
                ausentes=gm["ausentes"], eixo_ok=gm["eixo_ok"],
                eixo_10_16=gm["eixo_10_16"], espurias=gm["espurias"],
                walls_lt50=gm["walls_lt50"], walls_lt20=gm["walls_lt20"],
                total_len_cm=gm["total_len_cm"],
                openings_assigned=91 - len(unass), unassigned=sorted(unass),
                watch_ok=sum(1 for w in WATCH if w in covered),
                watch_missing=[w for w in WATCH if w not in covered],
                op_watch_orfa=(OP_WATCH in unass),
                excess_len_cm=excess_len_cm(res["walls"]),
                wall_fp=wfp, pair_time=res["pair_time"])


def downstream(lines, strat):
    with patched(strat):
        res = L.full_pipeline(lines)
    return snap(res)


def axis_fp(axes):
    """sha256 do CONJUNTO de eixos (chave canonica), independente de
    ordem - a camada imediatamente depois de find_wall_pairs (H3)."""
    keys = sorted(json.dumps(v, separators=(",", ":")) for v in axes.values())
    blob = json.dumps(keys, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
