# -*- coding: utf-8 -*-
"""CR-BLOCK-DETERMINISM / FINALIZACAO - invariantes permanentes do
PIPELINE de blocos (nao so' do grafo).

`tests/test_block_graph_determinism.py` congela o WALL GRAPH: mesma planta,
ordem diferente -> mesmo grafo. Esta suite congela a camada seguinte, que
aquela deixou explicitamente de fora:

    a MESMA parede fisica desenhada A->B ou B->A e' A MESMA PAREDE e tem
    que produzir exatamente a MESMA solucao fisica de blocos.

`GetEndPoint(0)`/`GetEndPoint(1)` sao detalhe de REPRESENTACAO. Eles nao
podem decidir inicio logico da parede, sequencia de preenchimento, escolha
de bloco, posicao de compensador, onde cai o B19, o reparo de abertura, as
juntas nem o resultado da fiada.

Cobre tambem as duas REGRAS FUNDAMENTAIS do motor:
  - REGRA 2 - ordem oficial de processamento ENTRE paredes;
  - REGRA 3 - parede completa primeiro, abertura depois.

Toda geometria daqui e' SINTETICA e construida no proprio teste (mesma
regra de tests/test_block_bonding.py). Nenhum teste le projeto real.

    python3 -m pytest tests/test_block_pipeline_determinism.py -q
"""

import random

import pytest

import load_script
import revit_stubs

XYZ = revit_stubs.XYZ
Line = revit_stubs.Line
m = load_script.load()
F = m.FEET_PER_METER


# --------------------------------------------------------------- helpers
def ft(cm):
    return cm / 100.0 * F


def to_cm(value_ft):
    return value_ft / F * 100.0


def seg(x0, y0, x1, y1):
    return Line.CreateBound(XYZ(ft(x0), ft(y0), 0.0), XYZ(ft(x1), ft(y1), 0.0))


def _cell(center_cm, size_cm, width_cm=8.0):
    return {"center_local": (ft(center_cm), 0.0), "size_local": (ft(size_cm), ft(width_cm))}


def _block(code, length_cm, cells):
    return {
        "symbol": None, "logical_code": code, "length_cm": float(length_cm),
        "height_cm": 19.0, "width_cm": 14.0, "cells_local": cells,
        "is_special_bond": code in ("B34", "B54"),
        "is_compensator": code in ("C09", "C04"),
        "source_instance_id": None,
    }


# B34 tem celulas ASSIMETRICAS de proposito (-10,2 / +7,4): e' o que permite
# detectar uma peca espelhada, e nao so' reposicionada (item 41 da missao).
CATALOG = {
    "B39": _block("B39", 39, [_cell(-9.9, 15.7), _cell(9.9, 15.8)]),
    "B34": _block("B34", 34, [_cell(-10.2, 10.7), _cell(7.4, 15.7)]),
    "B54": _block("B54", 54, [_cell(-19.5, 15.8), _cell(0.0, 12.5), _cell(19.5, 15.8)]),
    "B19": _block("B19", 19, [_cell(0.0, 15.7)]),
    "C09": _block("C09", 9, []),
    "C04": _block("C04", 4, []),
}


# ---------------------------------------------- identidade FISICA de peca
def _r(value_cm, places=3):
    return round(value_cm, places) + 0.0   # + 0.0 normaliza -0.0


def wall_key(walls, wall_idx):
    """Pontas ORDENADAS + espessura - independe do indice e do sentido."""
    if wall_idx is None or not (0 <= wall_idx < len(walls)):
        return None
    line, thickness_ft, _locks = walls[wall_idx]
    a = (_r(to_cm(line.GetEndPoint(0).X)), _r(to_cm(line.GetEndPoint(0).Y)))
    b = (_r(to_cm(line.GetEndPoint(1).X)), _r(to_cm(line.GetEndPoint(1).Y)))
    lo, hi = (a, b) if a <= b else (b, a)
    return (lo[0], lo[1], hi[0], hi[1], _r(to_cm(thickness_ft)))


