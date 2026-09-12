# -*- coding: utf-8 -*-
"""Constroi uma REGUA VERSIONADA do benchmark (2026-09-12, missao pre-Beta 2).

Por que existe: a regua historica (V1, raiz de `projects/<id>/`) foi gerada
pela FASE A de 2026-08-31 (TGD: 167 paredes / 272 nos / 82 aberturas
atribuidas). O motor atual nao produz mais essa topologia (145 / 234 / 91),
entao o baseline V1 compara o solver com um problema que a producao ja nao
gera. Este script regenera a FASE A com o motor ATUAL pelo pipeline real
ja existente - `runner.run_wall_modeling_only` -> `wall_modeling_bridge`
-> `wall_modeling_snapshot` -> `input_from_snapshot` - roda o solver, grava
o baseline da versao e um `manifest.json` com a proveniencia completa:

    <projeto>/<versao>/wall_modeling_snapshot.json   FASE A do motor atual
    <projeto>/<versao>/input.json                    problema para o solver
    <projeto>/<versao>/baseline.json + score.json    medicao honesta
    <projeto>/<versao>/manifest.json                 SHAs, contagens,
                                                     fingerprints, identidade
                                                     FISICA (chaves, nunca so'
                                                     W0xx), debito registrado

NUNCA toca nos arquivos da raiz (V1 = HISTORICAL / TOPOLOGIA ANTIGA). Projeto
sem `input_real.json` (TP1: input reconstruido do gabarito) nao tem FASE A
para regenerar - o input da raiz e' reutilizado e isso fica gravado no
manifest (`input_source`), nunca implicito.

O baseline gravado aqui MEDE o solver; nao e' ajustado para o solver passar.

Uso:
    py -3 nuvem/benchmark/tools/build_version_manifest.py --version v2 \\
        --project torre_easy_lo_r00_tgd --project torre_easy_lo_r00_tp1 \\
        --base-main-sha <sha> --head-sha <sha>
"""

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys

if __package__ in (None, ""):  # rodando como script solto
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
    __package__ = "benchmark.tools"

from .. import runner as benchmark_runner  # noqa: E402
from .. import model  # noqa: E402
from ..golden import fingerprint as fingerprint_module  # noqa: E402

MANIFEST_SCHEMA_VERSION = 1
CLASSIFICATION_CURRENT = "CURRENT_ENGINE_TOPOLOGY"
CLASSIFICATION_HISTORICAL_V1 = "HISTORICAL / TOPOLOGIA ANTIGA (raiz do projeto, FASE A de 2026-08-31)"

IDENTITY_DEBT = (
    "Migracao completa de identidade (#28) NAO feita nesta regua: validadores, "
    "scoring.per_wall, evaluation_scope e comparator continuam indexados por "
    "W0xx (= indice da parede + 1, dependente da ordem de `walls_to_create`). "
    "Esta versao grava, para cada parede, a chave FISICA (`key` = "
    "model.wall_stable_key: endpoints canonicos + espessura), os endpoints "
    "canonicos, a espessura, as aberturas associadas (element_id de origem) "
    "e, para cada no', o ponto e as chaves das paredes participantes - o "
    "suficiente para cruzar versoes sem depender do indice. Debito aberto: "
    "fazer validadores/scoring reportarem por `key`."
)


def _sha256_of_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        digest.update(handle.read())
    return digest.hexdigest()


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))


def _git(*args):
    try:
        out = subprocess.check_output(["git"] + list(args), cwd=_repo_root(),
                                      stderr=subprocess.STDOUT)
        return out.decode("utf-8", "replace").strip()
    except Exception:  # noqa: BLE001 - git ausente/sem repo: nao e' erro do benchmark
        return None


def _engine_hashes():
    root = _repo_root()
    files = {
        "wall_modeling.py": os.path.join(root, "nuvem", "core", "wall_modeling.py"),
        "engine/wall_stepper.py": os.path.join(root, "nuvem", "core", "engine", "wall_stepper.py"),
        "engine/wall_pairing.py": os.path.join(root, "nuvem", "core", "engine", "wall_pairing.py"),
        "engine/geometry.py": os.path.join(root, "nuvem", "core", "engine", "geometry.py"),
    }
    return dict((name, _sha256_of_file(path)) for name, path in files.items()
                if os.path.isfile(path))


def _node_kind_counts(nodes):
    counts = {}
    for node in nodes:
        kind = node.get("kind") or "?"
        counts[kind] = counts.get(kind, 0) + 1
    return dict(sorted(counts.items()))


