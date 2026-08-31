# -*- coding: utf-8 -*-
"""Ponte entre o `input.json` do benchmark e o SOLVER REAL.

E' o unico modulo do pacote que importa o motor. Ele existe para que o
benchmark rode o solver DE VERDADE (`solve_building_blocks_all_courses`,
a mesma funcao que o botao "Lancar Blocos" usa), e nao uma reimplementacao
- medir uma copia do solver nao mediria nada.

O motor precisa da API do Revit; fora do Revit ele roda com os dubles de
`tests/revit_stubs.py`, que ja' fazem geometria XYZ/Line de verdade (ver
`tests/README.md`). O mesmo caminho que `tests/solver_bench.py` usa desde
2026-08-27 - aqui so' generalizamos a planta: em vez de uma grade
sintetica, a planta vem do `input.json`.
"""

import os
import sys

_ENGINE = None

# Os SEIS codigos logicos que o solver de hoje conhece pelo nome - ver
# `BLOCK_FAMILY_CATALOG_DEFINITIONS` e `COMMON_FILL_BLOCK_CODES` /
# `MID_WALL_BLOCK_CODE` / `CORNER_SINGLE_ELEMENT_CODES` em
# core/engine/wall_stepper.py.
SOLVER_KNOWN_CODES = ("B39", "B34", "B54", "B19", "C09", "C04")


def _find_tests_dir():
    """Acha `tests/` subindo a arvore - mesma estrategia (e mesmo motivo)
    de `tests/load_script.py`: este repositorio existe em dois layouts,
    como pasta de extensao do pyRevit e como repo independente."""
    here = os.path.dirname(os.path.abspath(__file__))
    directory = here
    tried = []
    for _level in range(6):
        candidate = os.path.join(directory, "tests", "load_script.py")
        tried.append(candidate)
        if os.path.isfile(candidate):
            return os.path.dirname(candidate)
        nested = os.path.join(directory, "MinhaAba.tab", "MeuPainel.panel",
                              "MeuBotao.pushbutton", "tests", "load_script.py")
        tried.append(nested)
        if os.path.isfile(nested):
            return os.path.dirname(nested)
        parent = os.path.dirname(directory)
        if parent == directory:
            break
        directory = parent
    raise RuntimeError(
        "nao achei tests/load_script.py (necessario para carregar o motor "
        "fora do Revit). Procurei em: " + " | ".join(tried)
    )


def engine():
    """O modulo `core/wall_modeling.py` carregado com os dubles do Revit.
    Carregado uma vez so' - o motor tem estado de modulo (caches de
    geometria) e recarrega-lo no meio de uma rodada mudaria o resultado."""
    global _ENGINE
    if _ENGINE is None:
        tests_dir = _find_tests_dir()
        if tests_dir not in sys.path:
            sys.path.insert(0, tests_dir)
        import load_script  # noqa: E402  (depende do sys.path acima)
        _ENGINE = load_script.load()
    return _ENGINE


def _ft(value_cm):
    return float(value_cm) / 100.0 * engine().FEET_PER_METER


