# -*- coding: utf-8 -*-
"""SECAO 77 - PAPEL FUNCIONAL DO ENCONTRO POR FIADA (topologia base em planta,
papel efetivo por fiada/banda com as aberturas ativas naquela altura).

Fixtures SINTETICAS (coordenadas proprias, nenhum id de projeto): uma parede
PRINCIPAL reta (0..604 cm) e uma parede que CHEGA perpendicular em t=302 (T
modular de 14 cm, a mesma topologia de tests/test_regra76_d1_t_degradado.py).
Janelas na principal com peitoril 80 / verga 221 (as cotas do no' real que
motivou a secao). Fiada c ocupa z [20c+1, 20c+20] cm; abertura ativa se
sobrepoe mais de 0,5 cm -> fiadas 4..10 sao as das janelas, 3 e 11 nao.

Casos obrigatorios (decisao de produto 2026-09-22):
  A. duas janelas consumindo a principal dos dois lados -> NONE_FREE_END na
     banda das janelas; a que chega termina LIVRE na face da principal; a
     fiada sai do denominador do gate (NO_FUNCTIONAL_JUNCTION); MISSING 0.
  B. mesma geometria XY sem janelas -> T em todas as fiadas.
  C. uma janela so' -> L (a degradacao que ja' existia), nunca ponta livre.
  D. janelas afastadas (corpo solido sobrando) -> T/L permanece.
  E. porta (abertura desde o piso) -> sem encontro desde a fiada 0.
  F/G. abertura comecando/terminando exatamente na fronteira da fiada.
  H/I. no' no inicio x no fim da parede que chega: peca RENTE a' face nas
     duas orientacoes (o recuo de 1 cm foi corrigido - secao 77.4).
  J/K. translacao e pontas invertidas: mesmo papel.
  Transicao FREE_END -> T: na fiada em que o T volta a peca de amarracao cabe,
     tem apoio, cobre a regiao e nao e' compensador.
  Memo: o papel da banda faz parte da chave do memo por parede.
  Flag OFF reproduz o motor anterior (byte a byte nas fixtures).
  Toco entre a tolerancia e a menor peca: continua encontro (conservador).

    python3 -m pytest tests/test_secao77_papel_por_fiada.py -q
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import test_channel_reinforcement as tcr  # noqa: E402

m, ft, seg = tcr.m, tcr.ft, tcr.seg
from core.engine import wall_stepper as ws  # noqa: E402
from core.engine import junction_role as JR  # noqa: E402
from core.engine import physical_support as _support  # noqa: E402

CAT = tcr.sb.CATALOG
NUM_COURSES = tcr.NUM_COURSES
BAND = m._free_to_top_band(CAT, 0.0)
BAND_WIDTH_FT = ws._cm_to_ft(max(float((CAT.get(c) or {}).get("width_cm") or 0.0)
                                 for c in ws.JUNCTION_BOND_CODES))
COMPRIMENTO = 604.0
NO_T = 302.0
MEIA = 7.0
CHEGA = 298.0
PEITORIL = 80.0
VERGA = 221.0
ESQ = 150.0
DIR = 454.0
JANELA = range(4, 11)          # fiadas atravessadas pelas janelas (peitoril 80, verga 221)
FORA = [c for c in range(NUM_COURSES) if c not in JANELA]


def _cm(v):
    return tcr._cm(v)


def janela(lo, hi, sill=PEITORIL, head=VERGA):
    return (ft(lo), ft(hi), ft(sill), ft(head))


def t_base(janelas, sill=PEITORIL, head=VERGA, no_no_fim=False):
    inc = seg(NO_T, CHEGA, NO_T, 0) if no_no_fim else seg(NO_T, 0, NO_T, CHEGA)
    return [seg(0, 0, COMPRIMENTO, 0), inc], [[janela(a, b, sill, head) for a, b in janelas], []]


def corpo(menos, mais, sill=PEITORIL, head=VERGA, no_no_fim=False):
    """Janelas dos dois lados deixando `menos`/`mais` cm de corpo solido da
    principal alem da faixa do no' [295, 309] (None = sem janela do lado)."""
    js = []
    if menos is not None:
        js.append((ESQ, NO_T - MEIA - menos))
    if mais is not None:
        js.append((NO_T + MEIA + mais, DIR))
    return t_base(js, sill, head, no_no_fim)