def _identity_from_snapshot(snapshot):
    """Identidade FISICA de paredes e nos - chaves geometricas, nunca so' o
    indice (ver IDENTITY_DEBT)."""
    walls = snapshot.get("walls") or []
    keys = [w["key"] for w in walls]
    openings_by_index = {}
    for entry in snapshot.get("openings_per_wall") or []:
        openings_by_index.setdefault(entry["wall_index"], []).append({
            "t_start_cm": entry["t_start_cm"], "t_end_cm": entry["t_end_cm"],
            "sill_cm": entry["sill_cm"], "head_cm": entry["head_cm"],
            "source_opening_key": entry.get("source_opening_key"),
        })
    wall_rows = []
    for index, wall in enumerate(walls):
        a, b = model.canonical_segment(wall["start_cm"], wall["end_cm"])
        wall_rows.append({
            "key": wall["key"],
            "index_alias": "W{0:03d}".format(index + 1),
            "canonical_start_cm": list(a), "canonical_end_cm": list(b),
            "thickness_cm": wall["thickness_cm"], "length_cm": wall["length_cm"],
            "openings": openings_by_index.get(index, []),
        })
    node_rows = []
    for node in snapshot.get("nodes") or []:
        arms = node.get("arms") or []
        wall_keys = sorted(set(keys[w] for w, _e in arms if w < len(keys)))
        node_rows.append({
            "point_cm": node.get("point_cm"), "kind": node.get("kind"),
            "wall_keys": wall_keys,
        })
    node_rows.sort(key=lambda n: (n["point_cm"] or [0, 0], n["kind"]))
    return wall_rows, node_rows


def _identity_from_input(input_project):
    wall_rows = []
    for index, wall in enumerate(input_project.get("walls") or []):
        a, b = model.canonical_segment(wall["start_cm"], wall["end_cm"])
        wall_rows.append({
            "key": wall.get("key") or model.wall_stable_key(wall["start_cm"], wall["end_cm"], wall["thickness_cm"]),
            "index_alias": wall.get("id") or "W{0:03d}".format(index + 1),
            "canonical_start_cm": list(a), "canonical_end_cm": list(b),
            "thickness_cm": wall["thickness_cm"], "length_cm": wall.get("length_cm"),
            "openings": [{"t_start_cm": o.get("t_start_cm"), "t_end_cm": o.get("t_end_cm"),
                          "sill_cm": o.get("sill_cm"), "head_cm": o.get("head_cm"),
                          "source_opening_key": o.get("source_element_id")}
                         for o in wall.get("openings") or []],
        })
    return wall_rows


