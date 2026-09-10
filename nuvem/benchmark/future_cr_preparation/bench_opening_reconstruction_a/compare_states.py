# -*- coding: utf-8 -*-
"""STATE_A x STATE_B da CR-BENCH-OPENING-RECONSTRUCTION-A.

Compara por IDENTIDADE GEOMETRICA ESTAVEL, nunca por contagem:

  * detector -> (wall, z_range, n_courses, ENVELOPE). O envelope e' o que
    NAO muda com a correcao (continua sendo a referencia de identidade do
    trecho), entao serve de chave entre as duas versoes; `x_range` e' o que
    muda e por isso nao pode entrar na chave.
  * solver   -> (code, wall, detail) de cada achado. `block_id` e'
    sequencial e renumera quando entra peca na fiada: nao e' identidade.

Uso:
    python3 state_detector.py STATE_A detector_state_a.json   # motor sem a correcao
    python3 state_detector.py STATE_B detector_state_b.json   # motor com a correcao
    python3 compare_states.py detector_state_a.json detector_state_b.json
    python3 compare_states.py --solver solver_state_a.json solver_state_b.json
"""
import collections
import json
import sys


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)["projects"]


def compare_detector(path_a, path_b):
    A, B = load(path_a), load(path_b)
    report = {}
    for proj in sorted(set(A) & set(B)):
        a, b = A[proj], B[proj]
        ka = {(o["wall"], tuple(o["z_range"]), o["n_courses"],
               tuple(o["x_range"])): o for o in a["openings"]}
        kb = {(o["wall"], tuple(o["z_range"]), o["n_courses"],
               tuple(o["x_range_envelope"])): o for o in b["openings"]}
        comuns = set(ka) & set(kb)
        mudou = [(k, ka[k], kb[k]) for k in comuns
                 if ka[k]["x_range"] != kb[k]["x_range"]]
        deslocamento = []
        for _k, oa, ob in mudou:
            d = ((ob["x_range"][0] + ob["x_range"][1])
                 - (oa["x_range"][0] + oa["x_range"][1])) / 2.0
            if abs(d) > 1e-9:
                deslocamento.append(round(d, 6))
        report[proj] = {
            "aberturas_A": len(a["openings"]),
            "aberturas_B": len(b["openings"]),
            "so_em_A": len(set(ka) - set(kb)),
            "so_em_B": len(set(kb) - set(ka)),
            "geometria_alterada": len(mudou),
            "ALARGADAS": sum(1 for _k, oa, ob in mudou
                             if ob["width_cm"] > oa["width_cm"] + 1e-9),
            "estreitadas": sum(1 for _k, oa, ob in mudou
                               if ob["width_cm"] < oa["width_cm"] - 1e-9),
            "contida_no_envelope_antigo": all(
                oa["x_range"][0] - 1e-9 <= ob["x_range"][0]
                <= ob["x_range"][1] <= oa["x_range"][1] + 1e-9
                for _k, oa, ob in mudou),
            "reducao_de_largura_cm": {str(k): v for k, v in sorted(
                collections.Counter(round(oa["width_cm"] - ob["width_cm"], 2)
                                    for _k, oa, ob in mudou).items())},
            "centro_deslocado_n": len(deslocamento),
            "centro_deslocado_max_cm": max([abs(d) for d in deslocamento] or [0.0]),
            "proveniencia_B": dict(collections.Counter(
                o["opening_provenance"] for o in b["openings"])),
            "jamb_spread_cm_B": {str(k): v for k, v in sorted(
                collections.Counter(round(o["jamb_spread_cm"], 2)
                                    for o in b["openings"]).items())},
            "larguras_A": a["widths"],
            "larguras_B": b["widths"],
        }
    return report


def compare_solver(path_a, path_b):
    A, B = load(path_a), load(path_b)
    report = {}
    for proj in sorted(set(A) & set(B)):
        a, b = A[proj], B[proj]
        sa, sb = set(a["findings_identity"]), set(b["findings_identity"])
        report[proj] = {
            "fingerprint_A": a["fingerprint"], "fingerprint_B": b["fingerprint"],
            "fingerprint_igual": a["fingerprint"] == b["fingerprint"],
            "pecas_A": a["pecas"], "pecas_B": b["pecas"],
            "score_igual": a["score"] == b["score"],
            "criticos_A": a["score"].get("critical_errors"),
            "criticos_B": b["score"].get("critical_errors"),
            "achados_so_em_A": len(sa - sb), "achados_so_em_B": len(sb - sa),
            "aberturas_do_input_iguais": a["openings_input"] == b["openings_input"],
            "counts_A": a["counts"], "counts_B": b["counts"],
        }
    return report


def main():
    argv = sys.argv[1:]
    solver = "--solver" in argv
    if solver:
        argv.remove("--solver")
    report = (compare_solver if solver else compare_detector)(argv[0], argv[1])
    print(json.dumps(report, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
