# -*- coding: utf-8 -*-
"""CAPABILITIES por projeto (item 12 do pedido CR-BLOCK-REFERENCE-CORPUS).

Por que isto existe: no `manifest.json` anterior (CR-BLOCK-GOLDEN-BENCHMARK),
um projeto so' entrava no benchmark se tivesse basicamente TUDO (parede,
fiada, bloco, abertura, encontro). Agora um projeto PARCIAL tambem deve
participar - so' que apenas nas comparacoes que os dados dele realmente
sustentam. `capabilities` e' a lista do que dele e' seguro testar.

MECANICO, nao confiabilidade (item 32): inferir capability e' constatar um
FATO tecnico ("este projeto tem lista de aberturas nao vazia" -> pode medir
metrica de abertura). Isso nunca decide se o projeto e' confiavel como
verdade - aquilo continua sendo SO' `manifest.confidence`, escrito a mao.
Por isso `infer_capabilities` pode rodar automaticamente (e roda, dentro do
gerador do manifesto) sem violar a regra de nunca promover confianca
sozinho.
"""

from .. import model

# ---------------------------------------------------------------- lista
CAN_TEST_WALL_COVERAGE = "CAN_TEST_WALL_COVERAGE"
CAN_TEST_BLOCK_LAYOUT = "CAN_TEST_BLOCK_LAYOUT"
CAN_TEST_PRISM = "CAN_TEST_PRISM"
CAN_TEST_OPENINGS = "CAN_TEST_OPENINGS"
CAN_TEST_LTX = "CAN_TEST_LTX"
CAN_TEST_DETERMINISM = "CAN_TEST_DETERMINISM"
CAN_COMPARE_TO_HUMAN = "CAN_COMPARE_TO_HUMAN"
CAN_TEST_PROCESS_ORDER = "CAN_TEST_PROCESS_ORDER"
CAN_TEST_CONTINUOUS_FIRST = "CAN_TEST_CONTINUOUS_FIRST"

ALL_CAPABILITIES = (
    CAN_TEST_WALL_COVERAGE, CAN_TEST_BLOCK_LAYOUT, CAN_TEST_PRISM,
    CAN_TEST_OPENINGS, CAN_TEST_LTX, CAN_TEST_DETERMINISM,
    CAN_COMPARE_TO_HUMAN, CAN_TEST_PROCESS_ORDER, CAN_TEST_CONTINUOUS_FIRST,
)

CAPABILITY_MEANING = {
    CAN_TEST_WALL_COVERAGE: "tem paredes com fiadas/blocos - validate_wall_coverage roda",
    CAN_TEST_BLOCK_LAYOUT: "tem blocos posicionados (codigo, extensao no eixo) para comparar layout",
    CAN_TEST_PRISM: "tem >=2 fiadas numa mesma parede - junta vertical entre fiadas e' testavel",
    CAN_TEST_OPENINGS: "tem pelo menos uma abertura (porta/janela) com t_start/t_end/peitoril",
    CAN_TEST_LTX: "tem pelo menos um no' L/T/X registrado (wall['junctions'])",
    CAN_TEST_DETERMINISM: "tem input.json executavel - o solver pode ser rodado N vezes sobre ele",
    CAN_COMPARE_TO_HUMAN: "tem reference.json de origem HUMANA (reference_kind=HUMAN) - diff contra humano faz sentido",
    CAN_TEST_PROCESS_ORDER: "tem geometria de parede suficiente (start_cm/end_cm) para checar a ordem oficial (wall_order.py)",
    CAN_TEST_CONTINUOUS_FIRST: "tem PIPELINE TRACE gravado (pipeline_trace.py) - sem isso e' sempre NOT_AVAILABLE",
}


def _project_has_openings(project):
    for wall in (project or {}).get("walls") or []:
        if wall.get("openings"):
            return True
    return False


def _project_has_junctions(project):
    for wall in (project or {}).get("walls") or []:
        for junction in wall.get("junctions") or []:
            if junction.get("type") in (model.JUNCTION_L, model.JUNCTION_T, model.JUNCTION_X):
                return True
    return False


def _project_has_multi_row_wall(project):
    for wall in (project or {}).get("walls") or []:
        if len(wall.get("rows") or []) >= 2:
            return True
    return False


def _project_has_blocks(project):
    return model.count_blocks(project or {}) > 0 if (project or {}).get("walls") else False


def infer_capabilities(scan, reference_kind=None, has_pipeline_trace=False,
                       reference_project=None, input_project=None,
                       result_project=None):
    """Deriva as capabilities MECANICAMENTE, a partir do `inventory.scan_project(...)`
    (item 8) e, quando disponiveis em memoria, dos proprios projetos
    (`reference.json`/`input.json`/`result.json` ja carregados - carregar
    esses arquivos e' responsabilidade de quem chama; este modulo nao le'
    disco sozinho, so' recebe o que ja foi lido).

    `scan` e' o dict de `inventory.scan_project(project_id)`. Sem ele
    (`None`), devolve lista vazia - nunca inventa capability sem prova."""
    scan = scan or {}
    caps = set()

    any_project = reference_project or result_project or input_project
    has_wall_data = bool(scan.get("has_reference") or scan.get("has_input")
                         or (any_project and any_project.get("walls")))

    if has_wall_data:
        caps.add(CAN_TEST_PROCESS_ORDER)

    # As capabilities de conteudo (cobertura/layout/prisma/aberturas/LTX)
    # pedem o projeto de verdade em memoria - um scan mecanico so' sabe
    # "existe o arquivo", nao "o que tem dentro". Preferimos NOT_AVAILABLE
    # (a capability simplesmente nao entra na lista) a adivinhar pelo nome
    # do arquivo.
    content_project = reference_project or result_project
    if content_project is not None:
        if _project_has_blocks(content_project):
            caps.add(CAN_TEST_WALL_COVERAGE)
            caps.add(CAN_TEST_BLOCK_LAYOUT)
        if _project_has_multi_row_wall(content_project):
            caps.add(CAN_TEST_PRISM)
        if _project_has_openings(content_project):
            caps.add(CAN_TEST_OPENINGS)
        if _project_has_junctions(content_project):
            caps.add(CAN_TEST_LTX)

    if scan.get("has_input") or scan.get("has_input_real"):
        caps.add(CAN_TEST_DETERMINISM)

    if reference_kind == "HUMAN" and (scan.get("has_reference") or reference_project is not None):
        caps.add(CAN_COMPARE_TO_HUMAN)

    if has_pipeline_trace:
        caps.add(CAN_TEST_CONTINUOUS_FIRST)

    return sorted(caps)
