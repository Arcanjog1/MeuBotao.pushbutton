# -*- coding: utf-8 -*-
"""CR-G12 - a regra #1 (junta vertical nunca coincide entre duas fiadas
vizinhas) passa a ser avaliada TAMBEM na FRONTEIRA ENTRE BANDAS de
abertura.

Causa-raiz (secao 27.7 de `nuvem/REGRAS_MODULACAO_BLOCOS.md`, agora
implementada - ver `docs/CR_G12_CROSS_BAND_IMPLEMENTATION.md`):
`solve_building_blocks_all_courses` agrupa as fiadas fisicas em BANDAS por
conjunto de aberturas ativas e chama `solve_building_blocks` uma vez por
banda. Cada banda resolvia seu par A/B DO ZERO: a familia B de uma banda
desencontra a familia A da MESMA banda, mas nunca via a fiada fisica
imediatamente abaixo/acima quando ela caia em OUTRA banda. Na fronteira a
regra #1 simplesmente nao era avaliada.

O reproducer FIEL e' o projeto oficial - varias tentativas de reducao
sintetica (as tres ja' versionadas em `nuvem/benchmark/future_cr_
preparation/cr_g12_cross_band/`, mais duas varreduras parametricas desta
CR, ~4.900 combinacoes) NAO reproduzem: numa planta pequena o solver nao
produz junta continua nenhuma. Por isso os testes de corpus abaixo rodam
`torre_easy_lo_r00_tgd`/`_tp1` de verdade, a mesma pratica de
`tests/test_block_arm_role_prism_stagger.py` e
`tests/regression/test_benchmark_baselines.py`.

PRE-FIX x POS-FIX: os testes de corpus comparam o MESMO projeto resolvido
com `CROSS_BAND_JOINT_PROPAGATION_ENABLED` desligado (o comportamento
anterior a esta CR, e' esse o reproducer) e ligado (producao). Cada
asserto de "resolvido" falha se o patch for revertido.

    python3 -m pytest tests/test_cross_band_joint_propagation_cr_g12.py -q
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import load_script  # noqa: E402

m = load_script.load()

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from nuvem.benchmark import solver_bridge, validators, model  # noqa: E402
from nuvem.benchmark.extract import from_solver  # noqa: E402


# ============================================================
# unidade - as duas pecas novas, sem solver
# ============================================================

def test_semente_vazia_no_primeiro_passe_da_primeira_banda():
    """A primeira banda nao tem vizinha resolvida: semente vazia, e o
    solver reproduz exatamente o comportamento anterior a esta CR."""
    assert m._cross_band_seed_for_band([0, 1, 2], {}, None, {0: 0, 1: 0, 2: 0}) == {}


def test_semente_ignora_vizinha_da_propria_banda():
    """Dentro da banda a regra #1 ja' e' avaliada pelo mecanismo historico
    (familia B evita a familia A) - repetir isso na semente so'
    acrescentaria restricao duplicada."""
    banda = {0: 0, 1: 0, 2: 0}
    resolvidas = {1: {7: [10.0, 20.0]}}
    assert m._cross_band_seed_for_band([0, 2], resolvidas, None, banda) == {}


def test_semente_pega_vizinha_de_outra_banda_na_paridade_certa():
    """A vizinha fisica tem SEMPRE paridade oposta: a semente da familia
    "A" desta banda vem de uma fiada "B" de outra banda, e vice-versa."""
    banda = {4: 0, 5: 1, 6: 1}
    resolvidas = {4: {3: [30.0, 70.0]}}
    seed = m._cross_band_seed_for_band([5, 6], resolvidas, None, banda)
    # fiada 5 e' impar -> familia B; e' ela que faz fronteira com a fiada 4
    assert seed == {3: {"A": [], "B": [30.0, 70.0]}}


def test_semente_usa_o_passe_anterior_para_a_vizinha_de_cima():
    """Segundo passe: a vizinha de CIMA ainda nao rodou neste passe, entao
    entra pelo resultado do passe anterior (Gauss-Seidel)."""
    banda = {5: 0, 6: 1, 7: 2}
    resolvidas = {5: {3: [10.0]}}          # de baixo, ja' resolvida NESTE passe
    anterior = {7: {3: [90.0]}, 5: {3: [999.0]}}  # de cima, do passe anterior
    seed = m._cross_band_seed_for_band([6], resolvidas, anterior, banda)
    # fiada 6 e' par -> familia A; 999.0 nao entra (a de baixo deste passe vence)
    assert seed == {3: {"A": [10.0, 90.0], "B": []}}


def _cell(center_cm, length_cm):
    return {"center_local": (center_cm / 100.0 * m.FEET_PER_METER, 0.0),
            "size_local": (length_cm / 100.0 * m.FEET_PER_METER,
                           8.0 / 100.0 * m.FEET_PER_METER)}


def _catalogo():
    """Mesmo catalogo sintetico de `tests/test_block_bonding.py` - os 6
    codigos que o solver conhece pelo nome."""
    def _bloco(code, length_cm, cells):
        return {"symbol": None, "logical_code": code, "length_cm": float(length_cm),
                "height_cm": 19.0, "width_cm": 14.0, "cells_local": cells,
                "is_special_bond": code in ("B34", "B54"),
                "is_compensator": code in ("C09", "C04"),
                "source_instance_id": None}
    return {
        "B39": _bloco("B39", 39, [_cell(-9.9, 15.7), _cell(9.9, 15.8)]),
        "B34": _bloco("B34", 34, [_cell(-10.2, 10.7), _cell(7.4, 15.7)]),
        "B54": _bloco("B54", 54, [_cell(-19.5, 15.8), _cell(0.0, 12.5), _cell(19.5, 15.8)]),
        "B19": _bloco("B19", 19, [_cell(0.0, 15.7)]),
        "C09": _bloco("C09", 9, []),
        "C04": _bloco("C04", 4, []),
    }


def test_troca_cross_band_nao_mexe_em_quem_ja_esta_certo():
    """Sem coincidencia com a fiada vizinha, o layout escolhido pelo
    caminho normal e' devolvido INTACTO - nunca troca por empate."""
    catalog = _catalogo()
    layout = m._pier_ordered_layout(119.0, catalog, 0.0, 0.0)
    assert layout is not None
    juntas = m._layout_internal_joint_positions_cm(layout, 0.0)
    longe = [j + 17.0 for j in juntas]
    assert m._cross_band_swapped_layout(
        layout, 119.0, catalog, 0.0, 0.0, 0.0, longe, [],
        leading_is_open=True, trailing_is_open=True) is layout


