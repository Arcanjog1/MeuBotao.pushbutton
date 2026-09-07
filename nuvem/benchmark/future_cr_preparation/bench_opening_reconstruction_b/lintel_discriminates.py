# -*- coding: utf-8 -*-
"""CR-B: o TESTE DA VERGA discrimina? Roda em TODOS os trechos detectados
(94 TGD / 92 TP1) e estratifica por PROVENIENCIA MEDIDA do Revit.

Se as aberturas com `source_element_id` (janela/porta real do documento
INPUT do TGD) tiverem verga e as 19 nao tiverem, o teste e' discriminante.
Caso contrario, "0% acima" nao prova nada.

READ-ONLY.
"""
import collections
import json
import math
import os

ROOT = os.environ.get("REPO_ROOT", "/home/user/MeuBotao.pushbutton")
HERE = os.path.dirname(os.path.abspath(__file__))
COLLINEAR_OFFSET_CM = 3.0


def axis(w):
    sx, sy = w["start_cm"]
    ex, ey = w["end_cm"]
    n = math.hypot(ex - sx, ey - sy)
    return (sx, sy), ((ex - sx) / n, (ey - sy) / n)


def proj(o, d, p):
    dx, dy = p[0] - o[0], p[1] - o[1]
    return dx * d[0] + dy * d[1], -dx * d[1] + dy * d[0]


def overlap(a, b):
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


def measured_on_axis(host, inp_walls):
    o, d = axis(host)
    out = []
    for w in inp_walls:
        t0, s0 = proj(o, d, w["start_cm"])
        t1, s1 = proj(o, d, w["end_cm"])
        if abs(s0) > COLLINEAR_OFFSET_CM or abs(s1) > COLLINEAR_OFFSET_CM:
            continue
        o2, d2 = axis(w)
        dot = d2[0] * d[0] + d2[1] * d[1]      # +1 ou -1 (colinear)
        for op in w.get("openings") or []:
            if op.get("confidence") != "measured":
                continue
            a = t0 + op["t_start_cm"] * dot     # t0 = projecao do start_cm de w
            b = t0 + op["t_end_cm"] * dot
            out.append((min(a, b), max(a, b), op))
    return out


def run(proj_name):
    ref = json.load(open(os.path.join(ROOT, "nuvem/benchmark/projects",
                                      proj_name, "reference.json"), encoding="utf-8"))
    inp = json.load(open(os.path.join(ROOT, "nuvem/benchmark/projects",
                                      proj_name, "input.json"), encoding="utf-8"))
    repro = json.load(open(os.path.join(
        ROOT, "nuvem/benchmark/future_cr_preparation",
        "bench_opening_reconstruction_a/repro_envelope.json"),
        encoding="utf-8"))[proj_name]
    walls = {w["id"]: w for w in ref["walls"]}

    rows = []
    for rec in repro["runs"]:
        host = walls[rec["wall"]]
        cons = rec["consenso"]
        largura = cons[1] - cons[0]
        zs = {round(m[0], 3) for m in rec["membros"]}
        acima = []
        for row in host.get("rows") or []:
            z = round(row["elevation_cm"], 3)
            if z <= max(zs):
                continue
            cob = sum(overlap((b["t_start_cm"], b["t_end_cm"]), cons)
                      for b in row.get("blocks") or [])
            acima.append(100.0 * cob / largura)
        med = [m for m in measured_on_axis(host, inp["walls"])
               if overlap((m[0], m[1]), cons) > 0.5 * min(largura, m[1] - m[0])]
        assinatura = rec["spread_inicio"] >= 14.9 and rec["spread_fim"] >= 14.9
        rows.append({
            "wall": host["id"], "consenso": cons,
            "largura_cm": round(largura, 2),
            "assinatura_15cm": assinatura,
            "n_fiadas_acima": len(acima),
            "cobertura_max_acima_pct": round(max(acima or [0.0]), 1),
            "tem_verga": bool(acima) and max(acima) >= 50.0,
            "abertura_measured_casada": [
                {"kind": m[2].get("kind"), "width_cm": m[2].get("width_cm"),
                 "sill_cm": m[2].get("sill_cm"), "head_cm": m[2].get("head_cm"),
                 "source_element_id": m[2].get("source_element_id")} for m in med],
        })
    return rows


def main():
    res = {}
    for p in ["torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"]:
        rows = run(p)
        res[p] = rows
        print("=" * 92)
        print(p, "  trechos:", len(rows))
        grupos = collections.OrderedDict([
            ("A) COM abertura MEASURED casada",
             [r for r in rows if r["abertura_measured_casada"]]),
            ("B) os 19 da assinatura ~15cm",
             [r for r in rows if r["assinatura_15cm"]]),
            ("C) demais (sem measured, sem assinatura)",
             [r for r in rows if not r["abertura_measured_casada"]
              and not r["assinatura_15cm"]]),
        ])
        for nome, g in grupos.items():
            if not g:
                print("  %-42s n=0" % nome)
                continue
            com = [r for r in g if r["tem_verga"]]
            sem_fiada = [r for r in g if r["n_fiadas_acima"] == 0]
            print("  %-42s n=%-3d  COM verga=%-3d  SEM fiada acima=%-3d  "
                  "cob.max acima: mediana=%.0f%% max=%.0f%%"
                  % (nome, len(g), len(com), len(sem_fiada),
                     sorted(r["cobertura_max_acima_pct"] for r in g)[len(g) // 2],
                     max(r["cobertura_max_acima_pct"] for r in g)))
    path = os.path.join(HERE, "lintel_discriminates.json")
    json.dump(res, open(path, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False, sort_keys=True)
    print("escrito:", path)


if __name__ == "__main__":
    main()
