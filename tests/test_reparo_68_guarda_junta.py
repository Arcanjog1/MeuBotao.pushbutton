# -*- coding: utf-8 -*-
"""SECAO 83 - a secao 68 (a faixa jamba->ancora e' composta como UMA unidade) no
caminho GERAL, com a GUARDA DE JUNTA (regra #1) que faltava.

A secao 68 fica com a MELHOR composicao do reparo de abertura, mas a qualidade dela
so' olhava pecas de acerto: no NONE a composicao "limpa" podia cair com a junta em
cima da face NO'|FILL do B54 da familia oposta - junta a prumo em todas as fiadas
(medido na convergencia com o MCP; o MCP tem esse defeito, o HUMANO evita). Com a
guarda, a qualidade comeca pelas juntas coincidentes com a familia oposta, e uma
janela EXPANDIDA cuja composicao repetiria uma dessas juntas e' refeita
desencontrando-as.

Nenhum teste fixa parede, ElementId ou coordenada de projeto: a geometria e' uma
parede reta com um T e uma porta; as posicoes da porta foram achadas por varredura
(checkpoint do ciclo 11)."""
import inspect
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_channel_reinforcement as tcr  # noqa: E402

m, ft, seg = tcr.m, tcr.ft, tcr.seg
ws = __import__("core.engine.wall_stepper", fromlist=["x"])
CATALOG = tcr.sb.CATALOG
FIADAS = 8
T_CM = 407.0
# Porta a 474 cm: sem guarda, a janela expandida da fiada B sai `B19 B39` (junta em
# cima da face do B54 do no'); com a guarda, `B39 B19` - o que o legado ja' fazia.
# Porta a 489 cm: sem guarda, `B19 B34` com a mesma junta; com a guarda, `B34 B39`
# sem nenhum compensador (o legado tinha C04 + C09 nas duas fiadas).
PORTA_JUNTA_A_PRUMO = (474.0, 489.0)
PORTA_SEM_GANHO = 453.0


def _t_porta(porta_cm):
    lines = [seg(0, 0, 900, 0), seg(T_CM, 0, T_CM, 300)]
    return lines, [[(ft(porta_cm), ft(porta_cm + 91.0), ft(0), ft(221))], []]


_CACHE = {}


def _solve(porta_cm, modo="produto", estrategia=None):
    chave = (porta_cm, modo, estrategia)
    if chave in _CACHE:
        return _CACHE[chave]
    salvo = (m.GENERAL_REPAIR_PREFER_CLEAN_ENABLED, ws._repair_guard_joint_positions_cm)
    try:
        if modo == "legado":
            m.GENERAL_REPAIR_PREFER_CLEAN_ENABLED = False
        elif modo == "sem_guarda":
            # a secao 68 no NONE como ela era (sem a guarda): o que o MCP fazia
            ws._repair_guard_joint_positions_cm = lambda *a, **k: None
        lines, ops = _t_porta(porta_cm)
        res, walls, _n, _o = tcr.solve(lines, ops, strategy=estrategia, num_courses=FIADAS)
    finally:
        m.GENERAL_REPAIR_PREFER_CLEAN_ENABLED, ws._repair_guard_joint_positions_cm = salvo
    _CACHE[chave] = (res, walls)
    return _CACHE[chave]


def _juntas_por_fiada(res, walls):
    out = []
    for c in range(FIADAS):
        rows = tcr.strip(res, walls, 0, c)
        out.append(set(round(r["hi"]) for r in rows[:-1]))
    return out


def _juntas_continuas(res, walls, minimo=3):
    """Juntas da parede principal repetidas em `minimo` fiadas seguidas (identidade)."""
    continuas, seguidas = set(), {}
    for juntas in _juntas_por_fiada(res, walls):
        seguidas = dict((j, seguidas.get(j, 0) + 1) for j in juntas)
        continuas.update(j for j, n in seguidas.items() if n >= minimo)
    return continuas


def _faixa(res, walls, c, porta_cm):
    return [(r["cand"]["logical_code"], round(r["lo"])) for r in tcr.strip(res, walls, 0, c)
            if T_CM - 60 < r["lo"] < porta_cm]


def _compensadores(res, walls, porta_cm):
    return sum(1 for c in range(FIADAS) for code, _lo in _faixa(res, walls, c, porta_cm + 1)
               if (CATALOG.get(code) or {}).get("is_compensator"))


