# -*- coding: utf-8 -*-
"""INVARIANCIA (item 20): permutacao da ordem das paredes, inversao de
pontas, geometria espelhada e rotacao H/V, sobre o piloto sintetico e os
reprodutores minimos. Compara a assinatura FISICA canonica (parede
identificada pela chave geometrica, nunca por indice).
    -> invariance.json
"""
import os
import random
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas_lib as al  # noqa: E402
import repro_lib as R  # noqa: E402
from repro_lib import seg  # noqa: E402

m = al.engine()


def canonical_signature(run, transform=None):
    """{(chave geometrica da parede, fiada, codigo, t0', t1')...} com t
    medido a partir do ponto canonico (menor ponta) para ser invariante a
    inversao; `transform` (x,y)->(x,y) desfaz espelho/rotacao antes de
    assinar."""
    rows = set()
    walls = run["walls_to_create"]
    for ci, cands in al.physical_courses(run["solve_result"]).items():
        for c in cands:
            wi = c.get("wall_idx")
            if wi is None:
                continue
            p0, p1, d, L, th = al.wall_axis_cm(walls, wi)
            t0, t1, _s = al.candidate_extent_cm(c, walls, wi)
            if transform:
                p0 = transform(p0)
                p1 = transform(p1)
            a, b_ = (p0, p1)
            key_pts = sorted([(round(a[0], 1), round(a[1], 1)), (round(b_[0], 1), round(b_[1], 1))])
            # t canonico: distancia da menor ponta
            if (round(p0[0], 1), round(p0[1], 1)) == key_pts[0]:
                ct0, ct1 = t0, t1
            else:
                ct0, ct1 = L - t1, L - t0
            rows.add((tuple(key_pts[0]), tuple(key_pts[1]), ci, c.get("logical_code"), round(ct0, 1), round(ct1, 1)))
    return rows


def lines_of(run):
    out = []
    for line, th, locks in run["walls_to_create"]:
        pass
    return out


def parity_insensitive(sig):
    """Multiconjunto {parede: {composicao das fiadas pares, composicao das
    impares}} sem distinguir qual paridade e' qual - separa 'so' trocou A<->B'
    de 'layout fisico diferente'."""
    per_wall = {}
    for (a, b_, ci, code, t0, t1) in sig:
        per_wall.setdefault((a, b_), {0: set(), 1: set()})[ci % 2].add((code, t0, t1))
    out = set()
    for key, d in per_wall.items():
        pair = tuple(sorted([tuple(sorted(d[0])), tuple(sorted(d[1]))]))
        out.add((key, pair))
    return out


def classify(sig, base):
    if sig == base:
        return "INVARIANT"
    if parity_insensitive(sig) == parity_insensitive(base):
        return "PARITY_FLIP_ONLY"
    return "DIFFERENT_LAYOUT"


def build_variants(base_lines_cm, name, already_extended=False):
    """base_lines_cm: [(x0,y0,x1,y1)] em cm. Gera variantes e compara."""
    results = {}

    def solve_from(lines_cm, transform=None):
        lines = [seg(*l) for l in lines_cm]
        run = R.solve(lines, already_extended=already_extended)
        return canonical_signature(run, transform)

    base = solve_from(base_lines_cm)
    results["walls"] = len(base_lines_cm)
    results["pieces"] = len(base)
    # permutacoes
    rng = random.Random(7)
    perm_ok = 0
    perm_diff = []
    for k in range(6):
        order = list(range(len(base_lines_cm)))
        rng.shuffle(order)
        sig = solve_from([base_lines_cm[i] for i in order])
        cls = classify(sig, base)
        if cls == "INVARIANT":
            perm_ok += 1
        else:
            perm_diff.append((order, cls, len(sig ^ base)))
    results["permutation"] = {"ok": perm_ok, "of": 6, "diffs": perm_diff[:6]}
    # inversao de pontas (todas)
    rev = [(x1, y1, x0, y0) for (x0, y0, x1, y1) in base_lines_cm]
    sig = solve_from(rev)
    results["endpoint_reversal_all"] = {"class": classify(sig, base), "diff_pieces": len(sig ^ base)}
    # inversao de metade
    half = [(x1, y1, x0, y0) if i % 2 else (x0, y0, x1, y1) for i, (x0, y0, x1, y1) in enumerate(base_lines_cm)]
    sig = solve_from(half)
    results["endpoint_reversal_half"] = {"class": classify(sig, base), "diff_pieces": len(sig ^ base)}
    # espelho em X (x -> -x), desfeito na assinatura
    mir = [(-x0, y0, -x1, y1) for (x0, y0, x1, y1) in base_lines_cm]
    sig = solve_from(mir, transform=lambda p: (-p[0], p[1]))
    results["mirror_x"] = {"class": classify(sig, base), "diff_pieces": len(sig ^ base)}
    # rotacao 90 (H<->V): (x,y)->(-y,x)
    rot = [(-y0, x0, -y1, x1) for (x0, y0, x1, y1) in base_lines_cm]
    sig = solve_from(rot, transform=lambda p: (p[1], -p[0]))
    results["rotate_90"] = {"class": classify(sig, base), "diff_pieces": len(sig ^ base)}
    # translacao
    tr = [(x0 + 1234, y0 - 567, x1 + 1234, y1 - 567) for (x0, y0, x1, y1) in base_lines_cm]
    sig = solve_from(tr, transform=lambda p: (p[0] - 1234, p[1] + 567))
    results["translation"] = {"class": classify(sig, base), "diff_pieces": len(sig ^ base)}
    print("==", name, results)
    return results


def main():
    out = {}
    a, b = 350.0, 700.0
    grade = [(0, 0, a, 0), (0, 0, 0, a), (a, 0, b, 0), (a, 0, a, a), (b, 0, b, a), (0, a, a, a), (0, a, 0, b),
             (a, a, b, a), (a, a, a, b), (b, a, b, b), (0, b, a, b), (a, b, b, b)]
    out["grade_2x2_piloto"] = build_variants(grade, "grade 2x2 (topologia do piloto)")
    out["R1_boneca_79"] = build_variants([(7, 0, 597, 0), (302, 0, 302, 65), (302, 65, 699, 65), (7, 0, 7, 300), (597, 0, 597, 300)], "R1 boneca 79")
    out["R2b_x_borderline"] = build_variants([(7, 0, 1337, 0), (7, -400, 7, 300), (1337, -400, 1337, 300), (61.99, -55, 61.99, 55), (61.99, -55, 262, -55), (61.99, 55, 262, 55)], "R2b X borderline")
    out["R5_L_porta_5cm"] = build_variants([(0, 0, 400, 0), (400, 0, 400, 400)], "R5 (sem abertura - so' geometria)")
    al.write_json(al.out_path("invariance.json"), out)


if __name__ == "__main__":
    main()
