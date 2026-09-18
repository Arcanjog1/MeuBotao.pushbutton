# -*- coding: utf-8 -*-
"""REGRA 76 / correcao D1 - T degradado num pilar entre duas aberturas.

Topologia do no' 22 do BUTANTA, sintetica: parede principal com duas janelas
cujas jambas deixam um pilar de 34 cm em volta do encontro (27 cm de um lado do
eixo da parede que chega, 7 cm do outro). O B54 nao cabe; o passo "degrada para
L" exigia 34 cm a partir do PONTO do no', mas o B34 e' posto a partir do CONTATO
(meia espessura atras do ponto) e so' ocupa 27 cm do lado livre - cabe. Antes da
D1 o no' caia na escada do elemento unico e a familia oposta recebia um C09 como
peca do no'.

    python3 -m pytest tests/test_regra76_d1_t_degradado.py -q
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import test_channel_reinforcement as tcr  # noqa: E402

m, ft, seg, solve = tcr.m, tcr.ft, tcr.seg, tcr.solve
from core.engine import wall_stepper as ws  # noqa: E402

NO_T = 300.0


def pilar_34():
    """Principal 0..604 com janelas [150,273] e [307,450] (peitoril 80, topo 221):
    pilar de 34 cm (273..307) em volta do no' em t=300."""
    lines = [seg(0, 0, 604, 0), seg(NO_T, 0, NO_T, 298)]
    janelas = [(ft(150.0), ft(NO_T - 27.0), ft(80.0), ft(221.0)),
               (ft(NO_T + 7.0), ft(450.0), ft(80.0), ft(221.0))]
    return lines, [janelas, []]


def _ocupantes(res, walls, nodes):
    """{fiada: (codigo, razao)} do ocupante da regiao do no' T."""
    ni = [i for i, n in enumerate(nodes) if n.get("kind") == "T_INTERSECTION"][0]
    n = nodes[ni]
    poly = ws._node_region_polygon(n, walls)
    area = ws._poly_area(poly)
    paredes = ws._node_wall_indices(n)
    out = {}
    for ci, pecas in res["course_candidates"].items():
        best = None
        for c in pecas:
            if c.get("wall_idx") not in paredes:
                continue
            ov = ws._convex_overlap_area(ws._candidate_polygon(c), poly)
            if ov > 1e-6 * area and (best is None or ov > best[0]):
                best = (ov, c.get("logical_code"), str(c.get("placement_reason") or ""))
        out[ci] = best[1:] if best else None
    return out


def test_com_a_d1_o_pilar_amarra_com_b34_nas_duas_familias():
    res, walls, nodes, _o = solve(*pilar_34())
    assert res["compensator_as_junction_bond"] == []
    ocup = _ocupantes(res, walls, nodes)
    for ci in range(4, 11):   # faixa da janela
        assert ocup[ci] is not None and ocup[ci][0] == "B34", (ci, ocup[ci])
        assert ocup[ci][1].startswith("T_INTERSECTION_DEGRADED_L"), (ci, ocup[ci])


def test_mutante_sem_a_d1_o_c09_volta_a_ser_peca_do_no_e_o_gate_acusa():
    antes = m.CHANNEL_T_DEGRADED_L_ROOM_FROM_CONTACT_ENABLED
    m.CHANNEL_T_DEGRADED_L_ROOM_FROM_CONTACT_ENABLED = False
    try:
        res, walls, nodes, _o = solve(*pilar_34())
    finally:
        m.CHANNEL_T_DEGRADED_L_ROOM_FROM_CONTACT_ENABLED = antes
    gate = res["compensator_as_junction_bond"]
    assert gate, "sem a D1 o compensador volta a amarrar - o gate tem de acusar"
    assert all(v["logical_code"] in ("C04", "C09") for v in gate)
    assert all("OCCUPIES_NODE_REGION" in v["evidence"] for v in gate)


def test_a_d1_nao_muda_no_que_ja_degradava_para_l():
    """Com 34 cm livres a partir do ponto (teste historico passa) a D1 nao age:
    mesma geometria com e sem a flag."""
    lines = [seg(0, 0, 604, 0), seg(NO_T, 0, NO_T, 298)]
    janelas = [(ft(150.0), ft(NO_T - 40.0), ft(80.0), ft(221.0)),
               (ft(NO_T + 7.0), ft(450.0), ft(80.0), ft(221.0))]
    com, walls, nodes, _o = solve(lines, [janelas, []])
    antes = m.CHANNEL_T_DEGRADED_L_ROOM_FROM_CONTACT_ENABLED
    m.CHANNEL_T_DEGRADED_L_ROOM_FROM_CONTACT_ENABLED = False
    try:
        sem, _w, _n, _o = solve(lines, [janelas, []])
    finally:
        m.CHANNEL_T_DEGRADED_L_ROOM_FROM_CONTACT_ENABLED = antes
    assert tcr.physical_signature(com, walls) == tcr.physical_signature(sem, walls)


def test_a_d1_nasce_desligada_no_motor_e_so_o_channel_liga():
    assert ws.T_DEGRADED_L_ROOM_FROM_CONTACT is False
    assert m.CHANNEL_T_DEGRADED_L_ROOM_FROM_CONTACT_ENABLED is True
    res, _w, _n, _o = solve(*pilar_34(), strategy=None)
    assert "compensator_as_junction_bond" not in res
    assert ws.T_DEGRADED_L_ROOM_FROM_CONTACT is False


def test_candidatas_pendentes_seguem_desligadas():
    """R76 (recuo), D2 (B19) e D3 (outro braco) foram MEDIDAS e pioram portoes
    duros no corpus - ficam desligadas ate' decisao do usuario."""
    assert ws.COMPENSATOR_NEVER_JUNCTION_BOND is False
    assert ws.JUNCTION_BOND_B19_FALLBACK is False
    assert ws.L_CORNER_OTHER_ARM_OWNS is False
