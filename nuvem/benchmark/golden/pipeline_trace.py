# -*- coding: utf-8 -*-
"""Schema do PIPELINE TRACE (itens 28-30 do CR-BLOCK-REFERENCE-CORPUS).

NAO implementa a emissao do rastro em producao (item 30 e' explicito:
nao mexer em `wall_stepper.py`/`continuous_modulation.py` nesta tarefa).
Este modulo e' so' o CONTRATO: o formato pequeno e estavel de UM evento
de rastro, um parser que aceita dados ja' em memoria (nunca le' arquivo
sozinho) e um validador que checa se uma sequencia de eventos e'
coerente com a ordem oficial do pipeline (item 27).

Pipeline oficial (item 27), como estagios nomeados (item 29 - os nomes
sao sugestao, nao exigencia; o que importa e' a ORDEM):

    WALL_START                 (grafo L/T/X resolvido, parede INTEIRA identificada)
    INTERSECTIONS_RESOLVED     (encontros L/T/X amarrados)
    CONTINUOUS_FILL             (modulacao continua da parede, ANTES de recortar aberturas)
    PRISM_VALIDATED              (prisma - juntas verticais - conferido)
    OPENING_APPLIED               (abertura aplicada - um VAZIO dentro da parede continua)
    CONFLICTING_BLOCK_REMOVED      (blocos que caem dentro do vao removidos)
    LOCAL_REPAIR                    (reparo local ao redor do vao - verga/contraverga/canaleta)
    FINAL_VALIDATION                  (validacao final da parede)

Uma parede SEM abertura nao passa por `OPENING_APPLIED`/
`CONFLICTING_BLOCK_REMOVED`/`LOCAL_REPAIR` - esses tres so' fazem sentido
quando ha' abertura (item 27: "abertura e' um vazio DENTRO da parede
continua", nao um estagio universal). O validador aceita essa omissao.
"""

STAGE_WALL_START = "WALL_START"
STAGE_INTERSECTIONS_RESOLVED = "INTERSECTIONS_RESOLVED"
STAGE_CONTINUOUS_FILL = "CONTINUOUS_FILL"
STAGE_PRISM_VALIDATED = "PRISM_VALIDATED"
STAGE_OPENING_APPLIED = "OPENING_APPLIED"
STAGE_CONFLICTING_BLOCK_REMOVED = "CONFLICTING_BLOCK_REMOVED"
STAGE_LOCAL_REPAIR = "LOCAL_REPAIR"
STAGE_FINAL_VALIDATION = "FINAL_VALIDATION"

# ORDEM oficial (item 27/29) - o que `validate_trace` checa.
STAGE_ORDER = (
    STAGE_WALL_START,
    STAGE_INTERSECTIONS_RESOLVED,
    STAGE_CONTINUOUS_FILL,
    STAGE_PRISM_VALIDATED,
    STAGE_OPENING_APPLIED,
    STAGE_CONFLICTING_BLOCK_REMOVED,
    STAGE_LOCAL_REPAIR,
    STAGE_FINAL_VALIDATION,
)
STAGE_RANK = dict((stage, index) for index, stage in enumerate(STAGE_ORDER))

# Estagios que so' existem quando a parede TEM abertura (item 27) - o
# validador nao exige presenca deles.
OPENING_ONLY_STAGES = (STAGE_OPENING_APPLIED, STAGE_CONFLICTING_BLOCK_REMOVED,
                       STAGE_LOCAL_REPAIR)

REQUIRED_FIELDS = ("wall_id", "stage", "sequence")


def make_trace_event(wall_id, stage, sequence, opening_id=None,
                     affected_region=None, metadata=None):
    """Um evento (item 29). `sequence` e' a ordem de emissao GLOBAL do
    rastro (inteiro crescente) - nao um indice por parede; e' o que
    permite reconstruir "o que aconteceu antes do que" entre paredes
    diferentes tambem, se um dia isso importar."""
    if stage not in STAGE_RANK:
        raise ValueError(
            "estagio desconhecido: {0!r}. Use um de {1} (ou estenda "
            "STAGE_ORDER - nunca invente um nome solto no evento).".format(
                stage, STAGE_ORDER))
    return {
        "wall_id": wall_id,
        "stage": stage,
        "sequence": int(sequence),
        "opening_id": opening_id,
        "affected_region": dict(affected_region) if affected_region else None,
        "metadata": dict(metadata) if metadata else {},
    }


def parse_trace(raw_events):
    """`raw_events`: lista de dicts JA' EM MEMORIA (nunca le' arquivo
    sozinho - quem chama decide de onde veio). Devolve
    `(eventos_normalizados, problemas)` - problemas descrevem cada evento
    malformado pelo indice, sem derrubar o parser inteiro por causa de UM
    evento ruim (o mesmo espirito de `validators`: nunca engolir em
    silencio, nunca travar tudo por um dado sujo)."""
    events, problems = [], []
    for index, raw in enumerate(raw_events or []):
        missing = [field for field in REQUIRED_FIELDS if raw.get(field) is None]
        if missing:
            problems.append("evento[{0}]: faltam campos {1}".format(index, missing))
            continue
        if raw.get("stage") not in STAGE_RANK:
            problems.append("evento[{0}]: estagio desconhecido {1!r}".format(
                index, raw.get("stage")))
            continue
        try:
            events.append(make_trace_event(
                raw["wall_id"], raw["stage"], raw["sequence"],
                opening_id=raw.get("opening_id"),
                affected_region=raw.get("affected_region"),
                metadata=raw.get("metadata"),
            ))
        except (ValueError, TypeError) as exc:
            problems.append("evento[{0}]: {1}".format(index, exc))
    return events, problems


def group_by_wall(events):
    """`{wall_id: [eventos ordenados por sequence]}`."""
    by_wall = {}
    for event in events:
        by_wall.setdefault(event["wall_id"], []).append(event)
    for wall_id in by_wall:
        by_wall[wall_id].sort(key=lambda e: e["sequence"])
    return by_wall


def validate_trace(events):
    """O rastro (de UM projeto, todas as paredes) e' coerente com a ordem
    oficial (item 27)? Por parede: `sequence` estritamente crescente, e
    os estagios PRESENTES respeitam `STAGE_ORDER` (estagios OPENING_ONLY
    podem faltar; qualquer estagio fora de ordem, ou repetido antes de um
    posterior, e' um problema apontado por parede - nunca so' um booleano
    cego)."""
    by_wall = group_by_wall(events)
    problems = []
    for wall_id, wall_events in by_wall.items():
        sequences = [e["sequence"] for e in wall_events]
        if sequences != sorted(sequences) or len(set(sequences)) != len(sequences):
            problems.append({
                "wall_id": wall_id,
                "problem": "sequence nao e' estritamente crescente",
                "sequences": sequences,
            })
            continue
        last_rank = -1
        for event in wall_events:
            rank = STAGE_RANK[event["stage"]]
            if rank < last_rank:
                problems.append({
                    "wall_id": wall_id,
                    "problem": "estagio fora de ordem",
                    "stage": event["stage"],
                    "expected_not_before_rank": last_rank,
                    "got_rank": rank,
                })
                break
            last_rank = rank
    return {
        "ok": not problems,
        "walls_checked": len(by_wall),
        "problems": problems,
    }
