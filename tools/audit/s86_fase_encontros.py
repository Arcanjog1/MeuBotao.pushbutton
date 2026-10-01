# -*- coding: utf-8 -*-
"""Bancada da SECAO 86.2 - so' o ESTAGIO DE ENCONTROS (sem preenchimento) sobre o
corpus BUTANTA versionado: quem ocupa o quadrado de cada no' na fiada 0, motor x
projeto humano.

STATUS: EVIDENCIA / NAO NORMA. Nenhuma decisao do motor e' reimplementada aqui:
o grafo, as aberturas, a banda da fiada 0, o papel por fiada (77) e a decisao de
fase vem das funcoes REAIS (`build_context`, `_group_course_indices_by_opening_band`,
`junction_role_table`, `solve_all_intersections`). O que este modulo faz e' so'
REGUA: extrair os encontros da geometria e comparar o ocupante da fiada 0.

Barato (uma resolucao de nos, nenhuma de preenchimento): cabe na maquina com
pouca memoria. Uso:

    py -3 tools/audit/s86_fase_encontros.py --human <human_rows_unpad.json> [-v] [--off]

`--off` mede com a secao 86.2 desligada (busca gulosa da 82). Sem `--human` so'
imprime a fase do motor por encontro. O arquivo do humano (fileiras por
parede/fiada sem a folga de 1 cm da caixa da familia) NAO e' versionado.
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import s74_corpus as S  # noqa: E402

CM = S.CM_PER_FT


def _eixos(geo):
    out = []
    for i, w in enumerate(geo["walls"]):
        p0, p1 = w["p0_cm"], w["p1_cm"]
        comp = w["length_cm"]
        d = ((p1[0] - p0[0]) / comp, (p1[1] - p0[1]) / comp)
        out.append(dict(i=i, p0=p0, p1=p1, L=comp, d=d, vert=abs(d[0]) < 0.5))
    return out


def encontros(geo):
    """Encontros L/T/X entre eixos ORIGINAIS ortogonais (geometria pura)."""
    eixos = _eixos(geo)

    def t_de(w, pt):
        return (pt[0] - w["p0"][0]) * w["d"][0] + (pt[1] - w["p0"][1]) * w["d"][1]
    out = []
    for a in eixos:
        for b in eixos:
            if a["i"] >= b["i"] or a["vert"] == b["vert"]:
                continue
            v, h = (a, b) if a["vert"] else (b, a)
            x, y = v["p0"][0], h["p0"][1]
            ys = sorted([v["p0"][1], v["p1"][1]])
            xs = sorted([h["p0"][0], h["p1"][0]])
            if not (xs[0] - 1 <= x <= xs[1] + 1 and ys[0] - 1 <= y <= ys[1] + 1):
                continue
            ta, tb = t_de(a, (x, y)), t_de(b, (x, y))
            ea = "e0" if ta < 8 else ("e1" if ta > a["L"] - 8 else "mid")
            eb = "e0" if tb < 8 else ("e1" if tb > b["L"] - 8 else "mid")
            kind = {0: "X", 1: "T", 2: "L"}[(ea != "mid") + (eb != "mid")]
            out.append(dict(a=a["i"], b=b["i"], ta=ta, tb=tb, kind=kind, pos=(x, y)))
    return out


def _humano(caminho):
    d = json.load(open(caminho))
    out = {}
    for k, v in d["rows"].items():
        w, c = [int(x) for x in k.split(":")]
        out.setdefault(w, {})[c] = sorted(v)
    return out


def _ocupante_humano(H, j):
    """Ocupante da fiada 0 por maioria das fiadas 0-11 (fiada impar invertida)."""
    def cobre(itens, lo, hi):
        return sum(max(0, min(hi, it[1]) - max(lo, it[0])) for it in itens or [])
    votos = collections.Counter()
    for c in range(12):
        ca = cobre(H.get(j["a"], {}).get(c), j["ta"] - 7, j["ta"] + 7)
        cb = cobre(H.get(j["b"], {}).get(c), j["tb"] - 7, j["tb"] + 7)
        oc = "a" if (ca > 9 and cb < 5) else ("b" if (cb > 9 and ca < 5) else None)
        if oc is None:
            continue
        if c % 2 == 1:
            oc = "b" if oc == "a" else "a"
        votos[oc] += 1
    return votos.most_common(1)[0][0] if votos else "-"


def estagio_de_encontros(geo, fase86=True, num_courses=14):
    """Resolve SO' os nos, na banda da fiada 0, como o caminho geral (sem reforco
    adicional) faz na primeira banda. Restaura todas as chaves."""
    m, ws = S.engine()
    ctx = S.build_context(geo)
    nodes, walls, e2n, opw = ctx["nodes"], ctx["walls"], ctx["e2n"], ctx["openings_per_wall"]
    catalogo = S.catalog(geo)
    salvo = []

    def liga(mod, nome, valor):
        salvo.append((mod, nome, getattr(mod, nome)))
        setattr(mod, nome, valor)
    geral = bool(m.GENERAL_TIE_PARITY_ENABLED)
    usa86 = bool(geral and fase86 and m.GENERAL_PHASE_RELATION_ENABLED)
    liga(ws, "TIE_PARITY_FILL_BALANCE", geral)
    liga(ws, "TIE_PARITY_FILL_OPENING_BOUNDARIES", geral)
    liga(ws, "TIE_PARITY_STRUCTURAL_VETO", geral)
    liga(ws, "TIE_PARITY_FILL_STAGGER", geral)
    liga(ws, "TIE_PARITY_FILL_NODE_KINDS", ("T_INTERSECTION", "L_CORNER") if usa86 else ("T_INTERSECTION",))
    liga(ws, "PHASE_RELATION_COMPONENTS", usa86)
    liga(ws, "TIE_PARITY_FILL_ALL_OPENINGS", opw)
    liga(ws, "T_ROOM_PHYSICAL_TOLERANCE", True)
    liga(ws, "T_DEGRADED_L_ROOM_FROM_CONTACT", True)
    liga(ws, "JUNCTION_ROLE_BY_COURSE", True)
    liga(ws, "COMPENSATOR_NODE_PIECE_UNDESIGNATED", True)
    liga(ws, "RESIDUAL_NODE_BOUNDED_ABSORPTION_ENABLED", True)
    liga(ws, "JUNCTION_ROLE_TABLE", None)
    liga(ws, "JUNCTION_BAND_ROLES", None)
    try:
        passo, _erro = m._course_height_ft(catalogo, None)
        altura = passo - m._cm_to_ft(m.COURSE_JOINT_CM)
        ws.JUNCTION_ROLE_TABLE = ws.junction_role_table(
            nodes, walls, opw, m._free_to_top_band(catalogo, 0.0), num_courses, catalogo,
            m.OPENING_COURSE_BAND_TOLERANCE_FT)
        cursos, filtradas = m._group_course_indices_by_opening_band(opw, 0.0, passo, altura, num_courses)[0]
        ws.JUNCTION_BAND_ROLES = ws.junction_band_roles(ws.JUNCTION_ROLE_TABLE, cursos, nodes)
        out = ws.solve_all_intersections(nodes, walls, catalogo, openings_per_wall=filtradas, end_to_node=e2n)
    finally:
        for mod, nome, valor in reversed(salvo):
            setattr(mod, nome, valor)
    return ctx, out


def ocupante_motor(ctx, out, no, parede_a, parede_b):
    _m, ws = S.engine()
    nodes, walls = ctx["nodes"], ctx["walls"]
    pecas = [c for c in out["candidates"] if c.get("node_index") == no]
    passa = {}
    for tag, w in (("a", parede_a), ("b", parede_b)):
        t = ws._phase_t_cm(walls, w, nodes[no]["point"])
        passa[tag] = ws._phase_passes_course_a(pecas, w, walls, t)
    if passa["a"] != passa["b"]:
        return "a" if passa["a"] else "b"
    return "?" if passa["a"] else "-"


def comparar(geo, humano=None, fase86=True, verbose=False):
    ctx, out = estagio_de_encontros(geo, fase86=fase86)
    nodes = ctx["nodes"]
    H = _humano(humano) if humano else None
    linhas, iguais = [], 0
    for j in encontros(geo):
        melhor = None
        for ni, n in enumerate(nodes):
            if n.get("kind") not in ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION"):
                continue
            p = n["point"]
            d = ((p.X * CM - j["pos"][0]) ** 2 + (p.Y * CM - j["pos"][1]) ** 2) ** 0.5
            if melhor is None or d < melhor[0]:
                melhor = (d, ni)
        motor = ocupante_motor(ctx, out, melhor[1], j["a"], j["b"]) if melhor and melhor[0] < 20 else "N"
        hum = _ocupante_humano(H, j) if H else None
        iguais += int(hum == motor)
        linhas.append((j, melhor[1] if melhor else None, hum, motor))
    if H:
        print("encontros com a fase (fiada 0) do humano: %d/%d" % (iguais, len(linhas)))
    print("phase_relation:", dict((k, v) for k, v in (out.get("phase_relation") or {}).items()
                                  if k != "components"))
    if verbose:
        for j, no, hum, motor in linhas:
            print("%s n%-3s W%-2d x W%-2d humano=%s motor=%s %s" % (
                j["kind"], no, j["a"], j["b"], hum, motor, "" if (hum is None or hum == motor) else "<<"))
    return iguais, len(linhas)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--human", default=None)
    ap.add_argument("--off", action="store_true")
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args(argv)
    comparar(S.geometry(), a.human, fase86=not a.off, verbose=a.v)


if __name__ == "__main__":
    main()
