# -*- coding: utf-8 -*-
"""SECAO 86.9 (R9) - TOCOS DE EIXO ALEM DA FACE DA PAREDE QUE CRUZA.

PADRAO OBSERVADO no projeto HUMANO BUTANTA R08_LT (1o pavimento): um trecho de
eixo de no maximo 40 cm alem da FACE de uma parede perpendicular, sem abertura e
sem outra parede encostando nele, e' sobra da conversao CAD -> Walls e NAO e'
modulado - a parede termina na face da que cruza e o no' vira L. Casos no
corpus: W07 (40 cm), W29/W30/W31 (35 cm) e W09 (5 cm); o humano nao tem nenhuma
peca nesses trechos.

O corte e' feito ANTES de extend_wall_ends_to_junctions/build_wall_graph
(`trim_wall_end_stubs`, core/engine/wall_pairing.py), no fluxo de paredes
existentes, no refresh da janela e na bancada `tools/audit/s74_corpus.py`.

    py -3 -m pytest tests/test_stub_trim_86_9.py -q
"""
import contextlib
import itertools
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "audit"))

import load_script  # noqa: E402
import revit_stubs  # noqa: E402

m = load_script.load()
wp = sys.modules["core.engine.wall_pairing"]
ui_state = sys.modules.get("core.ui_state")
XYZ = revit_stubs.XYZ
Line = revit_stubs.Line
F = m.FEET_PER_METER
T = 14.0  # espessura das paredes de teste (cm)


def ft(cm):
    return cm / 100.0 * F


def cm(value_ft):
    return value_ft / F * 100.0


def seg(x0, y0, x1, y1):
    return Line.CreateBound(XYZ(ft(x0), ft(y0), 0.0), XYZ(ft(x1), ft(y1), 0.0))


def wall(x0, y0, x1, y1, locks=(False, False)):
    return (seg(x0, y0, x1, y1), ft(T), locks)


def ends_cm(entry):
    line = entry[0]
    a, b = line.GetEndPoint(0), line.GetEndPoint(1)
    return (round(cm(a.X), 4), round(cm(a.Y), 4)), (round(cm(b.X), 4), round(cm(b.Y), 4))


def geometry_key(walls):
    """Conjunto das paredes como SEGMENTOS sem sentido - invariante a ordem e ao
    sentido do eixo."""
    return sorted(tuple(sorted(ends_cm(w))) for w in walls)


# Correcao do usuario (2026-10-05): a 86.9 fica DESLIGADA no produto (os tocos sao modulados); estes
# testes exercitam a funcao com a chave ligada.
PADRAO_DO_PRODUTO = wp.STUB_TRIM_ENABLED


@pytest.fixture(autouse=True)
def _regra_86_9_ligada():
    antes = wp.STUB_TRIM_ENABLED
    wp.STUB_TRIM_ENABLED = True
    try:
        yield
    finally:
        wp.STUB_TRIM_ENABLED = antes


@contextlib.contextmanager
def chave(enabled):
    antes = wp.STUB_TRIM_ENABLED
    wp.STUB_TRIM_ENABLED = enabled
    try:
        yield
    finally:
        wp.STUB_TRIM_ENABLED = antes


def planta_t_com_toco(toco_cm):
    """A (horizontal, y=0) passa pela K (vertical, x=200) e segue `toco_cm` alem
    da face de longe dela (x=207). K chega de cima e termina na face de longe
    da A (y=-7), como o motor deixa um T. A ponta esquerda da A e' um canto L
    com a parede B (vertical em x=0)."""
    a = wall(-7.0, 0.0, 207.0 + toco_cm, 0.0)
    k = wall(200.0, 300.0, 200.0, -7.0)
    b = wall(0.0, 300.0, 0.0, -7.0)
    return [a, k, b]


def kinds(walls):
    ext, jmap = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, _e2n = m.build_wall_graph(ext, jmap)
    return sorted(n["kind"] for n in nodes)


