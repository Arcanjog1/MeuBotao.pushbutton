# -*- coding: utf-8 -*-
"""CR-B / CANDIDATO §7 — PROJECAO REAL DO SOLVER sobre copias ISOLADAS.

Roda o solver de PRODUCAO, sem alterar uma linha dele, sobre tres entradas
por projeto, e compara SEMPRE por identidade fisica:

  IN_OFICIAL   `nuvem/benchmark/projects/<proj>/input.json` (leitura)
  IN_R         input derivado do round-trip do gabarito, SEM corte
  IN_C         input derivado do CANDIDATO

E calibra os validadores sobre os TRES gabaritos (piso de ruido do
proprio gabarito): STATE_A (oficial), STATE_R, STATE_C.

Nada e' escrito em `nuvem/benchmark/projects/**`.
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import candidate_lib as C  # noqa: E402

from nuvem.benchmark import runner as bench_runner  # noqa: E402
from nuvem.benchmark import scoring, validators  # noqa: E402
from nuvem.benchmark import solver_bridge  # noqa: E402
from nuvem.benchmark.extract import from_solver  # noqa: E402


def solve(input_project, project_id):
    (res, walls, nodes, ops, catalog, base_z, ncourses, notes) = \
        solver_bridge.run_solver(input_project)
    return from_solver.project_from_solver(
        project_id, res, walls, nodes, ops, catalog, base_z, ncourses,
        metadata={"from_input": "isolated candidate run"})


def calib(reference):
    f, e = validators.run_all(reference, {})
    return scoring.score_project(reference, f, e), f


def flat(score):
    """Metricas comparaveis, achatadas."""
    out = {"blocks": score.get("blocks"),
           "walls": score.get("walls"),
           "critical_errors": score.get("critical_errors"),
           "coverage_pct": score.get("coverage_pct")}
    for c in score.get("categories") or []:
        out["cat:" + c["category"]] = c["findings"]
        out["catL1:" + c["category"]] = c["findings_level_1"]
    for code, n in (score.get("critical_by_code") or {}).items():
        out["crit:" + code] = n
    return out


def codes(findings):
    return collections.Counter(f.get("code") for f in findings)


def delta(a, b):
    keys = sorted(set(a) | set(b))
    return {k: {"antes": a.get(k, 0), "depois": b.get(k, 0),
                "delta": (b.get(k, 0) or 0) - (a.get(k, 0) or 0)}
            for k in keys
            if (b.get(k, 0) or 0) != (a.get(k, 0) or 0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.environ.get("CR_B_OUT",
                                                    os.path.join(HERE, "_out")))
    args = ap.parse_args()
    saida = {}
    for proj in C.PROJECTS:
        d = os.path.join(args.out, proj)
        refs = {
            "STATE_A_oficial": C.load_reference(proj),
            "STATE_R_roundtrip": json.load(open(d + "/reference_roundtrip.json",
                                                encoding="utf-8")),
            "STATE_C_candidato": json.load(open(d + "/reference_candidate.json",
                                                encoding="utf-8")),
        }
        inputs = {
            "IN_OFICIAL": C.load_input(proj),
            "IN_R": json.load(open(d + "/input_roundtrip.json", encoding="utf-8")),
            "IN_C": json.load(open(d + "/input_candidate.json", encoding="utf-8")),
        }

        entrada = {"gabarito_calibracao": {}, "solver": {}}
        # --- piso de ruido do PROPRIO gabarito (validadores sobre ele)
        for name, ref in refs.items():
            sc, fi = calib(ref)
            entrada["gabarito_calibracao"][name] = {
                "flat": flat(sc), "codigos": dict(sorted(codes(fi).items()))}

        # --- solver
        results = {}
        for name, inp in inputs.items():
            r = solve(inp, proj)
            results[name] = r
            entrada["solver"][name] = {
                "paredes_entrada": len(inp.get("walls") or []),
                "aberturas_entrada": sum(len(w.get("openings") or [])
                                         for w in inp.get("walls") or []),
            }

        # --- avaliacao: cada resultado contra o gabarito que lhe corresponde
        pares = [
            ("IN_OFICIAL x STATE_A", "IN_OFICIAL", "STATE_A_oficial"),
            ("IN_OFICIAL x STATE_R", "IN_OFICIAL", "STATE_R_roundtrip"),
            ("IN_OFICIAL x STATE_C", "IN_OFICIAL", "STATE_C_candidato"),
            ("IN_R x STATE_R", "IN_R", "STATE_R_roundtrip"),
            ("IN_C x STATE_C", "IN_C", "STATE_C_candidato"),
        ]
        entrada["avaliacao"] = {}
        for label, ink, refk in pares:
            fi, sc, cmpx = bench_runner.evaluate_project(results[ink], refs[refk])
            entrada["avaliacao"][label] = {
                "flat": flat(sc),
                "codigos": dict(sorted(codes(fi).items())),
                "comparacao": {k: v for k, v in (cmpx or {}).items()
                               if not isinstance(v, (list, dict))},
            }
        saida[proj] = entrada

        print("=" * 100)
        print(proj)
        print("-- PISO DE RUIDO DO PROPRIO GABARITO (validadores sobre o gabarito)")
        A = entrada["gabarito_calibracao"]["STATE_A_oficial"]["codigos"]
        R = entrada["gabarito_calibracao"]["STATE_R_roundtrip"]["codigos"]
        K = entrada["gabarito_calibracao"]["STATE_C_candidato"]["codigos"]
        for code in sorted(set(A) | set(R) | set(K)):
            print("   %-38s A=%-7s R=%-7s C=%-7s  (C-R)=%+d"
                  % (code, A.get(code, 0), R.get(code, 0), K.get(code, 0),
                     K.get(code, 0) - R.get(code, 0)))
        print("-- SOLVER (identidade das entradas)")
        for k in ["IN_OFICIAL", "IN_R", "IN_C"]:
            print("   %-12s paredes=%-5s aberturas=%s"
                  % (k, entrada["solver"][k]["paredes_entrada"],
                     entrada["solver"][k]["aberturas_entrada"]))
        print("-- AVALIACAO (achados por codigo)")
        for label, _i, _r in pares:
            f = entrada["avaliacao"][label]["flat"]
            print("   %-24s blocks=%-7s criticos=%-6s cobertura=%s"
                  % (label, f.get("blocks"), f.get("critical_errors"),
                     f.get("coverage_pct")))
    p = C.write_json(os.path.join(args.out, "solver_projection.json"), saida)
    print("escrito:", p)


if __name__ == "__main__":
    main()
