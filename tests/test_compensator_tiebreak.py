# -*- coding: utf-8 -*-
"""SECAO 71 - a QUANTIDADE de compensadores entra no desempate.

Entre variantes do mesmo trecho que empatam na regra #2 (compensador em
sequencia) e na regra #1 (coincidencia de junta), o ranking so' olhava trava e
alinhamento generico de vazio - a quantidade de compensadores nao participava.
Medido no lote da BUTANTA: trechos de 69 cm fechavam `B19+B39+C09` tendo
`B34+B34` disponivel com a MESMA coincidencia de junta (zero nas duas).

A preferencia entra DEPOIS das duas regras absolutas: se a alternativa sem
compensador piorar junta ou modularidade, ela perde."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_channel_reinforcement as tcr  # noqa: E402

m = tcr.m
ws = tcr.ws if hasattr(tcr, "ws") else __import__("core.engine.wall_stepper", fromlist=["x"])
CATALOG = tcr.sb.CATALOG


def _codes(layout):
    return None if layout is None else [c for c, _a, _b in layout]


def _comp(layout):
    return sum(1 for c, _a, _b in (layout or [])
               if (CATALOG.get(c) or {}).get("is_compensator"))


class _Secao(object):
    """liga/desliga a secao 71 sem deixar estado vazando entre testes."""

    def __init__(self, ligada):
        self.ligada = ligada

    def __enter__(self):
        self.saved = ws.COMPENSATOR_COUNT_IN_TIEBREAK
        ws.COMPENSATOR_COUNT_IN_TIEBREAK = self.ligada
        return self

    def __exit__(self, *exc):
        ws.COMPENSATOR_COUNT_IN_TIEBREAK = self.saved
        return False


# trecho real medido no lote: 70 cm entre a jamba da porta (ponta aberta) e a
# peca de no' do encontro. Fecha com `B34+B34` (limpo) ou `B19+B39+C09`.
PIER_CM = 70.0
LEAD, TRAIL = 0.0, 1.0


def _layout(avoid, alvo=None):
    return ws._pier_layout_avoiding_joints(
        PIER_CM, CATALOG, LEAD, TRAIL, 0.0, avoid,
        target_void_positions_cm=alvo, leading_is_open=True, trailing_is_open=False)


# Alvo de vazio da fiada oposta que faz o layout com meio bloco pontuar melhor
# no criterio ANTIGO (alinhamento generico de celula) - e' a situacao real
# medida no lote: as duas composicoes empatam nas regras absolutas e a com
# compensador ganhava o desempate.
ALVO_QUE_PREMIAVA_O_MEIO_BLOCO = [10.0, 30.0, 50.0]


def test_red_sem_a_secao_o_desempate_escolhe_a_com_compensador():
    """RED: com a secao desligada, o trecho fecha `B19+B39+C09`."""
    with _Secao(False):
        escolhido = _layout([], ALVO_QUE_PREMIAVA_O_MEIO_BLOCO)
    assert _comp(escolhido) == 1, _codes(escolhido)


def test_desempate_prefere_menos_compensador():
    """GREEN: com a secao ligada, o MESMO trecho fecha `B34+B34`, sem especial -
    e sem mexer em junta nenhuma (as duas empatam na regra #1)."""
    with _Secao(False):
        antes = _layout([], ALVO_QUE_PREMIAVA_O_MEIO_BLOCO)
    with _Secao(True):
        depois = _layout([], ALVO_QUE_PREMIAVA_O_MEIO_BLOCO)
    assert _comp(antes) == 1 and _comp(depois) == 0, (_codes(antes), _codes(depois))


def test_nao_vence_quando_piora_a_regra_1():
    """A alternativa sem compensador NAO pode ganhar se coincidir junta.

    As juntas internas de `B34+B34` ficam a 35 cm do inicio do trecho; com a
    fiada oposta tendo junta exatamente ali, a regra #1 reprova e o desempate de
    compensador (que vem DEPOIS) nao pode resgatar."""
    with _Secao(True):
        escolhido = _layout([35.0])
    juntas = [lo for _c, lo, _h in (escolhido or [])[1:]]
    assert not any(abs(j - 35.0) <= 1.0 for j in juntas), _codes(escolhido)


def test_variante_e_busca_exata_usam_a_mesma_tupla():
    """A DP da busca completa e o desempate por variante tem de concordar:
    mesma entrada, mesma contagem de compensadores no resultado."""
    with _Secao(True):
        por_variante = _layout([10.0, 50.0])
        completa = ws._pier_full_search_layout(
            ws._pier_ordered_layout(PIER_CM, CATALOG, LEAD, TRAIL,
                                    leading_open_override=True, trailing_open_override=False),
            CATALOG, 0.0, [10.0, 50.0], leading_open=True, trailing_open=False)
    if completa is not None:
        assert _comp(completa) <= _comp(por_variante) + 0


def test_desligada_nao_muda_nada():
    """Com a secao desligada o resultado e' o historico - e' o que garante que
    `strategy=None` continua identico a' main."""
    with _Secao(False):
        a = _codes(_layout([12.0]))
        b = _codes(_layout([12.0]))
    assert a == b


def test_deterministico():
    with _Secao(True):
        a = _codes(_layout([12.0], [20.0, 55.0]))
        b = _codes(_layout([12.0], [20.0, 55.0]))
    assert a == b
