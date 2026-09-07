# -*- coding: utf-8 -*-
"""CR-B: os 9 casos do TGD em que o buraco medido NAO bate com o consenso.

Amplia a busca: qualquer parede do input.json (MEDIDO, TGD) cujo eixo passe
a ate' LATERAL_CM do eixo do host e cuja projecao toque o envelope.
Objetivo: descobrir se o 'nao bate' e' ausencia de parede medida ou
DESLOCAMENTO LATERAL / recorte diferente do pareamento de eixos.

READ-ONLY.
"""
import json
import math
import os

ROOT = os.environ.get("REPO_ROOT", "/home/user/MeuBotao.pushbutton")
HERE = os.path.dirname(os.path.abspath(__file__))
LATERAL_CM = 45.0


def axis(w):
    sx, sy = w["start_cm"]
    ex, ey = w["end_cm"]
    n = math.hypot(ex - sx, ey - sy)
    return (sx, sy), ((ex - sx) / n, (ey - sy) / n)


def proj(o, d, p):
    dx, dy = p[0] - o[0], p[1] - o[1]
    return dx * d[0] + dy * d[1], -dx * d[1] + dy * d[0]


def main():
    proj_name = "torre_easy_lo_r00_tgd"
    ref = json.load(open(os.path.join(ROOT, "nuvem/benchmark/projects",
                                      proj_name, "reference.json"), encoding="utf-8"))
    inp = json.load(open(os.path.join(ROOT, "nuvem/benchmark/projects",
                                      proj_name, "input.json"), encoding="utf-8"))
    dossier = json.load(open(os.path.join(HERE, "case_dossier.json"),
                             encoding="utf-8"))[proj_name]["casos"]
    walls = {w["id"]: w for w in ref["walls"]}

    out = []
    for c in dossier:
        if c["eixo_medido__buraco_bate_consenso"]:
            continue
        host = walls[c["wall_id_reference"]]
        o, d = axis(host)
        env, cons = c["envelope_cm"], c["consenso_cm"]
        viz = []
        for w in inp["walls"]:
            o2, d2 = axis(w)
            dot = abs(d2[0] * d[0] + d2[1] * d[1])
            if dot < 0.99:                      # so' PARALELAS ao host
                continue
            t0, s0 = proj(o, d, w["start_cm"])
            t1, s1 = proj(o, d, w["end_cm"])
            lo, hi = min(t0, t1), max(t0, t1)
            s = (s0 + s1) / 2.0
            if abs(s) > LATERAL_CM:
                continue
            if hi < env[0] - 5.0 or lo > env[1] + 5.0:
                continue
            viz.append({"id": w["id"], "t": [round(lo, 2), round(hi, 2)],
                        "offset_lateral_cm": round(s, 2),
                        "comprimento_cm": w.get("length_cm"),
                        "espessura_cm": w.get("thickness_cm")})
        viz.sort(key=lambda v: (v["offset_lateral_cm"], v["t"][0]))
        out.append({"wall_id_reference": host["id"], "envelope_cm": env,
                    "consenso_cm": cons,
                    "jamba_lo_xy_cm": c["identidade_fisica"]["jamba_lo_xy_cm"],
                    "jamba_hi_xy_cm": c["identidade_fisica"]["jamba_hi_xy_cm"],
                    "paredes_medidas_paralelas_a_45cm": viz})

    for c in out:
        print("=== ref=%-6s cons=%-16s env=%-16s  XY %s -> %s" % (
            c["wall_id_reference"], c["consenso_cm"], c["envelope_cm"],
            c["jamba_lo_xy_cm"], c["jamba_hi_xy_cm"]))
        if not c["paredes_medidas_paralelas_a_45cm"]:
            print("    NENHUMA parede medida paralela dentro de 45cm tocando o envelope")
        for v in c["paredes_medidas_paralelas_a_45cm"]:
            print("    inp %-6s t=[%9.2f,%9.2f] offset=%+7.2f len=%7.2f esp=%s"
                  % (v["id"], v["t"][0], v["t"][1], v["offset_lateral_cm"],
                     v["comprimento_cm"], v["espessura_cm"]))
    path = os.path.join(HERE, "measured_neighbourhood.json")
    json.dump(out, open(path, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False, sort_keys=True)
    print("escrito:", path)


if __name__ == "__main__":
    main()