# ----------------------------------------------------------------- vermelho: o defeito existe
@pytest.mark.parametrize("porta", PORTA_JUNTA_A_PRUMO)
def test_red_secao_68_sem_guarda_cria_junta_a_prumo(porta):
    sem_guarda = _juntas_continuas(*_solve(porta, "sem_guarda"))
    legado = _juntas_continuas(*_solve(porta, "legado"))
    assert sem_guarda - legado, "a 68 sem guarda deveria criar junta continua nova nesta geometria"


# ----------------------------------------------------------------- a regra
@pytest.mark.parametrize("porta", PORTA_JUNTA_A_PRUMO + (PORTA_SEM_GANHO,))
def test_guarda_nunca_cria_junta_a_prumo_nova(porta):
    produto = _juntas_continuas(*_solve(porta))
    legado = _juntas_continuas(*_solve(porta, "legado"))
    assert not (produto - legado), sorted(produto - legado)


@pytest.mark.parametrize("porta", PORTA_JUNTA_A_PRUMO)
def test_guarda_nao_troca_a_junta_por_compensador(porta):
    """A composicao escolhida nunca tem MAIS compensadores que o legado na faixa T->porta."""
    assert _compensadores(*_solve(porta), porta) <= _compensadores(*_solve(porta, "legado"), porta)


def test_janela_expandida_e_refeita_desencontrando_a_face_do_no():
    """Porta a 474: a fiada B fica `B39 B19` (o que o legado ja' fazia), nunca
    `B19 B39` (junta a prumo) nem `C04 B34 B19` (compensador remanescente)."""
    res, walls = _solve(474.0)
    legado = _solve(474.0, "legado")
    assert _faixa(res, walls, 1, 474.0) == _faixa(*legado, 1, 474.0)
    assert [c for c, _lo in _faixa(res, walls, 1, 474.0)][-2:] == ["B39", "B19"]


def test_ganho_da_68_mantido_com_a_guarda():
    """Porta a 489: o legado fechava com C04 + C09 nas duas fiadas; a 68 com guarda fecha
    sem compensador e sem junta a prumo. Desde a secao 86.6 (fechamento da jamba pela forma
    do catalogo: `vao | B19 | C09 | B39 | C04` = pastilha atras do B19, 85.8) o recompositor
    da jamba chega a' mesma composicao tambem no legado (medido: 16 -> 0 compensadores,
    juntas continuas [479, 489] -> [489]) - o ganho continua, so' deixou de ser exclusivo."""
    res, walls = _solve(489.0)
    assert _compensadores(res, walls, 489.0) == 0
    assert _compensadores(res, walls, 489.0) <= _compensadores(*_solve(489.0, "legado"), 489.0)
    assert not (_juntas_continuas(res, walls) - _juntas_continuas(*_solve(489.0, "legado")))


# ----------------------------------------------------------------- guarda de tier (secao 2 / secao 70)
def _pilarete(pilar_cm):
    """Parede reta com duas janelas (peitoril 80) separadas por um pilarete: nas fiadas da
    banda das janelas o pilarete e' um trecho fechado pelos dois vaos."""
    v1 = (100.0, 220.0)
    v2 = (v1[1] + pilar_cm, v1[1] + pilar_cm + 120.0)
    lines = [seg(0, 0, v2[1] + 150.0, 0)]
    ops = [[(ft(v1[0]), ft(v1[1]), ft(80.0), ft(221.0)), (ft(v2[0]), ft(v2[1]), ft(80.0), ft(221.0))]]
    return lines, ops, (v1[1], v2[0])


def _pilarete_solve(pilar_cm, modo):
    salvo = (m.GENERAL_REPAIR_PREFER_CLEAN_ENABLED, ws._repair_tier_gate_blocks)
    try:
        if modo == "legado":
            m.GENERAL_REPAIR_PREFER_CLEAN_ENABLED = False
        elif modo == "sem_tier":
            ws._repair_tier_gate_blocks = lambda *a, **k: False
        lines, ops, (a, b) = _pilarete(pilar_cm)
        res, walls, _n, _o = tcr.solve(lines, ops, strategy=None, num_courses=FIADAS)
    finally:
        m.GENERAL_REPAIR_PREFER_CLEAN_ENABLED, ws._repair_tier_gate_blocks = salvo
    return [[r["cand"]["logical_code"] for r in tcr.strip(res, walls, 0, c) if r["lo"] >= a - 1 and r["hi"] <= b + 1]
            for c in (4, 5, 6, 7)]


def test_red_sem_guarda_de_tier_o_pilarete_vira_fileira_de_b34():
    sem_tier = _pilarete_solve(69.0, "sem_tier")
    assert any(f.count("B34") >= 2 for f in sem_tier), sem_tier


