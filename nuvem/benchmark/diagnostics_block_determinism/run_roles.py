# -*- coding: utf-8 -*-
"""CR-BLOCK-DETERMINISM / etapa A - DEPENDENCIAS DE ORDEM *LATENTES*.

`canonical_node_key` ORDENA `arms` e `crossing_walls` - de proposito, para
poder perguntar "e' o mesmo no'?". Mas o solver da Etapa 4 NAO usa esses
campos ordenados: ele le' a ORDEM deles (qual parede e' `main`, qual e'
`incoming`, qual e' `crossing_walls[0]`) para orientar B34/B54. Este
script mede exatamente o que o fingerprint canonico esconde: se o PAPEL
de cada parede dentro do no' muda com a permutacao.
"""
import sys

import lib_det as L


def role_rows(walls_to_create, nodes):
    """{identidade_do_no' -> papeis NA ORDEM em que o solver os le'}."""
    rows = {}
    for node in nodes:
        ident = str(L.canonical_node_identity(walls_to_create, node))
        rows[ident] = {
            "kind": node.get("kind"),
            "point_cm": L.pt_cm(node["point"]),
            # NAO ordenado - a ordem e' justamente o que se mede aqui.
            "arms_in_order": [str(L.canonical_arm_key(walls_to_create, w, e))
                              for w, e in (node.get("arms") or [])],
            "main": str(L.canonical_wall_key(walls_to_create, node.get("main_wall_idx"))),
            "incoming": str(L.canonical_wall_key(walls_to_create, node.get("incoming_wall_idx"))),
            "neighbor": str(L.canonical_wall_key(walls_to_create, node.get("neighbor_wall_idx"))),
            "neighbor_end_index": node.get("neighbor_end_index"),
            "crossing_in_order": [str(L.canonical_wall_key(walls_to_create, w))
                                  for w in (node.get("crossing_walls") or [])],
        }
    return rows


def run(project_id=None, limit=10):
    project_id = project_id or L.PRIMARY_PROJECT_ID
    input_project = L.load_input(project_id)
    variants = L.build_variants(input_project)

    by_name = {}
    for name, project in variants:
        plan = L.plan_only(project)
        by_name[name] = role_rows(plan["walls_to_create"], plan["nodes"])
        print("  probed", name)

    base = by_name["baseline"]
    report = []
    for name, _p in variants[1:]:
        other = by_name[name]
        shared = set(base) & set(other)
        diffs = {"point": [], "kind": [], "roles": [], "arms_order": [],
                 "crossing_order": []}
        for ident in sorted(shared):
            b, o = base[ident], other[ident]
            if b["point_cm"] != o["point_cm"]:
                diffs["point"].append({"node": ident, "baseline": b["point_cm"],
                                       "variant": o["point_cm"]})
            if b["kind"] != o["kind"]:
                diffs["kind"].append({"node": ident, "baseline": b["kind"],
                                      "variant": o["kind"]})
            if (b["main"], b["incoming"], b["neighbor"], b["neighbor_end_index"]) != \
               (o["main"], o["incoming"], o["neighbor"], o["neighbor_end_index"]):
                diffs["roles"].append({
                    "node": ident,
                    "baseline": [b["main"], b["incoming"], b["neighbor"], b["neighbor_end_index"]],
                    "variant": [o["main"], o["incoming"], o["neighbor"], o["neighbor_end_index"]]})
            if b["arms_in_order"] != o["arms_in_order"]:
                diffs["arms_order"].append({"node": ident, "baseline": b["arms_in_order"],
                                            "variant": o["arms_in_order"]})
            if b["crossing_in_order"] != o["crossing_in_order"]:
                diffs["crossing_order"].append({"node": ident,
                                                "baseline": b["crossing_in_order"],
                                                "variant": o["crossing_in_order"]})
        report.append({
            "variant": name,
            "n_shared_nodes": len(shared),
            "n_only_baseline": len(set(base) - set(other)),
            "n_only_variant": len(set(other) - set(base)),
            "counts": dict((k, len(v)) for k, v in diffs.items()),
            "samples": dict((k, v[:limit]) for k, v in diffs.items()),
        })
    return {"project_id": project_id, "report": report}


def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 else L.PRIMARY_PROJECT_ID
    result = run(project_id)
    L.write_json(L.out_path("out_roles.json"), result)
    print()
    print("%-20s %7s %7s %7s | %6s %6s %6s %6s %6s"
          % ("variante", "shared", "so'base", "so'var", "point", "kind", "roles",
             "armsO", "crossO"))
    for e in result["report"]:
        c = e["counts"]
        print("%-20s %7d %7d %7d | %6d %6d %6d %6d %6d"
              % (e["variant"], e["n_shared_nodes"], e["n_only_baseline"],
                 e["n_only_variant"], c["point"], c["kind"], c["roles"],
                 c["arms_order"], c["crossing_order"]))
    return result


if __name__ == "__main__":
    main()
