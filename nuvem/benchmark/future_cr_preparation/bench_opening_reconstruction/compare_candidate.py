# -*- coding: utf-8 -*-
"""BENCH-OPENING-RECONSTRUCTION - EXPERIMENTO CONTROLADO.

Roda TODOS os validadores sobre o gabarito ATUAL e sobre o CANDIDATO, e
compara. Nenhum arquivo oficial e' lido para escrita nem alterado.

Alem das contagens, checa as invariantes de seguranca do candidato:
  * mesma quantidade de paredes, fiadas e blocos (nada foi movido);
  * mesmo conjunto de aberturas (nenhuma sumiu nem nasceu);
  * nenhuma abertura DESLOCADA (centro preservado) - so' estreitada;
  * nenhuma abertura fora da lista de correcao foi tocada.
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT)

from nuvem.benchmark import validators  # noqa: E402

PROJ_DIR = os.path.join(ROOT, "nuvem", "benchmark", "projects")
PROJECTS = ("torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1")

WATCH = ("OPENING_BLOCK_CROSSES_JAMB", "OPENING_BLOCK_INSIDE_DOOR",
         "OPENING_BLOCK_INSIDE_WINDOW", "OPENING_MISSING_LINTEL",
         "OPENING_MISSING_COUNTER_LINTEL", "OPENING_SOLID_BELOW_SILL_MISSING")


def _counts(doc):
    findings, errors = validators.run_all(doc)
    assert not errors, errors
    return collections.Counter(f["code"] for f in findings), findings


def _shape(doc):
    walls = doc.get("walls") or []
    rows = sum(len(w.get("rows") or []) for w in walls)
    blocks = sum(len(r.get("blocks") or [])
                 for w in walls for r in w.get("rows") or [])
    openings = sum(len(w.get("openings") or []) for w in walls)
    return {"walls": len(walls), "rows": rows, "blocks": blocks,
            "openings": openings}


def main():
    report = {}
    for proj in PROJECTS:
        with open(os.path.join(PROJ_DIR, proj, "reference.json")) as handle:
            atual = json.load(handle)
        cand_path = os.path.join(HERE, "candidate_reference_%s.json" % proj)
        with open(cand_path) as handle:
            cand = json.load(handle)

        shape_a, shape_c = _shape(atual), _shape(cand)
        counts_a, _ = _counts(atual)
        counts_c, _ = _counts(cand)

        # invariantes de seguranca
        moved, narrowed, untouched = [], [], 0
        by_wall_a = {w["id"]: w for w in atual["walls"]}
        for wall in cand["walls"]:
            wa = by_wall_a[wall["id"]]
            for oc, oa in zip(wall.get("openings") or [], wa.get("openings") or []):
                span_a = (oa["t_start_cm"], oa["t_end_cm"])
                span_c = (oc["t_start_cm"], oc["t_end_cm"])
                if span_a == span_c:
                    untouched += 1
                    continue
                ca = (span_a[0] + span_a[1]) / 2.0
                cc = (span_c[0] + span_c[1]) / 2.0
                entry = {"wall": wall["id"], "opening": oc.get("id"),
                         "antes": [round(x, 3) for x in span_a],
                         "depois": [round(x, 3) for x in span_c],
                         "desloc_centro_cm": round(cc - ca, 4)}
                if abs(cc - ca) > 1e-6:
                    moved.append(entry)
                if span_c[0] >= span_a[0] - 1e-9 and span_c[1] <= span_a[1] + 1e-9:
                    narrowed.append(entry)

        codes = sorted(set(counts_a) | set(counts_c))
        deltas = {c: [counts_a.get(c, 0), counts_c.get(c, 0),
                      counts_c.get(c, 0) - counts_a.get(c, 0)]
                  for c in codes if counts_a.get(c, 0) != counts_c.get(c, 0)}
        report[proj] = {
            "forma_atual": shape_a, "forma_candidata": shape_c,
            "forma_identica": shape_a == shape_c,
            "aberturas_intocadas": untouched,
            "aberturas_estreitadas": len(narrowed),
            "aberturas_DESLOCADAS": moved,
            "watch": {c: [counts_a.get(c, 0), counts_c.get(c, 0)] for c in WATCH},
            "deltas": deltas,
            "total_findings": [sum(counts_a.values()), sum(counts_c.values())],
        }
        print("=" * 70)
        print(proj)
        print("  forma identica (paredes/fiadas/blocos/aberturas):", shape_a == shape_c, shape_a)
        print("  aberturas intocadas:", untouched, "| estreitadas:", len(narrowed),
              "| DESLOCADAS:", len(moved))
        for c in WATCH:
            print("   %-34s %5d -> %5d  (%+d)" % (c, counts_a.get(c, 0),
                                                  counts_c.get(c, 0),
                                                  counts_c.get(c, 0) - counts_a.get(c, 0)))
        print("  outros codigos com delta:")
        for c, v in sorted(deltas.items()):
            if c in WATCH:
                continue
            print("   %-34s %5d -> %5d  (%+d)" % (c, v[0], v[1], v[2]))

    with open(os.path.join(HERE, "comparison_report.json"), "w") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    print("\nescrito: comparison_report.json")


if __name__ == "__main__":
    main()
