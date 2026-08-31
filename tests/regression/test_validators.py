# -*- coding: utf-8 -*-
"""Cada validador, contra um defeito PLANTADO de proposito.

Todo teste aqui segue o mesmo par: uma planta com o defeito (tem que
acusar) e a mesma planta sem ele (nao pode acusar). Sem o segundo caso um
validador que devolvesse 'FAIL' sempre passaria em todos os testes.

Estes sao os casos de regressao do item 12: quando um defeito for
corrigido no solver, o teste que o descreve continua aqui, e uma mudanca
futura que o traga de volta quebra a suite."""

from benchmark import model
from benchmark.validators import (validate_block_positions, validate_compensators,
                                  validate_junctions, validate_openings,
                                  validate_prism, validate_wall_coverage)


def _blocks(*items):
    """items: (code, t_start, t_end) -> lista de blocos ja' no eixo X."""
    return [
        model.make_block(code, end - start, ((start + end) / 2.0, 0.0), 0.0, 0.0,
                         start, end, role=model.ROLE_STANDARD)
        for code, start, end in items
    ]


def _wall(rows, length=300.0, openings=None, junctions=None, wall_id="W001"):
    built = []
    for index, (elevation, items) in enumerate(rows):
        blocks = []
        for code, start, end in items:
            blocks.append(model.make_block(
                code, end - start, ((start + end) / 2.0, 0.0), elevation, 0.0,
                start, end, role=model.ROLE_STANDARD, width_cm=14.0,
                wall_id=wall_id, row=index))
        built.append(model.make_row(index, elevation, blocks))
    return model.make_wall(wall_id, (0, 0), (length, 0), 14.0,
                           height_cm=len(rows) * 20.0,
                           openings=openings or [], junctions=junctions or [],
                           rows=built)


def _project(walls, catalog=None):
    project = model.make_project(
        "t", "solver", walls=walls,
        settings={"base_z_cm": 0.0, "course_step_cm": 20.0, "block_height_cm": 19.0},
        catalog=catalog or {"B39": {"length_cm": 39.0, "height_cm": 19.0,
                                    "width_cm": 14.0}},
    )
    return model.assign_ids(project)


def _codes(findings):
    return sorted(f["code"] for f in findings)


# --------------------------------------------------------------- prisma
def test_prisma_acusa_junta_alinhada_em_fiadas_consecutivas():
    wall = _wall([
        (0.0, [("B39", 0, 39), ("B39", 40, 79)]),
        (20.0, [("B39", 0, 39), ("B39", 40, 79)]),
    ])
    findings = validate_prism.validate_wall(wall)
    assert "PRISM_CONTINUOUS_JOINT" in _codes(findings)


def test_prisma_nao_acusa_quando_as_juntas_desencontram():
    wall = _wall([
        (0.0, [("B39", 0, 39), ("B39", 40, 79)]),
        (20.0, [("B19", 0, 19), ("B39", 20, 59), ("B19", 60, 79)]),
    ])
    findings = validate_prism.validate_wall(wall)
    assert "PRISM_CONTINUOUS_JOINT" not in _codes(findings)


def test_prisma_respeita_a_excecao_da_peca_de_fechamento_na_ponta():
    """Secao 11.8: C04/C09/B19 encostados numa abertura ou na PONTA do
    eixo podem ficar alinhados entre fiadas."""
    wall = _wall([
        (0.0, [("B19", 0, 19), ("B39", 20, 59)]),
        (20.0, [("B19", 0, 19), ("B39", 20, 59)]),
    ], length=59.0)
    findings = validate_prism.validate_wall(wall)
    assert "PRISM_CONTINUOUS_JOINT" not in _codes(findings)


# -------------------------------------------------------- compensadores
def test_compensadores_consecutivos_sao_acusados():
    wall = _wall([(0.0, [("B39", 0, 39), ("C09", 40, 49), ("C04", 50, 54)])])
    findings = validate_compensators.validate_wall(wall, 19.0)
    assert "COMPENSATOR_CONSECUTIVE" in _codes(findings)


def test_um_compensador_sozinho_nao_e_acusado():
    wall = _wall([(0.0, [("B39", 0, 39), ("C09", 40, 49), ("B39", 50, 89)])])
    findings = validate_compensators.validate_wall(wall, 19.0)
    assert "COMPENSATOR_CONSECUTIVE" not in _codes(findings)
    assert "COMPENSATOR_EXCESS_IN_RUN" not in _codes(findings)