# ===================================================== 1. o toco vira canto L
@pytest.mark.parametrize("toco_cm", [35.0, 40.0])
def test_toco_de_35_e_40_cm_e_aparado_e_o_no_vira_L(toco_cm):
    walls = planta_t_com_toco(toco_cm)
    assert "T_INTERSECTION" in kinds(walls)
    novas, aberturas, tocos = m.trim_wall_end_stubs(walls, [[], [], []])
    assert len(tocos) == 1
    toco = tocos[0]
    assert (toco["wall_idx"], toco["end_index"], toco["crossing_wall_idx"]) == (0, 1, 1)
    assert abs(toco["stub_cm"] - toco_cm) < 1e-6
    # a parede A termina na face de longe da K (x = 207): canto L, como o motor monta
    assert ends_cm(novas[0]) == ((-7.0, 0.0), (207.0, 0.0))
    assert novas[1] is walls[1] and novas[2] is walls[2]
    depois = kinds(novas)
    assert "T_INTERSECTION" not in depois and depois.count("L_CORNER") == 2
    assert aberturas == [[], [], []]


def test_toco_de_41_cm_nao_e_aparado():
    walls = planta_t_com_toco(41.0)
    novas, _ab, tocos = m.trim_wall_end_stubs(walls, [[], [], []])
    assert tocos == []
    assert geometry_key(novas) == geometry_key(walls)
    assert "T_INTERSECTION" in kinds(novas)


def test_sobra_de_modelagem_abaixo_de_1_cm_nao_mexe_no_eixo():
    """Variacao submilimetrica (o corpus mede 0,013 cm) nao e' toco."""
    walls = planta_t_com_toco(0.4)
    assert m.trim_wall_end_stubs(walls, None)[2] == []


def test_o_limite_e_parametro_e_a_chave_desliga_tudo():
    walls = planta_t_com_toco(35.0)
    assert m.trim_wall_end_stubs(walls, None, max_cm=30.0)[2] == []
    with chave(False):
        novas, _ab, tocos = m.trim_wall_end_stubs(walls, None)
    assert tocos == [] and geometry_key(novas) == geometry_key(walls)
    assert m.trim_wall_end_stubs(walls, None, enabled=False)[2] == []
    assert PADRAO_DO_PRODUTO is False and wp.STUB_TRIM_MAX_CM == 40.0  # correcao do usuario 2026-10-05


# ============================================== 2. quando NAO e' toco
def test_toco_com_abertura_nao_e_aparado():
    walls = planta_t_com_toco(35.0)
    porta = (ft(210.0 + 7.0), ft(235.0 + 7.0), 0.0, ft(210.0))  # t a partir do p0 (x = -7)
    assert m.trim_wall_end_stubs(walls, [[porta], [], []])[2] == []


def test_abertura_que_so_encosta_na_face_nao_impede():
    walls = planta_t_com_toco(35.0)
    vao = (ft(100.0 + 7.0), ft(193.0 + 7.0), 0.0, ft(210.0))  # termina antes da K
    novas, aberturas, tocos = m.trim_wall_end_stubs(walls, [[vao], [], []])
    assert len(tocos) == 1 and aberturas[0] == [vao]


def test_toco_com_parede_encostada_na_lateral_nao_e_aparado():
    walls = planta_t_com_toco(35.0)
    walls.append(wall(215.0, -14.0, 400.0, -14.0))  # J paralela, colada na face de baixo do toco
    assert m.trim_wall_end_stubs(walls, None)[2] == []


def test_parede_perpendicular_que_chega_no_toco_vira_a_face_mais_proxima():
    """Uma parede que chega no meio do 'toco' e' um encontro de verdade: a face
    que conta e' a dela (a mais proxima da ponta) - o que sobra alem dela (10 cm)
    e' que e' toco; a K continua um T com a A passando."""
    walls = planta_t_com_toco(35.0)
    walls.append(wall(225.0, -300.0, 225.0, -7.0))  # J chega por baixo em x = 225
    novas, _ab, tocos = m.trim_wall_end_stubs(walls, None)
    assert [(t["wall_idx"], t["end_index"], t["crossing_wall_idx"], round(t["stub_cm"], 6)) for t in tocos] \
        == [(0, 1, 3, 10.0)]
    assert ends_cm(novas[0]) == ((-7.0, 0.0), (232.0, 0.0))
    assert kinds(novas).count("T_INTERSECTION") == 1


def test_toco_com_parede_na_ponta_e_trecho_entre_encontros_nao_e_aparado():
    walls = planta_t_com_toco(35.0)
    walls.append(wall(249.0, 300.0, 249.0, -300.0))  # J passa encostada na ponta da A
    assert m.trim_wall_end_stubs(walls, None)[2] == []