def piece_physical_key(walls, candidate):
    """Identidade FISICA de uma peca: parede geometrica, fiada, codigo,
    CENTRO e as CELULAS em coordenadas de MUNDO.

    As celulas sao o que resolve o item 41 da missao: um B39/B54/B19 girado
    180 graus no MESMO lugar e' A MESMA PECA fisica e produz a MESMA chave;
    um B34 (assimetrico) girado 180 graus NAO e', e a chave muda - entao
    espelhar uma peca de amarracao continua sendo detectado como diferenca
    de verdade, nunca escondido pela normalizacao.

    Deliberadamente NAO usa `rotation_deg`: para peca simetrica ele difere
    em 180 graus entre duas serializacoes da MESMA peca (item 40)."""
    center = (_r(to_cm(candidate["origin_world"].X), 1),
              _r(to_cm(candidate["origin_world"].Y), 1))
    cells = tuple(sorted(
        (_r(to_cm(cell["point"].X), 1), _r(to_cm(cell["point"].Y), 1),
         _r(abs(to_cm(cell["size_local"][0])), 1), _r(abs(to_cm(cell["size_local"][1])), 1))
        for cell in candidate.get("cells_world") or []
    ))
    return (wall_key(walls, candidate.get("wall_idx")), candidate["course"],
            candidate["logical_code"], center, cells)


def physical_fingerprint(walls, result):
    return sorted(piece_physical_key(walls, c) for c in result["candidates"])


# --------------------------------------------------------------- solver
def plan(raw_lines, thickness_cm=14.0, openings=None):
    """(walls_to_create, nodes, end_to_node, openings_per_wall) ja' com as
    pontas esticadas ate' os encontros - o mesmo caminho do fluxo real."""
    walls = [(line, ft(thickness_cm), (False, False)) for line in raw_lines]
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    per_wall = [list((openings or {}).get(i, [])) for i in range(len(walls))]
    return walls, nodes, end_to_node, per_wall


def solve(walls, nodes, end_to_node, per_wall, **kwargs):
    return m.solve_building_blocks(nodes, walls, end_to_node, per_wall, CATALOG, **kwargs)


def flip_wall(walls, per_wall, wall_idx):
    """A MESMA parede fisica com as pontas trocadas, com as aberturas dela
    REPARAMETRIZADAS contra o comprimento REAL do eixo (`t' = L - t`).

    Reparametrizar contra o comprimento do eixo JA ESTICADO (e nao contra o
    comprimento cru de antes de `extend_wall_ends_to_junctions`) e' o que
    faz a variante descrever a MESMA geometria: com o comprimento errado a
    abertura muda de lugar fisicamente e o teste passaria a comparar duas
    plantas diferentes."""
    line, thickness_ft, locks = walls[wall_idx]
    p0, p1 = line.GetEndPoint(0), line.GetEndPoint(1)
    length_ft = p0.DistanceTo(p1)
    new_walls = list(walls)
    new_walls[wall_idx] = (Line.CreateBound(XYZ(p1.X, p1.Y, p1.Z), XYZ(p0.X, p0.Y, p0.Z)),
                           thickness_ft, (locks[1], locks[0]))
    new_openings = [list(entry) for entry in per_wall]
    new_openings[wall_idx] = sorted(
        ((length_ft - op[1], length_ft - op[0]) + tuple(op[2:]))
        for op in per_wall[wall_idx]
    )
    return new_walls, new_openings


def solve_both_senses(raw_lines, openings=None, flip_indexes=None, **kwargs):
    """Resolve a MESMA planta duas vezes: no sentido original e com os eixos
    de `flip_indexes` (todos, por padrao) desenhados ao contrario. Devolve
    os dois fingerprints FISICOS."""
    walls, nodes, end_to_node, per_wall = plan(raw_lines, openings=openings)
    base = solve(walls, nodes, end_to_node, per_wall, **kwargs)

    targets = range(len(walls)) if flip_indexes is None else flip_indexes
    flipped_walls, flipped_openings = walls, per_wall
    for wall_idx in targets:
        flipped_walls, flipped_openings = flip_wall(flipped_walls, flipped_openings, wall_idx)
    # O grafo e' reconstruido do zero sobre a geometria invertida - nada de
    # reaproveitar `nodes`/`end_to_node`, que carregariam `end_index` antigo.
    f_nodes, f_end_to_node = m.build_wall_graph(flipped_walls, {})
    flipped = solve(flipped_walls, f_nodes, f_end_to_node, flipped_openings, **kwargs)

    return (physical_fingerprint(walls, base),
            physical_fingerprint(flipped_walls, flipped))


