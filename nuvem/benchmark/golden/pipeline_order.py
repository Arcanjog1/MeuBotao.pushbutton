# -*- coding: utf-8 -*-
"""Interface PREPARADA (nao implementada em producao) para provar a
estrategia de pipeline "parede completa primeiro" (item 18 do
CR-BLOCK-GOLDEN-BENCHMARK, evoluida no CR-BLOCK-REFERENCE-CORPUS itens
27-30 com o schema estruturado de `pipeline_trace.py`):

    GRAFO L/T/X -> PAREDE INTEIRA -> MODULACAO CONTINUA -> PRISMA
        -> ABERTURA -> REMOCAO -> REPARO LOCAL -> VALIDACAO

O pedido e' explicito (itens 28/30/34): NAO alterar producao
(`wall_stepper.py`/`continuous_modulation.py`) so' para resolver isto
neste CR. O motor hoje nao emite nenhum rastro (trace) de EM QUE ORDEM as
etapas rodaram para uma parede com abertura - sem esse rastro,
`continuous_first_evidence`/`continuous_first_evidence_from_trace` so'
podem dizer "nao sei" (`NOT_AVAILABLE`), nunca inventar um "sim" a partir
de indicios indiretos (o resultado final e' compativel com mais de uma
ordem de execucao).

Duas formas de passar o rastro, quando ele existir:

* `continuous_first_evidence(stage_trace=[...])` - lista FLAT de nomes de
  etapa (formato do CR anterior, mantido por compatibilidade).
* `continuous_first_evidence_from_trace(events)` - lista de EVENTOS
  estruturados no formato de `pipeline_trace.py` (`wall_id`, `stage`,
  `sequence`, ...), POR PAREDE - o formato novo, preferido, porque
  distingue "esta parede seguiu a ordem" de "aquela nao seguiu", em vez
  de UMA sequencia so' pra' o projeto inteiro.
"""

from . import pipeline_trace

# Rotulo LEGADO (CR-BLOCK-GOLDEN-BENCHMARK) - mantido por compatibilidade.
# Corresponde, na mesma ordem, a `pipeline_trace.STAGE_ORDER`.
EXPECTED_STAGE_ORDER = (
    "graph_l_t_x",
    "full_wall",
    "continuous_modulation",
    "prism",
    "opening",
    "removal",
    "local_repair",
    "validation",
)

# Rotulo legado -> estagio do schema novo (`pipeline_trace.py`), na mesma
# posicao - um so' lugar que sabe a correspondencia entre os dois nomes.
LEGACY_STAGE_TO_TRACE_STAGE = dict(zip(EXPECTED_STAGE_ORDER, pipeline_trace.STAGE_ORDER))

STATUS_NOT_AVAILABLE = "NOT_AVAILABLE"
STATUS_MATCHES = "MATCHES_EXPECTED_ORDER"
STATUS_DIVERGES = "DIVERGES_FROM_EXPECTED_ORDER"


def continuous_first_evidence(stage_trace=None):
    """`stage_trace`: lista FLAT de nomes de etapa (rotulo legado,
    `EXPECTED_STAGE_ORDER`) observados, na ordem em que o motor de fato
    rodou, para o PROJETO INTEIRO (nao distingue parede).

    SEM `stage_trace`, a resposta e' sempre NOT_AVAILABLE - nunca um
    "sim" ou "nao" adivinhado a partir do resultado final."""
    if not stage_trace:
        return {
            "status": STATUS_NOT_AVAILABLE,
            "expected_stage_order": list(EXPECTED_STAGE_ORDER),
            "observed_stage_order": None,
            "note": (
                "o motor ainda nao emite rastro de ordem de execucao por "
                "parede; sem isso nao ha' como provar nem refutar "
                "'continuous_first' - ver docs/REFERENCE_CORPUS.md, secao "
                "limitacoes."
            ),
        }
    matches = list(stage_trace) == list(EXPECTED_STAGE_ORDER)
    return {
        "status": STATUS_MATCHES if matches else STATUS_DIVERGES,
        "expected_stage_order": list(EXPECTED_STAGE_ORDER),
        "observed_stage_order": list(stage_trace),
        "note": None,
    }


def continuous_first_evidence_from_trace(events=None):
    """Mesma pergunta que `continuous_first_evidence`, mas a partir de
    EVENTOS ESTRUTURADOS (`pipeline_trace.py`), POR PAREDE - forma
    preferida (item 29): distingue qual parede seguiu a ordem oficial de
    qual nao seguiu, em vez de uma resposta so' para o projeto inteiro.

    SEM `events`, sempre `NOT_AVAILABLE` (mesma regra de honestidade)."""
    if not events:
        return {
            "status": STATUS_NOT_AVAILABLE,
            "expected_stage_order": list(pipeline_trace.STAGE_ORDER),
            "walls_checked": 0,
            "problems": [],
            "note": (
                "o motor ainda nao emite pipeline trace por parede; sem "
                "isso nao ha' como provar nem refutar 'continuous_first' - "
                "ver docs/REFERENCE_CORPUS.md, secao limitacoes."
            ),
        }
    result = pipeline_trace.validate_trace(events)
    status = STATUS_MATCHES if result["ok"] else STATUS_DIVERGES
    return {
        "status": status,
        "expected_stage_order": list(pipeline_trace.STAGE_ORDER),
        "walls_checked": result["walls_checked"],
        "problems": result["problems"],
        "note": None,
    }
