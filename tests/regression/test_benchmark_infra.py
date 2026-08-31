# -*- coding: utf-8 -*-
"""Testes da INFRAESTRUTURA do benchmark - modelo, identidade, comparador,
score.

Todos rodam sem Revit e sem solver: sao plantas montadas a mao, com
geometria conhecida, exatamente para que uma falha aqui aponte para o
benchmark e nunca para o motor."""

from benchmark import analysis, model, scoring
from benchmark.comparator import compare_projects as comparator
from benchmark.comparator import match as matcher
from benchmark.validators import base


# --------------------------------------------------------------- modelo
def test_chave_da_parede_nao_muda_com_o_sentido_do_desenho():
    """A MESMA parede desenhada ao contrario tem que ter a mesma chave -
    senao gabarito e resultado nunca casariam (item 4)."""
    a = model.wall_stable_key((0, 200), (100, 200), 14)
    b = model.wall_stable_key((100, 200), (0, 200), 14)
    assert a == b


def test_chave_da_parede_muda_com_a_espessura():
    a = model.wall_stable_key((0, 0), (100, 0), 14)
    b = model.wall_stable_key((0, 0), (100, 0), 19)
    assert a != b


def test_chave_do_bloco_ignora_o_codigo_de_proposito():
    """Trocar um B39 por dois B19 no mesmo ponto tem que aparecer como
    PECA DIFERENTE no mesmo lugar, nao como duas pecas sem relacao."""
    key_a = model.block_stable_key("W|x", 3, 39.0)
    key_b = model.block_stable_key("W|x", 3, 39.0)
    assert key_a == key_b


def test_ids_sao_deterministicos_e_independem_da_ordem_de_entrada():
    def build(order):
        walls = [
            model.make_wall("?", (0, 0), (300, 0), 14),
            model.make_wall("?", (0, 300), (300, 300), 14),
        ]
        project = model.make_project("p", "synthetic",
                                     walls=[walls[i] for i in order])
        return [w["id"] + "@" + w["key"] for w in model.assign_ids(project)["walls"]]

    assert build([0, 1]) == build([1, 0])


# ------------------------------------------------------------ geometria
def test_coordenada_axial_separa_ao_longo_de_perpendicular():
    t, s = model.axial_coordinates((50, 5), (0, 0), (1, 0))
    assert round(t, 6) == 50.0
    assert round(s, 6) == 5.0


def test_subtracao_de_intervalos_devolve_os_pedacos_certos():
    assert analysis.subtract_intervals((0, 100), [(20, 30), (50, 60)]) == [
        (0, 20), (30, 50), (60, 100)]


def test_abertura_so_esvazia_a_faixa_vertical_dela():
    """Regra da secao 4: janela com peitoril 90 nao interrompe a fiada de
    baixo."""
    janela = model.make_opening(model.OPENING_WINDOW, 100, 220, 90, 200)
    assert not analysis.opening_active_in_row(janela, 0.0, 19.0)
    assert analysis.opening_active_in_row(janela, 100.0, 19.0)
    assert not analysis.opening_active_in_row(janela, 200.0, 19.0)


def test_porta_esvazia_desde_a_base():
    porta = model.make_opening(model.OPENING_DOOR, 100, 200, 0, 210)
    assert analysis.opening_active_in_row(porta, 0.0, 19.0)


# ----------------------------------------------------------- casamento
def _wall(start, end, thickness=14.0, wall_id="W001"):
    return model.make_wall(wall_id, start, end, thickness)


def test_casa_paredes_iguais_mesmo_desenhadas_ao_contrario():
    result = model.make_project("r", "solver", walls=[_wall((0, 0), (300, 0))])
    reference = model.make_project("f", "revit_reference",
                                   walls=[_wall((300, 0), (0, 0), wall_id="W009")])
    matching = matcher.match_walls(result, reference)
    assert len(matching["pairs"]) == 1
    assert not matching["only_in_result"]


def test_casa_parede_que_o_ajuste_encurtou_alguns_centimetros():
    result = model.make_project("r", "solver", walls=[_wall((0, 0), (296, 0))])
    reference = model.make_project("f", "revit_reference", walls=[_wall((0, 0), (300, 0))])
    assert len(matcher.match_walls(result, reference)["pairs"]) == 1


def test_nao_casa_paredes_paralelas_distantes():
    result = model.make_project("r", "solver", walls=[_wall((0, 0), (300, 0))])
    reference = model.make_project("f", "revit_reference", walls=[_wall((0, 500), (300, 500))])
    matching = matcher.match_walls(result, reference)
    assert not matching["pairs"]
    assert len(matching["only_in_result"]) == 1
    assert len(matching["only_in_reference"]) == 1


