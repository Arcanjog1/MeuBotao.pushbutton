# -*- coding: utf-8 -*-
"""CR-B / RECONCILIACAO: o que ocupa FISICAMENTE o vao?

Para cada um dos 19 casos, projeta TODOS os blocos humanos do projeto (de
qualquer parede) no eixo do host e reporta os que caem dentro do envelope.
Responde a pergunta de dominio: o espaco esta' VAZIO (porta / duas paredes)
ou esta' OCUPADO por peca de amarracao de uma parede perpendicular
(reserva de no')?

READ-ONLY. Fonte B (modulacao humana) + fonte C (reconstrucao).
"""
import json
import math
import os

ROOT = os.environ.get("REPO_ROOT", "/home/user/MeuBotao.pushbutton")
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS = ["torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"]

HALF_BAND_CM = 9.0     # meia espessura 7,0 + folga de analise 2,0
PERP_REACH_CM = 60.0   # ate' onde procurar eixo perpendicular cruzando


def axis(w):
    sx, sy = w["start_cm"]
    ex, ey = w["end_cm"]
    n = math.hypot(ex - sx, ey - sy)
    return (sx, sy), ((ex - sx) / n, (ey - sy) / n)


def proj(o, d, p):
    dx, dy = p[0] - o[0], p[1] - o[1]
    return dx * d[0] + dy * d[1], -dx * d[1] + dy * d[0]


def build(proj_name):
    ref = json.load(open(os.path.join(
        ROOT, "nuvem/benchmark/projects", proj_name, "reference.json"),
        encoding="utf-8"))
    repro = json.load(open(os.path.join(
        ROOT, "nuvem/benchmark/future_cr_preparation",
        "bench_opening_reconstruction_a/repro_envelope.json"),
        encoding="utf-8"))[proj_name]
    walls = {w["id"]: w for w in ref["walls"]}

    all_blocks = []
    for w in ref["walls"]:
        for row in w.get("rows") or []:
            for b in row.get("blocks") or []:
                all_blocks.append((w["id"], row.get("elevation_cm"), b))

    out = []
    for rec in repro["runs"]:
        if not (rec["spread_inicio"] >= 14.9 and rec["spread_fim"] >= 14.9):
            continue
        host = walls[rec["wall"]]
        o, d = axis(host)
        env, cons = rec["envelope"], rec["consenso"]

        # 1) blocos de QUALQUER parede dentro da faixa do host, no envelope
        inside = []
        for wid, z, b in all_blocks:
            t, s = proj(o, d, b["center_cm"])
            if abs(s) > HALF_BAND_CM:
                continue
            if not (env[0] - 1.0 <= t <= env[1] + 1.0):
                continue
            inside.append({
                "wall_do_bloco": wid, "z_cm": z, "peca": b["type_name"],
                "t_centro_cm": round(t, 2), "offset_perp_cm": round(s, 2),
                "rotation_deg": b.get("rotation_deg"), "role": b.get("role"),
                "t_start_cm": b.get("t_start_cm"), "t_end_cm": b.get("t_end_cm"),
                "secondary_wall_id": b.get("secondary_wall_id"),
            })
        no_consenso = [b for b in inside
                       if cons[0] + 0.5 < b["t_centro_cm"] < cons[1] - 0.5]
        nas_tiras = [b for b in inside if b not in no_consenso]

        # 2) eixos PERPENDICULARES da reconstrucao que cruzam o host no envelope
        perp = []
        for w in ref["walls"]:
            if w["id"] == host["id"]:
                continue
            o2, d2 = axis(w)
            dot = abs(d2[0] * d[0] + d2[1] * d[1])
            if dot > 0.05:                      # nao e' perpendicular
                continue
            t0, s0 = proj(o, d, w["start_cm"])
            t1, s1 = proj(o, d, w["end_cm"])
            lo_s, hi_s = min(s0, s1), max(s0, s1)
            if not (lo_s - PERP_REACH_CM <= 0 <= hi_s + PERP_REACH_CM):
                continue
            tc = (t0 + t1) / 2.0
            if not (env[0] - 25.0 <= tc <= env[1] + 25.0):
                continue
            perp.append({
                "wall": w["id"], "t_do_cruzamento_cm": round(tc, 2),
                "espessura_cm": w.get("thickness_cm"),
                "faixa_ocupada_cm": [round(tc - w.get("thickness_cm", 14) / 2.0, 2),
                                     round(tc + w.get("thickness_cm", 14) / 2.0, 2)],
                "distancia_perp_do_host_cm": [round(lo_s, 2), round(hi_s, 2)],
                "comprimento_cm": w.get("length_cm"),
            })
        perp.sort(key=lambda p: p["t_do_cruzamento_cm"])

        out.append({
            "wall_id_reference": host["id"],
            "envelope_cm": env, "consenso_cm": cons,
            "jamba_lo_xy_cm": [round(o[0] + d[0] * cons[0], 3),
                               round(o[1] + d[1] * cons[0], 3)],
            "jamba_hi_xy_cm": [round(o[0] + d[0] * cons[1], 3),
                               round(o[1] + d[1] * cons[1], 3)],
            "n_blocos_no_consenso": len(no_consenso),
            "n_blocos_nas_tiras_de_15cm": len(nas_tiras),
            "blocos_no_consenso": no_consenso[:40],
            "blocos_nas_tiras_de_15cm": nas_tiras[:40],
            "eixos_perpendiculares_cruzando": perp,
        })
    out.sort(key=lambda c: (c["jamba_lo_xy_cm"], c["jamba_hi_xy_cm"]))
    return out


def main():
    res = {p: build(p) for p in PROJECTS}
    path = os.path.join(HERE, "void_occupancy.json")
    json.dump(res, open(path, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False, sort_keys=True)
    for p, cs in res.items():
        print("=" * 96)
        print(p)
        for c in cs:
            perp = ["%s@%.1f%s" % (x["wall"], x["t_do_cruzamento_cm"],
                                   x["faixa_ocupada_cm"]) for x in
                    c["eixos_perpendiculares_cruzando"]]
            print("  %-6s cons=%-16s env=%-16s | blocos: consenso=%d tiras=%d | perp: %s"
                  % (c["wall_id_reference"], c["consenso_cm"], c["envelope_cm"],
                     c["n_blocos_no_consenso"], c["n_blocos_nas_tiras_de_15cm"],
                     ", ".join(perp) or "nenhum"))
    print("escrito:", path)


if __name__ == "__main__":
    main()