def solve(lines, openings, flag=True):
    saved = m.CHANNEL_COURSE_AWARE_JUNCTION_ROLE_ENABLED
    m.CHANNEL_COURSE_AWARE_JUNCTION_ROLE_ENABLED = bool(flag)
    try:
        return tcr.solve(lines, openings)
    finally:
        m.CHANNEL_COURSE_AWARE_JUNCTION_ROLE_ENABLED = saved


def t_node(nodes):
    idx = [i for i, n in enumerate(nodes) if n.get("kind") == "T_INTERSECTION"]
    assert len(idx) == 1, [(i, n.get("kind")) for i, n in enumerate(nodes)]
    return idx[0]


def roles(lines, openings):
    """Tabela de papel (a MESMA que o solve e a auditoria usam) para o no' T."""
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, _e2n = m.build_wall_graph(walls, jm)
    ftt = m._presolve_free_to_top(nodes, walls, openings, CAT, 0.0, NUM_COURSES, tcr.CHANNEL, None)
    ops = m._effective_solve_openings(nodes, walls, openings, CAT, 0.0, NUM_COURSES, ftt, None)
    table = ws.junction_role_table(nodes, walls, ops, BAND, NUM_COURSES, CAT, m.OPENING_COURSE_BAND_TOLERANCE_FT)
    ni = t_node(nodes)
    return dict((ci, table[(ni, ci)]) for ci in range(NUM_COURSES)), walls, nodes, ni


def role_map(lines, openings):
    tab = roles(lines, openings)[0]
    return dict((ci, r["effective_role"]) for ci, r in tab.items())


def region(res, walls, nodes, ni):
    """{fiada: [(codigo, cobertura, razao, parede)]} dos ocupantes da regiao do no'."""
    poly, area, wall_set, _box = ws._bond_regions(nodes, walls, BAND_WIDTH_FT)[ni]
    out = {}
    for ci in range(NUM_COURSES):
        occ = []
        for c in res["course_candidates"].get(ci) or []:
            if c.get("wall_idx") not in wall_set:
                continue
            ov = ws._convex_overlap_area(ws._candidate_polygon(c), poly)
            if ov > area * 1e-6:
                occ.append((c["logical_code"], round(ov / area, 3), str(c.get("placement_reason") or ""),
                            c.get("wall_idx")))
        occ.sort(key=lambda o: -o[1])
        out[ci] = occ
    return out


def pieces(res, walls, wall_idx, course):
    rows = tcr.strip(res, walls, wall_idx, course)
    return sorted((round(r["lo"], 2), round(r["hi"], 2), r["cand"]["logical_code"],
                   str(r["cand"].get("placement_reason") or ""))
                  for r in rows if r["cand"].get("wall_idx") == wall_idx)


def missing(res, ni=None):
    return sorted(f["course_index"] for f in res.get("missing_required_junction_bond") or []
                  if ni is None or f["node_index"] == ni)


def nfj(res, ni):
    return sorted(x["course_index"] for x in (res.get("junction_bond_audit") or {}).get("not_required") or []
                  if x["node_index"] == ni and x.get("reason") == ws.NO_FUNCTIONAL_JUNCTION_REASON)