# =====================================================================
# 1. DIRECAO CANONICA DENTRO DA PAREDE
# =====================================================================

def test_INV_DET_001_direcao_canonica_horizontal_e_esquerda_para_direita():
    walls = [(seg(500, 30, 100, 30), ft(14.0), (False, False))]
    start, end, direction, _len, _th = m.canonical_wall_axis(walls, 0)
    assert m.wall_axis_is_reversed(walls, 0) is True
    assert to_cm(start.X) == pytest.approx(100.0)
    assert to_cm(end.X) == pytest.approx(500.0)
    assert direction.X > 0


def test_INV_DET_002_direcao_canonica_vertical_e_baixo_para_cima():
    walls = [(seg(30, 500, 30, 100), ft(14.0), (False, False))]
    start, end, direction, _len, _th = m.canonical_wall_axis(walls, 0)
    assert m.wall_axis_is_reversed(walls, 0) is True
    assert to_cm(start.Y) == pytest.approx(100.0)
    assert to_cm(end.Y) == pytest.approx(500.0)
    assert direction.Y > 0


@pytest.mark.parametrize("line", [
    seg(0, 0, 400, 0), seg(400, 0, 0, 0),          # horizontais
    seg(0, 0, 0, 400), seg(0, 400, 0, 0),          # verticais
    seg(0, 0, 300, 400), seg(300, 400, 0, 0),      # inclinadas
])
def test_INV_DET_003_eixo_canonico_e_o_mesmo_nos_dois_sentidos(line):
    """A MESMA reta desenhada nos dois sentidos tem UM eixo canonico."""
    p0, p1 = line.GetEndPoint(0), line.GetEndPoint(1)
    forward = [(line, ft(14.0), (False, False))]
    backward = [(Line.CreateBound(XYZ(p1.X, p1.Y, 0.0), XYZ(p0.X, p0.Y, 0.0)),
                 ft(14.0), (False, False))]
    a_start, a_end, a_dir, _l, _t = m.canonical_wall_axis(forward, 0)
    b_start, b_end, b_dir, _l2, _t2 = m.canonical_wall_axis(backward, 0)
    assert (_r(to_cm(a_start.X)), _r(to_cm(a_start.Y))) == \
           (_r(to_cm(b_start.X)), _r(to_cm(b_start.Y)))
    assert (_r(to_cm(a_end.X)), _r(to_cm(a_end.Y))) == \
           (_r(to_cm(b_end.X)), _r(to_cm(b_end.Y)))
    assert _r(a_dir.X, 9) == _r(b_dir.X, 9) and _r(a_dir.Y, 9) == _r(b_dir.Y, 9)


def test_INV_DET_004_direcao_canonica_nao_olha_indice_nem_ordem():
    """A mesma parede em posicoes diferentes da lista da' o mesmo veredito."""
    wall = seg(500, 30, 100, 30)
    outra = seg(0, 900, 400, 900)
    a = [(wall, ft(14.0), (False, False)), (outra, ft(14.0), (False, False))]
    b = [(outra, ft(14.0), (False, False)), (wall, ft(14.0), (False, False))]
    assert m.wall_axis_is_reversed(a, 0) == m.wall_axis_is_reversed(b, 1)


# =====================================================================
# 2. INVARIANCIA A INVERSAO DE ENDPOINTS - os 8 casos minimos da missao
# =====================================================================

L_PLANT = [seg(0, 0, 400, 0), seg(400, 0, 400, 400)]