def test_faixa_vertical_de_compensadores_e_acusada():
    rows = [(20.0 * i, [("B39", 0, 39), ("C09", 40, 49), ("B39", 50, 89)])
            for i in range(4)]
    findings = validate_compensators.validate_wall(_wall(rows), 19.0)
    assert "COMPENSATOR_VERTICAL_STRIP" in _codes(findings)


# ------------------------------------------------------------ aberturas
def test_bloco_dentro_do_vao_de_porta_e_erro_critico():
    porta = model.make_opening(model.OPENING_DOOR, 100, 200, 0, 210)
    wall = _wall([(0.0, [("B39", 120, 159)])], openings=[porta])
    findings = validate_openings.validate_wall(wall, 19.0)
    assert "OPENING_BLOCK_INSIDE_DOOR" in _codes(findings)


def test_bloco_que_atravessa_a_jamba_e_acusado_a_parte():
    porta = model.make_opening(model.OPENING_DOOR, 100, 200, 0, 210)
    wall = _wall([(0.0, [("B39", 80, 119)])], openings=[porta])
    codes = _codes(validate_openings.validate_wall(wall, 19.0))
    assert "OPENING_BLOCK_CROSSES_JAMB" in codes
    assert "OPENING_BLOCK_INSIDE_DOOR" not in codes


def test_fiada_abaixo_do_peitoril_da_janela_tem_que_ser_solida():
    """Secao 4: janela nao interrompe a fiada de baixo."""
    janela = model.make_opening(model.OPENING_WINDOW, 100, 220, 90, 200)
    wall = _wall([(0.0, [("B39", 0, 39)])], openings=[janela])
    assert "OPENING_SOLID_BELOW_SILL_MISSING" in _codes(
        validate_openings.validate_wall(wall, 19.0))


def test_fiada_solida_abaixo_do_peitoril_nao_e_acusada():
    janela = model.make_opening(model.OPENING_WINDOW, 100, 220, 90, 200)
    wall = _wall([(0.0, [("B39", 0, 39), ("B39", 40, 79), ("B39", 80, 119),
                         ("B39", 120, 159), ("B39", 160, 199), ("B39", 200, 239)])],
                 openings=[janela])
    assert "OPENING_SOLID_BELOW_SILL_MISSING" not in _codes(
        validate_openings.validate_wall(wall, 19.0))


def test_bloco_fora_do_vao_nao_e_acusado():
    porta = model.make_opening(model.OPENING_DOOR, 100, 200, 0, 210)
    wall = _wall([(0.0, [("B39", 0, 39), ("B39", 201, 240)])], openings=[porta])
    codes = _codes(validate_openings.validate_wall(wall, 19.0))
    assert "OPENING_BLOCK_INSIDE_DOOR" not in codes
    assert "OPENING_BLOCK_CROSSES_JAMB" not in codes


# ------------------------------------------------------------ cobertura
def test_parede_sem_nenhum_bloco_e_erro_critico():
    wall = _wall([])
    findings = validate_wall_coverage.validate_wall(wall, 19.0)
    assert "COVERAGE_WALL_NOT_MODULATED" in _codes(findings)


def test_fiada_faltando_no_meio_e_acusada():
    wall = _wall([(0.0, [("B39", 0, 39)]), (20.0, []), (40.0, [("B39", 0, 39)])])
    assert "COVERAGE_MISSING_ROW" in _codes(
        validate_wall_coverage.validate_wall(wall, 19.0))


def test_fiada_quase_vazia_ao_lado_de_fiada_cheia_e_critica():
    """O defeito real medido no piloto: metade das fiadas sai completa e a
    outra metade quase vazia."""
    cheia = [("B39", i * 40.0, i * 40.0 + 39.0) for i in range(5)]
    wall = _wall([(0.0, cheia), (20.0, [("C09", 190, 199)])], length=199.0)
    assert "COVERAGE_ROW_MOSTLY_EMPTY" in _codes(
        validate_wall_coverage.validate_wall(wall, 19.0))


