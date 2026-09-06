# -*- coding: utf-8 -*-
"""POST-PR19 ATLAS REVALIDATION - script diagnostico adicional (NAO do
Atlas original): varre uma pequena matriz de valores de
PIER_LAYOUT_TOLERANCE_CM / MODULATION_WHOLE_CM_TOLERANCE_CM (0.05..0.30cm)
para achar a faixa onde o ruido desaparece sem regressao fisica excessiva.
Mesma tecnica do run_ablation.py: monkeypatch em memoria, nenhuma
alteracao de producao. Escreve ablation_sweep.json em ATLAS_OUT_DIR.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas_lib as al  # noqa: E402
from run_ablation import run_with, patch_fit_tol  # noqa: E402

VALUES = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30)


def main():
    summary = al.read_json(al.out_path("state_current_summary.json"))
    out = {}
    for pid in ("torre_easy_lo_r00_tp1", "torre_easy_lo_r00_tgd"):
        short = al.SHORT[pid]
        base = summary["projects"][short]["counts_by_code"]
        base_pieces = summary["projects"][short]["physical_pieces"]
        out[short] = {}
        for value in VALUES:
            if value == 0.05:
                # baseline (valor de producao) - nao precisa monkeypatch
                counts = base
                n = base_pieces
                seconds = summary["projects"][short]["solver_seconds"]
            else:
                counts, run = run_with(pid, lambda e, s, m, v=value: patch_fit_tol(e, s, m, value=v))
                _fp, n = al.physical_fingerprint(run)
                seconds = round(run["solver_seconds"], 1)
            delta = {}
            for code in sorted(set(base) | set(counts)):
                b, c = base.get(code, 0), counts.get(code, 0)
                if b != c:
                    delta[code] = [b, c, c - b]
            out[short][str(value)] = {
                "counts": counts, "pieces": n, "pieces_delta": n - base_pieces,
                "delta_vs_baseline": delta, "solver_seconds": seconds,
            }
            print("=====", short, "tol", value, "pieces", n, "(+%d)" % (n - base_pieces),
                  "seconds", seconds)
            for code, (b, c, d) in sorted(delta.items()):
                print("   %-34s %6d -> %6d  (%+d)" % (code, b, c, d))
    al.write_json(al.out_path("ablation_sweep.json"), out)


if __name__ == "__main__":
    main()
