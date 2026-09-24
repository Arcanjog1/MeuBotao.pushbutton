# -*- coding: utf-8 -*-
"""REGRA 76 / 76.1 - dois resultados INDEPENDENTES sobre os encontros L/T/X.

  * COMPENSATOR_AS_JUNCTION_BOND (`wall_stepper.compensator_as_junction_bond`)
    - o motor DESIGNOU um compensador (C04/C09) peca de amarracao do no'
    (placement_reason comecando por L_CORNER/T_INTERSECTION/X_INTERSECTION/
    CORNER). So' a designacao conta: compensador nao designado nunca aparece
    aqui, qualquer que seja a geometria.
  * MISSING_REQUIRED_JUNCTION_BOND (`wall_stepper.missing_required_junction_bond`
    == `junction_bond_audit(...)["missing"]`) - GEOMETRIA: na fiada o encontro
    existe e nao ha' PECA DE AMARRACAO VALIDA na regiao do no' (interseccao das
    faixas de espessura). Valida = B34/B54, de parede do no', cobrindo a
    regiao INTEIRA (so' uma faixa de 0,05 cm na borda pode faltar), com apoio,
    no comprimento do catalogo e fora de trecho nao-modular. A autoridade e' a
    PRESENCA da peca de amarracao valida - nunca "qual peca tem a maior area" e
    nunca distancia: compensador perto, encostado ou dentro da regiao nao
    resolve o no' e, se a amarracao valida esta' la', nao o desfaz.

Fixtures sinteticas (L, T e cruz modulares do motor - nenhum id do projeto). Os
itens A-I e K montam candidatos sobre nodes/walls REAIS do motor (copias
locais dos helpers de test_compensator_never_bonds.py - este arquivo nao
importa aquele); o item J e o G (parte solve) rodam o solve do motor. As
coberturas afirmadas saem do ORACULO de amostragem (grade de 0,5 cm / 0,1 cm,
independente do recorte de poligono do gate).

    py -3 -m pytest tests/test_missing_required_junction_bond.py -q
"""
import os
import random
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import test_channel_reinforcement as tcr  # noqa: E402

m, ft, seg, solve = tcr.m, tcr.ft, tcr.seg, tcr.solve
from core.engine import opening_micro_adjust as oma  # noqa: E402
from core.engine import opening_reinforcement as orf  # noqa: E402
from core.engine import wall_stepper as ws  # noqa: E402

gate_comp = ws.compensator_as_junction_bond
gate_missing = ws.missing_required_junction_bond
auditoria = ws.junction_bond_audit

CAT = tcr.sb.CATALOG
CHANNEL = tcr.CHANNEL
NUM_COURSES = tcr.NUM_COURSES
COMP = ("C04", "C09")
FILL = ws.JUNCTION_UNRESOLVED_FILL_REASON
CHAVES_76_1 = ("compensator_as_junction_bond", "missing_required_junction_bond", "junction_bond_audit",
               "channel_unresolved_junction_fill")
BANDA = m._free_to_top_band(CAT, 0.0)          # a faixa de fiada que o solve passa para o gate
TOL_ABERTURA = m.OPENING_COURSE_BAND_TOLERANCE_FT

KIND = {"canto": "L_CORNER", "tee_80": "T_INTERSECTION", "cruz": "X_INTERSECTION"}
LARGURA_CM = 14.0


def _cm(value_ft):
    return tcr._cm(value_ft)


def porta(lo_cm, hi_cm):
    return (ft(lo_cm), ft(hi_cm), ft(0.0), ft(221.0))


# ------------------------------------------------------------------ fixtures
# Mesmas fixtures de test_compensator_never_bonds.py, definidas AQUI (sem
# importar aquele arquivo) para este arquivo nao depender dos helpers dele.
BASES = {
    # L modular sem aberturas (bracos de 402 e 298 cm)
    "canto": lambda: ([seg(0, 0, 402, 0), seg(0, 0, 0, 298)], [[], []]),
    # T modular dos testes vizinhos (tcr.tee, peitoril 80)
    "tee_80": lambda: tcr.tee(sill_cm=80.0),
    # cruz 604x604: duas paredes que se atravessam no meio (B54 de cruz nas duas)
    "cruz": lambda: ([seg(0, 302, 604, 302), seg(302, 0, 302, 604)], [[], []]),
}
_BASE_CACHE = {}


def _cenario(nome):
    """(res, walls, nodes, no') da fixture base CHANNEL. NUNCA mutar o que
    volta: os testes de validador trabalham numa copia (`_copia`)."""
    if nome not in _BASE_CACHE:
        res, walls, nodes, _o = solve(*BASES[nome]())
        _BASE_CACHE[nome] = (res, walls, nodes)
    res, walls, nodes = _BASE_CACHE[nome]
    return res, walls, nodes, _no(nodes, KIND[nome])


def _copia(res):
    return dict((ci, [dict(c) for c in v]) for ci, v in res["course_candidates"].items())


# ------------------------------------------------------- geometria de apoio
def _eixo(walls, wi):
    line = walls[wi][0]
    p0, p1 = line.GetEndPoint(0), line.GetEndPoint(1)
    comp = line.Length
    return p0, (p1.X - p0.X) / comp, (p1.Y - p0.Y) / comp


def _t_do_no_cm(walls, wi, no):
    """Posicao (cm) da projecao do ponto do no' na linha da parede, a partir da ponta 0."""
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
    t_no, comp = _t_do_no_cm(walls, wi, no), _cm(walls[wi][0].Length)
    for f in fileira:   # nenhuma peca montada flutua fora da parede
        assert -1e-6 <= t_no + f[1] and t_no + f[2] <= comp + 1e-6, ("peca fora da parede", wi, f, comp)
    cc[ci] = mantidas + novas
    return novas


def _no(nodes, kind):
    idx = [i for i, n in enumerate(nodes) if n.get("kind") == kind]
    assert len(idx) == 1, (kind, [(i, n.get("kind")) for i, n in enumerate(nodes)])
    return idx[0]


def _pecas_de_no(cc, ni, prefixo):
    """[(fiada, peca)] com node_index == ni e razao comecando por `prefixo`."""
    return [(ci, c) for ci in sorted(cc) for c in cc[ci]
            if c.get("node_index") == ni and str(c.get("placement_reason") or "").startswith(prefixo)]


def _uma_peca_de_no(cc, ni, prefixo):
    achadas = _pecas_de_no(cc, ni, prefixo)
    assert achadas, "a fixture precisa ter peca de no' %s" % prefixo
    return achadas[0]


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


def _outra_parede(nodes, ni, wi):
    return [w for w in _paredes_do_no(nodes[ni]) if w != wi][0]


def _assinatura(c):
    """Identidade FISICA da peca (sem razao nem node_index)."""
    o = c["origin_world"]
    return (c["logical_code"], round(_cm(o.X), 6), round(_cm(o.Y), 6), c["length_cm"], c["width_cm"],
            round(c["x_dir"].X, 9), round(c["x_dir"].Y, 9), c.get("wall_idx"))


def _chave(ci, c):
    o = c["origin_world"]
    return (ci, c["logical_code"], round(_cm(o.X), 1), round(_cm(o.Y), 1))


def _chave_v(v):
    return (v["course_index"], v["logical_code"], round(v["origin_cm"][0], 1), round(v["origin_cm"][1], 1))


def _foto(cc):
    return dict((ci, [(id(c), _assinatura(c), c.get("placement_reason"), c.get("node_index")) for c in v])
                for ci, v in cc.items())


# ------------------------------------------ ORACULO independente (amostragem)
def _faixas(no, walls):
    """(normal unitaria, n.p0, meia espessura) de cada parede do no', em cm."""
    out = []
    for wi in _paredes_do_no(no):
        p0, ux, uy = _eixo(walls, wi)
        n = (-uy, ux)
        out.append((n, n[0] * _cm(p0.X) + n[1] * _cm(p0.Y), _cm(walls[wi][1]) / 2.0))
    return out


def _amostras(no, walls, passo=0.5):
    """Centros de celula (grade de `passo` cm) dentro de TODAS as faixas de
    espessura das paredes do no' - a regiao do no' por amostragem, sem o
    recorte de poligono do gate."""
    P = (_cm(no["point"].X), _cm(no["point"].Y))
    faixas = _faixas(no, walls)
    R = 2.0 * max(h for _n, _c, h in faixas)
    n = int(round(2.0 * R / passo))
    pts = []
    for i in range(n):
        for j in range(n):
            X = (P[0] - R + (i + 0.5) * passo, P[1] - R + (j + 0.5) * passo)
            if all(abs(nn[0] * X[0] + nn[1] * X[1] - c) <= h for nn, c, h in faixas):
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


