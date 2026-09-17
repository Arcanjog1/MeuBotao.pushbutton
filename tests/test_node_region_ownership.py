# -*- coding: utf-8 -*-
"""POSSE DA REGIAO DO NO' -> COMPRIMENTO DO TRECHO -> COMPOSICAO.

Num encontro, so' UMA das duas paredes ocupa a regiao do no' em cada fiada.
Qual fiada de qual parede fica com ela e' uma escolha livre (as duas
alternativas sao amarracoes corretas), mas NAO e' neutra: ela decide o
COMPRIMENTO do trecho livre que sobra para cada fiada preencher - e o
comprimento decide sozinho a composicao (secao 72).

Estes testes provam a CADEIA CAUSAL inteira numa parede sintetica, sem
nenhum id do projeto e sem nenhuma coordenada do Butanta:

    posse da regiao do no'  ->  comprimento do trecho livre  ->  composicao

e provam que o resultado FISICO nao depende de como a mesma geometria e'
apresentada ao motor (pontas invertidas, planta transladada, ordem das
paredes permutada).

    python3 -m pytest tests/test_node_region_ownership.py -q
"""
import collections
import contextlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import revit_stubs  # noqa: E402
import test_block_node_fill_revalidation as NF  # noqa: E402

m = NF.m
ws = sys.modules["core.engine.wall_stepper"]
XYZ = revit_stubs.XYZ
Line = revit_stubs.Line
ft = NF.ft
CATALOG = NF.CATALOG


@contextlib.contextmanager
def secao72(ligada, vaos=None):
    antes, antes_vaos = ws.TIE_PARITY_FILL_BALANCE, ws.TIE_PARITY_FILL_ALL_OPENINGS
    ws.TIE_PARITY_FILL_BALANCE = ligada
    ws.TIE_PARITY_FILL_ALL_OPENINGS = vaos
    try:
        yield
    finally:
        ws.TIE_PARITY_FILL_BALANCE = antes
        ws.TIE_PARITY_FILL_ALL_OPENINGS = antes_vaos


# ------------------------------------------------------------------ fixtures
def seg(x0, y0, x1, y1):
    return Line.CreateBound(XYZ(ft(x0), ft(y0), 0.0), XYZ(ft(x1), ft(y1), 0.0))


def parede_entre_dois_T(L, braco=155.0, dx=0.0, dy=0.0, invertida=False, ordem=None):
    """Uma parede reta cujas DUAS pontas batem no MEIO de outra parede."""
    principal = seg(dx, dy, L + dx, dy) if not invertida else seg(L + dx, dy, dx, dy)
    linhas = [principal,
              seg(dx, dy - braco, dx, dy + braco),
              seg(L + dx, dy - braco, L + dx, dy + braco)]
    if ordem is not None:
        linhas = [linhas[i] for i in ordem]
    return linhas


def parede_em_cruz(L, braco=155.0):
    """Parede longa com UMA perpendicular atravessando o meio (cruz)."""
    meio = L / 2.0
    return [seg(0, 0, L, 0), seg(meio, -braco, meio, braco)]


