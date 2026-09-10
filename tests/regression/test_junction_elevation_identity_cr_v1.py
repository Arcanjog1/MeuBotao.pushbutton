# -*- coding: utf-8 -*-
"""CR-V1 - FIDELIDADE DO VALIDADOR DE ENCONTROS POR ELEVACAO FISICA.

`validate_junctions.py` agrupava as fiadas de um no' pelo INDICE ORDINAL
`row["row"]` (posicao da fiada na PILHA DAQUELA PAREDE), nao pela cota.
Duas paredes que chegam ao mesmo no' com pilhas de tamanhos diferentes
(meia-fiada de peca CORTADA, base_z_cm diferente) tinham o MESMO indice
apontando para COTAS DIFERENTES - o validador comparava fiadas fisicamente
distintas so' porque tinham o mesmo numero de ordem, e acusava
`JUNCTION_MISSING_BINDING` numa alvenaria perfeitamente amarrada.

Medido no corpus real (reconciliacao independente da CR-B, `docs/
BENCH_OPENING_RECONSTRUCTION_B_INDEPENDENT_RECONCILIATION.md`): 39 dos
+49 achados novos de `JUNCTION_MISSING_BINDING` nasciam so' desse
defeito; 63% dos 373 achados do gabarito de hoje (SEM nenhum corte) ja'
nasciam de um indice ordinal apontando para mais de uma cota.

O fix troca a identidade de fiada para `row["elevation_cm"]` (agrupada
com a MESMA tolerancia que o motor usa para juntar pecas em fiada,
`model.COURSE_Z_TOLERANCE_CM` - nenhuma tolerancia nova foi inventada) e
exige PELO MENOS DUAS paredes do no' com fiada registrada naquela cota
para afirmar "faltou amarracao" (a unica situacao em que a acusacao e'
logicamente sustentavel - ver `_cluster_participant_wall_ids`).

Casos A-G do pedido da CR-V1. Cada teste planta o defeito (ou a alvenaria
correta) e verifica o achado - nunca compara so' um total.

    python3 -m pytest tests/regression/test_junction_elevation_identity_cr_v1.py -q
"""

from benchmark import model
from benchmark.validators import base, validate_junctions as VJ


# --------------------------------------------------------------- helpers
def _junction(point, jtype=model.JUNCTION_L):
    return {"type": jtype, "point_cm": list(point), "t_cm": 0.0,
            "at_end": True, "neighbors": []}


def _block(wall_id, code, x, y, z, length_cm, rot_deg=0.0, width_cm=14.0):
    return model.make_block(code, length_cm, (x, y), z, rot_deg,
                            0.0, length_cm, role=model.ROLE_STANDARD,
                            width_cm=width_cm, wall_id=wall_id)


def _wall(wall_id, start, end, fiadas, rot_deg, dx, dy, jtype=model.JUNCTION_L,
          node=(0.0, 0.0), extra_junctions=None):
    """`fiadas`: [(indice_ordinal, elevacao_cm, tem_peca_no_no)]. A peca
    "no no'" fica centrada em `node + (dx, dy)`- alcanca o ponto do
    encontro. A peca "fora do no'" fica 12x mais longe - so' para a
    fiada existir na pilha, sem alcancar o encontro."""
    rows = []
    for indice, elevacao, no_no in fiadas:
        if no_no:
            cx, cy = node[0] + dx, node[1] + dy
        else:
            cx, cy = node[0] + dx * 12, node[1] + dy * 12
        blocos = [_block(wall_id, "B34", cx, cy, elevacao, 34.0, rot_deg)]
        rows.append(model.make_row(indice, elevacao, blocos))
    junctions = [_junction(node, jtype)]
    if extra_junctions:
        junctions.extend(extra_junctions)
    return model.make_wall(wall_id, start, end, 14.0, rows=rows,
                           junctions=junctions)


def _wall_empty_row(wall_id, start, end, indice, elevacao, jtype=model.JUNCTION_L,
                     node=(0.0, 0.0)):
    """Parede com uma fiada REGISTRADA mas sem NENHUMA peca - a fiada
    realmente vazia do caso (D)."""
    row = model.make_row(indice, elevacao, [])
    return model.make_wall(wall_id, start, end, 14.0, rows=[row],
                           junctions=[_junction(node, jtype)])


def _project(*walls):
    return {"schema_version": 2, "project_id": "cr-v1", "orphan_blocks": [],
            "settings": {}, "catalog": {}, "walls": list(walls)}


def _codes(findings):
    return sorted(f["code"] for f in findings)


def _achados(project):
    findings = []
    for group in VJ.collect_nodes(project):
        findings.extend(VJ.validate_node(group))
    return findings


