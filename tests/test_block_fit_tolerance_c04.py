# -*- coding: utf-8 -*-
"""CR-BLOCK-FIT-TOLERANCE-C04 (FIT_TOLERANCE_NOISE) - testes de borda da
nova tolerancia DEDICADA de "fit" modular, PIER_FIT_TOLERANCE_CM (0,30cm).

Causa-raiz: o solver rejeitava restos geometricamente validos quando o
comprimento calculado se afastava por poucos decimos de cm do multiplo
modular esperado (PIER_MODULE_CM=5cm) - a tolerancia antiga
(PIER_LAYOUT_TOLERANCE_CM/MODULATION_WHOLE_CM_TOLERANCE_CM = 0,05cm) so'
absorvia o ruido de UMA conversao pes<->cm, nao o ruido ACUMULADO de
varias operacoes encadeadas (encontro + extend_wall_ends_to_junctions).

Esta suite cobre:

1. `pier_closes_with_blocks_cm`/`wall_length_closes_with_blocks_cm`
   (core/engine/modulation_math.py, 100% puro) - a pre-checagem.
2. `_pier_remaining_snapped_cm` (core/engine/wall_stepper.py, via
   `load_script`/`revit_stubs`) - o mecanismo REAL que o empacotador usa,
   alvo direto desta CR.
3. Escopo: as tolerancias DERIVADAS de PIER_LAYOUT_TOLERANCE_CM
   (adjacencia de compensador/meio-bloco) continuam em 0,05cm - a CR
   proibe alarga-las.

Ver docs/BLOCK_FIT_TOLERANCE_C04_IMPLEMENTATION.md.

    python3 -m pytest tests/test_block_fit_tolerance_c04.py -q
"""

import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import load_script  # noqa: E402

m = load_script.load()

# Import direto do modulo puro (sem stub nenhum) para os testes que nao
# precisam do motor completo - mais rapido e mais isolado.
_NUVEM_ROOT = os.path.join(_ROOT, "nuvem")
if _NUVEM_ROOT not in sys.path:
    sys.path.insert(0, _NUVEM_ROOT)
from core.engine import modulation_math as mm  # noqa: E402

PIER_FIT_TOLERANCE_CM = mm.PIER_FIT_TOLERANCE_CM
PIER_LAYOUT_TOLERANCE_CM = mm.PIER_LAYOUT_TOLERANCE_CM
BLOCK_JOINT_CM = mm.BLOCK_JOINT_CM
BLOCK_OPENING_JOINT_CM = mm.BLOCK_OPENING_JOINT_CM


# ======================================================================
# 0. A constante em si - valor aprovado e separacao das demais
# ======================================================================

class TestConstantScope(object):
    def test_pier_fit_tolerance_is_030(self):
        assert PIER_FIT_TOLERANCE_CM == pytest.approx(0.30)

    def test_pier_fit_tolerance_is_wider_than_layout_tolerance(self):
        # A CR exige que o "fit" fique mais permissivo SEM alargar
        # PIER_LAYOUT_TOLERANCE_CM (que continua 0,05cm - ver secao 5).
        assert PIER_FIT_TOLERANCE_CM > PIER_LAYOUT_TOLERANCE_CM
        assert PIER_LAYOUT_TOLERANCE_CM == pytest.approx(0.05)

    def test_derived_adjacency_tolerances_stay_at_old_value(self):
        """Tolerancias DERIVADAS de PIER_LAYOUT_TOLERANCE_CM (adjacencia
        fisica de meio-bloco/compensador em wall_modeling.py) NAO podem
        ter sido alargadas por esta CR - escopo estrito (secao 5)."""
        half_tie = getattr(m, "HALF_BLOCK_TIE_ADJACENCY_CM")
        comp_open = getattr(m, "COMPENSATOR_OPENING_ADJACENCY_TOLERANCE_CM")
        assert half_tie == pytest.approx(BLOCK_JOINT_CM + PIER_LAYOUT_TOLERANCE_CM)
        assert comp_open == pytest.approx(BLOCK_OPENING_JOINT_CM + PIER_LAYOUT_TOLERANCE_CM)
        # nao podem ter "vazado" o valor novo (0,30cm)
        assert half_tie != pytest.approx(BLOCK_JOINT_CM + PIER_FIT_TOLERANCE_CM)
        assert comp_open != pytest.approx(BLOCK_OPENING_JOINT_CM + PIER_FIT_TOLERANCE_CM)


