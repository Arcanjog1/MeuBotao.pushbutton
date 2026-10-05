# -*- coding: utf-8 -*-
"""SECAO 86.15 - T COM TOCO: A PECA DA FIADA QUE PASSA ATRAVESSA A FACE.

Correcao do usuario (2026-10-05): os tocos alem da face da parede que cruza
voltaram a ser modulados (86.9 desligada). No BUTANTA as paredes de 99 cm
W29/W30/W31 tem um T no meio (a parede longa chega em t = 50-64 cm) e um toco
de 35 cm. A auditoria reprovava as tres: junta corrida em X~49,5 cm nas 13
fiadas - a peca da fiada que PASSA comecava exatamente na face da parede que
chega, onde a fiada oposta termina.

CAUSA PROVADA: o teste de espaco do B54 usava a reserva de PIOR CASO do canto
da outra ponta (34 cm nas duas fiadas), media 23 cm (precisa de 27) e o T
degradava para L - B34 ancorado na face da que chega. O canto, porem, ja'
deixava o espaco do B54 na fiada do T (regra 11.14). Com a 86.15 a principal
e' medida na fiada da peca do T: o T vira B54|B34 de verdade.

    py -3 -m pytest tests/test_junta_no_toco_86_15.py -q
"""
import ast
import contextlib
import io
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "audit"))

import s74_corpus as S  # noqa: E402

m, ws = S.engine()
XYZ = m.XYZ
CORPUS = S.geometry()
CM = 30.48
FACE_LO, FACE_HI = 50.0, 64.0        # faces da parede que chega (eixo em x = 57, 14 cm)
JUNTA_LO, JUNTA_HI = 49.5, 64.5      # onde a fiada cortada termina / recomeca
TOL_JUNTA = 1.5                      # BOND_JOINT_CLUSTER_TOLERANCE_CM da auditoria
# Catalogo da sobra (secao 86.6): composicao que fecha cada sobra, em cm
SOBRA = {4: ["C04"], 9: ["C09"], 14: ["C04", "C09"], 19: ["B19"], 24: ["B19", "C04"], 29: ["B19", "C09"],
         34: ["B34"]}


@contextlib.contextmanager
def chave(ligada):
    antes = ws.T_MAIN_ROOM_IN_OWN_COURSE_ENABLED
    ws.T_MAIN_ROOM_IN_OWN_COURSE_ENABLED = bool(ligada)
    try:
        yield
    finally:
        ws.T_MAIN_ROOM_IN_OWN_COURSE_ENABLED = antes


def planta(toco_cm=35.0, invertido=False, ordem=(0, 1, 2)):
    """Geometria do BUTANTA (W29 + W09 + W13) transladada para a origem:
    M (principal, horizontal, 64 + toco cm) comeca na face externa do canto C
    (vertical em x = 7, desce) e e' cruzada em x = 57 pela I, que chega de cima
    e termina na face de longe da M (y = -7). A ponta x = 64 + toco e' livre."""
    comp = 64.0 + toco_cm
    principal = {"key": "M", "thickness_cm": 14.0,
                 "p0_cm": [comp, 0.0] if invertido else [0.0, 0.0],
                 "p1_cm": [0.0, 0.0] if invertido else [comp, 0.0]}
    canto = {"key": "C", "p0_cm": [7.0, 7.0], "p1_cm": [7.0, -700.0], "thickness_cm": 14.0}
    chega = {"key": "I", "p0_cm": [57.0, 500.0], "p1_cm": [57.0, -7.0], "thickness_cm": 14.0}
    paredes = [principal, canto, chega]
    return {"walls": [paredes[k] for k in ordem], "openings": [], "catalog": CORPUS["catalog"]}


def resolve(geo, fiadas=6, ligada=True):
    with chave(ligada):
        ctx = S.build_context(geo)
        res = S.solve(ctx, True, geo=geo, courses=fiadas, strategy=None)
    return ctx, res


def fileiras(ctx, res, key="M"):
    """{fiada: [(x_lo, x_hi, codigo, celulas_x)]} das pecas da parede, em x MUNDO (cm)."""
    wi = ctx["keys"].index(key)
    origem, eixo = XYZ(0.0, 0.0, 0.0), XYZ(1.0, 0.0, 0.0)
    out = {}
    for ci, cands in res["course_candidates"].items():
        itens = []
        for c in cands:
            if c.get("wall_idx") != wi:
                continue
            lo, hi = ws._candidate_extent_on_wall_axis(c, origem, eixo)
            celulas = tuple(sorted(round(cell["point"].X * CM, 2) for cell in (c.get("cells_world") or [])))
            itens.append((round(lo, 2), round(hi, 2), c["logical_code"], celulas))
        out[ci] = sorted(itens)
    return out