def hard(res):
    sup = (res.get("physical_support") or {}).get("counts") or {}
    return {"collisions": len(res.get("collisions") or []), "non_modular": len(res.get("non_modular") or []),
            "unsupported": sup.get("UNSUPPORTED_BLOCK", 0) + sup.get("UNSUPPORTED_SMALL_BLOCK", 0),
            "opening_invasion": len(res.get("opening_invasions") or []),
            "channel_as_junction_bond": len(res.get("channel_as_junction_bond") or []),
            "compensator_as_junction_bond": len(res.get("compensator_as_junction_bond") or [])}


ZERO = {"collisions": 0, "non_modular": 0, "unsupported": 0, "opening_invasion": 0,
        "channel_as_junction_bond": 0, "compensator_as_junction_bond": 0}


# =============================================================== A. duas janelas
def test_A_duas_janelas_a_principal_some_e_o_T_deixa_de_existir_na_banda():
    rm = role_map(*corpo(0.0, 0.0))
    assert all(rm[c] == "NONE_FREE_END" for c in JANELA), rm
    assert all(rm[c] == "T" for c in FORA), rm
    tab = roles(*corpo(0.0, 0.0))[0]
    assert tab[5]["reason"] == "NO_BODY:main-,main+"
    assert tab[5]["free_end_wall"] == 1          # a parede que chega termina livre
    assert tab[3]["reason"] == "ALL_ARMS_SOLID" and tab[11]["reason"] == "ALL_ARMS_SOLID"


def test_A_o_solve_termina_a_parede_que_chega_como_ponta_livre_e_o_gate_nao_exige_amarracao():
    res, walls, nodes, _o = solve(*corpo(0.0, 0.0))
    ni = t_node(nodes)
    assert missing(res) == []
    assert nfj(res, ni) == list(JANELA)
    assert res["compensator_as_junction_bond"] == []
    assert hard(res) == ZERO
    inc = nodes[ni]["incoming_wall_idx"]
    L = round(_cm(walls[inc][0].Length), 2)
    reg = region(res, walls, nodes, ni)
    for ci in JANELA:
        # nenhuma peca DE NO' (razao de encontro) e nenhum C09 fingindo ajuste de no'
        assert all(not r.startswith("T_INTERSECTION") and r != "JUNCTION_UNRESOLVED_FILL"
                   for _c, _cov, r, _w in reg[ci]), (ci, reg[ci])
        # a regiao do no' e' 100% da parede que chega (e' a ponta dela)
        assert reg[ci] and reg[ci][0][3] == inc and reg[ci][0][1] >= 0.999, (ci, reg[ci])
        # a peca da ponta vai ate' a face externa da principal (a ponta da
        # parede que esta' no no'; aqui o no' e' o INICIO da parede que chega)
        pcs = pieces(res, walls, inc, ci)
        assert pcs[0][0] == 0.0, (ci, pcs[0])
        # a principal nao poe nada na boneca
        assert all(w != nodes[ni]["main_wall_idx"] for _c, _cov, _r, w in reg[ci]), (ci, reg[ci])
    for ci in FORA:
        assert reg[ci][0][0] in ("B34", "B54") and reg[ci][0][1] >= 0.999, (ci, reg[ci])
        assert reg[ci][0][2].startswith("T_INTERSECTION"), (ci, reg[ci])


def test_A_o_B19_so_aparece_na_ponta_livre_nunca_como_peca_de_no():
    res, walls, nodes, _o = solve(*corpo(0.0, 0.0))
    ni = t_node(nodes)
    inc = nodes[ni]["incoming_wall_idx"]
    for ci in range(NUM_COURSES):
        for lo, hi, code, reason in pieces(res, walls, inc, ci):
            if code == "B19":
                assert reason == "STANDARD_FILL", (ci, lo, hi, reason)
                # fora das fiadas das janelas o B19 nunca encosta na face do no'
                # (t=0, o no' e' o inicio da parede que chega); a outra ponta
                # (t=L) e' uma ponta livre de verdade e pode ter B19
                assert ci in JANELA or lo > 30.0, (ci, lo, hi)


