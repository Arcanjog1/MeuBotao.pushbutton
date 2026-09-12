# -*- coding: utf-8 -*-
"""Licenca RESTRITA do B19 forcado na busca de desencontro (2026-09-12).

Causa medida (bisseccao TP1, missao pre-Beta 2): o resto de 29cm de um
trecho entre dois nos fecha, pelo tier 7 de `_pier_ordered_layout`, como
`C09 C09 C09` - tres compensadores em sequencia com juntas FIXAS em
+9,5/+19,5 do inicio do trecho. Na parede de 54cm entre um canto L e um T
(W088/W090 do TP1) a junta do meio dessa cadeia ficou embaixo da junta
B34(canto)|fill que a regra 11.14 passou a produzir na fiada oposta: junta
corrida no'|fill (regressao 14 -> 16 do PR #37). A metade simetrica nao
conseguia consertar porque a busca NUNCA gerava um B19 fora de ponta
aberta - `C09 + B19` (junta em +9,5 apenas) nao existia como candidato.

O que entrou: `_pier_full_search_layout(allow_forced_half=True)`, chamada
por `_pier_layout_avoiding_joints` SO' quando o melhor candidato viola as
duas regras (cadeia de compensadores E junta empilhada) e aceita SO' se o
layout licenciado ZERA a coincidencia. Fora de conflito, a cadeia continua
sendo o layout - trocar o padrao do tier 6 foi medido e ficou como decisao
pendente (ver o docstring do tier 6 em `_pier_ordered_layout`).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import solver_bench as sb  # noqa: E402
import test_block_node_fill_revalidation as NF  # noqa: E402

m = sb.m
CATALOG = sb.CATALOG
ws = sys.modules["core.engine.wall_stepper"]


def _codes(layout):
    return [code for code, _a, _b in (layout or [])]


def _search(avoid, pier_cm=31.0, seg_start_cm=14.0):
    return ws._pier_layout_avoiding_joints(
        pier_cm, CATALOG, 1.0, 1.0, seg_start_cm, avoid,
        leading_is_open=False, trailing_is_open=False)


def test_padrao_continua_sendo_a_cadeia_quando_nao_ha_conflito():
    """Sem junta empilhada a licenca nao entra: o layout e' o de sempre."""
    assert _codes(ws._pier_ordered_layout(31.0, CATALOG, 1.0, 1.0)) == ["C09", "C09", "C09"]
    assert _codes(_search([60.0])) == ["C09", "C09", "C09"]
    assert _codes(_search([])) == ["C09", "C09", "C09"]


def test_cadeia_que_empilha_junta_vira_c09_mais_b19_desencontrado():
    """Junta da fiada oposta em +20,5 (34,5 global): a cadeia (juntas 24,5/
    34,5/44,5) empilha; o licenciado `C09 + B19` (junta so' em 24,5) zera."""
    layout = _search([34.5])
    assert _codes(layout) == ["C09", "B19"], layout
    juntas = m._layout_internal_joint_positions_cm(layout, 14.0)
    assert all(abs(j - 34.5) > m.VERTICAL_JOINT_STAGGER_TOLERANCE_CM for j in juntas), juntas
    # e o espelho: junta oposta em 24,5 -> B19 primeiro
    assert _codes(_search([24.5])) == ["B19", "C09"]


def test_licenca_so_vale_se_zerar_a_coincidencia():
    """Caso da CR-G12 (W113 do TGD / subplano minimo): as DUAS ordens com
    B19 empilham em alguma vizinha (39,5 abaixo, 54,5 na propria banda);
    a cadeia reordenada e' a unica composicao sem coincidencia e tem de
    continuar sendo devolvida - a licenca nao pode escondê-la."""
    layout = ws._pier_layout_avoiding_joints(
        24.0, CATALOG, 0.0, 0.0, 35.0, [39.5, 54.5, 14.5, 59.5],
        leading_is_open=False, trailing_is_open=False)
    assert "B19" not in _codes(layout), layout
    juntas = m._layout_internal_joint_positions_cm(layout, 35.0)
    assert m._count_joint_coincidences_cm(juntas, [39.5, 54.5]) == 0, juntas


def test_licenca_nunca_cria_dois_b19_nem_b19_sem_conflito_de_cadeia():
    """Um trecho que fecha sem cadeia (tier 1-5) nunca ganha B19 forcado
    por causa da licenca, mesmo com junta empilhada."""
    for pier_cm in (79.0, 119.0, 159.0, 199.0):
        baseline = ws._pier_ordered_layout(pier_cm, CATALOG, 0.0, 0.0,
                                           leading_open_override=False,
                                           trailing_open_override=False)
        assert not any(CATALOG[c]["is_compensator"] for c in _codes(baseline))
        escolhido = ws._pier_layout_avoiding_joints(
            pier_cm, CATALOG, 0.0, 0.0, 0.0, [39.5, 79.5, 119.5, 159.5],
            leading_is_open=False, trailing_is_open=False)
        assert _codes(escolhido).count("B19") <= _codes(baseline).count("B19")
    # e nunca mais de UM B19 forcado
    for avoid in ([34.5], [24.5], [24.5, 34.5, 44.5], [34.5, 44.5]):
        assert _codes(_search(avoid)).count("B19") <= 1, avoid


def test_parede_curta_entre_canto_e_T_nao_tem_mais_junta_corrida_no_fill():
    """Geometria de W088/W090 (TP1): parede de 54cm entre um canto L e um T
    em que ela chega. Com a regra 11.14 o canto deita B34 na fiada A
    ([0,34]); a fiada B, entre o corpo do canto e a peca do T, tem 30cm
    de preenchimento. Antes: `C09 C09 C09` com junta em 34,5 embaixo da
    junta B34|fill da A. Agora: nenhuma junta no'|fill empilhada."""
    seg = NF.seg
    for short_cm in (54.0, 75.0, 110.0, 115.0, 150.0):
        lines = [seg(0, 0, 300, 0), seg(0, 0, 0, short_cm), seg(-300, short_cm, 300, short_cm)]
        with NF.node_fill(True):
            result, walls = NF.solve_plan(lines)
        assert NF.node_fill_prism_violations(walls, result["candidates"]) == [], short_cm