def juntas(itens):
    return [(a[1] + b[0]) / 2.0 for a, b in zip(itens, itens[1:]) if b[0] - a[1] <= 2.5]


def passa(itens):
    return any(lo < 57.0 < hi for lo, hi, _c, _cel in itens)


def auditoria(ctx, res, key="M"):
    wi = ctx["keys"].index(key)
    return (res.get("wall_bond_audits") or {}).get(wi) or {}


def corrida(aud):
    return [p for p in (aud.get("problems") or []) if "CONTINUOUS_VERTICAL_JOINT" in p]


def no_t(ctx):
    nos = [i for i, n in enumerate(ctx["nodes"]) if n.get("kind") == "T_INTERSECTION"]
    assert len(nos) == 1, nos
    return nos[0]


def no_canto(ctx):
    nos = [i for i, n in enumerate(ctx["nodes"]) if n.get("kind") == "L_CORNER"]
    assert len(nos) == 1, nos
    return nos[0]


# ================================================= 1. causa (so' o grafo)
def test_causa_pior_caso_reprova_mas_a_fiada_do_T_tem_o_espaco_do_B54():
    """Reproducao minima da causa: o pior caso mede 23 cm do lado do canto (o
    B34 do canto nas DUAS fiadas) e reprova o B54; na fiada da peca do T o canto
    so' ocupa o corpo da perpendicular e sobram 43 cm."""
    ctx = S.build_context(planta())
    ti, ci = no_t(ctx), no_canto(ctx)
    node = ctx["nodes"][ti]
    walls, opw, nodes, e2n = ctx["walls"], ctx["openings_per_wall"], ctx["nodes"], ctx["e2n"]
    pior = ws._t_intersection_room_assessment(node, walls, opw, nodes=nodes, end_to_node=e2n, node_index=ti)
    assert abs(pior["room_minus_ft"] * CM - 23.0) < 0.1 and abs(pior["room_plus_ft"] * CM - 42.0) < 0.1
    assert ws._t_intersection_room_ok(node, walls, opw, nodes=nodes, end_to_node=e2n, node_index=ti) is False
    principal = node["main_wall_idx"]
    canto_na_outra = {ci: (None, {"wall_idx": principal, "course": "B"})}
    ok, medida = ws._t_intersection_room_ok_in_own_course(node, walls, opw, nodes, e2n, ti, canto_na_outra)
    assert ok is True and medida["course"] == "A"
    assert abs(medida["room_minus_ft"] * CM - 43.0) < 0.1


def test_canto_deitado_na_mesma_fiada_continua_degradando_nunca_colisao():
    """Se o canto JA' resolvido deita o B34 dele sobre a principal na fiada do T,
    nada muda: o B54 nao cabe e o T degrada como antes. Com a paridade do T
    invertida a peca dele vai para a outra fiada e volta a caber."""
    ctx = S.build_context(planta())
    ti, ci = no_t(ctx), no_canto(ctx)
    node = dict(ctx["nodes"][ti])
    walls, opw, nodes, e2n = ctx["walls"], ctx["openings_per_wall"], ctx["nodes"], ctx["e2n"]
    principal = node["main_wall_idx"]
    canto_na_mesma = {ci: ({"wall_idx": principal, "course": "A"}, None)}
    ok, medida = ws._t_intersection_room_ok_in_own_course(node, walls, opw, nodes, e2n, ti, canto_na_mesma)
    assert ok is False and abs(medida["room_minus_ft"] * CM - 23.0) < 0.1
    node["_tie_parity_flip"] = True
    ok, medida = ws._t_intersection_room_ok_in_own_course(node, walls, opw, nodes, e2n, ti, canto_na_mesma)
    assert ok is True and medida["course"] == "B"
    # sem `solved` (chamador antigo) nao ha' resgate
    assert ws._t_intersection_room_ok_in_own_course(node, walls, opw, nodes, e2n, ti, None)[0] is False


@pytest.mark.parametrize("ligada,codigo,motivo", [(True, "B54", "T_INTERSECTION_MAIN"),
                                                  (False, "B34", "T_INTERSECTION_DEGRADED_L")])