def test_A_com_a_flag_desligada_o_motor_anterior_volta_C09_e_MISSING():
    res, walls, nodes, _o = solve(*corpo(0.0, 0.0), flag=False)
    ni = t_node(nodes)
    assert missing(res) == [5, 7, 9]
    assert nfj(res, ni) == []
    reg = region(res, walls, nodes, ni)
    assert any(c == "C09" and r == "JUNCTION_UNRESOLVED_FILL" for c, _cov, r, _w in reg[5]), reg[5]
    assert res["junction_role_by_course"]["enabled"] is False


# ================================================================ B. sem janelas
def test_B_sem_janelas_o_T_existe_em_todas_as_fiadas_e_nada_muda():
    assert set(role_map(*t_base([])).values()) == {"T"}
    on, walls, _n, _o = solve(*t_base([]))
    off = solve(*t_base([]), flag=False)[0]
    assert tcr.physical_signature(on, walls) == tcr.physical_signature(off, walls)
    assert missing(on) == [] and hard(on) == ZERO


# =============================================================== C. uma janela
def test_C_uma_janela_vira_L_pela_degradacao_existente_nunca_ponta_livre():
    rm = role_map(*corpo(0.0, None))
    assert all(rm[c] == "L" for c in JANELA) and all(rm[c] == "T" for c in FORA), rm
    on, walls, nodes, _o = solve(*corpo(0.0, None))
    off = solve(*corpo(0.0, None), flag=False)[0]
    assert tcr.physical_signature(on, walls) == tcr.physical_signature(off, walls)
    assert missing(on) == [] and nfj(on, t_node(nodes)) == []
    reg = region(on, walls, nodes, t_node(nodes))
    assert reg[5][0][0] == "B34" and reg[5][0][2].startswith("T_INTERSECTION_DEGRADED_L")


# ============================================================ D. janelas afastadas
@pytest.mark.parametrize("menos,mais,esperado", [(20.0, 40.0, "T"), (40.0, 20.0, "T"),
                                                 (5.0, 20.0, "T"), (20.0, 0.0, "L")])
def test_D_com_corpo_solido_sobrando_o_encontro_permanece(menos, mais, esperado):
    rm = role_map(*corpo(menos, mais))
    assert all(rm[c] == esperado for c in JANELA), rm
    assert "NONE_FREE_END" not in rm.values()
    on, walls, _n, _o = solve(*corpo(menos, mais))
    off = solve(*corpo(menos, mais), flag=False)[0]
    assert tcr.physical_signature(on, walls) == tcr.physical_signature(off, walls)
    assert missing(on) == []


# ====================================================================== E. porta
def test_E_porta_desde_o_piso_sem_encontro_desde_a_fiada_0():
    lines, ops = corpo(0.0, 0.0, sill=0.0)
    rm = role_map(lines, ops)
    assert all(rm[c] == "NONE_FREE_END" for c in range(0, 11)), rm
    assert all(rm[c] == "T" for c in range(11, NUM_COURSES)), rm
    res, walls, nodes, _o = solve(lines, ops)
    assert missing(res) == [] and hard(res) == ZERO
    assert nfj(res, t_node(nodes)) == list(range(0, 11))
    assert res.get("intersection_failures") in (None, [])


# ================================================= F/G. fronteira exata de fiada
@pytest.mark.parametrize("sill,fiada3", [(80.0, "T"), (80.4, "T"), (79.6, "T"), (79.4, "NONE_FREE_END")])
def test_F_peitoril_na_fronteira_da_fiada_segue_a_regra_de_atividade_do_solve(sill, fiada3):
    rm = role_map(*corpo(0.0, 0.0, sill=sill))
    assert rm[3] == fiada3 and rm[4] == "NONE_FREE_END", rm


@pytest.mark.parametrize("head,fiada11", [(221.0, "T"), (220.6, "T"), (221.4, "T"), (221.6, "NONE_FREE_END")])
def test_G_verga_na_fronteira_da_fiada_segue_a_regra_de_atividade_do_solve(head, fiada11):
    rm = role_map(*corpo(0.0, 0.0, head=head))
    assert rm[11] == fiada11 and rm[10] == "NONE_FREE_END", rm


