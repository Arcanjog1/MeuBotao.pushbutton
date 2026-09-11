# -*- coding: utf-8 -*-
"""Regra 8a - a origem vertical e' o NIVEL, no referencial INTERNO do projeto.

Bug real medido em BUTANTA R08_LT (2026-09-10): niveis com Base de elevacao =
Ponto de Levantamento devolvem Level.Elevation = 72.665 cm enquanto Walls e
blocos vivem em ProjectElevation = 0. Usar .Elevation como base_z_abs poria a
modulacao 726 m acima das paredes."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import load_script  # noqa: E402

m = load_script.load()


class _SurveyLevel(object):
    Elevation = 2384.0        # ~72.665 cm em pes: cota relativa ao survey
    ProjectElevation = 0.0    # cota interna real


class _LegacyLevel(object):
    Elevation = -1.706        # dublê antigo, sem ProjectElevation


def test_usa_project_elevation_quando_existe():
    assert m._level_internal_elevation_ft(_SurveyLevel()) == 0.0


class _InertLevel(object):
    """Duble que responde a QUALQUER atributo com um objeto inerte (como
    revit_stubs._Inert): ProjectElevation existe, mas nao e' numero."""
    Elevation = 2.5

    def __getattr__(self, name):
        return object()


def test_project_elevation_nao_numerico_cai_para_elevation():
    assert m._level_internal_elevation_ft(_InertLevel()) == 2.5


def test_fallback_para_elevation_em_nivel_sem_a_propriedade():
    assert m._level_internal_elevation_ft(_LegacyLevel()) == -1.706


def test_nenhum_uso_direto_de_level_elevation_sobrou_no_motor():
    """Guarda de fonte: base_z_abs e comparacoes com Z interno nunca mais
    podem ler `.Elevation` direto."""
    import io
    src = io.open(m.__file__, encoding="utf-8").read()
    for line in src.splitlines():
        if "base_z_abs = " in line and ".Elevation" in line:
            assert "_level_internal_elevation_ft" in line, line