def test_solver_de_encontros_poe_B54_na_principal(ligada, codigo, motivo):
    ctx = S.build_context(planta())
    ti = no_t(ctx)
    with chave(ligada):
        out = m.solve_all_intersections(ctx["nodes"], ctx["walls"], S.catalog(), ctx["openings_per_wall"],
                                        ctx["e2n"])
    principal = ctx["nodes"][ti]["main_wall_idx"]
    pecas = [c for c in out["candidates"] if c.get("node_index") == ti and c.get("wall_idx") == principal]
    assert [(c["logical_code"], c["placement_reason"]) for c in pecas] == [(codigo, motivo)]
    assert not out["failures"]


# ================================================= 2. solve real
def _confere_sem_junta_na_face(ctx, res):
    linhas = fileiras(ctx, res)
    passou = cortou = 0
    for ci, itens in sorted(linhas.items()):
        if passa(itens):
            passou += 1
            no = [it for it in itens if it[0] < 57.0 < it[1]][0]
            assert no[2] == "B54" and no[0] < JUNTA_LO - 1.0 and no[1] > JUNTA_HI + 1.0, (ci, itens)
            assert any(abs(x - 57.0) <= 0.5 for x in no[3]), ("celula central fora do no'", ci, no)
            for x in juntas(itens):
                assert abs(x - JUNTA_LO) > TOL_JUNTA and abs(x - JUNTA_HI) > TOL_JUNTA, (ci, x, itens)
        else:
            cortou += 1
            assert all(hi <= JUNTA_LO + 0.1 or lo >= JUNTA_HI - 0.1 for lo, hi, _c, _cel in itens), (ci, itens)
    assert passou and cortou
    assert not corrida(auditoria(ctx, res)), auditoria(ctx, res)
    assert not res.get("collisions")
    return linhas


def test_t_com_toco_de_35_cm_sem_junta_corrida_na_face():
    ctx, res = resolve(planta())
    _confere_sem_junta_na_face(ctx, res)
    assert all(not corrida(a) for a in (res.get("wall_bond_audits") or {}).values())


def test_toco_fechado_pela_sobra():
    """Toda fiada cobre a principal do comeco a' ponta livre (so' juntas de
    1 cm e o quadrado do no' na fiada cortada); a sobra entre o B54 e a ponta
    livre fecha com o catalogo da 86.6 e a fiada cortada fecha o toco com B34."""
    ctx, res = resolve(planta())
    comp = 99.0
    for ci, itens in sorted(fileiras(ctx, res).items()):
        assert abs(itens[-1][1] - comp) <= 0.5, (ci, itens)
        for a, b in zip(itens, itens[1:]):
            vao = b[0] - a[1]
            assert vao <= 1.5 or (abs(a[1] - FACE_LO) <= 1.5 and abs(b[0] - FACE_HI) <= 1.5), (ci, a, b)
        if any(c.startswith("CHANNEL") for _lo, _hi, c, _cel in itens):
            continue
        if passa(itens):
            no = [it for it in itens if it[0] < 57.0 < it[1]][0]
            toco = [it for it in itens if it[0] >= no[1]]
            sobra = int(round(comp - no[1] - 1.0))
            assert sorted(c for _lo, _hi, c, _cel in toco) == sorted(SOBRA[sobra]), (ci, sobra, toco)
        else:
            toco = [it for it in itens if it[0] >= JUNTA_HI - 0.1]
            assert [c for _lo, _hi, c, _cel in toco] == ["B34"], (ci, toco)


def test_chave_desligada_reproduz_a_junta_corrida_na_face():
    """Prova causal: sem a 86.15 o mesmo solve volta a degradar o T e a junta a
    prumo aparece na face da que chega, em todas as fiadas."""
    ctx, res = resolve(planta(), ligada=False)
    achados = corrida(auditoria(ctx, res))
    assert achados and "49.5" in achados[0], achados
    linhas = fileiras(ctx, res)
    passando = [itens for itens in linhas.values() if passa(itens)]
    assert passando and all(any(abs(x - JUNTA_LO) <= TOL_JUNTA for x in juntas(itens)) for itens in passando)


def test_determinismo():
    a = fileiras(*resolve(planta()))
    b = fileiras(*resolve(planta()))
    assert a == b


@pytest.mark.parametrize("invertido,ordem", [(True, (0, 1, 2)), (False, (2, 1, 0)), (True, (2, 0, 1)),
                                             (False, (1, 2, 0))])
