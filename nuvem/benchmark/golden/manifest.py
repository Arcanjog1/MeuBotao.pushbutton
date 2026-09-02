# -*- coding: utf-8 -*-
"""Catalogo do CORPUS DE REFERENCIA (CR-BLOCK-REFERENCE-CORPUS).

Evolucao do manifesto do CR-BLOCK-GOLDEN-BENCHMARK anterior. A mudanca de
estrategia (registrada em `docs/REFERENCE_CORPUS.md`):

    ANTES: so' entrava no benchmark quem fosse "golden o suficiente".
    AGORA: TODO projeto com dado suficiente participa - GOLDEN_CONFIRMED
    continua existindo, mas so' como o nivel MAIS ALTO de confianca, nunca
    como requisito de entrada.

DOIS EIXOS (item 10 do pedido), independentes:

* `reference_kind` - O QUE produziu o dado: `HUMAN` (pessoa posicionou o
  bloco), `SOLVER` (o proprio solver, nalguma execucao passada), `SYNTHETIC`
  (gerado proceduralmente para teste), `ANALYSIS_ONLY` (so' existe resumo/
  censo, sem geometria reproduzivel), `UNKNOWN`.
* `confidence` - QUANTO confiar nisso como VERDADE de correcao:
  `NONE` -> `LOW` -> `MEDIUM` -> `HIGH` -> `GOLDEN`, nesta ordem.

Um projeto `HUMAN` sem verificacao formal e' `confidence=MEDIUM`
("HUMAN_REFERENCE_AVAILABLE" no vocabulario antigo). O mesmo projeto,
depois de alguem revisar a extracao contra a fonte, vira `HIGH`
("HUMAN_VERIFIED"). So' com processo de aprovacao formal registrado
(`validated_at` + `approved_by_human`) ele chega a `GOLDEN`
("GOLDEN_CONFIRMED") - o TETO da escala, nunca o piso de entrada.

COMPATIBILIDADE (item 16/48): o enum antigo (`reference_type`:
GOLDEN_CONFIRMED/HUMAN_REFERENCE_AVAILABLE/LEGACY_BASELINE/
SOLVER_GENERATED_ONLY/UNKNOWN, mais o novo ANALYSIS_ONLY_REFERENCE) e' MANTIDO
como rotulo legado - `new_entry` continua aceitando so' `reference_type`
como antes, e agora DERIVA `reference_kind`/`confidence` sozinho quando eles
nao sao passados explicitamente (`LEGACY_TO_AXES`). Nenhum import existente
de `manifest.GOLDEN_CONFIRMED`/`manifest.HUMAN_REFERENCE_AVAILABLE`/etc
quebra.

Um `baseline.json` (saida do PROPRIO SOLVER) continua sendo sempre
`reference_kind=SOLVER, confidence=LOW` - prova reprodutibilidade/
determinismo, nunca correcao. Isso nao mudou.
"""

import datetime
import json
import os

SCHEMA_VERSION = 2

# --------------------------------------------------------- reference_type
#
# Rotulo LEGADO (CR-BLOCK-GOLDEN-BENCHMARK). Mantido por compatibilidade -
# ver `LEGACY_TO_AXES` para a correspondencia com o par (kind, confidence).

GOLDEN_CONFIRMED = "GOLDEN_CONFIRMED"
HUMAN_REFERENCE_AVAILABLE = "HUMAN_REFERENCE_AVAILABLE"
LEGACY_BASELINE = "LEGACY_BASELINE"
SOLVER_GENERATED_ONLY = "SOLVER_GENERATED_ONLY"
ANALYSIS_ONLY_REFERENCE = "ANALYSIS_ONLY_REFERENCE"
UNKNOWN = "UNKNOWN"

ALL_REFERENCE_TYPES = (
    GOLDEN_CONFIRMED, HUMAN_REFERENCE_AVAILABLE, LEGACY_BASELINE,
    SOLVER_GENERATED_ONLY, ANALYSIS_ONLY_REFERENCE, UNKNOWN,
)

