# -*- coding: utf-8 -*-
"""Reconstrucao de eixos/vaos/encontros a partir dos blocos.

Todos os casos aqui usam um dump INVENTADO, com geometria conhecida - a
reconstrucao e' pura (nenhum import do Revit), e e' justamente por isso
que da' para testa-la. Cada teste que nasceu de um erro real medido no
projeto TORRE EASY-LO-R00 diz isso no proprio nome/docstring."""

from benchmark import model
from benchmark.extract import reconstruct


def _dump(types, instances, document="teste"):
    return {
        "schema_version": 1, "document": document, "document_path": "",
        "level_filter": None, "levels": [], "types": types,
        "instances": instances, "walls": [], "openings": [], "warnings": [],
    }


def _type(index, name, length, height=19.0):
    return {"index": index, "symbol_id": 100 + index, "type_name": name,
            "family": name, "length_cm": length, "height_cm": height,
            "width_cm": 14.0, "count": 0}


B39 = _type(0, "BLOCO INTEIRO - 14x19x39", 39.0)
B19 = _type(1, "MEIO BLOCO - 14x19x19", 19.0)
B34 = _type(2, "BLOCO 34 - 14x19x34", 34.0)
CANALETA = _type(3, "CANALETA INTEIRA - 14x19x39", 39.0)
VERGA = _type(4, "VERGA 129", 129.0)
CORTADO = _type(5, "BLOCO INTEIRO CORTADO - 14x9x39", 39.0, height=9.0)


def _row_of_b39(y, z, count, x0=0.0):
    """Uma fiada horizontal de `count` B39 encostados (junta de 1cm)."""
    return [[0, x0 + 19.5 + i * 40.0, y, z, 0.0, 0] for i in range(count)]


# ------------------------------------------------------------- codigos
def test_codigo_das_seis_pecas_do_nucleo_bate_com_o_solver():
    """Sem isso o comparador nunca casaria peca do gabarito com peca do
    solver - eles usariam nomes diferentes para a mesma coisa."""
    assert reconstruct.code_for_type("BLOCO INTEIRO - 14x19x39", 39.0, 19.0) == "B39"
    assert reconstruct.code_for_type("BLOCO 34 - 14x19x34", 34.0, 19.0) == "B34"
    assert reconstruct.code_for_type("BLOCO 54 - 14x19x54", 54.0, 19.0) == "B54"
    assert reconstruct.code_for_type("MEIO BLOCO - 14x19x19", 19.0, 19.0) == "B19"
    assert reconstruct.code_for_type("COMPENSADOR 14x19x9", 9.0, 19.0) == "C09"
    assert reconstruct.code_for_type("PASTILHA - 14x19X4", 4.0, 19.0) == "C04"


def test_peca_cortada_ganha_codigo_proprio():
    """Um bloco de meia altura NAO pode virar B39: o solver o usaria como
    peca inteira."""
    assert reconstruct.code_for_type(
        "BLOCO INTEIRO CORTADO - 14x9x39", 39.0, 9.0) == "B39_C"


def test_papel_sai_do_nome_da_familia():
    assert reconstruct.role_for_type("CANALETA INTEIRA - 14x19x39") == \
        model.ROLE_CHANNEL_BLOCK
    assert reconstruct.role_for_type("VERGA 129") == model.ROLE_LINTEL
    assert reconstruct.role_for_type("CONTRAVERGA 169") == model.ROLE_COUNTER_LINTEL
    assert reconstruct.role_for_type("BLOCO INTEIRO CORTADO - 14x9x39") == \
        model.ROLE_CUT_BLOCK
    assert reconstruct.role_for_type("MEIO BLOCO - 14x19x19") == model.ROLE_HALF_BLOCK
    assert reconstruct.role_for_type("BLOCO INTEIRO - 14x19x39") == model.ROLE_STANDARD


# --------------------------------------------------------------- eixos
def test_uma_fiada_reta_vira_uma_parede_so():
    instances = []
    for course in range(5):
        instances.extend(_row_of_b39(0.0, 612.0 + course * 20.0, 6))
    project = reconstruct.build_project(_dump([B39], instances), "p")
    assert len(project["walls"]) == 1
    assert project["walls"][0]["length_cm"] == 239.0
    assert project["metadata"]["orphan_blocks"] == 0


def test_duas_retas_paralelas_distantes_viram_duas_paredes():
    instances = []
    for course in range(5):
        instances.extend(_row_of_b39(0.0, 612.0 + course * 20.0, 6))
        instances.extend(_row_of_b39(500.0, 612.0 + course * 20.0, 6))
    project = reconstruct.build_project(_dump([B39], instances), "p")
    assert len(project["walls"]) == 2


def test_vazio_maior_que_o_teto_de_vao_quebra_a_parede_em_duas():
    instances = []
    for course in range(5):
        z = 612.0 + course * 20.0
        instances.extend(_row_of_b39(0.0, z, 4))
        instances.extend(_row_of_b39(0.0, z, 4, x0=900.0))
    project = reconstruct.build_project(_dump([B39], instances), "p")
    assert len(project["walls"]) == 2


