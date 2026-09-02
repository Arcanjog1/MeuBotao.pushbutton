# -*- coding: utf-8 -*-
"""Interface PREPARADA (nao implementada) para provar a estrategia de
pipeline "parede completa primeiro" (item 18 do pedido):

    GRAFO L/T/X -> PAREDE INTEIRA -> MODULACAO CONTINUA -> PRISMA
        -> ABERTURA -> REMOCAO -> REPARO LOCAL -> VALIDACAO

O pedido e' explicito (item 34/18): NAO inventar agora um jeito de provar
isso. O motor (`solver_bridge.py`/`core/engine/*`) hoje nao emite nenhum
rastro (trace) de EM QUE ORDEM as etapas rodaram para uma parede com
abertura - sem esse rastro, `continuous_first_evidence` so' pode dizer
"nao sei", nunca inventar um "sim" a partir de indicios indiretos.

Quando o motor passar a emitir esse rastro (uma lista de nomes de etapa,
na ordem em que rodaram, por parede), esta funcao ganha corpo de verdade:
comparar a ordem observada com `EXPECTED_STAGE_ORDER` abaixo, que E' a
sequencia oficial (copiada do pedido, nao inventada aqui).
"""

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

STATUS_NOT_AVAILABLE = "NOT_AVAILABLE"
STATUS_MATCHES = "MATCHES_EXPECTED_ORDER"
STATUS_DIVERGES = "DIVERGES_FROM_EXPECTED_ORDER"


def continuous_first_evidence(stage_trace=None):
    """`stage_trace`: lista de nomes de etapa observados, na ordem em que
    o motor de fato rodou (quando existir um jeito de capturar isso).

    SEM `stage_trace`, a resposta e' sempre NOT_AVAILABLE - nunca um
    "sim" ou "nao" adivinhado a partir do resultado final (o resultado
    final e' compativel com varias ordens de execucao diferentes, entao
    nao prova nada sozinho sobre a ORDEM)."""
    if not stage_trace:
        return {
            "status": STATUS_NOT_AVAILABLE,
            "expected_stage_order": list(EXPECTED_STAGE_ORDER),
            "observed_stage_order": None,
            "note": (
                "o motor ainda nao emite rastro de ordem de execucao por "
                "parede; sem isso nao ha' como prova nem refutar "
                "'continuous_first' - ver docs/GOLDEN_BENCHMARK.md, secao "
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
