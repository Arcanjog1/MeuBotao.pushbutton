# -*- coding: utf-8 -*-
"""Plantas SINTETICAS - `input.json` sem precisar de Revit.

Servem a tres coisas, nenhuma delas "substituir projeto real":

1. Testar a propria infraestrutura do benchmark (validadores, comparador,
   score) com geometria conhecida e controlada.
2. Dar um caso de regressao barato e reproduzivel para o solver, que roda
   em segundos e nao depende de nenhum .rvt estar na maquina.
3. Servir de piloto enquanto um projeto real ainda nao foi extraido.

A grade e' a MESMA de `tests/solver_bench.py` (mesmo gerador, mesmos
tamanhos, mesma alternancia porta/janela/nenhuma), de proposito: o
fingerprint de la' e o benchmark daqui passam a falar do mesmo cenario.
Um projeto sintetico SEMPRE marca `metadata.synthetic = true`, para
nenhum relatorio dar a entender que aquilo foi medido num projeto
entregue.
"""

from .. import model

# Mesmo catalogo de `tests/solver_bench.py` e `tests/test_script.py` - as
# medidas de celula sao as da familia real do projeto.
SYNTHETIC_CATALOG_CM = {
    "B39": {"length_cm": 39.0, "cells": [(-9.9, 15.7), (9.9, 15.8)]},
    "B34": {"length_cm": 34.0, "cells": [(-10.2, 10.7), (7.4, 15.7)]},
    "B54": {"length_cm": 54.0, "cells": [(-19.5, 15.8), (0.0, 12.5), (19.5, 15.8)]},
    "B19": {"length_cm": 19.0, "cells": [(0.0, 15.7)]},
    "C09": {"length_cm": 9.0, "cells": []},
    "C04": {"length_cm": 4.0, "cells": []},
}


def build_catalog():
    catalog = {}
    for code, entry in SYNTHETIC_CATALOG_CM.items():
        catalog[code] = {
            "code": code,
            "length_cm": entry["length_cm"],
            "height_cm": 19.0,
            "width_cm": 14.0,
            "is_special_bond": code in ("B34", "B54"),
            "is_compensator": code in ("C09", "C04"),
            "cells_local_cm": [
                {"center_cm": [center, 0.0], "size_cm": [size, 8.0]}
                for center, size in entry["cells"]
            ],
        }
    return catalog


def grid_segments(nx, ny, step_cm=350.0):
    """Eixos de uma planta em grade `nx` x `ny` comodos - identico a
    `build_grid_lines` de tests/solver_bench.py."""
    segments = []
    for j in range(ny + 1):
        for i in range(nx):
            segments.append(((i * step_cm, j * step_cm),
                             ((i + 1) * step_cm, j * step_cm)))
    for i in range(nx + 1):
        for j in range(ny):
            segments.append(((i * step_cm, j * step_cm),
                             (i * step_cm, (j + 1) * step_cm)))
    return segments


def build_input(project_id, nx=2, ny=2, step_cm=350.0, thickness_cm=14.0,
                num_courses=15, opening_every=3, base_z_cm=0.0):
    """`input.json` de uma grade sintetica. Aberturas alternam porta /
    janela / nenhuma - sem esse mix o solver rodaria uma banda vertical
    so' e o benchmark nao exercitaria a regra da secao 4."""
    walls = []
    for index, (start, end) in enumerate(grid_segments(nx, ny, step_cm)):
        openings = []
        if index % opening_every == 0:
            openings.append(model.make_opening(
                model.OPENING_DOOR, 120.0, 200.0, 0.0, 210.0,
                confidence="synthetic"))
        elif index % opening_every == 1:
            openings.append(model.make_opening(
                model.OPENING_WINDOW, 100.0, 220.0, 90.0, 200.0,
                confidence="synthetic"))
        walls.append(model.make_wall(
            "W{0:03d}".format(index + 1), start, end, thickness_cm,
            base_z_cm=base_z_cm, height_cm=num_courses * 20.0,
            openings=openings, junctions=[], rows=[],
        ))

    project = model.make_project(
        project_id, "input", walls=walls,
        settings={
            "base_z_cm": base_z_cm,
            "course_step_cm": 20.0,
            "block_height_cm": 19.0,
            "num_courses": num_courses,
            "expected_rows": num_courses,
            "wall_thickness_cm": thickness_cm,
            # Estes eixos sao os BRUTOS (nao esticados ate' os encontros) -
            # ver `solver_bridge.plan_from_input`.
            "walls_already_extended": False,
        },
        catalog=build_catalog(),
        metadata={
            "synthetic": True,
            "generator": "benchmark/extract/synthetic.py",
            "grid": [nx, ny],
            "step_cm": step_cm,
        },
    )
    return model.assign_ids(project)
