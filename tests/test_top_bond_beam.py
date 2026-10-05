# -*- coding: utf-8 -*-
"""SECAO 86.7 / 86.8 (2026-10-01) - aproximacao do projeto humano BUTANTA R08_LT.

86.7 - CINTA DE TOPO (TOP_BOND_BEAM), VARIANTE A: a ULTIMA fiada vira canaleta
continua (tambem sobre os vaos) trocando peca a peca a grade ja' resolvida
(B39->U39, B34->U34, B19->U19, compensador fundido em U39/U_CUT, B54 de
preenchimento -> U34+U19), mas no QUADRADO de cada no' L/T/X continua o BLOCO
de amarracao (canaleta nunca amarra - regra 75). Ocupacao unica com a verga
que cai na ultima fiada (51.10). Nos dois caminhos (None e CHANNEL).

86.8 - passagem livre (51.9) tambem sem CHANNEL e apoio preferencial de 40 cm
para verga de vao >= 140 cm.

Fixtures sinteticas (nenhum ID do projeto). 13 fiadas, como o pavimento do
humano: verga na 11, cinta na 12.

    py -3 -m pytest tests/test_top_bond_beam.py -q
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pytest
import test_channel_reinforcement as tcr  # noqa: E402
from core.engine import opening_reinforcement as orf  # noqa: E402
from core.engine import wall_stepper as ws  # noqa: E402

m, ft, seg = tcr.m, tcr.ft, tcr.seg
CAT = tcr.sb.CATALOG
NUM = 13
TOP = NUM - 1
ESTRATEGIAS = [None, tcr.CHANNEL]


def _l_corner():
    """U: parede de 400 cm com janela entre dois cantos L (as pernas de 300 cm
    terminam em ponta livre); os dois cantos amarram."""
    return ([seg(0, 0, 400, 0), seg(0, 0, 0, 300), seg(400, 0, 400, 300)],
            [[(ft(150), ft(270), ft(100), ft(221))], [], []])


def _verga_na_ultima_fiada():
    """Porta com topo em 241: a verga cai na fiada 12 (a ultima com 13 fiadas)."""
    return [seg(0, 0, 600, 0)], [[(ft(200), ft(300), ft(0), ft(241))]]


def _vao_grande():
    """Janela de 141 cm numa parede livre (vao >= 140: apoio preferencial 40)."""
    return [seg(0, 0, 700, 0)], [[(ft(260), ft(401), ft(100), ft(221))]]


def _vao_medio():
    return [seg(0, 0, 700, 0)], [[(ft(260), ft(381), ft(100), ft(221))]]


FIXTURES = {"free_wall": tcr.free_wall, "tee": lambda: tcr.tee(80.0), "l_corner": _l_corner,
            "verga_topo": _verga_na_ultima_fiada, "passage": tcr.passage, "vao_grande": _vao_grande,
            "vao_medio": _vao_medio}
_CACHE = {}


def _solve(nome, estrategia=None, beam=True, ftt=True, policy=None, num=NUM, follow=True):
    """`follow=False` desliga a SECAO 86.12 (canaleta segue a fiada c-2): o contrato
    da 86.7 isolado (troca no lugar, fundir so' remove junta)."""
    chave = (nome, estrategia, beam, ftt, repr(sorted((policy or {}).items())), num, follow)
    if chave not in _CACHE:
        antes = (m.TOP_BOND_BEAM_ENABLED, m.FREE_TO_TOP_WITHOUT_CHANNEL_ENABLED, m.CHANNEL_GRID_FOLLOW_ENABLED)
        m.TOP_BOND_BEAM_ENABLED, m.FREE_TO_TOP_WITHOUT_CHANNEL_ENABLED = beam, ftt
        m.CHANNEL_GRID_FOLLOW_ENABLED = follow
        try:
            lines, ops = FIXTURES[nome]()
            _CACHE[chave] = tcr.solve(lines, ops, strategy=estrategia, policy=policy, num_courses=num)
        finally:
            (m.TOP_BOND_BEAM_ENABLED, m.FREE_TO_TOP_WITHOUT_CHANNEL_ENABLED,
             m.CHANNEL_GRID_FOLLOW_ENABLED) = antes
    return _CACHE[chave]


def _rows(res, walls, wi, ci):
    return orf._wall_strip_pieces(res["course_candidates"][ci], walls, wi)


def _own(rows, wi):
    return [r for r in rows if r["cand"].get("wall_idx") == wi]


def _joints(rows):
    return [round((a["hi"] + b["lo"]) / 2.0, 2) for a, b in zip(rows, rows[1:]) if 0.0 <= b["lo"] - a["hi"] <= 2.5]


def _sig(res, ci):
    return sorted(orf._physical_key(c) for c in res["course_candidates"][ci])


def _sem_invasao(res, walls, openings):
    """Nenhuma peca no vao, nenhuma colisao, nada pulado pela regra 48."""
    pf = m.controlled_beta_preflight(res, walls, openings, CAT, 0.0)
    plano = m.materialization_plan(res, pf)
    return not pf.get("opening_violations") and not pf.get("collisions") and not plano["skip"]


# ------------------------------------------------------------------ defaults
def test_chaves_da_secao_86_ligadas_por_padrao():
    assert m.TOP_BOND_BEAM_ENABLED is True
    assert m.FREE_TO_TOP_WITHOUT_CHANNEL_ENABLED is True
    pol = orf.channel_policy()
    assert pol["large_span_cm"] == 140.0 and pol["min_support_large_span_cm"] == 40.0
    assert tuple(pol["large_span_roles"]) == (orf.ROLE_ABOVE_OPENING,)
    assert orf.DEFAULT_TOP_BOND_BEAM_POLICY["variant"] == orf.TOP_BOND_BEAM_VARIANT_A


# ------------------------------------------------------------------ 86.7 cinta
@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_cinta_troca_a_ultima_fiada_peca_a_peca_sem_junta_nova(estrategia):
    # contrato da 86.7 ISOLADO: a SECAO 86.12 (2026-10-05, correcao do usuario) muda de
    # proposito a grade da cinta - segue a f10 sobre alvenaria e e' livre sobre o vao
    # (tests/test_channel_grid_follow_86_12.py) - e por isso fica desligada aqui
    com, walls, _n, _o = _solve("free_wall", estrategia, follow=False)
    sem, walls0, _n0, _o0 = _solve("free_wall", estrategia, beam=False, follow=False)
    # as outras fiadas nao mudam
    for ci in range(TOP):
        assert _sig(com, ci) == _sig(sem, ci), ci
    antes, depois = _own(_rows(sem, walls0, 0, TOP), 0), _own(_rows(com, walls, 0, TOP), 0)
    assert depois and all(orf.is_channel_code(r["cand"]["logical_code"]) for r in depois)
    assert all(orf.is_top_bond_beam_piece(r["cand"]) for r in depois)
    # mesma cobertura e so' juntas que ja' existiam (fundir so' remove junta)
    assert tcr._covered(depois) == tcr._covered(antes)
    assert set(_joints(depois)) <= set(_joints(antes))
    # troca 1:1 de comprimento
    mapa = {"B39": "CHANNEL_U_39", "B34": "CHANNEL_U_34", "B19": "CHANNEL_U_19"}
    por_lo = dict((round(r["lo"], 2), r) for r in depois)
    for r in antes:
        code = r["cand"]["logical_code"]
        if code in mapa and round(r["lo"], 2) in por_lo and abs(por_lo[round(r["lo"], 2)]["hi"] - r["hi"]) < 0.05:
            assert por_lo[round(r["lo"], 2)]["cand"]["logical_code"] == mapa[code]
    tb = com["top_bond_beam"]
    assert tb["applied"] and tb["course_index"] == TOP and tb["variant"] == orf.TOP_BOND_BEAM_VARIANT_A
    assert tb["audit"]["counts"]["TOP_BOND_BEAM_BLOCK_NOT_CONVERTED"] == 0
    assert tb["audit"]["counts"]["TOP_BOND_BEAM_WRONG_COURSE"] == 0
    assert tb["audit"]["counts"]["beam_pieces"] == tb["counts"]["channel_pieces"] == len(depois)


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_cinta_continua_sobre_os_vaos_sem_fiada_de_bloco_ate_a_verga(estrategia):
    """Humano 38/38: verga (f11) + cinta (f12) = canaleta dupla sobre o vao."""
    res, walls, _n, _o = _solve("free_wall", estrategia)
    for t_lo, t_hi in ((200.0, 300.0), (400.0, 520.0)):
        for ci in (TOP - 1, TOP):
            sobre = tcr.codes_over(res, walls, 0, ci, t_lo, t_hi)
            assert sobre and all(orf.is_channel_code(c) for c in sobre), (ci, sobre)
    relacao = res["top_bond_beam"]["lintel_beam"]
    assert len(relacao) == 2
    assert all(x["lintel_course"] == TOP - 1 and x["block_courses_between"] == 0 for x in relacao)


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
@pytest.mark.parametrize("nome", ["tee", "l_corner"])
def test_cinta_mantem_o_bloco_de_amarracao_no_quadrado_do_no(nome, estrategia):
    """Variante A: no quadrado do no' continua o B34/B54 (canaleta nunca amarra)."""
    com, walls, nodes, _o = _solve(nome, estrategia)
    sem, walls0, _n0, _o0 = _solve(nome, estrategia, beam=False)
    tb = com["top_bond_beam"]
    assert tb["counts"]["kept_tie"] >= 1
    assert tb["audit"]["counts"]["TOP_BOND_BEAM_CHANNEL_AT_NODE"] == 0
    assert tb["audit"]["counts"]["TOP_BOND_BEAM_TIE_ROLE"] == 0
    assert tb["audit"]["counts"]["TOP_BOND_BEAM_BLOCK_NOT_CONVERTED"] == 0
    # toda peca de amarracao da ultima fiada continua igual (codigo e posicao)
    amarracoes = lambda res: sorted(orf._physical_key(c) for c in res["course_candidates"][TOP] if orf._is_tie(c))
    assert amarracoes(com) and amarracoes(com) == amarracoes(sem)
    assert not [c for c in com["course_candidates"][TOP] if orf._is_tie(c) and orf.is_channel_code(c["logical_code"])]
    # nenhuma canaleta da cinta dentro do quadrado de um no' (geometria do grafo)
    for wi in range(len(walls)):
        quadrados = orf._node_squares_cm(walls, nodes, wi)
        for r in _own(_rows(com, walls, wi, TOP), wi):
            if orf.is_top_bond_beam_piece(r["cand"]):
                assert orf._square_hit(r["lo"], r["hi"], quadrados, 0.5) is None, (wi, r["lo"], r["hi"])
    # os gates de amarracao nao mudam: regra 75 vazia e 76.1 igual
    assert com["channel_as_junction_bond"] == []
    assert len(com.get("missing_required_junction_bond") or []) == len(sem.get("missing_required_junction_bond") or [])
    assert (com.get("junction_bond_audit") or {}).get("valid") == (sem.get("junction_bond_audit") or {}).get("valid")


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_validacao_nao_acusa_a_cinta_como_canaleta_sem_demanda(estrategia):
    for nome in ("free_wall", "tee", "l_corner"):
        res, walls, _n, openings = _solve(nome, estrategia)
        counts = res["opening_reinforcement"]["validation"]["counts"]
        assert counts["top_bond_beam_pieces"] == res["top_bond_beam"]["counts"]["channel_pieces"] > 0, nome
        for key in ("CHANNEL_WRONG_COURSE", "EXTRA_CHANNEL", "CHANNEL_INVADES_OPENING", "CHANNEL_COLLISION",
                    "MISSING_REQUIRED_CHANNEL"):
            assert counts[key] == 0, (nome, key)
        assert _sem_invasao(res, walls, openings), nome
        # fonte unica: candidates = chaves fisicas distintas de course_candidates
        # (a mesma chave em varias fiadas conta uma vez) - a cinta entra nela
        chaves = set(orf._physical_key(c) for c in res["candidates"])
        assert all(orf._physical_key(c) in chaves for c in res["course_candidates"][TOP]), nome


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_ocupacao_unica_com_a_verga_na_ultima_fiada(estrategia):
    """51.10: a verga que cai na ultima fiada fica com o papel de abertura; a
    cinta cobre o resto da fiada sem duplicar peca."""
    com, walls, _n, openings = _solve("verga_topo", estrategia)
    sem, walls0, _n0, _o0 = _solve("verga_topo", estrategia, beam=False)
    verga = [c for c in sem["course_candidates"][TOP] if orf.is_channel_code(c["logical_code"])]
    assert verga, "a verga deveria cair na ultima fiada nesta fixture"
    pecas = com["course_candidates"][TOP]
    papeis = [tuple((c.get("reinforcement") or {}).get("roles") or ()) for c in pecas
              if orf.is_channel_code(c["logical_code"])]
    assert (orf.ROLE_ABOVE_OPENING,) in papeis and (orf.ROLE_TOP_BOND_BEAM,) in papeis
    assert not [p for p in papeis if len(p) > 1]                  # nunca dois papeis numa peca
    # as pecas da verga sao as mesmas (nenhuma substituida pela cinta)
    assert sorted(orf._physical_key(c) for c in verga) == sorted(
        orf._physical_key(c) for c in pecas if not orf.is_top_bond_beam_piece(c) and orf.is_channel_code(c["logical_code"]))
    assert com["top_bond_beam"]["counts"]["shared_with_opening"] == len(verga)
    assert com["top_bond_beam"]["lintel_beam"][0]["lintel_is_beam_course"] is True
    assert tcr._covered(_own(_rows(com, walls, 0, TOP), 0)) == tcr._covered(_own(_rows(sem, walls0, 0, TOP), 0))
    counts = com["opening_reinforcement"]["validation"]["counts"]
    assert counts["CHANNEL_COLLISION"] == 0 and counts["EXTRA_CHANNEL"] == 0 and counts["CHANNEL_WRONG_COURSE"] == 0
    assert counts["channel_top_matched"] == counts["channel_top_expected"] == 1


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_cinta_desligada_mantem_a_ultima_fiada_de_bloco(estrategia):
    res, _w, _n, _o = _solve("free_wall", estrategia, beam=False)
    assert "top_bond_beam" not in res
    assert not [c for c in res["course_candidates"][TOP] if orf.is_channel_code(c["logical_code"])]


def test_legado_historico_nao_tem_cinta():
    lines, ops = tcr.free_wall()
    res, _w, _n, _o = tcr.solve(lines, ops, strategy=tcr.LEGADO_HISTORICO, num_courses=NUM)
    assert "top_bond_beam" not in res and tcr.channel_count(res) == 0


def test_familias_de_canaleta_ausentes_nao_convertem_a_cinta():
    lines, ops = tcr.free_wall()
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    res = m.solve_building_blocks_all_courses(nodes, walls, e2n, ops, CAT, 0.0, NUM,
                                              variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE,
                                              opening_reinforcement_strategy=None,
                                              opening_structural_channel_available=False)
    assert res["top_bond_beam"]["applied"] is False
    assert res["top_bond_beam"]["reason"] == "CHANNEL_FAMILY_MISSING"
    assert tcr.channel_count(res) == 0


def test_cinta_nunca_decide_a_paridade_dos_nos():
    """A cinta e' pos-passe que COPIA a grade: as medidas da paridade 82.1 (que
    rodam sobre o resultado FINAL) leem a ultima fiada de bloco de antes da cinta.
    Sem isso a fusao dos compensadores escondia o excesso da regra #2 e virava a
    paridade do L da CR-S1 (tests/test_solver_l_node_alternation_cr_s1.py)."""
    com, walls, nodes, _o = _solve("tee", None)
    sem, walls0, nodes0, _o0 = _solve("tee", None, beam=False)
    for ci in range(TOP):
        assert _sig(com, ci) == _sig(sem, ci), ci
    vista = m._without_top_bond_beam(com)
    assert vista is not com and vista["course_candidates"] is not com["course_candidates"]
    assert _sig(vista, TOP) == _sig(sem, TOP)
    assert _sig(com, TOP) != _sig(sem, TOP)                       # a cinta existe de fato
    tes = [i for i, n in enumerate(nodes) if n.get("kind") == "T_INTERSECTION"]
    assert m._tie_parity_compensator_crowding(vista, nodes, walls, CAT, tes) == \
        m._tie_parity_compensator_crowding(sem, nodes0, walls0, CAT, tes)
    # sem cinta so' voltam as fiadas que a SECAO 86.12 (alinhamento da verga) tocou
    seguidas = (sem.get("channel_grid_follow") or {}).get("source_courses") or {}
    vista_sem = m._without_top_bond_beam(sem)
    if not seguidas:
        assert vista_sem is sem                                    # sem cinta: nada muda
    for ci in range(NUM):
        esperado = seguidas.get(ci, sem["course_candidates"][ci])
        assert _sig(vista_sem, ci) == sorted(orf._physical_key(c) for c in esperado), ci


def test_cinta_e_deterministica():
    a, _w, _n, _o = _solve("tee", None)
    lines, ops = tcr.tee(80.0)
    b, _w2, _n2, _o2 = tcr.solve(lines, ops, strategy=None, num_courses=NUM)
    assert _sig(a, TOP) == _sig(b, TOP)
    assert a["top_bond_beam"]["runs"] == b["top_bond_beam"]["runs"]


# ------------------------------------------------- 86.7 planejador isolado
def _peca(code, lo, hi, reason="STANDARD_FILL", z=241.0, wall_idx=0):
    origin = m.XYZ(ft((lo + hi) / 2.0), 0.0, ft(z))
    return ws._make_block_candidate(code, CAT[code], TOP, origin, m.XYZ(1.0, 0.0, 0.0), reason, wall_idx=wall_idx)


def test_planejador_funde_compensador_divide_b54_de_preenchimento_e_mantem_amarracao():
    walls = [(seg(0, 0, 400, 0), ft(14.0), (False, False))]
    verga = dict(_peca("B39", 300.0, 339.0), logical_code=orf.CHANNEL_U_39,
                 reinforcement={"roles": [orf.ROLE_ABOVE_OPENING], "run_id": "x"})
    topo = [_peca("B34", 0.0, 34.0, reason="L_CORNER"), _peca("B39", 35.0, 74.0), _peca("C04", 75.0, 79.0),
            _peca("B34", 80.0, 114.0), _peca("B54", 115.0, 169.0), _peca("B19", 170.0, 189.0),
            _peca("C09", 190.0, 199.0), _peca("B39", 200.0, 239.0), verga]
    baixo = [_peca("B39", 0.0, 39.0, z=221.0), _peca("B39", 40.0, 79.0, z=221.0), _peca("B39", 80.0, 119.0, z=221.0),
             _peca("B39", 120.0, 159.0, z=221.0), _peca("B39", 160.0, 199.0, z=221.0)]
    cc = {TOP - 1: baixo, TOP: topo}
    plano = orf.plan_top_bond_beam(cc, walls, NUM)
    assert cc[TOP] is topo and len(topo) == 9                    # entrada intacta
    rows = orf._wall_strip_pieces(plano["course_candidates"][TOP], walls, 0)
    got = [(r["cand"]["logical_code"], round(r["lo"], 1), round(r["hi"], 1)) for r in rows]
    assert got[0] == ("B34", 0.0, 34.0)                          # amarracao fica bloco
    assert ("CHANNEL_U_39", 35.0, 74.0) in got
    # C04 encostado no B34 seguinte: B34 + C04 = 39 (comprimento padrao, 51.3)
    assert ("CHANNEL_U_39", 75.0, 114.0) in got
    # B54 de preenchimento -> U34+U19, junta nova longe das juntas de baixo (119,5 / 159,5)
    split = [g for g in got if 115.0 - 0.1 <= g[1] and g[2] <= 169.0 + 0.1]
    assert sorted(g[0] for g in split) == ["CHANNEL_U_19", "CHANNEL_U_34"]
    nova = [g[2] + 0.5 for g in split if g[2] < 168.0][0]
    assert min(abs(nova - j) for j in (119.5, 159.5)) >= 1.5
    # B19 + C09 = 29: canaleta cortada (51.3), a verga fica como esta'
    assert ("CHANNEL_U_CUT", 170.0, 199.0) in got
    assert ("CHANNEL_U_39", 200.0, 239.0) in got and ("CHANNEL_U_39", 300.0, 339.0) in got
    c = plano["counts"]
    assert c["kept_tie"] == 1 and c["b54_split"] == 1 and c["shared_with_opening"] == 1
    assert c["source_pieces_converted"] == 7
    beam = [r["cand"] for r in rows if orf.is_top_bond_beam_piece(r["cand"])]
    assert len(beam) == c["channel_pieces"] == 6
    assert all(x["reinforcement"]["roles"] == [orf.ROLE_TOP_BOND_BEAM] for x in beam)
    assert orf.channel_as_junction_bond(plano["course_candidates"]) == []
    cortada = [x for x in beam if x["logical_code"] == orf.CHANNEL_U_CUT][0]
    assert cortada["instance_length_cm"] == pytest.approx(29.0)
    assert cortada["reinforcement"]["source_codes"] == ["B19", "C09"]
    assert sorted(x["reinforcement"]["source_codes"][0] for x in beam
                  if "B54_SPLIT" in x["reinforcement"]["source_codes"]) == ["B54_SPLIT", "B54_SPLIT"]


def test_auditoria_acusa_canaleta_no_quadrado_do_no_mutante():
    """Teste nao vacuo: uma canaleta da cinta posta no quadrado de um no' (o que
    a variante B faria) e' acusada pela auditoria independente."""
    com, walls, nodes, _o = _solve("tee", None)
    cc = dict((ci, list(p)) for ci, p in com["course_candidates"].items())
    tie = [c for c in cc[TOP] if orf._is_tie(c) and c.get("wall_idx") == 0][0]
    mutante = dict(tie, logical_code=orf.CHANNEL_U_CUT, placement_reason="STANDARD_FILL",
                   reinforcement={"roles": [orf.ROLE_TOP_BOND_BEAM]})
    cc[TOP] = [mutante if c is tie else c for c in cc[TOP]]
    audit = orf.top_bond_beam_audit(cc, walls, nodes, TOP)
    assert audit["counts"]["TOP_BOND_BEAM_CHANNEL_AT_NODE"] >= 1
    # e a mesma peca com a razao de amarracao e' acusada pela regra 75
    cc[TOP] = [dict(mutante, placement_reason=tie["placement_reason"]) if c is mutante else c for c in cc[TOP]]
    assert orf.top_bond_beam_audit(cc, walls, nodes, TOP)["counts"]["TOP_BOND_BEAM_TIE_ROLE"] >= 1
    assert orf.channel_as_junction_bond(cc)


# ------------------------------------------------- 86.8 passagem livre sem CHANNEL
def test_passagem_livre_tambem_sem_channel():
    res, walls, _n, openings = _solve("passage", None)
    assert res["opening_reinforcement"]["free_to_top"], "51.9 sem CHANNEL (86.8)"
    linha = sorted(res["opening_structural_trace"], key=lambda r: r["opening_index"])[0]
    assert linha["lintel_status"] == m.LINTEL_NOT_REQUIRED and linha["lintel_reason"] == "FREE_TO_TOP_PASSAGE_51_9"
    from_ci = res["opening_reinforcement"]["free_to_top"][0]["from_course"]
    for ci in range(from_ci, NUM):
        assert not tcr.codes_over(res, walls, 0, ci, 227, 473), ci
    counts = res["opening_reinforcement"]["validation"]["counts"]
    for key in ("CHANNEL_FREE_TO_TOP_NOT_OPEN", "CHANNEL_OPENING_OVERCUT", "CHANNEL_ORPHAN_PIECE",
                "MISSING_REQUIRED_CHANNEL"):
        assert counts[key] == 0, key
    assert _sem_invasao(res, walls, openings)
    # as mesmas pecas que o CHANNEL nessa geometria (a 51.9 e' a mesma decisao)
    chan, _w, _n2, _o2 = _solve("passage", tcr.CHANNEL)
    assert chan["opening_reinforcement"]["free_to_top"] == res["opening_reinforcement"]["free_to_top"]


def test_passagem_livre_sem_channel_desligada_volta_a_verga():
    res, walls, _n, _o = _solve("passage", None, ftt=False)
    assert res["opening_reinforcement"]["free_to_top"] == []
    linha = res["opening_structural_trace"][0]
    assert linha["lintel_status"] == m.LINTEL_CREATED and linha["lintel_course"] == TOP - 1
    assert tcr.codes_over(res, walls, 0, TOP, 227, 473)


def test_presolve_sem_channel_segue_as_duas_chaves(monkeypatch):
    lines, ops = tcr.passage()
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, _e2n = m.build_wall_graph(walls, jm)
    assert m._presolve_free_to_top(nodes, walls, ops, CAT, 0.0, NUM, None, None)
    monkeypatch.setattr(m, "FREE_TO_TOP_WITHOUT_CHANNEL_ENABLED", False)
    assert m._presolve_free_to_top(nodes, walls, ops, CAT, 0.0, NUM, None, None) == []
    monkeypatch.setattr(m, "FREE_TO_TOP_WITHOUT_CHANNEL_ENABLED", True)
    monkeypatch.setattr(m, "OPENING_STRUCTURAL_REINFORCEMENT_ENABLED", False)
    assert m._presolve_free_to_top(nodes, walls, ops, CAT, 0.0, NUM, None, None) == []
    assert m._presolve_free_to_top(nodes, walls, ops, CAT, 0.0, NUM, tcr.CHANNEL, None)
    assert m._presolve_free_to_top(nodes, walls, ops, CAT, 0.0, NUM, "DESCONHECIDA", None) == []


# ------------------------------------------------- 86.8 apoio de vao grande
def test_apoio_preferencial_por_vao():
    pol = orf.channel_policy()
    assert orf.preferred_support_cm(0.0, 141.0, orf.ROLE_ABOVE_OPENING, pol) == 40.0
    assert orf.preferred_support_cm(0.0, 139.6, orf.ROLE_ABOVE_OPENING, pol) == 40.0   # tolerancia da grade
    assert orf.preferred_support_cm(0.0, 121.0, orf.ROLE_ABOVE_OPENING, pol) == 19.0
    assert orf.preferred_support_cm(0.0, 151.0, orf.ROLE_BELOW_SILL, pol) == 19.0      # contraverga nao
    assert orf.preferred_support_cm(0.0, 300.0, orf.ROLE_ABOVE_OPENING, orf.channel_policy(
        {"large_span_cm": None})) == 19.0


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_verga_de_vao_grande_estende_ate_40_cm(estrategia):
    res, _w, _n, _o = _solve("vao_grande", estrategia)
    linha = res["opening_structural_trace"][0]
    assert linha["lintel_status"] == m.LINTEL_CREATED
    assert linha["lintel_left_support"] >= 40.0 - 1e-6 and linha["lintel_right_support"] >= 40.0 - 1e-6
    rec = res["opening_reinforcement"]["openings"][0]
    assert rec["above"]["preferred_support_cm"] == 40.0
    assert rec["below"]["preferred_support_cm"] == 19.0
    # contraverga continua com o alvo de 19 cm
    assert min(linha["sill_left_support"], linha["sill_right_support"]) >= 19.0 - 1e-6
    # desligada: a verga para no primeiro apoio >= 19 em pelo menos um lado
    off, _w2, _n2, _o2 = _solve("vao_grande", estrategia, policy={"large_span_cm": None})
    lo = off["opening_structural_trace"][0]
    assert off["opening_reinforcement"]["openings"][0]["above"]["preferred_support_cm"] == 19.0
    assert min(lo["lintel_left_support"], lo["lintel_right_support"]) < 40.0
    assert lo["lintel_end"] - lo["lintel_start"] < linha["lintel_end"] - linha["lintel_start"]


@pytest.mark.parametrize("estrategia", ESTRATEGIAS)
def test_vao_abaixo_de_140_nao_muda(estrategia):
    res, _w, _n, _o = _solve("vao_medio", estrategia)
    off, _w2, _n2, _o2 = _solve("vao_medio", estrategia, policy={"large_span_cm": None})
    for ci in range(NUM):
        assert _sig(res, ci) == _sig(off, ci), ci
    assert res["opening_reinforcement"]["openings"][0]["above"]["preferred_support_cm"] == 19.0