def test_guarda_de_tier_mantem_um_compensador_antes_da_fileira_de_b34():
    """Secao 2 (decisao do usuario de 2026-09-11): 1 compensador por trecho (tier 5)
    vem antes da fileira de B34 (tier 5b). O pilarete de 69 cm fecha com `B39 C09 B19`
    no legado (e no HUMANO); a secao 83 nao o troca por `B34 B34`."""
    produto = _pilarete_solve(69.0, "produto")
    assert produto == _pilarete_solve(69.0, "legado")
    assert not any(f.count("B34") >= 2 for f in produto), produto


def test_guarda_de_tier_libera_quando_o_legado_estoura_o_teto():
    """Pilarete de 75 cm: o legado usa 2 compensadores numa fiada (acima do teto) - ai' a
    fileira/B34 da secao 68 vem antes (tier 5b antes de 7) e os compensadores caem."""
    comp = lambda fiadas: sum(1 for f in fiadas for c in f if (CATALOG.get(c) or {}).get("is_compensator"))
    legado = _pilarete_solve(75.0, "legado")
    assert max(sum(1 for c in f if (CATALOG.get(c) or {}).get("is_compensator")) for f in legado) >= 2
    assert comp(_pilarete_solve(75.0, "produto")) < comp(legado)


def test_guarda_de_tier_funcao_pura(monkeypatch):
    monkeypatch.setattr(ws, "OPENING_REPAIR_TIER_GATE_ACTIVE", True)
    sub = _sub(0.0, 69.0, left_opening=0, right_opening=1)
    um_comp = [(sub, [("B39", 0.0, 39.0), ("C09", 40.0, 49.0), ("B19", 50.0, 69.0)])]
    dois_comp = [(sub, [("B19", 0.0, 19.0), ("B39", 20.0, 59.0), ("C09", 60.0, 69.0)]),
                 (sub, [("C04", 0.0, 4.0)])]
    fileira = [(sub, [("B34", 0.0, 34.0), ("B34", 35.0, 69.0)])]
    um_b34 = [(sub, [("B34", 0.0, 34.0), ("B39", 35.0, 69.0)])]
    assert ws._repair_tier_gate_blocks(um_comp, fileira, CATALOG) is True
    assert ws._repair_tier_gate_blocks(um_comp, um_b34, CATALOG) is False     # 1 B34 nao e' fileira
    assert ws._repair_tier_gate_blocks(um_comp, um_comp, CATALOG) is False
    assert ws._repair_tier_gate_blocks([(sub, dois_comp[0][1] + [("C04", 70.0, 74.0)])], fileira, CATALOG) is False
    # faixa com 2 compensadores: o lado aberto para a ancora (sem abertura) libera a fileira
    sub_dir = _sub(0.0, 69.0, left_opening=0, right_opening=None)
    assert ws._repair_tier_gate_blocks([(sub_dir, um_comp[0][1])], [(sub_dir, fileira[0][1])], CATALOG, ((), ["B39", "C09"])) is False
    assert ws._repair_tier_gate_blocks(um_comp, fileira, CATALOG, ((), ["B39", "C09"])) is True   # entre dois vaos: sem lado aberto
    # subtrechos independentes: um compensador em OUTRO subtrecho nao libera a fileira neste
    outro = _sub(200.0, 250.0, left_opening=1, right_opening=None)
    assert ws._repair_tier_gate_blocks(um_comp + [(outro, [("C09", 0.0, 9.0), ("B39", 10.0, 49.0)])], fileira, CATALOG) is True
    monkeypatch.setattr(ws, "OPENING_REPAIR_TIER_GATE_ACTIVE", False)
    assert ws._repair_tier_gate_blocks(um_comp, fileira, CATALOG) is False    # CHANNEL: 68 historica


# ----------------------------------------------------------------- qualidade (funcao pura)
def _sub(lo, hi, left_opening=None, right_opening=0):
    return {"lo": lo, "hi": hi, "leading_open": True, "trailing_open": True,
            "left_opening": left_opening, "right_opening": right_opening}


