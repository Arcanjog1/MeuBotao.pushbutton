# -*- coding: utf-8 -*-
"""REGRA 76 / 76.1 - compensador (C04/C09) NUNCA e' amarracao de encontro L, T ou X.

Compensador e' peca de AJUSTE DIMENSIONAL. Decisao do usuario (2026-09-18): "a
autoridade deve ser PRESENCA DE PECA DE AMARRACAO VALIDA e nao QUAL PECA TEM
MAIOR AREA". Dois resultados INDEPENDENTES, os dois somente leitura:

  A) COMPENSATOR_AS_JUNCTION_BOND = ws.compensator_as_junction_bond: uma entrada
     por compensador que o motor DESIGNOU amarracao (placement_reason comecando
     por L_CORNER/T_INTERSECTION/X_INTERSECTION/CORNER), evidence ==
     ["DESIGNATED_NODE_PIECE"]; `occupied_nodes` e' so' diagnostico. Compensador
     NAO designado nunca aparece aqui, qualquer que seja a geometria (o criterio
     "maior ocupante da regiao" foi ABANDONADO).
  B) MISSING_REQUIRED_JUNCTION_BOND = ws.missing_required_junction_bond ==
     ws.junction_bond_audit(...)["missing"]: por no' L/T/X e fiada, o encontro
     EXISTE (nenhuma abertura ativa na fiada cobre a regiao do no' inteira ao
     longo de uma parede do no' - senao `not_required`) e NAO ha' peca B34/B54
     da parede do no' cobrindo a regiao INTEIRA, com apoio e modular. reason
     EMPTY_REGION | BOND_PIECE_UNSUPPORTED | BOND_PIECE_NON_MODULAR |
     BOND_PIECE_PARTIAL | NO_BOND_PIECE; review HUMAN_REVIEW.
Compensador perto, encostado ou dentro da regiao NUNCA resolve o no'; a peca de
maior area nao e' criterio; nenhum criterio (nem deste arquivo) usa distancia
para acusar - distancia aparece so' para PROVAR que um caso valido tem o
compensador encostado (nao-vacuidade). Valido: [B54 de amarracao][C09][B39] ->
os dois vazios. Invalido: compensador no lugar da amarracao -> B acusa; e A
tambem, se o motor o designou.

Nivel 1 (validador) monta/muta candidatos sobre nodes/walls REAIS do motor
(fixtures sinteticas L, T, cruz, dois T a 10 cm). Nivel 2 (solver): no fluxo
CHANNEL (wall_modeling.CHANNEL_UNRESOLVED_JUNCTION_FILL_ENABLED liga
wall_stepper.COMPENSATOR_NODE_PIECE_UNDESIGNATED) o no' degradado sai com
JUNCTION_UNRESOLVED_FILL - mesma geometria fisica, so' a classificacao muda; no
legado o mesmo compensador segue designado. Os dois gates sao comparados com um
ORACULO independente (regiao do no' amostrada numa grade de 0,5 cm - sem
recorte de poligono, sem `_convex_overlap_area`).

MUTACAO (medida em 2026-09-18 com um plugin de pytest fora do repo que troca o
gate em `wall_stepper` - o solve passa a usar o mutante tambem). 109 testes:
  mutante                                   falham  quem
  A -> []                                     33    os 33 que exigem A acusar um
                                                    designado (e so' eles)
  B -> [] (audit["missing"] = [])             75    os 75 com caso invalido de B
                                                    (e so' eles)
  A acusa compensador dentro ou a <= 2,05 cm  66    os 26 validos com compensador
  B acusa a fiada-no' desse compensador       29    encostado quebram (os 26 sob
                                                    "B acusa"; A-toca pega tambem
                                                    invalidos nao designados)
  Com raio de 1,05 cm (uma junta) 6 dos 26 sobrevivem: o solver poe o
  compensador a 2 cm da regiao nos T_sobra_* e L_C0*_proximo. Os 14 testes que
  nenhum mutante quebra sao controles sem compensador encostado e sem falta
  (constantes, 3 fixtures base, T_sem_sobra/abertura_perto_do_no_T/cruz/
  cruz_com_porta nos dois fluxos e L_C04/L_C09_proximo no legado).

A regra 75 (canaleta no papel de amarracao) tem o seu proprio gate e os seus
testes em test_channel_never_bonds.py.

    py -3 -m pytest tests/test_compensator_never_bonds.py -q
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
from core.engine import opening_reinforcement as orf  # noqa: E402
from core.engine import wall_stepper as ws  # noqa: E402

COMP = ("C04", "C09")
AMARRACAO = ("B34", "B54")
PAPEL_DE_NO = ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION", "CORNER")
TIPOS_DE_NO = ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION")
FILL = "JUNCTION_UNRESOLVED_FILL"
LARGURA_CM = 14.0
CHANNEL = tcr.CHANNEL
CATALOGO = tcr.sb.CATALOG
FIT_CM = 0.05                  # PIER_PHYSICAL_FIT_TOLERANCE_CM (conferido abaixo)
ALTURA_CM = float(CATALOGO["B39"]["height_cm"])
TOL_FIADA_CM = float(m.OPENING_COURSE_BAND_TOLERANCE_CM)


# Os gates sao chamados SEMPRE pelo atributo do modulo (nunca por um alias
# capturado na importacao): assim o mutante do docstring troca o gate aqui e
# dentro do solve ao mesmo tempo.
def gate_a(cc, nodes, walls):
    return ws.compensator_as_junction_bond(cc, nodes, walls)


def gate_b(cc, nodes, walls, **kw):
    return ws.missing_required_junction_bond(cc, nodes, walls, **kw)


def auditoria(cc, nodes, walls, **kw):
    return ws.junction_bond_audit(cc, nodes, walls, **kw)


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


def _t_parede_cm(walls, wi, X):
    """t (cm) do ponto X (cm) ao longo da parede, a partir da ponta 0 da linha."""
    p0, ux, uy = _eixo(walls, wi)
    return (X[0] - _cm(p0.X)) * ux + (X[1] - _cm(p0.Y)) * uy


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
            round(c["x_dir"].X, 9), round(c["x_dir"].Y, 9), c.get("wall_idx"),
            c.get("placement_reason"), c.get("node_index"))


def _designada(c):
    """Criterio de A pelo CONTRATO: compensador com razao de papel de no'."""
    return (c.get("logical_code") in COMP
            and any(str(c.get("placement_reason") or "").startswith(p) for p in PAPEL_DE_NO))


def _compensadores(cc):
    return [(ci, c) for ci in sorted(cc) for c in cc[ci] if c.get("logical_code") in COMP]


def _chave(ci, c):
    o = c["origin_world"]
    return (ci, c["logical_code"], round(_cm(o.X), 1), round(_cm(o.Y), 1))


def _chave_v(v):
    return (v["course_index"], v["logical_code"], round(v["origin_cm"][0], 1), round(v["origin_cm"][1], 1))


def _chave_fisica(ci, c):
    o = c["origin_world"]
    return (ci, c["logical_code"], round(_cm(o.X), 3), round(_cm(o.Y), 3), round(float(c["length_cm"]), 3),
            c.get("wall_idx"))


def _faltas(lista):
    return [(f["course_index"], f["node_index"], f["reason"]) for f in lista]


def _ocupantes(f):
    return [(o["logical_code"], o["is_compensator"], o["placement_reason"], o["coverage"]) for o in f["occupants"]]


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


def _faixas(no, walls):
    """(normal unitaria, n.p0, meia espessura) de cada parede do no', em cm."""
    out = []
    for wi in _paredes_do_no(no):
        p0, ux, uy = _eixo(walls, wi)
        n = (-uy, ux)
        out.append((n, n[0] * _cm(p0.X) + n[1] * _cm(p0.Y), _cm(walls[wi][1]) / 2.0))
    return out


def _amostras(no, walls, passo=0.5, borda=0.0):
    """Centros de celula (grade de `passo` cm) dentro de TODAS as faixas de
    espessura das paredes do no' - a regiao do no' por amostragem. `borda` > 0
    descarta os pontos a ate' `borda` cm da fronteira (a faixa de fit)."""
    faixas = _faixas(no, walls)
    if len(faixas) < 2:
        return []
    P = (_cm(no["point"].X), _cm(no["point"].Y))
    R = 2.0 * max(h for _n, _c, h in faixas)
    n = int(round(2.0 * R / passo))
    pts = []
    for i in range(n):
        for j in range(n):
            X = (P[0] - R + (i + 0.5) * passo, P[1] - R + (j + 0.5) * passo)
            if all(abs(nn[0] * X[0] + nn[1] * X[1] - c) <= h - borda for nn, c, h in faixas):
                pts.append(X)
    return pts


def _local(c, X):
    o = c["origin_world"]
    rx, ry = X[0] - _cm(o.X), X[1] - _cm(o.Y)
    a = rx * c["x_dir"].X + ry * c["x_dir"].Y
    b = rx * c["y_dir"].X + ry * c["y_dir"].Y
    return abs(a) - float(c["length_cm"]) / 2.0, abs(b) - float(c.get("width_cm") or 0.0) / 2.0


def _cobre(c, X):
    return max(_local(c, X)) < 0.0


def _conta(c, pts):
    return sum(1 for X in pts if _cobre(c, X))


def _regiao_cm(no, walls):
    """Vertices (cm) da regiao do no': cruzamentos das bordas das faixas que
    ficam dentro de TODAS as faixas - construcao direta, sem recorte."""
    import math
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
    return pts