def test_continuacao_colinear_do_outro_lado_nao_e_toco():
    walls = planta_t_com_toco(35.0)
    walls.append(wall(242.0, 0.0, 600.0, 0.0))  # a A continua noutra parede
    assert m.trim_wall_end_stubs(walls, None)[2] == []


def test_aba_curta_que_nasce_na_parede_nao_e_apagada():
    """Parede de 35 cm que so' nasce na K (sem corpo do outro lado) nao e' toco."""
    k = wall(200.0, 300.0, 200.0, -300.0)
    aba = wall(193.0, 0.0, 242.0, 0.0)  # ponta 0 na face de longe da K
    assert m.trim_wall_end_stubs([k, aba], None)[2] == []


def test_ponta_travada_por_testa_do_cad_nao_e_aparada():
    walls = planta_t_com_toco(35.0)
    a = walls[0]
    walls[0] = (a[0], a[1], (False, True))
    assert m.trim_wall_end_stubs(walls, None)[2] == []


def test_parede_dividida_no_no_nao_conta_como_encostada():
    """X em que a parede que cruza chega em DOIS trechos (um de cada lado da A):
    a outra metade so' encosta na linha da face - o toco continua toco."""
    a = wall(-7.0, 0.0, 242.0, 0.0)
    k1 = wall(200.0, 300.0, 200.0, -7.0)
    k2 = wall(200.0, -300.0, 200.0, 7.0)
    b = wall(0.0, 300.0, 0.0, -7.0)
    tocos = m.trim_wall_end_stubs([a, k1, k2, b], None)[2]
    assert [(t["wall_idx"], t["end_index"]) for t in tocos] == [(0, 1)]


# ============================================== 3. invariancia e aberturas
def test_invariante_a_ordem_das_paredes_e_ao_sentido_do_eixo():
    base = planta_t_com_toco(35.0)
    base.append(wall(600.0, 300.0, 600.0, -300.0))   # parede longe, sem toco
    base.append(wall(420.0, 150.0, 607.0 + 20.0, 150.0))  # toco de 20 cm alem da de x=600
    esperado = geometry_key(m.trim_wall_end_stubs(base, None)[0])
    assert len(m.trim_wall_end_stubs(base, None)[2]) == 2
    for perm in itertools.permutations(range(len(base))):
        for flip in (0, 1, 2, 3, 4):
            walls = [base[i] for i in perm]
            line, th, locks = walls[flip]
            a, b = line.GetEndPoint(0), line.GetEndPoint(1)
            walls[flip] = (Line.CreateBound(b, a), th, (locks[1], locks[0]))
            novas, _ab, tocos = m.trim_wall_end_stubs(walls, None)
            assert geometry_key(novas) == esperado
            assert sorted(round(t["stub_cm"], 6) for t in tocos) == [20.0, 35.0]


def test_ponta_0_aparada_reancora_as_aberturas_no_novo_p0():
    walls = planta_t_com_toco(35.0)
    a = walls[0]
    p0, p1 = a[0].GetEndPoint(0), a[0].GetEndPoint(1)
    walls[0] = (Line.CreateBound(p1, p0), a[1], a[2])  # A desenhada da ponta do toco para a esquerda
    vao = (ft(100.0), ft(190.0), ft(100.0), ft(220.0))  # 100..190 cm a partir da ponta do toco
    novas, aberturas, tocos = m.trim_wall_end_stubs(walls, [[vao], [], []])
    assert [(t["wall_idx"], t["end_index"]) for t in tocos] == [(0, 0)]
    lo, hi, sill, head = aberturas[0][0]
    assert abs(cm(lo) - 65.0) < 1e-6 and abs(cm(hi) - 155.0) < 1e-6
    assert (sill, head) == (vao[2], vao[3])
    # o vao continua no MESMO lugar do mundo
    nova = novas[0][0]
    q0 = nova.GetEndPoint(0)
    assert abs(cm(q0.X) - 207.0) < 1e-6
    assert abs((cm(q0.X) - cm(lo)) - (242.0 - 100.0)) < 1e-6


def test_entrada_nao_e_mutada():
    walls = planta_t_com_toco(35.0)
    opw = [[], [], []]
    antes = geometry_key(walls)
    m.trim_wall_end_stubs(walls, opw)
    assert geometry_key(walls) == antes and opw == [[], [], []]