def test_vazio_dentro_do_vao_nao_conta_como_falta_de_cobertura():
    porta = model.make_opening(model.OPENING_DOOR, 100, 200, 0, 210)
    wall = _wall([(0.0, [("B39", 0, 39), ("B39", 40, 79), ("B19", 80, 99),
                         ("B19", 200, 219), ("B39", 220, 259),
                         ("B39", 260, 299)])],
                 length=299.0, openings=[porta])
    assert "COVERAGE_GAP_IN_ROW" not in _codes(
        validate_wall_coverage.validate_wall(wall, 19.0))


def test_blocos_orfaos_nunca_somem_do_relatorio():
    project = _project([_wall([(0.0, [("B39", 0, 39)])])])
    project["orphan_blocks"] = [{"code": "B39"}]
    assert "COVERAGE_ORPHAN_BLOCKS" in _codes(
        validate_wall_coverage.validate(project))


# -------------------------------------------------------- posicionamento
def test_sobreposicao_na_mesma_fiada_e_erro_critico():
    wall = _wall([(0.0, [("B39", 0, 39), ("B39", 30, 69)])])
    assert "POSITION_OVERLAP" in _codes(
        validate_block_positions.validate_wall(wall))


def test_pecas_encostadas_com_junta_nao_sao_sobreposicao():
    wall = _wall([(0.0, [("B39", 0, 39), ("B39", 40, 79)])])
    assert "POSITION_OVERLAP" not in _codes(
        validate_block_positions.validate_wall(wall))


def test_bloco_alem_da_ponta_da_parede_e_acusado():
    wall = _wall([(0.0, [("B39", 280, 319)])], length=300.0)
    assert "POSITION_OUTSIDE_WALL" in _codes(
        validate_block_positions.validate_wall(wall))


def test_bloco_com_comprimento_incoerente_e_acusado():
    block = model.make_block("B39", 39.0, (20.0, 0.0), 0.0, 0.0, 0.0, 60.0)
    wall = model.make_wall("W001", (0, 0), (300, 0), 14.0,
                           rows=[model.make_row(0, 0.0, [block])])
    assert "POSITION_LENGTH_MISMATCH" in _codes(
        validate_block_positions.validate_wall(wall))


# ----------------------------------------------------------- amarracoes
def _junction(point, junction_type=model.JUNCTION_L, t_cm=0.0):
    return {"type": junction_type, "t_cm": t_cm, "point_cm": list(point),
            "neighbors": [], "at_end": True}


def test_encontro_sem_nenhuma_peca_e_acusado():
    wall_a = _wall([(0.0, [("B39", 40, 79)])],
                   junctions=[_junction((0.0, 0.0))], wall_id="W001")
    wall_b = model.make_wall("W002", (0, 0), (0, 300), 14.0,
                             junctions=[_junction((0.0, 0.0))],
                             rows=[model.make_row(0, 0.0, [])])
    project = _project([wall_a, wall_b])
    assert "JUNCTION_MISSING_BINDING" in _codes(validate_junctions.validate(project))


def test_amarracao_em_L_com_peca_no_no_nao_e_acusada():
    """A peca que amarra pode estar na parede VIZINHA - por isso o
    validador olha o NO', nao a parede (falso positivo real de 120
    achados na primeira versao)."""
    tie = model.make_block("B34", 34.0, (17.0, 0.0), 0.0, 0.0, 0.0, 34.0,
                           role=model.ROLE_L_BINDING, width_cm=14.0,
                           wall_id="W001", row=0)
    wall_a = model.make_wall("W001", (0, 0), (300, 0), 14.0,
                             junctions=[_junction((0.0, 0.0))],
                             rows=[model.make_row(0, 0.0, [tie])])
    wall_b = model.make_wall("W002", (0, 0), (0, 300), 14.0,
                             junctions=[_junction((0.0, 0.0))],
                             rows=[model.make_row(0, 0.0, [])])
    project = _project([wall_a, wall_b])
    assert "JUNCTION_MISSING_BINDING" not in _codes(
        validate_junctions.validate(project))


def test_no_declarado_por_uma_parede_so_nao_vira_erro():
    """Encontro com uma parede so' e' dado incompleto da extracao, nao
    erro do solver - culpar o solver por isso seria mentira."""
    wall = _wall([(0.0, [("B39", 40, 79)])], junctions=[_junction((0.0, 0.0))])
    project = _project([wall])
    assert "JUNCTION_MISSING_BINDING" not in _codes(
        validate_junctions.validate(project))