def plan_from_input(input_project):
    """`input.json` -> `(nodes, walls_to_create, end_to_node,
    openings_per_wall)`, a tupla que o solver consome.

    A ORDEM das paredes e' preservada: `walls_to_create[i]` corresponde a
    `input_project["walls"][i]`. Sem isso, `openings_per_wall` (que e'
    indexado por posicao) apontaria para a parede errada."""
    module = engine()
    walls_input = list(input_project.get("walls") or [])

    walls_to_create = []
    for wall in walls_input:
        line = module.Line.CreateBound(
            module.XYZ(_ft(wall["start_cm"][0]), _ft(wall["start_cm"][1]), 0.0),
            module.XYZ(_ft(wall["end_cm"][0]), _ft(wall["end_cm"][1]), 0.0),
        )
        walls_to_create.append((line, _ft(wall["thickness_cm"]), (False, False)))

    settings = input_project.get("settings") or {}
    if settings.get("walls_already_extended"):
        # Ja' vieram esticadas ate' os encontros por uma extracao anterior
        # - esticar de novo empurraria as pontas mais uma espessura de
        # parede a cada rodada (erro que so' apareceria como colisao
        # varias execucoes depois).
        junction_map = {}
        walls_to_create, junction_map = module.extend_wall_ends_to_junctions(
            walls_to_create, 0.0)
    else:
        walls_to_create, junction_map = module.extend_wall_ends_to_junctions(
            walls_to_create, module.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = module.build_wall_graph(walls_to_create, junction_map)

    openings_per_wall = []
    for wall in walls_input:
        entries = []
        for opening in wall.get("openings") or []:
            entries.append((
                _ft(opening["t_start_cm"]), _ft(opening["t_end_cm"]),
                _ft(opening["sill_cm"]), _ft(opening["head_cm"]),
            ))
        openings_per_wall.append(entries)

    return nodes, walls_to_create, end_to_node, openings_per_wall


def solver_supported_catalog(input_project):
    """O subconjunto do catalogo que o SOLVER de hoje sabe usar, e o que
    ficou de fora.

    Motivo, medido no projeto real TORRE EASY-LO-R00: o catalogo extraido
    de um projeto entregue tem 33 tipos, com alturas de 9, 19 e 29cm
    (canaleta J, blocos CORTADOS de meia altura, vergas). O solver assume
    UMA altura de fiada e recusa o catalogo inteiro com
    "os blocos usados tem alturas diferentes no catalogo (9.0, 19.0,
    29.0)" - resultado: zero bloco gerado, e o benchmark mediria "96
    paredes nao moduladas" quando o que houve foi o solver receber pecas
    que ele nao implementa.

    Entao o benchmark entrega ao solver o catalogo DELE (a altura
    dominante) e registra o resto como limitacao conhecida. As pecas
    excluidas continuam no gabarito: o comparador as mostra como
    diferenca (nivel 2), que e' o que elas sao - escopo pendente do
    solver, nao erro de modulacao.
    """
    catalog = input_project.get("catalog") or {}

    # 1) O solver so' conhece SEIS codigos logicos (o catalogo fixo de
    #    `BLOCK_FAMILY_CATALOG_DEFINITIONS`, referenciados por nome em
    #    `COMMON_FILL_BLOCK_CODES`, `MID_WALL_BLOCK_CODE`,
    #    `CORNER_SINGLE_ELEMENT_CODES`, `solve_l_corner`/`solve_t_intersection`).
    #    Deixar uma CANALETA entrar no catalogo dele nao daria erro - daria
    #    coisa pior: canaleta usada como enchimento comum, porque para o
    #    solver ela e' so' uma peca de 39x19x14 como outra qualquer.
    known = [code for code in catalog if code in SOLVER_KNOWN_CODES]
    if known:
        kept = dict((code, catalog[code]) for code in known)
        dropped = [
            {"code": code, "height_cm": entry.get("height_cm"),
             "reason": "peca fora do catalogo fixo de 6 codigos do solver"}
            for code, entry in sorted(catalog.items())
            if code not in SOLVER_KNOWN_CODES
        ]
        return kept, dropped

    # 2) Catalogo que nao usa os codigos canonicos (planta sintetica de
    #    teste, projeto de outro escritorio): cai no criterio de ALTURA.
    heights = {}
    for entry in catalog.values():
        height = entry.get("height_cm")
        if not height:
            continue
        key = round(float(height), 1)
        heights[key] = heights.get(key, 0) + (entry.get("count") or 1)
    if not heights:
        return dict(catalog), []
    dominant = max(heights.items(), key=lambda kv: kv[1])[0]

    kept, dropped = {}, []
    for code, entry in catalog.items():
        height = entry.get("height_cm")
        if height is None or abs(float(height) - dominant) > 0.5:
            dropped.append({"code": code, "height_cm": height,
                            "reason": "altura fora da fiada de {0}cm".format(dominant)})
            continue
        kept[code] = entry
    return kept, dropped


def catalog_from_input(input_project):
    """Catalogo no formato que o solver espera, a partir do `input.json`.

    `cells_local` (as celulas/furos de cada peca) NAO cabem no input.json
    de um projeto extraido de um .rvt de terceiro - a leitura de
    `EdgeLoops` falha em varios ambientes (ver PADRAO_MODULACAO.md). Quando
    faltarem, sao reconstruidas simetricamente a partir do comprimento, que
    e' o suficiente para o solver posicionar as pecas; o que se perde e' o
    ajuste fino de alinhamento de celula das pecas assimetricas (B34/B54).
    Isso fica REGISTRADO em `metadata.cells_reconstructed` para o relatorio
    nao dar a entender que a geometria veio medida."""
    module = engine()
    catalog = {}
    reconstructed = []
    source_catalog, dropped = solver_supported_catalog(input_project)
    for code, entry in source_catalog.items():
        length_cm = float(entry.get("length_cm") or 0.0)
        cells = entry.get("cells_local_cm")
        if cells:
            cells_local = [
                {"center_local": (_ft(cell["center_cm"][0]), _ft(cell["center_cm"][1])),
                 "size_local": (_ft(cell["size_cm"][0]), _ft(cell["size_cm"][1]))}
                for cell in cells
            ]
        else:
            cells_local = _default_cells_local(module, code, length_cm,
                                               float(entry.get("width_cm") or 14.0))
            # Compensador nao TEM celula (lista vazia e' o valor correto,
            # nao uma reconstrucao) - so' conta como reconstruido o que de
            # fato teve celula inventada.
            if cells_local:
                reconstructed.append(code)
        catalog[code] = {
            "symbol": None,
            "logical_code": code,
            "length_cm": length_cm,
            "height_cm": float(entry.get("height_cm") or 19.0),
            "width_cm": float(entry.get("width_cm") or 14.0),
            "cells_local": cells_local,
            "is_special_bond": bool(entry.get("is_special_bond")),
            "is_compensator": bool(entry.get("is_compensator")),
            "source_instance_id": None,
        }
    return catalog, reconstructed, dropped


def _default_cells_local(module, code, length_cm, width_cm):
    """Celulas simetricas de reserva (ver `catalog_from_input`). Uma celula
    por 'modulo' de 19,5cm, centradas - reproduz a topologia real (B39 tem
    2, B54 tem 3, B19 tem 1, compensadores nao tem)."""
    if length_cm < 15.0:
        return []
    count = max(1, int(round(length_cm / 19.5)))
    cell_size = length_cm / count * 0.8
    cells = []
    for index in range(count):
        center = (index + 0.5) * (length_cm / count) - length_cm / 2.0
        cells.append({
            "center_local": (_ft(center), 0.0),
            "size_local": (_ft(cell_size), _ft(width_cm * 0.55)),
        })
    return cells


def run_solver(input_project, variants_per_course=None):
    """Roda o solver real sobre o `input.json` e devolve
    `(solve_result, walls_to_create, nodes, openings_per_wall, catalog,
    base_z_ft, num_courses, notes)`."""
    module = engine()
    nodes, walls_to_create, end_to_node, openings_per_wall = plan_from_input(input_project)
    catalog, reconstructed_cells, dropped_codes = catalog_from_input(input_project)

    settings = input_project.get("settings") or {}
    base_z_ft = _ft(settings.get("base_z_cm") or 0.0)
    num_courses = int(settings.get("num_courses")
                      or settings.get("expected_rows") or 15)
    if variants_per_course is None:
        variants_per_course = module.PIER_LAYOUT_VARIANTS_PER_COURSE

    solve_result = module.solve_building_blocks_all_courses(
        nodes, walls_to_create, end_to_node, openings_per_wall, catalog,
        base_z_ft, num_courses, variants_per_course=variants_per_course,
    )
    notes = {
        "cells_reconstructed": sorted(reconstructed_cells),
        "catalog_codes_used": sorted(catalog),
        # Pecas do projeto real que o solver de hoje NAO sabe usar - ver
        # `solver_supported_catalog`. Escopo pendente, nao erro.
        "catalog_codes_dropped": dropped_codes,
    }
    return (solve_result, walls_to_create, nodes, openings_per_wall, catalog,
            base_z_ft, num_courses, notes)
