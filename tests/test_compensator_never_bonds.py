# -*- coding: utf-8 -*-
"""REGRA 76 - compensador (C04/C09) NUNCA exerce funcao de amarracao (L, T ou X).

Compensador e' peca de AJUSTE DIMENSIONAL. Proximidade do no' NAO e' violacao;
a violacao e' FUNCIONAL: o compensador ocupando o lugar da peca que amarra o
encontro. Valido: [B54 de amarracao][C09 de ajuste][B39]. Invalido: C09 no
lugar do B54/B34 do no'.

O hard gate e' `wall_stepper.compensator_as_junction_bond` (aceitavel SOMENTE
vazio, somente leitura). Duas evidencias:
  * METADADO - o motor DESIGNOU o compensador peca do no' (node_index + razao
    L_CORNER/T_INTERSECTION/X_INTERSECTION/CORNER) -> DESIGNATED_NODE_PIECE;
  * GEOMETRIA (autoridade) - o compensador e' a peca das paredes do no' que
    cobre a MAIOR AREA da regiao do no' (interseccao das faixas de espessura)
    naquela fiada -> OCCUPIES_NODE_REGION.

Parte A (itens 1-11) monta/muta candidatos sobre nodes/walls REAIS do motor
(fixtures sinteticas L, T e cruz), sem depender de decisao do solver. Parte B
(itens 12-13) confere a consistencia do gate com o solver, sem apostar na
correcao futura do motor: o gate e' comparado com um ORACULO independente
(regiao do no' amostrada numa grade de 0,5 cm, nao recorte de poligono).

Dois defeitos do VALIDADOR encontrados por estes testes (empate de area
decidido pelo texto do codigo; compensador ocupando dois nos com evidencia
duplicada) foram corrigidos no validador; os testes do fim da parte A os fixam.

A regra 75 (canaleta no papel de amarracao) tem o seu proprio gate e os seus
testes em test_channel_never_bonds.py.

    python3 -m pytest tests/test_compensator_never_bonds.py -q
"""
import math
import os
import random
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import test_channel_reinforcement as tcr  # noqa: E402

m, ft, seg, solve = tcr.m, tcr.ft, tcr.seg, tcr.solve
from core.engine import opening_reinforcement as orf  # noqa: E402
from core.engine import wall_stepper as ws  # noqa: E402

gate = ws.compensator_as_junction_bond

COMP = ("C04", "C09")
PAPEL_DE_NO = ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION", "CORNER")
TIPOS_DE_NO = ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION")
LARGURA_CM = 14.0
CHANNEL = tcr.CHANNEL


def _cm(value_ft):
    return tcr._cm(value_ft)


def porta(lo_cm, hi_cm):
    return (ft(lo_cm), ft(hi_cm), ft(0.0), ft(221.0))


def janela(lo_cm, hi_cm, peitoril_cm=100.0, topo_cm=221.0):
    return (ft(lo_cm), ft(hi_cm), ft(peitoril_cm), ft(topo_cm))


# ------------------------------------------------------------------ fixtures
def canto():
    """L modular sem aberturas (bracos de 402 e 298 cm)."""
    return [seg(0, 0, 402, 0), seg(0, 0, 0, 298)], [[], []]


def tee_80():
    """O T modular dos testes vizinhos (tcr.tee, peitoril 80)."""
    return tcr.tee(sill_cm=80.0)


def cruz():
    """Duas paredes de 604 cm que se atravessam no meio (B54 de cruz nas duas)."""
    return [seg(0, 302, 604, 302), seg(302, 0, 302, 604)], [[], []]


_CACHE = {}


def _resolve(nome, lines, ops, strategy=CHANNEL, tag="padrao"):
    """Resolve uma vez por (nome, estrategia, tag). NUNCA mutar o que volta:
    os testes de validador trabalham numa copia (`_copia`)."""
    key = (nome, strategy, tag)
    if key not in _CACHE:
        res, walls, nodes, _o = solve(lines, ops, strategy=strategy)
        _CACHE[key] = (res, walls, nodes)
    return _CACHE[key]


def _base(nome):
    fabrica = {"canto": canto, "tee_80": tee_80, "cruz": cruz}[nome]
    return _resolve(nome, *fabrica())


def _copia(res):
    return dict((ci, [dict(c) for c in v]) for ci, v in res["course_candidates"].items())


# ------------------------------------------------------- geometria de apoio
def _eixo(walls, wi):
    line = walls[wi][0]
    p0, p1 = line.GetEndPoint(0), line.GetEndPoint(1)
    comp = line.Length
    return p0, (p1.X - p0.X) / comp, (p1.Y - p0.Y) / comp


def _t_do_no_cm(walls, wi, no):
    p0, ux, uy = _eixo(walls, wi)
    P = no["point"]
    return _cm((P.X - p0.X) * ux + (P.Y - p0.Y) * uy)


def _peca(walls, no, wi, code, a_cm, b_cm, reason="STANDARD_FILL", node_index=None):
    """Peca na parede `wi` cobrindo [a, b] cm ao longo da parede, medidos a
    partir da projecao do ponto do no' (negativo = antes do no')."""
    p0, ux, uy = _eixo(walls, wi)
    t = ft(_t_do_no_cm(walls, wi, no) + (a_cm + b_cm) / 2.0)
    return {"logical_code": code, "course": "A",
            "origin_world": m.XYZ(p0.X + ux * t, p0.Y + uy * t, 0.0),
            "x_dir": m.XYZ(ux, uy, 0.0), "y_dir": m.XYZ(-uy, ux, 0.0),
            "length_cm": float(b_cm - a_cm), "width_cm": LARGURA_CM,
            "wall_idx": wi, "node_index": node_index, "placement_reason": reason}


def _trecho(walls, no, wi, c):
    """Extensao (a, b) da peca ao longo da parede `wi`, relativa ao no' (cm)."""
    p0, ux, uy = _eixo(walls, wi)
    o = c["origin_world"]
    t = _cm((o.X - p0.X) * ux + (o.Y - p0.Y) * uy) - _t_do_no_cm(walls, wi, no)
    along = abs(c["x_dir"].X * ux + c["x_dir"].Y * uy) > 0.99
    h = (float(c["length_cm"]) if along else float(c.get("width_cm") or 0.0)) / 2.0
    return round(t - h, 6), round(t + h, 6)


def _monta(cc, ci, walls, nodes, ni, wi, fileira):
    """Na fiada `ci`, parede `wi`: tira as pecas que tocam o trecho de
    `fileira` e poe as pecas de `fileira` [(codigo, a, b[, razao, node_index])].
    Devolve as pecas novas, na ordem de `fileira`."""
    no = nodes[ni]
    lo = min(f[1] for f in fileira)
    hi = max(f[2] for f in fileira)
    mantidas = []
    for c in cc[ci]:
        if c.get("wall_idx") == wi:
            a, b = _trecho(walls, no, wi, c)
            if b > lo + 0.1 and a < hi - 0.1:
                continue
        mantidas.append(c)
    novas = [_peca(walls, no, wi, *f) for f in fileira]
    # nenhuma peca montada flutua fora da parede (um "valido" com o compensador
    # alem da ponta da parede passaria por vacuidade)
    t_no, comp = _t_do_no_cm(walls, wi, no), _cm(walls[wi][0].Length)
    for f in fileira:
        assert -1e-6 <= t_no + f[1] and t_no + f[2] <= comp + 1e-6, ("peca fora da parede", wi, f, comp)
    cc[ci] = mantidas + novas
    return novas