def test_qualidade_poe_a_regra_1_antes_das_pecas_de_acerto(monkeypatch):
    monkeypatch.setattr(ws, "OPENING_REPAIR_JOINT_GUARD_ACTIVE", True)
    sub = _sub(415.0, 474.0)
    junta = [(sub, [("B19", 0.0, 19.0), ("B39", 20.0, 59.0)])]            # junta a 434,5
    limpa = [(sub, [("B39", 0.0, 39.0), ("B19", 40.0, 59.0)])]            # junta a 454,5
    com_acerto = [(sub, [("C04", 0.0, 4.0), ("B34", 5.0, 39.0), ("B19", 40.0, 59.0)])]
    guarda = [434.5]
    q = lambda s: ws._repair_solution_quality(s, CATALOG, guarda)
    assert q(junta)[0] == 1 and q(limpa)[0] == 0
    assert q(limpa) < q(junta)
    assert q(com_acerto) < q(junta), "um compensador nunca perde para uma junta a prumo"


def test_sem_guarda_a_ordem_historica_nao_muda(monkeypatch):
    monkeypatch.setattr(ws, "OPENING_REPAIR_JOINT_GUARD_ACTIVE", False)
    sub = _sub(415.0, 474.0)
    junta = [(sub, [("B19", 0.0, 19.0), ("B39", 20.0, 59.0)])]
    com_acerto = [(sub, [("C04", 0.0, 4.0), ("B34", 5.0, 39.0), ("B19", 40.0, 59.0)])]
    q = lambda s: ws._repair_solution_quality(s, CATALOG, [434.5])
    assert q(junta)[0] == 0 and q(com_acerto)[0] == 0
    assert q(junta) < q(com_acerto)          # a secao 68 historica: pecas de acerto primeiro


def test_isencao_de_peca_pequena_so_contra_abertura(monkeypatch):
    """B19 encostado no BRACO de um no' (leading_open True, sem abertura) nao e' isento;
    o mesmo B19 encostado numa ABERTURA e' (excecao da regra #1, secao 11.8)."""
    monkeypatch.setattr(ws, "OPENING_REPAIR_JOINT_GUARD_ACTIVE", True)
    layout = [("B19", 0.0, 19.0), ("B39", 20.0, 59.0)]
    no = [(_sub(415.0, 474.0, left_opening=None), layout)]
    vao = [(_sub(415.0, 474.0, left_opening=0, right_opening=None), layout)]
    assert ws._repair_solution_quality(no, CATALOG, [434.5])[0] == 1
    assert ws._repair_solution_quality(vao, CATALOG, [434.5])[0] == 0


def test_lista_da_guarda(monkeypatch):
    monkeypatch.setattr(ws, "OPENING_REPAIR_JOINT_GUARD_ACTIVE", False)
    assert ws._repair_guard_joint_positions_cm("B", [1.0], [2.0], [3.0]) is None
    monkeypatch.setattr(ws, "OPENING_REPAIR_JOINT_GUARD_ACTIVE", True)
    assert sorted(ws._repair_guard_joint_positions_cm("B", [1.0], [2.0], [3.0])) == [1.0, 2.0, 3.0]
    assert sorted(ws._repair_guard_joint_positions_cm("A", [1.0], [2.0], [3.0])) == [1.0, 2.0]


def test_janela_sem_coincidencia_fica_como_a_busca_devolveu(monkeypatch):
    monkeypatch.setattr(ws, "OPENING_REPAIR_JOINT_GUARD_ACTIVE", True)
    sub = _sub(415.0, 474.0)
    limpa = [(sub, [("B39", 0.0, 39.0), ("B19", 40.0, 59.0)])]
    chamadas = []
    monkeypatch.setattr(ws, "_solve_repair_subsegments", lambda *a, **k: chamadas.append(1) or ([], []))
    assert ws._repair_guarded_window_solution({"segments": [sub]}, CATALOG, True, limpa, [434.5], None) is limpa
    assert chamadas == [], "sem coincidencia a janela nao e' refeita"


# ----------------------------------------------------------------- escopo e chaves
def test_none_liga_68_com_guarda_e_channel_mantem_a_68_historica(monkeypatch):
    estados = {"NONE": [], "CHANNEL": []}
    atual = []
    core = m._solve_building_blocks_all_courses_core

    def espia(*a, **k):
        estados[atual[-1]].append((ws.OPENING_REPAIR_PREFER_CLEAN_ACTIVE, ws.OPENING_REPAIR_JOINT_GUARD_ACTIVE,
                                    ws.OPENING_REPAIR_TIER_GATE_ACTIVE))
        return core(*a, **k)

    monkeypatch.setattr(m, "_solve_building_blocks_all_courses_core", espia)
    lines, ops = _t_porta(489.0)
    atual.append("NONE")
    none, _w, _n, _o = tcr.solve(lines, ops, strategy=None, num_courses=2)
    atual.append("CHANNEL")
    channel, _w, _n, _o = tcr.solve(lines, ops, strategy=tcr.CHANNEL, num_courses=2)
    assert estados["NONE"] and estados["CHANNEL"]
    assert all(e == (True, True, True) for e in estados["NONE"]), estados["NONE"]      # 68 com as guardas
    assert all(e == (True, False, False) for e in estados["CHANNEL"]), estados["CHANNEL"]  # 68 historica
    assert none["general_repair_prefer_clean"] is True
    assert channel["general_repair_prefer_clean"] is False
    assert not (ws.OPENING_REPAIR_PREFER_CLEAN_ACTIVE or ws.OPENING_REPAIR_JOINT_GUARD_ACTIVE
                or ws.OPENING_REPAIR_TIER_GATE_ACTIVE)


