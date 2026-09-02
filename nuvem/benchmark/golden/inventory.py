# -*- coding: utf-8 -*-
"""Inventario MECANICO do repositorio (itens 4 e 5 do pedido).

Diferenca deliberada em relacao a `manifest.py`: este modulo so' OLHA o
disco e relata o que existe - nunca decide se algo e' confiavel. A
classificacao (GOLDEN_CONFIRMED/HUMAN_REFERENCE_AVAILABLE/...) e' sempre
humana, gravada a mao em `manifest.json`. `inventory.py` existe para essa
classificacao ter uma lista completa e atualizada para trabalhar em cima -
e para nenhum projeto novo (ou baseline novo) passar despercebido.

Roda sem Revit e sem o solver: so' `os.path`/`json`.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BENCHMARK_DIR = os.path.dirname(HERE)
PROJECTS_DIR = os.path.join(BENCHMARK_DIR, "projects")

# Arquivos que, quando presentes numa pasta de projeto, sao relatados no
# inventario (item 5: "arquivos disponiveis"). Lista fechada de proposito -
# um arquivo novo e' um sinal de que este modulo precisa ser atualizado, e
# nao deve ser inferido por regex frouxo.
KNOWN_FILES = (
    "input.json", "input_real.json", "reference.json", "baseline.json",
    "metadata.json", "result.json", "score.json", "findings.json",
    "comparison.json", "reference_score.json", "reference_findings.json",
    "wall_modeling_snapshot.json", "evaluation_scope.json",
    "scoped_score.json", "scoped_comparison.json", "scope_summary.json",
    "scoped_reference_score.json", "catalog_comparison.json",
    "unassigned_openings_audit.json",
)


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (IOError, OSError, ValueError):
        return None


def _project_ids():
    if not os.path.isdir(PROJECTS_DIR):
        return []
    return sorted(
        name for name in os.listdir(PROJECTS_DIR)
        if os.path.isdir(os.path.join(PROJECTS_DIR, name))
    )


def _legacy_baseline_files(project_dir):
    """Todo arquivo, dentro da pasta do projeto, que e' um SNAPSHOT
    congelado da saida do PROPRIO SOLVER (item 3: nunca golden por
    definicao). Cobre `baseline.json` (score.json congelado) e
    `baselines/*.json` (registros tipo `baseline_real_v1.json`, com
    `solver_decision_fingerprint`)."""
    found = []
    direct = os.path.join(project_dir, "baseline.json")
    if os.path.isfile(direct):
        data = _read_json(direct) or {}
        found.append({
            "path": os.path.relpath(direct, BENCHMARK_DIR),
            "kind": "solver_score_snapshot",
            "source_field": data.get("source"),
            "success_rate": data.get("success_rate"),
            "critical_errors": data.get("critical_errors"),
        })
    extra_dir = os.path.join(project_dir, "baselines")
    if os.path.isdir(extra_dir):
        for name in sorted(os.listdir(extra_dir)):
            if not name.endswith(".json"):
                continue
            path = os.path.join(extra_dir, name)
            data = _read_json(path) or {}
            found.append({
                "path": os.path.relpath(path, BENCHMARK_DIR),
                "kind": "solver_decision_record",
                "status_field": data.get("status"),
                "frozen_at": data.get("frozen_at"),
                "solver_decision_fingerprint": data.get("solver_decision_fingerprint"),
            })
    return found


def scan_project(project_id):
    """Fatos brutos de UM projeto (item 5): nome, arquivos, datas do
    baseline, se veio do solver, sem nenhum julgamento de confiabilidade."""
    project_dir = os.path.join(PROJECTS_DIR, project_id)
    files_present = sorted(
        name for name in KNOWN_FILES
        if os.path.isfile(os.path.join(project_dir, name))
    )
    metadata = _read_json(os.path.join(project_dir, "metadata.json")) or {}
    input_project = _read_json(os.path.join(project_dir, "input.json"))
    reference_project = _read_json(os.path.join(project_dir, "reference.json"))

    return {
        "project_id": project_id,
        "files_present": files_present,
        "has_input": "input.json" in files_present,
        "has_input_real": "input_real.json" in files_present,
        "has_reference": "reference.json" in files_present,
        "has_metadata": "metadata.json" in files_present,
        "input_walls": len((input_project or {}).get("walls") or []) if input_project else None,
        "reference_walls": len((reference_project or {}).get("walls") or []) if reference_project else None,
        "reference_confiabilidade": metadata.get("reference_confiabilidade"),
        "origem": metadata.get("origem"),
        "extraido_em": metadata.get("extraido_em"),
        "legacy_baselines": _legacy_baseline_files(project_dir),
    }


def scan_all():
    return [scan_project(pid) for pid in _project_ids()]


def build_inventory():
    projects = scan_all()
    return {
        "schema_version": 1,
        "note": (
            "Inventario MECANICO (so' o que existe em disco). A "
            "classificacao de confiabilidade fica em manifest.json - "
            "regenerar este arquivo com "
            "`python -m nuvem.benchmark.golden.inventory` nunca muda "
            "aquela classificacao sozinho."
        ),
        "projects_dir": os.path.relpath(PROJECTS_DIR, BENCHMARK_DIR),
        "projects": projects,
    }


def save(inventory, path):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(inventory, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    return path


DEFAULT_INVENTORY_PATH = os.path.join(HERE, "inventory.json")


def main():
    inventory = build_inventory()
    save(inventory, DEFAULT_INVENTORY_PATH)
    print("inventario gravado em {0} ({1} projeto(s))".format(
        DEFAULT_INVENTORY_PATH, len(inventory["projects"])))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