# Tipos que podem, no futuro, ser promovidos a GOLDEN_CONFIRMED assim que
# houver prova de validacao humana explicita (item 6 do CR anterior:
# "candidate_goldens"). So' informativo para o relatorio.
CANDIDATE_GOLDEN_TYPES = (HUMAN_REFERENCE_AVAILABLE,)

REFERENCE_TYPE_MEANING = {
    GOLDEN_CONFIRMED: (
        "Referencia com PROVA registrada de validacao/aprovacao humana "
        "explicita (data + quem aprovou, ou processo formal descrito em "
        "metadata.json). O TETO da escala de confianca - nunca requisito "
        "de entrada no corpus."
    ),
    HUMAN_REFERENCE_AVAILABLE: (
        "Projeto Revit real, entregue, com blocos posicionados por uma "
        "pessoa (nao pelo solver). Nao ha' registro formal de aprovacao "
        "capturado - e' candidato a GOLDEN, mas AINDA NAO E' um."
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
    ANALYSIS_ONLY_REFERENCE: (
        "So' existe resumo/censo/metrica agregada (ou uma imagem, ou um "
        "relatorio narrativo) - SEM geometria reproduzivel (sem paredes, "
        "sem blocos por posicao). Nao pode ser rodado nem comparado "
        "estruturalmente; serve so' como registro do que precisa ser "
        "extraido para virar um projeto de verdade (`missing_requirements`)."
    ),
    UNKNOWN: (
        "Origem nao determinada a partir do que esta' gravado no "
        "repositorio - precisa de investigacao antes de qualquer uso."
    ),
}

# ------------------------------------------------------------- eixo 1: kind
KIND_HUMAN = "HUMAN"
KIND_SOLVER = "SOLVER"
KIND_SYNTHETIC = "SYNTHETIC"
KIND_ANALYSIS_ONLY = "ANALYSIS_ONLY"
KIND_UNKNOWN = "UNKNOWN"

ALL_REFERENCE_KINDS = (KIND_HUMAN, KIND_SOLVER, KIND_SYNTHETIC,
                       KIND_ANALYSIS_ONLY, KIND_UNKNOWN)

# -------------------------------------------------------- eixo 2: confidence
CONFIDENCE_NONE = "NONE"
CONFIDENCE_LOW = "LOW"
CONFIDENCE_MEDIUM = "MEDIUM"
CONFIDENCE_HIGH = "HIGH"
CONFIDENCE_GOLDEN = "GOLDEN"

# ORDEM importa (usada por `filter_by_confidence`/promocao) - do menor pro
# maior grau de confianca como VERDADE de correcao.
CONFIDENCE_ORDER = (CONFIDENCE_NONE, CONFIDENCE_LOW, CONFIDENCE_MEDIUM,
                    CONFIDENCE_HIGH, CONFIDENCE_GOLDEN)
CONFIDENCE_RANK = dict((level, index) for index, level in enumerate(CONFIDENCE_ORDER))

CONFIDENCE_MEANING = {
    CONFIDENCE_NONE: "sem sinal de correcao (sintetico sem gabarito, analysis-only, origem desconhecida)",
    CONFIDENCE_LOW: "reproduzivel, mas a 'referencia' e' a saida passada do PROPRIO solver (prova determinismo, nao correcao)",
    CONFIDENCE_MEDIUM: "referencia humana disponivel, sem verificacao formal da extracao",
    CONFIDENCE_HIGH: "referencia humana com a EXTRACAO verificada por alguem com autoridade de dominio (HUMAN_VERIFIED)",
    CONFIDENCE_GOLDEN: "validacao/aprovacao humana formal e registrada (GOLDEN_CONFIRMED) - o teto",
}

# Correspondencia do rotulo LEGADO -> par (kind, confidence). Usada por
# `new_entry` quando `reference_kind`/`confidence` nao sao passados - e' o
# que mantem toda chamada antiga funcionando sem mudanca nenhuma.
LEGACY_TO_AXES = {
    GOLDEN_CONFIRMED: (KIND_HUMAN, CONFIDENCE_GOLDEN),
    HUMAN_REFERENCE_AVAILABLE: (KIND_HUMAN, CONFIDENCE_MEDIUM),
    LEGACY_BASELINE: (KIND_SOLVER, CONFIDENCE_LOW),
    SOLVER_GENERATED_ONLY: (KIND_SOLVER, CONFIDENCE_NONE),
    ANALYSIS_ONLY_REFERENCE: (KIND_ANALYSIS_ONLY, CONFIDENCE_NONE),
    UNKNOWN: (KIND_UNKNOWN, CONFIDENCE_NONE),
}

# ------------------------------------------------------------ promocao
#
# Item 38: regras EXPLICITAS de promocao entre niveis de confianca. Nunca
# automatica - `promote()` sempre exige `evidence` (texto) e quem chamou e'
# sempre humano/uma decisao humana explicita, nunca o scan mecanico
# (`inventory.py` nunca chama `promote`).
PROMOTION_REQUIREMENTS = {
    (CONFIDENCE_MEDIUM, CONFIDENCE_HIGH): (
        "'verified_at' preenchido (e 'verified_by' recomendado): alguem "
        "com autoridade de dominio revisou a extracao/reconstrucao contra "
        "a fonte (o .rvt, ou o desenho) e confirma que ela e' fiel."
    ),
    (CONFIDENCE_HIGH, CONFIDENCE_GOLDEN): (
        "'validated_at' preenchido E 'approved_by_human': true - processo "
        "formal de aprovacao, registrado (quem, quando, o que foi aprovado)."
    ),
    (CONFIDENCE_LOW, CONFIDENCE_MEDIUM): (
        "o projeto passa a ter reference_kind=HUMAN com dado geometrico "
        "de verdade (nao so' saida do solver) - normalmente isso e' uma "
        "reextracao, nao uma 'promocao' no sentido estrito."
    ),
}


class PromotionError(ValueError):
    pass


def promote(entry, to_confidence, evidence, at=None, by=None, extra_fields=None):
    """Promove `entry` (dict, NAO MODIFICADO) para `to_confidence` -
    devolve uma COPIA nova. Item 38: nunca automatico, sempre com
    `evidence` (texto livre, obrigatorio) descrevendo o que foi checado.

    Recusa (levanta `PromotionError`, nunca promove parcialmente):
    * degradar confianca (`to_confidence` <= confianca atual);
    * pular o requisito do proprio degrau (`PROMOTION_REQUIREMENTS`) sem
      os campos exigidos ja' preenchidos em `entry`/`extra_fields`.
    """
    current = entry.get("confidence")
    if current not in CONFIDENCE_RANK or to_confidence not in CONFIDENCE_RANK:
        raise PromotionError("confidence desconhecido: {0!r} -> {1!r}".format(
            current, to_confidence))
    if CONFIDENCE_RANK[to_confidence] <= CONFIDENCE_RANK[current]:
        raise PromotionError(
            "promocao tem que SUBIR de nivel: {0} -> {1} nao sobe nada".format(
                current, to_confidence))
    if not evidence:
        raise PromotionError(
            "promocao sem 'evidence' (o que foi checado, por quem) nunca "
            "e' aceita - item 38 exige requisito minimo, nao promocao as cegas."
        )

    new_entry_dict = dict(entry)
    new_entry_dict.update(extra_fields or {})
    new_entry_dict["confidence"] = to_confidence
    when = at or datetime.date.today().isoformat()

    requirement = PROMOTION_REQUIREMENTS.get((current, to_confidence))
    problems = []
    if to_confidence == CONFIDENCE_HIGH and not new_entry_dict.get("verified_at"):
        new_entry_dict["verified_at"] = when
        new_entry_dict["verified_by"] = by
        new_entry_dict["verification_notes"] = evidence
    if to_confidence == CONFIDENCE_GOLDEN:
        if not new_entry_dict.get("approved_by_human"):
            problems.append(
                "promocao para GOLDEN exige 'approved_by_human': true "
                "(passe extra_fields={'approved_by_human': True, ...})."
            )
        if not new_entry_dict.get("validated_at"):
            new_entry_dict["validated_at"] = when

    history = list(entry.get("promotion_history") or [])
    history.append({
        "from_confidence": current,
        "to_confidence": to_confidence,
        "at": when,
        "by": by,
        "evidence": evidence,
        "requirement": requirement,
    })
    new_entry_dict["promotion_history"] = history

    problems.extend(validate_entry(new_entry_dict))
    if problems:
        raise PromotionError("; ".join(problems))
    return new_entry_dict


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
             produced_by_solver=None, approved_by_human=False,
             reference_kind=None, confidence=None, reproducible=None,
             capabilities=None, missing_requirements=None,
             verified_at=None, verified_by=None, verification_notes=None,
             project_version=None, reference_version=None,
             source_commit=None, extraction_version=None,
             promotion_history=None):
    """Uma linha do catalogo (item 8/15). `reference_type` continua
    obrigatorio (rotulo legado, sempre presente) - `reference_kind`/
    `confidence` sao OPCIONAIS: quando omitidos, saem de `LEGACY_TO_AXES`.
    Isso mantem toda chamada do CR-BLOCK-GOLDEN-BENCHMARK anterior
    funcionando sem editar uma linha."""
    if reference_kind is None or confidence is None:
        derived_kind, derived_confidence = LEGACY_TO_AXES.get(
            reference_type, (KIND_UNKNOWN, CONFIDENCE_NONE))
        reference_kind = reference_kind or derived_kind
        confidence = confidence or derived_confidence
    if reproducible is None:
        reproducible = reference_kind != KIND_ANALYSIS_ONLY
    return {
        "project_id": project_id,
        "name": name,
        # "status" e' o mesmo valor de "reference_type" - mantido pelo
        # nome antigo por compatibilidade com quem ja' le' o manifesto.
        "status": reference_type,
        "reference_type": reference_type,
        "reference_kind": reference_kind,
        "confidence": confidence,
        "reproducible": bool(reproducible),
        "source": source,
        "created_at": created_at or datetime.date.today().isoformat(),
        "validated_at": validated_at,
        "verified_at": verified_at,
        "verified_by": verified_by,
        "verification_notes": verification_notes,
        "baseline_commit": baseline_commit,
        "project_version": project_version,
        "reference_version": reference_version,
        "source_commit": source_commit,
        "extraction_version": extraction_version,
        "has_revit_model": bool(has_revit_model),
        "produced_by_solver": produced_by_solver,
        "approved_by_human": bool(approved_by_human),
        "available_metrics": sorted(set(available_metrics or [])),
        "capabilities": sorted(set(capabilities or [])),
        "missing_requirements": list(missing_requirements or []),
        "promotion_history": list(promotion_history or []),
        "notes": notes,
    }