# ======================================================================
# 1. pier_closes_with_blocks_cm / wall_length_closes_with_blocks_cm
#    (pre-checagem pura, core/engine/modulation_math.py)
# ======================================================================

# pier_closes_with_blocks_cm(pier_cm, lead, trail) fecha quando
# (pier_cm - lead - trail + BLOCK_JOINT_CM) e' multiplo de PIER_MODULE_CM
# (=5). Com lead=BLOCK_JOINT_CM(1) e trail=BLOCK_OPENING_JOINT_CM(0):
# remaining = pier_cm - 1 - 0 + 1 = pier_cm -> pier_cm precisa estar perto
# de um multiplo de 5 (0, 5, 10, ... 830, ...).
LEAD, TRAIL = BLOCK_JOINT_CM, BLOCK_OPENING_JOINT_CM


def _closes(pier_cm):
    return mm.pier_closes_with_blocks_cm(pier_cm, LEAD, TRAIL)


class TestPierClosesWithBlocksTolerance(object):
    # ---- ao redor de um multiplo de 5 (830cm) ----
    @pytest.mark.parametrize("pier_cm", [
        830.00, 830.05, 830.10, 830.15, 830.20, 830.25, 830.29, 830.30,
        829.95, 829.90, 829.80, 829.71, 829.70,
    ])
    def test_within_tolerance_snaps(self, pier_cm):
        assert _closes(pier_cm) is True

    @pytest.mark.parametrize("pier_cm", [830.31, 830.35, 829.69, 829.65])
    def test_outside_tolerance_does_not_snap(self, pier_cm):
        assert _closes(pier_cm) is False

    def test_exactly_at_the_limit_is_defined_as_snapping(self):
        # comportamento definido: no limite exato (diferenca == tolerancia),
        # o teste usa "<=" - fecha (ver pier_closes_with_blocks_cm).
        assert _closes(830.0 + PIER_FIT_TOLERANCE_CM) is True
        assert _closes(830.0 - PIER_FIT_TOLERANCE_CM) is True

    def test_just_past_the_limit_does_not_snap(self):
        eps = 1e-6
        assert _closes(830.0 + PIER_FIT_TOLERANCE_CM + eps) is False
        assert _closes(830.0 - PIER_FIT_TOLERANCE_CM - eps) is False

    # ---- faixa antiga (0,05cm) nao era suficiente - prova da regressao
    # que esta CR corrige: 830,20 e 829,80 (0,20cm de ruido) FICAVAM fora
    # da tolerancia antiga mas agora fecham. ----
    def test_noise_beyond_old_tolerance_now_closes(self):
        assert abs(830.20 - 830.0) > PIER_LAYOUT_TOLERANCE_CM
        assert _closes(830.20) is True
        assert abs(829.80 - 830.0) > PIER_LAYOUT_TOLERANCE_CM
        assert _closes(829.80) is True

    # ---- um resto genuinamente NAO-modular (155,5cm nunca fecha,
    # nenhuma tolerancia razoavel deveria aceitar isso) ----
    def test_genuinely_non_modular_length_never_closes(self):
        assert _closes(832.5) is False
        assert _closes(155.5) is False

    # ---- outros multiplos de 5 pelo corpus (nao so' 830) ----
    @pytest.mark.parametrize("base_cm", [5, 10, 15, 20, 55, 100, 405, 1000])
    def test_other_multiples_of_five_also_snap_within_tolerance(self, base_cm):
        assert _closes(base_cm + 0.25) is True
        assert _closes(base_cm - 0.25) is True
        assert _closes(base_cm + 0.35) is False

    def test_wall_length_closes_with_blocks_cm_uses_same_tolerance(self):
        # Wrapper permissivo (tenta as 4 combinacoes de junta de contorno) -
        # deve fechar para o mesmo residuo de ruido dentro de 0,30cm.
        assert mm.wall_length_closes_with_blocks_cm(830.20) is True
        assert mm.wall_length_closes_with_blocks_cm(830.35) is False