# ============================================== 4. registro no corpus da RUN
def test_registro_em_corpus_trimmed_relatorio_e_ui():
    walls = planta_t_com_toco(35.0)
    _n, _a, tocos = m.trim_wall_end_stubs(walls, None)
    itens = m.stub_trim_corpus_items(tocos, [501, 502, 503], ["k-a", "k-k", "k-b"])
    assert len(itens) == 1
    item = itens[0]
    assert item["rule_id"] == m.STUB_TRIM_RULE_ID == "REGRA_86_9_STUB_TRIM"
    assert (item["index"], item["end_index"], item["wall_id"], item["axis_key"]) == (0, 1, 501, "k-a")
    assert item["trimmed_cm"] == 35.0 and item["length_cm"] == 249.0 and item["new_length_cm"] == 214.0
    assert item["crossing_wall_index"] == 1 and "86.9" in item["reason"]
    corpus = m.corpus_selection_record("paredes existentes", 3, 3, [], trimmed=itens)
    assert corpus["trimmed"] == itens
    linhas = m._corpus_report_lines(corpus)
    assert any("TRIMMED axis_index=0" in ln and "REGRA_86_9_STUB_TRIM" in ln and "trimmed_cm=35.0" in ln
               for ln in linhas), linhas
    if ui_state is not None:
        ui = ui_state.corpus_lines({"corpus_selection": corpus})
        assert any("Toco aparado" in ln and "86.9" in ln for ln in ui), ui


class _FakeWall(object):
    def __init__(self, curve):
        self.Location = m.LocationCurve()
        self.Location.Curve = curve


class _FakeDoc(object):
    def __init__(self, elements):
        self._elements = elements

    def GetElement(self, element_id):
        return self._elements.get(element_id)


def test_refresh_da_janela_refaz_o_corte_sem_deriva_das_aberturas():
    """A Wall do Revit NAO e' aparada: o refresh rele o toco e tem de cortar de
    novo antes do grafo. A ponta aparada e' a 0 (o p0 anda): as aberturas ficam
    no referencial do p0 aparado e nao derivam de um refresh para o outro."""
    revit = [seg(242.0, 0.0, -7.0, 0.0), seg(200.0, 300.0, 200.0, -7.0), seg(0.0, 300.0, 0.0, -7.0)]
    vao = (ft(100.0), ft(190.0), ft(100.0), ft(220.0))  # na Wall do Revit (p0 = ponta do toco)
    walls = [(c, ft(T), (False, False)) for c in revit]
    walls, opw, tocos = m.trim_wall_end_stubs(walls, [[vao], [], []])
    corpus = m.corpus_selection_record("paredes existentes", 3, 3, [],
                                       trimmed=m.stub_trim_corpus_items(tocos, [11, 12, 13]))
    handler = m._PostCreationEventHandler()
    handler.walls_to_create = list(walls)
    handler.openings_per_wall = opw
    handler.created_walls_by_axis = {0: [(11, "cad")], 1: [(12, "cad")], 2: [(13, "cad")]}
    handler.wall_segment_geometry = {}
    handler.setup = {"corpus_selection": corpus}
    doc = _FakeDoc(dict((eid, _FakeWall(c)) for eid, c in zip((11, 12, 13), revit)))
    for _vez in range(3):
        handler._refresh_geometry_from_document(doc)
        a0, a1 = ends_cm(handler.walls_to_create[0])
        assert sorted([a0, a1]) == [(-7.0, 0.0), (207.0, 0.0)], (a0, a1)
        lo, hi = handler.openings_per_wall[0][0][:2]
        assert abs(cm(lo) - 65.0) < 1e-6 and abs(cm(hi) - 155.0) < 1e-6
        tipos = [n["kind"] for n in handler.wall_graph_nodes]
        assert "T_INTERSECTION" not in tipos and tipos.count("L_CORNER") == 2, tipos
    itens = handler.setup["corpus_selection"]["trimmed"]
    assert [(it["index"], it["end_index"], it["wall_id"]) for it in itens] == [(0, 0, 11)]


