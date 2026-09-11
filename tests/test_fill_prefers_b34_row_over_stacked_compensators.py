# -*- coding: utf-8 -*-
"""Secao 2 de REGRAS_MODULACAO_BLOCOS.md, regra da FILEIRA DE B34 (revisada em
2026-09-11 pela evidencia do projeto humano BUTANTA R08_LT, decisao do usuario):
o teto MAX_SPECIAL_BOND_PER_TRECHO e' de PREFERENCIA, nao proibicao. Ordem:
B39 -> B19 em ponta aberta -> ate' 1 B34 -> 1 unico compensador -> FILEIRA de
B34 -> meio-bloco forcado -> 2+ compensadores.

Bug real medido no projeto humano (2026-09-10): trecho de 466cm (com juntas)
fechava com 11xB39 + C09 C09 C04 - tres compensadores em sequencia, reprovados
pelo proprio auditor - porque a fileira de B34 (tier 3, rejeitada so' pelo
teto) vinha DEPOIS do fallback irrestrito de compensadores. O humano fecha o
mesmo trecho com 9xB39 + 3xB34; corridas de 2 a 6 B34 sao rotina la' (1.615
B34 contra 242 C09 no 1o pavimento).
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


def _n_b34(codes):
    return sum(1 for c in codes if CATALOG[c].get("is_special_bond"))


def _modular_lengths():
    """Modulos (comprimento + junta) de cada peca, lidos do catalogo - nunca
    numeros fixos."""
    return dict((code, spec["length_cm"] + 1.0) for code, spec in CATALOG.items())


def _closes_with(total_cm, max_b34, max_comp, mod):
    """Existe composicao do trecho com <= max_b34 pecas de 34, <= max_comp
    compensadores e nenhum B19? (forca bruta sobre o catalogo)."""
    big = [c for c in CATALOG if not CATALOG[c].get("is_compensator")
           and not CATALOG[c].get("is_special_bond") and c != m.HALF_BLOCK_CODE]
    b34s = [c for c in CATALOG if CATALOG[c].get("is_special_bond") and c != "B54"]
    comps = [c for c in CATALOG if CATALOG[c].get("is_compensator")]
    target = round(total_cm - 1.0, 3)   # a ultima peca nao paga junta de saida
    seen = set()

    def rec(rest, nb34, ncomp):
        key = (round(rest, 3), nb34, ncomp)
        if key in seen:
            return False
        seen.add(key)
        if abs(rest) < 1e-6:
            return True
        if rest < 0:
            return False
        for c in big:
            if rec(rest - mod[c], nb34, ncomp):
                return True
        if nb34 < max_b34:
            for c in b34s:
                if rec(rest - mod[c], nb34 + 1, ncomp):
                    return True
        if ncomp < max_comp:
            for c in comps:
                if rec(rest - mod[c], nb34, ncomp + 1):
                    return True
        return False

    return rec(target, 0, 0)


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


def test_regra_geral_fileira_de_b34_so_quando_nem_um_b34_nem_um_compensador_fecham():
    """A regra e' GERAL (varre todo comprimento inteiro de 40 a 900cm) e
    explicavel: uma fileira de B34 (> MAX_SPECIAL_BOND_PER_TRECHO) so'
    aparece quando NAO existe fechamento com <= 1 B34 e <= 1 compensador;
    e, quando a fileira existe, o solver NUNCA empilha 2+ compensadores.
    O contrario tambem vale: 2+ compensadores so' quando nem a fileira de
    B34 fecha (o teto continua sendo a preferencia)."""
    mod = _modular_lengths()
    fileiras = 0
    for total in range(40, 901):
        codes = _codes(float(total))
        if not codes:
            continue
        nb34, ncomp = _n_b34(codes), _n_comp(codes)
        if nb34 > m.MAX_SPECIAL_BOND_PER_TRECHO:
            fileiras += 1
            assert ncomp == 0, (total, codes)
            assert not _closes_with(total, m.MAX_SPECIAL_BOND_PER_TRECHO,
                                    m.MAX_COMPENSATORS_PER_TRECHO, mod), (total, codes)
        elif ncomp > m.MAX_COMPENSATORS_PER_TRECHO:
            assert not _closes_with(total, 99, 0, mod), (total, codes)
    assert fileiras > 0, "a varredura nao exercitou nenhuma fileira de B34"