def test_channel_identico_com_e_sem_a_chave():
    for porta in PORTA_JUNTA_A_PRUMO:
        com = _solve(porta, "produto", tcr.CHANNEL)
        sem = _solve(porta, "legado", tcr.CHANNEL)
        assert tcr.physical_signature(*com) == tcr.physical_signature(*sem)


def test_desligar_a_chave_nao_chama_a_qualidade_nem_a_guarda(monkeypatch):
    chamadas = []
    monkeypatch.setattr(m, "GENERAL_REPAIR_PREFER_CLEAN_ENABLED", False)
    monkeypatch.setattr(ws, "_repair_solution_quality", lambda *a, **k: chamadas.append("q") or (0, 0, 0, 0, 0))
    lines, ops = _t_porta(489.0)
    res, _w, _n, _o = tcr.solve(lines, ops, strategy=None, num_courses=2)
    assert chamadas == []
    assert res["general_repair_prefer_clean"] is False


def test_estrutura_preservada():
    """Os gates estruturais sao os MESMOS do legado (a fixture minima tem, nos dois, o
    braco livre do T sem apoio e dois trechos sem modulacao - geometria, nao a secao 83)."""
    def gates(res):
        return (sorted((x["course_index"], x["node_index"], x.get("reason")) for x in res["missing_required_junction_bond"]),
                len(res["compensator_as_junction_bond"]), len(res["channel_as_junction_bond"]),
                len(res["unresolved_spans"]))
    for porta in PORTA_JUNTA_A_PRUMO:
        res, walls = _solve(porta)
        assert gates(res) == gates(_solve(porta, "legado")[0])
        assert res["compensator_as_junction_bond"] == [] and res["channel_as_junction_bond"] == []
        assert res["opening_reinforcement"]["validation"]["counts"].get("OPENING_INVASION", 0) == 0


def test_deterministico():
    lines, ops = _t_porta(489.0)
    a, wa, _n, _o = tcr.solve(lines, ops, strategy=None, num_courses=4)
    b, wb, _n, _o = tcr.solve(lines, ops, strategy=None, num_courses=4)
    assert tcr.physical_signature(a, wa) == tcr.physical_signature(b, wb)


def test_espelhamento_nao_cria_junta_a_prumo():
    lines, ops = _t_porta(489.0)
    res, walls, _n, _o = tcr.solve(lines, ops, strategy=None, num_courses=FIADAS, reverse=True)
    legado_salvo = m.GENERAL_REPAIR_PREFER_CLEAN_ENABLED
    m.GENERAL_REPAIR_PREFER_CLEAN_ENABLED = False
    try:
        leg, wl, _n, _o = tcr.solve(lines, ops, strategy=None, num_courses=FIADAS, reverse=True)
    finally:
        m.GENERAL_REPAIR_PREFER_CLEAN_ENABLED = legado_salvo
    assert not (_juntas_continuas(res, walls) - _juntas_continuas(leg, wl))


def test_sem_hardcode():
    """As funcoes da secao 83 nao conhecem parede, id, coordenada nem projeto."""
    for fn in (ws._repair_guard_joint_positions_cm, ws._repair_guarded_window_solution, ws._repair_tier_gate_blocks,
               ws._repair_solution_quality):
        numeros = [c for c in fn.__code__.co_consts if isinstance(c, (int, float)) and not isinstance(c, bool)]
        assert all(abs(c) < 1000 for c in numeros), (fn.__name__, numeros)
        codigo = re.sub(r'"""[\s\S]*?"""', "", inspect.getsource(fn))
        codigo = "\n".join(linha.split("#")[0] for linha in codigo.splitlines())
        assert "butanta" not in codigo.lower() and "8284" not in codigo, fn.__name__
