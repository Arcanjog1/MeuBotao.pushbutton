# -*- coding: utf-8 -*-
"""SECAO 74 - o teste de espaco do T compara com tolerancia FISICA.

`_t_intersection_room_ok` pergunta "cabe um B54 centrado no no'?" e reprovava
quando o espaco medido ficava abaixo de 27 cm por QUALQUER margem - a
comparacao usava `+ 1e-6` PES, 0,3 micrometro. Isso nao e' uma tolerancia
fisica: e' o epsilon de ponto flutuante. A junta de argamassa do sistema tem
10 mm, e a geometria do encontro chega com ruido acumulado de varias conversoes
pes<->cm.

O ponto destes testes NAO e' "passar a aceitar mais": e' que a MESMA situacao
fisica deixe de ser decidida pelo SINAL do ruido. Quem nao cabe de verdade
continua reprovando - e isso e' testado explicitamente.

A tolerancia usada e' PIER_PHYSICAL_FIT_TOLERANCE_CM, a constante que o motor ja'
define para "o quanto uma peca JA' MATERIALIZADA pode ultrapassar o limite
FISICO real do trecho". Nenhum numero novo.

    python3 -m pytest tests/test_t_room_physical_tolerance.py -q
"""
import contextlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_block_node_fill_revalidation as NF  # noqa: E402

m = NF.m
ws = sys.modules["core.engine.wall_stepper"]
seg, ft = NF.seg, NF.ft
CATALOG = NF.CATALOG
CM_POR_PE = 100.0 / m.FEET_PER_METER
EXIGE_CM = ws.T_INTERSECTION_B54_HALF_ROOM_FT * CM_POR_PE     # 27,0 cm


@contextlib.contextmanager
def secao74(ligada):
    antes = ws.T_ROOM_PHYSICAL_TOLERANCE
    ws.T_ROOM_PHYSICAL_TOLERANCE = ligada
    try:
        yield
    finally:
        ws.T_ROOM_PHYSICAL_TOLERANCE = antes