# ===================================================== H/I. no' no inicio x no fim
def _face_flush(no_no_fim):
    res, walls, nodes, _o = solve(*corpo(0.0, 0.0, no_no_fim=no_no_fim))
    ni = t_node(nodes)
    inc = nodes[ni]["incoming_wall_idx"]
    L = round(_cm(walls[inc][0].Length), 2)
    out = {}
    for ci in JANELA:
        pcs = pieces(res, walls, inc, ci)
        face = pcs[-1][1] if no_no_fim else pcs[0][0]
        longe = pcs[0][0] if no_no_fim else pcs[-1][1]
        out[ci] = (round(face, 2), round(longe, 2), [p[2] for p in (pcs if not no_no_fim else pcs[::-1])])
    return out, L, res


def test_H_I_a_peca_fica_rente_a_face_nas_duas_orientacoes_sem_recuo_de_1cm():
    ini, L_ini, res_ini = _face_flush(False)
    fim, L_fim, res_fim = _face_flush(True)
    assert L_ini == L_fim
    for ci in JANELA:
        assert ini[ci][0] == 0.0, ("no' no inicio: peca deve comecar na face", ci, ini[ci])
        assert fim[ci][0] == L_fim, ("no' no fim: peca deve terminar na face", ci, fim[ci])
        # a folga de modulacao (1 cm) vai para a ponta LIVRE de verdade, nas duas orientacoes
        assert abs((L_ini - ini[ci][1]) - fim[ci][1]) < 0.05, (ci, ini[ci], fim[ci])
    assert missing(res_ini) == [] and missing(res_fim) == []
    assert hard(res_ini) == ZERO and hard(res_fim) == ZERO


# ============================================================ J/K. apresentacoes
def _apresentacao(dx=0.0, dy=0.0, reverse_main=False, swap=False, mirror=False):
    lines, ops = corpo(0.0, 0.0)
    main_ops = list(ops[0])
    L = ft(COMPRIMENTO)
    if reverse_main:
        main = seg(COMPRIMENTO + dx, dy, dx, dy)
        main_ops = sorted((L - o[1], L - o[0], o[2], o[3]) for o in main_ops)
    else:
        main = seg(dx, dy, COMPRIMENTO + dx, dy)
    y1 = -CHEGA if mirror else CHEGA
    inc = seg(NO_T + dx, dy, NO_T + dx, y1 + dy)
    if swap:
        return [inc, main], [[], main_ops]
    return [main, inc], [main_ops, []]


@pytest.mark.parametrize("kw", [dict(dx=1234.5, dy=-987.25), dict(reverse_main=True), dict(swap=True),
                                dict(mirror=True), dict(dx=50.0, dy=50.0, reverse_main=True, swap=True, mirror=True)])
def test_J_K_translacao_pontas_invertidas_ordem_e_lado_nao_mudam_o_papel(kw):
    base = role_map(*corpo(0.0, 0.0))
    outro = role_map(*_apresentacao(**kw))
    assert outro == base


# ================================================= transicao FREE_END -> T ativo
def test_transicao_na_fiada_em_que_o_T_volta_a_amarracao_cabe_tem_apoio_e_nao_e_compensador():
    res, walls, nodes, _o = solve(*corpo(0.0, 0.0))
    ni = t_node(nodes)
    reg = region(res, walls, nodes, ni)
    for ci in (3, 11):                                   # ultima antes / primeira depois das janelas
        code, cov, reason, _w = reg[ci][0]
        assert code in ws.JUNCTION_BOND_CODES and cov >= 0.999 and reason.startswith("T_INTERSECTION"), (ci, reg[ci])
        assert all(not (CAT.get(c) or {}).get("is_compensator") for c, _cov, _r, _w in reg[ci]), reg[ci]
    sem_apoio = _support.unsupported_pieces(res["course_candidates"], walls, _o, BAND)
    assert sem_apoio == [], sem_apoio
    assert (res.get("beta_preflight") or {}).get("opening_violations") in (None, [])
    assert 11 not in missing(res) and 3 not in missing(res)


