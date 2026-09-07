# -*- coding: utf-8 -*-
"""CR-B / §8: PROJECAO do candidato "DUAS PAREDES SEPARADAS".

NAO aplica nada. Gera o candidato em diretorio TEMPORARIO, lado a lado com
o gabarito atual, e mede as consequencias por IDENTIDADE ESTAVEL
(coordenada de mundo), nunca por `W0xx`.

Metodo - usa o codigo de PRODUCAO em tudo, com uma unica injecao cirurgica:
  1. dump sintetico a partir de `reference.json` (round-trip provado
     identico em `roundtrip_probe.py`);
  2. `build_project` normal -> gabarito ATUAL reproduzido;
  3. identifica os 19 pelo criterio ESTRUTURAL C1 (reserva de no' nas duas
     jambas), sem limiar de largura;
  4. `build_project` de novo, com `split_axis_into_walls` embrulhado para
     tambem cortar nos pontos de C1 -> candidato B;
  5. compara.

Nenhuma constante de producao e' alterada. Nenhum arquivo de
`nuvem/benchmark/projects/**` e' escrito.
"""
import collections
import json
import math
import os
import sys

ROOT = os.environ.get("REPO_ROOT", "/home/user/MeuBotao.pushbutton")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from nuvem.benchmark.extract import reconstruct  # noqa: E402

FACE_TOL_CM = 1.0
PERP_REACH_CM = 60.0


def axis(w):
    sx, sy = w["start_cm"]
    ex, ey = w["end_cm"]
    n = math.hypot(ex - sx, ey - sy)
    return (sx, sy), ((ex - sx) / n, (ey - sy) / n)


def pr(o, d, p):
    dx, dy = p[0] - o[0], p[1] - o[1]
    return dx * d[0] + dy * d[1], -dx * d[1] + dy * d[0]


def dump_from_reference(ref):
    types, index_of, instances = [], {}, []
    blocks = []
    for wall in ref.get("walls") or []:
        for row in wall.get("rows") or []:
            blocks.extend(row.get("blocks") or [])
    blocks.extend(ref.get("orphan_blocks") or [])
    for b in blocks:
        key = (b["type_name"], b["family"], b["length_cm"], b["height_cm"],
               b["width_cm"])
        if key not in index_of:
            index_of[key] = len(types)
            types.append({"index": len(types), "type_name": b["type_name"],
                          "family": b["family"], "length_cm": b["length_cm"],
                          "height_cm": b["height_cm"], "width_cm": b["width_cm"]})
        instances.append([index_of[key], b["center_cm"][0], b["center_cm"][1],
                          b["z_cm"], b["rotation_deg"], bool(b["mirrored"])])
    return {"types": types, "instances": instances}


def c1_cases(project):
    """Vaos cujas DUAS jambas coincidem com a face interna de uma parede
    perpendicular (reserva de no'). Sem limiar de largura."""
    hits = []
    for host in project["walls"]:
        o, d = axis(host)
        for op in host.get("openings") or []:
            lo_ok = hi_ok = False
            for w in project["walls"]:
                if w["id"] == host["id"]:
                    continue
                o2, d2 = axis(w)
                if abs(d2[0] * d[0] + d2[1] * d[1]) > 0.05:
                    continue
                t0, s0 = pr(o, d, w["start_cm"])
                t1, s1 = pr(o, d, w["end_cm"])
                if not (min(s0, s1) - PERP_REACH_CM <= 0 <= max(s0, s1) + PERP_REACH_CM):
                    continue
                tc = (t0 + t1) / 2.0
                half = (w.get("thickness_cm") or 14.0) / 2.0
                if abs((tc + half) - op["t_start_cm"]) <= FACE_TOL_CM:
                    lo_ok = True
                if abs((tc - half) - op["t_end_cm"]) <= FACE_TOL_CM:
                    hi_ok = True
            if lo_ok and hi_ok:
                hits.append({
                    "wall": host["id"],
                    "t_range": [op["t_start_cm"], op["t_end_cm"]],
                    "largura_cm": round(op["t_end_cm"] - op["t_start_cm"], 2),
                    "xy_lo": [round(o[0] + d[0] * op["t_start_cm"], 3),
                              round(o[1] + d[1] * op["t_start_cm"], 3)],
                    "xy_hi": [round(o[0] + d[0] * op["t_end_cm"], 3),
                              round(o[1] + d[1] * op["t_end_cm"], 3)],
                })
    return hits