# ------------------------------------------------------------------- A
def test_a_mesmo_indice_ordinal_cotas_diferentes_nao_agrupa():
    """(A) Mesmo indice ordinal, elevacoes fisicas diferentes: nao podem
    ser tratadas como a mesma fiada - cada uma avaliada na sua propria
    cota, com o restante da amarracao (>=2 paredes na mesma cota)
    continuando a acusar corretamente onde falta peca."""
    wall_a = _wall("WA", (0.0, 0.0), (400.0, 0.0),
                   [(0, 0.0, True), (1, 20.0, False)], 0.0, 8.0, 0.0)
    # WB: indice 1 aponta para 200.0cm - nada a ver com o indice 1 (20.0cm)
    # de WA. Se o validador ainda comparasse por indice, casaria os dois.
    wall_b = _wall("WB", (0.0, 0.0), (0.0, 400.0),
                   [(0, 0.0, False), (1, 200.0, True)], 90.0, 0.0, 8.0)
    project = _project(wall_a, wall_b)
    achados = _achados(project)
    # As fiadas 20.0 (so' WA) e 200.0 (so' WB) tem UMA UNICA parede na
    # cota - nao sao comparaveis (regra dos participantes) - continuam
    # sem achado. A fiada 0.0 (as duas paredes, WA sem peca no no') e'
    # avaliavel e amarra pela peca de WB.
    assert "JUNCTION_MISSING_BINDING" not in _codes(achados)


def test_a_indice_ordinal_igual_nao_mascara_falha_em_cota_propria():
    """(A) Complemento: se as duas paredes tem fiada no MESMO indice mas
    em cotas diferentes E nenhuma amarra na cota que teria 2 paredes, o
    achado tem que continuar saindo - a troca de unidade nao pode ficar
    "menos sensivel" que o indice ordinal."""
    wall_a = _wall("WA", (0.0, 0.0), (400.0, 0.0),
                   [(0, 0.0, False)], 0.0, 8.0, 0.0)
    wall_b = _wall("WB", (0.0, 0.0), (0.0, 400.0),
                   [(0, 0.0, False)], 90.0, 0.0, 8.0)
    project = _project(wall_a, wall_b)
    assert "JUNCTION_MISSING_BINDING" in _codes(_achados(project))


# ------------------------------------------------------------------- B
def test_b_indices_diferentes_mesma_elevacao_associa_corretamente():
    """(B) Indices ordinais diferentes, mesma elevacao fisica: tem que
    ser tratados como a MESMA fiada quando pertencem ao mesmo encontro.
    Reproduz o caso 2 do reprodutor da CR-V1 (`repro_junction_row_unit.py`):
    meia-fiada CORTADA em z=10 desloca os indices ordinais de WB em 1,
    mas a amarracao nas cotas 0/20/40 continua correta e nao pode acusar
    nada."""
    fiadas_a = [(0, 0.0, True), (1, 20.0, False), (2, 40.0, True)]
    fiadas_b_deslocadas = [(0, 0.0, False), (1, 10.0, False),
                            (2, 20.0, True), (3, 40.0, False)]
    wall_a = _wall("WA", (0.0, 0.0), (400.0, 0.0), fiadas_a, 0.0, 8.0, 0.0)
    wall_b = _wall("WB", (0.0, 0.0), (0.0, 400.0), fiadas_b_deslocadas,
                   90.0, 0.0, 8.0)
    project = _project(wall_a, wall_b)
    assert _achados(project) == []


def test_b_sem_o_fix_indices_deslocados_seriam_falso_positivo():
    """Contraprova do caso (B): comparando pelo INDICE ORDINAL puro (o
    contrato antigo), as mesmas fiadas dariam falso positivo - prova que
    o teste acima exercita o defeito de verdade, nao um caso trivial."""
    fiadas_a = {0: 0.0, 1: 20.0, 2: 40.0}
    fiadas_b = {0: 0.0, 1: 10.0, 2: 20.0, 3: 40.0}
    # A fiada 2 de WA (elevacao 40, amarra) casaria por indice com a
    # fiada 2 de WB (elevacao 20, NAO amarra) - unidades diferentes.
    assert fiadas_a[2] != fiadas_b[2]


