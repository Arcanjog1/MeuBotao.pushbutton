# -*- coding: utf-8 -*-
"""CR-BLOCK-DETERMINISM / secao 17 - LOCALIZAR A SEGUNDA CAUSA.

Depois de canonizar o grafo, 7 das 8 variantes passam a dar o MESMO
fingerprint de blocos. So' `endpoint_reversal` continua diferente, e a
primeira camada divergente dela ja' NAO e' o grafo (que fica identico) -
e' `fp_candidates`.

Este script responde: onde exatamente, e de quem e' a linha.
"""
import sys

import lib_det as L


def _spans_by_wall(walls_to_create, solve_result, only=None):
    """Para cada parede (chave GEOMETRICA) e fiada, a sequencia de pecas
    projetada no eixo - mas medida a partir da ponta CANONICA `lo` da
    parede, nao de `p0`, para que inverter o sentido do desenho nao mude a
    medicao por si so'. Se as sequencias continuarem diferentes depois
    disso, a diferenca e' REAL (o solver posicionou outra coisa), nao um
    artefato do referencial."""
    import math
    out = {}
    course_candidates = solve_result.get("course_candidates") or {}
    for course_index in sorted(course_candidates.keys()):
        for cand in course_candidates[course_index]:
            wall_idx = cand.get("wall_idx")
            if wall_idx is None:
                continue
            is_node_piece = cand.get("node_index") is not None
            if only == "node" and not is_node_piece:
                continue
            if only == "fill" and is_node_piece:
                continue
            line = walls_to_create[wall_idx][0]
            a = L.pt_cm(line.GetEndPoint(0))
            b = L.pt_cm(line.GetEndPoint(1))
            lo, hi = (a, b) if a <= b else (b, a)
            dx, dy = hi[0] - lo[0], hi[1] - lo[1]
            norm = math.hypot(dx, dy) or 1.0
            ux, uy = dx / norm, dy / norm
            origin = cand["origin_world"]
            ox = origin.X * L.FT_TO_CM
            oy = origin.Y * L.FT_TO_CM
            t = (ox - lo[0]) * ux + (oy - lo[1]) * uy
            key = (L.canonical_wall_key(walls_to_create, wall_idx), course_index)
            # 0,1 cm de granularidade: bem abaixo do modulo de 5 cm e da
            # junta de 1 cm, e longe o bastante das bordas de
            # arredondamento para o proprio round() nao inventar
            # divergencia de 0,01 cm que nao existe na geometria.
            out.setdefault(key, []).append((round(t, 1), cand["logical_code"]))
    for key in out:
        out[key].sort()
    return out


def run(project_id=None):
    project_id = project_id or L.PRIMARY_PROJECT_ID
    input_project = L.load_input(project_id)

    base = L.run_full(input_project)
    rev = L.run_full(L.reversed_endpoints_input(input_project))

    layers = {}
    for only, label in ((None, "todas"), ("node", "pecas de amarracao (L/T/X)"),
                        ("fill", "pecas de preenchimento")):
        b = _spans_by_wall(base["walls_to_create"], base["solve_result"], only)
        r = _spans_by_wall(rev["walls_to_create"], rev["solve_result"], only)
        ks = set(b) | set(r)
        layers[label] = {
            "n_pares": len(ks),
            "n_divergentes": sum(1 for k in ks if b.get(k) != r.get(k)),
        }

    base_spans = _spans_by_wall(base["walls_to_create"], base["solve_result"])
    rev_spans = _spans_by_wall(rev["walls_to_create"], rev["solve_result"])

    keys = set(base_spans) | set(rev_spans)
    diverging = sorted(str(k) for k in keys if base_spans.get(k) != rev_spans.get(k))
    walls_diverging = sorted(set(str(k[0]) for k in keys
                                if base_spans.get(k) != rev_spans.get(k)))

    samples = []
    for key in sorted(keys, key=str):
        if base_spans.get(key) == rev_spans.get(key):
            continue
        samples.append({
            "wall": str(key[0]), "course": key[1],
            "baseline": base_spans.get(key),
            "endpoint_reversal": rev_spans.get(key),
        })
        if len(samples) >= 6:
            break

    return {
        "project_id": project_id,
        "por_camada": layers,
        "n_wall_course_pairs": len(keys),
        "n_diverging_pairs": len(diverging),
        "n_diverging_walls": len(walls_diverging),
        "n_walls_total": len(set(str(k[0]) for k in keys)),
        "samples": samples,
    }


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else L.PRIMARY_PROJECT_ID
    result = run(project_id)
    L.write_json(L.out_path("out_second_cause.json"), result)
    print("pares (parede, fiada) divergentes: %d de %d"
          % (result["n_diverging_pairs"], result["n_wall_course_pairs"]))
    print("paredes envolvidas: %d de %d"
          % (result["n_diverging_walls"], result["n_walls_total"]))
    print()
    for label, row in result["por_camada"].items():
        print("  %-30s %5d de %5d pares divergem"
              % (label, row["n_divergentes"], row["n_pares"]))
    for s in result["samples"][:3]:
        print("\nparede", s["wall"], "fiada", s["course"])
        print("  base:", s["baseline"])
        print("  rev :", s["endpoint_reversal"])
    return result


if __name__ == "__main__":
    main()
