# -*- coding: utf-8 -*-
"""CR-C1 - `COVERAGE_MISSING_ROW` no topo era decidido por um numero GLOBAL.

O DEFEITO (medido antes de tocar em codigo)
-------------------------------------------
`validate_wall_coverage.validate` lia `settings.expected_rows` - que sai de
`settings.num_courses`, o TETO de fiadas do PROJETO - e comparava com a
CONTAGEM de fiadas de CADA parede:

    if expected_rows and indices and len(indices) < expected_rows: acusa

As paredes do corpus real tem alturas DIFERENTES (220 / 260 / 270 / 280 /
281cm com passo de 20cm). Uma parede de 260cm nunca vai ter 17 fiadas: ela
esta' correta e era acusada assim mesmo.

Prova independente do gabarito: rodando os validadores sobre o PROPRIO
gabarito HUMANO (`reference.json`, que e' a referencia de correcao),
`COVERAGE_MISSING_ROW` da' 95 (TGD) e 94 (TP1) - numeros que o
`reference_score.json` oficial ja' registra - e 100% deles vem deste ramo,
ZERO do ramo do meio da pilha. Um validador que acusa a propria referencia
esta' medindo a coisa errada.

A CORRECAO (secao 37 das regras)
--------------------------------
A pergunta passa a ser FISICA e por ELEVACAO, parede a parede: *ainda cabe
uma fiada INTEIRA (proximo passo + corpo da peca) abaixo do pe-direito
DESTA parede?* Nao se calcula ONDE cada fiada deveria cair - a fiada do
topo nao segue o grid (no gabarito, 270cm fecha em z=250 e 281cm em
z=261, com canaleta `CJ19` de 29cm e pecas `_C` de 9cm); reproduzir isso
aqui seria reimplementar a politica de empilhamento DENTRO do validador.

Estes testes cobrem os dois lados: o falso positivo que tem que sumir E a
ausencia real de fiada, que tem que continuar sendo acusada.

    python3 -m pytest tests/test_validator_coverage_expected_rows_cr_c1.py -q
"""

import json
import os

import pytest

from benchmark import model
from benchmark.validators import validate_wall_coverage as VC

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECTS_DIR = os.path.join(ROOT, "nuvem", "benchmark", "projects")

STEP_CM = 20.0
BLOCK_H_CM = 19.0


# --------------------------------------------------------------- helpers
def _row(index, z_cm, length_cm=300.0, pieces=None, wall_id="W001"):
    """Uma fiada cheia (ou com as pecas dadas) na cota `z_cm`."""
    if pieces is None:
        pieces = [(t, min(t + 39.0, length_cm))
                  for t in range(0, int(length_cm), 40)
                  if t + 39.0 <= length_cm]
    blocks = [
        model.make_block("B39", end - start, ((start + end) / 2.0, 0.0), z_cm,
                         0.0, start, end, role=model.ROLE_STANDARD,
                         width_cm=14.0, height_cm=BLOCK_H_CM, wall_id=wall_id,
                         row=index)
        for start, end in pieces
    ]
    return model.make_row(index, z_cm, blocks)


def _wall(height_cm, n_courses, base_z_cm=0.0, length_cm=300.0, wall_id="W001",
          extra_rows=(), openings=None, y_cm=0.0):
    """Parede com `n_courses` fiadas no passo do grid a partir de `base_z_cm`.

    `extra_rows`: cotas INTERCALADAS (faixas de abertura), que e' como o
    corpus real produz fiadas fora do passo."""
    rows = [_row(i, base_z_cm + i * STEP_CM, length_cm, wall_id=wall_id)
            for i in range(n_courses)]
    for offset, z_cm in enumerate(extra_rows):
        rows.append(_row(n_courses + offset, z_cm, length_cm,
                         pieces=[(0.0, 39.0)], wall_id=wall_id))
    return model.make_wall(wall_id, (0, y_cm), (length_cm, y_cm), 14.0,
                           base_z_cm=base_z_cm, height_cm=height_cm,
                           openings=list(openings or []), junctions=[],
                           rows=rows)


def _project(walls, expected_rows=17):
    project = model.make_project(
        "cr_c1", "solver", walls=list(walls),
        settings={"base_z_cm": 0.0, "course_step_cm": STEP_CM,
                  "block_height_cm": BLOCK_H_CM, "num_courses": expected_rows,
                  "expected_rows": expected_rows},
        catalog={"B39": {"length_cm": 39.0, "height_cm": BLOCK_H_CM,
                         "width_cm": 14.0}},
    )
    return model.assign_ids(project)


