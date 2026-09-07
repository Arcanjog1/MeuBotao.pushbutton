# -*- coding: utf-8 -*-
"""CR-B: a reconstrucao do gabarito e' REPRODUTIVEL a partir do proprio
`reference.json`?

O dump bruto do Revit NAO esta' versionado (`revit_dump.py` roda dentro do
Revit via MCP). Mas `build_project` so' precisa de `types` + `instances`, e
todos esses campos sobrevivem em `reference.json`. Se o round-trip devolver
o gabarito IDENTICO, a CR-B pode projetar constantes alternativas offline,
sem reabrir o Revit. Se nao devolver, a CR-B depende de nova extracao.

NAO escreve nada em `nuvem/benchmark/projects/**`. Saida em /tmp.
"""
import json
import os
import sys

ROOT = os.environ.get("REPO_ROOT", "/home/user/MeuBotao.pushbutton")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from nuvem.benchmark.extract import reconstruct  # noqa: E402


def dump_from_reference(ref):
    """`reference.json` -> dump bruto sintetico (types + instances)."""
    types, index_of = [], {}
    instances = []
    blocks = []
    for wall in ref.get("walls") or []:
        for row in wall.get("rows") or []:
            for b in row.get("blocks") or []:
                blocks.append(b)
    blocks.extend(ref.get("orphan_blocks") or [])
    for b in blocks:
        key = (b["type_name"], b["family"], b["length_cm"], b["height_cm"],
               b["width_cm"])
        if key not in index_of:
            index_of[key] = len(types)
            types.append({"index": len(types), "type_name": b["type_name"],
                          "family": b["family"], "length_cm": b["length_cm"],
                          "height_cm": b["height_cm"], "width_cm": b["width_cm"]})
        instances.append([index_of[key], b["center_cm"][0], b["center_cm"][1],
                          b["z_cm"], b["rotation_deg"], bool(b["mirrored"])])
    return {"types": types, "instances": instances}, len(blocks)


def compare(a, b):
    """Diferencas estruturais entre dois projetos."""
    wa = {w["key"]: w for w in a.get("walls") or []}
    wb = {w["key"]: w for w in b.get("walls") or []}
    so_a, so_b = sorted(set(wa) - set(wb)), sorted(set(wb) - set(wa))
    dif_geom, dif_op = [], []
    for k in sorted(set(wa) & set(wb)):
        x, y = wa[k], wb[k]
        nb_x = sum(len(r.get("blocks") or []) for r in x.get("rows") or [])
        nb_y = sum(len(r.get("blocks") or []) for r in y.get("rows") or [])
        if (round(x["length_cm"], 3) != round(y["length_cm"], 3)
                or nb_x != nb_y or len(x.get("rows") or []) != len(y.get("rows") or [])):
            dif_geom.append((k, x["length_cm"], y["length_cm"], nb_x, nb_y))
        ox = sorted((round(o["t_start_cm"], 3), round(o["t_end_cm"], 3), o["kind"])
                    for o in x.get("openings") or [])
        oy = sorted((round(o["t_start_cm"], 3), round(o["t_end_cm"], 3), o["kind"])
                    for o in y.get("openings") or [])
        if ox != oy:
            dif_op.append((k, ox, oy))
    return so_a, so_b, dif_geom, dif_op


def main():
    out = {}
    for proj in ["torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"]:
        path = os.path.join(ROOT, "nuvem/benchmark/projects", proj, "reference.json")
        ref = json.load(open(path, encoding="utf-8"))
        dump, n_blocks = dump_from_reference(ref)
        rebuilt = reconstruct.build_project(dump, proj, source="revit_reference")
        so_a, so_b, dif_geom, dif_op = compare(ref, rebuilt)

        n_op_ref = sum(len(w.get("openings") or []) for w in ref["walls"])
        n_op_new = sum(len(w.get("openings") or []) for w in rebuilt["walls"])
        print("=" * 88)
        print("%s   blocos=%d" % (proj, n_blocks))
        print("  paredes  gabarito=%-4d round-trip=%-4d  so' no gabarito=%d  so' no round-trip=%d"
              % (len(ref["walls"]), len(rebuilt["walls"]), len(so_a), len(so_b)))
        print("  aberturas gabarito=%-4d round-trip=%-4d" % (n_op_ref, n_op_new))
        print("  paredes casadas com geometria/contagem DIFERENTE: %d" % len(dif_geom))
        print("  paredes casadas com ABERTURAS diferentes:         %d" % len(dif_op))
        for k, ox, oy in dif_op[:6]:
            print("     %s\n        gabarito  : %s\n        round-trip: %s" % (k, ox, oy))
        out[proj] = {
            "n_blocos": n_blocks,
            "paredes_gabarito": len(ref["walls"]),
            "paredes_roundtrip": len(rebuilt["walls"]),
            "so_no_gabarito": so_a, "so_no_roundtrip": so_b,
            "n_aberturas_gabarito": n_op_ref, "n_aberturas_roundtrip": n_op_new,
            "paredes_com_geometria_diferente": dif_geom,
            "paredes_com_aberturas_diferentes": dif_op,
        }
    p = os.path.join(HERE, "roundtrip_probe.json")
    json.dump(out, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False,
              sort_keys=True)
    print("escrito:", p)


if __name__ == "__main__":
    main()