def _no(nodes, kind):
    idx = [i for i, n in enumerate(nodes) if n.get("kind") == kind]
    assert len(idx) == 1, (kind, [(i, n.get("kind")) for i, n in enumerate(nodes)])
    return idx[0]


def _pecas_de_no(cc, ni, prefixo):
    """[(fiada, peca)] com node_index == ni e razao comecando por `prefixo`."""
    out = []
    for ci in sorted(cc):
        for c in cc[ci]:
            if c.get("node_index") == ni and str(c.get("placement_reason") or "").startswith(prefixo):
                out.append((ci, c))
    return out


def _uma_peca_de_no(cc, ni, prefixo, wall_idx=None):
    achadas = [(ci, c) for ci, c in _pecas_de_no(cc, ni, prefixo)
               if wall_idx is None or c.get("wall_idx") == wall_idx]
    assert achadas, "a fixture precisa ter peca de no' %s" % prefixo
    return achadas[0]


def _assinatura(c):
    o = c["origin_world"]
    return (c["logical_code"], round(_cm(o.X), 6), round(_cm(o.Y), 6), c["length_cm"], c["width_cm"],
            round(c["x_dir"].X, 9), round(c["x_dir"].Y, 9), c.get("wall_idx"))


# ------------------------------------------ ORACULO independente (grade 0,5 cm)
def _paredes_do_no(no):
    out = set()
    for w, _e in no.get("arms") or []:
        out.add(w)
    for k in ("main_wall_idx", "incoming_wall_idx", "neighbor_wall_idx"):
        if no.get(k) is not None:
            out.add(no[k])
    for w in no.get("crossing_walls") or ():
        if w is not None:
            out.add(w)
    return sorted(out)


def _amostras(no, walls, passo=0.5):
    """Centros de celula (grade de `passo` cm) dentro de TODAS as faixas de
    espessura das paredes do no' - a regiao do no' por amostragem."""
    P = (_cm(no["point"].X), _cm(no["point"].Y))
    faixas = []
    for wi in _paredes_do_no(no):
        p0, ux, uy = _eixo(walls, wi)
        faixas.append(((-uy, ux), (_cm(p0.X), _cm(p0.Y)), _cm(walls[wi][1]) / 2.0))
    if len(faixas) < 2:
        return []
    R = 2.0 * max(h for _n, _q, h in faixas)
    n = int(round(2.0 * R / passo))
    pts = []
    for i in range(n):
        for j in range(n):
            X = (P[0] - R + (i + 0.5) * passo, P[1] - R + (j + 0.5) * passo)
            if all(abs((X[0] - q[0]) * nn[0] + (X[1] - q[1]) * nn[1]) <= h for nn, q, h in faixas):
                pts.append(X)
    return pts


def _local(c, X):
    o = c["origin_world"]
    rx, ry = X[0] - _cm(o.X), X[1] - _cm(o.Y)
    a = rx * c["x_dir"].X + ry * c["x_dir"].Y
    b = rx * c["y_dir"].X + ry * c["y_dir"].Y
    return abs(a) - float(c["length_cm"]) / 2.0, abs(b) - float(c.get("width_cm") or 0.0) / 2.0


def _conta(c, pts):
    return sum(1 for X in pts if max(_local(c, X)) < 0.0)


def _faixas(no, walls):
    """(normal unitaria, n.p0, meia espessura) de cada parede do no', em cm."""
    out = []
    for wi in _paredes_do_no(no):
        p0, ux, uy = _eixo(walls, wi)
        n = (-uy, ux)
        out.append((n, n[0] * _cm(p0.X) + n[1] * _cm(p0.Y), _cm(walls[wi][1]) / 2.0))
    return out


def _regiao_cm(no, walls):
    """Vertices (cm) da regiao do no': cruzamentos das bordas das faixas que
    ficam dentro de TODAS as faixas - construcao direta, sem recorte."""
    faixas = _faixas(no, walls)
    bordas = [(n, c + s * h) for n, c, h in faixas for s in (-1.0, 1.0)]
    pts = []
    for i, (n1, d1) in enumerate(bordas):
        for n2, d2 in bordas[i + 1:]:
            det = n1[0] * n2[1] - n1[1] * n2[0]
            if abs(det) < 1e-9:
                continue
            x = (d1 * n2[1] - d2 * n1[1]) / det
            y = (n1[0] * d2 - n2[0] * d1) / det
            if all(abs(n[0] * x + n[1] * y - c) <= h + 1e-6 for n, c, h in faixas) and \
                    all(math.hypot(x - p[0], y - p[1]) > 1e-6 for p in pts):
                pts.append((x, y))
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    return sorted(pts, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))