def _missing_row_findings(project):
    return [f for f in VC.validate(project) if f["code"] == "COVERAGE_MISSING_ROW"]


def _codes(findings):
    return sorted(f["code"] for f in findings)


# ============================================================
# 1 - O DEFEITO: parede fisicamente completa, mas mais baixa
# ============================================================

@pytest.mark.parametrize("height_cm,n_courses", [
    (220.0, 11),   # 200 + 19 = 219 <= 220; nao cabe fiada em 220
    (260.0, 13),   # o caso dominante do corpus (69 de 97 paredes no TGD)
    (280.0, 14),
])
def test_parede_baixa_e_completa_nao_e_acusada(height_cm, n_courses):
    """FALHA antes da CR-C1: `len(fiadas) < expected_rows` (17 global)
    acusava toda parede mais baixa que o pe-direito do projeto."""
    project = _project([_wall(height_cm, n_courses)], expected_rows=17)
    assert _missing_row_findings(project) == [], (
        "parede de %scm com %d fiadas esta' completa e nao pode ser acusada"
        % (height_cm, n_courses))


def test_paredes_de_alturas_diferentes_no_mesmo_projeto():
    """O caso que define a CR: um unico `expected_rows` nao serve para
    paredes de alturas diferentes."""
    walls = [_wall(220.0, 11, wall_id="W001"),
             _wall(260.0, 13, wall_id="W002"),
             _wall(280.0, 14, wall_id="W003")]
    assert _missing_row_findings(_project(walls, expected_rows=17)) == []


def test_fiada_de_topo_encostada_no_pe_direito_fora_do_grid():
    """No gabarito real a fiada do topo NAO segue o passo: 281cm fecha em
    z=261 (canaleta de 29cm abaixo). Nao pode ser acusada."""
    wall = _wall(281.0, 13, extra_rows=(261.0,))
    assert _missing_row_findings(_project([wall], expected_rows=17)) == []


def test_faixa_intercalada_de_abertura_nao_muda_o_veredito():
    """Faixas em cotas nao-modulares (z=150/170/190) sao vergas/
    contravergas - adicionais legitimos, nunca a fiada do topo."""
    janela = model.make_opening(model.OPENING_WINDOW, 100.0, 220.0, 160.0, 240.0)
    wall = _wall(260.0, 13, extra_rows=(150.0, 230.0), openings=[janela])
    assert _missing_row_findings(_project([wall], expected_rows=17)) == []


# ============================================================
# 2 - ANTI-TAUTOLOGIA: ausencia REAL continua acusada
# ============================================================

def test_ausencia_real_de_fiada_no_topo_continua_acusada():
    """O criterio nao pode virar "espera-se o que ja' esta' la'": uma
    parede de 260cm que para em z=100 tem 6 fiadas faltando."""
    project = _project([_wall(260.0, 6)], expected_rows=17)
    findings = _missing_row_findings(project)
    assert len(findings) == 1, findings
    assert findings[0]["missing_course_z_cm"] == 120.0, findings[0]
    assert findings[0]["wall_top_z_cm"] == 260.0, findings[0]


def test_falta_exatamente_a_ultima_fiada():
    """O caso de fronteira: cabe UMA fiada e ela nao esta' la'."""
    project = _project([_wall(260.0, 12)], expected_rows=17)
    findings = _missing_row_findings(project)
    assert len(findings) == 1, findings
    assert findings[0]["missing_course_z_cm"] == 240.0, findings[0]


def test_solver_que_parou_na_metade_e_acusado_mesmo_com_expected_rows_baixo():
    """Antes da CR-C1 um `expected_rows` pequeno escondia o truncamento;
    agora quem decide e' a altura fisica da parede."""
    project = _project([_wall(260.0, 3)], expected_rows=2)
    assert len(_missing_row_findings(project)) == 1


# ============================================================
# 3 - BASE Z: o corpus tem um nivel inteiro deslocado (TP1)
# ============================================================

def test_base_z_deslocada_parede_completa_nao_e_acusada():
    """TP1 real: `base_z_cm = 612`. A cota e' ABSOLUTA."""
    wall = _wall(260.0, 13, base_z_cm=612.0)
    assert _missing_row_findings(_project([wall], expected_rows=17)) == []


def test_base_z_deslocada_ausencia_real_continua_acusada():
    wall = _wall(260.0, 6, base_z_cm=612.0)
    findings = _missing_row_findings(_project([wall], expected_rows=17))
    assert len(findings) == 1, findings
    assert findings[0]["missing_course_z_cm"] == 612.0 + 120.0, findings[0]
    assert findings[0]["wall_top_z_cm"] == 612.0 + 260.0, findings[0]