# ==================================================================== memo/cache
def test_memo_o_papel_da_banda_faz_parte_da_chave_do_preenchimento():
    lines, ops = corpo(0.0, 0.0)
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    ni = t_node(nodes)
    inc = nodes[ni]["incoming_wall_idx"]
    saved = ws.JUNCTION_BAND_ROLES
    try:
        ws.JUNCTION_BAND_ROLES = None
        k_ativo = ws._wall_fill_memo_key(inc, walls, nodes, e2n, ops, {}, {}, True, 1, tcr.CHANNEL, None)
        ws.JUNCTION_BAND_ROLES = {ni: {"effective_role": "NONE_FREE_END", "free_end_wall": inc,
                                       "continuous_walls": []}}
        k_livre = ws._wall_fill_memo_key(inc, walls, nodes, e2n, ops, {}, {}, True, 1, tcr.CHANNEL, None)
    finally:
        ws.JUNCTION_BAND_ROLES = saved
    assert k_ativo != k_livre
    assert "NONE_FREE_END" in k_livre and "NONE_FREE_END" not in k_ativo


def test_o_contexto_de_banda_e_restaurado_depois_do_solve():
    solve(*corpo(0.0, 0.0))
    assert ws.JUNCTION_BAND_ROLES is None
    assert ws.JUNCTION_ROLE_BY_COURSE is False
    assert ws.PIER_SLACK_PREFER_TRAILING is False


def test_a_folga_rente_a_face_e_contexto_da_parede_e_e_restaurada_mesmo_com_excecao():
    """Revisao adversarial (objecao A): a flag da folga era gravada por trecho e
    nunca restaurada na saida. Agora e' um envelope por parede com finally."""
    lines, ops = corpo(0.0, 0.0)
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(walls, jm)
    ni = t_node(nodes)
    inc = nodes[ni]["incoming_wall_idx"]
    saved_roles, saved_impl = ws.JUNCTION_BAND_ROLES, ws._solve_wall_free_fill_impl
    visto = {}

    def _boom(*a, **k):
        visto["flag"] = ws.PIER_SLACK_PREFER_TRAILING
        raise RuntimeError("simulada")
    try:
        ws.JUNCTION_BAND_ROLES = {ni: {"effective_role": "NONE_FREE_END", "free_end_wall": inc,
                                       "continuous_walls": []}}
        ws._solve_wall_free_fill_impl = _boom
        with pytest.raises(RuntimeError):
            ws.solve_wall_free_fill(inc, walls, nodes, e2n, ops, {}, {}, CAT)
    finally:
        ws._solve_wall_free_fill_impl = saved_impl
        ws.JUNCTION_BAND_ROLES = saved_roles
    assert visto["flag"] is True                      # a parede que chega comeca na face do no'
    assert ws.PIER_SLACK_PREFER_TRAILING is False     # restaurada apesar da excecao


