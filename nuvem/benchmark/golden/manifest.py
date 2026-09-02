# -*- coding: utf-8 -*-
"""Manifesto oficial do GOLDEN BENCHMARK (itens 5, 6 e 8 do pedido).

Um projeto do benchmark (`nuvem/benchmark/projects/<id>/`) pode ter DUAS
coisas independentes, e este modulo nunca deixa as duas se confundirem:

* `reference.json` - uma tentativa de "verdade" (gabarito). A
  confiabilidade dela e' `reference_type`.
* `baseline.json` - a ULTIMA saida do PROPRIO SOLVER, gravada para
  regressao (`runner.py --save-baseline`). Isto NUNCA e' `reference_type`
  golden - por definicao um baseline.json e' `LEGACY_BASELINE`, mesmo
  quando o arquivo carrega `status: "OFICIAL"` (ver
  `projects/torre_easy_lo_r00_tgd/baselines/baseline_real_v1.json`):
  "oficial" ali quer dizer "e' o baseline de regressao valendo agora",
  nao "foi validado por humano".

NAO INVENTAR GOLDEN (item 6): nenhum projeto deste repositorio tem, hoje,
um registro explicito de aprovacao humana (data, nome, ou processo de
sign-off) capturado em `metadata.json`. Por isso NENHUM projeto aqui e'
classificado `GOLDEN_CONFIRMED` - o valor mais alto que a evidencia atual
sustenta e' `HUMAN_REFERENCE_AVAILABLE` (projeto Revit realmente entregue,
com blocos posicionados por uma pessoa, mas sem prova de aprovacao
formal). Ver `docs/GOLDEN_BENCHMARK.md`, secao "Inventario", para o
raciocinio classe a classe.

Este arquivo SO' classifica. Promover um projeto a GOLDEN_CONFIRMED e'
edicao manual do manifest.json, feita por quem tem autoridade para
aprovar - nunca automatica.
"""

import datetime
import json
import os

SCHEMA_VERSION = 1

# --------------------------------------------------------- reference_type
#
# O que `reference.json` (quando existe) representa, em ordem de
# confianca decrescente.

GOLDEN_CONFIRMED = "GOLDEN_CONFIRMED"
HUMAN_REFERENCE_AVAILABLE = "HUMAN_REFERENCE_AVAILABLE"
LEGACY_BASELINE = "LEGACY_BASELINE"
SOLVER_GENERATED_ONLY = "SOLVER_GENERATED_ONLY"
UNKNOWN = "UNKNOWN"

ALL_REFERENCE_TYPES = (
    GOLDEN_CONFIRMED, HUMAN_REFERENCE_AVAILABLE, LEGACY_BASELINE,
    SOLVER_GENERATED_ONLY, UNKNOWN,
)

# Tipos que podem, no futuro, ser promovidos a GOLDEN_CONFIRMED assim que
# houver prova de validacao humana explicita (item 6: "candidate_goldens").
# Continua sendo um HUMAN_REFERENCE_AVAILABLE ate' essa prova existir - a
# lista serve so' para o relatorio destacar quem esta' mais perto.
CANDIDATE_GOLDEN_TYPES = (HUMAN_REFERENCE_AVAILABLE,)

REFERENCE_TYPE_MEANING = {
    GOLDEN_CONFIRMED: (
        "Referencia com PROVA registrada de validacao/aprovacao humana "
        "explicita (data + quem aprovou, ou processo formal descrito em "
        "metadata.json). Pode ser tratada como verdade."
    ),
    HUMAN_REFERENCE_AVAILABLE: (
        "Projeto Revit real, entregue, com blocos posicionados por uma "
        "pessoa (nao pelo solver). Nao ha' registro formal de aprovacao "
        "capturado - e' o melhor candidato a golden, mas AINDA NAO E' um."
    ),
    LEGACY_BASELINE: (
        "Snapshot congelado de uma execucao ANTERIOR DO PROPRIO SOLVER "
        "(ex.: baseline.json gravado por `runner.py --save-baseline`). "
        "Prova reprodutibilidade/determinismo, NUNCA correcao."
    ),
    SOLVER_GENERATED_ONLY: (
        "Nao existe gabarito humano nem baseline de regressao - so' "
        "entrada + o que o solver decidir agora. Usado como fixture de "
        "infraestrutura (ex.: piloto_sintetico_2x2), nao como referencia."
    ),
    UNKNOWN: (
        "Origem nao determinada a partir do que esta' gravado no "
        "repositorio - precisa de investigacao antes de qualquer uso."
    ),
}

