# -*- coding: utf-8 -*-
"""ABLACOES DIAGNOSTICAS (prova de causa, NUNCA fix): reexecuta o solver
com UMA constante/funcao trocada em memoria (monkeypatch neste processo) e
mede o delta de achados por codigo. Nenhum arquivo de producao e' tocado.

  --ablation fit_tol_0_3     PIER_LAYOUT_TOLERANCE_CM 0.05 -> 0.30 (ruido de entrada)
  --ablation x_room_slack    folga de 0.05cm no room check do X (borderline float)
  --ablation no_arm          ARM safe repair desligado (custo x beneficio)
    -> ablation_<name>.json
"""
import argparse
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas_lib as al  # noqa: E402


def run_with(pid, patch):
    engine = al.engine()
    st = al.stepper()
    mm = sys.modules["core.engine.modulation_math"]
    undo = patch(engine, st, mm)
    try:
        run = al.run_solver_in_memory(al.load_input(pid))
    finally:
        undo()
    project = al.build_result_project(pid, run)
    findings, score, comparison, _s = al.evaluate(project, al.load_reference(pid))
    return al.counts_by_code(findings), run


def patch_fit_tol(engine, st, mm, value=0.30):
    saved = {}
    for mod in (engine, st, mm):
        for name in ("PIER_LAYOUT_TOLERANCE_CM", "MODULATION_WHOLE_CM_TOLERANCE_CM"):
            if hasattr(mod, name):
                saved[(id(mod), name)] = (mod, getattr(mod, name))
                setattr(mod, name, value)

    def undo():
        for (mod, old) in saved.values():
            pass
        for key, (mod, old) in saved.items():
            setattr(mod, key[1], old)
    return undo


def patch_x_room_slack(engine, st, mm, slack_cm=0.05):
    orig = st._x_intersection_wall_room_ft
    slack_ft = slack_cm / 30.48

    def wrapped(*a, **k):
        rp, rm = orig(*a, **k)
        return rp + slack_ft, rm + slack_ft
    st._x_intersection_wall_room_ft = wrapped

    def undo():
        st._x_intersection_wall_room_ft = orig
    return undo


def patch_no_arm(engine, st, mm):
    old = engine.ARM_ROLE_SAFE_REPAIR_ENABLED
    engine.ARM_ROLE_SAFE_REPAIR_ENABLED = False

    def undo():
        engine.ARM_ROLE_SAFE_REPAIR_ENABLED = old
    return undo


PATCHES = {"fit_tol_0_3": patch_fit_tol, "x_room_slack": patch_x_room_slack, "no_arm": patch_no_arm}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ablation", required=True, choices=sorted(PATCHES))
    ap.add_argument("--project", action="append", default=None)
    args = ap.parse_args(argv)
    ids = tuple(args.project) if args.project else ("torre_easy_lo_r00_tp1", "torre_easy_lo_r00_tgd")
    summary = al.read_json(al.out_path("state_current_summary.json"))
    out = {}
    for pid in ids:
        short = al.SHORT[pid]
        base = summary["projects"][short]["counts_by_code"]
        counts, run = run_with(pid, PATCHES[args.ablation])
        delta = {}
        for code in sorted(set(base) | set(counts)):
            b, c = base.get(code, 0), counts.get(code, 0)
            if b != c:
                delta[code] = [b, c, c - b]
        fp, n = al.physical_fingerprint(run)
        out[short] = {"baseline": base, "ablated": counts, "delta(base,ablated,diff)": delta,
                      "pieces": n, "pieces_baseline": summary["projects"][short]["physical_pieces"],
                      "solver_seconds": round(run["solver_seconds"], 1)}
        print("=====", short, args.ablation, "pieces", summary["projects"][short]["physical_pieces"], "->", n,
              "seconds", round(run["solver_seconds"], 1))
        for code, (b, c, d) in sorted(delta.items()):
            print("   %-34s %6d -> %6d  (%+d)" % (code, b, c, d))
    al.write_json(al.out_path("ablation_%s.json" % args.ablation), out)


if __name__ == "__main__":
    main()