def test_INV_DET_010_caso1_parede_simples_sem_abertura():
    base, flipped = solve_both_senses([seg(0, 0, 439, 0)])
    assert base and base == flipped


def test_INV_DET_011_caso2_parede_com_porta():
    porta = {0: [(ft(120.0), ft(210.0), ft(0.0), ft(210.0))]}
    base, flipped = solve_both_senses([seg(0, 0, 439, 0)], openings=porta)
    assert base and base == flipped


def test_INV_DET_012_caso3_parede_com_janela():
    janela = {0: [(ft(140.0), ft(260.0), ft(110.0), ft(230.0))]}
    base, flipped = solve_both_senses([seg(0, 0, 500, 0)], openings=janela)
    assert base and base == flipped


def test_INV_DET_013_caso4_parede_com_duas_aberturas():
    duas = {0: [(ft(80.0), ft(170.0), ft(0.0), ft(210.0)),
                (ft(320.0), ft(440.0), ft(110.0), ft(230.0))]}
    base, flipped = solve_both_senses([seg(0, 0, 600, 0)], openings=duas)
    assert base and base == flipped


def test_INV_DET_014_caso5_reparo_de_abertura_em_parede_com_encontro():
    """Abertura perto de um L: exercita o `_recut_openings_and_repair`, a
    camada que a cross-audit mediu como a MAIS sensivel ao sentido."""
    abertura = {0: [(ft(150.0), ft(240.0), ft(0.0), ft(210.0))]}
    base, flipped = solve_both_senses(L_PLANT, openings=abertura)
    assert base and base == flipped


@pytest.mark.parametrize("length_cm", [59, 79, 99, 119, 139, 219, 259, 339, 419])
def test_INV_DET_015_caso6_e_7_comprimentos_que_forcam_B19_e_compensador(length_cm):
    """Varre comprimentos que obrigam o solver a fechar a conta com meio
    bloco (B19) e/ou compensador (C09/C04) - as pecas cuja POSICAO era
    justamente o que mudava de ponta quando o eixo era invertido."""
    base, flipped = solve_both_senses([seg(0, 0, length_cm, 0)])
    assert base == flipped


def test_INV_DET_016_caso8_duas_fiadas_com_regra_de_prisma():
    """As duas familias A/B (a regra de prisma entre fiadas) tem que sair
    identicas nos dois sentidos - inclusive com variantes por fiada."""
    base, flipped = solve_both_senses([seg(0, 0, 439, 0)], variants_per_course=2)
    assert base and base == flipped


def test_INV_DET_017_inverter_so_uma_parede_do_L_nao_muda_o_resultado():
    for flip_indexes in ([0], [1], [0, 1]):
        base, flipped = solve_both_senses(L_PLANT, flip_indexes=flip_indexes)
        assert base == flipped, flip_indexes


def test_INV_DET_018_planta_fechada_com_T_e_X_invariante():
    plant = [
        seg(0, 0, 700, 0), seg(0, 350, 700, 350), seg(0, 700, 700, 700),
        seg(0, 0, 0, 700), seg(350, 0, 350, 700), seg(700, 0, 700, 700),
    ]
    base, flipped = solve_both_senses(plant)
    assert base and base == flipped


@pytest.mark.parametrize("seed", [1, 2, 3, 7, 42])
def test_INV_DET_019_reversao_aleatoria_de_subconjunto(seed):
    """Item 37/G4: inverter METADE das paredes, sorteada - nao so' todas."""
    plant = [
        seg(0, 0, 700, 0), seg(0, 350, 700, 350), seg(0, 700, 700, 700),
        seg(0, 0, 0, 700), seg(350, 0, 350, 700), seg(700, 0, 700, 700),
    ]
    rng = random.Random(seed)
    flip_indexes = [i for i in range(len(plant)) if rng.random() < 0.5]
    base, flipped = solve_both_senses(plant, flip_indexes=flip_indexes)
    assert base == flipped, flip_indexes


