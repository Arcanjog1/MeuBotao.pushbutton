# -*- coding: utf-8 -*-
"""Parede cujo comprimento nao fecha em blocos fica INTEIRAMENTE VAZIA.

Reprodutor PERMANENTE da secao 42 de `nuvem/REGRAS_MODULACAO_BLOCOS.md`
(pendencia normativa aberta - NADA implementado). Estes testes NAO
consertam o comportamento: eles CARACTERIZAM a fronteira exata, com os
controles de medidas vizinhas, para que qualquer decisao futura do
usuario (manter / modular com folga / outra) tenha o caso medido pronto
e para que uma mudanca acidental nessa fronteira seja detectada.

Etapa EXATA que descarta a parede, medida (2026-09-09):
  `_pier_remaining_snapped_cm`  (nuvem/core/engine/wall_stepper.py)
    remaining = pier - lead - trail + BLOCK_JOINT_CM
    snapped   = 5 * round(remaining / 5)
    |remaining - snapped| > PIER_FIT_TOLERANCE_CM (0,30cm)  ->  None
  `_pier_ordered_layout` recebe None, tenta o fallback de junta de
  ABERTURA (as 3 combinacoes de junta de contorno) e, se nenhuma fechar,
  devolve None; o chamador registra `non_modular` e NAO lanca peca
  nenhuma - em TODAS as fiadas.

    python3 -m pytest tests/test_non_modular_wall_coverage.py -q
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import load_script  # noqa: E402
import revit_stubs  # noqa: F401,E402

from test_block_bonding import seg, solve_plan  # noqa: E402

m = load_script.load()


def _parede_livre(length_cm):
    """Uma parede reta isolada, as duas pontas LIVRES, sem abertura e sem
    encontro - o caso mais simples possivel."""
    result, _walls, _nodes = solve_plan([seg(0.0, 0.0, length_cm, 0.0)])
    return result


def _pecas(length_cm):
    return len(_parede_livre(length_cm)["candidates"])


# Comprimentos MEDIDOS (2026-09-09) numa parede livre com o catalogo
# padrao. O padrao e' "multiplo de 5cm, mais ou menos 1cm" - as tres
# combinacoes de junta de contorno que `_pier_ordered_layout` tenta
# (0/0, 1/0, 1/1) deslocam o alvo em 1cm para cada lado.
FECHAM_CM = (99.0, 99.75, 99.8, 100.0, 194.0, 195.0, 196.0, 199.0, 200.0,
             201.0, 269.0)
NAO_FECHAM_CM = (99.5, 197.0, 197.5, 197.9, 197.943, 198.0, 198.5, 199.5)


@pytest.mark.parametrize("length_cm", FECHAM_CM)
def test_controle_positivo_medidas_vizinhas_continuam_fechando(length_cm):
    """CONTROLE. Estas medidas fecham hoje - se alguma parar de fechar, a
    regressao e' de COBERTURA, muito pior que a pendencia da secao 42."""
    assert _pecas(length_cm) > 0, (
        "parede livre de %.3fcm deixou de receber peca" % length_cm)


@pytest.mark.parametrize("length_cm", NAO_FECHAM_CM)
def test_caracterizacao_medida_fora_do_modulo_fica_vazia(length_cm):
    """CARACTERIZACAO da pendencia 42 - NAO e' o comportamento desejado.

    Se algum destes passar a receber peca, foi porque a decisao normativa
    da secao 42 finalmente saiu: ATUALIZE a secao 42 e mova o comprimento
    para `FECHAM_CM`, em vez de so' apagar a linha."""
    assert _pecas(length_cm) == 0, (
        "parede livre de %.3fcm passou a fechar - se foi decisao da secao "
        "42, atualize a regra e mova para FECHAM_CM" % length_cm)


def test_o_caso_real_do_tgd_197_9cm():
    """As duas paredes reais do TGD (`W|-1257.1,3.4|-1252.4,201.3|t14.0` e
    `W|1446.8,201.3|1451.5,3.4|t14.0`, 197,943cm, as duas pontas
    FREE_END) saem VAZIAS - 1,98m de alvenaria sem uma peca. O achado
    carrega o ajuste pedido: 194cm (-4) ou 199cm (+1)."""
    result = _parede_livre(197.943)
    assert result["candidates"] == []
    non_modular = result.get("non_modular") or []
    assert non_modular, "esperava o trecho registrado como NON_MODULAR"
    achado = non_modular[0]
    assert achado["lower_valid_cm"] == 194
    assert achado["upper_valid_cm"] == 199
    assert achado["delta_to_upper_cm"] == 1, (
        "o sistema pede 1cm a mais - e' esse numero que a decisao da "
        "secao 42 tem de encarar")


def test_a_etapa_exata_e_o_snap_do_resto_do_trecho():
    """Localiza a ETAPA, nao so' o sintoma: e'
    `_pier_remaining_snapped_cm` que devolve None, e e' por passar da
    tolerancia de FIT - nao por ser negativo nem por catalogo."""
    lead = trail = m.BLOCK_OPENING_JOINT_CM  # duas pontas livres
    remaining_cru = m._pier_remaining_cm(197.943, lead, trail)
    assert remaining_cru > 0, "o trecho tem espaco de sobra - nao e' negativo"
    snapped = m.PIER_MODULE_CM * round(remaining_cru / float(m.PIER_MODULE_CM))
    assert abs(remaining_cru - snapped) > m.PIER_FIT_TOLERANCE_CM, (
        "%.3fcm de resto contra %.2fcm de tolerancia"
        % (abs(remaining_cru - snapped), m.PIER_FIT_TOLERANCE_CM))
    assert m._pier_remaining_snapped_cm(197.943, lead, trail) is None

    # e o mecanismo que EXISTE para o caso "conteudo modular imediatamente
    # ABAIXO" nao esta' ligado neste caminho - ele so' e' usado pela guarda
    # fisica da CR-BLOCK-FIT-TOLERANCE-C04. Aqui ele daria 194cm.
    floored = m.pier_cm_floored_to_module(197.943, lead, trail)
    assert floored == pytest.approx(194.0), (
        "o modulo imediatamente abaixo existe (%.2fcm) - e' a opcao 2 da "
        "secao 42, ainda NAO implementada" % floored)


def test_nenhuma_combinacao_de_junta_de_contorno_salva_197_9():
    """O fallback de junta de ABERTURA de `_pier_ordered_layout` tenta as
    tres combinacoes; nenhuma fecha. Isto e' o que separa 197,9cm (sem
    saida dentro do contrato) de 99,75cm (que so' fecha porque UMA das
    combinacoes cai dentro da tolerancia)."""
    for lead, trail in m.PIER_BOUNDARY_JOINT_COMBINATIONS_CM:
        assert m._pier_remaining_snapped_cm(197.943, lead, trail) is None, (
            "combinacao %s/%s fecharia - a secao 42 estaria errada"
            % (lead, trail))
    assert any(m._pier_remaining_snapped_cm(99.754, lead, trail) is not None
               for lead, trail in m.PIER_BOUNDARY_JOINT_COMBINATIONS_CM), (
        "99,754cm TEM de fechar em alguma combinacao - se nao fechar, a "
        "parede real de 99,75cm do TGD estaria vazia pelo mesmo motivo da "
        "secao 42, e nao pelo motivo dos encontros (ver 42.4)")
