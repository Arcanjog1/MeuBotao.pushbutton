# -*- coding: utf-8 -*-
"""Testes de core/engine/modulation_math.py::evaluate_wall_block_length -
campo `is_clean_cm` (FASE 2 do plano em
C:\\Users\\CIVIX\\.claude\\plans\\quiet-painting-petal.md). Ver
tests/README.md.

Cobre o requisito explicito do usuario: um residuo pequeno tipo 25,01cm
(diferenca de so' 0,01cm de 25,00cm) precisa ser detectado como
"comprimento quebrado" (vermelho), MESMO quando a aritmetica de modulacao
(tolerancia LARGA, MODULATION_WHOLE_CM_TOLERANCE_CM=0,05cm) o trataria como
`compatible=True` - sem isso o residuo passaria silenciosamente. Ao mesmo
tempo, ruido de geometria genuino (ex.: 829,99791cm, medido numa planta
real do usuario - ver comentario de MODULATION_WHOLE_CM_TOLERANCE_CM em
core/engine/modulation_math.py) precisa continuar SEM ser sinalizado -
normalizacao de unidade com tolerancia adequada, nunca comparacao de float
"nua"."""
import os
import sys
import unittest

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_BUTTON_ROOT = os.path.dirname(_TESTS_DIR)
if _BUTTON_ROOT not in sys.path:
    sys.path.insert(0, _BUTTON_ROOT)

from core.engine.modulation_math import (
    evaluate_wall_block_length,
    MODULATION_WHOLE_CM_TOLERANCE_CM,
    BROKEN_LENGTH_RESIDUE_TOLERANCE_CM,
)


class EvaluateWallBlockLengthCleanCmTests(unittest.TestCase):
    def test_exact_integer_length_is_clean(self):
        result = evaluate_wall_block_length(830.0)
        self.assertTrue(result["is_clean_cm"])
        self.assertTrue(result["is_whole_cm"])
        self.assertTrue(result["compatible"])

    def test_real_geometry_noise_stays_clean(self):
        """O exemplo REAL medido (ver comentario da tolerancia larga) -
        829,99791cm em vez de 830cm, diferenca de ~0,00209cm - precisa
        continuar sem ser sinalizado como quebrado (e' ruido de calculo,
        nao um erro de desenho)."""
        result = evaluate_wall_block_length(829.99791)
        self.assertTrue(result["is_clean_cm"])
        self.assertTrue(result["is_whole_cm"])
        self.assertTrue(result["compatible"])

    def test_small_visible_residue_is_flagged_even_when_compatible(self):
        """O caso PEDIDO explicitamente pelo usuario: 25,01cm - a
        aritmetica de modulacao (tolerancia larga) trata como
        `compatible=True` (25cm fecha em blocos), mas o residuo de 0,01cm
        e' grande o bastante (> BROKEN_LENGTH_RESIDUE_TOLERANCE_CM) para
        precisar ser sinalizado e corrigido ANTES de confiar nisso."""
        result = evaluate_wall_block_length(25.01)
        self.assertFalse(result["is_clean_cm"])
        self.assertTrue(result["is_whole_cm"])   # dentro da tolerancia larga
        self.assertTrue(result["compatible"])    # a aritmetica deixaria passar
        self.assertEqual(result["length_cm_rounded"], 25)

    def test_length_far_from_any_integer_is_also_broken(self):
        """Comprimento genuinamente fracionario (bem alem de qualquer
        tolerancia) - continua vermelho (nao vira azul por acidente)."""
        result = evaluate_wall_block_length(127.43)
        self.assertFalse(result["is_clean_cm"])
        self.assertFalse(result["is_whole_cm"])
        self.assertFalse(result["compatible"])

    def test_clean_tolerance_is_strictly_tighter_than_whole_tolerance(self):
        """Garante a invariante documentada: is_clean_cm=True SEMPRE
        implica is_whole_cm=True (a tolerancia apertada e' um
        subconjunto da larga) - nunca o contrario."""
        self.assertLess(BROKEN_LENGTH_RESIDUE_TOLERANCE_CM, MODULATION_WHOLE_CM_TOLERANCE_CM)
        for length_cm in (100.0, 100.001, 100.004, 100.049, 99.951, 250.02):
            result = evaluate_wall_block_length(length_cm)
            if result["is_clean_cm"]:
                self.assertTrue(
                    result["is_whole_cm"],
                    "is_clean_cm=True mas is_whole_cm=False para {}cm".format(length_cm)
                )

    def test_broken_length_reports_correction_needed(self):
        """Formato do relatorio pedido pelo usuario (Parede X / Comprimento
        atual / Status / Comprimento sugerido / Correcao necessaria) -
        confirma que os campos usados por core/wall_modeling.py para montar
        essas linhas existem e tem os valores certos."""
        result = evaluate_wall_block_length(25.01)
        correction_needed_cm = result["length_cm_rounded"] - result["length_cm"]
        self.assertAlmostEqual(correction_needed_cm, -0.01, places=6)


if __name__ == "__main__":
    unittest.main()