def build_version(project_id, version, base_main_sha=None, head_sha=None,
                  save_baseline=True, note=None):
    paths = benchmark_runner.project_paths(project_id, version)
    root_paths = benchmark_runner.project_paths(project_id)
    if not os.path.isdir(paths["generated_dir"]):
        os.makedirs(paths["generated_dir"])

    fase_a = None
    snapshot = None
    if os.path.isfile(root_paths["input_real"]):
        snapshot = benchmark_runner.run_wall_modeling_only(project_id, write_files=True, version=version)
        diag = snapshot.get("diagnostics") or {}
        fase_a = {
            "regenerated": True,
            "pipeline": "input_real.json -> runner.run_wall_modeling_only -> wall_modeling_bridge "
                        "-> extract/wall_modeling_snapshot -> extract/input_from_snapshot",
            "lines_in_layer": diag.get("lines_in_layer"),
            "lines_after_merge": diag.get("lines_after_merge"),
            "duplicates_removed_count": diag.get("duplicates_removed_count"),
            "unused_lines": len(snapshot.get("unused_lines") or []),
            "walls": len(snapshot.get("walls") or []),
            "nodes": len(snapshot.get("nodes") or []),
            "nodes_by_kind": _node_kind_counts(snapshot.get("nodes") or []),
            "intersections": sum(1 for n in snapshot.get("nodes") or []
                                 if n.get("kind") in ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION", "AMBIGUOUS")),
            "end_to_node": len(snapshot.get("end_to_node") or []),
            "openings_assigned": len(snapshot.get("openings_per_wall") or []),
            "openings_unassigned": len((diag.get("openings") or {}).get("unassigned_openings") or []),
            "wall_modeling_engine_sha256": snapshot.get("wall_modeling_engine_sha256"),
            "settings": snapshot.get("settings"),
        }
        input_source = os.path.relpath(paths["input"], benchmark_runner.PROJECTS_DIR)
    else:
        fase_a = {
            "regenerated": False,
            "reason": "projeto sem input_real.json - o input e' reconstruido do gabarito "
                      "(extract/reconstruct.py); nao ha' FASE A para regenerar. Topologia "
                      "IDENTICA a' V1 (mesmo input.json da raiz); so' a medicao e' desta versao.",
        }
        input_source = os.path.relpath(root_paths["input"], benchmark_runner.PROJECTS_DIR)

    outcome = benchmark_runner.run_project(project_id, save_baseline=save_baseline,
                                           write_files=True, version=version)
    score = outcome["score"]
    result = outcome["result"]
    input_project = benchmark_runner._read_json(paths["input"]) or benchmark_runner._read_json(root_paths["input"])

    if snapshot is not None:
        wall_rows, node_rows = _identity_from_snapshot(snapshot)
    else:
        wall_rows, node_rows = _identity_from_input(input_project), None

    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "kind": "BENCHMARK_VERSION_MANIFEST",
        "generated_by": "nuvem/benchmark/tools/build_version_manifest.py",
        "project_id": project_id,
        "version": version,
        "classification": CLASSIFICATION_CURRENT,
        "v1_classification": CLASSIFICATION_HISTORICAL_V1,
        "created_at": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
        "note": note,
        "git": {
            "base_main_sha": base_main_sha,
            "head_sha": head_sha or _git("rev-parse", "HEAD"),
            "head_tree": _git("rev-parse", "HEAD^{tree}"),
            "worktree_dirty": bool(_git("status", "--porcelain", "--", "nuvem/core")) if _git("rev-parse", "HEAD") else None,
        },
        "engine_sha256": _engine_hashes(),
        "input_source": input_source,
        "input_sha256": _sha256_of_file(paths["input"]) if os.path.isfile(paths["input"]) else _sha256_of_file(root_paths["input"]),
        "input_fingerprint": fingerprint_module.canonical_fingerprint(input_project),
        "fase_a": fase_a,
        "solver": {
            "catalog_codes": sorted((input_project.get("catalog") or {}).keys()),
            "num_courses": (input_project.get("settings") or {}).get("num_courses"),
            "walls": score.get("walls"), "blocks": score.get("blocks"),
        },
        "result_fingerprint": fingerprint_module.canonical_fingerprint(result),
        "result_component_fingerprints": fingerprint_module.component_fingerprints(result),
        "baseline": {
            "path": os.path.relpath(paths["baseline"], benchmark_runner.PROJECTS_DIR),
            "success_rate": score.get("success_rate"),
            "critical_errors": score.get("critical_errors"),
            "critical_by_code": score.get("critical_by_code"),
            "findings_level_1": score.get("findings_level_1"),
            "findings_level_2": score.get("findings_level_2"),
            "categories": dict((cat.get("category"), {"fail": cat.get("fail"), "findings": cat.get("findings"),
                                                      "success_rate": cat.get("success_rate")})
                               for cat in (score.get("categories") or [])
                               if isinstance(cat, dict)),
        },
        "identity": {
            "principle": "chave FISICA primeiro (key/endpoints canonicos/espessura/aberturas/nos); "
                         "W0xx e' so' alias de indice desta rodada",
            "walls": wall_rows,
            "nodes": node_rows,
            "debt": IDENTITY_DEBT,
        },
    }
    manifest_path = os.path.join(paths["generated_dir"], "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=1, sort_keys=False)
    return manifest, manifest_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--version", required=True, dest="version")
    parser.add_argument("--project", action="append", required=True)
    parser.add_argument("--base-main-sha", default=None)
    parser.add_argument("--head-sha", default=None)
    parser.add_argument("--note", default=None)
    parser.add_argument("--no-save-baseline", action="store_true")
    args = parser.parse_args(argv)
    for project_id in args.project:
        manifest, path = build_version(project_id, args.version, args.base_main_sha, args.head_sha,
                                       save_baseline=not args.no_save_baseline, note=args.note)
        b = manifest["baseline"]
        print("{0} [{1}]: {2:.1f}% | criticos {3} | {4} -> {5}".format(
            project_id, args.version, 100.0 * (b["success_rate"] or 0.0), b["critical_errors"],
            json.dumps(b["critical_by_code"], sort_keys=True), path))
        print("   fingerprint {0}".format(manifest["result_fingerprint"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