def test_troca_cross_band_desencontra_quando_ha_alternativa():
    """Com a fiada vizinha empilhando junta em cima, a troca acontece - e
    o resultado tem ESTRITAMENTE menos coincidencia.

    Cenario identico ao `INV-BLOCK-BOND-005` de `test_block_bonding.py`
    (trecho de 99cm fechado dos dois lados, juntas em 54,5 e 94,5) - la'
    ele prova o desencontro DENTRO da banda; aqui, o mesmo trecho, a
    mesma busca, so' que a fiada vizinha esta' na banda de baixo."""
    catalog = _catalogo()
    avoid = [54.5, 94.5]
    layout = m._pier_ordered_layout(99.0, catalog, 0.0, 0.0,
                                    leading_open_override=False,
                                    trailing_open_override=False)
    antes = m._count_joint_coincidences_cm(
        m._layout_internal_joint_positions_cm(layout, 35.0), avoid)
    assert antes == 2, "cenario perdeu o sentido"
    trocado = m._cross_band_swapped_layout(
        layout, 99.0, catalog, 0.0, 0.0, 35.0, avoid, [],
        leading_is_open=False, trailing_is_open=False)
    depois = m._count_joint_coincidences_cm(
        m._layout_internal_joint_positions_cm(trocado, 35.0), avoid)
    assert depois == 0, (
        "esperava desencontro cross-band: antes=%d depois=%d" % (antes, depois))