def validate_entry(entry):
    """Devolve lista de problemas (vazia = ok). NUNCA levanta excecao
    sozinha - quem usa decide se aborta ou so' avisa."""
    problems = []
    reference_type = entry.get("reference_type")
    reference_kind = entry.get("reference_kind")
    confidence = entry.get("confidence")

    if reference_type not in ALL_REFERENCE_TYPES:
        problems.append("reference_type desconhecido: {0!r}".format(reference_type))
    if reference_kind not in ALL_REFERENCE_KINDS:
        problems.append("reference_kind desconhecido: {0!r}".format(reference_kind))
    if confidence not in CONFIDENCE_RANK:
        problems.append("confidence desconhecido: {0!r}".format(confidence))

    is_golden = (reference_type == GOLDEN_CONFIRMED or confidence == CONFIDENCE_GOLDEN)
    if is_golden:
        if not entry.get("validated_at"):
            problems.append(
                "GOLDEN (reference_type=GOLDEN_CONFIRMED ou confidence=GOLDEN) "
                "exige 'validated_at' preenchido - prova de QUANDO foi validado."
            )
        if not entry.get("approved_by_human"):
            problems.append(
                "GOLDEN exige 'approved_by_human': true - sem isso e' no "
                "maximo HUMAN_VERIFIED/HIGH."
            )
        if reference_kind not in (None, KIND_HUMAN):
            problems.append(
                "GOLDEN so' faz sentido com reference_kind=HUMAN (verdade "
                "vem de gente, nao do solver nem de dado sintetico)."
            )

    if confidence == CONFIDENCE_HIGH and not entry.get("verified_at"):
        problems.append(
            "confidence=HIGH (HUMAN_VERIFIED) exige 'verified_at' - "
            "prova de que alguem revisou a extracao (item 38)."
        )

    if reference_kind == KIND_ANALYSIS_ONLY:
        if entry.get("reproducible"):
            problems.append(
                "reference_kind=ANALYSIS_ONLY nunca e' 'reproducible': true "
                "- por definicao nao ha' dado executavel (item 7)."
            )
        if confidence != CONFIDENCE_NONE:
            problems.append(
                "reference_kind=ANALYSIS_ONLY so' pode ter confidence=NONE "
                "- nao ha' geometria para sustentar nenhum grau de confianca "
                "de correcao."
            )
        if not entry.get("missing_requirements"):
            problems.append(
                "reference_kind=ANALYSIS_ONLY exige 'missing_requirements' "
                "preenchido - o que falta para virar um projeto de verdade "
                "(item 7/36)."
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
        "kind": "REFERENCE_CORPUS_CATALOG",
        "principle": (
            "TODO projeto com dado suficiente participa do benchmark - "
            "GOLDEN_CONFIRMED/confidence=GOLDEN e' so' o NIVEL MAIS ALTO de "
            "confianca, nunca requisito de entrada. Um baseline.json "
            "produzido pelo proprio solver NUNCA e' tratado como golden "
            "automaticamente. Promover a confidence mais alta e' acao "
            "manual (`promote()`), com evidencia registrada."
        ),
        "reference_types": REFERENCE_TYPE_MEANING,
        "reference_kinds": dict((k, k) for k in ALL_REFERENCE_KINDS),
        "confidence_levels": CONFIDENCE_MEANING,
        "confidence_order": list(CONFIDENCE_ORDER),
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
    """Projetos que ainda nao sao golden mas sao os melhores candidatos -
    referencia humana disponivel (confidence MEDIUM ou HIGH), sem prova de
    aprovacao formal ainda registrada."""
    return [
        entry for entry in manifest.get("projects") or []
        if entry.get("reference_kind") == KIND_HUMAN
        and entry.get("confidence") in (CONFIDENCE_MEDIUM, CONFIDENCE_HIGH)
    ]


def filter_by_reference_kind(manifest, kind):
    return [e for e in manifest.get("projects") or [] if e.get("reference_kind") == kind]


def filter_by_confidence(manifest, minimum=None, exact=None):
    """`minimum`: confidence minima (inclusive, na ordem de `CONFIDENCE_ORDER`).
    `exact`: exatamente este nivel. Um dos dois, nunca os dois."""
    entries = manifest.get("projects") or []
    if exact is not None:
        return [e for e in entries if e.get("confidence") == exact]
    if minimum is not None:
        threshold = CONFIDENCE_RANK.get(minimum, 0)
        return [e for e in entries
               if CONFIDENCE_RANK.get(e.get("confidence"), -1) >= threshold]
    return list(entries)


DEFAULT_MANIFEST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "manifest.json")


def load_default():
    return load(DEFAULT_MANIFEST_PATH)
