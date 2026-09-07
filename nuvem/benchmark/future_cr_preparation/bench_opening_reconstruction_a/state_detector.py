# -*- coding: utf-8 -*-
"""STATE do DETECTOR: roda detect_wall_openings_from_courses sobre a
geometria REAL do gabarito humano (reference.json) dos 3 projetos.

Nao escreve nada em nuvem/benchmark/projects. E' o unico ponto onde a
correcao do detector produz efeito mensuravel no corpus atual, ja' que
input.json/reference.json estao congelados.
"""
import collections
import json
import os
import sys

ROOT = os.environ.get("REPO_ROOT", os.path.abspath("."))
sys.path.insert(0, ROOT)

from nuvem.core.engine import opening_audit  # noqa: E402

PROJECTS = ["piloto_sintetico_2x2", "torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"]


def courses_of(wall):
    by_z = {}
    for row in wall.get("rows") or []:
        z = row.get("elevation_cm")
        bucket = by_z.setdefault(z, [])
        for block in row.get("blocks") or []:
            bucket.append((block["t_start_cm"], block["t_end_cm"],
                           block.get("type_name")))
    return [(z, iv) for z, iv in sorted(by_z.items())]


def main():
    label = sys.argv[1]
    out_path = sys.argv[2]
    state = {"label": label, "projects": {}}
    for proj in PROJECTS:
        path = os.path.join(ROOT, "nuvem", "benchmark", "projects", proj,
                            "reference.json")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        detected = []
        for wall in data.get("walls") or []:
            for op in opening_audit.detect_wall_openings_from_courses(courses_of(wall)):
                row = {"wall": wall["id"]}
                row.update(op)
                row["x_range"] = [round(v, 4) for v in op["x_range"]]
                row["z_range"] = [round(v, 4) for v in op["z_range"]]
                row["width_cm"] = round(op["width_cm"], 4)
                detected.append(row)
        detected.sort(key=lambda r: (r["wall"], r["x_range"][0], r["z_range"][0]))
        widths = collections.Counter(round(r["width_cm"], 1) for r in detected)
        state["projects"][proj] = {
            "n_openings": len(detected),
            "widths": dict(sorted(widths.items())),
            "openings": detected,
        }
        print("%-24s aberturas_detectadas=%d larguras_distintas=%d" % (
            proj, len(detected), len(widths)))
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=1, sort_keys=True)
    print("escrito:", out_path)


if __name__ == "__main__":
    main()