def resolve(linhas, vaos=None, alvo=0):
    paredes = [(l, ft(14.0), (False, False)) for l in linhas]
    paredes, jm = m.extend_wall_ends_to_junctions(paredes, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(paredes, jm)
    per = vaos or dict((i, []) for i in range(len(paredes)))
    res = m.solve_building_blocks(nodes, paredes, e2n, per, CATALOG)
    return res, paredes, nodes, alvo


def pecas(paredes, res, wall_idx):
    todas = NF.wall_course_pieces(paredes, res["candidates"])
    return dict((c, itens) for (wi, c), itens in todas.items() if wi == wall_idx)


def assinatura_fisica(paredes, res, wall_idx):
    """O que e' FISICO na parede: o conjunto das duas fiadas, cada uma como a
    sequencia de codigos ao longo do eixo. Nao olha rotulo A/B (a troca de
    nome entre fiadas nao muda a parede) nem coordenada absoluta."""
    saida = []
    for _c, itens in sorted(pecas(paredes, res, wall_idx).items()):
        saida.append(tuple(code for _lo, _hi, code, _no in itens))
    return frozenset(saida)


def trechos_livres(paredes, res, wall_idx):
    """[(comprimento, [codigos])] dos trechos que NAO sao peca de amarracao."""
    saida = []
    for _c, itens in sorted(pecas(paredes, res, wall_idx).items()):
        atual = []
        for lo, hi, code, e_no in itens:
            if e_no:
                if atual:
                    saida.append((round(atual[-1][1] - atual[0][0], 1),
                                  [x[2] for x in atual]))
                atual = []
                continue
            if atual and lo - atual[-1][1] > 3.0:
                saida.append((round(atual[-1][1] - atual[0][0], 1), [x[2] for x in atual]))
                atual = []
            atual.append((lo, hi, code))
        if atual:
            saida.append((round(atual[-1][1] - atual[0][0], 1), [x[2] for x in atual]))
    return sorted(saida)


def conta(paredes, res, wall_idx):
    c = collections.Counter()
    for _cu, itens in pecas(paredes, res, wall_idx).items():
        for _lo, _hi, code, _no in itens:
            c[code] += 1
    return c


# ===================================================== 1. a cadeia causal
def test_a_posse_do_no_muda_o_comprimento_do_trecho():
    """ELO 1: mudar de quem e' a regiao do no' muda o COMPRIMENTO livre."""
    with secao72(False):
        off = resolve(parede_entre_dois_T(235.0))
        comp_off = [L for L, _codes in trechos_livres(off[1], off[0], 0)]
    with secao72(True):
        on = resolve(parede_entre_dois_T(235.0))
        comp_on = [L for L, _codes in trechos_livres(on[1], on[0], 0)]
    assert comp_off != comp_on, (comp_off, comp_on)
    # desligada, as duas fiadas ficam com trechos de tamanhos DIFERENTES;
    # ligada, elas se igualam - e' o equilibrio que o humano mostra.
    assert max(comp_off) - min(comp_off) > 20.0
    assert max(comp_on) - min(comp_on) <= 1.0


def test_o_comprimento_do_trecho_decide_a_composicao():
    """ELO 2: para o comprimento que sobra, a composicao e' consequencia.

    Com junta de 1 cm, fechar L cm e' trocar L+1 em moedas de 40/35/20/10/5:
    L=159 fecha so' com bloco inteiro; L=174 e L=179 nao fecham sem bloco de
    ajuste. Nao ha' escolha a fazer - e' aritmetica."""
    with secao72(True):
        on = resolve(parede_entre_dois_T(235.0))
    for L, codes in trechos_livres(on[1], on[0], 0):
        if abs(L - 159.0) < 0.5:
            assert set(codes) == {"B39"}, (L, codes)
    with secao72(False):
        off = resolve(parede_entre_dois_T(235.0))
    ruins = [(L, codes) for L, codes in trechos_livres(off[1], off[0], 0)
             if abs((round(L) + 1) % 40) not in (0, 35)]
    assert ruins, "a fixture precisa ter pelo menos um trecho de resto ruim"
    for _L, codes in ruins:
        assert "B34" in codes or "B19" in codes or "C09" in codes or "C04" in codes


def test_a_composicao_decide_as_pecas():
    """ELO 3: fecha a cadeia - equilibrar a posse do no' troca bloco de
    ajuste por bloco inteiro, sem inventar peca nenhuma."""
    with secao72(False):
        off = resolve(parede_entre_dois_T(235.0))
        c_off = conta(off[1], off[0], 0)
    with secao72(True):
        on = resolve(parede_entre_dois_T(235.0))
        c_on = conta(on[1], on[0], 0)
    assert c_on["B39"] > c_off["B39"]
    assert c_on["B34"] < c_off["B34"]
    assert not off[0].get("collisions") and not on[0].get("collisions")


# ============================================ 2. invariancia de apresentacao
def test_inverter_as_pontas_nao_muda_a_parede():
    """A mesma parede desenhada do fim para o comeco da o MESMO resultado
    fisico (a sequencia le-se ao contrario)."""
    with secao72(True):
        a = resolve(parede_entre_dois_T(235.0))
        b = resolve(parede_entre_dois_T(235.0, invertida=True))
    sa = assinatura_fisica(a[1], a[0], 0)
    sb = frozenset(tuple(reversed(x)) for x in assinatura_fisica(b[1], b[0], 0))
    assert sa == sb, (sorted(sa), sorted(sb))


def test_transladar_a_planta_nao_muda_a_parede():
    with secao72(True):
        a = resolve(parede_entre_dois_T(235.0))
        b = resolve(parede_entre_dois_T(235.0, dx=1234.0, dy=-567.0))
    assert assinatura_fisica(a[1], a[0], 0) == assinatura_fisica(b[1], b[0], 0)


def test_permutar_a_ordem_das_paredes_nao_muda_a_parede():
    """A parede sob teste muda de indice; o resultado fisico dela nao muda."""
    with secao72(True):
        a = resolve(parede_entre_dois_T(235.0))
        sa = assinatura_fisica(a[1], a[0], 0)
    for ordem in ((1, 0, 2), (2, 1, 0), (1, 2, 0), (2, 0, 1), (0, 2, 1)):
        novo_idx = ordem.index(0)      # onde a parede sob teste foi parar
        with secao72(True):
            b = resolve(parede_entre_dois_T(235.0, ordem=ordem))
        assert assinatura_fisica(b[1], b[0], novo_idx) == sa, ordem


def test_determinismo_em_repeticao():
    with secao72(True):
        a = resolve(parede_entre_dois_T(235.0))
        b = resolve(parede_entre_dois_T(235.0))
    assert NF.layout_signature(a[1], a[0]["candidates"]) == \
        NF.layout_signature(b[1], b[0]["candidates"])


# ======================================================= 3. outras topologias
def test_cruz_fecha_sem_colisao_e_sem_buraco():
    with secao72(True):
        res, paredes, nodes, _ = resolve(parede_em_cruz(470.0))
    assert not res.get("collisions")
    for _c, itens in pecas(paredes, res, 0).items():
        for a, b in zip(itens, itens[1:]):
            assert b[0] - a[1] <= 40.0, (a, b)


def test_no_perto_de_abertura_nao_e_invertido():
    """Onde a canaleta da abertura converte a amarracao, a paridade nao e'
    livre - a secao 72 nao mexe (guarda do alcance da verga)."""
    linhas = parede_entre_dois_T(235.0)
    paredes = [(l, ft(14.0), (False, False)) for l in linhas]
    paredes, jm = m.extend_wall_ends_to_junctions(paredes, m.JUNCTION_FACE_SEARCH_FT)
    nodes, _e2n = m.build_wall_graph(paredes, jm)
    tees = [n for n in nodes if n.get("kind") == "T_INTERSECTION"]
    assert tees
    sem = [[] for _ in paredes]
    assert not ws._tie_parity_node_under_opening_reach(tees[0], paredes, sem, CATALOG)
    com = [[] for _ in paredes]
    com[0] = [(ft(30.0), ft(120.0), ft(0.0), ft(210.0))]
    assert ws._tie_parity_node_under_opening_reach(tees[0], paredes, com, CATALOG)


def test_nao_depende_do_comprimento_do_butanta():
    """O mesmo principio em varios comprimentos: sempre que equilibrar a
    posse do no' der trechos iguais, o bloco inteiro ganha espaco."""
    melhorou = 0
    for L in (190.0, 235.0, 275.0, 310.0):
        with secao72(False):
            off = resolve(parede_entre_dois_T(L))
            c_off = conta(off[1], off[0], 0)
        with secao72(True):
            on = resolve(parede_entre_dois_T(L))
            c_on = conta(on[1], on[0], 0)
        assert not on[0].get("collisions"), L
        if c_on["B39"] > c_off["B39"] and c_on["B34"] <= c_off["B34"]:
            melhorou += 1
    assert melhorou >= 3, melhorou