def test_INV_DET_020_peca_assimetrica_B34_nao_e_espelhada_pela_inversao():
    """Item 41: canonizar o eixo NAO pode espelhar cegamente a peca. O B34
    deste catalogo tem celulas assimetricas (-10,2 / +7,4); se a inversao
    de endpoints girasse a peca, as CELULAS em mundo mudariam e o
    fingerprint fisico acusaria."""
    base, flipped = solve_both_senses(L_PLANT)
    b34_base = [k for k in base if k[2] == "B34"]
    assert b34_base, "a planta em L precisa produzir B34 de amarracao"
    assert b34_base == [k for k in flipped if k[2] == "B34"]


# =====================================================================
# 3. ORDEM OFICIAL ENTRE PAREDES (REGRA FUNDAMENTAL 2)
# =====================================================================

ORDER_PLANT = [
    seg(0, 0, 100, 0),        # 0 H  nivel y=0 (o mais BAIXO), esquerda
    seg(300, 200, 400, 200),  # 1 H  nivel y=200 (o mais ALTO), direita
    seg(0, 200, 100, 200),    # 2 H  nivel y=200, esquerda
    seg(300, 0, 400, 0),      # 3 H  nivel y=0, direita
    seg(400, 100, 400, 200),  # 4 V  faixa y=100 (CIMA), direita
    seg(0, 0, 0, 100),        # 5 V  faixa y=0 (BAIXO), esquerda
    seg(400, 0, 400, 100),    # 6 V  faixa y=0 (BAIXO), direita
    seg(0, 100, 0, 200),      # 7 V  faixa y=100 (CIMA), esquerda
]
ORDER_EXPECTED = [2, 1, 0, 3, 5, 6, 7, 4]


def _walls_of(lines):
    return [(line, ft(14.0), (False, False)) for line in lines]


def test_INV_DET_030_horizontais_vem_antes_das_verticais():
    walls = _walls_of(ORDER_PLANT)
    order = m.order_walls_for_processing(walls)
    kinds = [m.classify_wall_orientation(walls, i) for i in order]
    assert kinds == ["H"] * 4 + ["V"] * 4


def test_INV_DET_031_horizontal_de_cima_para_baixo_e_empate_esquerda_direita():
    walls = _walls_of(ORDER_PLANT)
    order = m.order_walls_for_processing(walls)
    assert order[:4] == [2, 1, 0, 3]


def test_INV_DET_032_vertical_de_baixo_para_cima_e_empate_esquerda_direita():
    walls = _walls_of(ORDER_PLANT)
    order = m.order_walls_for_processing(walls)
    assert order[4:] == [5, 6, 7, 4]


@pytest.mark.parametrize("seed", [1, 2, 3, 10, 42, 99])
def test_INV_DET_033_ordem_oficial_independe_da_ordem_de_entrada(seed):
    """G12: embaralhar a lista nao muda a SEQUENCIA GEOMETRICA resultante."""
    walls = _walls_of(ORDER_PLANT)
    baseline = [wall_key(walls, i) for i in m.order_walls_for_processing(walls)]

    permutation = list(range(len(ORDER_PLANT)))
    random.Random(seed).shuffle(permutation)
    shuffled = _walls_of([ORDER_PLANT[i] for i in permutation])
    assert [wall_key(shuffled, i) for i in m.order_walls_for_processing(shuffled)] == baseline


def test_INV_DET_034_ordem_oficial_independe_da_inversao_de_endpoints():
    """G13: inverter o sentido de desenho de TODAS as paredes nao muda a
    posicao de nenhuma delas na ordem."""
    walls = _walls_of(ORDER_PLANT)
    baseline = [wall_key(walls, i) for i in m.order_walls_for_processing(walls)]

    flipped = _walls_of([
        Line.CreateBound(line.GetEndPoint(1), line.GetEndPoint(0)) for line in ORDER_PLANT
    ])
    assert [wall_key(flipped, i) for i in m.order_walls_for_processing(flipped)] == baseline