# ============================================================
# 4 - CONTRATO: o que NAO pode mudar
# ============================================================

def test_expected_rows_global_nao_decide_mais_o_achado():
    """Mesma parede, dois `expected_rows` absurdamente diferentes: o
    veredito fisico e' o mesmo."""
    wall_kwargs = dict(height_cm=260.0, n_courses=13)
    baixo = _missing_row_findings(_project([_wall(**wall_kwargs)], expected_rows=1))
    alto = _missing_row_findings(_project([_wall(**wall_kwargs)], expected_rows=999))
    assert baixo == [] and alto == [], (baixo, alto)


def test_fiada_faltando_no_meio_da_pilha_continua_acusada():
    """Controle: o outro ramo de `COVERAGE_MISSING_ROW` nao foi tocado."""
    wall = _wall(260.0, 13)
    wall["rows"][5]["blocks"] = []
    findings = _missing_row_findings(_project([wall], expected_rows=17))
    assert len(findings) == 1, findings
    assert findings[0]["row"] == 5, findings[0]


def test_parede_sem_altura_declarada_fica_sem_veredito():
    """Sem pe-direito nao ha' com o que comparar - e chutar a altura a
    partir das fiadas existentes tornaria o criterio tautologico."""
    wall = _wall(260.0, 6)
    wall["height_cm"] = None
    assert _missing_row_findings(_project([wall], expected_rows=17)) == []


def test_parede_sem_bloco_nenhum_continua_critica():
    """Controle: `COVERAGE_WALL_NOT_MODULATED` cobre a parede inteira e
    sai antes deste ramo."""
    wall = _wall(260.0, 0)
    codes = _codes(VC.validate(_project([wall], expected_rows=17)))
    assert "COVERAGE_WALL_NOT_MODULATED" in codes
    assert "COVERAGE_MISSING_ROW" not in codes


def test_invariancia_a_ordem_de_entrada_das_paredes():
    """O veredito e' por parede; a ordem da lista nao pode muda-lo.

    Comparado por IDENTIDADE FISICA (eixo da parede + cota), nunca pelo
    rotulo `W0xx` - que `assign_ids` deriva da ordem geometrica e portanto
    NAO e' identidade estavel (mesmo achado da CR-B)."""
    def vereditos(walls):
        project = _project(walls, expected_rows=17)
        por_id = dict((w["id"], tuple(w["start_cm"])) for w in project["walls"])
        return sorted((por_id[f["wall"]], f.get("missing_course_z_cm"))
                      for f in _missing_row_findings(project))
    a = _wall(260.0, 13, wall_id="WA", y_cm=0.0)
    b = _wall(260.0, 6, wall_id="WB", y_cm=100.0)
    c = _wall(220.0, 11, wall_id="WC", y_cm=200.0)
    assert vereditos([a, b, c]) == vereditos([c, b, a]) == vereditos([b, a, c])


def test_resultado_e_deterministico_em_execucoes_repetidas():
    walls = [_wall(260.0, 13, wall_id="W001"), _wall(260.0, 6, wall_id="W002")]
    saidas = {json.dumps(_missing_row_findings(_project(walls, expected_rows=17)),
                         sort_keys=True) for _ in range(3)}
    assert len(saidas) == 1


# ============================================================
# 5 - CORPUS REAL: o validador nao pode acusar a propria referencia
# ============================================================

@pytest.mark.parametrize("project_id", ["torre_easy_lo_r00_tgd",
                                        "torre_easy_lo_r00_tp1"])
def test_gabarito_humano_real_nao_tem_fiada_de_topo_faltando(project_id):
    """FALHA antes da CR-C1 com 95 (TGD) / 94 (TP1) achados - os mesmos
    numeros que o `reference_score.json` oficial registra."""
    path = os.path.join(PROJECTS_DIR, project_id, "reference.json")
    if not os.path.exists(path):
        pytest.skip("%s sem reference.json" % project_id)
    with open(path, encoding="utf-8") as handle:
        reference = json.load(handle)
    # `row is None` distingue o ramo do TOPO do ramo do meio da pilha nas
    # DUAS arvores (antes e depois da CR-C1) - filtrar por um campo que so'
    # existe depois do fix faria o teste passar na base por vacuidade.
    topo = [f for f in _missing_row_findings(reference) if f.get("row") is None]
    assert topo == [], "%s: %d fiadas de topo acusadas no gabarito HUMANO" % (
        project_id, len(topo))
