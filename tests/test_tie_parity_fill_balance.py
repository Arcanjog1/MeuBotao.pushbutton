# -*- coding: utf-8 -*-
"""SECAO 72 - a paridade do no' e' escolhida pelo que ela deixa para preencher.

PRINCIPIO (nao e' este projeto, e' aritmetica de junta): com junta de
BLOCK_JOINT_CM, fechar um trecho de L cm e' trocar `L + junta` em moedas de
(comprimento do bloco + junta). Com o catalogo padrao (B39=40, B34=35,
B19=20, C09=10, C04=5) o RESTO modulo 40 decide quanto do trecho nao pode
ser B39. Num encontro, so' uma das duas paredes ocupa a regiao do no' em
cada fiada, e QUAL fiada e' uma escolha livre - que muda o comprimento do
trecho livre das duas fiadas. Escolher errado troca bloco inteiro por bloco
de ajuste sem ganho fisico nenhum.

FIXTURE DO PRINCIPIO (nenhum id de parede, nenhum offset do Butanta): uma
parede reta entre DOIS T. Com os dois nos na MESMA fiada, uma fiada fica com
o trecho curto e a outra com o longo, e as duas precisam de B34; com um no'
em cada fiada, as duas ficam com o MESMO trecho e fecham so' com B39 - o
unico B34 que sobra e' a propria peca de amarracao.

    python3 -m pytest tests/test_tie_parity_fill_balance.py -q
"""
import collections
import contextlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_block_node_fill_revalidation as NF  # noqa: E402

m = NF.m
ws = sys.modules["core.engine.wall_stepper"]
seg, ft = NF.seg, NF.ft
CATALOG = NF.CATALOG


@contextlib.contextmanager
def balance(enabled, openings=None):
    antes = ws.TIE_PARITY_FILL_BALANCE
    antes_ops = ws.TIE_PARITY_FILL_ALL_OPENINGS
    ws.TIE_PARITY_FILL_BALANCE = enabled
    ws.TIE_PARITY_FILL_ALL_OPENINGS = openings
    try:
        yield
    finally:
        ws.TIE_PARITY_FILL_BALANCE = antes
        ws.TIE_PARITY_FILL_ALL_OPENINGS = antes_ops


def parede_entre_dois_T(comprimento_cm, braco_cm=150.0):
    """Uma parede reta cujas DUAS pontas batem no meio de outra parede."""
    return [seg(0, 0, comprimento_cm, 0),
            seg(0, -braco_cm, 0, braco_cm),
            seg(comprimento_cm, -braco_cm, comprimento_cm, braco_cm)]


def resolve(lines, openings=None, catalog=None):
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    per_wall = openings or dict((i, []) for i in range(len(walls)))
    res = m.solve_building_blocks(nodes, walls, e2n, per_wall, catalog or CATALOG)
    return res, walls, nodes


def pecas_da_parede(walls, res, wall_idx=0):
    pcs = NF.wall_course_pieces(walls, res["candidates"])
    return dict((course, itens) for (wi, course), itens in pcs.items() if wi == wall_idx)


def conta(walls, res, wall_idx=0):
    c = collections.Counter()
    for itens in pecas_da_parede(walls, res, wall_idx).values():
        for _lo, _hi, code, _no in itens:
            c[code] += 1
    return c


def b34_de_preenchimento(walls, res, wall_idx=0):
    """B34 que NAO e' peca de amarracao - o bloco de ajuste evitavel."""
    n = 0
    for itens in pecas_da_parede(walls, res, wall_idx).values():
        for _lo, _hi, code, e_no in itens:
            if code == "B34" and not e_no:
                n += 1
    return n


def buracos(walls, res, wall_idx=0, folga_cm=2.5):
    achados = []
    for course, itens in pecas_da_parede(walls, res, wall_idx).items():
        for a, b in zip(itens, itens[1:]):
            if b[0] - a[1] > folga_cm:
                achados.append((course, round(a[1], 1), round(b[0], 1)))
    return achados


# ------------------------------------------------------- 1. funcao pura
def test_melhor_composicao_e_funcao_pura_do_comprimento():
    """`_pier_arith_best` so' depende do comprimento - e acerta a aritmetica."""
    coins = ws._pier_arith_coins(CATALOG)
    esperado = {
        160.0: (0, 0, 4),     # 4 x B39 exatos
        195.0: (0, 1, 5),     # 4 x B39 + 1 B34
        180.0: (0, 4, 5),     # resto 20: 4 B34 saem mais baratos que 1 B19
        175.0: (0, 5, 5),     # resto 15
        40.0: (0, 0, 1),
    }
    for restante, alvo in sorted(esperado.items()):
        assert ws._pier_arith_best(restante, coins) == alvo, restante
    # nao fecha: nao e' multiplo do modulo
    assert ws._pier_arith_best(163.0, coins) is None


def test_melhor_composicao_nao_olha_nada_alem_do_comprimento():
    coins = ws._pier_arith_coins(CATALOG)
    a = ws._pier_arith_best(235.0, coins)
    b = ws._pier_arith_best(235.0, coins)
    assert a == b and a is not None