def test_refresh_sem_reler_a_parede_aparada_nao_desfaz_o_corte():
    """Wall do eixo aparado sumiu do documento (nao e' relida): o eixo segue
    aparado, as aberturas nao andam e o registro do corpus continua."""
    revit = [seg(242.0, 0.0, -7.0, 0.0), seg(200.0, 300.0, 200.0, -7.0), seg(0.0, 300.0, 0.0, -7.0)]
    vao = (ft(100.0), ft(190.0), ft(100.0), ft(220.0))
    walls, opw, tocos = m.trim_wall_end_stubs([(c, ft(T), (False, False)) for c in revit], [[vao], [], []])
    handler = m._PostCreationEventHandler()
    handler.walls_to_create = list(walls)
    handler.openings_per_wall = opw
    handler.created_walls_by_axis = {0: [(11, "cad")], 1: [(12, "cad")], 2: [(13, "cad")]}
    handler.wall_segment_geometry = {}
    handler.setup = {"corpus_selection": m.corpus_selection_record(
        "paredes existentes", 3, 3, [], trimmed=m.stub_trim_corpus_items(tocos, [11, 12, 13]))}
    doc = _FakeDoc({12: _FakeWall(revit[1]), 13: _FakeWall(revit[2])})  # a Wall 11 sumiu
    for _vez in range(2):
        handler._refresh_geometry_from_document(doc)
        assert sorted(ends_cm(handler.walls_to_create[0])) == [(-7.0, 0.0), (207.0, 0.0)]
        assert abs(cm(handler.openings_per_wall[0][0][0]) - 65.0) < 1e-6
    assert [(it["index"], it["end_index"]) for it in handler.setup["corpus_selection"]["trimmed"]] == [(0, 0)]


def test_refresh_do_fluxo_classico_apara_na_primeira_vez():
    """Fluxo CAD -> Walls: a Wall foi criada COM o toco e as aberturas estao no
    referencial dela; o primeiro refresh apara e reancora uma unica vez."""
    revit = [seg(242.0, 0.0, -7.0, 0.0), seg(200.0, 300.0, 200.0, -7.0), seg(0.0, 300.0, 0.0, -7.0)]
    vao = (ft(100.0), ft(190.0), ft(100.0), ft(220.0))
    handler = m._PostCreationEventHandler()
    handler.walls_to_create = [(c, ft(T), (False, False)) for c in revit]
    handler.openings_per_wall = [[vao], [], []]
    handler.created_walls_by_axis = {0: [(11, "cad")], 1: [(12, "cad")], 2: [(13, "cad")]}
    handler.wall_segment_geometry = {}
    handler.setup = {"corpus_selection": m.corpus_selection_record("cad", 3, 3, [])}
    doc = _FakeDoc(dict((eid, _FakeWall(c)) for eid, c in zip((11, 12, 13), revit)))
    for _vez in range(2):
        handler._refresh_geometry_from_document(doc)
        lo = handler.openings_per_wall[0][0][0]
        assert abs(cm(lo) - 65.0) < 1e-6
    assert len(handler.setup["corpus_selection"]["trimmed"]) == 1


# ============================================== 5. corpus BUTANTA (so' grafo)
def test_corpus_butanta_os_cinco_tocos_e_os_quatro_T_que_viram_L():
    import s74_corpus as S
    geo = S.geometry()
    antes = S.build_context(geo, stub_trim=False)
    depois = S.build_context(geo)
    achados = [(depois["keys"][t["wall_idx"]], t["end_index"], t["stub_cm"], depois["keys"][t["crossing_wall_idx"]])
               for t in depois["stub_trims"]]
    assert achados == [("W07", 1, 40.0, "W31"), ("W09", 0, 5.0, "W29"), ("W29", 1, 35.0, "W13"),
                       ("W30", 1, 35.0, "W24"), ("W31", 1, 35.0, "W13")]
    assert antes["stub_trims"] == []
    from collections import Counter
    k0 = Counter(n["kind"] for n in antes["nodes"])
    k1 = Counter(n["kind"] for n in depois["nodes"])
    assert (k0["T_INTERSECTION"], k1["T_INTERSECTION"]) == (37, 33)
    assert (k0["L_CORNER"], k1["L_CORNER"]) == (13, 17)
    # so' sobra a ponta livre de verdade (W25 - indice 24 -, sem parede na ponta 1)
    livres = [n["arms"] for n in depois["nodes"] if n["kind"] == "FREE_END"]
    assert livres == [[(24, 1)]]
    # os comprimentos que o humano modula (human_rows_unpad: 999 e 64 cm)
    for key, esperado in (("W07", 999.0), ("W29", 64.0), ("W30", 64.0), ("W31", 64.0), ("W09", 714.0)):
        i = depois["keys"].index(key)
        assert abs(cm(depois["walls"][i][0].Length) - esperado) < 0.05
    # W09 (ponta 0 aparada 5 cm): as aberturas andam 5 cm junto com o p0
    i = depois["keys"].index("W09")
    for a, b in zip(antes["openings_per_wall"][i], depois["openings_per_wall"][i]):
        assert abs(cm(a[0] - b[0]) - 5.0) < 1e-6
    assert depois["openings_per_wall_original"][i] == antes["openings_per_wall"][i]
    assert [it["axis_key"] for it in depois["corpus_trimmed"]] == ["W07", "W09", "W29", "W30", "W31"]


