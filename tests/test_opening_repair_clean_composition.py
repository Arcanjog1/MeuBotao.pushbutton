# -*- coding: utf-8 -*-
"""SECAO 68 - a faixa jamba->ancora e' composta como UMA unidade.

A regiao de reparo de uma abertura so' era expandida quando NAO fechava; quando
fechava MAL (meio bloco + pastilha + compensador herdado da modulacao continua)
a primeira composicao que fechasse era aceita. Evidencia humana de 2026-09-16
(parede 8284534 do BUTANTA): a faixa de 75 cm entre a jamba da porta e o no' do
encontro sai `B19+C04+B39+C09` no solver e `B39+B34` no projeto humano.

Estes testes NAO fixam parede, ElementId nem deslocamento: usam a geometria
generica "porta ao lado de um T" que os testes de canaleta ja' usam."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_channel_audit_fixes as tca  # noqa: E402
import test_channel_reinforcement as tcr  # noqa: E402

m = tcr.m
ws = tcr.ws if hasattr(tcr, "ws") else __import__("core.engine.wall_stepper", fromlist=["x"])
CATALOG = tcr.sb.CATALOG

# Posicoes (cm) da jamba da porta nesta parede de 584 cm com um T em x=382:
# medidas no proprio fixture, nao escolhidas a dedo - ver o scan em
# docs/checkpoints (secao 68). A faixa jamba->no' fecha sem peca de acerto.
JAMBA_LIMPA = (310.0, 411.0)
# Aqui a faixa NAO tem nenhuma composicao sem peca de acerto: serve para provar
# que a regra nao inventa geometria quando o bloco inteiro nao fecha.
JAMBA_PRESA = (269.0, 370.0)


def _acerto(res, walls, course=0):
    """Pecas de ACERTO da fiada: compensador, pastilha e meio bloco."""
    codigos = [r["cand"]["logical_code"] for r in tcr.strip(res, walls, 0, course)]
    return [c for c in codigos if (CATALOG.get(c) or {}).get("is_compensator") or c == ws.HALF_BLOCK_CODE]


def _resolve(jamba, clean):
    saved = m.CHANNEL_REPAIR_PREFER_CLEAN_ENABLED
    m.CHANNEL_REPAIR_PREFER_CLEAN_ENABLED = clean
    try:
        lines, ops = tca._door_next_to_tee(jamba[0], jamba[1])
        return tcr.solve(lines, ops)
    finally:
        m.CHANNEL_REPAIR_PREFER_CLEAN_ENABLED = saved


def test_red_primeira_composicao_que_fecha_deixa_compensador_e_meio_bloco():
    """RED (comportamento antigo): a janela estreita de reparo fecha com peca de
    acerto e as pecas vizinhas da modulacao continua ficam congeladas."""
    res, walls, _n, _o = _resolve(JAMBA_LIMPA, False)
    assert _acerto(res, walls) != []


def test_faixa_jamba_ate_ancora_fecha_sem_peca_de_acerto():
    """GREEN: expandindo dentro do orcamento que ja' existia, a MESMA faixa
    fecha so' com bloco - e' a composicao que o projeto humano usa."""
    res, walls, _n, _o = _resolve(JAMBA_LIMPA, True)
    assert _acerto(res, walls) == []


def test_nao_inventa_geometria_quando_o_bloco_inteiro_nao_fecha():
    """A regra e' de PREFERENCIA, nao de proibicao: onde nenhuma composicao
    fecha sem peca de acerto, a peca de acerto continua la'."""
    livre = 65.0     # medido na parede 8284534 depois do microajuste de +5 cm
    layout = ws._pier_ordered_layout(livre, CATALOG, 0.0, 1.0,
                                     leading_open_override=True, trailing_open_override=False)
    assert layout is not None
    assert any((CATALOG.get(code) or {}).get("is_compensator") for code, _a, _b in layout)
    # e no fluxo completo a regra nao piora nada nesse fixture: mesmos trechos
    # sem modulacao e mesmas colisoes com a flag ligada e desligada (o fixture
    # ja' nasce com 4 trechos nao modulares na parede que chega no T).
    antes = _resolve(JAMBA_PRESA, False)[0]
    depois = _resolve(JAMBA_PRESA, True)[0]
    assert depois.get("error") is None
    assert len(depois["non_modular"]) <= len(antes["non_modular"])
    assert depois["collisions"] == antes["collisions"] == []


def test_qualidade_prefere_bloco_a_compensador_e_so_depois_bloco_inteiro():
    """A ORDEM do criterio: um B34 a mais nunca perde para um compensador."""
    sub = {"lo": 0.0}
    com_comp = [(sub, [("B39", 0.0, 39.0), ("C09", 40.0, 49.0), ("B19", 50.0, 69.0)])]
    com_b34 = [(sub, [("B39", 0.0, 39.0), ("B34", 40.0, 74.0)])]
    assert ws._repair_solution_quality(com_b34, CATALOG) < ws._repair_solution_quality(com_comp, CATALOG)


def test_nao_engole_peca_que_outro_reparo_ja_substituiu():
    """GUARDA: a expansao para a esquerda nao pode invadir o territorio de uma
    regiao de reparo anterior da MESMA fiada - isso gerava duas pecas
    OPENING_REPAIR_FILL sobrepostas (colisao medida na parede 8284502)."""
    saved = m.CHANNEL_REPAIR_PREFER_CLEAN_ENABLED
    m.CHANNEL_REPAIR_PREFER_CLEAN_ENABLED = True
    try:
        lines, ops = tca._double_passage()
        res, _walls, _n, _o = tcr.solve(lines, ops)
    finally:
        m.CHANNEL_REPAIR_PREFER_CLEAN_ENABLED = saved
    assert res["collisions"] == []


def test_legado_nao_muda():
    """`strategy=None` nao passa pela secao 68: assinatura fisica identica com a
    flag ligada e desligada."""
    lines, ops = tca._door_next_to_tee(*JAMBA_LIMPA)
    assinaturas = []
    for flag in (False, True):
        saved = m.CHANNEL_REPAIR_PREFER_CLEAN_ENABLED
        m.CHANNEL_REPAIR_PREFER_CLEAN_ENABLED = flag
        try:
            res, walls, _n, _o = tcr.solve(lines, ops, strategy=None)
        finally:
            m.CHANNEL_REPAIR_PREFER_CLEAN_ENABLED = saved
        assinaturas.append(tcr.physical_signature(res, walls))
    assert assinaturas[0] == assinaturas[1]


def test_idempotente():
    """Mesma entrada, duas execucoes: mesma geometria."""
    a_res, a_walls, _n, _o = _resolve(JAMBA_LIMPA, True)
    b_res, b_walls, _n2, _o2 = _resolve(JAMBA_LIMPA, True)
    assert tcr.physical_signature(a_res, a_walls) == tcr.physical_signature(b_res, b_walls)