def test_isencao_so_com_a_ponta_livre_composta_parede_nao_modular_nao_e_mascarada():
    """Revisao adversarial (objecao B): a parede que chega nao modular (307 cm) nao
    fecha nas fiadas sem encontro; a regiao do no' fica vazia e isso NAO pode
    virar isencao - sai como missing FREE_END_NOT_COMPOSED."""
    lines = [seg(0, 0, COMPRIMENTO, 0), seg(NO_T, 0, NO_T, 300.0)]   # chega com 307 cm ate' a face
    ops = [[janela(ESQ, NO_T - MEIA), janela(NO_T + MEIA, DIR)], []]
    res, walls, nodes, _o = solve(lines, ops)
    ni = t_node(nodes)
    inc = nodes[ni]["incoming_wall_idx"]
    vazias = [ci for ci in JANELA if not pieces(res, walls, inc, ci)]
    if not vazias:
        pytest.skip("o motor compos a parede de 307 cm; a fixture nao e' nao modular neste catalogo")
    reasons = dict((f["course_index"], f["reason"]) for f in res["missing_required_junction_bond"]
                   if f["node_index"] == ni)
    for ci in vazias:
        assert reasons.get(ci) == "FREE_END_NOT_COMPOSED", (ci, reasons)
    assert set(nfj(res, ni)).isdisjoint(vazias)
    assert res["junction_role_by_course"]["free_end_not_composed"]


# ================================================ toco entre tolerancia e menor peca
def test_toco_acima_da_tolerancia_continua_encontro_e_e_registrado_para_decisao():
    tab = roles(*corpo(0.5, 0.5))[0]
    assert all(tab[c]["effective_role"] == "T" for c in JANELA)
    flags = [f for c in JANELA for f in tab[c]["stub_flags"]]
    assert flags and all(f.startswith("STUB_BELOW_MIN_UNIT") for f in flags)
    resumo = JR.summarize(list(tab.values()))
    assert resumo["pending_product_decision"]
    # a ponta natural da parede NUNCA desliga o braco (item 7 do criterio): a
    # principal termina 20,5 cm depois da faixa (T de um lado, toco do outro)
    # e a janela consome o outro lado -> o toco continua sendo braco -> L
    tab2 = roles([seg(0, 0, NO_T + MEIA + 20.5, 0), seg(NO_T, 0, NO_T, CHEGA)], [[janela(ESQ, NO_T - MEIA)], []])[0]
    assert tab2[5]["effective_role"] == "L", tab2[5]
    assert tab2[5]["s_by_wall"][0]["+"] == 20.5


def test_parede_inteira_dentro_da_faixa_do_no_nunca_rebaixa_o_papel():
    """Toco de modelagem: a parede que chega tem 14 cm (as duas pontas no no').
    Nao ha' braco dela para medir; o encontro fica como a topologia base."""
    lines = [seg(0, 0, COMPRIMENTO, 0), seg(NO_T, -MEIA, NO_T, MEIA)]
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, _e2n = m.build_wall_graph(walls, jm)
    kinds = [n.get("kind") for n in nodes]
    if "T_INTERSECTION" not in kinds:
        pytest.skip("o grafo nao classifica o toco como T: %s" % kinds)
    ops = m._effective_solve_openings(nodes, walls, [[], []], CAT, 0.0, NUM_COURSES, None, None)
    table = ws.junction_role_table(nodes, walls, ops, BAND, NUM_COURSES, CAT, m.OPENING_COURSE_BAND_TOLERANCE_FT)
    ni = kinds.index("T_INTERSECTION")
    for ci in range(NUM_COURSES):
        r = table[(ni, ci)]
        assert r["effective_role"] == "T", r
        assert not ws.junction_role_skips_bond(nodes[ni], r)


# ================================= guardas: paralelas sobrepostas e canto L
def test_paredes_paralelas_sobrepostas_nao_viram_ponta_livre():
    """CAD cru: uma segunda parede paralela, 2,4 cm deslocada, forma "T" no
    grafo. Mesmo com a principal consumida dos dois lados, a parede que sobra
    nao e' perpendicular - nao tem face para terminar: papel base."""
    lines = [seg(0, 0, COMPRIMENTO, 0), seg(NO_T, 2.4, NO_T - 200.0, 2.4)]
    ops = [[janela(ESQ, NO_T - MEIA), janela(NO_T + MEIA, DIR)], []]
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, _e2n = m.build_wall_graph(walls, jm)
    kinds = [n.get("kind") for n in nodes]
    if "T_INTERSECTION" not in kinds:
        pytest.skip("o grafo nao classifica as paralelas como T: %s" % kinds)
    ni = kinds.index("T_INTERSECTION")
    opsx = m._effective_solve_openings(nodes, walls, ops, CAT, 0.0, NUM_COURSES, None, None)
    table = ws.junction_role_table(nodes, walls, opsx, BAND, NUM_COURSES, CAT, m.OPENING_COURSE_BAND_TOLERANCE_FT)
    for ci in JANELA:
        r = table[(ni, ci)]
        assert r["effective_role"] == "T", r
        assert any(f.startswith("ARMS_NOT_PERPENDICULAR") for f in r["stub_flags"]), r
        assert not ws.junction_role_skips_bond(nodes[ni], r)