def _extensao(walls, no, wi):
    """(a, b) da regiao do no' ao longo da parede `wi`, relativo ao ponto do
    no' (cm): as amostras da regiao projetadas no eixo, arredondadas para a
    borda da celula (grade de 0,5 cm)."""
    p0, ux, uy = _eixo(walls, wi)
    t_no = _t_do_no_cm(walls, wi, no)
    ts = [(x - _cm(p0.X)) * ux + (y - _cm(p0.Y)) * uy - t_no for x, y in _amostras(no, walls)]
    return round(min(ts) - 0.25, 6), round(max(ts) + 0.25, 6)


def _ocupantes_oraculo(cc, ci, nodes, walls, ni, pts):
    """[(codigo, amostras)] das pecas de parede do no' que tocam a regiao."""
    paredes = _paredes_do_no(nodes[ni])
    return sorted((c["logical_code"], _conta(c, pts)) for c in cc[ci]
                  if c.get("wall_idx") in paredes and _conta(c, pts) > 0)


def _audita(cc, nodes, walls, **kw):
    kw.setdefault("catalog", CAT)
    return auditoria(cc, nodes, walls, **kw)


def _resumo(missing):
    return [(v["course_index"], v["node_index"], v["reason"]) for v in missing]


def _ocup(v):
    return [(o["logical_code"], o["coverage"], o["is_compensator"]) for o in v["occupants"]]


def _designado(c):
    return (c.get("logical_code") in COMP
            and any(str(c.get("placement_reason") or "").startswith(p) for p in ws.COMPENSATOR_BOND_ROLE_PREFIXES))


def _origem_cm(c):
    o = c["origin_world"]
    return (round(_cm(o.X), 3), round(_cm(o.Y), 3))


# =========================================================================
# controle - as fixtures base amarram TODA fiada (senao os mutantes nao provam nada)
# =========================================================================
@pytest.mark.parametrize("nome", sorted(KIND))
def test_controle_fixtures_base_tem_amarracao_valida_em_toda_fiada(nome):
    res, walls, nodes, ni = _cenario(nome)
    cc = res["course_candidates"]
    assert res["channel_unresolved_junction_fill"] is True
    assert res["compensator_as_junction_bond"] == []
    assert res["missing_required_junction_bond"] == []
    assert res["junction_bond_audit"] == {"checked": NUM_COURSES, "valid": NUM_COURSES, "not_required": []}
    pts = _amostras(nodes[ni], walls)
    for ci in sorted(cc):
        ocup = _ocupantes_oraculo(cc, ci, nodes, walls, ni, pts)
        assert len(ocup) == 1 and ocup[0][0] in ("B34", "B54") and ocup[0][1] == len(pts), (ci, ocup)
    # a regiao, em cada parede do no', e' [-7, 7] cm em volta do ponto do no'
    for wi in _paredes_do_no(nodes[ni]):
        assert _extensao(walls, nodes[ni], wi) == pytest.approx((-7.0, 7.0))


# =========================================================================
# A) amarracao funcional presente + C09 ao lado -> valido nos dois gates
# =========================================================================
@pytest.mark.parametrize("nome,papel", [("canto", "L_CORNER"), ("tee_80", "T_INTERSECTION_MAIN"),
                                        ("tee_80", "T_INTERSECTION_INCOMING"), ("cruz", "X_INTERSECTION")])
def test_A_amarracao_presente_e_c09_ao_lado_valido_nos_dois_gates(nome, papel):
    """[B34/B54 de amarracao][C09][B39] na parede da amarracao e um C09
    ENCOSTADO (sem junta) na face da regiao do no' na outra parede: os dois
    gates vazios. O C09 esta' "perto do no'" - proximidade nao e' criterio."""
    res, walls, nodes, ni = _cenario(nome)
    cc = _copia(res)
    ci, amarra = _uma_peca_de_no(cc, ni, papel)
    wi = amarra["wall_idx"]
    wj = _outra_parede(nodes, ni, wi)
    _a, b = _trecho(walls, nodes[ni], wi, amarra)
    c09_lado, _b39 = _monta(cc, ci, walls, nodes, ni, wi, [("C09", b + 1.0, b + 10.0), ("B39", b + 11.0, b + 50.0)])
    (c09_face,) = _monta(cc, ci, walls, nodes, ni, wj, [("C09", 7.0, 16.0)])
    pts = _amostras(nodes[ni], walls)
    # nao-vacuidade: a amarracao cobre a regiao inteira, os C09 nao entram nela
    assert _ocupantes_oraculo(cc, ci, nodes, walls, ni, pts) == [(amarra["logical_code"], len(pts))]
    assert _conta(c09_lado, pts) == _conta(c09_face, pts) == 0
    # o C09 da outra parede comeca EXATAMENTE na face da regiao (encostado, sem junta)
    assert _trecho(walls, nodes[ni], wj, c09_face)[0] == _extensao(walls, nodes[ni], wj)[1] == 7.0

    assert gate_comp(cc, nodes, walls) == []
    r = _audita(cc, nodes, walls)
    assert r["missing"] == [] and r["valid"] == r["checked"] == NUM_COURSES


# =========================================================================
# B) B34 ausente + C09 DESIGNADO cobrindo 64% -> MISSING acusa + COMPENSATOR acusa
# =========================================================================
CASOS_B = [
    ("canto", "L_CORNER", "L_CORNER_DEGRADED"),
    ("canto", "L_CORNER", "CORNER_DEGRADED"),
    ("tee_80", "T_INTERSECTION_INCOMING", "T_INTERSECTION_INCOMING_DEGRADED"),
    ("tee_80", "T_INTERSECTION_MAIN", "T_INTERSECTION_DEGRADED_L"),
    ("cruz", "X_INTERSECTION", "X_INTERSECTION_DEGRADED"),
]


def _c09_no_lugar_da_amarracao(nome, papel, razao, node_index):
    """Tira a amarracao da primeira fiada do papel e poe um C09 de 9 cm a
    partir da face da regiao (-7..2 cm): cobre 9 de 14 cm = 64%."""
    res, walls, nodes, ni = _cenario(nome)
    cc = _copia(res)
    ci, amarra = _uma_peca_de_no(cc, ni, papel)
    wi = amarra["wall_idx"]
    (c09,) = _monta(cc, ci, walls, nodes, ni, wi, [("C09", -7.0, 2.0, razao, node_index)])
    return cc, walls, nodes, ni, ci, wi, c09