def _cantos_cm(c):
    o = c["origin_world"]
    hl, hw = float(c["length_cm"]) / 2.0, float(c.get("width_cm") or 0.0) / 2.0
    xd, yd = c["x_dir"], c["y_dir"]
    return [(_cm(o.X) + sx * hl * xd.X + sy * hw * yd.X, _cm(o.Y) + sx * hl * xd.Y + sy * hw * yd.Y)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def _dist_ponto_segmento(p, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    t = ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / (vx * vx + vy * vy)
    t = max(0.0, min(1.0, t))
    return math.hypot(p[0] - a[0] - t * vx, p[1] - a[1] - t * vy)


def _folga_cm(c, no, walls):
    """Distancia (cm) entre o retangulo da peca e a regiao do no' (0 se
    invade). Poligonos convexos separados: o minimo e' vertice x aresta."""
    if _conta(c, _amostras(no, walls)) > 0:
        return 0.0
    A, B = _cantos_cm(c), _regiao_cm(no, walls)
    return min(min(_dist_ponto_segmento(p, Q[i], Q[(i + 1) % len(Q)]) for i in range(len(Q)))
               for P, Q in ((A, B), (B, A)) for p in P)


def _perto(c, no, raio_cm):
    o = c["origin_world"]
    d = math.hypot(_cm(o.X - no["point"].X), _cm(o.Y - no["point"].Y))
    return d <= raio_cm + (float(c["length_cm"]) + float(c.get("width_cm") or 0.0)) / 2.0


def _designada(c):
    return (c.get("logical_code") in COMP and c.get("node_index") is not None
            and any(str(c.get("placement_reason") or "").startswith(p) for p in PAPEL_DE_NO))


def _chave(ci, c):
    o = c["origin_world"]
    return (ci, c["logical_code"], round(_cm(o.X), 1), round(_cm(o.Y), 1))


def _chave_v(v):
    return (v["course_index"], v["logical_code"], round(v["origin_cm"][0], 1), round(v["origin_cm"][1], 1))


def oraculo(cc, nodes, walls):
    """O que o gate TEM de acusar, calculado sem o codigo do gate: designados
    (metadado) + compensadores que sao o maior ocupante (contagem de amostras)
    da regiao de algum no' L/T/X. EMPATE de area: todo compensador entre os
    lideres e' acusado (divide a funcao - o veredito nunca depende do codigo da
    outra peca); o empate fica registrado so' para a mensagem. A contagem e'
    exata para pecas alinhadas aos eixos com faces em multiplos de 0,5 cm (os
    centros de celula caem entre as faces). Devolve (esperado{chave:
    evidencias}, empates, amostras_por_no)."""
    esperado = {}
    for ci in sorted(cc):
        for c in cc[ci]:
            if _designada(c):
                esperado.setdefault(_chave(ci, c), set()).add("DESIGNATED_NODE_PIECE")
    empates = []
    amostras = {}
    for ni, no in enumerate(nodes):
        if no.get("kind") not in TIPOS_DE_NO:
            continue
        pts = _amostras(no, walls)
        if not pts:
            continue
        amostras[ni] = pts
        paredes = set(_paredes_do_no(no))
        for ci in sorted(cc):
            contagem = [(_conta(c, pts), c) for c in cc[ci]
                        if c.get("wall_idx") in paredes and _perto(c, no, 20.0)]
            contagem = [(k, c) for k, c in contagem if k > 0]
            if not contagem:
                continue
            topo = max(k for k, _c in contagem)
            lideres = [c for k, c in contagem if k == topo]
            if len(lideres) > 1:
                empates.append((ci, ni, sorted(c["logical_code"] for c in lideres)))
            for c in lideres:
                if c["logical_code"] in COMP:
                    esperado.setdefault(_chave(ci, c), set()).add("OCCUPIES_NODE_REGION")
    return esperado, empates, amostras


def _resumo(nome, cc, nodes, walls, violacoes, esperado, empates, amostras):
    """Texto para a mensagem do assert: o que o motor pos e o que o gate viu."""
    por_razao = {}
    perto = []
    acusadas = set(_chave_v(v) for v in violacoes)
    for ci in sorted(cc):
        for c in cc[ci]:
            if c.get("logical_code") not in COMP:
                continue
            k = (c["logical_code"], str(c.get("placement_reason")))
            por_razao[k] = por_razao.get(k, 0) + 1
            if _chave(ci, c) in acusadas:
                continue
            for ni in sorted(amostras):
                if c.get("wall_idx") in _paredes_do_no(nodes[ni]) and _perto(c, nodes[ni], 15.0):
                    g = _folga_cm(c, nodes[ni], walls)
                    if g <= 12.0:
                        perto.append((ci, ni, c["logical_code"], c.get("placement_reason"), round(g, 2)))
    ev = {}
    for v in violacoes:
        for e in v["evidence"]:
            ev[e] = ev.get(e, 0) + 1
    return ("%s: compensadores por (codigo, razao)=%s | acusados=%d evidencias=%s | esperados pelo "
            "oraculo=%d | empates=%s | compensadores a <=12 cm da regiao NAO acusados (fiada, no', "
            "codigo, razao, folga_cm)=%s" % (
                nome, sorted(por_razao.items()), len(violacoes), sorted(ev.items()), len(esperado),
                empates, perto))


# =========================================================================
# A) NIVEL VALIDADOR - candidatos montados sobre nodes/walls reais do motor
# =========================================================================
@pytest.mark.parametrize("nome", ["canto", "tee_80", "cruz"])
def test_controle_fixtures_base_nao_tem_violacao(nome):
    """Controle: com as amarracoes do motor intactas o gate e' vazio (senao os
    mutantes abaixo nao provariam nada)."""
    res, walls, nodes = _base(nome)
    assert gate(res["course_candidates"], nodes, walls) == []
    assert any(_pecas_de_no(res["course_candidates"], ni, p) for ni in range(len(nodes)) for p in PAPEL_DE_NO)


# ------------------------------------------------------------------ 1. L
@pytest.mark.parametrize("familia,codigo", [(0, "C09"), (1, "C09"), (0, "C04"), (1, "C04")])
def test_L_invalido_compensador_no_lugar_do_b34_de_canto_acusa_por_geometria(familia, codigo):
    """Item 1: tira o B34 L_CORNER de uma fiada e poe o compensador NO LUGAR
    dele (a partir da face externa do canto), SEM razao de no' e sem
    node_index. O gate acusa pela GEOMETRIA: metadado nao e' necessario."""
    res, walls, nodes = _base("canto")
    ni = _no(nodes, "L_CORNER")
    cc = _copia(res)
    # uma fiada de cada familia: a primeira em que cada braco tem o B34
    fiadas = sorted(set((c.get("wall_idx"), ci) for ci, c in _pecas_de_no(cc, ni, "L_CORNER")))
    por_parede = {}
    for wi, ci in fiadas:
        por_parede.setdefault(wi, ci)
    wi = sorted(por_parede)[familia]
    ci = por_parede[wi]
    _ci, b34 = _uma_peca_de_no({ci: cc[ci]}, ni, "L_CORNER", wall_idx=wi)
    assert b34["logical_code"] == "B34"
    a, _b = _trecho(walls, nodes[ni], wi, b34)
    comp = float(codigo[1:])
    _monta(cc, ci, walls, nodes, ni, wi, [(codigo, a, a + comp)])
    violacoes = gate(cc, nodes, walls)
    assert len(violacoes) == 1, violacoes
    v = violacoes[0]
    assert v["logical_code"] == codigo and v["course_index"] == ci
    assert v["evidence"] == ["OCCUPIES_NODE_REGION"]
    assert v["placement_reason"] == "STANDARD_FILL"
    assert v["node_index"] == ni and v["node_kind"] == "L_CORNER"
    assert v["coverage"] == round(comp / LARGURA_CM, 4)


def test_L_valido_canto_intacto_e_c09_encostado_fora_da_regiao():
    """Item 2: o B34 de canto continua la'; um C09 de ajuste encostado nele
    (junta de 1 cm, fora da regiao do no') e outro encostado na face do canto,
    no outro braco -> nada e' acusado."""
    res, walls, nodes = _base("canto")
    ni = _no(nodes, "L_CORNER")
    cc = _copia(res)
    ci, b34 = _uma_peca_de_no(cc, ni, "L_CORNER")
    wi = b34["wall_idx"]
    wj = [w for w in _paredes_do_no(nodes[ni]) if w != wi][0]
    _a, b = _trecho(walls, nodes[ni], wi, b34)
    # [B34 de canto][C09][B39] no braco do canto
    _monta(cc, ci, walls, nodes, ni, wi, [("C09", b + 1.0, b + 10.0), ("B39", b + 11.0, b + 50.0)])
    # no outro braco, o C09 comeca a 1 cm da face do canto
    novas = _monta(cc, ci, walls, nodes, ni, wj, [("C09", 8.0, 17.0), ("B39", 18.0, 57.0)])
    assert _folga_cm(novas[0], nodes[ni], walls) == pytest.approx(1.0)
    assert gate(cc, nodes, walls) == []


# ------------------------------------------------------------------ 3. T
@pytest.mark.parametrize("papel,codigo", [
    ("T_INTERSECTION_MAIN", "C09"), ("T_INTERSECTION_MAIN", "C04"),
    ("T_INTERSECTION_INCOMING", "C09"), ("T_INTERSECTION_INCOMING", "C04"),
])
def test_T_invalido_compensador_no_lugar_da_amarracao_acusa(papel, codigo):
    """Item 3: troca a amarracao do T (B54 da principal ou B34 da que chega)
    por C04/C09 na regiao do no', sem metadado -> acusa por geometria."""
    res, walls, nodes = _base("tee_80")
    ni = _no(nodes, "T_INTERSECTION")
    cc = _copia(res)
    ci, peca = _uma_peca_de_no(cc, ni, papel)
    wi = peca["wall_idx"]
    a, b = _trecho(walls, nodes[ni], wi, peca)
    comp = float(codigo[1:])
    if papel == "T_INTERSECTION_MAIN":
        assert peca["logical_code"] == "B54" and a < 0.0 < b
        fileira = [(codigo, -comp / 2.0, comp / 2.0)]          # centrado no no', como o B54
    else:
        assert peca["logical_code"] == "B34"
        fileira = [(codigo, a, a + comp)]                        # da face oposta da principal
    _monta(cc, ci, walls, nodes, ni, wi, fileira)
    violacoes = gate(cc, nodes, walls)
    assert [(v["course_index"], v["logical_code"], v["evidence"]) for v in violacoes] == \
        [(ci, codigo, ["OCCUPIES_NODE_REGION"])]
    assert violacoes[0]["node_kind"] == "T_INTERSECTION"
    assert violacoes[0]["coverage"] == round(comp / LARGURA_CM, 4)


def test_T_valido_amarracao_preservada_e_c09_fechando_comprimento():
    """Item 4: [B54 de amarracao][C09][B39] na principal e, na fiada do B34 da
    que chega, C09/C04 encostados nas faces do no' -> nada e' acusado."""
    res, walls, nodes = _base("tee_80")
    ni = _no(nodes, "T_INTERSECTION")
    cc = _copia(res)
    ci0, b54 = _uma_peca_de_no(cc, ni, "T_INTERSECTION_MAIN")
    main = b54["wall_idx"]
    _a, b = _trecho(walls, nodes[ni], main, b54)
    _monta(cc, ci0, walls, nodes, ni, main, [("C09", b + 1.0, b + 10.0), ("B39", b + 11.0, b + 50.0)])
    ci1, _b34 = _uma_peca_de_no(cc, ni, "T_INTERSECTION_INCOMING")
    c09, _b39 = _monta(cc, ci1, walls, nodes, ni, main, [("C09", 8.0, 17.0), ("B39", 18.0, 57.0)])
    _b39, c04 = _monta(cc, ci1, walls, nodes, ni, main, [("B39", -52.0, -13.0), ("C04", -12.0, -8.0)])
    # nao-vacuidade: os dois compensadores estao encostados (1 cm) na regiao do no'
    assert _folga_cm(c09, nodes[ni], walls) == pytest.approx(1.0)
    assert _folga_cm(c04, nodes[ni], walls) == pytest.approx(1.0)
    assert gate(cc, nodes, walls) == []


# ------------------------------------------------------------- 5/6. cruz
def _fiadas_da_cruz(cc, ni):
    por_parede = {}
    for ci, c in _pecas_de_no(cc, ni, "X_INTERSECTION"):
        por_parede.setdefault(c["wall_idx"], (ci, c))
    assert len(por_parede) == 2, "a cruz precisa do B54 de cruz nas DUAS paredes"
    return [por_parede[w] for w in sorted(por_parede)]


@pytest.mark.parametrize("parede,codigo", [(0, "C09"), (1, "C09"), (0, "C04"), (1, "C04")])
def test_cruz_invalida_compensador_no_lugar_do_b54_de_cruz_acusa(parede, codigo):
    """Item 5: troca o B54 de cruz (X_INTERSECTION) por C04/C09 centrado no
    cruzamento -> acusa por geometria."""
    res, walls, nodes = _base("cruz")
    ni = _no(nodes, "X_INTERSECTION")
    cc = _copia(res)
    ci, b54 = _fiadas_da_cruz(cc, ni)[parede]
    assert b54["logical_code"] == "B54"
    comp = float(codigo[1:])
    _monta(cc, ci, walls, nodes, ni, b54["wall_idx"], [(codigo, -comp / 2.0, comp / 2.0)])
    violacoes = gate(cc, nodes, walls)
    assert [(v["course_index"], v["logical_code"], v["evidence"], v["node_kind"]) for v in violacoes] == \
        [(ci, codigo, ["OCCUPIES_NODE_REGION"], "X_INTERSECTION")]


def test_cruz_valida_b54_de_cruz_e_c09_encostado():
    """Item 6: B54 de cruz intacto + [C09][B39] depois dele e C09 encostado na
    face do cruzamento na outra parede -> nada e' acusado."""
    res, walls, nodes = _base("cruz")
    ni = _no(nodes, "X_INTERSECTION")
    cc = _copia(res)
    for ci, b54 in _fiadas_da_cruz(cc, ni):
        wi = b54["wall_idx"]
        wj = [w for w in _paredes_do_no(nodes[ni]) if w != wi][0]
        _a, b = _trecho(walls, nodes[ni], wi, b54)
        _monta(cc, ci, walls, nodes, ni, wi, [("C09", b + 1.0, b + 10.0), ("B39", b + 11.0, b + 50.0)])
        (c09,) = _monta(cc, ci, walls, nodes, ni, wj, [("C09", 8.0, 17.0)])
        (c04,) = _monta(cc, ci, walls, nodes, ni, wj, [("C04", -12.0, -8.0)])
        # nao-vacuidade: encostados (1 cm) nas duas faces do cruzamento
        assert _folga_cm(c09, nodes[ni], walls) == pytest.approx(1.0)
        assert _folga_cm(c04, nodes[ni], walls) == pytest.approx(1.0)
    assert gate(cc, nodes, walls) == []


# ------------------------------------------------ 7. O TESTE MAIS IMPORTANTE
def _detector_por_distancia(cc, walls, nodes, ni, raio_cm):
    """O detector ERRADO que a regra 76 proibe: compensador cuja ponta mais
    proxima fica a ate' `raio_cm` do ponto do no', medido ao longo da parede."""
    out = []
    for ci in sorted(cc):
        for c in cc[ci]:
            if c.get("logical_code") in COMP and c.get("wall_idx") in _paredes_do_no(nodes[ni]):
                a, b = _trecho(walls, nodes[ni], c["wall_idx"], c)
                d = 0.0 if a <= 0.0 <= b else min(abs(a), abs(b))
                if d <= raio_cm:
                    out.append((ci, c["logical_code"], d))
    return out


def test_A_x_B_mesmo_c09_na_mesma_posicao_so_a_funcao_decide():
    """Item 7 (o mais importante), forma estrita: o MESMO C09 (dicionario
    identico: codigo, centro, dimensoes, parede) na MESMA distancia do no'.
      A: [B54 funcional][C09][B39] - o B54 segura a regiao do no', o C09 so'
         fecha comprimento (entra 3 cm na regiao, mas o B54 cobre 10 cm)  -> valido;
      B: o B54 sai; o C09, no MESMO lugar, vira o que ocupa a regiao do no',
         o lugar da amarracao                                           -> invalido.
    Se o gate nao separar A de B, o validador esta' errado."""
    res, walls, nodes = _base("tee_80")
    ni = _no(nodes, "T_INTERSECTION")
    ci, b54 = _uma_peca_de_no(_copia(res), ni, "T_INTERSECTION_MAIN")
    main = b54["wall_idx"]

    cc_a = _copia(res)
    a_b54, c09_a, _b39 = _monta(cc_a, ci, walls, nodes, ni, main, [
        ("B54", -51.0, 3.0, "T_INTERSECTION_MAIN", ni), ("C09", 4.0, 13.0), ("B39", 14.0, 53.0)])
    assert a_b54["length_cm"] == b54["length_cm"] == 54.0      # o B54 de A tem o tamanho do B54 real
    # A sem nenhum metadado no B54: o veredito de A vem da GEOMETRIA, nao da razao do B54
    cc_a_sem_razao = _copia(res)
    _monta(cc_a_sem_razao, ci, walls, nodes, ni, main, [
        ("B54", -51.0, 3.0), ("C09", 4.0, 13.0), ("B39", 14.0, 53.0)])
    cc_b = _copia(res)
    _b39l, c09_b, _b39r = _monta(cc_b, ci, walls, nodes, ni, main, [
        ("B39", -47.0, -8.0), ("C09", 4.0, 13.0), ("B39", 14.0, 53.0)])

    # mesmo C09, mesma distancia ao no', mesma invasao da regiao
    assert _assinatura(c09_a) == _assinatura(c09_b)
    assert _detector_por_distancia(cc_a, walls, nodes, ni, 5.0) == \
        _detector_por_distancia(cc_b, walls, nodes, ni, 5.0) == [(ci, "C09", 4.0)]
    pts = _amostras(nodes[ni], walls)
    assert _conta(c09_a, pts) == _conta(c09_b, pts) > 0
    assert _conta(a_b54, pts) > _conta(c09_a, pts)
    # em B nada alem do C09 toca a regiao do no' (a amarracao sumiu mesmo)
    assert [c["logical_code"] for c in cc_b[ci] if _conta(c, pts) > 0] == ["C09"]

    assert gate(cc_a, nodes, walls) == []
    assert gate(cc_a_sem_razao, nodes, walls) == []
    violacoes = gate(cc_b, nodes, walls)
    assert [(v["course_index"], v["logical_code"], v["evidence"]) for v in violacoes] == \
        [(ci, "C09", ["OCCUPIES_NODE_REGION"])]
    assert violacoes[0]["coverage"] == round(3.0 / LARGURA_CM, 4)


def test_A_x_B_b54_c09_b39_valido_e_c09_no_lugar_do_b54_invalido():
    """Item 7, forma literal do usuario, com o B54 centrado de verdade:
      A: [B54 de amarracao][C09 de ajuste][B39]  -> valido;
      B: C09 ocupando o lugar do B54             -> invalido.
    O MESMO C09 (codigo e dimensoes) esta' "perto do no'" nos dois: um detector
    por distancia (raio de 30 cm) acusa A e B - o gate funcional so' acusa B."""
    res, walls, nodes = _base("tee_80")
    ni = _no(nodes, "T_INTERSECTION")
    ci, b54 = _uma_peca_de_no(_copia(res), ni, "T_INTERSECTION_MAIN")
    main = b54["wall_idx"]
    a, b = _trecho(walls, nodes[ni], main, b54)
    assert (a, b) == (-27.0, 27.0)

    cc_a = _copia(res)
    (c09_a, _b39) = _monta(cc_a, ci, walls, nodes, ni, main,
                           [("C09", b + 1.0, b + 10.0), ("B39", b + 11.0, b + 50.0)])
    cc_b = _copia(res)
    (c09_b,) = _monta(cc_b, ci, walls, nodes, ni, main, [("C09", -4.5, 4.5)])
    # A: o B54 de amarracao continua la' e e' o unico na regiao; o C09 so' encosta nele.
    # B: o C09 e' o unico na regiao. Sem isto o "valido" de A poderia ser vazio.
    pts = _amostras(nodes[ni], walls)
    assert [(c["logical_code"], c.get("placement_reason")) for c in cc_a[ci] if _conta(c, pts) > 0] == \
        [("B54", "T_INTERSECTION_MAIN")]
    assert _conta(c09_a, pts) == 0
    assert [c["logical_code"] for c in cc_b[ci] if _conta(c, pts) > 0] == ["C09"]
    assert (c09_a["logical_code"], c09_a["length_cm"]) == (c09_b["logical_code"], c09_b["length_cm"])

    ingenuo_a = _detector_por_distancia(cc_a, walls, nodes, ni, 30.0)
    ingenuo_b = _detector_por_distancia(cc_b, walls, nodes, ni, 30.0)
    assert [x[:2] for x in ingenuo_a] == [x[:2] for x in ingenuo_b] == [(ci, "C09")]

    assert gate(cc_a, nodes, walls) == []
    violacoes = gate(cc_b, nodes, walls)
    assert [(v["course_index"], v["logical_code"], v["evidence"]) for v in violacoes] == \
        [(ci, "C09", ["OCCUPIES_NODE_REGION"])]


# ------------------------------------------------------- 8. so' metadado
def test_so_metadado_c09_designado_fora_da_regiao_acusa():
    """Item 8: C09 com node_index + razao L_CORNER_DEGRADED, mas FORA da regiao
    do no' (o B34 de canto continua la') -> acusado so' pelo METADADO. O mesmo
    C09 sem o metadado nao e' acusado (controle)."""
    res, walls, nodes = _base("canto")
    ni = _no(nodes, "L_CORNER")
    ci, b34 = _uma_peca_de_no(_copia(res), ni, "L_CORNER")
    wj = [w for w in _paredes_do_no(nodes[ni]) if w != b34["wall_idx"]][0]

    cc = _copia(res)
    _monta(cc, ci, walls, nodes, ni, wj, [("C09", 8.0, 17.0, "L_CORNER_DEGRADED", ni)])
    violacoes = gate(cc, nodes, walls)
    assert len(violacoes) == 1
    v = violacoes[0]
    assert v["evidence"] == ["DESIGNATED_NODE_PIECE"]
    assert v["coverage"] is None
    assert (v["node_index"], v["node_kind"], v["placement_reason"]) == (ni, "L_CORNER", "L_CORNER_DEGRADED")

    controle = _copia(res)
    _monta(controle, ci, walls, nodes, ni, wj, [("C09", 8.0, 17.0)])
    assert gate(controle, nodes, walls) == []


# ------------------------------------------------------- 9. escopo: canaleta
def test_canaleta_na_regiao_nao_e_escopo_da_regra_76():
    """Item 9: CHANNEL_U_34 no lugar do B34 de canto (mesma geometria, com e
    sem razao de no') NAO e' acusada por ESTE gate - canaleta e' da regra 75,
    cujo gate acusa a peca com papel de no'. Um C09 que invade menos que a
    canaleta tambem nao e' acusado: ele nao e' o ocupante."""
    res, walls, nodes = _base("canto")
    ni = _no(nodes, "L_CORNER")
    ci, b34 = _uma_peca_de_no(_copia(res), ni, "L_CORNER")
    wi = b34["wall_idx"]
    wj = [w for w in _paredes_do_no(nodes[ni]) if w != wi][0]
    a, b = _trecho(walls, nodes[ni], wi, b34)

    cc = _copia(res)
    _monta(cc, ci, walls, nodes, ni, wi, [(orf.CHANNEL_U_34, a, b, "L_CORNER", ni)])
    assert gate(cc, nodes, walls) == []
    assert orf.channel_as_junction_bond(cc, None), "a regra 75 e' quem acusa a canaleta"

    sem_razao = _copia(res)
    (canaleta,) = _monta(sem_razao, ci, walls, nodes, ni, wi, [(orf.CHANNEL_U_34, a, b)])
    (c09,) = _monta(sem_razao, ci, walls, nodes, ni, wj, [("C09", 6.0, 15.0)])   # entra 1 cm na regiao
    pts = _amostras(nodes[ni], walls)
    assert 0 < _conta(c09, pts) < _conta(canaleta, pts)
    assert gate(sem_razao, nodes, walls) == []


# ------------------------------------------------------ 10. determinismo
def _cc_com_tres_evidencias():
    res, walls, nodes = _base("tee_80")
    ni = _no(nodes, "T_INTERSECTION")
    cc = _copia(res)
    ci0, b54 = _uma_peca_de_no(cc, ni, "T_INTERSECTION_MAIN")
    main = b54["wall_idx"]
    _monta(cc, ci0, walls, nodes, ni, main, [("C09", -4.5, 4.5)])                     # geometria
    fiadas_b34 = _pecas_de_no(cc, ni, "T_INTERSECTION_INCOMING")
    ci1, b34 = fiadas_b34[0]
    a, _b = _trecho(walls, nodes[ni], b34["wall_idx"], b34)
    _monta(cc, ci1, walls, nodes, ni, b34["wall_idx"],
           [("C04", a, a + 4.0, "T_INTERSECTION_INCOMING_DEGRADED", ni)])              # as duas
    ci2 = fiadas_b34[1][0]
    _monta(cc, ci2, walls, nodes, ni, main,
           [("C09", 8.0, 17.0, "T_INTERSECTION_MAIN_DEGRADED", ni)])                   # so' metadado
    _monta(cc, ci2, walls, nodes, ni, main, [("C09", -17.0, -8.0)])                     # ajuste valido
    return cc, nodes, walls


def _foto(cc):
    return dict((ci, [(id(c), _assinatura(c), c.get("placement_reason"), c.get("node_index")) for c in v])
                for ci, v in cc.items())


def test_deterministico_somente_leitura_e_independente_da_ordem():
    """Item 10: mesma entrada -> mesma lista; o gate nao muda a entrada; pecas
    embaralhadas (e copiadas, ids novos) e fiadas em outra ordem -> mesma lista."""
    cc, nodes, walls = _cc_com_tres_evidencias()
    antes = _foto(cc)
    primeira = gate(cc, nodes, walls)
    assert _foto(cc) == antes
    assert gate(cc, nodes, walls) == primeira
    assert sorted(tuple(v["evidence"]) for v in primeira) == [
        ("DESIGNATED_NODE_PIECE",), ("DESIGNATED_NODE_PIECE", "OCCUPIES_NODE_REGION"),
        ("OCCUPIES_NODE_REGION",)]
    for semente in range(8):
        rng = random.Random(semente)
        fiadas = list(cc)
        rng.shuffle(fiadas)
        embaralhado = {}
        for ci in fiadas:
            pecas = [dict(c) for c in cc[ci]]
            rng.shuffle(pecas)
            embaralhado[ci] = pecas
        assert gate(embaralhado, nodes, walls) == primeira, semente


# ------------------------------------------ 11. area coberta, nao distancia
def test_nao_e_detector_por_distancia_o_criterio_e_a_area_coberta():
    """Item 11:
      (a) C09 a 0,5 cm da face do no' (encostado, fora da regiao) -> 0;
      (b) C09 que entra 1 cm na regiao, com o B54 cobrindo 12 cm -> 0;
      (c) o MESMO C09, mas a outra peca cobre so' 0,5 cm -> o C09 e' o maior
          ocupante -> acusa, com cobertura 1/14;
      (d) o MESMO C09 sozinho na regiao -> acusa, cobertura 1/14."""
    res, walls, nodes = _base("tee_80")
    ni = _no(nodes, "T_INTERSECTION")
    pts = _amostras(nodes[ni], walls)
    ci0, b54 = _uma_peca_de_no(_copia(res), ni, "T_INTERSECTION_MAIN")
    ci1, _b34 = _uma_peca_de_no(_copia(res), ni, "T_INTERSECTION_INCOMING")
    main = b54["wall_idx"]

    cc = _copia(res)
    (c09,) = _monta(cc, ci1, walls, nodes, ni, main, [("C09", 7.5, 16.5)])
    assert _folga_cm(c09, nodes[ni], walls) == pytest.approx(0.5)
    assert gate(cc, nodes, walls) == []

    def cenario(esquerda):
        cc = _copia(res)
        novas = _monta(cc, ci0, walls, nodes, ni, main, esquerda + [("C09", 6.0, 15.0), ("B39", 16.0, 55.0)])
        return cc, novas

    cc_b, (b54_b, c09_b, _r) = cenario([("B54", -49.0, 5.0, "T_INTERSECTION_MAIN", ni)])
    assert _conta(c09_b, pts) > 0 and _conta(b54_b, pts) > _conta(c09_b, pts)
    assert gate(cc_b, nodes, walls) == []

    cc_c, (b19_c, c09_c, _r) = cenario([("B19", -25.5, -6.5)])
    assert 0 < _conta(b19_c, pts) < _conta(c09_c, pts)
    cc_d, (_l, c09_d, _r) = cenario([("B39", -47.0, -8.0)])
    assert _assinatura(c09_b) == _assinatura(c09_c) == _assinatura(c09_d)
    for caso in (cc_c, cc_d):
        violacoes = gate(caso, nodes, walls)
        assert [(v["course_index"], v["logical_code"], v["evidence"]) for v in violacoes] == \
            [(ci0, "C09", ["OCCUPIES_NODE_REGION"])]
        assert violacoes[0]["coverage"] == round(1.0 / LARGURA_CM, 4)


# ------------------------- defeitos do VALIDADOR (encontrados aqui, corrigidos)
def test_empate_de_area_nao_pode_depender_do_nome_da_outra_peca():
    """C09 e a outra peca cobrindo exatamente a mesma area da regiao (1 cm
    cada, nas duas pontas). O veredito sobre o C09 tem de ser o mesmo qualquer
    que seja o CODIGO da outra peca. Antes da correcao nao era: o desempate era
    `(-cobertura, codigo, x, y)`. Agora, num empate, o compensador divide a
    funcao e e' acusado nos dois casos."""
    res, walls, nodes = _base("tee_80")
    ni = _no(nodes, "T_INTERSECTION")
    ci0, b54 = _uma_peca_de_no(_copia(res), ni, "T_INTERSECTION_MAIN")
    main = b54["wall_idx"]
    pts = _amostras(nodes[ni], walls)
    veredito = {}
    for outra in ("B19", orf.CHANNEL_U_19):
        cc = _copia(res)
        esquerda, c09 = _monta(cc, ci0, walls, nodes, ni, main, [(outra, -25.0, -6.0), ("C09", 6.0, 15.0)])
        assert _conta(esquerda, pts) == _conta(c09, pts) > 0          # empate exato
        violacoes = gate(cc, nodes, walls)
        veredito[outra] = [v["logical_code"] for v in violacoes]
        # o oraculo do item 13 modela o empate do mesmo jeito (senao ele divergiria do gate)
        esperado, empates, _am = oraculo(cc, nodes, walls)
        assert empates == [(ci0, ni, sorted([outra, "C09"]))]
        assert dict((_chave_v(v), set(v["evidence"])) for v in violacoes) == esperado
    assert veredito["B19"] == veredito[orf.CHANNEL_U_19] == ["C09"], veredito


def test_compensador_ocupando_dois_nos_nao_duplica_evidencia():
    """Dois T na mesma principal a 10 cm um do outro (paredes que chegam
    desalinhadas, comum em projeto real). Um C09 cobrindo a sobreposicao das
    duas regioes e' o ocupante das duas: UMA violacao, evidencia sem repeticao,
    e os DOIS nos no laudo (`occupied_nodes`)."""
    lines = [seg(-302, 0, 302, 0), seg(0, 0, 0, 298), seg(10, 0, 10, -298)]
    res, walls, nodes = _resolve("dois_T_a_10cm", lines, [[], [], []])
    tees = sorted((i for i, n in enumerate(nodes) if n.get("kind") == "T_INTERSECTION"),
                  key=lambda i: nodes[i]["point"].X)
    assert len(tees) == 2   # o de x=0 primeiro, o de x=10 depois
    principal = sorted(set(_paredes_do_no(nodes[tees[0]])) & set(_paredes_do_no(nodes[tees[1]])))[0]
    cc = _copia(res)
    ci = sorted(cc)[0]
    cc[ci] = [c for c in cc[ci] if c.get("wall_idx") not in _paredes_do_no(nodes[tees[0]]) +
              _paredes_do_no(nodes[tees[1]])]
    (c09,) = _monta(cc, ci, walls, nodes, tees[0], principal, [("C09", 0.5, 9.5)])
    for ni in tees:
        assert _conta(c09, _amostras(nodes[ni], walls)) > 0
    violacoes = gate(cc, nodes, walls)
    assert len(violacoes) == 1
    assert len(set(violacoes[0]["evidence"])) == len(violacoes[0]["evidence"]), violacoes
    assert sorted(o["node_index"] for o in violacoes[0]["occupied_nodes"]) == sorted(tees), violacoes
    assert violacoes[0]["node_index"] in tees


# =========================================================================
# B) NIVEL SOLVER - consistencia do gate, sem apostar na correcao futura
# =========================================================================
# Fixtures em que o motor DEGRADA o no' para compensador com a regra 76
# desligada no motor (o comportamento medido no BUTANTA antes da correcao).
DEGRADAM = {
    # braco de 298 cm com porta a 23 cm do ponto do no' (16 cm da face)
    "L_braco_curto_ate_porta": ([seg(0, 0, 402, 0), seg(0, 0, 0, 298)], [[], [porta(30.0, 120.0)]]),
    # braco inteiro de 25 cm
    "L_braco_curto": ([seg(0, 0, 402, 0), seg(0, 0, 0, 25)], [[], []]),
    # boneca de 13 cm entre a face da principal e a porta da parede que chega
    "T_boneca_curta": ([seg(-302, 0, 302, 0), seg(0, 0, 0, 298)], [[], [porta(27.0, 117.0)]]),
    # parede que chega com 20 cm
    "T_parede_que_chega_curta": ([seg(-302, 0, 302, 0), seg(0, 0, 0, 20)], [[], []]),
}


@pytest.fixture
def motor_de_hoje(monkeypatch):
    """Fixa o motor no comportamento que DEGRADA o no' para compensador: a
    flag da regra 76 no motor (wall_stepper) e qualquer ligacao dela no fluxo
    CHANNEL (wall_modeling, nome com COMPENSATOR_NEVER...BOND) desligadas. Nao
    aposta na correcao: so' reproduz o defeito medido para provar o gate."""
    monkeypatch.setattr(ws, "COMPENSATOR_NEVER_JUNCTION_BOND", False)
    for nome in dir(m):
        if "COMPENSATOR_NEVER" in nome and "BOND" in nome and isinstance(getattr(m, nome), bool):
            monkeypatch.setattr(m, nome, False)


def _compensadores(cc):
    return [(ci, c) for ci in sorted(cc) for c in cc[ci] if c.get("logical_code") in COMP]


@pytest.mark.parametrize("estrategia", [None, CHANNEL], ids=["legado", "CHANNEL"])
@pytest.mark.parametrize("nome", sorted(DEGRADAM))
def test_solver_todo_compensador_designado_e_acusado_e_fill_fora_do_no_nao(nome, estrategia, motor_de_hoje):
    """Item 12: onde o motor hoje designa um compensador PECA DO NO', o gate
    acusa (DESIGNATED -> sempre acusado); nenhum compensador de preenchimento
    comum (STANDARD_FILL/OPENING_REPAIR_FILL) fora da regiao do no' e' acusado."""
    lines, ops = DEGRADAM[nome]
    res, walls, nodes = _resolve(nome, lines, ops, strategy=estrategia, tag="motor_de_hoje")
    cc = res["course_candidates"]
    violacoes = gate(cc, nodes, walls)
    acusadas = dict((_chave_v(v), v) for v in violacoes)
    esperado, empates, amostras = oraculo(cc, nodes, walls)
    msg = _resumo(nome, cc, nodes, walls, violacoes, esperado, empates, amostras)

    designados = [(ci, c) for ci, c in _compensadores(cc) if _designada(c)]
    assert designados, "a fixture deixou de degradar o no' para compensador - " + msg
    for ci, c in designados:
        v = acusadas.get(_chave(ci, c))
        assert v is not None and "DESIGNATED_NODE_PIECE" in v["evidence"], msg

    for ci, c, _folga in _preenchimento_fora_da_regiao(cc, nodes, walls, amostras):
        assert _chave(ci, c) not in acusadas, msg
    if "compensator_as_junction_bond" in res:     # a ligacao no resultado usa o mesmo gate
        assert res["compensator_as_junction_bond"] == violacoes


def _preenchimento_fora_da_regiao(cc, nodes, walls, amostras):
    """[(fiada, peca, folga_cm ate' a regiao mais proxima)] dos compensadores
    NAO designados que nao entram na regiao de nenhum no' (folga None = a peca
    nao e' de parede de no' L/T/X)."""
    out = []
    for ci, c in _compensadores(cc):
        if _designada(c):
            continue
        dos_nos = [ni for ni in amostras if c.get("wall_idx") in _paredes_do_no(nodes[ni])]
        if any(_conta(c, amostras[ni]) > 0 for ni in dos_nos if _perto(c, nodes[ni], 20.0)):
            continue
        out.append((ci, c, min(_folga_cm(c, nodes[ni], walls) for ni in dos_nos) if dos_nos else None))
    return out


def test_solver_item_12_exercita_preenchimento_encostado_no_no(motor_de_hoje):
    """Nao-vacuidade do item 12: a metade "preenchimento fora do no' nao e'
    acusado" so' prova algo se houver compensador comum ENCOSTADO no no' (ate'
    3 cm da regiao). Nem toda fixture tem um (ha' fixture sem compensador comum
    nenhum e fixture com eles longe do no'); o conjunto tem de ter pelo menos um."""
    achados = []
    for nome in sorted(DEGRADAM):
        for estrategia in (None, CHANNEL):
            lines, ops = DEGRADAM[nome]
            res, walls, nodes = _resolve(nome, lines, ops, strategy=estrategia, tag="motor_de_hoje")
            cc = res["course_candidates"]
            acusadas = set(_chave_v(v) for v in gate(cc, nodes, walls))
            _e, _emp, amostras = oraculo(cc, nodes, walls)
            for ci, c, folga in _preenchimento_fora_da_regiao(cc, nodes, walls, amostras):
                if folga is not None and folga <= 3.0:
                    assert _chave(ci, c) not in acusadas
                    achados.append((nome, estrategia, ci, c["logical_code"], c.get("placement_reason"),
                                    round(folga, 2)))
    assert achados, "nenhum compensador comum encostado no no' nas fixtures do item 12"


# Corpus sintetico do item 17 do usuario. Os comentarios dizem a GEOMETRIA; o
# que o motor fez com ela sai na mensagem do assert (medido, nunca suposto).
CORPUS_ITEM_17 = {
    # porta na principal com a jamba a 6 cm da face da parede que chega
    "T_sobra_4cm": ([seg(-302, 0, 302, 0), seg(0, 0, 0, 298)], [[porta(315.0, 405.0)], []]),
    # porta na principal com a jamba a 11 cm da face da parede que chega
    "T_sobra_9cm": ([seg(-302, 0, 302, 0), seg(0, 0, 0, 298)], [[porta(320.0, 410.0)], []]),
    "T_sem_sobra": ([seg(-302, 0, 302, 0), seg(0, 0, 0, 298)], [[], []]),
    # janela no braco de 402 cm com a jamba a 53 / 58 cm do ponto do no'
    "L_C04_proximo": ([seg(0, 0, 402, 0), seg(0, 0, 0, 298)], [[janela(60.0, 180.0)], []]),
    "L_C09_proximo": ([seg(0, 0, 402, 0), seg(0, 0, 0, 298)], [[janela(65.0, 185.0)], []]),
    "cruz": cruz(),
    # porta numa das paredes da cruz com a jamba a 21 cm da face do cruzamento
    "cruz_com_porta": ([seg(0, 302, 604, 302), seg(302, 0, 302, 604)], [[porta(330.0, 420.0)], []]),
    "abertura_perto_do_no_T": tee_80(),
    "abertura_perto_do_no_L": DEGRADAM["L_braco_curto_ate_porta"],
    "parede_curta_L": DEGRADAM["L_braco_curto"],
    "parede_curta_T": DEGRADAM["T_parede_que_chega_curta"],
    "boneca_T": DEGRADAM["T_boneca_curta"],
    # parede que chega a 10 / 20 cm da ponta livre da principal
    "no_perto_da_extremidade_10cm": ([seg(0, 0, 600, 0), seg(10, 0, 10, 298)], [[], []]),
    "no_perto_da_extremidade_20cm": ([seg(0, 0, 600, 0), seg(20, 0, 20, 298)], [[], []]),
}


@pytest.mark.parametrize("nome", sorted(CORPUS_ITEM_17))
def test_corpus_item_17_gate_igual_ao_oraculo_independente(nome):
    """Item 13: fluxo CHANNEL com as flags de HOJE (sem fixar nada). Para cada
    fixture o gate acusa EXATAMENTE os compensadores que o motor designou peca
    do no' OU que sao o maior ocupante da regiao do no' - conferido contra o
    oraculo de amostragem - e cada evidencia bate com o motivo. O que foi
    encontrado vai na mensagem."""
    lines, ops = CORPUS_ITEM_17[nome]
    res, walls, nodes = _resolve(nome, lines, ops)
    cc = res["course_candidates"]
    violacoes = gate(cc, nodes, walls)
    esperado, empates, amostras = oraculo(cc, nodes, walls)
    msg = _resumo(nome, cc, nodes, walls, violacoes, esperado, empates, amostras)
    # um empate de area NAO e' erro do solver nem do gate: o oraculo o modela
    # (compensador entre os lideres e' acusado) e o empate so' vai na mensagem
    obtido = dict((_chave_v(v), set(v["evidence"])) for v in violacoes)
    assert len(obtido) == len(violacoes), msg
    assert obtido == esperado, msg
    for v in violacoes:
        assert v["logical_code"] in COMP, msg
    if "compensator_as_junction_bond" in res:
        assert res["compensator_as_junction_bond"] == violacoes, msg


def test_corpus_item_17_exercita_compensador_perto_do_no_sem_acusar():
    """Nao-vacuidade do item 13: o corpus tem de conter, em algum lugar,
    compensador a ate' 3 cm da regiao de um no' que o gate NAO acusa (a
    proximidade permitida) - senao o corpus nao prova a regra de FUNCAO."""
    achados = []
    for nome in sorted(CORPUS_ITEM_17):
        res, walls, nodes = _resolve(nome, *CORPUS_ITEM_17[nome])
        cc = res["course_candidates"]
        acusadas = set(_chave_v(v) for v in gate(cc, nodes, walls))
        for ni, no in enumerate(nodes):
            if no.get("kind") not in TIPOS_DE_NO:
                continue
            for ci, c in _compensadores(cc):
                if c.get("wall_idx") in _paredes_do_no(no) and _perto(c, no, 10.0) \
                        and _chave(ci, c) not in acusadas:
                    g = _folga_cm(c, no, walls)
                    if g <= 3.0:
                        achados.append((nome, ci, c["logical_code"], c.get("placement_reason"), round(g, 2)))
    assert achados, "nenhum compensador perto do no' no corpus"