def test_troca_cross_band_nao_piora_a_regra_1_dentro_da_banda():
    """Guarda explicita: uma alternativa que resolvesse a fronteira de
    banda ao custo de empilhar junta com a familia OPOSTA da PROPRIA banda
    e' recusada - a regra #1 intra-banda ja' valia e nao pode piorar."""
    catalog = _catalogo()
    layout = m._pier_ordered_layout(99.0, catalog, 0.0, 0.0,
                                    leading_open_override=False,
                                    trailing_open_override=False)
    juntas = m._layout_internal_joint_positions_cm(layout, 35.0)
    # a MESMA lista nos dois papeis: qualquer alternativa que desencontre
    # do cross-band desencontra tambem do intra - entao o guard nao pode
    # devolver algo com MAIS coincidencia intra do que o layout original.
    trocado = m._cross_band_swapped_layout(
        layout, 99.0, catalog, 0.0, 0.0, 35.0, list(juntas), list(juntas),
        leading_is_open=False, trailing_is_open=False)
    intra_antes = m._count_joint_coincidences_cm(juntas, juntas)
    intra_depois = m._count_joint_coincidences_cm(
        m._layout_internal_joint_positions_cm(trocado, 35.0), juntas)
    assert intra_depois <= intra_antes


def test_troca_cross_band_e_desligavel_pela_flag_do_modulo():
    """`CROSS_BAND_JOINT_PROPAGATION_ENABLED` existe e o default de
    producao e' LIGADO (mesmo padrao de ARM_ROLE_SAFE_REPAIR_ENABLED)."""
    assert m.CROSS_BAND_JOINT_PROPAGATION_ENABLED is True
    assert m.CROSS_BAND_JOINT_PROPAGATION_PASSES >= 2


# ============================================================
# REPRODUCER MINIMO - 3 paredes REAIS do input.json oficial
#
# Reducao obtida por delta-debugging sobre a planta real (ver
# `nuvem/benchmark/future_cr_preparation/cr_g12_cross_band/reduzir.py` e
# `repro_g12d_minimo.py`): das 167 paredes do TGD sobraram TRES que ainda
# acusam a MESMA identidade fisica. Nenhuma coordenada inventada.
#
# Preserva o que importa: bandas abaixo/dentro/acima da abertura (uma
# delas de UMA FIADA SO'), o L_CORNER da ponta, o B54 de
# T_INTERSECTION_MIDSPAN que FIXA a junta da fiada z=121, o recorte/
# reparo da janela e os parametros reais dela.
#
# SUBPLANO TROCADO em 2026-09-09 (CR-N1). O subplano anterior
# (`(55, 82, 124)`, alvo `(-401,5; 309,5)`) DEIXOU DE REPRODUZIR: a CR-N1
# (`nuvem/REGRAS_MODULACAO_BLOCOS.md` secao 40) mudou a peca do no' de
# encontro vizinho naquelas tres paredes e, com a propagacao DESLIGADA, o
# sub-plano passou a acusar ZERO identidade - os dois testes do par
# viravam vacuos. O defeito NAO sumiu do corpus: com a flag desligada o
# TGD inteiro continua com 10 identidades cross-band PURAS (os testes de
# corpus abaixo continuam verdes, e sao eles a prova de que a CR-G12
# ainda tem alvo). O que se perdeu foi a REDUCAO, e ela foi refeita pelo
# MESMO metodo (vizinhanca geometrica do alvo + delta-debugging com o
# predicado duplo "reproduz com a flag OFF" E "zera com a flag ON").
# Nenhuma coordenada nova: `(4, 83, 119)` sao tres paredes do MESMO
# `input.json` oficial - uma principal de 1174cm com abertura e duas
# bonecas perpendiculares (183,2cm com abertura e 94cm), a mesma
# topologia de bandas do subplano antigo. Medido em 2026-09-09:
# flag OFF -> 21 identidades, entre elas o alvo, CROSS-BAND;
# flag ON  -> ZERO identidade; pecas de amarracao/abertura IDENTICAS
# nas duas rodadas (40 x 40).
# ============================================================

