# -*- coding: utf-8 -*-
"""CR-B / RECONCILIACAO: ficha por caso dos 19 vaos com assinatura ~15cm.

READ-ONLY. Nao escreve em `nuvem/benchmark/projects/**`. Nao chama o solver.
Separa explicitamente as quatro fontes de verdade:
  A) GEOMETRIA MEDIDA DO REVIT  -> input.json (so' quando `confidence=measured`
     / `source_element_id` existir; no TP1 o input e' RECONSTRUIDO)
  B) MODULACAO HUMANA           -> reference.json rows/blocks
  C) RECONSTRUCAO DO BENCHMARK  -> reference.json walls/openings/junctions
  D) RESULTADO DO SOLVER        -> NAO usado aqui
"""
import collections
import json
import math
import os
import sys

ROOT = os.environ.get("REPO_ROOT", "/home/user/MeuBotao.pushbutton")
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS = ["torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"]

# tolerancias de ANALISE (nao sao tolerancias de dominio; nao entram em
# nenhum arquivo de producao)
COLLINEAR_OFFSET_CM = 3.0    # desvio perpendicular para "mesmo eixo"
NEAR_CM = 2.0                # proximidade para casar borda com face


def load(proj, name):
    with open(os.path.join(ROOT, "nuvem/benchmark/projects", proj, name),
              encoding="utf-8") as fh:
        return json.load(fh)


def axis(wall):
    sx, sy = wall["start_cm"]
    ex, ey = wall["end_cm"]
    n = math.hypot(ex - sx, ey - sy)
    return (sx, sy), ((ex - sx) / n, (ey - sy) / n)


def project(origin, direction, pt):
    dx, dy = pt[0] - origin[0], pt[1] - origin[1]
    return (dx * direction[0] + dy * direction[1],
            -dx * direction[1] + dy * direction[0])


def world(origin, direction, t):
    return (round(origin[0] + direction[0] * t, 3),
            round(origin[1] + direction[1] * t, 3))


def collinear_runs(host, walls):
    """Trechos de parede de `walls` que caem sobre o EIXO de `host`."""
    origin, direction = axis(host)
    runs = []
    for w in walls:
        t0, s0 = project(origin, direction, w["start_cm"])
        t1, s1 = project(origin, direction, w["end_cm"])
        if abs(s0) > COLLINEAR_OFFSET_CM or abs(s1) > COLLINEAR_OFFSET_CM:
            continue
        runs.append({"id": w["id"], "lo": round(min(t0, t1), 3),
                     "hi": round(max(t0, t1), 3),
                     "thickness_cm": w.get("thickness_cm"),
                     "src": list(w.get("source_element_ids") or [])})
    runs.sort(key=lambda r: r["lo"])
    return runs


def measured_openings_on_axis(host, walls):
    """Aberturas com PROVENIENCIA do Revit projetadas no eixo do host."""
    origin, direction = axis(host)
    out = []
    for w in walls:
        t0, s0 = project(origin, direction, w["start_cm"])
        t1, s1 = project(origin, direction, w["end_cm"])
        if abs(s0) > COLLINEAR_OFFSET_CM or abs(s1) > COLLINEAR_OFFSET_CM:
            continue
        w_origin, w_dir = axis(w)
        flip = (w_dir[0] * direction[0] + w_dir[1] * direction[1]) < 0
        base = min(t0, t1) if not flip else max(t0, t1)
        for op in w.get("openings") or []:
            a = base + (op["t_start_cm"] if not flip else -op["t_end_cm"])
            b = base + (op["t_end_cm"] if not flip else -op["t_start_cm"])
            out.append({
                "host_wall_input": w["id"],
                "t_range_no_eixo_do_host": [round(a, 2), round(b, 2)],
                "kind": op.get("kind"), "width_cm": op.get("width_cm"),
                "sill_cm": op.get("sill_cm"), "head_cm": op.get("head_cm"),
                "source_element_id": op.get("source_element_id"),
                "confidence": op.get("confidence"),
            })
    out.sort(key=lambda o: o["t_range_no_eixo_do_host"][0])
    return out


def jamb_blocks(host, lo, hi):
    """Pecas humanas que encostam em cada jamba, fiada a fiada (fonte B)."""
    left, right = [], []
    for row in host.get("rows") or []:
        z = row.get("elevation_cm")
        for b in row.get("blocks") or []:
            if abs(b["t_end_cm"] - lo) <= NEAR_CM:
                left.append((z, b["type_name"], b["t_start_cm"], b["t_end_cm"],
                             b.get("role"), b.get("secondary_wall_id")))
            if abs(b["t_start_cm"] - hi) <= NEAR_CM:
                right.append((z, b["type_name"], b["t_start_cm"], b["t_end_cm"],
                              b.get("role"), b.get("secondary_wall_id")))
    return sorted(left), sorted(right)


def summarize_blocks(items):
    c = collections.Counter((i[1], round(i[2], 2), round(i[3], 2)) for i in items)
    return [{"peca": k[0], "t_start_cm": k[1], "t_end_cm": k[2], "n_fiadas": v}
            for k, v in sorted(c.items(), key=lambda kv: -kv[1])]


