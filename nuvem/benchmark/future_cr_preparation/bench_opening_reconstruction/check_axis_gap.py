# -*- coding: utf-8 -*-
"""Confronta o vao ENVELOPE / CONSENSO com os TRECHOS DE PAREDE MEDIDOS
(input.json com `confidence=measured`) no mesmo eixo.

Pergunta respondida: no modelo real, aquele espaco e' um VAO DENTRO de uma
parede, ou o ESPACO ENTRE DUAS PAREDES separadas que a reconstrucao fundiu?
So' o TGD tem geometria medida; o TP1 e' inteiramente reconstruido.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "reconstruction_evidence.json")) as handle:
    evidence = json.load(handle)

for proj, data in evidence["projetos"].items():
    print("=" * 74)
    print(proj)
    hit = miss = nodata = 0
    for rec in data["aberturas"]:
        if not (abs(rec["spread_inicio_cm"] - 15.0) < 0.02
                and abs(rec["spread_fim_cm"] - 15.0) < 0.02):
            continue
        runs = rec["trechos_medidos_no_eixo"] or []
        cons = rec["consenso_t_cm"]
        env = rec["gravado_t_cm"]
        if not runs:
            nodata += 1
            print("   %-6s %-10s consenso=%s  SEM GEOMETRIA MEDIDA no eixo" %
                  (rec["wall"], rec["opening"], cons))
            continue
        # o consenso cai exatamente num buraco entre dois trechos medidos?
        gaps = []
        ordered = sorted(runs, key=lambda r: r["t_lo_cm"])
        for a, b in zip(ordered, ordered[1:]):
            if b["t_lo_cm"] - a["t_hi_cm"] > 1.0:
                gaps.append((a["t_hi_cm"], b["t_lo_cm"], a["input_wall"], b["input_wall"]))
        match = None
        for lo, hi, wa, wb in gaps:
            if abs(lo - cons[0]) <= 2.0 and abs(hi - cons[1]) <= 2.0:
                match = (lo, hi, wa, wb)
                break
        if match:
            hit += 1
            print("   %-6s %-10s gravado=%s consenso=%s  == BURACO MEDIDO [%.1f,%.1f] entre %s e %s"
                  % (rec["wall"], rec["opening"], env, cons, match[0], match[1], match[2], match[3]))
        else:
            miss += 1
            print("   %-6s %-10s gravado=%s consenso=%s  buracos medidos no eixo: %s"
                  % (rec["wall"], rec["opening"], env, cons,
                     [(g[0], g[1]) for g in gaps] or "nenhum (parede medida continua)"))
    print("   >> consenso == buraco entre paredes medidas: %d | divergente: %d | sem geometria medida: %d"
          % (hit, miss, nodata))
