# -*- coding: utf-8 -*-
"""Secao 2 de REGRAS_MODULACAO_BLOCOS.md: acima de MAX_COMPENSATORS_PER_TRECHO
o solver prefere B34 (em qualquer posicao) a empilhar compensadores.

Bug real medido no projeto humano BUTANTA R08_LT (2026-09-10): trecho de
466cm (com juntas) fechava com 11xB39 + C09 C09 C04 - tres compensadores em
sequencia, reprovados pelo proprio auditor - porque a fileira de B34 (tier 3,
rejeitada so' pelo teto MAX_SPECIAL_BOND_PER_TRECHO) vinha DEPOIS do fallback
irrestrito de compensadores. O humano fecha o mesmo trecho com 9xB39 + 3xB34.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import solver_bench as sb  # noqa: E402

m = sb.m
CATALOG = sb.CATALOG


def _codes(pier_cm):
    layout = m._pier_ordered_layout(pier_cm, CATALOG, 1.0, 1.0)
    return [code for code, _a, _b in (layout or [])]


def _n_comp(codes):
    return sum(1 for c in codes if CATALOG[c].get("is_compensator"))


def test_trecho_de_466_fecha_com_fileira_de_b34_e_zero_compensador():
    codes = _codes(466.0)
    assert codes, "466cm fecha (465 uteis = 9x40 + 3x35)"
    assert _n_comp(codes) == 0, codes
    assert codes.count("B34") == 3 and codes.count("B39") == 9, codes


def test_nunca_mais_de_um_compensador_quando_existe_fileira_de_b34():
    for pier in (426.0, 506.0, 386.0):
        codes = _codes(pier)
        assert codes and _n_comp(codes) <= m.MAX_COMPENSATORS_PER_TRECHO, (pier, codes)
        assert codes.count("B34") >= 2, (pier, codes)


def test_um_compensador_dentro_do_teto_continua_preferido_a_b34():
    """Controle: tier 5 (<= 1 compensador) ainda vem antes da fileira de B34
    acima do teto - 246cm = 6x40 + C04, nao 4x40 + 2x35 + ...; o que mudou e'
    so' a posicao relativa ao fallback com MAIS de um compensador."""
    codes = _codes(246.0)
    assert _n_comp(codes) == 1, codes


def test_bancada_de_340_fecha_com_11_pecas_como_no_revit_real():
    """A bancada real (2 paredes, 14 fiadas) tem 154 blocos = 11 por fiada:
    340cm entre canto e ponta livre agora fecha sem compensador."""
    codes = _codes(340.0 - 34.0)   # trecho depois do B34 de canto, 306cm
    assert codes and _n_comp(codes) == 0, codes
