# -*- coding: utf-8 -*-
"""CR-BLOCK-DETERMINISM / etapa A - EXEMPLOS GEOMETRICOS REAIS.

Para cada causa-raiz achada por `run_rootcause.py`, imprime o no'
divergente COM NUMEROS: coordenada, paredes participantes, distancias
entre ancoras, resultado no baseline, resultado na permutacao, e QUAL
decisao do codigo produziu a diferenca.
"""
import itertools
import sys

import lib_det as L
import run_rootcause as RC


def anchor_triangles(project_id=None):
    """Todos os TRIOS de pontas cuja relacao 'a menos de tolerancia' NAO e'
    transitiva (A~B, A~C, mas B!~C). Cada um desses e' um no' cuja
    composicao depende de QUEM foi visitado primeiro em
    `_cluster_wall_arms` - e' a definicao operacional da causa-raiz."""
    module = L.engine()
    project_id = project_id or L.PRIMARY_PROJECT_ID
    input_project = L.load_input(project_id)
    walls_to_create, junction_map = RC._rebuild_walls(module, input_project)
    arms = module._wall_node_arms(walls_to_create, junction_map)
    tol = module.WALL_GRAPH_NODE_SNAP_TOLERANCE_FT

    keys = [L.canonical_arm_key(walls_to_create, a["wall_idx"], a["end_index"]) for a in arms]
    n = len(arms)
    near = [[False] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            close = arms[i]["anchor"].DistanceTo(arms[j]["anchor"]) <= tol
            near[i][j] = near[j][i] = close

    triangles = []
    for i in range(n):
        partners = [j for j in range(n) if near[i][j]]
        for a, b in itertools.combinations(partners, 2):
            if not near[a][b]:
                triangles.append({
                    "pivot": str(keys[i]),
                    "pivot_anchor_cm": L.pt_cm(arms[i]["anchor"]),
                    "arm_b": str(keys[a]),
                    "arm_b_anchor_cm": L.pt_cm(arms[a]["anchor"]),
                    "arm_c": str(keys[b]),
                    "arm_c_anchor_cm": L.pt_cm(arms[b]["anchor"]),
                    "d_pivot_b_cm": L.r(arms[i]["anchor"].DistanceTo(arms[a]["anchor"]) * L.FT_TO_CM),
                    "d_pivot_c_cm": L.r(arms[i]["anchor"].DistanceTo(arms[b]["anchor"]) * L.FT_TO_CM),
                    "d_b_c_cm": L.r(arms[a]["anchor"].DistanceTo(arms[b]["anchor"]) * L.FT_TO_CM),
                    "tolerance_cm": L.r(tol * L.FT_TO_CM),
                })
    return triangles


def degenerate_groups(project_id=None):
    """Grupos em que a MESMA parede entra com as DUAS pontas (parede mais
    curta que a tolerancia de agrupamento). Nesses, `group[0]["anchor"]`
    - o ponto do no' - depende do SENTIDO em que o eixo foi desenhado."""
    module = L.engine()
    project_id = project_id or L.PRIMARY_PROJECT_ID
    input_project = L.load_input(project_id)
    walls_to_create, junction_map = RC._rebuild_walls(module, input_project)
    arms = module._wall_node_arms(walls_to_create, junction_map)
    clusters = module._cluster_wall_arms(arms, module.WALL_GRAPH_NODE_SNAP_TOLERANCE_FT)
    out = []
    for group in clusters:
        seen = {}
        for arm in group:
            seen.setdefault(arm["wall_idx"], []).append(arm)
        for wall_idx, group_arms in seen.items():
            if len(group_arms) < 2:
                continue
            line = walls_to_create[wall_idx][0]
            out.append({
                "wall": str(L.canonical_wall_key(walls_to_create, wall_idx)),
                "length_cm": L.r(line.GetEndPoint(0).DistanceTo(line.GetEndPoint(1)) * L.FT_TO_CM),
                "anchors_cm": [L.pt_cm(a["anchor"]) for a in group_arms],
                "node_point_taken_cm": L.pt_cm(group[0].get("anchor") or group[0]["point"]),
                "group_size": len(group),
            })
    return out


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else L.PRIMARY_PROJECT_ID
    triangles = anchor_triangles(project_id)
    degenerates = degenerate_groups(project_id)
    payload = {
        "project_id": project_id,
        "causa_1_cluster_nao_transitivo": {
            "descricao": "trios (A~B, A~C, B!~C) - a composicao do no' "
                         "depende de quem `_cluster_wall_arms` visitou primeiro",
            "total": len(triangles),
            "exemplos": triangles[:12],
        },
        "causa_2_ponto_do_no_pelo_group0": {
            "descricao": "paredes mais curtas que a tolerancia entram no "
                         "grupo com as DUAS pontas; `point = group[0].anchor` "
                         "escolhe uma delas pela ORDEM, nao pela geometria",
            "total": len(degenerates),
            "exemplos": degenerates[:12],
        },
    }
    L.write_json(L.out_path("out_examples.json"), payload)
    print("trios nao-transitivos:", len(triangles))
    for t in triangles[:5]:
        print("  pivot %s @%s" % (t["pivot"], t["pivot_anchor_cm"]))
        print("     d(pivot,B)=%.2f d(pivot,C)=%.2f d(B,C)=%.2f  tol=%.2f"
              % (t["d_pivot_b_cm"], t["d_pivot_c_cm"], t["d_b_c_cm"], t["tolerance_cm"]))
    print("\ngrupos com parede curta (duas pontas no mesmo no'):", len(degenerates))
    for d in degenerates[:5]:
        print("  parede %s len=%.2fcm ancoras=%s -> no' em %s"
              % (d["wall"], d["length_cm"], d["anchors_cm"], d["node_point_taken_cm"]))
    return payload


if __name__ == "__main__":
    main()
