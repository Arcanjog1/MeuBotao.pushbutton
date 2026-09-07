# -*- coding: utf-8 -*-
"""CR-B / §7: divergencias entre a GEOMETRIA MEDIDA (input.json do TGD) e a
MODULACAO HUMANA (reference.json), nas 19 jambas.

Separa FATO (o numero medido), INFERENCIA (a leitura) e DECISAO HUMANA
(o que fica para o usuario). NAO cria tolerancia nova.

So' o TGD entra: o `input.json` do TP1 e' derivado do proprio gabarito
(`input_from_reference`), logo nao e' fonte independente.

READ-ONLY.
"""
import json
import math
import os

ROOT = os.environ.get("REPO_ROOT", "/home/user/MeuBotao.pushbutton")
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = "torre_easy_lo_r00_tgd"
LATERAL_CM = 45.0


def axis(w):
    sx, sy = w["start_cm"]
    ex, ey = w["end_cm"]
    n = math.hypot(ex - sx, ey - sy)
    return (sx, sy), ((ex - sx) / n, (ey - sy) / n)


def pr(o, d, p):
    dx, dy = p[0] - o[0], p[1] - o[1]
    return dx * d[0] + dy * d[1], -dx * d[1] + dy * d[0]


def main():
    ref = json.load(open(os.path.join(ROOT, "nuvem/benchmark/projects", PROJ,
                                      "reference.json"), encoding="utf-8"))
    inp = json.load(open(os.path.join(ROOT, "nuvem/benchmark/projects", PROJ,
                                      "input.json"), encoding="utf-8"))
    dossier = json.load(open(os.path.join(HERE, "case_dossier.json"),
                             encoding="utf-8"))[PROJ]["casos"]
    walls = {w["id"]: w for w in ref["walls"]}

    linhas, out = [], []
    for c in dossier:
        host = walls[c["wall_id_reference"]]
        o, d = axis(host)
        cons = c["consenso_cm"]
        # paredes medidas PARALELAS ao host, a ate' LATERAL_CM
        fim_antes, ini_depois = [], []
        for w in inp["walls"]:
            o2, d2 = axis(w)
            if abs(d2[0] * d[0] + d2[1] * d[1]) < 0.99:
                continue
            t0, s0 = pr(o, d, w["start_cm"])
            t1, s1 = pr(o, d, w["end_cm"])
            lo, hi = min(t0, t1), max(t0, t1)
            if abs((s0 + s1) / 2.0) > LATERAL_CM:
                continue
            if lo < cons[0] + 1.0:
                fim_antes.append((hi, w["id"], round((s0 + s1) / 2.0, 2)))
            if hi > cons[1] - 1.0:
                ini_depois.append((lo, w["id"], round((s0 + s1) / 2.0, 2)))
        borda_lo = max(fim_antes, default=None)
        borda_hi = min(ini_depois, default=None)
        d_lo = round(borda_lo[0] - cons[0], 2) if borda_lo else None
        d_hi = round(borda_hi[0] - cons[1], 2) if borda_hi else None
        out.append({
            "wall_id_reference": host["id"], "consenso_cm": cons,
            "jamba_lo_xy_cm": c["identidade_fisica"]["jamba_lo_xy_cm"],
            "jamba_hi_xy_cm": c["identidade_fisica"]["jamba_hi_xy_cm"],
            "medido_antes": borda_lo, "medido_depois": borda_hi,
            "divergencia_jamba_lo_cm": d_lo, "divergencia_jamba_hi_cm": d_hi,
        })
        linhas.append("  %-6s cons=%-16s | lo: %-28s dif=%-8s | hi: %-28s dif=%s" % (
            host["id"], cons,
            ("%s@%.2f off=%+.1f" % (borda_lo[1], borda_lo[0], borda_lo[2])) if borda_lo else "SEM PAREDE MEDIDA",
            d_lo,
            ("%s@%.2f off=%+.1f" % (borda_hi[1], borda_hi[0], borda_hi[2])) if borda_hi else "SEM PAREDE MEDIDA",
            d_hi))
    print(PROJ, "- fim da parede MEDIDA vs jamba do consenso HUMANO")
    print("\n".join(linhas))
    exatos = sum(1 for r in out
                 if r["divergencia_jamba_lo_cm"] is not None
                 and r["divergencia_jamba_hi_cm"] is not None
                 and abs(r["divergencia_jamba_lo_cm"]) <= 0.3
                 and abs(r["divergencia_jamba_hi_cm"]) <= 0.3)
    print("\n>> jambas COM parede medida terminando a <=0,3cm nas DUAS bordas: %d de 19" % exatos)
    for r in out:
        dl, dh = r["divergencia_jamba_lo_cm"], r["divergencia_jamba_hi_cm"]
        if dl is None or dh is None or abs(dl) > 0.3 or abs(dh) > 0.3:
            print("   RESIDUAL: %-6s cons=%-16s dif_lo=%-8s dif_hi=%s"
                  % (r["wall_id_reference"], r["consenso_cm"], dl, dh))
    p = os.path.join(HERE, "measured_vs_human.json")
    json.dump(out, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False,
              sort_keys=True)
    print("escrito:", p)


if __name__ == "__main__":
    main()