# ======================================================================
# 2. _pier_remaining_snapped_cm (mecanismo REAL do empacotador,
#    core/engine/wall_stepper.py)
# ======================================================================

def _remaining(pier_cm, lead=BLOCK_JOINT_CM, trail=BLOCK_OPENING_JOINT_CM):
    return m._pier_remaining_snapped_cm(pier_cm, lead, trail)


class TestPierRemainingSnappedCm(object):
    """`_pier_remaining_snapped_cm(pier_cm, lead, trail)` calcula
    `remaining = pier_cm - lead - trail + BLOCK_JOINT_CM` e devolve o
    multiplo de PIER_MODULE_CM mais proximo se `|remaining - multiplo| <=
    PIER_FIT_TOLERANCE_CM`, None caso contrario. Com lead=1, trail=0:
    remaining == pier_cm."""

    @pytest.mark.parametrize("pier_cm,expected_snapped", [
        (830.00, 830.0), (830.05, 830.0), (830.10, 830.0), (830.15, 830.0),
        (830.20, 830.0), (830.25, 830.0), (830.29, 830.0), (830.30, 830.0),
        (829.95, 830.0), (829.90, 830.0), (829.80, 830.0), (829.71, 830.0),
        (829.70, 830.0),
    ])
    def test_within_tolerance_snaps_to_nearest_module(self, pier_cm, expected_snapped):
        result = _remaining(pier_cm)
        assert result == pytest.approx(expected_snapped)

    @pytest.mark.parametrize("pier_cm", [830.31, 830.35, 829.69, 829.65])
    def test_outside_tolerance_returns_none(self, pier_cm):
        assert _remaining(pier_cm) is None

    def test_negative_beyond_tolerance_returns_none(self):
        # pier_cm bem menor que as juntas de contorno -> remaining bem
        # negativo -> nunca fecha, tolerancia nenhuma deveria salvar isso.
        assert _remaining(-10.0) is None

    def test_small_negative_within_tolerance_is_treated_as_empty(self):
        # remaining levemente negativo (ruido) dentro de
        # PIER_FIT_TOLERANCE_CM conta como trecho vazio (0.0), nao None.
        pier_cm = -(PIER_FIT_TOLERANCE_CM / 2.0)
        assert _remaining(pier_cm) == pytest.approx(0.0)

    def test_floating_point_adversarial_noise(self):
        # Ruido tipico de conversao pes<->cm (o caso real medido:
        # 829,99791 em vez de 830 - ~0,002cm). Bem dentro da tolerancia
        # nova E' da antiga - nao pode ter regredido.
        assert _remaining(829.99791) == pytest.approx(830.0)
        # Ruido maior (~0,29cm), so' absorvido pela tolerancia NOVA.
        noisy = 830.0 - 0.29
        assert _remaining(noisy) == pytest.approx(830.0)

    def test_symmetric_positive_and_negative_offsets(self):
        for offset in (0.05, 0.10, 0.20, 0.29, 0.30):
            assert _remaining(830.0 + offset) == pytest.approx(830.0)
            assert _remaining(830.0 - offset) == pytest.approx(830.0)
        for offset in (0.31, 0.40):
            assert _remaining(830.0 + offset) is None
            assert _remaining(830.0 - offset) is None

    def test_result_matches_pier_closes_with_blocks_cm_verdict(self):
        # Invariante do design (comentario de PIER_FIT_TOLERANCE_CM):
        # pre-checagem e solver real NUNCA podem discordar sobre o que
        # fecha.
        for pier_cm in (830.20, 830.30, 830.31, 829.70, 829.65, 155.5):
            snapped = _remaining(pier_cm)
            closes = _closes(pier_cm)
            assert (snapped is not None) == closes, pier_cm


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