# ------------------------------------------------------------ metricas
#
# `available_metrics`: quais blocos de `golden.metrics` este projeto tem
# dado suficiente para calcular. Ver `golden/metrics.py`.
METRIC_GROUPS = (
    "walls", "courses", "blocks", "prism", "junctions", "openings",
    "quality", "performance",
)


def new_entry(project_id, name, reference_type, source, notes="",
             created_at=None, validated_at=None, baseline_commit=None,
             available_metrics=None, has_revit_model=False,
             produced_by_solver=None, approved_by_human=False):
    """Uma linha do manifesto (item 8). `validated_at`/`approved_by_human`
    so' fazem sentido preenchidos quando `reference_type` for
    GOLDEN_CONFIRMED - `validate_entry` reforca isso."""
    return {
        "project_id": project_id,
        "name": name,
        "status": reference_type,
        "reference_type": reference_type,
        "source": source,
        "created_at": created_at or datetime.date.today().isoformat(),
        "validated_at": validated_at,
        "baseline_commit": baseline_commit,
        "has_revit_model": bool(has_revit_model),
        "produced_by_solver": produced_by_solver,
        "approved_by_human": bool(approved_by_human),
        "available_metrics": sorted(set(available_metrics or [])),
        "notes": notes,
    }


def validate_entry(entry):
    """Devolve lista de problemas (vazia = ok). NUNCA levanta excecao
    sozinha - quem usa decide se aborta ou so' avisa (item 6 pede para o
    sistema NUNCA inventar golden, nao para quebrar em runtime)."""
    problems = []
    if entry.get("reference_type") not in ALL_REFERENCE_TYPES:
        problems.append("reference_type desconhecido: {0!r}".format(
            entry.get("reference_type")))
    if entry.get("reference_type") == GOLDEN_CONFIRMED:
        if not entry.get("validated_at"):
            problems.append(
                "GOLDEN_CONFIRMED exige 'validated_at' preenchido - "
                "prova de QUANDO foi validado (item 6)."
            )
        if not entry.get("approved_by_human"):
            problems.append(
                "GOLDEN_CONFIRMED exige 'approved_by_human': true - "
                "sem isso e' HUMAN_REFERENCE_AVAILABLE, no maximo."
            )
    return problems


def make_manifest(entries):
    for entry in entries:
        problems = validate_entry(entry)
        if problems:
            raise ValueError(
                "entrada de manifest invalida para '{0}': {1}".format(
                    entry.get("project_id"), "; ".join(problems)))
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_by": "nuvem/benchmark/golden/manifest.py",
        "principle": (
            "Um baseline.json produzido pelo proprio solver NUNCA e' "
            "tratado como golden automaticamente (ver README desta "
            "secao). Promover um projeto a GOLDEN_CONFIRMED e' acao "
            "manual, com prova de validacao humana registrada."
        ),
        "reference_types": REFERENCE_TYPE_MEANING,
        "projects": list(entries),
    }


def load(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save(manifest, path):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    return path


def by_id(manifest):
    return dict((entry["project_id"], entry) for entry in manifest.get("projects") or [])


def get(manifest, project_id):
    """Entrada de um projeto, ou `None`. NUNCA levanta excecao - um
    projeto sem manifesto e' `UNKNOWN` para quem chama, nao um crash."""
    return by_id(manifest).get(project_id)


def candidates_for_promotion(manifest):
    """Projetos que ainda nao sao golden mas sao os melhores candidatos
    (item 6: 'candidate_goldens') - referencia humana disponivel, sem
    prova de aprovacao formal ainda registrada."""
    return [
        entry for entry in manifest.get("projects") or []
        if entry.get("reference_type") in CANDIDATE_GOLDEN_TYPES
    ]


DEFAULT_MANIFEST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "manifest.json")


def load_default():
    return load(DEFAULT_MANIFEST_PATH)