_SUBPLANO_PROJETO = "torre_easy_lo_r00_tgd"
_SUBPLANO_INDICES = (4, 83, 119)
_SUBPLANO_PONTO = (621.0, 17.0)
_SUBPLANO_COTAS = (121.0, 141.0)


def _subplano():
    import copy
    path = os.path.join(_ROOT, "nuvem", "benchmark", "projects",
                        _SUBPLANO_PROJETO, "input.json")
    with open(path, "r", encoding="utf-8") as handle:
        base = json.load(handle)
    projeto = copy.deepcopy(base)
    projeto["walls"] = [base["walls"][i] for i in _SUBPLANO_INDICES]
    return model.assign_ids(projeto)


def _resolve_subplano(enabled):
    projeto = _subplano()
    anterior = m.CROSS_BAND_JOINT_PROPAGATION_ENABLED
    m.CROSS_BAND_JOINT_PROPAGATION_ENABLED = enabled
    try:
        (solve_result, walls_to_create, nodes, openings_per_wall, catalog,
         base_z_ft, num_courses, _notes) = solver_bridge.run_solver(projeto)
    finally:
        m.CROSS_BAND_JOINT_PROPAGATION_ENABLED = anterior
    result_project = from_solver.project_from_solver(
        "repro_g12d", solve_result, walls_to_create, nodes, openings_per_wall,
        catalog, base_z_ft, num_courses, metadata={})
    findings, _errors = validators.run_all(result_project, {})
    band_of_course = _band_of_course(m, openings_per_wall, catalog, base_z_ft, num_courses)
    return _identidades(result_project, findings, band_of_course)


def test_reproducer_minimo_falha_no_codigo_anterior():
    """PRE-FIX: as 3 paredes reais acusam a junta continua cross-band em
    `(-401,5, 309,5)`, cotas 121/141, desencontro 0,00cm."""
    identidades = _resolve_subplano(False)
    alvo = [(chave, cross) for chave, cross in identidades.items()
            if chave[0] == _SUBPLANO_PONTO and chave[1] == _SUBPLANO_COTAS]
    assert alvo, (
        "o reproducer minimo deixou de reproduzir - conferir se alguma "
        "outra correcao mudou o layout das bandas antes de mexer aqui. "
        "identidades vistas: %s" % sorted(identidades))
    assert alvo[0][1] is True, "a identidade alvo tem de ser CROSS-BAND"


def test_reproducer_minimo_passa_com_a_correcao():
    """POS-FIX: o mesmo subplano nao tem junta continua NENHUMA."""
    identidades = _resolve_subplano(True)
    assert identidades == {}, (
        "esperava zero junta continua no subplano minimo com a correcao "
        "ligada: %s" % sorted(identidades))