def test_sentido_do_eixo_invertido_e_ordem_das_paredes(invertido, ordem):
    """Com o eixo da principal invertido (o toco no comeco do eixo) ou outra
    ordem das paredes (o T resolvido antes do canto), o resultado fisico do no'
    e' o mesmo: B54 em x = 30-84 com a celula central sobre o no' e nenhuma
    junta na face."""
    ref = _confere_sem_junta_na_face(*resolve(planta()))
    ctx, res = resolve(planta(invertido=invertido, ordem=ordem))
    linhas = _confere_sem_junta_na_face(ctx, res)

    def pecas_do_no(fil):
        return sorted(set(it[:3] for itens in fil.values() for it in itens if it[0] < 57.0 < it[1]))
    assert pecas_do_no(linhas) == pecas_do_no(ref) == [(30.0, 84.0, "B54")]


def test_mini_planta_real_do_corpus_W29_W09_W13():
    """Geometria REAL do BUTANTA (W29 + W09 + W13, sem aberturas, 4 fiadas): com
    a 86.15 a W29 passa o no' com B54 e a auditoria aprova; sem ela, junta
    corrida em X~49,5 (o defeito medido no Revit)."""
    keys = [w["key"] for w in CORPUS["walls"]]
    sub = dict(CORPUS, walls=[CORPUS["walls"][keys.index(k)] for k in ("W29", "W09", "W13")], openings=[])
    for ligada in (True, False):
        ctx, res = resolve(sub, fiadas=4, ligada=ligada)
        achados = corrida(auditoria(ctx, res, "W29"))
        if ligada:
            assert not achados and not res.get("collisions"), achados
            wi = ctx["keys"].index("W29")
            cods = set(c["logical_code"] for lst in res["course_candidates"].values() for c in lst
                       if c.get("wall_idx") == wi)
            assert "B54" in cods
        else:
            assert achados and "49.5" in achados[0], achados


@contextlib.contextmanager
def sem_guarda_de_fase():
    antes = ws.T_MAIN_ROOM_PHASE_PENALTY
    ws.T_MAIN_ROOM_PHASE_PENALTY = 0
    try:
        yield
    finally:
        ws.T_MAIN_ROOM_PHASE_PENALTY = antes


def test_mini_planta_real_W31_W07_W13_a_busca_de_fase_escolhe_a_relacao_do_B54():
    """W31: a ponta 0 nao e' canto, e' a ponta da que CHEGA num T da W07 (que
    tambem tem toco). Na mini-planta real (sem aberturas, 4 fiadas) a busca de
    fase (86.2) so' via as pecas dos estados uniformes e escolhia a relacao em
    que o B34 do T da W07 deita na MESMA fiada do T da W31 - o B54 nao cabia e a
    junta a prumo voltava. Com a penalidade da 86.15 nas tabelas da busca a
    relacao certa e' escolhida."""
    keys = [w["key"] for w in CORPUS["walls"]]
    sub = dict(CORPUS, walls=[CORPUS["walls"][keys.index(k)] for k in ("W31", "W07", "W13")], openings=[])
    ctx, res = resolve(sub, fiadas=4)
    assert not corrida(auditoria(ctx, res, "W31")) and not res.get("collisions")
    assert all(not corrida(a) for a in (res.get("wall_bond_audits") or {}).values())
    wi = ctx["keys"].index("W31")
    assert "B54" in set(c["logical_code"] for lst in res["course_candidates"].values() for c in lst
                        if c.get("wall_idx") == wi)
    with sem_guarda_de_fase():
        ctx0, res0 = resolve(sub, fiadas=4)
    assert corrida(auditoria(ctx0, res0, "W31")), "sem a guarda a busca de fase escolhia a relacao ruim"


def test_guarda_de_fase_so_marca_a_relacao_em_que_a_ponta_deita_na_fiada_do_T():
    ctx = S.build_context(planta())
    ti, ci = no_t(ctx), no_canto(ctx)
    walls, opw, nodes, e2n = ctx["walls"], ctx["openings_per_wall"], ctx["nodes"], ctx["e2n"]
    principal = nodes[ti]["main_wall_idx"]
    moveis = set([ti, ci])
    mesma = [{"wall_idx": principal, "course": "A"}]
    outra = [{"wall_idx": principal, "course": "B"}]
    conflito = ws._phase_t_main_room_conflict
    assert conflito(nodes, walls, opw, e2n, principal, ti, 0, moveis, ci, mesma) is True
    assert conflito(nodes, walls, opw, e2n, principal, ti, 0, moveis, ci, outra) is False
    # T invertido: a peca dele vai para a fiada B
    assert conflito(nodes, walls, opw, e2n, principal, ti, 1, moveis, ci, outra) is True
    assert conflito(nodes, walls, opw, e2n, principal, ti, 1, moveis, ci, mesma) is False
    # o no' do T nao e' mutado pela sonda
    assert not nodes[ti].get("_tie_parity_flip")
    # so' vale para a parede principal do T e para no' de PONTA dela
    assert conflito(nodes, walls, opw, e2n, nodes[ti]["incoming_wall_idx"], ti, 0, moveis, ci, mesma) is False
    assert conflito(nodes, walls, opw, e2n, principal, ci, 0, moveis, ti, mesma) is False


