# -*- coding: utf-8 -*-
"""CR-B / §3+§7: cada jamba dos 19 esta' confirmada pela GEOMETRIA MEDIDA?

Uma jamba fisica pode ser confirmada de DUAS formas, ambas medidas:
  (a) FIM DE PAREDE COLINEAR - uma parede medida paralela ao host termina
      (ou comeca) na jamba;
  (b) FACE DE PERPENDICULAR - a face proxima de uma parede medida
      perpendicular cai na jamba (a parede do host morre no no').

O teste colinear sozinho (usado na CR-A) subconta: perde (b).

So' TGD - o `input.json` do TP1 e' derivado do gabarito. READ-ONLY.
"""
import json
import math
import os

ROOT = os.environ.get("REPO_ROOT", "/home/user/MeuBotao.pushbutton")
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = "torre_easy_lo_r00_tgd"
TOL_CM = 0.3
LATERAL_CM = 45.0
PERP_REACH_CM = 60.0


def axis(w):
    sx, sy = w["start_cm"]
    ex, ey = w["end_cm"]
    n = math.hypot(ex - sx, ey - sy)
    return (sx, sy), ((ex - sx) / n, (ey - sy) / n)


def pr(o, d, p):
    dx, dy = p[0] - o[0], p[1] - o[1]
    return dx * d[0] + dy * d[1], -dx * d[1] + dy * d[0]


def confirma(o, d, t_jamba, lado, inp_walls):
    """lado=-1: a parede esta' ANTES da jamba; +1: DEPOIS."""
    for w in inp_walls:
        o2, d2 = axis(w)
        dot = d2[0] * d[0] + d2[1] * d[1]
        t0, s0 = pr(o, d, w["start_cm"])
        t1, s1 = pr(o, d, w["end_cm"])
        if abs(dot) >= 0.99:                                   # COLINEAR
            if abs((s0 + s1) / 2.0) > LATERAL_CM:
                continue
            borda = max(t0, t1) if lado < 0 else min(t0, t1)
            if abs(borda - t_jamba) <= TOL_CM:
                return ("FIM_DE_PAREDE_COLINEAR", w["id"],
                        round(borda - t_jamba, 3), round((s0 + s1) / 2.0, 2))
        elif abs(dot) <= 0.05:                                 # PERPENDICULAR
            if not (min(s0, s1) - PERP_REACH_CM <= 0 <= max(s0, s1) + PERP_REACH_CM):
                continue
            tc = (t0 + t1) / 2.0
            half = (w.get("thickness_cm") or 14.0) / 2.0
            # testa as DUAS faces: uma perpendicular pode ficar do lado
            # esperado OU atravessar a jamba (caso de par de paredes
            # paralelas no CAD medido - ver W053/W100 do TGD).
            for face in (tc - half, tc + half):
                if abs(face - t_jamba) <= TOL_CM:
                    lado_esperado = (face == tc + half) if lado < 0 else (face == tc - half)
                    return ("FACE_DE_PERPENDICULAR", w["id"],
                            round(face - t_jamba, 3),
                            None if lado_esperado else "FACE_OPOSTA")
    return None


def main():
    ref = json.load(open(os.path.join(ROOT, "nuvem/benchmark/projects", PROJ,
                                      "reference.json"), encoding="utf-8"))
    inp = json.load(open(os.path.join(ROOT, "nuvem/benchmark/projects", PROJ,
                                      "input.json"), encoding="utf-8"))
    dossier = json.load(open(os.path.join(HERE, "case_dossier.json"),
                             encoding="utf-8"))[PROJ]["casos"]
    walls = {w["id"]: w for w in ref["walls"]}

    out, n_dupla = [], 0
    for c in dossier:
        host = walls[c["wall_id_reference"]]
        o, d = axis(host)
        lo, hi = c["consenso_cm"]
        a = confirma(o, d, lo, -1, inp["walls"])
        b = confirma(o, d, hi, +1, inp["walls"])
        if a and b:
            n_dupla += 1
        out.append({"wall_id_reference": host["id"], "consenso_cm": [lo, hi],
                    "jamba_lo_xy_cm": c["identidade_fisica"]["jamba_lo_xy_cm"],
                    "jamba_hi_xy_cm": c["identidade_fisica"]["jamba_hi_xy_cm"],
                    "confirmacao_jamba_lo": a, "confirmacao_jamba_hi": b})
        print("  %-6s cons=%-16s lo: %-46s hi: %s" % (
            host["id"], c["consenso_cm"],
            ("%s %s dif=%+.3f" % (a[0], a[1], a[2])) if a else "NAO CONFIRMADA",
            ("%s %s dif=%+.3f" % (b[0], b[1], b[2])) if b else "NAO CONFIRMADA"))
    print("\n>> casos com as DUAS jambas confirmadas por geometria medida: %d de 19"
          % n_dupla)
    p = os.path.join(HERE, "measured_jamb_confirmation.json")
    json.dump(out, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False,
              sort_keys=True)
    print("escrito:", p)


if __name__ == "__main__":
    main()