def test_INV_DET_035_inclinadas_vem_por_ultimo_com_chave_canonica():
    lines = [seg(0, 0, 400, 0), seg(0, 0, 0, 400),
             seg(0, 0, 300, 400), seg(500, 0, 800, 400)]
    walls = _walls_of(lines)
    order = m.order_walls_for_processing(walls)
    kinds = [m.classify_wall_orientation(walls, i) for i in order]
    assert kinds == ["H", "V", "D", "D"]

    flipped = _walls_of([Line.CreateBound(l.GetEndPoint(1), l.GetEndPoint(0)) for l in lines])
    assert [wall_key(walls, i) for i in order] == \
           [wall_key(flipped, i) for i in m.order_walls_for_processing(flipped)]
    # angulo da RETA (modulo 180): igual nos dois sentidos de desenho
    for i in range(len(lines)):
        assert m._wall_canonical_angle_deg(walls, i) == \
               m._wall_canonical_angle_deg(flipped, i)


def test_INV_DET_036_desempate_nao_usa_mais_a_posicao_na_lista():
    """Duas paredes na MESMA faixa e no MESMO x_min (comprimentos
    diferentes) desempatam por GEOMETRIA, nunca por `wall_idx`."""
    a, b = seg(0, 0, 100, 0), seg(0, 0, 200, 0)
    first = [wall_key(_walls_of([a, b]), i)
             for i in m.order_walls_for_processing(_walls_of([a, b]))]
    second = [wall_key(_walls_of([b, a]), i)
              for i in m.order_walls_for_processing(_walls_of([b, a]))]
    assert first == second


# =====================================================================
# 4. PAREDE COMPLETA PRIMEIRO, ABERTURA DEPOIS (REGRA FUNDAMENTAL 3)
# =====================================================================

def test_INV_DET_040_continuous_first_e_o_default():
    """G14: nenhum caminho de producao pode cair em `split_first` calado."""
    assert m.DEFAULT_OPENING_STRATEGY == m.OPENING_STRATEGY_CONTINUOUS_FIRST
    assert m.OPENING_STRATEGY_CONTINUOUS_FIRST == "continuous_first"
    assert m.OPENING_STRATEGY_SPLIT_FIRST == "split_first"


def test_INV_DET_041_split_first_so_roda_quando_pedido_explicitamente():
    """G15: `split_first` continua existindo (comparacao/benchmark), mas
    so' e' alcancado passando o parametro - o default nao o produz."""
    abertura = {0: [(ft(150.0), ft(240.0), ft(0.0), ft(210.0))]}
    walls, nodes, end_to_node, per_wall = plan([seg(0, 0, 600, 0)], openings=abertura)

    default = solve(walls, nodes, end_to_node, per_wall)
    explicit_continuous = solve(walls, nodes, end_to_node, per_wall,
                                opening_strategy=m.OPENING_STRATEGY_CONTINUOUS_FIRST)
    explicit_split = solve(walls, nodes, end_to_node, per_wall,
                           opening_strategy=m.OPENING_STRATEGY_SPLIT_FIRST)

    assert physical_fingerprint(walls, default) == \
           physical_fingerprint(walls, explicit_continuous)
    # `split_first` e' um MODO DIFERENTE de verdade (senao o teste acima nao
    # provaria nada): ele fatia o eixo na abertura e emite peca de jamb.
    assert explicit_split["jamb_exceptions"] or \
        physical_fingerprint(walls, explicit_split) != physical_fingerprint(walls, default)


