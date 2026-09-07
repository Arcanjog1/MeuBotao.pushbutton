# -*- coding: utf-8 -*-
"""CR-B / RECONCILIACAO: TESTE DA VERGA.

Discriminante fisico entre ABERTURA REAL e DUAS PAREDES SEPARADAS:
uma abertura (porta/janela) tem parede ACIMA do vao (verga/lintel);
duas paredes separadas nao tem nada acima do espaco entre elas.

Para cada caso, percorre TODAS as fiadas do host (nao so' as do trecho
detectado) e mede quanto do intervalo de consenso esta' coberto por peca
do proprio host, fiada a fiada.

READ-ONLY. Fonte B (modulacao humana).
"""
import json
import os

ROOT = os.environ.get("REPO_ROOT", "/home/user/MeuBotao.pushbutton")
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS = ["torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"]


def overlap(a, b):
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


def build(proj):
    ref = json.load(open(os.path.join(
        ROOT, "nuvem/benchmark/projects", proj, "reference.json"),
        encoding="utf-8"))
    repro = json.load(open(os.path.join(
        ROOT, "nuvem/benchmark/future_cr_preparation",
        "bench_opening_reconstruction_a/repro_envelope.json"),
        encoding="utf-8"))[proj]
    walls = {w["id"]: w for w in ref["walls"]}

    out = []
    for rec in repro["runs"]:
        if not (rec["spread_inicio"] >= 14.9 and rec["spread_fim"] >= 14.9):
            continue
        host = walls[rec["wall"]]
        cons, env = rec["consenso"], rec["envelope"]
        largura = cons[1] - cons[0]
        zs_do_trecho = {round(m[0], 3) for m in rec["membros"]}

        perfil = []
        for row in sorted(host.get("rows") or [], key=lambda r: r["elevation_cm"]):
            z = round(row["elevation_cm"], 3)
            cob = sum(overlap((b["t_start_cm"], b["t_end_cm"]), cons)
                      for b in row.get("blocks") or [])
            cob_env = sum(overlap((b["t_start_cm"], b["t_end_cm"]), env)
                          for b in row.get("blocks") or [])
            perfil.append({
                "z_cm": z,
                "no_trecho_detectado": z in zs_do_trecho,
                "cobertura_do_consenso_cm": round(cob, 2),
                "cobertura_do_consenso_pct": round(100.0 * cob / largura, 1),
                "cobertura_do_envelope_cm": round(cob_env, 2),
            })

        acima = [p for p in perfil
                 if p["z_cm"] > max(zs_do_trecho) and not p["no_trecho_detectado"]]
        abaixo = [p for p in perfil
                  if p["z_cm"] < min(zs_do_trecho) and not p["no_trecho_detectado"]]
        verga = [p for p in acima if p["cobertura_do_consenso_pct"] >= 50.0]
        peitoril = [p for p in abaixo if p["cobertura_do_consenso_pct"] >= 50.0]

        out.append({
            "wall_id_reference": host["id"],
            "envelope_cm": env, "consenso_cm": cons,
            "wall_height_cm": host.get("height_cm"),
            "n_fiadas_totais_do_host": len(perfil),
            "n_fiadas_do_trecho": rec["n_courses"],
            "z_do_trecho": [min(zs_do_trecho), max(zs_do_trecho)],
            "n_fiadas_acima_do_trecho": len(acima),
            "n_fiadas_abaixo_do_trecho": len(abaixo),
            "VERGA__fiadas_acima_cobrindo_>=50pct": len(verga),
            "PEITORIL__fiadas_abaixo_cobrindo_>=50pct": len(peitoril),
            "cobertura_max_acima_pct": max([p["cobertura_do_consenso_pct"]
                                            for p in acima] or [0.0]),
            "cobertura_max_abaixo_pct": max([p["cobertura_do_consenso_pct"]
                                             for p in abaixo] or [0.0]),
            "perfil_por_fiada": perfil,
        })
    return out


def main():
    res = {}
    for p in PROJECTS:
        res[p] = build(p)
        print("=" * 100)
        print(p)
        print("  %-6s %-16s %-6s %-9s %-7s %-7s %-6s %-6s" % (
            "parede", "consenso", "h_cm", "fiadas", "acima", "abaixo",
            "VERGA", "PEIT"))
        for c in res[p]:
            print("  %-6s %-16s %-6s %2d/%-6d %-7d %-7d %-6d %-6d  (max acima %.0f%%, abaixo %.0f%%)" % (
                c["wall_id_reference"], c["consenso_cm"], c["wall_height_cm"],
                c["n_fiadas_do_trecho"], c["n_fiadas_totais_do_host"],
                c["n_fiadas_acima_do_trecho"], c["n_fiadas_abaixo_do_trecho"],
                c["VERGA__fiadas_acima_cobrindo_>=50pct"],
                c["PEITORIL__fiadas_abaixo_cobrindo_>=50pct"],
                c["cobertura_max_acima_pct"], c["cobertura_max_abaixo_pct"]))
    path = os.path.join(HERE, "lintel_test.json")
    json.dump(res, open(path, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False, sort_keys=True)
    print("escrito:", path)


if __name__ == "__main__":
    main()