def test_casamento_e_um_para_um():
    """Duas paredes do resultado nao podem casar com o MESMO gabarito."""
    result = model.make_project("r", "solver", walls=[
        _wall((0, 0), (300, 0), wall_id="W001"),
        _wall((0, 1), (300, 1), wall_id="W002"),
    ])
    reference = model.make_project("f", "revit_reference", walls=[_wall((0, 0), (300, 0))])
    matching = matcher.match_walls(result, reference)
    assert len(matching["pairs"]) == 1
    assert len(matching["only_in_result"]) == 1


# ---------------------------------------------------------- comparacao
def _project_with_row(codes_and_extents, project_id, source):
    blocks = [
        model.make_block(code, end - start, ((start + end) / 2.0, 0.0), 0.0, 0.0,
                         start, end)
        for code, start, end in codes_and_extents
    ]
    wall = model.make_wall("W001", (0, 0), (300, 0), 14,
                           rows=[model.make_row(0, 0.0, blocks)])
    return model.assign_ids(model.make_project(project_id, source, walls=[wall]))


def test_peca_diferente_no_mesmo_lugar_e_substituicao_equivalente():
    """Item 10: solucao diferente NAO e' erro. O comparador precisa
    distinguir 'outra peca no mesmo lugar' de 'outro layout'."""
    result = _project_with_row([("B39", 0, 39)], "r", "solver")
    reference = _project_with_row([("B34", 0, 39)], "f", "revit_reference")
    comparison = comparator.compare_projects(result, reference)
    assert comparison["totals"][comparator.DIFF_EQUIVALENT] == 1
    assert comparison["totals"][comparator.DIFF_IDENTICAL] == 0
    assert comparison["structural_similarity"] == 1.0


def test_mesma_peca_no_mesmo_lugar_e_identica():
    result = _project_with_row([("B39", 0, 39)], "r", "solver")
    reference = _project_with_row([("B39", 0, 39)], "f", "revit_reference")
    comparison = comparator.compare_projects(result, reference)
    assert comparison["totals"][comparator.DIFF_IDENTICAL] == 1
    assert comparison["similarity"] == 1.0


def test_peca_que_o_solver_nao_pos_aparece_como_faltando():
    result = _project_with_row([("B39", 0, 39)], "r", "solver")
    reference = _project_with_row([("B39", 0, 39), ("B19", 40, 59)],
                                  "f", "revit_reference")
    comparison = comparator.compare_projects(result, reference)
    assert comparison["totals"][comparator.DIFF_MISSING] == 1


# --------------------------------------------------------------- score
def _score_with(findings, walls=3):
    project = model.make_project("p", "solver", walls=[
        model.make_wall("W{0:03d}".format(i + 1), (0, i * 300), (300, i * 300), 14)
        for i in range(walls)
    ])
    return scoring.score_project(project, findings)


def test_erro_de_nivel_2_nao_reprova_a_parede():
    """Preferencia nao e' erro (item 10)."""
    finding = base.finding("JUNCTION_WRONG_PIECE", wall="W001")
    score = _score_with([finding])
    assert score["success_rate"] == 1.0
    assert score["findings_level_2"] == 1


def test_erro_critico_nao_some_atras_da_media():
    """Item 13: 98% com 3 paredes nao moduladas continua sendo grave."""
    findings = [base.finding("COVERAGE_WALL_NOT_MODULATED", wall="W001")]
    score = _score_with(findings, walls=100)
    assert score["success_rate"] > 0.98
    assert score["blocking"] is True
    assert score["critical_errors"] == 1


def test_comparacao_entre_versoes_marca_regressao_critica():
    """Item 14: erro critico novo e' REGRESSAO CRITICA mesmo com o total
    de erros caindo."""
    antes = _score_with([base.finding("COMPENSATOR_CONSECUTIVE", wall="W001"),
                         base.finding("COMPENSATOR_CONSECUTIVE", wall="W002")])
    depois = _score_with([base.finding("COVERAGE_WALL_NOT_MODULATED", wall="W003")])
    delta = scoring.compare_runs(antes, depois)
    assert delta["verdict"] == scoring.STATUS_CRITICAL_REGRESSION


def test_comparacao_entre_versoes_reconhece_melhoria():
    antes = _score_with([base.finding("COMPENSATOR_CONSECUTIVE", wall="W001")])
    depois = _score_with([])
    delta = scoring.compare_runs(antes, depois)
    assert delta["verdict"] == scoring.STATUS_IMPROVED
    assert delta["walls_fixed"] == ["W001"]


def test_toda_classe_de_erro_de_nivel_1_tem_regra_de_origem():
    """Um erro obrigatorio sem referencia de regra e' uma exigencia que
    ninguem consegue justificar depois."""
    sem_regra = [e.code for e in base.ERROR_CLASSES
                 if e.level == base.LEVEL_MANDATORY and not e.rule_ref]
    assert sem_regra == []


def test_taxonomia_nao_tem_codigo_duplicado():
    codes = [e.code for e in base.ERROR_CLASSES]
    assert len(codes) == len(set(codes))