def test_INV_DET_042_uma_parede_com_duas_aberturas_nao_vira_tres_paredes():
    """A abertura e' UM VAZIO DENTRO de uma parede continua - nao uma
    fronteira que quebra a parede em problemas independentes.

    Prova: com `continuous_first` a modulacao-base atravessa os dois vaos,
    entao as pecas de preenchimento comum NAO comecam/terminam nas bordas
    dos vaos como comecariam se cada trecho fosse resolvido isolado. O
    contraste com `split_first` (que resolve trecho a trecho) e' o que
    torna a afirmacao verificavel em vez de retorica."""
    duas = {0: [(ft(80.0), ft(170.0), ft(0.0), ft(210.0)),
                (ft(320.0), ft(440.0), ft(110.0), ft(230.0))]}
    walls, nodes, end_to_node, per_wall = plan([seg(0, 0, 600, 0)], openings=duas)

    continuous = solve(walls, nodes, end_to_node, per_wall,
                       opening_strategy=m.OPENING_STRATEGY_CONTINUOUS_FIRST)
    split = solve(walls, nodes, end_to_node, per_wall,
                  opening_strategy=m.OPENING_STRATEGY_SPLIT_FIRST)

    # No modo continuo o recorte REGISTRA o que derrubou - e' a evidencia de
    # que a parede foi modulada inteira ANTES de o vao existir.
    assert continuous["candidates"], "a parede tem que receber blocos"
    assert physical_fingerprint(walls, continuous) != physical_fingerprint(walls, split)
    # nenhuma peca pode acabar DENTRO de um vao, nos dois modos
    for op_lo, op_hi, _sill, _head in per_wall[0]:
        lo_cm, hi_cm = to_cm(op_lo), to_cm(op_hi)
        for cand in continuous["candidates"]:
            if cand.get("wall_idx") != 0:
                continue
            center_cm = to_cm(cand["origin_world"].X)
            half = cand["length_cm"] / 2.0
            assert not (lo_cm + 0.5 < center_cm - half + cand["length_cm"] - 0.5 < hi_cm - 0.5
                        and lo_cm + 0.5 < center_cm - half + 0.5 < hi_cm - 0.5), \
                "peca dentro do vao [%s, %s]" % (lo_cm, hi_cm)


def test_INV_DET_043_duas_aberturas_invariantes_a_inversao_no_modo_continuo():
    duas = {0: [(ft(80.0), ft(170.0), ft(0.0), ft(210.0)),
                (ft(320.0), ft(440.0), ft(110.0), ft(230.0))]}
    base, flipped = solve_both_senses(
        [seg(0, 0, 600, 0)], openings=duas,
        opening_strategy=m.OPENING_STRATEGY_CONTINUOUS_FIRST)
    assert base and base == flipped


# =====================================================================
# 5. NAO-REGRESSAO DO CR-BLOCK-01 (G5/G6) NOS DOIS SENTIDOS
# =====================================================================

@pytest.mark.parametrize("flip", [False, True])
def test_INV_DET_050_sem_conflito_de_alinhamento_nos_dois_sentidos(flip):
    plant = [
        seg(0, 0, 700, 0), seg(0, 350, 700, 350),
        seg(0, 0, 0, 350), seg(700, 0, 700, 350),
    ]
    walls, nodes, end_to_node, per_wall = plan(plant)
    if flip:
        for wall_idx in range(len(walls)):
            walls, per_wall = flip_wall(walls, per_wall, wall_idx)
        nodes, end_to_node = m.build_wall_graph(walls, {})
    result = solve(walls, nodes, end_to_node, per_wall, variants_per_course=2)
    assert result["alignment_conflicts"] == []


# =====================================================================
# 6. SNAP LONGITUDINAL - a grade e' fina o bastante para nao mudar decisao
# =====================================================================

def test_INV_DET_060_snap_e_ordens_de_grandeza_abaixo_de_qualquer_tolerancia():
    grade_cm = 10.0 ** -m.PIER_LENGTH_SNAP_DECIMALS
    assert grade_cm <= 1e-6
    # menor tolerancia FISICA do motor: 0,1 cm
    assert grade_cm < m.WALL_NO_GROWTH_TOLERANCE_CM / 1000.0
    assert grade_cm < m.BOND_COLLISION_EPS_CM / 1000.0
    assert grade_cm < m.BLOCK_JOINT_CM / 1000.0


def test_INV_DET_061_snap_absorve_ruido_de_ultimo_bit_e_nao_mais_que_isso():
    assert m._snap_cm(364.00899999999984) == m._snap_cm(364.0089999999998)
    assert m._snap_cm(39.0) == 39.0
    # 1mm continua sendo 1mm - o snap nao come diferenca fisica nenhuma
    assert m._snap_cm(39.1) != m._snap_cm(39.0)
    assert m._snap_cm(None) is None