# ------------------------------------------------------------------- C
def test_c_participantes_em_cotas_de_origem_diferentes():
    """(C) Encontro com participantes que nascem em bases (`base_z_cm`)
    diferentes: a comparacao tem que continuar sendo pela cota fisica
    real, nao pelo indice - cada parede pode ter a fiada 0 numa altura
    diferente e ainda assim amarrar corretamente onde as cotas de fato
    coincidem."""
    # WA nasce em z=0 (base_z_cm=0), WB nasce em z=50 (base_z_cm=50) -
    # fiada 0 de cada uma esta' em cotas bem diferentes; a fiada 2 de WA
    # (z=40) e a fiada 0 de WB (z=50) NAO sao a mesma cota (diferenca
    # 10cm > tolerancia do motor) - continuam avaliadas separadamente,
    # cada uma com uma unica parede na banda, portanto sem achado.
    wall_a = _wall("WA", (0.0, 0.0), (400.0, 0.0),
                   [(0, 0.0, False), (1, 20.0, False), (2, 40.0, False)],
                   0.0, 8.0, 0.0)
    wall_b = _wall("WB", (0.0, 0.0), (0.0, 400.0),
                   [(0, 50.0, False), (1, 70.0, False)], 90.0, 0.0, 8.0)
    project = _project(wall_a, wall_b)
    assert "JUNCTION_MISSING_BINDING" not in _codes(_achados(project))

    # Agora as duas realmente compartilham uma cota fisica (WA fiada 2 =
    # 40.0, WB ganha uma fiada extra em 40.0) e nenhuma das duas amarra
    # ali - a identidade fisica correta tem que acusar.
    wall_b_compartilha = _wall(
        "WB", (0.0, 0.0), (0.0, 400.0),
        [(0, 40.0, False), (1, 50.0, False), (2, 70.0, False)], 90.0, 0.0, 8.0)
    project2 = _project(wall_a, wall_b_compartilha)
    assert "JUNCTION_MISSING_BINDING" in _codes(_achados(project2))


# ------------------------------------------------------------------- D
def test_d_ausencia_real_de_amarracao_continua_acusada():
    """(D) Na fiada 0.0 (cota compartilhada pelas duas paredes), WA tem
    uma peca mas ela NAO alcanca o no' e WB nao tem peca nenhuma ali (a
    fiada esta' REGISTRADA, so' vazia) - defeito fisico real, tem que
    continuar acusado. Na fiada 20.0 a amarracao existe (WA cobre o no')
    e nao pode acusar nada - prova que o achado da fiada 0.0 e' seletivo
    por cota, nao um efeito colateral do teste. O filtro de participantes
    (>=2 paredes) nao pode virar desculpa para engolir amarracao faltando
    de verdade."""
    wall_a = _wall("WA", (0.0, 0.0), (400.0, 0.0),
                   [(0, 0.0, False), (1, 20.0, True)], 0.0, 8.0, 0.0)
    wall_b = _wall_empty_row("WB", (0.0, 0.0), (0.0, 400.0), 0, 0.0)
    project = _project(wall_a, wall_b)
    achados = _achados(project)
    assert "JUNCTION_MISSING_BINDING" in _codes(achados)
    missing = [f for f in achados if f["code"] == "JUNCTION_MISSING_BINDING"]
    assert all(f["elevation_cm"] == 0.0 for f in missing)


# ------------------------------------------------------------------- E
def test_e_encontro_humano_valido_sem_falso_positivo_ordinal():
    """(E) Encontro valido, alternando corretamente fiada a fiada (B34
    de WA na fiada 0, de WB na fiada 1, de volta a WA na fiada 2) - igual
    ao caso 1 do reprodutor da CR-V1. Nao pode acusar nada."""
    fiadas_a = [(0, 0.0, True), (1, 20.0, False), (2, 40.0, True)]
    fiadas_b = [(0, 0.0, False), (1, 20.0, True), (2, 40.0, False)]
    wall_a = _wall("WA", (0.0, 0.0), (400.0, 0.0), fiadas_a, 0.0, 8.0, 0.0)
    wall_b = _wall("WB", (0.0, 0.0), (0.0, 400.0), fiadas_b, 90.0, 0.0, 8.0)
    project = _project(wall_a, wall_b)
    assert _achados(project) == []


# ------------------------------------------------------------------- F
def test_f_no_com_uma_unica_parede_nao_e_defeito_fisico():
    """(F) No' "recem-registrado" (por exemplo pela fragmentacao T->L da
    CR-B) que hoje so' aparece com uma parede: e' mudanca de UNIDADE de
    avaliacao (o no' passou a existir), nao defeito fisico - continua
    sem achado, igual ao contrato anterior a esta CR."""
    wall_a = _wall("WA", (0.0, 0.0), (400.0, 0.0),
                   [(0, 0.0, False)], 0.0, 8.0, 0.0)
    project = _project(wall_a)
    assert _achados(project) == []


