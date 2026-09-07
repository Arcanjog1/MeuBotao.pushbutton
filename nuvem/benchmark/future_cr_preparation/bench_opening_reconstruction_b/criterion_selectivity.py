# -*- coding: utf-8 -*-
"""CR-B / §6+§8: um criterio ESTRUTURAL (sem limiar de largura) isola os 19?

Avalia, nos 94 (TGD) / 92 (TP1) trechos detectados, tres sinais
independentes de largura:

  C1  RESERVA DE NO NAS DUAS JAMBAS - cada jamba do consenso coincide
      (<=1cm) com a face INTERNA de uma parede perpendicular que cruza o
      eixo do host.
  C2  SEM VERGA - nenhuma fiada acima do vao tem peca sobre o consenso
      (inclui o caso "vao de altura plena", sem fiada acima).
  C3  SEM PROVENIENCIA MEDIDA - nenhuma abertura `measured` do Revit casa
      com o vao (so' avaliavel no TGD).

READ-ONLY.
"""
import json
import math
import os

ROOT = os.environ.get("REPO_ROOT", "/home/user/MeuBotao.pushbutton")
HERE = os.path.dirname(os.path.abspath(__file__))
FACE_TOL_CM = 1.0
COLLINEAR_OFFSET_CM = 3.0
PERP_REACH_CM = 60.0


def axis(w):
    sx, sy = w["start_cm"]
    ex, ey = w["end_cm"]
    n = math.hypot(ex - sx, ey - sy)
    return (sx, sy), ((ex - sx) / n, (ey - sy) / n)


def pr(o, d, p):
    dx, dy = p[0] - o[0], p[1] - o[1]
    return dx * d[0] + dy * d[1], -dx * d[1] + dy * d[0]


def ov(a, b):
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


def run(proj):
    ref = json.load(open(os.path.join(ROOT, "nuvem/benchmark/projects", proj,
                                      "reference.json"), encoding="utf-8"))
    inp = json.load(open(os.path.join(ROOT, "nuvem/benchmark/projects", proj,
                                      "input.json"), encoding="utf-8"))
    repro = json.load(open(os.path.join(
        ROOT, "nuvem/benchmark/future_cr_preparation",
        "bench_opening_reconstruction_a/repro_envelope.json"),
        encoding="utf-8"))[proj]
    walls = {w["id"]: w for w in ref["walls"]}

    rows = []
    for rec in repro["runs"]:
        host = walls[rec["wall"]]
        o, d = axis(host)
        cons = rec["consenso"]
        largura = cons[1] - cons[0]
        zs = {round(m[0], 3) for m in rec["membros"]}

        # C1 - reserva de no' nas duas jambas
        lo_ok = hi_ok = False
        for w in ref["walls"]:
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
            if abs((tc + half) - cons[0]) <= FACE_TOL_CM:
                lo_ok = True
            if abs((tc - half) - cons[1]) <= FACE_TOL_CM:
                hi_ok = True
        c1 = lo_ok and hi_ok

        # C2 - sem verga
        cob_acima = [
            sum(ov((b["t_start_cm"], b["t_end_cm"]), cons)
                for b in (row.get("blocks") or []))
            for row in (host.get("rows") or [])
            if round(row["elevation_cm"], 3) > max(zs)]
        c2 = not any(c / largura >= 0.5 for c in cob_acima)

        # C3 - sem proveniencia medida
        med = []
        for w in inp["walls"]:
            t0, s0 = pr(o, d, w["start_cm"])
            t1, s1 = pr(o, d, w["end_cm"])
            if abs(s0) > COLLINEAR_OFFSET_CM or abs(s1) > COLLINEAR_OFFSET_CM:
                continue
            o2, d2 = axis(w)
            dot = d2[0] * d[0] + d2[1] * d[1]
            for op in w.get("openings") or []:
                if op.get("confidence") != "measured":
                    continue
                a = t0 + op["t_start_cm"] * dot
                b = t0 + op["t_end_cm"] * dot
                seg = (min(a, b), max(a, b))
                if ov(seg, cons) > 0.5 * min(largura, seg[1] - seg[0]):
                    med.append(op.get("source_element_id"))
        c3 = not med

        rows.append({"wall": host["id"], "consenso": cons,
                     "largura_cm": round(largura, 2),
                     "assinatura_15cm": (rec["spread_inicio"] >= 14.9
                                         and rec["spread_fim"] >= 14.9),
                     "C1_reserva_de_no_nas_duas_jambas": c1,
                     "C2_sem_verga": c2,
                     "C3_sem_proveniencia_medida": c3,
                     "measured_ids": med})
    return rows


def main():
    out = {}
    for proj in ["torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"]:
        rows = run(proj)
        out[proj] = rows
        n19 = [r for r in rows if r["assinatura_15cm"]]
        rest = [r for r in rows if not r["assinatura_15cm"]]
        print("=" * 92)
        print("%s   trechos=%d   (19 da assinatura + %d demais)"
              % (proj, len(rows), len(rest)))
        for nome, key in [("C1 reserva de no' nas DUAS jambas",
                           "C1_reserva_de_no_nas_duas_jambas"),
                          ("C2 sem verga", "C2_sem_verga"),
                          ("C3 sem proveniencia medida",
                           "C3_sem_proveniencia_medida")]:
            print("  %-36s  nos 19: %2d/19   nos demais: %2d/%d"
                  % (nome, sum(r[key] for r in n19),
                     sum(r[key] for r in rest), len(rest)))
        comb = [r for r in rows if r["C1_reserva_de_no_nas_duas_jambas"]
                and r["C2_sem_verga"] and r["C3_sem_proveniencia_medida"]]
        print("  >> C1 AND C2 AND C3: %d trechos   (dos 19: %d; falsos positivos: %d)"
              % (len(comb), sum(1 for r in comb if r["assinatura_15cm"]),
                 sum(1 for r in comb if not r["assinatura_15cm"])))
        for r in comb:
            if not r["assinatura_15cm"]:
                print("     FALSO POSITIVO: %s %s larg=%s" % (r["wall"], r["consenso"], r["largura_cm"]))
        faltando = [r for r in n19 if not (r["C1_reserva_de_no_nas_duas_jambas"]
                                           and r["C2_sem_verga"] and r["C3_sem_proveniencia_medida"])]
        for r in faltando:
            print("     DOS 19 NAO CAPTURADO: %s %s C1=%s C2=%s C3=%s"
                  % (r["wall"], r["consenso"], r["C1_reserva_de_no_nas_duas_jambas"],
                     r["C2_sem_verga"], r["C3_sem_proveniencia_medida"]))
    p = os.path.join(HERE, "criterion_selectivity.json")
    json.dump(out, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False,
              sort_keys=True)
    print("escrito:", p)


if __name__ == "__main__":
    main()