def test_guarda_de_fase_nao_toca_T_que_cabe_no_pior_caso():
    """T longe do canto (o B54 cabe no pior caso): nenhuma relacao e' marcada."""
    longe = planta()
    longe["walls"][0] = dict(longe["walls"][0], p0_cm=[-200.0, 0.0])
    longe["walls"][1] = dict(longe["walls"][1], p0_cm=[-193.0, 7.0], p1_cm=[-193.0, -700.0])
    ctx = S.build_context(longe)
    ti, ci = no_t(ctx), no_canto(ctx)
    principal = ctx["nodes"][ti]["main_wall_idx"]
    assert ws._t_intersection_room_ok(ctx["nodes"][ti], ctx["walls"], ctx["openings_per_wall"], nodes=ctx["nodes"],
                                      end_to_node=ctx["e2n"], node_index=ti)
    assert ws._phase_t_main_room_conflict(ctx["nodes"], ctx["walls"], ctx["openings_per_wall"], ctx["e2n"],
                                          principal, ti, 0, set([ti, ci]), ci,
                                          [{"wall_idx": principal, "course": "A"}]) is False


# ============================================ 3. corpus BUTANTA (so' o grafo)
def test_corpus_butanta_so_os_tres_T_das_paredes_de_99_cm_mudam():
    """No grafo do corpus (34 paredes, tocos modulados como no produto), a
    medida na fiada do T so' resgata os 3 T das paredes de 99 cm (W29, W30,
    W31 x W13/W24/W13); os outros 34 T ficam como estavam."""
    ctx = S.build_context(CORPUS)
    antes = ws.T_ROOM_PHYSICAL_TOLERANCE
    ws.T_ROOM_PHYSICAL_TOLERANCE = True      # secao 74, como o produto
    try:
        resgatados = set()
        for i, node in S.tee_nodes(ctx):
            pior = ws._t_intersection_room_ok(node, ctx["walls"], ctx["openings_per_wall"], nodes=ctx["nodes"],
                                              end_to_node=ctx["e2n"], node_index=i)
            proprio, _medida = ws._t_intersection_room_ok_in_own_course(
                node, ctx["walls"], ctx["openings_per_wall"], ctx["nodes"], ctx["e2n"], i, {})
            if not pior and proprio:
                resgatados.add(S.node_key(ctx, i))
    finally:
        ws.T_ROOM_PHYSICAL_TOLERANCE = antes
    assert resgatados == {"T@1192.0,1437.0", "T@1192.0,737.0", "T@1192.0,1937.0"}, resgatados


# ============================================ 4. chave e IronPython 2.7
def test_chave_ligada_no_produto_e_citada_na_regra():
    assert ws.T_MAIN_ROOM_IN_OWN_COURSE_ENABLED is True
    regras = io.open(os.path.join(ROOT, "nuvem", "REGRAS_MODULACAO_BLOCOS.md"), encoding="utf-8").read()
    assert "### 86.15" in regras and "T_MAIN_ROOM_IN_OWN_COURSE_ENABLED" in regras
    fonte = io.open(os.path.join(ROOT, "nuvem", "core", "engine", "wall_stepper.py"), encoding="utf-8").read()
    assert "SECAO 86.15" in fonte


def test_modulo_tocado_compativel_com_ironpython27():
    proibidos = tuple(getattr(ast, n) for n in ("JoinedStr", "Nonlocal", "NamedExpr", "YieldFrom", "AnnAssign",
                                                 "AsyncFunctionDef", "AsyncFor", "AsyncWith", "Await", "Match")
                      if hasattr(ast, n))
    arvore = ast.parse(io.open(os.path.join(ROOT, "nuvem", "core", "engine", "wall_stepper.py"),
                               encoding="utf-8").read())
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
    assert not achados, achados[:10]