def build_with_splits(dump, project_id, cortes_xy):
    """`build_project` com `split_axis_into_walls` embrulhado para cortar
    tambem nos intervalos de `cortes_xy` (pares de pontos de mundo)."""
    original = reconstruct.split_axis_into_walls

    def wrapped(group):
        walls = original(group)
        out = []
        for w in walls:
            o = w["start_cm"]
            d = w["direction"]
            pontos = []
            for lo_xy, hi_xy in cortes_xy:
                tlo, slo = pr(o, d, lo_xy)
                thi, shi = pr(o, d, hi_xy)
                if abs(slo) > 2.0 or abs(shi) > 2.0:
                    continue
                a, b = min(tlo, thi), max(tlo, thi)
                comp = math.hypot(w["end_cm"][0] - o[0], w["end_cm"][1] - o[1])
                if a > 1.0 and b < comp - 1.0:
                    pontos.append((a, b))
            if not pontos:
                out.append(w)
                continue
            pontos.sort()
            restantes = list(w["blocks"])
            fronteiras = [-1e9] + [p for pair in pontos for p in pair] + [1e9]
            for i in range(0, len(fronteiras) - 1, 2):
                lo, hi = fronteiras[i], fronteiras[i + 1]
                bl = []
                for b in restantes:
                    tc, _s = pr(o, d, b["center_cm"])
                    if lo <= tc <= hi:
                        bl.append(b)
                if not bl:
                    continue
                ext = []
                for b in bl:
                    tc, _s = pr(o, d, b["center_cm"])
                    ext.append((tc - b["length_cm"] / 2.0, tc + b["length_cm"] / 2.0))
                t_lo = min(e[0] for e in ext)
                t_hi = max(e[1] for e in ext)
                if t_hi - t_lo < reconstruct.MIN_WALL_LENGTH_CM:
                    continue
                out.append({
                    "start_cm": (o[0] + d[0] * t_lo, o[1] + d[1] * t_lo),
                    "end_cm": (o[0] + d[0] * t_hi, o[1] + d[1] * t_hi),
                    "direction": d, "blocks": bl, "t_offset": t_lo,
                })
        return out

    reconstruct.split_axis_into_walls = wrapped
    try:
        return reconstruct.build_project(dump, project_id, source="revit_reference")
    finally:
        reconstruct.split_axis_into_walls = original


def resumo(p):
    op = [o for w in p["walls"] for o in (w.get("openings") or [])]
    jt = collections.Counter(j["type"] for w in p["walls"]
                             for j in (w.get("junctions") or []))
    nb = sum(len(r.get("blocks") or []) for w in p["walls"]
             for r in (w.get("rows") or []))
    return {"paredes": len(p["walls"]), "aberturas": len(op),
            "blocos_em_paredes": nb, "orfaos": len(p.get("orphan_blocks") or []),
            "juncoes_por_tipo": dict(sorted(jt.items())),
            "comprimento_total_cm": round(sum(w["length_cm"] for w in p["walls"]), 1)}


def main():
    out = {}
    for proj in ["torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"]:
        ref = json.load(open(os.path.join(ROOT, "nuvem/benchmark/projects",
                                          proj, "reference.json"), encoding="utf-8"))
        dump = dump_from_reference(ref)
        atual = reconstruct.build_project(dump, proj, source="revit_reference")
        casos = c1_cases(atual)
        cortes = [(c["xy_lo"], c["xy_hi"]) for c in casos]
        cand = build_with_splits(dump, proj, cortes)

        a, b = resumo(atual), resumo(cand)
        larg = collections.Counter(c["largura_cm"] for c in casos)
        print("=" * 92)
        print("%s   casos C1 (reserva de no' nas duas jambas) = %d   larguras=%s"
              % (proj, len(casos), dict(sorted(larg.items()))))
        print("  paredes hospedeiras distintas: %d"
              % len({c["wall"] for c in casos}))
        print("  %-24s %-14s %-14s %s" % ("", "ATUAL", "CANDIDATO B", "delta"))
        for k in ["paredes", "aberturas", "blocos_em_paredes", "orfaos",
                  "comprimento_total_cm"]:
            print("  %-24s %-14s %-14s %+g" % (k, a[k], b[k], b[k] - a[k]))
        tipos = sorted(set(a["juncoes_por_tipo"]) | set(b["juncoes_por_tipo"]))
        for t in tipos:
            x = a["juncoes_por_tipo"].get(t, 0)
            y = b["juncoes_por_tipo"].get(t, 0)
            print("  juncoes %-16s %-14s %-14s %+d" % (t, x, y, y - x))
        out[proj] = {"casos_C1": casos, "ATUAL": a, "CANDIDATO_B": b,
                     "n_paredes_hospedeiras": len({c["wall"] for c in casos})}
    p = os.path.join(HERE, "projection_split.json")
    json.dump(out, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False,
              sort_keys=True)
    print("escrito:", p)


if __name__ == "__main__":
    main()