def test_canto_L_com_um_braco_consumido_e_classificado_mas_nao_consumido_pelo_solve():
    """Canto L: uma parede tem uma porta encostada na quina (braco consumido).
    O classificador diz NONE_FREE_END (a outra termina livre), mas o escopo da
    secao 77 e' o T: o solve nao consome e o gate continua exigindo amarracao."""
    lines = [seg(0, 0, 300.0, 0), seg(300.0, 0, 300.0, 250.0)]
    ops = [[(ft(300.0 - MEIA - 0.0 - 90.0), ft(300.0 - MEIA), ft(0.0), ft(221.0))], []]
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, _e2n = m.build_wall_graph(walls, jm)
    kinds = [n.get("kind") for n in nodes]
    assert "L_CORNER" in kinds, kinds
    ni = kinds.index("L_CORNER")
    opsx = m._effective_solve_openings(nodes, walls, ops, CAT, 0.0, NUM_COURSES, None, None)
    table = ws.junction_role_table(nodes, walls, opsx, BAND, NUM_COURSES, CAT, m.OPENING_COURSE_BAND_TOLERANCE_FT)
    r = table[(ni, 5)]
    assert r["effective_role"] in ("NONE_FREE_END", "ABSENT"), r
    assert not ws.junction_role_skips_bond(nodes[ni], r)
    on, w_on, _n, _o = solve(lines, ops)
    off = solve(lines, ops, flag=False)[0]
    assert tcr.physical_signature(on, w_on) == tcr.physical_signature(off, w_on)


# ===================================================================== overfit
@pytest.mark.parametrize("largura,dist,sill,head", [(145.0, 14.0, 80.0, 221.0), (60.0, 14.0, 100.0, 200.0),
                                                    (200.0, 14.0, 40.0, 260.0), (145.0, 14.0, 20.0, 180.0)])
def test_overfit_o_papel_deriva_da_geometria_nao_da_largura_ou_altura(largura, dist, sill, head):
    lo1 = NO_T - MEIA - dist / 2.0 + MEIA          # jamba interna = borda da faixa do no'
    js = [(NO_T - MEIA - largura, NO_T - MEIA), (NO_T + MEIA, NO_T + MEIA + largura)]
    assert lo1 or True
    lines, ops = t_base(js, sill, head)
    rm = role_map(lines, ops)
    ativas = [c for c in range(NUM_COURSES)
              if m._opening_active_in_course_band(ft(sill), ft(head), BAND(c)[0], BAND(c)[1])]
    assert all(rm[c] == ("NONE_FREE_END" if c in ativas else "T") for c in range(NUM_COURSES)), (rm, ativas)


@pytest.mark.parametrize("corpo_cm", [0.0, 0.03, 4.0, 10.0, 34.0, 100.0])
def test_overfit_a_distancia_entre_as_janelas_nao_e_um_limiar(corpo_cm):
    rm = role_map(*corpo(corpo_cm, corpo_cm))
    esperado = "NONE_FREE_END" if corpo_cm <= ws.PIER_PHYSICAL_FIT_TOLERANCE_CM else "T"
    assert all(rm[c] == esperado for c in JANELA), (corpo_cm, rm)