@pytest.mark.parametrize("nome,papel,razao", CASOS_B)
def test_B_b34_ausente_c09_designado_64pct_missing_e_compensator_acusam(nome, papel, razao):
    res, walls, nodes, ni = _cenario(nome)
    cc, walls, nodes, ni, ci, wi, c09 = _c09_no_lugar_da_amarracao(nome, papel, razao, ni)
    kind = KIND[nome]
    pts = _amostras(nodes[ni], walls)
    # oraculo: so' o C09 na regiao, cobrindo 9/14 dela
    assert _ocupantes_oraculo(cc, ci, nodes, walls, ni, pts) == [("C09", len(pts) * 9 // 14)]
    assert _conta(c09, pts) * 14 == len(pts) * 9
    cobertura = round(9.0 / 14.0, 4)

    comp = gate_comp(cc, nodes, walls)
    assert len(comp) == 1, comp
    v = dict(comp[0])
    assert tuple(v.pop("origin_cm")) == _origem_cm(c09)
    assert v == {"course_index": ci, "node_index": ni, "node_kind": kind, "wall_idx": wi, "logical_code": "C09",
                 "placement_reason": razao, "evidence": ["DESIGNATED_NODE_PIECE"], "coverage": cobertura,
                 "occupied_nodes": [{"node_index": ni, "node_kind": kind, "coverage": cobertura}]}

    missing = gate_missing(cc, nodes, walls, catalog=CAT)
    assert missing == _audita(cc, nodes, walls)["missing"]
    assert len(missing) == 1, missing
    v = dict(missing[0])
    ocupantes = v.pop("occupants")
    assert v == {"course_index": ci, "node_index": ni, "node_kind": kind, "walls": _paredes_do_no(nodes[ni]),
                 "reason": "NO_BOND_PIECE", "classification": "MISSING_REQUIRED_JUNCTION_BOND",
                 "review": "HUMAN_REVIEW"}
    assert len(ocupantes) == 1
    o = dict(ocupantes[0])
    assert tuple(o.pop("origin_cm")) == _origem_cm(c09)
    assert o == {"logical_code": "C09", "coverage": cobertura, "placement_reason": razao, "wall_idx": wi,
                 "node_index": ni, "is_compensator": True}


@pytest.mark.parametrize("nome,papel,razao", CASOS_B)
def test_B_mesmo_c09_sem_designacao_so_o_missing_acusa(nome, papel, razao):
    """Controle de B: o MESMO C09 no MESMO lugar, sem a razao de no' ->
    COMPENSATOR vazio (a versao de ontem o acusava como 'maior ocupante'; o
    criterio foi abandonado) e o MISSING identico (a geometria decide)."""
    cc_d, walls, nodes, ni, ci, _wi, c09_d = _c09_no_lugar_da_amarracao(nome, papel, razao, None)
    cc_s, _w, _n, _ni, _ci, _wi2, c09_s = _c09_no_lugar_da_amarracao(nome, papel, "STANDARD_FILL", None)
    assert _assinatura(c09_d) == _assinatura(c09_s)
    assert gate_comp(cc_s, nodes, walls) == []
    # designado sem node_index: acusado, e o no' vem da regiao que ele ocupa
    comp = gate_comp(cc_d, nodes, walls)
    assert [(v["course_index"], v["node_index"], v["evidence"]) for v in comp] == \
        [(ci, ni, ["DESIGNATED_NODE_PIECE"])]
    md, ms = gate_missing(cc_d, nodes, walls), gate_missing(cc_s, nodes, walls)
    assert _resumo(md) == _resumo(ms) == [(ci, ni, "NO_BOND_PIECE")]
    assert _ocup(md[0]) == _ocup(ms[0]) == [("C09", round(9.0 / 14.0, 4), True)]


def test_B_independencia_designado_fora_da_regiao_so_o_compensator_acusa():
    """Os dois resultados sao INDEPENDENTES: com o B34 de canto intacto, um C09
    designado (L_CORNER_DEGRADED) FORA da regiao do no' e' acusado pelo
    COMPENSATOR (designacao) e o no' continua com amarracao valida (MISSING
    vazio)."""
    res, walls, nodes, ni = _cenario("canto")
    cc = _copia(res)
    ci, b34 = _uma_peca_de_no(cc, ni, "L_CORNER")
    wj = _outra_parede(nodes, ni, b34["wall_idx"])
    (c09,) = _monta(cc, ci, walls, nodes, ni, wj, [("C09", 8.0, 17.0, "L_CORNER_DEGRADED", ni)])
    assert _conta(c09, _amostras(nodes[ni], walls)) == 0
    comp = gate_comp(cc, nodes, walls)
    assert [(v["course_index"], v["node_index"], v["evidence"], v["coverage"], v["occupied_nodes"])
            for v in comp] == [(ci, ni, ["DESIGNATED_NODE_PIECE"], None, [])]
    r = _audita(cc, nodes, walls)
    assert r["missing"] == [] and r["valid"] == r["checked"] == NUM_COURSES


# =========================================================================
# C) B34 ausente + dois C09 (nao designados) dividindo a regiao -> MISSING
# =========================================================================
@pytest.mark.parametrize("nome,papel,fileira,cobertura", [
    ("canto", "L_CORNER", [("C09", -7.0, 2.0), ("C09", 2.0, 11.0)], [9.0 / 14.0, 5.0 / 14.0]),
    ("tee_80", "T_INTERSECTION_MAIN", [("C09", -9.0, 0.0), ("C09", 0.0, 9.0)], [0.5, 0.5]),
    ("tee_80", "T_INTERSECTION_INCOMING", [("C09", -7.0, 2.0), ("C09", 2.0, 11.0)], [9.0 / 14.0, 5.0 / 14.0]),
    ("cruz", "X_INTERSECTION", [("C09", -9.0, 0.0), ("C09", 0.0, 9.0)], [0.5, 0.5]),
])
def test_C_dois_c09_dividindo_a_regiao_missing_e_nao_compensator(nome, papel, fileira, cobertura):
    """Os dois C09 cobrem a regiao INTEIRA juntos (no T e na cruz, 50%/50% -
    empate exato). Nenhum e' amarracao: o no' fica sem amarracao (MISSING,
    NO_BOND_PIECE) e o COMPENSATOR fica vazio (nenhum foi designado)."""
    res, walls, nodes, ni = _cenario(nome)
    cc = _copia(res)
    ci, amarra = _uma_peca_de_no(cc, ni, papel)
    novas = _monta(cc, ci, walls, nodes, ni, amarra["wall_idx"], fileira)
    pts = _amostras(nodes[ni], walls)
    contagens = [_conta(c, pts) for c in novas]
    assert sum(contagens) == len(pts)                    # a regiao esta' toda coberta...
    assert [k * 14 for k in contagens] == [round(f * 14) * len(pts) for f in cobertura]
    assert _ocupantes_oraculo(cc, ci, nodes, walls, ni, pts) == sorted(("C09", k) for k in contagens)  # ...so' por C09

    assert gate_comp(cc, nodes, walls) == []
    missing = gate_missing(cc, nodes, walls, catalog=CAT)
    assert _resumo(missing) == [(ci, ni, "NO_BOND_PIECE")]
    assert _ocup(missing[0]) == [("C09", round(f, 4), True) for f in sorted(cobertura, reverse=True)]


# =========================================================================
# D) compensador invadindo 10/20/25% da regiao COM a amarracao valida -> valido
# =========================================================================
@pytest.mark.parametrize("fracao", [0.10, 0.20, 0.25])
@pytest.mark.parametrize("nome,papel", [("canto", "L_CORNER"), ("tee_80", "T_INTERSECTION_MAIN"),
                                        ("tee_80", "T_INTERSECTION_INCOMING"), ("cruz", "X_INTERSECTION")])
def test_D_compensador_toca_parte_da_regiao_com_amarracao_inteira_valido(nome, papel, fracao):
    """A amarracao correta (B34/B54 cobrindo a regiao INTEIRA) esta' la'; um C09
    da outra parede entra 10%/20%/25% na regiao. Os DOIS gates ficam vazios: a
    presenca da amarracao valida decide, nao a area do compensador.

    O C09 dentro do volume da amarracao e' uma COLISAO fisica - isso e' OUTRO
    portao (colisoes / regra 18.7), que este teste nao exercita nem mascara:
    aqui a unica pergunta e' "o no' tem amarracao valida?"."""
    res, walls, nodes, ni = _cenario(nome)
    cc = _copia(res)
    ci, amarra = _uma_peca_de_no(cc, ni, papel)
    wj = _outra_parede(nodes, ni, amarra["wall_idx"])
    p = fracao * 14.0
    (c09,) = _monta(cc, ci, walls, nodes, ni, wj, [("C09", 7.0 - p, 16.0 - p)])
    pts = _amostras(nodes[ni], walls, passo=0.1)          # faces em multiplos de 0,1 cm: contagem exata
    assert _conta(c09, pts) == int(round(fracao * len(pts)))
    assert _conta(amarra, pts) == len(pts)
    # a colisao existe (o C09 esta' dentro da amarracao) - portao de colisao, nao este
    assert sum(1 for X in pts if max(_local(c09, X)) < 0.0 and max(_local(amarra, X)) < 0.0) == _conta(c09, pts)

    assert gate_comp(cc, nodes, walls) == []
    r = _audita(cc, nodes, walls)
    assert r["missing"] == [] and r["valid"] == r["checked"] == NUM_COURSES


# =========================================================================
# E) regiao vazia -> EMPTY_REGION
# =========================================================================
@pytest.mark.parametrize("nome,papel", [("canto", "L_CORNER"), ("tee_80", "T_INTERSECTION_MAIN"),
                                        ("tee_80", "T_INTERSECTION_INCOMING"), ("cruz", "X_INTERSECTION")])
def test_E_regiao_vazia_sem_peca_funcional_empty_region(nome, papel):
    res, walls, nodes, ni = _cenario(nome)
    cc = _copia(res)
    ci, _amarra = _uma_peca_de_no(cc, ni, papel)
    pts = _amostras(nodes[ni], walls)
    cc[ci] = [c for c in cc[ci] if _conta(c, pts) == 0]      # tira TODA peca que toca a regiao (oraculo)
    assert _ocupantes_oraculo(cc, ci, nodes, walls, ni, pts) == []
    assert gate_comp(cc, nodes, walls) == []
    r = _audita(cc, nodes, walls)
    assert _resumo(r["missing"]) == [(ci, ni, "EMPTY_REGION")]
    assert r["missing"][0]["occupants"] == []
    assert (r["checked"], r["valid"]) == (NUM_COURSES, NUM_COURSES - 1)


def test_E_peca_de_parede_fora_do_no_nao_ocupa_a_regiao():
    """So' conta peca de PAREDE DO NO': o mesmo B34 de canto, com wall_idx de
    uma parede que nao e' do no', deixa a regiao vazia para o gate."""
    res, walls, nodes, ni = _cenario("canto")
    cc = _copia(res)
    ci, b34 = _uma_peca_de_no(cc, ni, "L_CORNER")
    a, b = _trecho(walls, nodes[ni], b34["wall_idx"], b34)
    (novo,) = _monta(cc, ci, walls, nodes, ni, b34["wall_idx"], [("B34", a, b, "L_CORNER", ni)])
    assert _conta(novo, _amostras(nodes[ni], walls)) == len(_amostras(nodes[ni], walls))
    assert _audita(cc, nodes, walls)["missing"] == []          # controle: com a parede certa, valido
    novo["wall_idx"] = len(walls) + 5
    assert _resumo(_audita(cc, nodes, walls)["missing"]) == [(ci, ni, "EMPTY_REGION")]


# =========================================================================
# F) amarracao sem apoio / nao modular nao conta
# =========================================================================
@pytest.mark.parametrize("nome,papel", [("canto", "L_CORNER"), ("tee_80", "T_INTERSECTION_MAIN"),
                                        ("tee_80", "T_INTERSECTION_INCOMING"), ("cruz", "X_INTERSECTION")])
def test_F_amarracao_sem_apoio_nao_conta(nome, papel):
    res, walls, nodes, ni = _cenario(nome)
    cc = res["course_candidates"]
    ci, amarra = _uma_peca_de_no(cc, ni, papel)
    item = {"course": ci, "wall_idx": amarra["wall_idx"], "code": amarra["logical_code"],
            "point_cm": _origem_cm(amarra), "kind": "UNSUPPORTED_BLOCK"}
    r = _audita(cc, nodes, walls, unsupported=[item])
    assert _resumo(r["missing"]) == [(ci, ni, "BOND_PIECE_UNSUPPORTED")]
    assert _ocup(r["missing"][0]) == [(amarra["logical_code"], 1.0, False)]
    # o item casa por IDENTIDADE (fiada, parede, codigo, ponto): trocado qualquer um, a peca volta a valer
    outra_fiada = [c for c in sorted(cc) if c != ci][0]
    for trocado in (dict(item, course=outra_fiada), dict(item, code="B39"),
                    dict(item, wall_idx=_outra_parede(nodes, ni, amarra["wall_idx"]))):
        r = _audita(cc, nodes, walls, unsupported=[trocado])
        assert r["missing"] == [] and r["valid"] == NUM_COURSES, trocado


@pytest.mark.parametrize("comprimento,modular", [(34.0, True), (34.03, True), (34.1, False), (35.0, False),
                                                 (33.5, False)])
def test_F_b34_fora_do_comprimento_do_catalogo_e_nao_modular(comprimento, modular):
    """B34 de canto com comprimento != catalogo (cobrindo a regiao inteira do
    mesmo jeito) -> BOND_PIECE_NON_MODULAR. Ate' 0,05 cm de diferenca e' a
    tolerancia fisica. Sem catalogo nao ha' referencia (controle)."""
    res, walls, nodes, ni = _cenario("canto")
    cc = _copia(res)
    ci, b34 = _uma_peca_de_no(cc, ni, "L_CORNER")
    (novo,) = _monta(cc, ci, walls, nodes, ni, b34["wall_idx"], [("B34", -7.0, -7.0 + comprimento, "L_CORNER", ni)])
    pts = _amostras(nodes[ni], walls)
    assert _conta(novo, pts) == len(pts)
    assert CAT["B34"]["length_cm"] == 34.0
    r = _audita(cc, nodes, walls, catalog=CAT)
    if modular:
        assert r["missing"] == []
    else:
        assert _resumo(r["missing"]) == [(ci, ni, "BOND_PIECE_NON_MODULAR")]
        assert _ocup(r["missing"][0]) == [("B34", 1.0, False)]
    assert _audita(cc, nodes, walls, catalog=None)["missing"] == []


@pytest.mark.parametrize("caso,trecho,outra_fiada,outra_parede,acusa", [
    ("cobre_o_b34", (0.0, 40.0), False, False, True),
    ("invertido_como_SEM_ESPACO", (40.0, 0.0), False, False, True),
    ("pega_o_meio", (20.0, 100.0), False, False, True),
    ("pega_1cm_da_ponta", (33.0, 100.0), False, False, True),
    ("pega_0_03cm_da_ponta", (33.97, 100.0), False, False, False),
    ("depois_do_b34", (35.0, 100.0), False, False, False),
    ("outra_fiada", (0.0, 40.0), True, False, False),
    ("outra_parede", (0.0, 40.0), False, True, False),
])
def test_F_b34_dentro_de_trecho_nao_modular(caso, trecho, outra_fiada, outra_parede, acusa):
    """Trecho `non_modular` ({wall_idx, course, seg_start_cm, seg_end_cm}, cm
    ao longo da linha da parede a partir da ponta 0) sobre o B34 de canto na
    MESMA parede e fiada -> BOND_PIECE_NON_MODULAR; so' 0,03 cm (<= 0,05) nao."""
    res, walls, nodes, ni = _cenario("canto")
    cc = res["course_candidates"]
    ci, b34 = _uma_peca_de_no(cc, ni, "L_CORNER")
    wi = b34["wall_idx"]
    a, b = _trecho(walls, nodes[ni], wi, b34)
    t_no = _t_do_no_cm(walls, wi, nodes[ni])
    assert (t_no + a, t_no + b) == pytest.approx((0.0, 34.0))   # o B34 ocupa t = 0..34 cm na parede
    entrada = {"wall_idx": _outra_parede(nodes, ni, wi) if outra_parede else wi,
               "course": [c for c in sorted(cc) if c != ci][0] if outra_fiada else ci,
               "seg_start_cm": trecho[0], "seg_end_cm": trecho[1]}
    r = _audita(cc, nodes, walls, non_modular=[entrada])
    if acusa:
        assert _resumo(r["missing"]) == [(ci, ni, "BOND_PIECE_NON_MODULAR")], caso
    else:
        assert r["missing"] == [] and r["valid"] == NUM_COURSES, caso


def test_F_sem_apoio_tem_precedencia_sobre_nao_modular_no_motivo():
    res, walls, nodes, ni = _cenario("canto")
    cc = res["course_candidates"]
    ci, b34 = _uma_peca_de_no(cc, ni, "L_CORNER")
    item = {"course": ci, "wall_idx": b34["wall_idx"], "code": "B34", "point_cm": _origem_cm(b34)}
    trecho = {"wall_idx": b34["wall_idx"], "course": ci, "seg_start_cm": 0.0, "seg_end_cm": 40.0}
    r = _audita(cc, nodes, walls, unsupported=[item], non_modular=[trecho])
    assert _resumo(r["missing"]) == [(ci, ni, "BOND_PIECE_UNSUPPORTED")]


def test_F_solve_trecho_nao_modular_no_formato_gravado_pelo_motor_desqualifica_a_amarracao():
    """O gate DO SOLVE (`wall_modeling._junction_bond_audit_final`) le
    `result["non_modular"]` como o motor o grava. Um trecho nao-modular
    gravado pelo motor, levado para cima do B34 de canto (mesma parede, 0..40
    cm, as MESMAS entradas - so' parede e trecho trocados), tem de
    desqualificar a amarracao em toda fiada em que o B34 esta' nessa parede."""
    curto, _wc, _nc, _oc = _solve("L_braco_curto", CHANNEL)
    gravados = curto["non_modular"]
    assert gravados, "a fixture de braco curto deixou de gravar trecho nao-modular"
    res, walls, nodes, ni = _cenario("canto")
    cc = res["course_candidates"]
    ci, b34 = _uma_peca_de_no(cc, ni, "L_CORNER")
    wi = b34["wall_idx"]
    esperado = sorted(c for c, p in _pecas_de_no(cc, ni, "L_CORNER") if p["wall_idx"] == wi)
    # a funcao pura honra o trecho quando a fiada e' o INDICE da fiada (controle)
    pura = _audita(cc, nodes, walls, non_modular=[{"wall_idx": wi, "course": c, "seg_start_cm": 0.0,
                                                   "seg_end_cm": 40.0} for c in esperado])
    assert sorted(v["course_index"] for v in pura["missing"] if v["reason"] == "BOND_PIECE_NON_MODULAR") == esperado

    falso = dict(res)
    falso["non_modular"] = [dict(e, wall_idx=wi, seg_start_cm=0.0, seg_end_cm=40.0) for e in gravados]
    audit = m._junction_bond_audit_final(falso, nodes, walls, [[], []], CAT, 0.0, NUM_COURSES, None)
    obtido = sorted(v["course_index"] for v in audit["missing"] if v["reason"] == "BOND_PIECE_NON_MODULAR")
    assert obtido == esperado, (
        "o gate do solve ignorou o trecho nao-modular gravado pelo motor; chave 'course' das entradas "
        "gravadas=%s, chaves de fiada de course_candidates=%s" % (
            sorted(set(repr(e.get("course")) for e in gravados)), sorted(cc)[:4]))


# =========================================================================
# G) o encontro existe na fiada? (aberturas)
# =========================================================================
def _vao(t_lo_cm, t_hi_cm, z):
    return (ft(t_lo_cm), ft(t_hi_cm), z[0], z[1])


CASOS_G = [
    # (caso, (t_lo, t_hi) relativos a regiao [r0, r1] ao longo da parede, fiada da faixa, existe?)
    ("cobre_a_regiao_inteira", lambda r0, r1: (r0 - 1.0, r1 + 40.0), 0, False),
    ("cobre_faltando_0_03cm", lambda r0, r1: (r0 + 0.03, r1 + 40.0), 0, False),
    ("cobre_parte", lambda r0, r1: (r0 + 3.0, r1 + 40.0), 0, True),
    ("cobre_faltando_0_1cm", lambda r0, r1: (r0 + 0.1, r1 + 40.0), 0, True),
    ("so_encosta_na_regiao", lambda r0, r1: (r1, r1 + 40.0), 0, True),
    ("fora_da_faixa_da_fiada", lambda r0, r1: (r0 - 1.0, r1 + 40.0), 2, True),
]


@pytest.mark.parametrize("caso,vao,delta_fiada,existe", CASOS_G, ids=[c[0] for c in CASOS_G])
@pytest.mark.parametrize("nome,papel,qual", [("canto", "L_CORNER", 0), ("canto", "L_CORNER", 1),
                                             ("tee_80", "T_INTERSECTION_MAIN", 0),
                                             ("tee_80", "T_INTERSECTION_MAIN", 1)])
def test_G_abertura_ativa_cobrindo_a_regiao_encontro_inexistente(nome, papel, qual, caso, vao, delta_fiada, existe):
    """Regiao do no' VAZIA na fiada ci (sem amarracao). Com uma abertura ATIVA
    na fiada cobrindo TODA a regiao ao longo de uma parede do no', o encontro
    nao existe -> not_required (nunca missing). Cobrindo so' parte, so'
    encostando, ou ativa em OUTRA fiada -> o encontro existe -> EMPTY_REGION."""
    res, walls, nodes, ni = _cenario(nome)
    cc = _copia(res)
    ci, _amarra = _uma_peca_de_no(cc, ni, papel)
    pts = _amostras(nodes[ni], walls)
    cc[ci] = [c for c in cc[ci] if _conta(c, pts) == 0]
    w = _paredes_do_no(nodes[ni])[qual]
    t_no = _t_do_no_cm(walls, w, nodes[ni])
    a, b = _extensao(walls, nodes[ni], w)
    r0, r1 = t_no + a, t_no + b
    lo, hi = vao(r0, r1)
    fiada_do_vao = ci + delta_fiada
    aberturas = [[] for _ in walls]
    aberturas[w] = [_vao(lo, hi, BANDA(fiada_do_vao))]
    r = _audita(cc, nodes, walls, openings_per_wall=aberturas, course_band_ft=BANDA, opening_tol_ft=TOL_ABERTURA)
    nao_req = [(x["course_index"], x["node_index"], x["absent_walls"]) for x in r["not_required"]]
    if existe:
        assert _resumo(r["missing"]) == [(ci, ni, "EMPTY_REGION")], (caso, nao_req)
        assert ci not in [x[0] for x in nao_req]
        if delta_fiada:
            # a MESMA abertura, na fiada em que ela esta' ativa, tira o encontro dali
            assert nao_req == [(fiada_do_vao, ni, [w])]
    else:
        assert r["missing"] == [], caso
        assert nao_req == [(ci, ni, [w])]
        assert r["checked"] == NUM_COURSES - 1


def test_G_abertura_abaixo_da_tolerancia_da_faixa_nao_esta_ativa():
    """Sobreposicao vertical de 0,3 cm (<= tolerancia de 0,5 cm da faixa): a
    abertura nao esta' ativa na fiada -> o encontro existe."""
    res, walls, nodes, ni = _cenario("canto")
    cc = _copia(res)
    ci, b34 = _uma_peca_de_no(cc, ni, "L_CORNER")
    pts = _amostras(nodes[ni], walls)
    cc[ci] = [c for c in cc[ci] if _conta(c, pts) == 0]
    w = b34["wall_idx"]
    z_lo, z_hi = BANDA(ci)
    assert TOL_ABERTURA == pytest.approx(ft(0.5))
    aberturas = [[] for _ in walls]
    aberturas[w] = [(ft(-1.0), ft(60.0), z_hi - ft(0.3), z_hi + ft(0.2))]
    r = _audita(cc, nodes, walls, openings_per_wall=aberturas, course_band_ft=BANDA, opening_tol_ft=TOL_ABERTURA)
    assert _resumo(r["missing"]) == [(ci, ni, "EMPTY_REGION")]
    assert ci not in [x["course_index"] for x in r["not_required"]]


def test_G_sem_aberturas_todo_encontro_existe():
    res, walls, nodes, ni = _cenario("canto")
    cc = _copia(res)
    ci, _b34 = _uma_peca_de_no(cc, ni, "L_CORNER")
    pts = _amostras(nodes[ni], walls)
    cc[ci] = [c for c in cc[ci] if _conta(c, pts) == 0]
    for kw in ({}, {"openings_per_wall": [[], []]}, {"course_band_ft": BANDA}):
        r = _audita(cc, nodes, walls, **kw)
        assert r["not_required"] == [] and _resumo(r["missing"]) == [(ci, ni, "EMPTY_REGION")], kw


# solve: porta na principal do T cobrindo a regiao do no' inteira / so' parte dela
T_PORTA_SOBRE_O_NO = ([seg(-302, 0, 302, 0), seg(0, 0, 0, 298)], [[porta(280.0, 340.0)], []])
T_PORTA_SOBRE_PARTE_DO_NO = ([seg(-302, 0, 302, 0), seg(0, 0, 0, 298)], [[porta(300.0, 390.0)], []])


def _fiadas_ativas(vao):
    out = []
    for ci in range(NUM_COURSES):
        z_lo, z_hi = BANDA(ci)
        if min(vao[3], z_hi) - max(vao[2], z_lo) > TOL_ABERTURA:
            out.append(ci)
    return out


def test_G_solve_porta_cobrindo_a_regiao_do_no_encontro_inexistente_nas_fiadas_da_porta():
    lines, ops = T_PORTA_SOBRE_O_NO
    res, walls, nodes, _o = _solve("T_porta_sobre_o_no", CHANNEL)
    ni = _no(nodes, "T_INTERSECTION")
    main = nodes[ni]["main_wall_idx"]
    t_no = _t_do_no_cm(walls, main, nodes[ni])
    a, b = _extensao(walls, nodes[ni], main)
    assert _cm(ops[main][0][0]) < t_no + a and _cm(ops[main][0][1]) > t_no + b   # a porta cobre a regiao
    fiadas = _fiadas_ativas(ops[main][0])
    assert fiadas and fiadas[0] == 0
    audit = res["junction_bond_audit"]
    assert [(x["course_index"], x["node_index"], x["absent_walls"]) for x in audit["not_required"]] == \
        [(ci, ni, [main]) for ci in fiadas]
    assert audit["checked"] == NUM_COURSES - len(fiadas)
    assert res["missing_required_junction_bond"] == []
    assert res["compensator_as_junction_bond"] == []


def test_G_solve_porta_cobrindo_so_parte_da_regiao_encontro_existe():
    lines, ops = T_PORTA_SOBRE_PARTE_DO_NO
    res, walls, nodes, _o = _solve("T_porta_sobre_parte_do_no", CHANNEL)
    ni = _no(nodes, "T_INTERSECTION")
    main = nodes[ni]["main_wall_idx"]
    t_no = _t_do_no_cm(walls, main, nodes[ni])
    a, b = _extensao(walls, nodes[ni], main)
    assert t_no + a < _cm(ops[main][0][0]) < t_no + b      # a porta cobre so' parte da regiao
    audit = res["junction_bond_audit"]
    assert audit["not_required"] == []
    assert audit["checked"] == NUM_COURSES
    assert audit["checked"] == audit["valid"] + len(res["missing_required_junction_bond"])


# passagem livre CONTINUA: principal x = 13..787 (pilaretes das pontas livres
# modulares), T em x = 200 / 400 / 600 (paredes que chegam de 298 cm) e duas
# portas [227, 373] / [427, 573] com as jambas a 27 cm dos nos externos e do
# no' do meio - o padrao que o solve abre de face de no' a face de no' acima
# do topo das portas.
PASSAGEM_CONTINUA = ([seg(13, 0, 787, 0), seg(200, 0, 200, 298), seg(400, 0, 400, 298), seg(600, 0, 600, 298)],
                     [[porta(214.0, 360.0), porta(414.0, 560.0)], [], [], []])


def test_G_solve_passagem_livre_continua_o_gate_usa_as_aberturas_do_solve():
    """Acima das portas o solve abre a passagem de face de no' a face de no'
    (aberturas do SOLVE, estendidas ate' o topo): o T do meio nao existe
    nessas fiadas -> not_required. Com as aberturas CRUAS o mesmo resultado
    acusaria EMPTY_REGION ali - por isso o gate tem de ler as do solve."""
    res, walls, nodes, ops = _solve("passagem_continua", CHANNEL)
    ftt = res["opening_reinforcement"]["free_to_top"]
    assert len(ftt) == 2 and len(set(f["from_course"] for f in ftt)) == 1
    desde = ftt[0]["from_course"]
    meio = [i for i, n in enumerate(nodes) if n.get("kind") == "T_INTERSECTION"
            and abs(_cm(n["point"].X) - 400.0) < 1e-6]
    assert len(meio) == 1
    ni = meio[0]
    paredes = sorted([nodes[ni]["main_wall_idx"], nodes[ni]["incoming_wall_idx"]])
    audit = res["junction_bond_audit"]
    assert [(x["course_index"], x["node_index"], x["absent_walls"]) for x in audit["not_required"]] == \
        [(ci, ni, paredes) for ci in range(desde, NUM_COURSES)]
    assert res["missing_required_junction_bond"] == []
    assert res["compensator_as_junction_bond"] == []
    # contraprova: as aberturas CRUAS (sem a extensao do solve) cobrariam o no' do meio
    cru = auditoria(res["course_candidates"], nodes, walls, ops, BANDA,
                    res["physical_support"]["items"], None, CAT, TOL_ABERTURA)
    assert _resumo(cru["missing"]) == [(ci, ni, "EMPTY_REGION") for ci in range(desde, NUM_COURSES)]
    assert cru["not_required"] == []


# =========================================================================
# H) B19 / canaleta / B39 cobrindo a regiao inteira NAO e' amarracao
# =========================================================================
CODIGOS_H = [("B19", 19.0), (orf.CHANNEL_U_19, 19.0), (orf.CHANNEL_U_34, 34.0), (orf.CHANNEL_U_39, 39.0),
             (orf.CHANNEL_U_CUT, 25.0), ("K19", 19.0), ("K39", 39.0), ("B39", 39.0)]


@pytest.mark.parametrize("razao", ["STANDARD_FILL", "L_CORNER"])
@pytest.mark.parametrize("codigo,comprimento", CODIGOS_H, ids=[c for c, _l in CODIGOS_H])
def test_H_b19_ou_canaleta_cobrindo_a_regiao_inteira_nao_e_amarracao(codigo, comprimento, razao):
    """Amarracao aprovada = B34/B54 (JUNCTION_BOND_CODES). B19, canaleta (as
    CHANNEL_U_* do motor e os nomes K.. do projeto humano) e B39 no lugar do
    B34 de canto - cobrindo a regiao INTEIRA, com ou sem razao de no' - deixam
    o no' SEM amarracao. Nao sao compensador: o COMPENSATOR fica vazio."""
    assert ws.JUNCTION_BOND_CODES == ("B34", "B54")
    res, walls, nodes, ni = _cenario("canto")
    cc = _copia(res)
    ci, b34 = _uma_peca_de_no(cc, ni, "L_CORNER")
    (peca,) = _monta(cc, ci, walls, nodes, ni, b34["wall_idx"],
                     [(codigo, -7.0, -7.0 + comprimento, razao, ni if razao != "STANDARD_FILL" else None)])
    pts = _amostras(nodes[ni], walls)
    assert _ocupantes_oraculo(cc, ci, nodes, walls, ni, pts) == [(codigo, len(pts))]
    assert gate_comp(cc, nodes, walls) == []
    missing = gate_missing(cc, nodes, walls, catalog=CAT)
    assert _resumo(missing) == [(ci, ni, "NO_BOND_PIECE")]
    assert _ocup(missing[0]) == [(codigo, 1.0, False)]


@pytest.mark.parametrize("codigo", ["B19", orf.CHANNEL_U_19])
def test_H_b19_centrado_no_t_no_lugar_do_b54_nao_e_amarracao(codigo):
    res, walls, nodes, ni = _cenario("tee_80")
    cc = _copia(res)
    ci, b54 = _uma_peca_de_no(cc, ni, "T_INTERSECTION_MAIN")
    _monta(cc, ci, walls, nodes, ni, b54["wall_idx"], [(codigo, -9.5, 9.5, "T_INTERSECTION_MAIN", ni)])
    missing = gate_missing(cc, nodes, walls, catalog=CAT)
    assert _resumo(missing) == [(ci, ni, "NO_BOND_PIECE")]
    assert _ocup(missing[0]) == [(codigo, 1.0, False)]
    assert gate_comp(cc, nodes, walls) == []


# =========================================================================
# I) amarracao PARCIAL: falta 1 mm alem da tolerancia -> PARTIAL; 0,03 cm -> valido
# =========================================================================
CASOS_I = [("canto", "L_CORNER", "B34", 34.0), ("tee_80", "T_INTERSECTION_INCOMING", "B34", 34.0),
           ("cruz", "X_INTERSECTION", "B54", 54.0)]


def _amarracao_recuada(nome, papel, codigo, comprimento, falta_cm):
    """A amarracao comeca `falta_cm` DENTRO da face da regiao (-7 cm): falta
    uma faixa de `falta_cm` de um lado; o resto da regiao esta' coberto."""
    res, walls, nodes, ni = _cenario(nome)
    cc = _copia(res)
    ci, amarra = _uma_peca_de_no(cc, ni, papel)
    (nova,) = _monta(cc, ci, walls, nodes, ni, amarra["wall_idx"],
                     [(codigo, -7.0 + falta_cm, -7.0 + falta_cm + comprimento, papel, ni)])
    a, b = _trecho(walls, nodes[ni], amarra["wall_idx"], nova)
    assert (a, b) == pytest.approx((-7.0 + falta_cm, -7.0 + falta_cm + comprimento))
    return cc, walls, nodes, ni, ci


@pytest.mark.parametrize("nome,papel,codigo,comprimento", CASOS_I, ids=[c[0] + "-" + c[1] for c in CASOS_I])
def test_I_amarracao_faltando_1mm_alem_da_tolerancia_e_partial(nome, papel, codigo, comprimento):
    """Falta 0,15 cm = a tolerancia (0,05 cm) + 1 mm, de UM lado: a peca cobre
    13,85 de 14 cm (~99%) -> BOND_PIECE_PARTIAL."""
    assert ws.PIER_PHYSICAL_FIT_TOLERANCE_CM == pytest.approx(0.05)
    falta = ws.PIER_PHYSICAL_FIT_TOLERANCE_CM + 0.1
    cc, walls, nodes, ni, ci = _amarracao_recuada(nome, papel, codigo, comprimento, falta)
    r = _audita(cc, nodes, walls)
    assert _resumo(r["missing"]) == [(ci, ni, "BOND_PIECE_PARTIAL")], (
        "faltando %.2f cm de um lado (cobertura %.4f) a amarracao foi aceita como valida" % (
            falta, (14.0 - falta) / 14.0))
    assert _ocup(r["missing"][0]) == [(codigo, round((14.0 - falta) / 14.0, 4), False)]


@pytest.mark.parametrize("nome,papel,codigo,comprimento", CASOS_I, ids=[c[0] + "-" + c[1] for c in CASOS_I])
def test_I_amarracao_faltando_0_03cm_dentro_da_tolerancia_e_valida(nome, papel, codigo, comprimento):
    cc, walls, nodes, ni, ci = _amarracao_recuada(nome, papel, codigo, comprimento, 0.03)
    r = _audita(cc, nodes, walls)
    assert r["missing"] == [] and r["valid"] == r["checked"] == NUM_COURSES
    assert gate_comp(cc, nodes, walls) == []


@pytest.mark.parametrize("nome,papel,codigo,comprimento", CASOS_I, ids=[c[0] + "-" + c[1] for c in CASOS_I])
def test_I_amarracao_faltando_5mm_e_partial(nome, papel, codigo, comprimento):
    cc, walls, nodes, ni, ci = _amarracao_recuada(nome, papel, codigo, comprimento, 0.5)
    r = _audita(cc, nodes, walls)
    assert _resumo(r["missing"]) == [(ci, ni, "BOND_PIECE_PARTIAL")]
    assert _ocup(r["missing"][0]) == [(codigo, round(13.5 / 14.0, 4), False)]


# =========================================================================
# J) solve do motor: no' degradado vira MISSING (nunca COMPENSATOR); legado intacto
# =========================================================================
FIXTURES_SOLVE = {
    # L: braco de 298 cm com porta a 23 cm do ponto do no' (16 cm da face)
    "L_braco_curto_ate_porta": ([seg(0, 0, 402, 0), seg(0, 0, 0, 298)], [[], [porta(30.0, 120.0)]]),
    # T: boneca de 13 cm entre a face da principal e a porta da parede que chega
    "T_boneca_curta": ([seg(-302, 0, 302, 0), seg(0, 0, 0, 298)], [[], [porta(27.0, 117.0)]]),
    # X (cruz 604x604): porta com a jamba a 10 cm da face do cruzamento - o B54 nao cabe
    "X_porta_perto": ([seg(0, 302, 604, 302), seg(302, 0, 302, 604)], [[porta(319.0, 409.0)], []]),
    # L com braco inteiro de 25 cm (grava trecho nao-modular - usado no item F)
    "L_braco_curto": ([seg(0, 0, 402, 0), seg(0, 0, 0, 25)], [[], []]),
    "T_porta_sobre_o_no": T_PORTA_SOBRE_O_NO,
    "T_porta_sobre_parte_do_no": T_PORTA_SOBRE_PARTE_DO_NO,
    "passagem_continua": PASSAGEM_CONTINUA,
}
DEGRADAM = ("L_braco_curto_ate_porta", "T_boneca_curta", "X_porta_perto")
_SOLVES = {}


def _solve(nome, estrategia):
    """Solve cacheado (nunca mutar o que volta)."""
    key = (nome, estrategia)
    if key not in _SOLVES:
        lines, ops = FIXTURES_SOLVE[nome]
        res, walls, nodes, ops2 = solve(lines, ops, strategy=estrategia)
        _SOLVES[key] = (res, walls, nodes, ops2)
    return _SOLVES[key]


def _no_do_encontro(nodes):
    idx = [i for i, n in enumerate(nodes) if n.get("kind") in KIND.values()]
    assert len(idx) == 1, [(i, n.get("kind")) for i, n in enumerate(nodes)]
    return idx[0]


def _fills(cc):
    return [(ci, c) for ci in sorted(cc) for c in cc[ci] if c.get("logical_code") in COMP
            and c.get("placement_reason") == FILL]


@pytest.mark.parametrize("nome", DEGRADAM)
def test_J_solve_channel_no_degradado_e_missing_e_nunca_compensator(nome):
    res, walls, nodes, ops = _solve(nome, CHANNEL)
    ni = _no_do_encontro(nodes)
    cc = res["course_candidates"]
    assert ws.COMPENSATOR_NODE_PIECE_UNDESIGNATED is False          # o fluxo CHANNEL restaura a flag
    assert res["channel_unresolved_junction_fill"] is True
    assert res["compensator_as_junction_bond"] == [] == gate_comp(cc, nodes, walls)
    assert not [c for ci in cc for c in cc[ci] if _designado(c)]

    fills = _fills(cc)
    assert fills, "a fixture deixou de degradar o no' para compensador"
    pts = _amostras(nodes[ni], walls)
    for ci, c in fills:
        assert c.get("node_index") == ni                          # node_index mantido
        assert _conta(c, pts) > 0                                 # o fill esta' na regiao do no'
    degradadas = sorted(set(ci for ci, _c in fills))

    missing = res["missing_required_junction_bond"]
    por_fiada = dict((v["course_index"], v) for v in missing if v["node_index"] == ni)
    msg = "%s: degradadas=%s missing=%s" % (nome, degradadas, _resumo(missing))
    for ci in degradadas:
        v = por_fiada.get(ci)
        assert v is not None and v["reason"] == "NO_BOND_PIECE", msg
        assert [o for o in v["occupants"] if o["is_compensator"] and o["placement_reason"] == FILL], msg
        assert not [o for o in v["occupants"] if o["logical_code"] in ws.JUNCTION_BOND_CODES], msg
    # fiada acusada que NAO e' degradada: so' por amarracao sem apoio, com o item do physical_support
    sem_apoio = set((it["course"], it["wall_idx"], it["code"]) for it in res["physical_support"]["items"])
    for ci, v in sorted(por_fiada.items()):
        if ci in degradadas:
            continue
        assert v["reason"] == "BOND_PIECE_UNSUPPORTED", msg
        assert [o for o in v["occupants"] if (ci, o["wall_idx"], o["logical_code"]) in sem_apoio], msg

    # o gate gravado no resultado == o gate recalculado com as entradas do solve
    audit = m._junction_bond_audit_final(res, nodes, walls, ops, CAT, 0.0, NUM_COURSES, None)
    assert audit["missing"] == missing
    assert dict((k, audit[k]) for k in ("checked", "valid", "not_required")) == res["junction_bond_audit"]
    assert res["junction_bond_audit"]["checked"] == res["junction_bond_audit"]["valid"] + len(missing)


@pytest.mark.parametrize("nome", DEGRADAM)
def test_J_legado_nao_liga_nada_e_nao_ganha_as_chaves_novas(nome):
    # legado HISTORICO (anterior a' secao 79)
    res, walls, nodes, _o = _solve(nome, tcr.LEGADO_HISTORICO)
    ni = _no_do_encontro(nodes)
    cc = res["course_candidates"]
    for chave in CHAVES_76_1:
        assert chave not in res, chave
    assert _fills(cc) == []
    assert ws.COMPENSATOR_NODE_PIECE_UNDESIGNATED is False
    designados = [(ci, c) for ci in sorted(cc) for c in cc[ci] if _designado(c)]
    assert designados and all(c.get("node_index") == ni for _ci, c in designados)
    assert all(str(c["placement_reason"]).endswith("_DEGRADED") for _ci, c in designados)


@pytest.mark.parametrize("nome", DEGRADAM)
def test_J_legado_do_produto_ganha_os_gates_e_o_compensador_nao_e_designado(nome):
    """SECAO 79: sem reforco, o MESMO no' degradado vem com os gates 76/76.1 e
    o rastreio; o compensador que fecha o no' sai JUNCTION_UNRESOLVED_FILL
    (nunca designado) e a fiada sem amarracao fica acusada - nunca silencio."""
    res, walls, nodes, _o = _solve(nome, None)
    for chave in ("compensator_as_junction_bond", "missing_required_junction_bond", "junction_bond_audit",
                  "bond_trace"):
        assert chave in res, chave
    assert "channel_unresolved_junction_fill" not in res     # informacao do fluxo CHANNEL
    assert res["compensator_as_junction_bond"] == []
    cc = res["course_candidates"]
    assert not [(ci, c) for ci in sorted(cc) for c in cc[ci] if _designado(c)]
    ni = _no_do_encontro(nodes)
    faltas = [v for v in res["missing_required_junction_bond"] if v["node_index"] == ni]
    for ci, c in _fills(cc):
        assert c.get("node_index") == ni
        assert any(v["course_index"] == ci for v in faltas), (ci, faltas)
    linhas = [r for r in res["bond_trace"] if r["node_index"] == ni]
    assert linhas and all(r["classification"] for r in linhas)
    assert ws.COMPENSATOR_NODE_PIECE_UNDESIGNATED is False


def _projecao_missing(missing):
    return [(v["course_index"], v["node_index"], v["reason"],
             [(o["logical_code"], o["coverage"], o["wall_idx"], o["is_compensator"], tuple(o["origin_cm"]))
              for o in v["occupants"]]) for v in missing]


@pytest.mark.parametrize("nome", DEGRADAM)
def test_J_mesma_geometria_so_a_designacao_muda(nome, monkeypatch):
    """CHANNEL com CHANNEL_UNRESOLVED_JUNCTION_FILL_ENABLED desligada x ligada:
    pecas FISICAMENTE identicas; o compensador que era DESIGNADO (*_DEGRADED)
    vira JUNCTION_UNRESOLVED_FILL no MESMO lugar. O COMPENSATOR so' acusa
    enquanto ele e' designado; o MISSING e' o MESMO nos dois (geometria)."""
    lig, walls, nodes, _o = _solve(nome, CHANNEL)
    lines, ops = FIXTURES_SOLVE[nome]
    monkeypatch.setattr(m, "CHANNEL_UNRESOLVED_JUNCTION_FILL_ENABLED", False)
    des, walls_d, nodes_d, _o2 = solve(lines, ops, strategy=CHANNEL)
    assert ws.COMPENSATOR_NODE_PIECE_UNDESIGNATED is False
    assert des["channel_unresolved_junction_fill"] is False
    assert tcr.physical_signature(lig, walls) == tcr.physical_signature(des, walls_d)

    fills_lig = sorted(_chave(ci, c) for ci, c in _fills(lig["course_candidates"]))
    cc_d = des["course_candidates"]
    designados_des = sorted(_chave(ci, c) for ci in cc_d for c in cc_d[ci] if _designado(c))
    assert fills_lig and fills_lig == designados_des
    assert sorted(_chave_v(v) for v in des["compensator_as_junction_bond"]) == designados_des
    assert all(v["evidence"] == ["DESIGNATED_NODE_PIECE"] for v in des["compensator_as_junction_bond"])
    assert lig["compensator_as_junction_bond"] == []
    assert _projecao_missing(des["missing_required_junction_bond"]) == \
        _projecao_missing(lig["missing_required_junction_bond"])


def test_J_microajuste_mede_o_portao_missing_e_rejeita_piora():
    res, walls, nodes, ops = _solve("T_boneca_curta", CHANNEL)
    ni = _no_do_encontro(nodes)
    incoming = nodes[ni]["incoming_wall_idx"]
    medida = m._micro_adjust_measure(res, walls, ops, CAT, BANDA, incoming, nodes=nodes)
    n = len(res["missing_required_junction_bond"])
    assert n > 0 and medida["gates"]["MISSING_REQUIRED_JUNCTION_BOND"] == n
    pior = dict(medida["gates"], MISSING_REQUIRED_JUNCTION_BOND=n + 1)
    assert oma._worse_gates(pior, medida["gates"]) is True
    assert oma._worse_gates(dict(medida["gates"]), medida["gates"]) is False
    # fluxo sem reforco: o resultado nao traz a chave, e o microajuste calcula o
    # MISSING ali mesmo (achado da revisao: antes o portao ficava sem evidencia
    # geometrica nesse caminho)
    legado, walls_l, nodes_l, ops_l = _solve("T_boneca_curta", tcr.LEGADO_HISTORICO)
    assert "missing_required_junction_bond" not in legado
    medida_l = m._micro_adjust_measure(legado, walls_l, ops_l, CAT, BANDA, incoming, nodes=nodes_l)
    from core.engine import physical_support as _ps
    direto = ws.missing_required_junction_bond(
        legado["course_candidates"], nodes_l, walls_l, ops_l, BANDA,
        _ps.unsupported_pieces(legado["course_candidates"], walls_l, ops_l, BANDA),
        m._non_modular_by_physical_course(legado), CAT, m.OPENING_COURSE_BAND_TOLERANCE_FT)
    assert medida_l["gates"]["MISSING_REQUIRED_JUNCTION_BOND"] == len(direto) > 0


def test_J_escadas_de_peca_de_no_so_trocam_a_razao_do_compensador(monkeypatch):
    """As escadas de no' degradado (_corner_single_element_candidate para L/T,
    _x_intersection_centered_candidate para X) com a flag: MESMA peca e MESMO
    lugar, razao JUNCTION_UNRESOLVED_FILL e node_index mantido. Bloco de
    amarracao (B34) da mesma escada continua designado."""
    P, d = m.XYZ(0.0, 0.0, 0.0), m.XYZ(1.0, 0.0, 0.0)

    def gera(flag):
        monkeypatch.setattr(ws, "COMPENSATOR_NODE_PIECE_UNDESIGNATED", flag)
        return [ws._corner_single_element_candidate(CAT, P, d, ft(12.0), "A", 0, 1, 5,
                                                    placement_reason="L_CORNER_DEGRADED"),
                ws._x_intersection_centered_candidate(CAT, P, d, ft(10.0), "A", 0, 1, 5, "X_INTERSECTION_DEGRADED"),
                ws._corner_single_element_candidate(CAT, P, d, ft(40.0), "A", 0, 1, 5,
                                                    placement_reason="L_CORNER_DEGRADED",
                                                    codes=ws.CORNER_DEGRADED_TIE_CODES),
                ws._x_intersection_centered_candidate(CAT, P, d, ft(20.0), "A", 0, 1, 5, "X_INTERSECTION_DEGRADED")]

    sem, com = gera(False), gera(True)
    assert [c["logical_code"] for c in sem] == [c["logical_code"] for c in com] == ["C09", "C09", "B34", "B34"]
    for a, b in zip(sem, com):
        assert _assinatura(a) == _assinatura(b)
        assert a["node_index"] == b["node_index"] == 5
    assert [c["placement_reason"] for c in sem] == ["L_CORNER_DEGRADED", "X_INTERSECTION_DEGRADED",
                                                    "L_CORNER_DEGRADED", "X_INTERSECTION_DEGRADED"]
    assert [c["placement_reason"] for c in com] == [FILL, FILL, "L_CORNER_DEGRADED", "X_INTERSECTION_DEGRADED"]


# =========================================================================
# K) cruz 604x604: B54 de cruz -> valido; trocado por C09 -> MISSING
# =========================================================================
def _fiadas_da_cruz(cc, ni):
    por_parede = {}
    for ci, c in _pecas_de_no(cc, ni, "X_INTERSECTION"):
        por_parede.setdefault(c["wall_idx"], (ci, c))
    assert len(por_parede) == 2, "a cruz precisa do B54 de cruz nas DUAS paredes"
    return [por_parede[w] for w in sorted(por_parede)]


@pytest.mark.parametrize("parede", [0, 1])
@pytest.mark.parametrize("designado", [False, True], ids=["nao_designado", "designado"])
def test_K_cruz_b54_trocado_por_c09_missing(parede, designado):
    res, walls, nodes, ni = _cenario("cruz")
    cc = _copia(res)
    ci, b54 = _fiadas_da_cruz(cc, ni)[parede]
    assert (b54["logical_code"], _trecho(walls, nodes[ni], b54["wall_idx"], b54)) == ("B54", (-27.0, 27.0))
    extra = ("X_INTERSECTION_DEGRADED", ni) if designado else ()
    (c09,) = _monta(cc, ci, walls, nodes, ni, b54["wall_idx"], [("C09", -4.5, 4.5) + extra])
    pts = _amostras(nodes[ni], walls)
    assert _ocupantes_oraculo(cc, ci, nodes, walls, ni, pts) == [("C09", len(pts) * 9 // 14)]
    missing = gate_missing(cc, nodes, walls, catalog=CAT)
    assert _resumo(missing) == [(ci, ni, "NO_BOND_PIECE")]
    assert missing[0]["node_kind"] == "X_INTERSECTION"
    assert _ocup(missing[0]) == [("C09", round(9.0 / 14.0, 4), True)]
    comp = gate_comp(cc, nodes, walls)
    if designado:
        assert [(v["course_index"], v["node_index"], v["node_kind"], v["evidence"]) for v in comp] == \
            [(ci, ni, "X_INTERSECTION", ["DESIGNATED_NODE_PIECE"])]
    else:
        assert comp == []


def test_K_cruz_b34_centrado_da_escada_degradada_e_amarracao_valida():
    """A escada do X degradado ainda tem o B34 centrado (meio comprimento 17 cm
    > 7 cm da meia regiao): e' peca de amarracao aprovada e cobre a regiao."""
    res, walls, nodes, ni = _cenario("cruz")
    cc = _copia(res)
    ci, b54 = _fiadas_da_cruz(cc, ni)[0]
    (b34,) = _monta(cc, ci, walls, nodes, ni, b54["wall_idx"], [("B34", -17.0, 17.0, "X_INTERSECTION_DEGRADED", ni)])
    pts = _amostras(nodes[ni], walls)
    assert _conta(b34, pts) == len(pts)
    r = _audita(cc, nodes, walls)
    assert r["missing"] == [] and r["valid"] == NUM_COURSES
    assert gate_comp(cc, nodes, walls) == []


# =========================================================================
# somente leitura e deterministico
# =========================================================================
def test_auditoria_somente_leitura_e_independente_da_ordem():
    res, walls, nodes, ni = _cenario("tee_80")
    cc = _copia(res)
    ci0, b54 = _uma_peca_de_no(cc, ni, "T_INTERSECTION_MAIN")
    _monta(cc, ci0, walls, nodes, ni, b54["wall_idx"], [("C09", -9.0, 0.0), ("C09", 0.0, 9.0)])
    ci1, b34 = _uma_peca_de_no(cc, ni, "T_INTERSECTION_INCOMING")
    _monta(cc, ci1, walls, nodes, ni, b34["wall_idx"], [("C09", -7.0, 2.0, "T_INTERSECTION_INCOMING_DEGRADED", ni)])
    antes = _foto(cc)
    primeira = _audita(cc, nodes, walls)
    comp = gate_comp(cc, nodes, walls)
    assert _foto(cc) == antes
    assert _resumo(primeira["missing"]) == [(ci0, ni, "NO_BOND_PIECE"), (ci1, ni, "NO_BOND_PIECE")]
    for semente in range(6):
        rng = random.Random(semente)
        fiadas = list(cc)
        rng.shuffle(fiadas)
        embaralhado = {}
        for ci in fiadas:
            pecas = [dict(c) for c in cc[ci]]
            rng.shuffle(pecas)
            embaralhado[ci] = pecas
        assert _audita(embaralhado, nodes, walls) == primeira, semente
        assert gate_comp(embaralhado, nodes, walls) == comp, semente