def build(proj):
    ref = load(proj, "reference.json")
    inp = load(proj, "input.json")
    ref_walls = {w["id"]: w for w in ref["walls"]}
    repro = json.load(open(os.path.join(
        ROOT, "nuvem/benchmark/future_cr_preparation",
        "bench_opening_reconstruction_a/repro_envelope.json"),
        encoding="utf-8"))[proj]

    inp_measured = sum(
        1 for w in inp["walls"] for o in (w.get("openings") or [])
        if o.get("confidence") == "measured")

    cases = []
    for rec in repro["runs"]:
        if not (rec["spread_inicio"] >= 14.9 and rec["spread_fim"] >= 14.9):
            continue
        host = ref_walls[rec["wall"]]
        origin, direction = axis(host)
        cons, env = rec["consenso"], rec["envelope"]

        # (C) juncoes da reconstrucao dentro/na borda do envelope
        js = []
        for j in host.get("junctions") or []:
            t = j.get("t_cm")
            if t is None or not (env[0] - 20.0 <= t <= env[1] + 20.0):
                continue
            js.append({"type": j.get("type"), "t_cm": round(t, 3),
                       "point_cm": j.get("point_cm"),
                       "neighbors": j.get("neighbors"),
                       "at_end": j.get("at_end")})

        # (A) geometria medida no MESMO eixo
        runs = collinear_runs(host, inp["walls"])
        gaps = [{"lo": a["hi"], "hi": b["lo"], "antes": a["id"], "depois": b["id"],
                 "largura_cm": round(b["lo"] - a["hi"], 3),
                 "src_antes": a["src"], "src_depois": b["src"]}
                for a, b in zip(runs, runs[1:]) if b["lo"] - a["hi"] > 1.0]
        gap_match = next((g for g in gaps
                          if abs(g["lo"] - cons[0]) <= NEAR_CM
                          and abs(g["hi"] - cons[1]) <= NEAR_CM), None)
        env_match = next((g for g in gaps
                          if abs(g["lo"] - env[0]) <= NEAR_CM
                          and abs(g["hi"] - env[1]) <= NEAR_CM), None)

        ops = measured_openings_on_axis(host, inp["walls"])
        ops_here = [o for o in ops
                    if o["t_range_no_eixo_do_host"][1] > env[0] - 20.0
                    and o["t_range_no_eixo_do_host"][0] < env[1] + 20.0]

        left, right = jamb_blocks(host, cons[0], cons[1])
        env_left, env_right = jamb_blocks(host, env[0], env[1])

        ref_op = next((o for o in (host.get("openings") or [])
                       if abs(o["t_start_cm"] - env[0]) <= 0.5
                       and abs(o["t_end_cm"] - env[1]) <= 0.5), None)

        cases.append({
            # identidade FISICA estavel (nao depende do id W0xx)
            "identidade_fisica": {
                "eixo_inicio_cm": [round(origin[0], 3), round(origin[1], 3)],
                "direcao": [round(direction[0], 6), round(direction[1], 6)],
                "angulo_deg": host.get("angle_deg"),
                "jamba_lo_xy_cm": world(origin, direction, cons[0]),
                "jamba_hi_xy_cm": world(origin, direction, cons[1]),
                "envelope_lo_xy_cm": world(origin, direction, env[0]),
                "envelope_hi_xy_cm": world(origin, direction, env[1]),
            },
            "wall_id_reference": host["id"],
            "wall_key_reference": host["key"],
            "wall_source_element_ids": list(host.get("source_element_ids") or []),
            "wall_length_cm": host.get("length_cm"),
            "wall_thickness_cm": host.get("thickness_cm"),
            "n_fiadas_do_trecho": rec["n_courses"],
            "envelope_cm": env,
            "consenso_cm": cons,
            "largura_envelope_cm": rec["largura_envelope"],
            "largura_consenso_cm": rec["largura_consenso"],
            "spread_inicio_cm": rec["spread_inicio"],
            "spread_fim_cm": rec["spread_fim"],
            "abertura_gravada_no_gabarito": ref_op,
            "juncoes_no_intervalo": js,
            "eixo_medido__trechos": runs,
            "eixo_medido__buracos": gaps,
            "eixo_medido__buraco_bate_consenso": gap_match,
            "eixo_medido__buraco_bate_envelope": env_match,
            "aberturas_com_proveniencia_no_eixo": ops_here,
            "pecas_humanas_jamba_lo": summarize_blocks(left),
            "pecas_humanas_jamba_hi": summarize_blocks(right),
            "pecas_humanas_jamba_lo_envelope": summarize_blocks(env_left),
            "pecas_humanas_jamba_hi_envelope": summarize_blocks(env_right),
        })

    cases.sort(key=lambda c: (c["identidade_fisica"]["jamba_lo_xy_cm"],
                              c["identidade_fisica"]["jamba_hi_xy_cm"]))
    return {
        "projeto": proj,
        "input_e_medido": inp_measured > 0,
        "n_aberturas_measured_no_input": inp_measured,
        "n_walls_reference": len(ref["walls"]),
        "n_walls_input": len(inp["walls"]),
        "n_casos": len(cases),
        "casos": cases,
    }


def main():
    out = {p: build(p) for p in PROJECTS}
    path = os.path.join(HERE, "case_dossier.json")
    json.dump(out, open(path, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False, sort_keys=True)
    for p, d in out.items():
        print("%-24s casos=%d  input_medido=%s (%d aberturas measured)  "
              "walls ref=%d input=%d" % (
                  p, d["n_casos"], d["input_e_medido"],
                  d["n_aberturas_measured_no_input"],
                  d["n_walls_reference"], d["n_walls_input"]))
    print("escrito:", path)


if __name__ == "__main__":
    main()
