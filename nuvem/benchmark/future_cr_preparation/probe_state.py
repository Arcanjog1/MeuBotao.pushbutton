"""Driver de revisao independente C04. NAO escreve nada no repo."""
import hashlib, json, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from nuvem.benchmark import runner, solver_bridge  # noqa
from nuvem.benchmark.extract import from_solver  # noqa


def block_rows(project):
    """Toda peca com identidade FISICA absoluta e tambem local a parede."""
    rows = []
    for wall in project.get("walls") or []:
        wid = wall.get("id")
        for row in wall.get("rows") or []:
            ri = row.get("row")
            for b in row.get("blocks") or []:
                c = b.get("center_cm") or [None, None]
                rows.append([
                    wid, ri, b.get("code"),
                    round(float(b.get("t_start_cm") or 0.0), 3),
                    round(float(b.get("t_end_cm") or 0.0), 3),
                    round(float(c[0]), 3) if c[0] is not None else None,
                    round(float(c[1]), 3) if c[1] is not None else None,
                    round(float(b.get("z_cm") or 0.0), 3),
                    b.get("role"),
                ])
    rows.sort(key=lambda r: [str(x) for x in r])
    return rows


def physical_rows(rows):
    """So' a geometria absoluta - independente de indice/ordem de parede."""
    out = sorted({(r[2], r[5], r[6], r[7]) for r in rows})
    return out


def fp(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
                                     default=str).encode()).hexdigest()


def ident(f):
    return json.dumps({
        "code": f.get("code"), "wall": f.get("wall"), "row": f.get("row"),
        "detail": f.get("detail"),
    }, sort_keys=True, ensure_ascii=False)


def main():
    project_id, out_path = sys.argv[1], sys.argv[2]
    paths = runner.project_paths(project_id)
    with open(paths["input"], encoding="utf-8") as fh:
        input_project = json.load(fh)

    (solve_result, walls_to_create, nodes, openings_per_wall, catalog,
     base_z_ft, num_courses, notes) = solver_bridge.run_solver(input_project)
    result_project = from_solver.project_from_solver(
        project_id, solve_result, walls_to_create, nodes, openings_per_wall,
        catalog, base_z_ft, num_courses, metadata={"generated_at": "PROBE"})

    reference = None
    if os.path.exists(paths["reference"]):
        with open(paths["reference"], encoding="utf-8") as fh:
            reference = json.load(fh)
    findings, score, comparison = runner.evaluate_project(result_project, reference)

    rows = block_rows(result_project)
    phys = physical_rows(rows)

    counts, idents = {}, {}
    for f in findings:
        c = f.get("code")
        counts[c] = counts.get(c, 0) + 1
        idents.setdefault(c, []).append(ident(f))
    for c in idents:
        idents[c].sort()

    payload = {
        "project_id": project_id,
        "n_blocks": len(rows),
        "fingerprint_local": fp(rows),
        "fingerprint_physical": fp(phys),
        "counts_by_code": counts,
        "finding_identities": idents,
        "score_categories": score.get("categories"),
        "score_critical": score.get("critical"),
        "score_summary": {k: v for k, v in score.items()
                          if not isinstance(v, (list, dict))},
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True, ensure_ascii=False)
    with open(out_path.replace(".json", ".blocks.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False)
    print("OK", project_id, "blocks=", len(rows),
          "fpL=", payload["fingerprint_local"][:12],
          "fpP=", payload["fingerprint_physical"][:12])


if __name__ == "__main__":
    main()