def _cantos_cm(c):
    o = c["origin_world"]
    hl, hw = float(c["length_cm"]) / 2.0, float(c.get("width_cm") or 0.0) / 2.0
    xd, yd = c["x_dir"], c["y_dir"]
    return [(_cm(o.X) + sx * hl * xd.X + sy * hw * yd.X, _cm(o.Y) + sx * hl * xd.Y + sy * hw * yd.Y)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def _faixa_da_fiada_cm(ci):
    """(z_lo, z_hi) cm da fiada `ci`: a 1a a 1 cm da base, passo bloco + junta."""
    z0 = float(m.FIRST_COURSE_Z_OFFSET_CM) + ci * (ALTURA_CM + float(m.COURSE_JOINT_CM))
    return z0, z0 + ALTURA_CM


def _faixa_ft(ci):
    z0, z1 = _faixa_da_fiada_cm(ci)
    return ft(z0), ft(z1)


def _parede_ausente(no, walls, openings, ci, wi):
    """Uma abertura ativa na fiada cobre a regiao do no' INTEIRA ao longo de wi?"""
    z_lo, z_hi = _faixa_da_fiada_cm(ci)
    ts = [_t_parede_cm(walls, wi, V) for V in _regiao_cm(no, walls)]
    t_lo, t_hi = min(ts), max(ts)
    for row in (openings[wi] if wi < len(openings) else ()):
        lo, hi, peitoril, verga = [_cm(v) for v in row[:4]]
        if min(verga, z_hi) - max(peitoril, z_lo) <= TOL_FIADA_CM:
            continue
        if lo <= t_lo + FIT_CM and hi >= t_hi - FIT_CM:
            return True
    return False


def _sem_apoio(c, ci, itens):
    o = c["origin_world"]
    x, y = _cm(o.X), _cm(o.Y)
    return any(it.get("course") == ci and it.get("wall_idx") == c.get("wall_idx")
               and it.get("code") == c.get("logical_code")
               and abs(it["point_cm"][0] - x) <= 0.11 and abs(it["point_cm"][1] - y) <= 0.11
               for it in itens or ())


def _modular(c, ci, walls, nao_modular, catalogo):
    if catalogo is not None:
        nominal = (catalogo.get(c["logical_code"]) or {}).get("length_cm")
        if nominal and abs(float(c["length_cm"]) - float(nominal)) > FIT_CM:
            return False
    ts = [_t_parede_cm(walls, c["wall_idx"], P) for P in _cantos_cm(c)]
    lo, hi = min(ts), max(ts)
    for e in nao_modular or ():
        if e.get("wall_idx") != c.get("wall_idx") or e.get("course") != ci:
            continue
        a, b = sorted((e["seg_start_cm"], e["seg_end_cm"]))
        if min(b, hi) - max(a, lo) > FIT_CM:
            return False
    return True


def oraculo(cc, nodes, walls, openings=None, sem_apoio=(), nao_modular=(), catalogo=None, passo=0.5):
    """O que os DOIS gates tem de dizer, sem o codigo deles: a regiao do no' e'
    amostrada numa grade de `passo` cm (e sem a faixa de fit na borda, para a
    pergunta "cobre a regiao INTEIRA"). Pecas alinhadas aos eixos com faces em
    multiplos de 0,5 cm nunca caem sobre um centro de celula. Devolve
    (faltas{(fiada, no'): motivo}, ausentes{(fiada, no')},
     designados{chave: [nos cuja regiao o compensador cobre]})."""
    faltas, ausentes = {}, set()
    for ni, no in enumerate(nodes):
        if no.get("kind") not in TIPOS_DE_NO:
            continue
        # pre-condicao: parede da largura do bloco -> faixa da parede == faixa
        # de alvenaria (o oraculo nao modela parede mais grossa que o bloco)
        assert all(abs(_cm(walls[w][1]) - LARGURA_CM) < 1e-6 for w in _paredes_do_no(no)), ni
        pts = _amostras(no, walls, passo)
        if not pts:
            continue
        miolo = _amostras(no, walls, passo, borda=FIT_CM)
        paredes = _paredes_do_no(no)
        for ci in sorted(cc):
            if openings is not None and any(_parede_ausente(no, walls, openings, ci, w) for w in paredes):
                ausentes.add((ci, ni))
                continue
            tocam = [c for c in cc[ci] if c.get("wall_idx") in paredes and _conta(c, pts) > 0]
            falhas = set()
            valida = False
            for c in tocam:
                if c["logical_code"] not in AMARRACAO:
                    continue
                if not all(_cobre(c, X) for X in miolo):
                    falhas.add("BOND_PIECE_PARTIAL")
                elif _sem_apoio(c, ci, sem_apoio):
                    falhas.add("BOND_PIECE_UNSUPPORTED")
                elif not _modular(c, ci, walls, nao_modular, catalogo):
                    falhas.add("BOND_PIECE_NON_MODULAR")
                else:
                    valida = True
            if valida:
                continue
            if not tocam:
                faltas[(ci, ni)] = "EMPTY_REGION"
            else:
                for motivo in ("BOND_PIECE_UNSUPPORTED", "BOND_PIECE_NON_MODULAR", "BOND_PIECE_PARTIAL"):
                    if motivo in falhas:
                        faltas[(ci, ni)] = motivo
                        break
                else:
                    faltas[(ci, ni)] = "NO_BOND_PIECE"
    designados = {}
    for ci in sorted(cc):
        for c in cc[ci]:
            if not _designada(c):
                continue
            designados[_chave(ci, c)] = sorted(
                ni for ni, no in enumerate(nodes)
                if no.get("kind") in TIPOS_DE_NO and c.get("wall_idx") in _paredes_do_no(no)
                and _conta(c, _amostras(no, walls, passo)) > 0)
    return faltas, ausentes, designados


def _nao_modular_fisico(res):
    """O `non_modular` que o motor entrega ao gate: o resultado grava a
    FAMILIA ("A"/"B") por banda e o solve converte para a FIADA FISICA
    (wall_modeling._non_modular_by_physical_course) antes da auditoria. E'
    DADO de entrada do gate - o oraculo recebe o mesmo."""
    out = m._non_modular_by_physical_course(res, m.PIER_LAYOUT_VARIANTS_PER_COURSE)
    assert all(isinstance(e.get("course"), int) for e in out), out
    return out


def _gate_a_como_oraculo(violacoes):
    for v in violacoes:
        assert v["evidence"] == ["DESIGNATED_NODE_PIECE"], v
    return dict((_chave_v(v), sorted(o["node_index"] for o in v["occupied_nodes"])) for v in violacoes)


def _folga_cm(c, no, walls):
    """Distancia (cm) entre o retangulo da peca e a regiao do no' (0 se
    invade). SO' para provar que um caso valido tem o compensador ENCOSTADO -
    nunca para decidir acusacao. Convexos separados: minimo vertice x aresta."""
    import math

    def _seg(p, a, b):
        vx, vy = b[0] - a[0], b[1] - a[1]
        t = max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / (vx * vx + vy * vy)))
        return math.hypot(p[0] - a[0] - t * vx, p[1] - a[1] - t * vy)

    if _conta(c, _amostras(no, walls)) > 0:
        return 0.0
    B = _regiao_cm(no, walls)
    cx = sum(p[0] for p in B) / len(B)
    cy = sum(p[1] for p in B) / len(B)
    B = sorted(B, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
    A = _cantos_cm(c)
    return min(min(_seg(p, Q[i], Q[(i + 1) % len(Q)]) for i in range(len(Q)))
               for P, Q in ((A, B), (B, A)) for p in P)


def _detector_por_distancia(cc, walls, nodes, ni, raio_cm):
    """O detector ERRADO que a regra 76 proibe (so' como contraprova):
    compensador cuja ponta mais proxima fica a ate' `raio_cm` do ponto do no',
    medido ao longo da parede."""
    out = []
    for ci in sorted(cc):
        for c in cc[ci]:
            if c.get("logical_code") in COMP and c.get("wall_idx") in _paredes_do_no(nodes[ni]):
                a, b = _trecho(walls, nodes[ni], c["wall_idx"], c)
                d = 0.0 if a <= 0.0 <= b else min(abs(a), abs(b))
                if d <= raio_cm:
                    out.append((ci, c["logical_code"], d))
    return out


def test_constantes_do_contrato():
    """As constantes que o oraculo usa sao as do contrato do motor."""
    assert ws.PIER_PHYSICAL_FIT_TOLERANCE_CM == FIT_CM
    assert tuple(ws.JUNCTION_BOND_CODES) == AMARRACAO
    assert tuple(ws.COMPENSATOR_BOND_GATE_CODES) == COMP
    assert tuple(ws.COMPENSATOR_BOND_ROLE_PREFIXES) == PAPEL_DE_NO
    assert ws.JUNCTION_UNRESOLVED_FILL_REASON == FILL
    assert ws.COMPENSATOR_NODE_PIECE_UNDESIGNATED is False       # desligada no motor
    assert m.CHANNEL_UNRESOLVED_JUNCTION_FILL_ENABLED is True    # ligada no fluxo CHANNEL


# =========================================================================
# 1) NIVEL VALIDADOR - candidatos montados sobre nodes/walls reais do motor
# =========================================================================
@pytest.mark.parametrize("nome", ["canto", "tee_80", "cruz"])
def test_controle_fixtures_base_sem_acusacao(nome):
    """Controle: com as amarracoes do motor intactas os DOIS gates sao vazios
    (senao os mutantes abaixo nao provariam nada) e o resultado do solve diz o
    mesmo que a chamada direta."""
    res, walls, nodes = _base(nome)
    cc = res["course_candidates"]
    assert gate_a(cc, nodes, walls) == [] == res["compensator_as_junction_bond"]
    au = auditoria(cc, nodes, walls)
    assert au["missing"] == [] == gate_b(cc, nodes, walls) == res["missing_required_junction_bond"]
    nos = sum(1 for n in nodes if n.get("kind") in TIPOS_DE_NO)
    assert au["checked"] == au["valid"] == nos * len(cc) == res["junction_bond_audit"]["valid"]
    assert any(_pecas_de_no(cc, ni, p) for ni in range(len(nodes)) for p in PAPEL_DE_NO)


# ------------------------------------------------------------------ 1. L
@pytest.mark.parametrize("designado", [False, True], ids=["nao_designado", "designado"])
@pytest.mark.parametrize("familia,codigo", [(0, "C09"), (1, "C09"), (0, "C04"), (1, "C04")])
def test_L_compensador_no_lugar_do_b34_de_canto(familia, codigo, designado):
    """Item 1: tira o B34 L_CORNER de uma fiada e poe o compensador NO LUGAR
    dele (a partir da face externa do canto). B acusa a fiada-no' com
    NO_BOND_PIECE (o compensador na regiao nao resolve); A acusa SO' se o motor
    o designou (L_CORNER_DEGRADED) - a mesma geometria nos dois casos."""
    res, walls, nodes = _base("canto")
    ni = _no(nodes, "L_CORNER")
    cc = _copia(res)
    # uma fiada de cada familia: a primeira em que cada braco tem o B34
    por_parede = {}
    for wi, ci in sorted(set((c.get("wall_idx"), ci) for ci, c in _pecas_de_no(cc, ni, "L_CORNER"))):
        por_parede.setdefault(wi, ci)
    wi = sorted(por_parede)[familia]
    ci = por_parede[wi]
    _ci, b34 = _uma_peca_de_no({ci: cc[ci]}, ni, "L_CORNER", wall_idx=wi)
    assert b34["logical_code"] == "B34"
    a, _b = _trecho(walls, nodes[ni], wi, b34)
    comp = float(codigo[1:])
    razao, no_idx = ("L_CORNER_DEGRADED", ni) if designado else ("STANDARD_FILL", None)
    _monta(cc, ci, walls, nodes, ni, wi, [(codigo, a, a + comp, razao, no_idx)])
    cobertura = round(comp / LARGURA_CM, 4)

    faltas = gate_b(cc, nodes, walls)
    assert _faltas(faltas) == [(ci, ni, "NO_BOND_PIECE")]
    f = faltas[0]
    assert (f["node_kind"], f["classification"], f["review"]) == \
        ("L_CORNER", "MISSING_REQUIRED_JUNCTION_BOND", "HUMAN_REVIEW")
    assert _ocupantes(f) == [(codigo, True, razao, cobertura)]

    acusados = gate_a(cc, nodes, walls)
    if not designado:
        assert acusados == []
        return
    assert [(v["course_index"], v["logical_code"], v["evidence"], v["placement_reason"], v["node_index"],
             v["node_kind"], v["coverage"]) for v in acusados] == \
        [(ci, codigo, ["DESIGNATED_NODE_PIECE"], "L_CORNER_DEGRADED", ni, "L_CORNER", cobertura)]
    assert acusados[0]["occupied_nodes"] == [{"node_index": ni, "node_kind": "L_CORNER", "coverage": cobertura}]


def test_L_valido_canto_intacto_e_c09_encostado_fora_da_regiao():
    """Item 2: o B34 de canto continua la'; um C09 de ajuste encostado nele
    (junta de 1 cm, fora da regiao do no') e outro encostado na face do canto,
    no outro braco -> os DOIS gates vazios."""
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
    assert gate_a(cc, nodes, walls) == []
    assert gate_b(cc, nodes, walls) == []


# ------------------------------------------------------------------ 3. T
@pytest.mark.parametrize("designado", [False, True], ids=["nao_designado", "designado"])
@pytest.mark.parametrize("papel,codigo", [
    ("T_INTERSECTION_MAIN", "C09"), ("T_INTERSECTION_MAIN", "C04"),
    ("T_INTERSECTION_INCOMING", "C09"), ("T_INTERSECTION_INCOMING", "C04"),
])
def test_T_compensador_no_lugar_da_amarracao(papel, codigo, designado):
    """Item 3: troca a amarracao do T (B54 da principal ou B34 da que chega)
    por C04/C09 na regiao do no'. B acusa NO_BOND_PIECE; A so' se designado
    (<papel>_DEGRADED)."""
    res, walls, nodes = _base("tee_80")
    ni = _no(nodes, "T_INTERSECTION")
    cc = _copia(res)
    ci, peca = _uma_peca_de_no(cc, ni, papel)
    wi = peca["wall_idx"]
    a, b = _trecho(walls, nodes[ni], wi, peca)
    comp = float(codigo[1:])
    razao, no_idx = (papel + "_DEGRADED", ni) if designado else ("STANDARD_FILL", None)
    if papel == "T_INTERSECTION_MAIN":
        assert peca["logical_code"] == "B54" and a < 0.0 < b
        fileira = [(codigo, -comp / 2.0, comp / 2.0, razao, no_idx)]   # centrado no no', como o B54
    else:
        assert peca["logical_code"] == "B34"
        fileira = [(codigo, a, a + comp, razao, no_idx)]               # da face oposta da principal
    _monta(cc, ci, walls, nodes, ni, wi, fileira)
    cobertura = round(comp / LARGURA_CM, 4)

    faltas = gate_b(cc, nodes, walls)
    assert _faltas(faltas) == [(ci, ni, "NO_BOND_PIECE")]
    assert faltas[0]["node_kind"] == "T_INTERSECTION"
    assert _ocupantes(faltas[0]) == [(codigo, True, razao, cobertura)]

    acusados = gate_a(cc, nodes, walls)
    if not designado:
        assert acusados == []
        return
    assert [(v["course_index"], v["logical_code"], v["evidence"], v["node_index"], v["node_kind"],
             v["coverage"]) for v in acusados] == \
        [(ci, codigo, ["DESIGNATED_NODE_PIECE"], ni, "T_INTERSECTION", cobertura)]


def test_T_valido_amarracao_preservada_e_c09_fechando_comprimento():
    """Item 4: [B54 de amarracao][C09][B39] na principal e, na fiada do B34 da
    que chega, C09/C04 encostados nas faces do no' -> os DOIS gates vazios."""
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
    assert gate_a(cc, nodes, walls) == []
    assert gate_b(cc, nodes, walls) == []


# ------------------------------------------------------------- 5/6. cruz
def _fiadas_da_cruz(cc, ni):
    por_parede = {}
    for ci, c in _pecas_de_no(cc, ni, "X_INTERSECTION"):
        por_parede.setdefault(c["wall_idx"], (ci, c))
    assert len(por_parede) == 2, "a cruz precisa do B54 de cruz nas DUAS paredes"
    return [por_parede[w] for w in sorted(por_parede)]


@pytest.mark.parametrize("designado", [False, True], ids=["nao_designado", "designado"])
@pytest.mark.parametrize("parede,codigo", [(0, "C09"), (1, "C09"), (0, "C04"), (1, "C04")])
def test_cruz_compensador_no_lugar_do_b54_de_cruz(parede, codigo, designado):
    """Item 5: troca o B54 de cruz (X_INTERSECTION) por C04/C09 centrado no
    cruzamento. B acusa NO_BOND_PIECE; A so' se designado
    (X_INTERSECTION_DEGRADED)."""
    res, walls, nodes = _base("cruz")
    ni = _no(nodes, "X_INTERSECTION")
    cc = _copia(res)
    ci, b54 = _fiadas_da_cruz(cc, ni)[parede]
    assert b54["logical_code"] == "B54"
    comp = float(codigo[1:])
    razao, no_idx = ("X_INTERSECTION_DEGRADED", ni) if designado else ("STANDARD_FILL", None)
    _monta(cc, ci, walls, nodes, ni, b54["wall_idx"], [(codigo, -comp / 2.0, comp / 2.0, razao, no_idx)])

    faltas = gate_b(cc, nodes, walls)
    assert _faltas(faltas) == [(ci, ni, "NO_BOND_PIECE")]
    assert faltas[0]["node_kind"] == "X_INTERSECTION"
    assert _ocupantes(faltas[0]) == [(codigo, True, razao, round(comp / LARGURA_CM, 4))]
    acusados = gate_a(cc, nodes, walls)
    if not designado:
        assert acusados == []
    else:
        assert [(v["course_index"], v["logical_code"], v["evidence"], v["node_kind"]) for v in acusados] == \
            [(ci, codigo, ["DESIGNATED_NODE_PIECE"], "X_INTERSECTION")]


def test_cruz_valida_b54_de_cruz_e_c09_encostado():
    """Item 6: B54 de cruz intacto + [C09][B39] depois dele e C09/C04
    encostados nas faces do cruzamento na outra parede -> os DOIS gates vazios."""
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
    assert gate_a(cc, nodes, walls) == []
    assert gate_b(cc, nodes, walls) == []


# ------------------------------------------------ 7. O TESTE MAIS IMPORTANTE
@pytest.mark.parametrize("designado", [False, True], ids=["nao_designado", "designado"])
def test_A_x_B_mesmo_c09_na_mesma_posicao_so_a_amarracao_decide(designado):
    """Item 7, forma estrita: o MESMO C09 (dicionario identico: codigo, centro,
    dimensoes, parede, razao) encostado a 1 cm da face do no'.
      A: [B54 de amarracao cobrindo a regiao INTEIRA][C09][B39]  -> B vazio;
      B: sem o B54 (a regiao do no' fica vazia), C09 no mesmo lugar -> B acusa.
    A acusa o C09 nos DOIS cenarios se (e so' se) ele for designado: a
    designacao e' metadado, independente da amarracao existir. Um detector por
    distancia ve A e B iguais - nao separa os casos."""
    res, walls, nodes = _base("tee_80")
    ni = _no(nodes, "T_INTERSECTION")
    ci, b54 = _uma_peca_de_no(_copia(res), ni, "T_INTERSECTION_MAIN")
    main = b54["wall_idx"]
    razao, no_idx = ("T_INTERSECTION_MAIN_DEGRADED", ni) if designado else ("STANDARD_FILL", None)

    cc_a = _copia(res)
    b54_a, c09_a, _b39 = _monta(cc_a, ci, walls, nodes, ni, main, [
        ("B54", -47.0, 7.0, "T_INTERSECTION_MAIN", ni), ("C09", 8.0, 17.0, razao, no_idx), ("B39", 18.0, 57.0)])
    cc_b = _copia(res)
    _b39l, c09_b, _b39r = _monta(cc_b, ci, walls, nodes, ni, main, [
        ("B39", -47.0, -8.0), ("C09", 8.0, 17.0, razao, no_idx), ("B39", 18.0, 57.0)])

    assert b54_a["length_cm"] == b54["length_cm"] == 54.0      # o B54 de A tem o tamanho do B54 real
    assert _assinatura(c09_a) == _assinatura(c09_b)
    assert _folga_cm(c09_a, nodes[ni], walls) == _folga_cm(c09_b, nodes[ni], walls) == pytest.approx(1.0)
    assert _detector_por_distancia(cc_a, walls, nodes, ni, 10.0) == \
        _detector_por_distancia(cc_b, walls, nodes, ni, 10.0) == [(ci, "C09", 8.0)]
    pts = _amostras(nodes[ni], walls)
    assert _conta(b54_a, pts) == len(pts)                          # A: amarracao cobre a regiao inteira
    assert [c for c in cc_b[ci] if _conta(c, pts) > 0] == []        # B: a amarracao sumiu mesmo

    assert gate_b(cc_a, nodes, walls) == []
    assert _faltas(gate_b(cc_b, nodes, walls)) == [(ci, ni, "EMPTY_REGION")]
    for cc in (cc_a, cc_b):
        acusados = gate_a(cc, nodes, walls)
        if not designado:
            assert acusados == []
        else:
            assert [(v["course_index"], v["logical_code"], v["evidence"], v["coverage"], v["occupied_nodes"])
                    for v in acusados] == [(ci, "C09", ["DESIGNATED_NODE_PIECE"], None, [])]


@pytest.mark.parametrize("designado", [False, True], ids=["nao_designado", "designado"])
def test_A_x_B_literal_b54_c09_b39_valido_e_c09_no_lugar_do_b54_invalido(designado):
    """Item 7, forma literal do usuario, com o B54 centrado de verdade:
      A: [B54 de amarracao][C09 de ajuste][B39]  -> os dois gates vazios;
      B: C09 ocupando o lugar do B54             -> B acusa NO_BOND_PIECE;
         A acusa so' se o C09 de B for designado.
    O MESMO C09 esta' "perto do no'" nos dois: um detector por distancia (raio
    de 30 cm) acusa A e B. Nos dois ha' tambem um C09 de ajuste ENCOSTADO (1 cm)
    na face do no', na parede que chega - encostar nao muda nada."""
    res, walls, nodes = _base("tee_80")
    ni = _no(nodes, "T_INTERSECTION")
    ci, b54 = _uma_peca_de_no(_copia(res), ni, "T_INTERSECTION_MAIN")
    main = b54["wall_idx"]
    inc = [w for w in _paredes_do_no(nodes[ni]) if w != main][0]
    a, b = _trecho(walls, nodes[ni], main, b54)
    assert (a, b) == (-27.0, 27.0)
    razao, no_idx = ("T_INTERSECTION_MAIN_DEGRADED", ni) if designado else ("STANDARD_FILL", None)

    cc_a = _copia(res)
    (c09_a, _b39) = _monta(cc_a, ci, walls, nodes, ni, main,
                           [("C09", b + 1.0, b + 10.0), ("B39", b + 11.0, b + 50.0)])
    cc_b = _copia(res)
    (c09_b,) = _monta(cc_b, ci, walls, nodes, ni, main, [("C09", -4.5, 4.5, razao, no_idx)])
    for cc in (cc_a, cc_b):
        (ajuste,) = _monta(cc, ci, walls, nodes, ni, inc, [("C09", 8.0, 17.0)])
        assert _folga_cm(ajuste, nodes[ni], walls) == pytest.approx(1.0)
    pts = _amostras(nodes[ni], walls)
    assert [(c["logical_code"], c.get("placement_reason")) for c in cc_a[ci] if _conta(c, pts) > 0] == \
        [("B54", "T_INTERSECTION_MAIN")]
    assert _conta(c09_a, pts) == 0
    assert [c["logical_code"] for c in cc_b[ci] if _conta(c, pts) > 0] == ["C09"]
    assert (c09_a["logical_code"], c09_a["length_cm"]) == (c09_b["logical_code"], c09_b["length_cm"])
    ingenuo_a = _detector_por_distancia(cc_a, walls, nodes, ni, 30.0)
    ingenuo_b = _detector_por_distancia(cc_b, walls, nodes, ni, 30.0)
    assert sorted(x[:2] for x in ingenuo_a) == sorted(x[:2] for x in ingenuo_b) == [(ci, "C09")] * 2

    assert gate_a(cc_a, nodes, walls) == []
    assert gate_b(cc_a, nodes, walls) == []
    faltas = gate_b(cc_b, nodes, walls)
    assert _faltas(faltas) == [(ci, ni, "NO_BOND_PIECE")]
    assert _ocupantes(faltas[0]) == [("C09", True, razao, round(9.0 / LARGURA_CM, 4))]
    acusados = gate_a(cc_b, nodes, walls)
    if not designado:
        assert acusados == []
    else:
        assert [(v["course_index"], v["logical_code"], v["evidence"], v["node_index"]) for v in acusados] == \
            [(ci, "C09", ["DESIGNATED_NODE_PIECE"], ni)]


# ------------------------------------------------------- 8. so' metadado
def test_so_metadado_c09_designado_fora_da_regiao_com_amarracao_valida():
    """Item 8 - os gates sao INDEPENDENTES: C09 com node_index + razao
    L_CORNER_DEGRADED, FORA da regiao do no' e com o B34 de canto la' -> A
    acusa (so' metadado: coverage None, occupied_nodes []) e B NAO acusa (o no'
    tem amarracao valida). O mesmo C09 sem o metadado: os dois vazios."""
    res, walls, nodes = _base("canto")
    ni = _no(nodes, "L_CORNER")
    ci, b34 = _uma_peca_de_no(_copia(res), ni, "L_CORNER")
    wj = [w for w in _paredes_do_no(nodes[ni]) if w != b34["wall_idx"]][0]

    cc = _copia(res)
    (c09,) = _monta(cc, ci, walls, nodes, ni, wj, [("C09", 8.0, 17.0, "L_CORNER_DEGRADED", ni)])
    assert _folga_cm(c09, nodes[ni], walls) == pytest.approx(1.0)
    acusados = gate_a(cc, nodes, walls)
    assert [(v["course_index"], v["evidence"], v["coverage"], v["occupied_nodes"], v["node_index"],
             v["node_kind"], v["placement_reason"]) for v in acusados] == \
        [(ci, ["DESIGNATED_NODE_PIECE"], None, [], ni, "L_CORNER", "L_CORNER_DEGRADED")]
    assert gate_b(cc, nodes, walls) == []

    controle = _copia(res)
    _monta(controle, ci, walls, nodes, ni, wj, [("C09", 8.0, 17.0)])
    assert gate_a(controle, nodes, walls) == []
    assert gate_b(controle, nodes, walls) == []


# ------------------------------------------------------- 9. escopo: canaleta
def test_canaleta_no_lugar_do_b34_nao_e_compensador_mas_nao_amarra():
    """Item 9: CHANNEL_U_34 no lugar do B34 de canto (mesma geometria, com e
    sem razao de no'). A NAO acusa (canaleta nao e' compensador - e' da regra
    75, cujo gate acusa a canaleta com papel de no'); B acusa: canaleta nao e'
    peca de amarracao aprovada. Com um C09 entrando 1 cm na regiao ao lado da
    canaleta o veredito de B e' o mesmo - ninguem ali amarra."""
    res, walls, nodes = _base("canto")
    ni = _no(nodes, "L_CORNER")
    ci, b34 = _uma_peca_de_no(_copia(res), ni, "L_CORNER")
    wi = b34["wall_idx"]
    wj = [w for w in _paredes_do_no(nodes[ni]) if w != wi][0]
    a, b = _trecho(walls, nodes[ni], wi, b34)

    cc = _copia(res)
    _monta(cc, ci, walls, nodes, ni, wi, [(orf.CHANNEL_U_34, a, b, "L_CORNER", ni)])
    assert gate_a(cc, nodes, walls) == []
    assert orf.channel_as_junction_bond(cc, None), "a regra 75 e' quem acusa a canaleta"
    faltas = gate_b(cc, nodes, walls)
    assert _faltas(faltas) == [(ci, ni, "NO_BOND_PIECE")]
    assert _ocupantes(faltas[0]) == [(orf.CHANNEL_U_34, False, "L_CORNER", 1.0)]

    sem_razao = _copia(res)
    (canaleta,) = _monta(sem_razao, ci, walls, nodes, ni, wi, [(orf.CHANNEL_U_34, a, b)])
    (c09,) = _monta(sem_razao, ci, walls, nodes, ni, wj, [("C09", 6.0, 15.0)])   # entra 1 cm na regiao
    pts = _amostras(nodes[ni], walls)
    assert 0 < _conta(c09, pts) < _conta(canaleta, pts)
    assert gate_a(sem_razao, nodes, walls) == []
    faltas = gate_b(sem_razao, nodes, walls)
    assert _faltas(faltas) == [(ci, ni, "NO_BOND_PIECE")]
    assert sorted(o["logical_code"] for o in faltas[0]["occupants"]) == sorted(["C09", orf.CHANNEL_U_34])


# ------------------------------------------- B: cada motivo, isoladamente
def _canto_b34():
    res, walls, nodes = _base("canto")
    ni = _no(nodes, "L_CORNER")
    ci, b34 = _uma_peca_de_no(_copia(res), ni, "L_CORNER")
    return res, walls, nodes, ni, ci, b34


def _caso_motivo(nome):
    """(cc, kwargs do gate, motivo esperado ou None=valido) sobre o canto. Em
    TODOS os casos ha' um C09 de ajuste encostado (1 cm) na face do canto, no
    outro braco, na mesma fiada: ele nunca muda o veredito."""
    res, walls, nodes, ni, ci, b34 = _canto_b34()
    wi = b34["wall_idx"]
    wj = [w for w in _paredes_do_no(nodes[ni]) if w != wi][0]
    a, b = _trecho(walls, nodes[ni], wi, b34)
    t0 = _t_do_no_cm(walls, wi, nodes[ni])
    cc = _copia(res)
    _monta(cc, ci, walls, nodes, ni, wj, [("C09", 8.0, 17.0)])
    o = b34["origin_world"]
    ponto = (round(_cm(o.X), 1), round(_cm(o.Y), 1))
    sem_apoio = {"course": ci, "wall_idx": wi, "code": "B34", "point_cm": ponto}
    if nome == "intacto":
        return cc, {}, None
    if nome == "vazia":                                          # tira o B34: nada na regiao
        cc[ci] = [c for c in cc[ci] if _assinatura(c) != _assinatura(b34)]
        return cc, {}, "EMPTY_REGION"
    if nome == "parcial_1cm":                                    # B34 recuado 1 cm da face do canto
        _monta(cc, ci, walls, nodes, ni, wi, [("B34", a + 1.0, b + 1.0, "L_CORNER", ni)])
        return cc, {}, "BOND_PIECE_PARTIAL"
    if nome == "recuo_dentro_do_fit":                            # 0,04 cm < fit de 0,05 cm
        _monta(cc, ci, walls, nodes, ni, wi, [("B34", a + 0.04, b + 0.04, "L_CORNER", ni)])
        return cc, {}, None
    if nome == "recuo_alem_do_fit":                              # 0,15 cm: a FAIXA de fit e' 0,05 cm
        _monta(cc, ci, walls, nodes, ni, wi, [("B34", a + 0.15, b + 0.15, "L_CORNER", ni)])
        return cc, {}, "BOND_PIECE_PARTIAL"
    if nome == "b19_no_lugar":                                   # B19 nao e' peca de amarracao
        _monta(cc, ci, walls, nodes, ni, wi, [("B19", a, a + 19.0)])
        return cc, {}, "NO_BOND_PIECE"
    if nome == "sem_apoio":
        return cc, {"unsupported": [sem_apoio]}, "BOND_PIECE_UNSUPPORTED"
    if nome == "sem_apoio_outra_peca":                           # item de outra peca: nao casa
        return cc, {"unsupported": [dict(sem_apoio, code="B39"),
                                    dict(sem_apoio, course=ci + 1),
                                    dict(sem_apoio, point_cm=(ponto[0] + 1.0, ponto[1]))]}, None
    if nome == "comprimento_fora_do_catalogo":                   # B34 de 35 cm cobrindo a regiao
        _monta(cc, ci, walls, nodes, ni, wi, [("B34", a, b + 1.0, "L_CORNER", ni)])
        return cc, {"catalog": CATALOGO}, "BOND_PIECE_NON_MODULAR"
    if nome == "comprimento_fora_do_catalogo_sem_catalogo":
        _monta(cc, ci, walls, nodes, ni, wi, [("B34", a, b + 1.0, "L_CORNER", ni)])
        return cc, {}, None
    if nome == "trecho_nao_modular":                             # trecho declarado invade o B34 em 7 cm
        return cc, {"non_modular": [{"wall_idx": wi, "course": ci, "seg_start_cm": t0 + 20.0,
                                     "seg_end_cm": t0 + 60.0}]}, "BOND_PIECE_NON_MODULAR"
    if nome == "trecho_nao_modular_encostado":                   # comeca onde o B34 termina
        return cc, {"non_modular": [{"wall_idx": wi, "course": ci, "seg_start_cm": t0 + b,
                                     "seg_end_cm": t0 + b + 40.0}]}, None
    if nome == "parede_fora_do_no":                              # mesmo B34, parede que nao e' do no'
        for c in cc[ci]:
            if _assinatura(c) == _assinatura(b34):
                c["wall_idx"] = 99
        return cc, {}, "EMPTY_REGION"
    raise AssertionError(nome)


MOTIVOS = ["intacto", "vazia", "parcial_1cm", "recuo_dentro_do_fit", "recuo_alem_do_fit", "b19_no_lugar", "sem_apoio",
           "sem_apoio_outra_peca", "comprimento_fora_do_catalogo", "comprimento_fora_do_catalogo_sem_catalogo",
           "trecho_nao_modular", "trecho_nao_modular_encostado", "parede_fora_do_no"]


@pytest.mark.parametrize("caso", MOTIVOS)
def test_B_motivo_de_cada_amarracao_invalida(caso):
    """B: a peca de amarracao so' vale se for B34/B54 da parede do no',
    cobrindo a regiao INTEIRA (so' a faixa de fit na borda pode faltar), com
    apoio, no comprimento do catalogo e fora de trecho nao-modular. Cada
    violacao isolada no canto -> o motivo dela; os controles -> valido. O
    oraculo de amostragem (grade de 0,2 cm, sem a faixa de fit) concorda."""
    _res, walls, nodes, ni, ci, _b34 = _canto_b34()
    cc, kw, esperado = _caso_motivo(caso)
    (ajuste,) = [c for c in cc[ci] if c["logical_code"] in COMP
                 and _trecho(walls, nodes[ni], c["wall_idx"], c) == (8.0, 17.0)]
    assert _folga_cm(ajuste, nodes[ni], walls) == pytest.approx(1.0)
    au = auditoria(cc, nodes, walls, **kw)
    assert gate_b(cc, nodes, walls, **kw) == au["missing"]
    obtido = _faltas(au["missing"])
    assert obtido == ([] if esperado is None else [(ci, ni, esperado)]), obtido
    assert au["checked"] == len(cc) and au["valid"] == len(cc) - len(obtido) and au["not_required"] == []
    faltas_o, _aus, _des = oraculo(cc, nodes, walls, sem_apoio=kw.get("unsupported"),
                                   nao_modular=kw.get("non_modular"), catalogo=kw.get("catalog"), passo=0.2)
    assert dict(((c, n), r) for c, n, r in obtido) == faltas_o
    for f in au["missing"]:
        assert (f["classification"], f["review"], f["walls"]) == \
            ("MISSING_REQUIRED_JUNCTION_BOND", "HUMAN_REVIEW", _paredes_do_no(nodes[ni]))
        assert all(not o["is_compensator"] for o in f["occupants"])   # o encostado nao e' ocupante
    assert gate_a(cc, nodes, walls) == []                        # o C09 encostado nao e' designado


# --------------------------------------------- B: o encontro existe?
def test_B_encontro_inexistente_nao_e_cobrado_e_abertura_parcial_e():
    """B passo 1: com a regiao do no' vazia em TODAS as fiadas, uma porta que
    cobre a regiao inteira ao longo de uma parede do no' tira o encontro das
    fiadas ativas (not_required, a parede nao esta' ali); acima da verga o
    encontro volta e e' cobrado. A mesma porta 1 cm mais curta (cobre so'
    parte da regiao) -> o encontro existe em todas; janela com peitoril -> so'
    as fiadas da janela. Sem aberturas/faixa -> todo encontro existe."""
    res, walls, nodes = _base("canto")
    ni = _no(nodes, "L_CORNER")
    no = nodes[ni]
    cc = _copia(res)
    pts = _amostras(no, walls)
    paredes = _paredes_do_no(no)
    for ci in cc:
        cc[ci] = [c for c in cc[ci] if not (c.get("wall_idx") in paredes and _conta(c, pts) > 0)]
    fiadas = sorted(cc)
    wi, wj = paredes
    for ci in fiadas:      # C09 de ajuste encostado (1 cm) na face, no outro braco: nunca conta
        (ajuste,) = _monta(cc, ci, walls, nodes, ni, wj, [("C09", 8.0, 17.0)])
    assert _folga_cm(ajuste, no, walls) == pytest.approx(1.0)
    assert gate_a(cc, nodes, walls) == []
    ts = [_t_parede_cm(walls, wi, V) for V in _regiao_cm(no, walls)]
    t_lo, t_hi = min(ts), max(ts)
    assert (round(t_lo, 6), round(t_hi, 6)) == (0.0, 14.0)
    kw = {"course_band_ft": _faixa_ft, "opening_tol_ft": ft(TOL_FIADA_CM)}

    def rodar(linha):
        aberturas = [[], []]
        aberturas[wi] = [linha]
        au = auditoria(cc, nodes, walls, openings_per_wall=aberturas, **kw)
        assert au["checked"] + len(au["not_required"]) == len(fiadas)
        assert au["valid"] == 0
        return ([(x["course_index"], x["node_index"], x["absent_walls"]) for x in au["not_required"]],
                _faltas(au["missing"]))

    def ativas(sill, head):
        return [ci for ci in fiadas
                if min(head, _faixa_da_fiada_cm(ci)[1]) - max(sill, _faixa_da_fiada_cm(ci)[0]) > TOL_FIADA_CM]

    sob_a_porta = ativas(0.0, 221.0)
    assert sob_a_porta == list(range(11))
    ausentes, faltas = rodar((ft(t_lo), ft(t_lo + 90.0), ft(0.0), ft(221.0)))
    assert ausentes == [(ci, ni, [wi]) for ci in sob_a_porta]
    assert faltas == [(ci, ni, "EMPTY_REGION") for ci in fiadas if ci not in sob_a_porta]

    ausentes, faltas = rodar((ft(t_lo + 1.0), ft(t_lo + 90.0), ft(0.0), ft(221.0)))
    assert ausentes == []
    assert faltas == [(ci, ni, "EMPTY_REGION") for ci in fiadas]

    da_janela = ativas(100.0, 221.0)
    assert da_janela == list(range(5, 11))
    ausentes, faltas = rodar((ft(t_lo), ft(t_lo + 120.0), ft(100.0), ft(221.0)))
    assert ausentes == [(ci, ni, [wi]) for ci in da_janela]

    assert _faltas(auditoria(cc, nodes, walls)["missing"]) == [(ci, ni, "EMPTY_REGION") for ci in fiadas]
    # o oraculo diz o mesmo com a porta inteira
    faltas_o, ausentes_o, _d = oraculo(cc, nodes, walls, openings=[[(ft(t_lo), ft(t_lo + 90.0), ft(0.0),
                                                                     ft(221.0))], []])
    assert ausentes_o == set((ci, ni) for ci in sob_a_porta)
    assert faltas_o == dict(((ci, ni), "EMPTY_REGION") for ci in fiadas if ci not in sob_a_porta)


# ------------------------------------------------------ 10. determinismo
def _cc_de_todos_os_casos():
    """tee_80 com: C09 NAO designado no lugar do B54 (so' B); C04 designado no
    lugar do B34 (A e B); C09 designado FORA da regiao com a amarracao intacta
    (so' A) + um C09 de ajuste encostado (nenhum); B34 recuado 1 cm (so' B,
    PARTIAL)."""
    res, walls, nodes = _base("tee_80")
    ni = _no(nodes, "T_INTERSECTION")
    cc = _copia(res)
    ci0, b54 = _uma_peca_de_no(cc, ni, "T_INTERSECTION_MAIN")
    main = b54["wall_idx"]
    _monta(cc, ci0, walls, nodes, ni, main, [("C09", -4.5, 4.5)])
    fiadas_b34 = _pecas_de_no(cc, ni, "T_INTERSECTION_INCOMING")
    ci1, b34 = fiadas_b34[0]
    inc = b34["wall_idx"]
    a, b = _trecho(walls, nodes[ni], inc, b34)
    _monta(cc, ci1, walls, nodes, ni, inc, [("C04", a, a + 4.0, "T_INTERSECTION_INCOMING_DEGRADED", ni)])
    ci2 = fiadas_b34[1][0]
    _monta(cc, ci2, walls, nodes, ni, main, [("C09", 8.0, 17.0, "T_INTERSECTION_MAIN_DEGRADED", ni)])
    _monta(cc, ci2, walls, nodes, ni, main, [("C09", -17.0, -8.0)])
    ci3 = fiadas_b34[2][0]
    _monta(cc, ci3, walls, nodes, ni, inc, [("B34", a + 1.0, b + 1.0, "T_INTERSECTION_INCOMING", ni)])
    return cc, nodes, walls, ni, (ci0, ci1, ci2, ci3)


def _foto(cc):
    return dict((ci, [(id(c), _assinatura(c), c.get("course")) for c in v]) for ci, v in cc.items())


def test_deterministico_somente_leitura_e_independente_da_ordem_nos_dois_gates():
    """Item 10: mesma entrada -> mesma saida nos DOIS gates (A e a auditoria
    inteira de B, ocupantes inclusive); nenhum dos dois muda a entrada; pecas
    embaralhadas (e copiadas, ids novos) e fiadas em outra ordem -> mesma saida."""
    cc, nodes, walls, ni, (ci0, ci1, ci2, ci3) = _cc_de_todos_os_casos()
    antes = _foto(cc)
    a1 = gate_a(cc, nodes, walls)
    b1 = auditoria(cc, nodes, walls)
    assert _foto(cc) == antes
    assert gate_a(cc, nodes, walls) == a1
    assert auditoria(cc, nodes, walls) == b1
    assert gate_b(cc, nodes, walls) == b1["missing"]
    assert _foto(cc) == antes
    assert [(v["course_index"], v["logical_code"], v["evidence"]) for v in a1] == \
        [(ci1, "C04", ["DESIGNATED_NODE_PIECE"]), (ci2, "C09", ["DESIGNATED_NODE_PIECE"])]
    assert _faltas(b1["missing"]) == [(ci0, ni, "NO_BOND_PIECE"), (ci1, ni, "NO_BOND_PIECE"),
                                      (ci3, ni, "BOND_PIECE_PARTIAL")]
    for semente in range(8):
        rng = random.Random(semente)
        fiadas = list(cc)
        rng.shuffle(fiadas)
        embaralhado = {}
        for ci in fiadas:
            pecas = [dict(c) for c in cc[ci]]
            rng.shuffle(pecas)
            embaralhado[ci] = pecas
        assert gate_a(embaralhado, nodes, walls) == a1, semente
        assert auditoria(embaralhado, nodes, walls) == b1, semente


# ------------------------------------ 11. a maior area NAO e' criterio
def test_maior_area_nao_e_criterio_so_a_amarracao_inteira_resolve():
    """Item 11 (o criterio abandonado): o MESMO C09 (6..15 cm, entra 1 cm na
    regiao do T) em quatro vizinhancas:
      (b) B54 cobrindo 12 cm da regiao - a MAIOR area, mas nao a regiao
          inteira -> B acusa BOND_PIECE_PARTIAL (o criterio antigo aprovava);
      (c) B19 cobrindo 0,5 cm - o C09 e' o maior ocupante -> NO_BOND_PIECE;
      (d) C09 sozinho -> NO_BOND_PIECE.
    A nunca acusa (C09 nao designado). Controles: (a) C09 a 0,5 cm da face
    com a amarracao intacta e (e) [B54 inteiro][C09][B39] -> os dois vazios."""
    res, walls, nodes = _base("tee_80")
    ni = _no(nodes, "T_INTERSECTION")
    pts = _amostras(nodes[ni], walls)
    ci0, b54 = _uma_peca_de_no(_copia(res), ni, "T_INTERSECTION_MAIN")
    ci1, _b34 = _uma_peca_de_no(_copia(res), ni, "T_INTERSECTION_INCOMING")
    main = b54["wall_idx"]

    cc = _copia(res)
    (c09,) = _monta(cc, ci1, walls, nodes, ni, main, [("C09", 7.5, 16.5)])
    assert _folga_cm(c09, nodes[ni], walls) == pytest.approx(0.5)
    assert gate_a(cc, nodes, walls) == [] and gate_b(cc, nodes, walls) == []

    def cenario(esquerda, c09=("C09", 6.0, 15.0)):
        cc = _copia(res)
        return cc, _monta(cc, ci0, walls, nodes, ni, main, esquerda + [c09, ("B39", c09[2] + 1.0, c09[2] + 40.0)])

    cc_e, (b54_e, c09_e, _r) = cenario([("B54", -47.0, 7.0, "T_INTERSECTION_MAIN", ni)], ("C09", 8.0, 17.0))
    assert _conta(b54_e, pts) == len(pts) and _folga_cm(c09_e, nodes[ni], walls) == pytest.approx(1.0)
    assert gate_a(cc_e, nodes, walls) == [] and gate_b(cc_e, nodes, walls) == []

    cc_b, (b54_b, c09_b, _r) = cenario([("B54", -49.0, 5.0, "T_INTERSECTION_MAIN", ni)])
    cc_c, (b19_c, c09_c, _r) = cenario([("B19", -25.5, -6.5)])
    cc_d, (_l, c09_d, _r) = cenario([("B39", -47.0, -8.0)])
    assert _assinatura(c09_b) == _assinatura(c09_c) == _assinatura(c09_d)
    assert _conta(b54_b, pts) > _conta(c09_b, pts) > 0 and b54_b["length_cm"] == 54.0
    assert 0 < _conta(b19_c, pts) < _conta(c09_c, pts)
    for caso, motivo in ((cc_b, "BOND_PIECE_PARTIAL"), (cc_c, "NO_BOND_PIECE"), (cc_d, "NO_BOND_PIECE")):
        assert gate_a(caso, nodes, walls) == []
        faltas = gate_b(caso, nodes, walls)
        assert _faltas(faltas) == [(ci0, ni, motivo)]
        assert ("C09", True, "STANDARD_FILL", round(1.0 / LARGURA_CM, 4)) in _ocupantes(faltas[0])
    assert _ocupantes(gate_b(cc_b, nodes, walls)[0])[0] == \
        ("B54", False, "T_INTERSECTION_MAIN", round(12.0 / LARGURA_CM, 4))


# ------------------------------------------------ empate de area e dois nos
def test_empate_de_area_nao_importa_e_o_veredito_nao_depende_da_outra_peca():
    """C09 e a outra peca cobrindo exatamente a mesma area da regiao (1 cm
    cada, nas duas pontas). Com o criterio novo o empate e' irrelevante: sem
    amarracao inteira B acusa, com o motivo dado pela OUTRA peca ser ou nao de
    amarracao (B19/canaleta -> NO_BOND_PIECE; B34 parcial -> PARTIAL), e A so'
    acusa o C09 se ele for designado - qualquer que seja o codigo da outra."""
    res, walls, nodes = _base("tee_80")
    ni = _no(nodes, "T_INTERSECTION")
    ci0, b54 = _uma_peca_de_no(_copia(res), ni, "T_INTERSECTION_MAIN")
    main = b54["wall_idx"]
    pts = _amostras(nodes[ni], walls)
    for outra, comp, motivo in (("B19", 19.0, "NO_BOND_PIECE"), (orf.CHANNEL_U_19, 19.0, "NO_BOND_PIECE"),
                                ("B34", 34.0, "BOND_PIECE_PARTIAL")):
        for designado in (False, True):
            razao, no_idx = ("T_INTERSECTION_MAIN_DEGRADED", ni) if designado else ("STANDARD_FILL", None)
            cc = _copia(res)
            esquerda, c09 = _monta(cc, ci0, walls, nodes, ni, main,
                                   [(outra, -6.0 - comp, -6.0), ("C09", 6.0, 15.0, razao, no_idx)])
            assert _conta(esquerda, pts) == _conta(c09, pts) > 0          # empate exato
            faltas = gate_b(cc, nodes, walls)
            assert _faltas(faltas) == [(ci0, ni, motivo)], (outra, designado)
            cob = sorted(o["coverage"] for o in faltas[0]["occupants"])
            assert cob == [round(1.0 / LARGURA_CM, 4)] * 2
            acusados = [(v["logical_code"], v["evidence"]) for v in gate_a(cc, nodes, walls)]
            assert acusados == ([("C09", ["DESIGNATED_NODE_PIECE"])] if designado else []), (outra, designado)


@pytest.mark.parametrize("designado", [False, True], ids=["nao_designado", "designado"])
def test_compensador_cobrindo_duas_regioes_uma_entrada_com_os_dois_nos(designado):
    """Dois T na mesma principal a 10 cm um do outro (paredes que chegam
    desalinhadas, comum em projeto real). Um C09 na sobreposicao das duas
    regioes, com a fiada sem nenhuma outra peca das paredes dos nos: B acusa
    os DOIS nos naquela fiada (NO_BOND_PIECE, o C09 e' ocupante de cada um);
    A: designado -> UMA entrada, evidencia sem repeticao, `occupied_nodes` com
    os dois nos e o no' designado como `node_index`; nao designado -> nada."""
    lines = [seg(-302, 0, 302, 0), seg(0, 0, 0, 298), seg(10, 0, 10, -298)]
    res, walls, nodes = _resolve("dois_T_a_10cm", lines, [[], [], []])
    tees = sorted((i for i, n in enumerate(nodes) if n.get("kind") == "T_INTERSECTION"),
                  key=lambda i: nodes[i]["point"].X)
    assert len(tees) == 2   # o de x=0 primeiro, o de x=10 depois
    principal = sorted(set(_paredes_do_no(nodes[tees[0]])) & set(_paredes_do_no(nodes[tees[1]])))[0]
    cc = _copia(res)
    ci = sorted(cc)[0]
    base = [f for f in auditoria(cc, nodes, walls)["missing"] if f["course_index"] != ci]
    cc[ci] = [c for c in cc[ci] if c.get("wall_idx") not in _paredes_do_no(nodes[tees[0]]) +
              _paredes_do_no(nodes[tees[1]])]
    razao, no_idx = ("T_INTERSECTION_MAIN_DEGRADED", tees[0]) if designado else ("STANDARD_FILL", None)
    (c09,) = _monta(cc, ci, walls, nodes, tees[0], principal, [("C09", 0.5, 9.5, razao, no_idx)])
    for ni in tees:
        assert _conta(c09, _amostras(nodes[ni], walls)) > 0

    au = auditoria(cc, nodes, walls)
    desta = [f for f in au["missing"] if f["course_index"] == ci]
    assert sorted(_faltas(desta)) == sorted((ci, ni, "NO_BOND_PIECE") for ni in tees)
    for f in desta:
        assert [o["logical_code"] for o in f["occupants"]] == ["C09"]
    assert [f for f in au["missing"] if f["course_index"] != ci] == base   # as outras fiadas nao mudam

    acusados = gate_a(cc, nodes, walls)
    if not designado:
        assert acusados == []
        return
    assert len(acusados) == 1
    v = acusados[0]
    assert v["evidence"] == ["DESIGNATED_NODE_PIECE"]
    assert sorted(o["node_index"] for o in v["occupied_nodes"]) == sorted(tees)
    assert v["node_index"] == tees[0]
    assert v["coverage"] == [o["coverage"] for o in v["occupied_nodes"] if o["node_index"] == tees[0]][0]


# =========================================================================
# 2) NIVEL SOLVER
# =========================================================================
# Fixtures em que o motor DEGRADA o no' para compensador (medido): o espaco do
# encontro nao comporta B34/B54, a escada de peca de no' fecha com C09/C04.
DEGRADAM = {
    # braco de 298 cm com porta a 23 cm do ponto do no' (16 cm da face)
    "L_braco_curto_ate_porta": ([seg(0, 0, 402, 0), seg(0, 0, 0, 298)], [[], [porta(30.0, 120.0)]]),
    # braco inteiro de 25 cm
    "L_braco_curto": ([seg(0, 0, 402, 0), seg(0, 0, 0, 25)], [[], []]),
    # boneca de 13 cm entre a face da principal e a porta da parede que chega
    "T_boneca_curta": ([seg(-302, 0, 302, 0), seg(0, 0, 0, 298)], [[], [porta(27.0, 117.0)]]),
    # parede que chega com 20 cm
    "T_parede_que_chega_curta": ([seg(-302, 0, 302, 0), seg(0, 0, 0, 20)], [[], []]),
    # porta numa parede da cruz com a jamba a 10 cm do cruzamento (3 cm da face)
    "X_porta_a_3cm_da_face": ([seg(0, 302, 604, 302), seg(302, 0, 302, 604)], [[porta(312.0, 402.0)], []]),
}
# razao que o legado (e o CHANNEL com a flag desligada) da' ao compensador do no'
RAZAO_DESIGNADA = {"L": "L_CORNER_DEGRADED", "T": "T_INTERSECTION_INCOMING_DEGRADED",
                   "X": "X_INTERSECTION_DEGRADED"}


@pytest.fixture
def escada_com_compensador(monkeypatch):
    """Fixa as escadas de no' no comportamento que DEGRADA o no' para
    compensador: as candidatas pendentes que tiram o compensador da escada
    (R76 recuo, B19 de amarracao) desligadas, como estao no motor hoje."""
    monkeypatch.setattr(ws, "COMPENSATOR_NEVER_JUNCTION_BOND", False)
    monkeypatch.setattr(ws, "JUNCTION_BOND_B19_FALLBACK", False)


def _degradado(nome, estrategia=CHANNEL):
    return _resolve(nome, *DEGRADAM[nome], strategy=estrategia, tag="escada")


def _fills(cc):
    return [(ci, c) for ci, c in _compensadores(cc) if c.get("placement_reason") == FILL]


@pytest.mark.parametrize("nome", sorted(DEGRADAM))
def test_solver_channel_no_degradado_compensador_nao_designado_e_missing_acusa(nome, escada_com_compensador):
    """Item 12 (fluxo CHANNEL): nenhum compensador designado amarracao (A
    vazio, no resultado e na chamada direta); o compensador que a escada usa
    para fechar o no' sai com JUNCTION_UNRESOLVED_FILL (node_index mantido,
    DENTRO da regiao do no') e B acusa cada fiada desse no' com NO_BOND_PIECE,
    com o compensador entre os ocupantes. A flag do motor volta a False."""
    res, walls, nodes = _degradado(nome)
    cc = res["course_candidates"]
    assert res["channel_unresolved_junction_fill"] is True
    assert ws.COMPENSATOR_NODE_PIECE_UNDESIGNATED is False
    assert [(ci, c.get("placement_reason")) for ci, c in _compensadores(cc) if _designada(c)] == []
    assert res["compensator_as_junction_bond"] == [] == gate_a(cc, nodes, walls)

    fills = _fills(cc)
    assert fills, "a fixture deixou de degradar o no' para compensador"
    # todo compensador com node_index e' o fill do no' (nenhuma outra razao de no')
    assert set(c.get("placement_reason") for _ci, c in _compensadores(cc) if c.get("node_index") is not None) \
        == set([FILL])
    faltas = dict(((f["course_index"], f["node_index"]), f) for f in res["missing_required_junction_bond"])
    for ci, c in fills:
        ni = c["node_index"]
        assert nodes[ni]["kind"] == {"L": "L_CORNER", "T": "T_INTERSECTION", "X": "X_INTERSECTION"}[nome[0]]
        assert _conta(c, _amostras(nodes[ni], walls)) > 0
        f = faltas.get((ci, ni))
        assert f is not None and f["reason"] == "NO_BOND_PIECE", (ci, ni, f)
        o = c["origin_world"]
        assert [x for x in f["occupants"] if x["is_compensator"] and x["placement_reason"] == FILL
                and x["origin_cm"] == [round(_cm(o.X), 3), round(_cm(o.Y), 3)]], f["occupants"]


@pytest.mark.parametrize("nome", sorted(DEGRADAM))
def test_solver_legado_o_mesmo_compensador_segue_designado_e_A_o_acusa(nome, escada_com_compensador):
    """Item 12 (legado, strategy=None): nada da regra 76.1 liga - o resultado
    nao ganha as chaves novas - e o MESMO compensador (mesma fiada, codigo,
    centro, comprimento, parede) segue designado (L_CORNER_DEGRADED /
    T_INTERSECTION_INCOMING_DEGRADED / X_INTERSECTION_DEGRADED). A chamado
    direto acusa exatamente os designados; B chamado direto acusa as mesmas
    fiadas-no'."""
    res_c, _walls_c, _nodes_c = _degradado(nome)
    res_l, walls, nodes = _degradado(nome, None)
    for chave in ("compensator_as_junction_bond", "missing_required_junction_bond", "junction_bond_audit",
                  "channel_unresolved_junction_fill"):
        assert chave not in res_l
    cc = res_l["course_candidates"]
    legado = dict((_chave_fisica(ci, c), c) for ci, c in _compensadores(cc))
    fills = [(_chave_fisica(ci, c), c) for ci, c in _fills(res_c["course_candidates"])]
    assert fills
    for k, c in fills:
        assert k in legado, k
        assert (legado[k].get("placement_reason"), legado[k].get("node_index")) == \
            (RAZAO_DESIGNADA[nome[0]], c["node_index"])
    acusados = gate_a(cc, nodes, walls)
    designados = [(ci, c) for ci, c in _compensadores(cc) if _designada(c)]
    assert sorted(_chave_v(v) for v in acusados) == sorted(_chave(ci, c) for ci, c in designados)
    assert set(_chave(k[0], c) for k, c in fills) <= set(_chave_v(v) for v in acusados)
    assert all(v["evidence"] == ["DESIGNATED_NODE_PIECE"] for v in acusados)
    faltas = set((f["course_index"], f["node_index"]) for f in gate_b(cc, nodes, walls))
    assert set((k[0], c["node_index"]) for k, c in fills) <= faltas


@pytest.mark.parametrize("nome", sorted(DEGRADAM))
def test_solver_flag_desligada_mesma_geometria_so_muda_a_classificacao(nome, escada_com_compensador,
                                                                        monkeypatch):
    """Item 12 (flag): CHANNEL com CHANNEL_UNRESOLVED_JUNCTION_FILL_ENABLED
    ligada e desligada -> geometria fisica IDENTICA (tcr.physical_signature);
    a unica diferenca e' a razao dos compensadores do no' (JUNCTION_UNRESOLVED_FILL
    <-> <papel>_DEGRADED, node_index igual). Desligada, A acusa exatamente
    esses; ligada, nada. B e' o mesmo nos dois (mesma geometria)."""
    lig, walls, nodes = _degradado(nome)
    monkeypatch.setattr(m, "CHANNEL_UNRESOLVED_JUNCTION_FILL_ENABLED", False)
    des, walls_d, nodes_d = _resolve(nome, *DEGRADAM[nome], strategy=CHANNEL, tag="escada_flag_desligada")
    assert tcr.physical_signature(lig, walls) == tcr.physical_signature(des, walls_d)
    assert (lig["channel_unresolved_junction_fill"], des["channel_unresolved_junction_fill"]) == (True, False)

    def razoes(res):
        out = {}
        for ci, pecas in res["course_candidates"].items():
            for c in pecas:
                k = _chave_fisica(ci, c)
                assert k not in out, k
                out[k] = (c.get("placement_reason"), c.get("node_index"))
        return out

    r_lig, r_des = razoes(lig), razoes(des)
    assert set(r_lig) == set(r_des)
    difere = sorted(k for k in r_lig if r_lig[k] != r_des[k])
    assert difere
    assert set(r_lig[k][0] for k in difere) == set([FILL])
    assert set(r_des[k][0] for k in difere) == set([RAZAO_DESIGNADA[nome[0]]])
    assert all(r_lig[k][1] == r_des[k][1] is not None for k in difere)
    assert all(k[1] in COMP for k in difere)

    assert lig["compensator_as_junction_bond"] == []
    assert sorted(_chave_v(v) for v in des["compensator_as_junction_bond"]) == \
        sorted((k[0], k[1], round(k[2], 1), round(k[3], 1)) for k in difere)
    assert des["compensator_as_junction_bond"] == gate_a(des["course_candidates"], nodes_d, walls_d)
    assert _faltas(lig["missing_required_junction_bond"]) == _faltas(des["missing_required_junction_bond"])
    assert lig["junction_bond_audit"] == des["junction_bond_audit"]
    # e B acusa, nos dois, toda fiada-no' em que a razao mudou
    assert set((k[0], r_lig[k][1]) for k in difere) <= \
        set((f["course_index"], f["node_index"]) for f in lig["missing_required_junction_bond"])


# Corpus sintetico. Os comentarios dizem a GEOMETRIA; o que o motor fez com
# ela sai na mensagem do assert (medido, nunca suposto).
CORPUS = {
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
    # porta que comeca DENTRO da regiao da cruz (jamba a 2 cm do cruzamento)
    "cruz_porta_dentro_da_regiao": ([seg(0, 302, 604, 302), seg(302, 0, 302, 604)], [[porta(304.0, 394.0)], []]),
    "abertura_perto_do_no_T": tee_80(),
    "abertura_perto_do_no_L": DEGRADAM["L_braco_curto_ate_porta"],
    "parede_curta_L": DEGRADAM["L_braco_curto"],
    "parede_curta_T": DEGRADAM["T_parede_que_chega_curta"],
    "boneca_T": DEGRADAM["T_boneca_curta"],
    "cruz_degradada": DEGRADAM["X_porta_a_3cm_da_face"],
    # parede que chega a 10 / 20 cm da ponta livre da principal
    "no_perto_da_extremidade_10cm": ([seg(0, 0, 600, 0), seg(10, 0, 10, 298)], [[], []]),
    "no_perto_da_extremidade_20cm": ([seg(0, 0, 600, 0), seg(20, 0, 20, 298)], [[], []]),
    # porta / janela que comecam na ponta do braco do canto: o braco nao existe
    # na regiao do no' nas fiadas da abertura (encontro inexistente)
    "L_porta_no_canto": ([seg(0, 0, 402, 0), seg(0, 0, 0, 298)], [[porta(0.0, 90.0)], []]),
    "L_janela_no_canto": ([seg(0, 0, 402, 0), seg(0, 0, 0, 298)], [[janela(0.0, 120.0)], []]),
}


def _msg(nome, res, faltas_o, ausentes_o):
    razoes = {}
    for _ci, c in _compensadores(res["course_candidates"]):
        k = (c["logical_code"], str(c.get("placement_reason")))
        razoes[k] = razoes.get(k, 0) + 1
    return "%s: compensadores (codigo, razao)=%s | B=%s | oraculo=%s | not_required=%s / oraculo %s" % (
        nome, sorted(razoes.items()), _faltas(res["missing_required_junction_bond"]), sorted(faltas_o.items()),
        [(x["course_index"], x["node_index"]) for x in res["junction_bond_audit"]["not_required"]],
        sorted(ausentes_o))


@pytest.mark.parametrize("nome", sorted(CORPUS))
def test_corpus_channel_os_dois_gates_iguais_ao_oraculo_independente(nome):
    """Item 13: fluxo CHANNEL com as flags de HOJE. Para cada fixture, B do
    resultado (faltas com motivo, not_required, contagens) e' EXATAMENTE o
    oraculo de amostragem com as aberturas do solve, o apoio fisico e o
    nao-modular (por fiada fisica) do proprio resultado; A do resultado e' a
    chamada direta e o oraculo (designados por metadado, regioes por
    amostragem)."""
    lines, ops = CORPUS[nome]
    res, walls, nodes = _resolve(nome, lines, ops)
    cc = res["course_candidates"]
    # pre-condicao do oraculo: as aberturas do solve sao as brutas (nenhuma
    # passagem livre estendida ate' o topo neste corpus)
    assert not (res.get("opening_reinforcement") or {}).get("free_to_top")
    faltas_o, ausentes_o, designados_o = oraculo(
        cc, nodes, walls, openings=ops, sem_apoio=(res.get("physical_support") or {}).get("items"),
        nao_modular=_nao_modular_fisico(res), catalogo=CATALOGO)
    msg = _msg(nome, res, faltas_o, ausentes_o)
    obtido = dict(((f["course_index"], f["node_index"]), f["reason"]) for f in res["missing_required_junction_bond"])
    assert len(obtido) == len(res["missing_required_junction_bond"]), msg
    assert obtido == faltas_o, msg
    au = res["junction_bond_audit"]
    assert set((x["course_index"], x["node_index"]) for x in au["not_required"]) == ausentes_o, msg
    nos = sum(1 for n in nodes if n.get("kind") in TIPOS_DE_NO)
    assert au["checked"] == au["valid"] + len(obtido), msg
    assert au["checked"] + len(ausentes_o) == nos * len(cc), msg
    assert res["compensator_as_junction_bond"] == gate_a(cc, nodes, walls), msg
    assert _gate_a_como_oraculo(res["compensator_as_junction_bond"]) == designados_o == {}, msg


@pytest.mark.parametrize("nome", sorted(CORPUS))
def test_corpus_legado_os_dois_gates_chamados_direto_iguais_ao_oraculo(nome):
    """Item 13 no legado (o resultado nao traz os gates): A e B chamados
    direto com as aberturas brutas e a faixa da fiada; iguais ao oraculo. E'
    aqui que o oraculo de A tem designados de verdade (as fixtures que
    degradam)."""
    lines, ops = CORPUS[nome]
    res, walls, nodes = _resolve(nome, lines, ops, strategy=None)
    cc = res["course_candidates"]
    itens = (res.get("physical_support") or {}).get("items")
    nao_modular = _nao_modular_fisico(res)
    faltas_o, ausentes_o, designados_o = oraculo(cc, nodes, walls, openings=ops, sem_apoio=itens,
                                                 nao_modular=nao_modular, catalogo=CATALOGO)
    au = auditoria(cc, nodes, walls, openings_per_wall=ops, course_band_ft=_faixa_ft, unsupported=itens,
                   non_modular=nao_modular, catalog=CATALOGO, opening_tol_ft=ft(TOL_FIADA_CM))
    assert dict(((f["course_index"], f["node_index"]), f["reason"]) for f in au["missing"]) == faltas_o
    assert set((x["course_index"], x["node_index"]) for x in au["not_required"]) == ausentes_o
    assert _gate_a_como_oraculo(gate_a(cc, nodes, walls)) == designados_o


def test_corpus_nao_e_vacuo():
    """Nao-vacuidade do item 13: o corpus CHANNEL exercita faltas de mais de
    um motivo, encontro inexistente, nos validos e um no' degradado de cada
    tipo; o legado tem designados para o oraculo de A."""
    motivos, tipos_fill, ausentes, validos, designados = set(), set(), 0, 0, 0
    for nome in sorted(CORPUS):
        res, walls, nodes = _resolve(nome, *CORPUS[nome])
        motivos |= set(f["reason"] for f in res["missing_required_junction_bond"])
        ausentes += len(res["junction_bond_audit"]["not_required"])
        validos += res["junction_bond_audit"]["valid"]
        tipos_fill |= set(nodes[c["node_index"]]["kind"] for _ci, c in _fills(res["course_candidates"]))
        leg, _w, _n = _resolve(nome, *CORPUS[nome], strategy=None)
        designados += sum(1 for _ci, c in _compensadores(leg["course_candidates"]) if _designada(c))
    assert set(["EMPTY_REGION", "NO_BOND_PIECE", "BOND_PIECE_UNSUPPORTED"]) <= motivos, motivos
    assert tipos_fill == set(TIPOS_DE_NO), tipos_fill
    assert ausentes > 0 and validos > 0 and designados > 0


def test_solver_compensador_encostado_em_no_valido_ou_inexistente_nao_e_acusado():
    """Caso VALIDO no solver: no corpus CHANNEL ha' compensador comum
    ENCOSTADO (fora da regiao, a <= 3 cm dela) num no' que, naquela fiada,
      * tem peca B34/B54 da parede do no' cobrindo a regiao inteira
        (amostragem) - o motor mede 2 cm nestes; ou
      * nao tem encontro (a abertura tira a parede da regiao) - 1 cm.
    Nenhum dos dois gates acusa esse compensador nem essa fiada-no'. A
    distancia aqui so' ESCOLHE os casos de nao-vacuidade; quem decide e' a
    amarracao (ou o encontro inexistente)."""
    achados = {"amarrado": [], "inexistente": []}
    for nome in sorted(CORPUS):
        lines, ops = CORPUS[nome]
        res, walls, nodes = _resolve(nome, lines, ops)
        cc = res["course_candidates"]
        faltas = set((f["course_index"], f["node_index"]) for f in res["missing_required_junction_bond"])
        acusados = set(_chave_v(v) for v in res["compensator_as_junction_bond"])
        for ni, no in enumerate(nodes):
            if no.get("kind") not in TIPOS_DE_NO:
                continue
            pts = _amostras(no, walls)
            paredes = _paredes_do_no(no)
            for ci, c in _compensadores(cc):
                if c.get("wall_idx") not in paredes or _designada(c):
                    continue
                folga = _folga_cm(c, no, walls)
                if not 0.0 < folga <= 3.0:
                    continue
                if any(p["logical_code"] in AMARRACAO and p.get("wall_idx") in paredes
                       and _conta(p, pts) == len(pts) for p in cc[ci]):
                    tipo = "amarrado"
                elif any(_parede_ausente(no, walls, ops, ci, w) for w in paredes):
                    tipo = "inexistente"
                else:
                    continue
                assert (ci, ni) not in faltas, (nome, tipo, ci, ni)
                assert _chave(ci, c) not in acusados, (nome, tipo, ci, c)
                achados[tipo].append((nome, ci, ni, c["logical_code"], c.get("placement_reason"), round(folga, 2)))
    assert achados["amarrado"] and achados["inexistente"], achados
    # nao-vacuidade de verdade: encostado = no maximo 2 juntas de 1 cm
    assert min(a[-1] for a in achados["amarrado"]) <= 2.0 + 1e-6, achados["amarrado"]
    assert min(a[-1] for a in achados["inexistente"]) <= 2.0 + 1e-6, achados["inexistente"]