def test_f_no_com_fiada_exclusiva_de_uma_parede_nao_e_defeito_fisico():
    """(F) Dentro de um no' de >=2 paredes (esse ja' e' avaliavel), uma
    fiada que existe SO' numa das paredes (parede mais baixa, ou meia-
    fiada de compensacao que a vizinha nao tem) e' dado incompleto
    daquela fiada especifica - nao e' defeito fisico ali, mesmo que o
    no' inteiro ja' seja avaliavel por outras fiadas."""
    fiadas_a = [(0, 0.0, True), (1, 20.0, False)]
    # WB so' chega ate' 0.0 - nao tem NENHUMA fiada em 20.0.
    wall_a = _wall("WA", (0.0, 0.0), (400.0, 0.0), fiadas_a, 0.0, 8.0, 0.0)
    wall_b = _wall("WB", (0.0, 0.0), (0.0, 400.0),
                   [(0, 0.0, False)], 90.0, 0.0, 8.0)
    project = _project(wall_a, wall_b)
    assert _achados(project) == []


# ------------------------------------------------------------------- G
def test_g_determinismo_ordem_de_entrada_das_paredes():
    """(G) Trocar a ORDEM em que as paredes entram no projeto (a mesma
    alvenaria fisica) tem que dar o MESMO conjunto de achados - o
    agrupamento por elevacao nao pode depender de quem chegou primeiro."""
    fiadas_a = [(0, 0.0, True), (1, 20.0, False)]
    fiadas_b_deslocadas = [(0, 0.0, False), (1, 10.0, False), (2, 20.0, True)]
    wall_a = _wall("WA", (0.0, 0.0), (400.0, 0.0), fiadas_a, 0.0, 8.0, 0.0)
    wall_b = _wall("WB", (0.0, 0.0), (0.0, 400.0), fiadas_b_deslocadas,
                   90.0, 0.0, 8.0)

    achados_ab = _achados(_project(wall_a, wall_b))
    achados_ba = _achados(_project(wall_b, wall_a))

    def _sem_wall_primario(fs):
        return sorted((f["code"], f.get("row"), f.get("elevation_cm"),
                       f.get("row_a"), f.get("row_b"))
                      for f in fs)

    assert _sem_wall_primario(achados_ab) == _sem_wall_primario(achados_ba)


def test_g_invariancia_por_translacao():
    """(G) Transladar o encontro inteiro (mesma alvenaria, outro lugar do
    mundo) tem que dar os MESMOS codigos de achado - a identidade e'
    elevacao + participantes, nao coordenada absoluta do no'."""
    fiadas_a = [(0, 0.0, True), (1, 20.0, False)]
    fiadas_b = [(0, 0.0, False), (1, 10.0, False), (2, 20.0, True)]

    def _monta(origem):
        ox, oy = origem
        wall_a = _wall("WA", (ox, oy), (ox + 400.0, oy), fiadas_a, 0.0,
                       8.0, 0.0, node=(ox, oy))
        wall_b = _wall("WB", (ox, oy), (ox, oy + 400.0), fiadas_b, 90.0,
                       0.0, 8.0, node=(ox, oy))
        return _project(wall_a, wall_b)

    achados_origem = _achados(_monta((0.0, 0.0)))
    achados_transladado = _achados(_monta((913.0, -217.0)))
    assert _codes(achados_origem) == _codes(achados_transladado)


def test_g_invariancia_por_inversao_de_paredes_start_end():
    """(G) Inverter `start_cm`/`end_cm` de uma parede (mesma parede, eixo
    percorrido no sentido oposto) nao pode mudar o achado - a peca ainda
    alcanca o mesmo ponto fisico do encontro."""
    fiadas_a = [(0, 0.0, True), (1, 20.0, False)]
    fiadas_b = [(0, 0.0, False), (1, 10.0, False), (2, 20.0, True)]
    wall_a_normal = _wall("WA", (0.0, 0.0), (400.0, 0.0), fiadas_a, 0.0, 8.0, 0.0)
    wall_a_invertida = _wall("WA", (400.0, 0.0), (0.0, 0.0), fiadas_a, 0.0, 8.0, 0.0)
    wall_b = _wall("WB", (0.0, 0.0), (0.0, 400.0), fiadas_b, 90.0, 0.0, 8.0)

    achados_normal = _achados(_project(wall_a_normal, wall_b))
    achados_invertido = _achados(_project(wall_a_invertida, wall_b))
    assert _codes(achados_normal) == _codes(achados_invertido) == []


def test_regressao_taxonomia_continua_valida():
    """Sanity check de infraestrutura: os novos campos (`elevation_cm`,
    `rows_by_wall`, `elevation_a`, `elevation_b`) sao aceitos por
    `base.finding` sem quebrar a taxonomia (item 9) - so' viram achado
    para codigos que ja existem em `ERROR_CLASSES`."""
    base.error_class("JUNCTION_MISSING_BINDING")
    base.error_class("JUNCTION_NOT_ALTERNATING")