def test_reproducer_minimo_nao_move_peca_de_amarracao_nem_abertura():
    """A correcao mexe SO' no preenchimento: as pecas de amarracao e as
    pecas de reparo de abertura ficam onde estavam."""
    def _pecas(enabled):
        projeto = _subplano()
        anterior = m.CROSS_BAND_JOINT_PROPAGATION_ENABLED
        m.CROSS_BAND_JOINT_PROPAGATION_ENABLED = enabled
        try:
            (solve_result, walls_to_create, nodes, openings_per_wall, catalog,
             base_z_ft, num_courses, _notes) = solver_bridge.run_solver(projeto)
        finally:
            m.CROSS_BAND_JOINT_PROPAGATION_ENABLED = anterior
        result_project = from_solver.project_from_solver(
            "repro_g12d", solve_result, walls_to_create, nodes, openings_per_wall,
            catalog, base_z_ft, num_courses, metadata={})
        return set(
            (wall["id"], row["row"], block["code"], round(block["t_start_cm"], 2),
             round(block["t_end_cm"], 2))
            for wall in result_project["walls"] for row in wall["rows"]
            for block in row["blocks"]
            if str(block.get("placement_reason") or "").startswith(
                ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION", "CORNER", "OPENING_REPAIR"))
        )

    assert _pecas(False) == _pecas(True)


# ============================================================
# corpus real - pre-fix (reproducer) x pos-fix
# ============================================================

_CACHE = {}


def _run(project_id, enabled):
    key = (project_id, enabled)
    if key in _CACHE:
        return _CACHE[key]
    path = os.path.join(_ROOT, "nuvem", "benchmark", "projects", project_id, "input.json")
    with open(path, "r", encoding="utf-8") as handle:
        input_project = json.load(handle)
    anterior = m.CROSS_BAND_JOINT_PROPAGATION_ENABLED
    m.CROSS_BAND_JOINT_PROPAGATION_ENABLED = enabled
    try:
        (solve_result, walls_to_create, nodes, openings_per_wall, catalog,
         base_z_ft, num_courses, _notes) = solver_bridge.run_solver(input_project)
    finally:
        m.CROSS_BAND_JOINT_PROPAGATION_ENABLED = anterior
    result_project = from_solver.project_from_solver(
        project_id, solve_result, walls_to_create, nodes, openings_per_wall,
        catalog, base_z_ft, num_courses, metadata={})
    findings, _errors = validators.run_all(result_project, {})
    band_of_course = _band_of_course(m, openings_per_wall, catalog, base_z_ft, num_courses)
    _CACHE[key] = (result_project, findings, band_of_course)
    return _CACHE[key]


def _band_of_course(module, openings_per_wall, catalog, base_z_ft, num_courses):
    course_height_ft, _err = module._course_height_ft(catalog, None)
    block_height_ft = course_height_ft - module._cm_to_ft(module.COURSE_JOINT_CM)
    groups = module._group_course_indices_by_opening_band(
        openings_per_wall, base_z_ft, course_height_ft, block_height_ft, num_courses)
    return dict((ci, band_pos) for band_pos, (cis, _f) in enumerate(groups) for ci in cis)


def _identidades(result_project, findings, band_of_course):
    """{identidade fisica: cross_band?} de PRISM_CONTINUOUS_JOINT.

    Identidade = (ponto GLOBAL da junta, cotas das duas fiadas, espessura)
    - regra §38.5: nunca `W0xx`, nunca o eixo, nunca o tipo do no'."""
    saida = {}
    for wall in result_project["walls"]:
        ordem = dict((row["row"], i) for i, row in enumerate(
            sorted(wall["rows"], key=lambda r: r["elevation_cm"])))
        cota = dict((row["row"], round(row["elevation_cm"], 1)) for row in wall["rows"])
        direction, _length = model.direction_of(wall["start_cm"], wall["end_cm"])
        for finding in findings:
            if finding["code"] != "PRISM_CONTINUOUS_JOINT" or finding["wall"] != wall["id"]:
                continue
            t_cm = finding["joint_t_cm"]
            ponto = (round(wall["start_cm"][0] + direction[0] * t_cm, 1),
                     round(wall["start_cm"][1] + direction[1] * t_cm, 1))
            cotas = tuple(sorted((cota[finding["row_a"]], cota[finding["row_b"]])))
            cross = (band_of_course.get(ordem[finding["row_a"]])
                     != band_of_course.get(ordem[finding["row_b"]]))
            chave = (ponto, cotas, wall["thickness_cm"])
            saida[chave] = saida.get(chave, False) or cross
    return saida


def _cross_band_puras(identidades):
    """As identidades que so' existem POR CAUSA da fronteira de banda.

    Uma junta que tambem coincide DENTRO de uma banda naquele mesmo ponto
    e' outro fenomeno (junta de peca de AMARRACAO repetida - conflito
    §27.8 item 2, sem decisao normativa) e nao e' desta CR."""
    intra = set(ponto for (ponto, _c, _t), cross in identidades.items() if not cross)
    return set(chave for chave, cross in identidades.items()
               if cross and not any(abs(chave[0][0] - p[0]) <= 1.6
                                    and abs(chave[0][1] - p[1]) <= 1.6 for p in intra))


PROJETOS = ("torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1")


@pytest.mark.slow
@pytest.mark.parametrize("project_id", PROJETOS)
def test_reproducer_pre_fix_tem_junta_continua_na_fronteira_de_banda(project_id):
    """REPRODUCER. Com a propagacao DESLIGADA (comportamento anterior a
    esta CR) o corpus oficial tem juntas continuas que existem
    exclusivamente na fronteira entre duas bandas de abertura."""
    puras = _cross_band_puras(_identidades(*_run(project_id, False)))
    assert puras, (
        "o reproducer da CR-G12 deixou de reproduzir em %s - antes de "
        "ajustar este teste, conferir se alguma outra correcao mudou o "
        "layout das bandas" % project_id)


@pytest.mark.slow
@pytest.mark.parametrize("project_id", PROJETOS)
def test_fronteira_de_banda_deixa_de_criar_junta_continua(project_id):
    """POS-FIX: as identidades cross-band PURAS do reproducer somem (ou
    encolhem muito), e nenhuma nova aparece."""
    antes = _cross_band_puras(_identidades(*_run(project_id, False)))
    depois = _cross_band_puras(_identidades(*_run(project_id, True)))
    assert not (depois - antes), (
        "a correcao criou junta continua cross-band NOVA em %s: %s"
        % (project_id, sorted(depois - antes)))
    assert len(depois) < len(antes), (
        "esperava menos junta continua cross-band pura em %s (antes=%d "
        "depois=%d)" % (project_id, len(antes), len(depois)))


@pytest.mark.slow
@pytest.mark.parametrize("project_id", PROJETOS)
def test_nenhuma_junta_continua_nova_em_lugar_nenhum(project_id):
    """Regra #1 e' absoluta: a correcao nao pode CRIAR junta continua em
    nenhum ponto, nem cross-band nem dentro de uma banda."""
    antes = set(_identidades(*_run(project_id, False)))
    depois = set(_identidades(*_run(project_id, True)))
    assert not (depois - antes), (
        "juntas continuas NOVAS em %s: %s" % (project_id, sorted(depois - antes)))
    assert len(depois) < len(antes)


@pytest.mark.slow
@pytest.mark.parametrize("project_id", PROJETOS)
def test_cobertura_aberturas_amarracao_e_posicao_com_delta_zero(project_id):
    """A correcao mexe SO' na composicao do preenchimento: nenhum achado
    de cobertura, abertura, encontro ou colisao pode mudar de contagem."""
    def _por_codigo(findings):
        contagem = {}
        for finding in findings:
            contagem[finding["code"]] = contagem.get(finding["code"], 0) + 1
        return contagem

    antes = _por_codigo(_run(project_id, False)[1])
    depois = _por_codigo(_run(project_id, True)[1])
    intocaveis = [code for code in set(antes) | set(depois)
                  if code.startswith(("COVERAGE_", "OPENING_", "JUNCTION_", "POSITION_"))]
    divergentes = [(code, antes.get(code, 0), depois.get(code, 0))
                   for code in sorted(intocaveis)
                   if antes.get(code, 0) != depois.get(code, 0)]
    assert not divergentes, (
        "esperava delta ZERO em cobertura/abertura/encontro/posicao em %s: %s"
        % (project_id, divergentes))


@pytest.mark.slow
def test_determinismo_da_correcao():
    """Duas execucoes da MESMA entrada produzem exatamente as mesmas
    pecas, na mesma ordem - a semente nunca depende de ordem de dict."""
    project_id = "torre_easy_lo_r00_tgd"
    path = os.path.join(_ROOT, "nuvem", "benchmark", "projects", project_id, "input.json")
    with open(path, "r", encoding="utf-8") as handle:
        input_project = json.load(handle)

    def _impressao():
        (solve_result, _walls, _nodes, _ops, _cat, _bz, num_courses,
         _notes) = solver_bridge.run_solver(input_project)
        course_candidates = solve_result["course_candidates"]
        return [
            (course_index, candidate["logical_code"], candidate["wall_idx"],
             round(candidate["origin_world"].X, 6), round(candidate["origin_world"].Y, 6))
            for course_index in sorted(course_candidates)
            for candidate in course_candidates[course_index]
        ]

    assert _impressao() == _impressao()
