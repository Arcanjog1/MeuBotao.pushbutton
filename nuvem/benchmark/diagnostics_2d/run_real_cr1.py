# -*- coding: utf-8 -*-
"""ETAPA 2E - mede o CODIGO REAL (nuvem/core/engine/wall_pairing.py via
wall_modeling_bridge.run_wall_modeling, exatamente como a producao chama)
sobre torre_easy_lo_r00_tgd, e compara com o gabarito (reference.json).

Diferenca para os scripts de diagnostics_2d/run_sim*.py da Etapa 2D: aqueles
reimplementavam a varredura de candidatos numa biblioteca de simulacao
(simlib.py) para testar politicas de ranking OFFLINE, sem tocar o core. Este
script roda o PIPELINE REAL (find_wall_pairs de verdade, ja com a correcao do
CR-1 aplicada quando executado depois do Passo 2), para provar que o codigo
implementado reproduz (ou explica a diferenca de) os numeros previstos pela
simulacao. SOMENTE LEITURA do repo - nao cria nenhum arquivo dentro de
nuvem/core/**.

Uso:
    py -3 nuvem/benchmark/diagnostics_2d/run_real_cr1.py
"""
import json
import math
import os
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "nuvem")
sys.path.insert(0, "tests")

from benchmark import solver_bridge, wall_modeling_bridge as wmb  # noqa: E402
import simlib as L  # noqa: E402 - reaproveita ang/adiff/Ax/coverage/metrics helpers

BASE = "nuvem/benchmark/projects/torre_easy_lo_r00_tgd"


def cm(mod, ft_value):
    return ft_value / mod.FEET_PER_METER * 100.0


def main():
    input_real = json.load(open(os.path.join(BASE, "input_real.json"), encoding="utf-8"))
    reference = json.load(open(os.path.join(BASE, "reference.json"), encoding="utf-8"))

    mod = solver_bridge.engine()

    setup = input_real["setup_frozen"]
    layer = setup["layer"]
    segments_in_layer = [s for s in input_real["segments"] if s.get("layer") == layer]

    t0 = time.time()
    result = wmb.run_wall_modeling(input_real)
    elapsed = time.time() - t0

    diag = result["diagnostics"]
    final_walls = result["walls_to_create"]

    XY = [L.wall_xy(w) for w in final_walls]
    lens = [math.hypot(x1 - x0, y1 - y0) for x0, y0, x1, y1 in XY]

    # ---- cobertura do gabarito -------------------------------------------
    covs = []
    for w in reference["walls"]:
        A = L.Ax(w["start_cm"][0], w["start_cm"][1], w["end_cm"][0], w["end_cm"][1])
        covs.append(L.coverage(A, XY))
    cobertas = sum(1 for c in covs if c >= 0.85)
    ausentes = sum(1 for c in covs if c <= 0.0)

    # ---- erro de eixo -------------------------------------------------
    R = [L.Ax(w["start_cm"][0], w["start_cm"][1], w["end_cm"][0], w["end_cm"][1]) for w in reference["walls"]]
    eb = Counter()
    espurias = 0
    for x0, y0, x1, y1 in XY:
        A = L.Ax(x0, y0, x1, y1)
        mid = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
        best = None
        for B in R:
            if L.adiff(A.a, B.a) > 3.0:
                continue
            t = B.proj(*mid)
            if t < -20 or t > B.L + 20:
                continue
            e = abs(B.perp(*mid))
            if best is None or e < best:
                best = e
        if best is None:
            espurias += 1
            continue
        k = ("<=0,5" if best <= 0.5 else "0,5-2" if best <= 2 else "2-6" if best <= 6
             else "6-10" if best <= 10 else "10-16" if best <= 16 else ">16")
        eb[k] += 1

    # NOTA: "espessura exata entre os pares aceitos" (err = |dist medido -
    # matched_thickness| <= 0,05cm) NAO pode ser medida aqui: o retorno de
    # find_wall_pairs (via este bridge) so' guarda a espessura FINAL
    # gravada (sempre o valor exato do alvo - ver docstring de
    # find_wall_pairs), nao a distancia bruta medida entre as duas linhas
    # do CAD que formaram o par. Medir "exato"/"err"/"steals" exige o dado
    # por-candidato, exposto so' por diagnostics_2d/simlib.py
    # (build_candidates), que usa as MESMAS funcoes geometricas do motor
    # real (_line_geom_cache/_are_parallel_cached/etc., importadas ao
    # vivo) - nao uma reimplementacao. Ver run_real_cr1_result.json /
    # relatorio da Etapa 2E para os numeros cruzados dessa forma.

    unass = diag["openings"].get("unassigned_openings") or []
    total_ops = len(input_real.get("openings") or [])
    ops_assigned = total_ops - len(unass)

    pairing = diag["wall_pairing"]

    print("=" * 78)
    print("CR-1 - MEDICAO SOBRE O CODIGO REAL (wall_modeling_bridge.run_wall_modeling)")
    print("=" * 78)
    print("segments (layer '%s')      : %d" % (layer, len(segments_in_layer)))
    print("lines apos merge            : %d" % diag["lines_after_merge"])
    print("parallel_pairs avaliados    : %d" % pairing["parallel_pairs"])
    print("accepted pairs (paredes)    : %d  (antes do dedup)" % (
        diag["walls_created"] + diag["duplicates_removed_count"]))
    print("dedup removidas             : %d" % diag["duplicates_removed_count"])
    print("final walls                 : %d" % diag["walls_created"])
    print("cobertura gabarito (>=0,85) : %d de %d" % (cobertas, len(reference["walls"])))
    print("ausentes (cobertura 0)      : %d" % ausentes)
    print("eixo correto (<=0,5cm)      : %d de %d" % (eb["<=0,5"], len(final_walls)))
    print("eixo 10-16cm fora           : %d" % eb["10-16"])
    print("espurias (sem eixo gabarito): %d" % espurias)
    print("walls <50cm                 : %d" % sum(1 for l in lens if l < 50.0))
    print("walls <20cm                 : %d" % sum(1 for l in lens if l < 20.0))
    print("openings atribuidas         : %d de %d" % (ops_assigned, total_ops))
    print("comprimento total (cm)      : %.0f" % sum(lens))
    print("runtime (s)                 : %.2f" % elapsed)
    print("=" * 78)

    out = dict(
        lines_in_layer=len(segments_in_layer),
        lines_after_merge=diag["lines_after_merge"],
        parallel_pairs=pairing["parallel_pairs"],
        accepted_pairs=diag["walls_created"] + diag["duplicates_removed_count"],
        dedup_removed=diag["duplicates_removed_count"],
        final_walls=diag["walls_created"],
        cobertas=cobertas,
        ausentes=ausentes,
        eixo_ok=eb["<=0,5"],
        eixo_10_16=eb["10-16"],
        espurias=espurias,
        walls_lt50=sum(1 for l in lens if l < 50.0),
        walls_lt20=sum(1 for l in lens if l < 20.0),
        openings_assigned=ops_assigned,
        openings_total=total_ops,
        total_len_cm=sum(lens),
        runtime_s=elapsed,
    )
    out_dir = os.environ.get("D2OUT", os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(out_dir, "run_real_cr1_result.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    return out


if __name__ == "__main__":
    main()
