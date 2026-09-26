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


def _nos_resolvidos(lines):
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    per_wall = dict((i, []) for i in range(len(walls)))
    out = m.solve_all_intersections(nodes, walls, CATALOG, per_wall, e2n, _parity_pass=False)
    return walls, nodes, e2n, out


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
def test_custo_da_paridade_e_funcao_pura_dos_trechos():
    """O custo so' depende dos trechos que a paridade deixa - mesma entrada,
    mesmo resultado, e ele conta o que diz que conta."""
    walls, nodes, e2n, out = _nos_resolvidos(parede_entre_dois_T(235.0))
    a = ws._tie_parity_fill_layout_cost({0}, nodes, walls, e2n, out["candidates"], CATALOG)
    b = ws._tie_parity_fill_layout_cost({0}, nodes, walls, e2n, out["candidates"], CATALOG)
    assert a == b and len(a) == 5
    assert a[0] == 0                      # a parede medida fecha nas duas fiadas
    assert a[1] == 0                      # nenhuma cadeia de compensador (regra #2)
    # os bracos da fixture tem comprimento nao-modular de proposito: o custo
    # SEPARA isso em `fail`, o primeiro termo, em vez de esconder.
    todas = ws._tie_parity_fill_layout_cost(set(range(len(walls))), nodes, walls, e2n,
                                            out["candidates"], CATALOG)
    assert todas[0] > 0


def test_ordem_do_custo_e_pecas_depois_especiais_depois_b34():
    """(falhas, regra #2, pecas, especiais, B34): menos pecas e' sempre
    melhor - para o mesmo comprimento, menos pecas quer dizer pecas maiores,
    que e' a preferencia por B39 sem precisar de um termo por codigo."""
    walls, nodes, e2n, out = _nos_resolvidos(parede_entre_dois_T(235.0))
    c = ws._tie_parity_fill_layout_cost({0}, nodes, walls, e2n, out["candidates"], CATALOG)
    assert (c[0], c[1], c[2] - 1, c[3] + 3, c[4] + 3) < c   # menos pecas vence tudo
    assert (c[0], c[1], c[2], c[3] - 1, c[4] + 3) < c       # depois, menos especiais
    assert (c[0], c[1], c[2], c[3], c[4] - 1) < c           # por ultimo, menos B34
    assert (c[0], c[1] + 1, 0, 0, 0) > c                    # regra #2 continua na frente


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


def test_decisao_e_unica_por_planta(monkeypatch):
    """Monotonia: resolvida a paridade uma vez, as bandas seguintes nao
    refazem a busca (senao o conjunto de inversoes deixa de ser o medido).
    SECAO 82: a chamada seguinte DEVOLVE a decisao ja' tomada (lida do no'),
    sem avaliar custo nenhum - a busca nao roda de novo."""
    linhas = parede_entre_dois_T(235.0)
    walls = [(line, ft(14.0), (False, False)) for line in linhas]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    per_wall = dict((i, []) for i in range(len(walls)))
    custos = []
    real_custo = ws._tie_parity_fill_layout_cost
    monkeypatch.setattr(ws, "_tie_parity_fill_layout_cost",
                        lambda *a, **k: custos.append(1) or real_custo(*a, **k))
    with balance(True):
        primeiro = m.solve_all_intersections(nodes, walls, CATALOG, per_wall, e2n)
        avaliados = len(custos)
        segundo = m.solve_all_intersections(nodes, walls, CATALOG, per_wall, e2n)
    assert primeiro.get("tie_parity_fill_flips") and avaliados > 0
    assert len(custos) == avaliados                      # a busca nao rodou de novo
    assert segundo.get("tie_parity_fill_flips") == primeiro.get("tie_parity_fill_flips")
    assert all(n.get("_tie_parity_fill_done") for n in nodes)