# ------------------------------------------- 2. o principio (RED/GREEN)
def test_desligada_a_paridade_desequilibrada_enche_a_parede_de_b34():
    """VERMELHO: com os dois T na mesma fiada, o preenchimento vira B34."""
    with balance(False):
        res, walls, _nodes = resolve(parede_entre_dois_T(235.0))
    assert not res.get("collisions")
    assert b34_de_preenchimento(walls, res) >= 8


def test_ligada_a_paridade_equilibra_e_o_preenchimento_fecha_so_com_b39():
    """VERDE: com um T em cada fiada, as duas ficam com o mesmo trecho e o
    unico B34 que sobra e' a propria peca de amarracao."""
    with balance(True):
        res, walls, nodes = resolve(parede_entre_dois_T(235.0))
    assert not res.get("collisions")
    assert buracos(walls, res) == []
    assert b34_de_preenchimento(walls, res) == 0
    c = conta(walls, res)
    assert c["B39"] >= 10
    assert c["B34"] == 2            # so' as duas amarracoes
    assert any(n.get("_tie_parity_flip") for n in nodes)


def test_as_duas_fiadas_ficam_com_trechos_do_mesmo_tamanho():
    """A medida do principio: o comprimento livre das duas fiadas se iguala."""
    def vaos_livres(walls, res):
        out = {}
        for course, itens in pecas_da_parede(walls, res).items():
            livres = [(lo, hi) for lo, hi, _c, no in itens if not no]
            out[course] = round(max(h for _l, h in livres) - min(l for l, _h in livres), 1) \
                if livres else 0.0
        return out

    with balance(False):
        res_off, walls_off, _n = resolve(parede_entre_dois_T(235.0))
    with balance(True):
        res_on, walls_on, _n = resolve(parede_entre_dois_T(235.0))
    off, on = vaos_livres(walls_off, res_off), vaos_livres(walls_on, res_on)
    assert abs(off["A"] - off["B"]) > 20.0      # desequilibrado
    assert abs(on["A"] - on["B"]) <= 1.0        # equilibrado


# ---------------------------------------------- 3. so' melhora estrita
def test_nao_inverte_quando_nao_ha_ganho():
    """Sem ganho aritmetico, a paridade fica como estava - nenhuma troca
    gratuita (o resultado tem de ser IDENTICO ao da flag desligada)."""
    with balance(False):
        res_off, walls_off, _n = resolve(parede_entre_dois_T(160.0))
    with balance(True):
        res_on, walls_on, nodes_on = resolve(parede_entre_dois_T(160.0))
    assert NF.layout_signature(walls_off, res_off["candidates"]) == \
        NF.layout_signature(walls_on, res_on["candidates"])


def test_determinismo():
    with balance(True):
        a, walls_a, _n = resolve(parede_entre_dois_T(235.0))
        b, walls_b, _n2 = resolve(parede_entre_dois_T(235.0))
    assert NF.layout_signature(walls_a, a["candidates"]) == \
        NF.layout_signature(walls_b, b["candidates"])


# ------------------------------------------ 4. guarda do alcance da verga
def test_no_dentro_do_alcance_da_verga_nao_e_invertido():
    """A canaleta de uma abertura vizinha converte/recua a amarracao naquela
    fiada: ali a paridade nao e' livre, entao a secao 72 nao mexe."""
    walls = [(line, ft(14.0), (False, False)) for line in parede_entre_dois_T(235.0)]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, _e2n = m.build_wall_graph(walls, jm)
    no_t = [n for n in nodes if n.get("kind") == "T_INTERSECTION"]
    assert no_t, "a fixture precisa ter T"
    sem_vao = [[] for _ in walls]
    assert not ws._tie_parity_node_under_opening_reach(no_t[0], walls, sem_vao, CATALOG)
    # abertura encostando no no' da ponta (jamba a 30 cm do encontro)
    com_vao = [[] for _ in walls]
    com_vao[0] = [(ft(30.0), ft(120.0), ft(0.0), ft(210.0))]
    assert ws._tie_parity_node_under_opening_reach(no_t[0], walls, com_vao, CATALOG)
    # abertura longe: volta a ser livre
    longe = [[] for _ in walls]
    longe[0] = [(ft(120.0), ft(200.0), ft(0.0), ft(210.0))]
    perto = [ws._tie_parity_node_under_opening_reach(n, walls, longe, CATALOG) for n in no_t]
    assert not all(perto)


# --------------------------------------------------- 5. legado intacto
def test_flag_desligada_por_padrao_no_motor():
    assert ws.TIE_PARITY_FILL_BALANCE is False
    assert ws.TIE_PARITY_FILL_ALL_OPENINGS is None


def test_decisao_e_unica_por_planta():
    """Monotonia: resolvida a paridade uma vez, as bandas seguintes nao
    refazem a busca (senao o conjunto de inversoes deixa de ser o medido)."""
    linhas = parede_entre_dois_T(235.0)
    walls = [(line, ft(14.0), (False, False)) for line in linhas]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    per_wall = dict((i, []) for i in range(len(walls)))
    with balance(True):
        primeiro = m.solve_all_intersections(nodes, walls, CATALOG, per_wall, e2n)
        segundo = m.solve_all_intersections(nodes, walls, CATALOG, per_wall, e2n)
    assert primeiro.get("tie_parity_fill_flips")
    assert not segundo.get("tie_parity_fill_flips")
    assert all(n.get("_tie_parity_fill_done") for n in nodes)