def t_com_espaco(falta_cm, comprimento=300.0, dx=0.0, dy=0.0, invertida=False, ordem=None):
    """Um T em que o espaco da PRINCIPAL de um dos lados e' (27 - falta) cm.

    Medido: nesta topologia o espaco do lado curto e' exatamente `t`, a posicao
    do encontro ao longo da principal - entao `falta` e' pedida direto."""
    t = EXIGE_CM - falta_cm
    principal = (seg(dx, dy, comprimento + dx, dy) if not invertida
                 else seg(comprimento + dx, dy, dx, dy))
    linhas = [principal, seg(t + dx, dy, t + dx, dy + 200.0)]
    if ordem is not None:
        linhas = [linhas[i] for i in ordem]
    paredes = [(l, ft(14.0), (False, False)) for l in linhas]
    paredes, jm = m.extend_wall_ends_to_junctions(paredes, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(paredes, jm)
    per = dict((i, []) for i in range(len(paredes)))
    return paredes, nodes, e2n, per


def cabe(falta_cm, **kw):
    paredes, nodes, e2n, per = t_com_espaco(falta_cm, **kw)
    for i, n in enumerate(nodes):
        if n.get("kind") != "T_INTERSECTION":
            continue
        return bool(ws._t_intersection_room_ok(n, paredes, per, nodes=nodes,
                                               end_to_node=e2n, node_index=i))
    raise AssertionError("a fixture precisa produzir um T_INTERSECTION")


def espaco_medido(falta_cm, **kw):
    paredes, nodes, e2n, per = t_com_espaco(falta_cm, **kw)
    for i, n in enumerate(nodes):
        if n.get("kind") != "T_INTERSECTION":
            continue
        a = ws._t_intersection_room_assessment(n, paredes, per, nodes=nodes,
                                               end_to_node=e2n, node_index=i)
        return min(a["room_plus_ft"], a["room_minus_ft"]) * CM_POR_PE
    raise AssertionError("sem T")


# ================================================== 1. a fixture mede o que diz
def test_a_fixture_controla_o_espaco_em_centesimos_de_milimetro():
    for falta in (0.0, 0.003, 0.05, 4.0):
        medido = espaco_medido(falta)
        assert abs((EXIGE_CM - medido) - falta) < 1e-6, (falta, medido)


# ============================================ 2. o portao NAO foi afrouxado
def test_quem_nao_cabe_de_verdade_continua_reprovando():
    """4 cm de falta e' a margem real dos nos 19/20/39 do projeto - continua
    reprovando nos DOIS estados. A secao 74 nao abre a porta para eles.

    Medido: acima de ~9 cm de falta o encontro deixa de ser T nesta fixture
    (cai perto da ponta da principal e o motor o classifica como canto L), entao
    a faixa testada para em 8 cm."""
    for falta in (2.0, 4.0, 6.0, 8.0):
        with secao74(False):
            assert not cabe(falta), falta
        with secao74(True):
            assert not cabe(falta), falta


def test_uma_falta_maior_que_a_tolerancia_continua_reprovando():
    tol = ws.PIER_PHYSICAL_FIT_TOLERANCE_CM
    with secao74(True):
        assert not cabe(tol * 4.0)
        assert cabe(tol / 10.0)


# ====================================== 3. o argumento central: consistencia
def test_sem_a_secao_74_o_sinal_do_ruido_decide():
    """VERMELHO: duas geometrias identicas a menos de 35 MICROMETROS - uma para
    cada lado dos 27 cm - recebem vereditos OPOSTOS. E' o caso real dos nos
    12 x 44/46 (8284515) e 26 x 24 (8284526) do projeto."""
    ruido = 0.0035
    with secao74(False):
        assert cabe(-ruido), "sobrando 35 um deveria passar"
        assert not cabe(+ruido), "faltando 35 um reprovava - e' o defeito"


def test_com_a_secao_74_as_duas_recebem_o_mesmo_veredito():
    """VERDE: a mesma situacao fisica passa a ser decidida pela geometria."""
    for ruido in (0.0035, 0.012):
        with secao74(True):
            assert cabe(-ruido) and cabe(+ruido), ruido


# ================================== 4. a tolerancia e' a constante do motor
def test_a_tolerancia_e_a_constante_fisica_ja_existente():
    with secao74(True):
        esperado = ws.PIER_PHYSICAL_FIT_TOLERANCE_CM / 100.0 * m.FEET_PER_METER
        assert abs(ws._t_intersection_room_tolerance_ft() - esperado) < 1e-12
    with secao74(False):
        assert ws._t_intersection_room_tolerance_ft() == 1e-6


def test_flag_desligada_por_padrao_no_motor():
    assert ws.T_ROOM_PHYSICAL_TOLERANCE is False


# ============================== 5. invariancia de apresentacao da geometria
def test_o_veredito_nao_depende_de_como_a_geometria_e_apresentada():
    ruido = 0.0035
    with secao74(True):
        base = cabe(ruido)
        assert base is True
        assert cabe(ruido, dx=1234.0, dy=-567.0) == base      # transladada
        assert cabe(ruido, invertida=True) == base            # pontas invertidas
        assert cabe(ruido, ordem=(1, 0)) == base              # ordem permutada
        assert cabe(ruido, comprimento=500.0) == base         # principal mais longa


def test_determinismo_em_repeticao():
    with secao74(True):
        assert cabe(0.0035) == cabe(0.0035) == cabe(0.0035)


# ============================================ 6. consequencia na composicao
def test_o_no_que_passa_a_caber_ganha_a_amarracao_de_verdade():
    """Sem a secao 74 o no' degrada; com ela ele recebe o B54 da principal e o
    B34 da que chega - a amarracao que a geometria sempre permitiu."""
    def codigos_do_no(ligada):
        with secao74(ligada):
            paredes, nodes, e2n, per = t_com_espaco(0.0035)
            res = m.solve_building_blocks(nodes, paredes, e2n, per, CATALOG)
            saida = []
            for c in res["candidates"]:
                if c.get("node_index") is None:
                    continue
                saida.append((c.get("logical_code"), str(c.get("placement_reason") or "")))
            return sorted(saida)

    sem = codigos_do_no(False)
    com = codigos_do_no(True)
    assert sem != com
    assert not any(code == "B54" for code, _r in sem), sem
    assert any(code == "B54" for code, _r in com), com
    assert any(r.startswith("T_INTERSECTION_MAIN") for _c, r in com), com