def test_corpus_butanta_invariante_a_ordem_e_ao_sentido():
    import s74_corpus as S
    geo = S.geometry()
    base = S.build_context(geo)
    ordem = list(reversed(range(len(geo["walls"]))))
    outro = S.build_context(geo, order=ordem, swap_ends=tuple(w["key"] for w in geo["walls"]))

    def chave_toco(ctx):
        return sorted((ctx["keys"][t["wall_idx"]], round(t["stub_cm"], 6)) for t in ctx["stub_trims"])

    def segs(ctx):
        return sorted(tuple(sorted(ends_cm(w))) for w in ctx["walls"])

    assert chave_toco(base) == chave_toco(outro)
    assert segs(base) == segs(outro)


def test_mini_planta_real_nenhuma_peca_no_toco_da_W29():
    """Solve REAL (2 fiadas, sem aberturas) da W13 + W29: com a 86.9 nenhuma peca
    da W29 passa da face da W13 (64 cm, como o humano); sem ela o toco e' modulado."""
    import s74_corpus as S
    geo = S.geometry()
    keys = [w["key"] for w in geo["walls"]]
    sub = dict(geo, walls=[geo["walls"][keys.index("W13")], geo["walls"][keys.index("W29")]], openings=[])
    alcance = {}
    for ligada in (True, False):
        ctx = S.build_context(sub, stub_trim=ligada)
        res = S.solve(ctx, True, geo=sub, courses=2, strategy=None)
        p0 = S.geometry()["walls"][keys.index("W29")]["p0_cm"]
        maior = 0.0
        for cands in res["course_candidates"].values():
            for c in cands:
                if c.get("wall_idx") != 1:
                    continue
                for cell in c.get("cells_world") or []:
                    pt = cell["point"]
                    maior = max(maior, abs(pt.X * 30.48 - p0[0]))
        alcance[ligada] = maior
        if ligada:
            assert not res.get("collisions") and not res.get("non_modular")
    assert alcance[True] <= 64.0 + 0.5, alcance
    assert alcance[False] > 70.0, alcance


# ============================================== 6. IronPython 2.7
def test_modulos_tocados_compativeis_com_ironpython27():
    """O motor roda em IronPython 2.7: nenhuma construcao so'-Python-3 nos
    modulos tocados pela 86.9 (arvore de sintaxe)."""
    import ast
    import io
    proibidos = tuple(getattr(ast, n) for n in ("JoinedStr", "Nonlocal", "NamedExpr", "YieldFrom", "AnnAssign",
                                                 "AsyncFunctionDef", "AsyncFor", "AsyncWith", "Await", "Match")
                      if hasattr(ast, n))
    for rel in (("nuvem", "core", "engine", "wall_pairing.py"), ("nuvem", "core", "wall_modeling.py"),
                ("nuvem", "core", "ui_state.py")):
        arvore = ast.parse(io.open(os.path.join(ROOT, *rel), encoding="utf-8").read())
        achados = []
        for no in ast.walk(arvore):
            if isinstance(no, proibidos):
                achados.append((type(no).__name__, getattr(no, "lineno", None)))
            elif isinstance(no, (ast.FunctionDef, ast.Lambda)):
                a = no.args
                if a.kwonlyargs or getattr(a, "posonlyargs", None):
                    achados.append(("kwonly/posonly", getattr(no, "lineno", None)))
                if any(x.annotation is not None for x in a.args + a.kwonlyargs) or getattr(no, "returns", None):
                    achados.append(("anotacao", getattr(no, "lineno", None)))
        assert not achados, (rel, achados[:10])
