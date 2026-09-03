# -*- coding: utf-8 -*-
"""CR-BLOCK-DETERMINISM / etapa A - DIAGNOSTICO DE CAUSA-RAIZ.

Desce camada a camada DENTRO de `build_wall_graph`, comparando cada uma
por chave GEOMETRICA canonica entre as 8 variantes:

  1. junction_map          - o que extend_wall_ends_to_junctions registrou
                             para cada PONTA canonica;
  2. arms                  - ponta, direcao e ANCORA de cada ponta;
  3. clusters              - QUAIS pontas caem no mesmo no';
  4. classificacao         - o tipo de cada no' ja' agrupado.

A primeira dessas que divergir e' a causa-raiz; as de baixo sao efeito.
"""
import sys

import lib_det as L


def _rebuild_walls(module, input_project):
    """Mesmo caminho de `solver_bridge.plan_from_input`, parando ANTES de
    `build_wall_graph` - so' para ter o `junction_map` em maos."""
    def ft(cm):
        return float(cm) / 100.0 * module.FEET_PER_METER
    walls_to_create = []
    for wall in (input_project.get("walls") or []):
        line = module.Line.CreateBound(
            module.XYZ(ft(wall["start_cm"][0]), ft(wall["start_cm"][1]), 0.0),
            module.XYZ(ft(wall["end_cm"][0]), ft(wall["end_cm"][1]), 0.0),
        )
        walls_to_create.append((line, ft(wall["thickness_cm"]), (False, False)))
    settings = input_project.get("settings") or {}
    search = 0.0 if settings.get("walls_already_extended") else module.JUNCTION_FACE_SEARCH_FT
    return module.extend_wall_ends_to_junctions(walls_to_create, search)


def _junction_rows(walls_to_create, junction_map):
    rows = {}
    for (wall_idx, end_index), entry in junction_map.items():
        key = L.canonical_arm_key(walls_to_create, wall_idx, end_index)
        rows[str(key)] = {
            "neighbor": str(L.canonical_wall_key(walls_to_create, entry.get("neighbor_idx"))),
            "hit_t_cm": L.r((entry.get("hit_t_on_neighbor") or 0.0) * L.FT_TO_CM),
            "neighbor_len_cm": L.r((entry.get("neighbor_length_ft") or 0.0) * L.FT_TO_CM),
        }
    return rows


def _arm_rows(module, walls_to_create, junction_map):
    arms = module._wall_node_arms(walls_to_create, junction_map)
    rows = {}
    for arm in arms:
        key = L.canonical_arm_key(walls_to_create, arm["wall_idx"], arm["end_index"])
        rows[str(key)] = {
            "point_cm": L.pt_cm(arm["point"]),
            "anchor_cm": L.pt_cm(arm["anchor"]),
            "dir": (L.r(arm["outward_dir"].X), L.r(arm["outward_dir"].Y)),
        }
    return rows, arms


def _cluster_rows(module, walls_to_create, arms, tolerance_ft):
    clusters = module._cluster_wall_arms(arms, tolerance_ft)
    rows = []
    for group in clusters:
        rows.append(sorted(
            str(L.canonical_arm_key(walls_to_create, a["wall_idx"], a["end_index"]))
            for a in group))
    return sorted(rows, key=str), clusters


def probe(input_project):
    module = L.engine()
    plan = L.plan_only(input_project)
    walls_to_create, junction_map = _rebuild_walls(module, input_project)
    arm_rows, arms = _arm_rows(module, walls_to_create, junction_map)
    tolerance_ft = module.WALL_GRAPH_NODE_SNAP_TOLERANCE_FT
    cluster_rows, _clusters = _cluster_rows(module, walls_to_create, arms, tolerance_ft)
    node_rows = {}
    for node in plan["nodes"]:
        node_rows[str(L.canonical_node_identity(plan["walls_to_create"], node))] = node.get("kind")
    return {
        "junction_rows": _junction_rows(walls_to_create, junction_map),
        "arm_rows": arm_rows,
        "cluster_rows": cluster_rows,
        "node_rows": node_rows,
        "nodes": plan["nodes"],
        "plan_walls": plan["walls_to_create"],
        "arms": arms,
        "walls_to_create": walls_to_create,
    }


def _diff_dicts(a, b, limit=8):
    out = []
    for key in sorted(set(a) | set(b)):
        if a.get(key) != b.get(key):
            out.append({"key": key, "baseline": a.get(key), "variant": b.get(key)})
        if len(out) >= limit:
            break
    return out


def run(project_id=None, limit=8):
    project_id = project_id or L.PRIMARY_PROJECT_ID
    input_project = L.load_input(project_id)
    variants = L.build_variants(input_project)

    probes = {}
    for name, project in variants:
        probes[name] = probe(project)
        print("  probed", name)

    base = probes["baseline"]
    report = []
    for name, _project in variants[1:]:
        other = probes[name]
        entry = {
            "variant": name,
            "junction_map_equal": base["junction_rows"] == other["junction_rows"],
            "arms_equal": base["arm_rows"] == other["arm_rows"],
            "clusters_equal": base["cluster_rows"] == other["cluster_rows"],
            "n_clusters_baseline": len(base["cluster_rows"]),
            "n_clusters_variant": len(other["cluster_rows"]),
        }
        if not entry["junction_map_equal"]:
            entry["first_divergent_sublayer"] = "junction_map"
            entry["junction_diffs"] = _diff_dicts(base["junction_rows"], other["junction_rows"], limit)
        elif not entry["arms_equal"]:
            entry["first_divergent_sublayer"] = "arms (point/anchor/dir)"
            entry["arm_diffs"] = _diff_dicts(base["arm_rows"], other["arm_rows"], limit)
        elif not entry["clusters_equal"]:
            entry["first_divergent_sublayer"] = "_cluster_wall_arms (agrupamento)"
            base_set = set(map(str, base["cluster_rows"]))
            other_set = set(map(str, other["cluster_rows"]))
            entry["clusters_only_in_baseline"] = sorted(base_set - other_set)[:limit]
            entry["clusters_only_in_variant"] = sorted(other_set - base_set)[:limit]
        else:
            entry["first_divergent_sublayer"] = "_classify_wall_node (classificacao)"
            entry["node_diffs"] = _diff_dicts(base["node_rows"], other["node_rows"], limit)
        report.append(entry)
    return {"project_id": project_id, "report": report}, probes


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else L.PRIMARY_PROJECT_ID
    result, _probes = run(project_id)
    L.write_json(L.out_path("out_rootcause.json"), result)
    print()
    for entry in result["report"]:
        print("%-20s junction=%-5s arms=%-5s clusters=%-5s (%d vs %d) -> %s"
              % (entry["variant"], entry["junction_map_equal"], entry["arms_equal"],
                 entry["clusters_equal"], entry["n_clusters_baseline"],
                 entry["n_clusters_variant"], entry["first_divergent_sublayer"]))
    return result


if __name__ == "__main__":
    main()