# --------------------------------------------------------- passo da fiada
def test_passo_da_fiada_ignora_cotas_pouco_povoadas():
    """ERRO REAL medido em TORRE EASY-LO-R00: com as meias-fiadas de peca
    CORTADA (cotas com 2 a 36 pecas) entrando na conta, o passo saiu 10cm
    num projeto cujo passo real, medido em 12.758 pecas, e' 20cm."""
    instances = []
    for course in range(6):
        instances.extend(_row_of_b39(0.0, 612.0 + course * 20.0, 8))
    # meia-fiada de ajuste: duas pecas cortadas a 10cm da grade
    instances.append([5, 19.5, 0.0, 722.0, 0.0, 0])
    instances.append([5, 59.5, 0.0, 722.0, 0.0, 0])
    project = reconstruct.build_project(_dump([B39, CORTADO], instances), "p")
    assert project["settings"]["course_step_cm"] == 20.0
    assert project["metadata"]["off_grid_blocks"] == 2


def test_meia_fiada_fora_da_grade_vira_fiada_propria_e_nao_apaga_a_vizinha():
    """A fiada e' a POSICAO na pilha, nao `(z - base)/passo` - pelo indice
    de grade, 712 e 722 caiam na mesma fiada e uma sobrescrevia a outra."""
    instances = []
    for course in range(6):
        instances.extend(_row_of_b39(0.0, 612.0 + course * 20.0, 8))
    instances.append([5, 19.5, 0.0, 722.0, 0.0, 0])
    project = reconstruct.build_project(_dump([B39, CORTADO], instances), "p")
    wall = project["walls"][0]
    indices = [row["row"] for row in wall["rows"]]
    assert len(indices) == len(set(indices)), "fiada duplicada"
    assert len(wall["rows"]) == 7
    elevations = sorted(row["elevation_cm"] for row in wall["rows"])
    assert 722.0 in elevations


# ------------------------------------------------------------ encontros
def test_ponta_encostada_no_meio_de_outra_parede_e_um_T_nao_um_L():
    """ERRO REAL: contando PAREDES em vez de BRACOS, um pavimento inteiro
    saiu com 286 'L' e nenhum T."""
    instances = []
    for course in range(6):
        z = 612.0 + course * 20.0
        instances.extend(_row_of_b39(0.0, z, 10))               # parede passante
        for i in range(5):                                       # parede que chega
            instances.append([0, 199.5, -19.5 - i * 40.0, z, 90.0, 0])
    project = reconstruct.build_project(_dump([B39], instances), "p")
    tipos = set(j["type"] for w in project["walls"] for j in w["junctions"])
    assert model.JUNCTION_T in tipos


def test_duas_pontas_que_se_encontram_formam_um_L():
    # A parede vertical nasce SOBRE a ponta da horizontal (x = 0): num
    # canto real os dois eixos se cruzam. Deslocar um deles meia peca ja'
    # passa da tolerancia de toque e o canto deixa de existir.
    instances = []
    for course in range(6):
        z = 612.0 + course * 20.0
        instances.extend(_row_of_b39(0.0, z, 6))
        for i in range(5):
            instances.append([0, 0.0, 19.5 + i * 40.0, z, 90.0, 0])
    project = reconstruct.build_project(_dump([B39], instances), "p")
    tipos = set(j["type"] for w in project["walls"] for j in w["junctions"])
    assert model.JUNCTION_L in tipos


# -------------------------------------------------------------- vaos
def test_vao_persistente_entre_fiadas_vira_abertura():
    instances = []
    for course in range(6):
        z = 612.0 + course * 20.0
        instances.extend(_row_of_b39(0.0, z, 4))            # 0..159
        instances.extend(_row_of_b39(0.0, z, 4, x0=260.0))  # 260..419
    project = reconstruct.build_project(_dump([B39], instances), "p")
    openings = project["walls"][0]["openings"]
    assert len(openings) == 1
    assert openings[0]["confidence"] == "reconstructed"
    assert 90.0 <= openings[0]["width_cm"] <= 110.0


def test_input_derivado_do_gabarito_nao_leva_nenhuma_peca():
    """O `input.json` e' o PROBLEMA. Uma peca vazada dele para o solver
    seria resposta dada."""
    instances = []
    for course in range(6):
        instances.extend(_row_of_b39(0.0, 612.0 + course * 20.0, 6))
    reference = reconstruct.build_project(_dump([B39], instances), "p")
    entrada = reconstruct.input_from_reference(reference)
    assert model.count_blocks(entrada) == 0
    assert entrada["source"] == "input"
    assert len(entrada["walls"]) == len(reference["walls"])
    assert entrada["walls"][0]["openings"] == reference["walls"][0]["openings"]
