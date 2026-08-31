# -*- coding: utf-8 -*-
"""Ponte HEADLESS entre `input_real` e o WALL MODELING real do motor.

FASE A do benchmark (ver `nuvem/benchmark/README.md`):

    input_real
       -> wall_modeling_bridge.run_wall_modeling()
          -> extract/wall_modeling_snapshot.py
             -> wall_modeling_snapshot.json

PREMISSA ARQUITETURAL (confirmada antes desta sessao, NAO redesenhada aqui):
a Revit Wall nativa NAO e' entrada do solver - e' so' materializacao.
`Wall.Create` acontece bem depois, dentro de uma Transaction, sobre o
resultado deste modulo. O Wall Modeling de verdade - o que decide os EIXOS,
os NOS de encontro (L/T/X) e quais aberturas pertencem a qual parede - roda
ANTES de qualquer Transaction, sobre linhas de CAD (`Line`/`XYZ` puros) e
dicts de abertura. E' exatamente essa parte que este modulo reproduz, na
MESMA ordem de `core/wall_modeling.py` (main(), secao 3-4d):

    merge_collinear_fragments
       -> find_wall_pairs
          -> deduplicate_walls
             -> extend_wall_ends_to_junctions
                -> build_wall_graph
                   -> assign_openings_to_walls

Este modulo NAO:
  - abre nenhuma Transaction;
  - acessa `doc`;
  - cria nenhuma Wall do Revit;
  - alterar o solver de blocos (`solve_building_blocks_all_courses`) -
    isso continua em `solver_bridge.py`, etapa seguinte do pipeline;
  - reimplementa NENHUMA regra geometrica - toda funcao usada aqui e'
    importada do motor real (via `solver_bridge.engine()`, o mesmo modulo
    carregado com os dubles de `tests/revit_stubs.py` que `solver_bridge.py`
    ja usa desde a Etapa 1 do benchmark).

A ORDEM de `walls_to_create` e' preservada em toda etapa - nunca reordenada
nem deduplicada "para facilitar teste" (isso e' literalmente o trabalho de
`deduplicate_walls`, chamado na posicao exata que a producao chama).
"""

from . import solver_bridge

# Campos de `setup_frozen` sem os quais a geometria do Wall Modeling NAO
# pode ser reproduzida de forma determinista. `ask_setup` (interativo) os
# preenche na producao; aqui, a ausencia de qualquer um deles e' erro
# explicito - NUNCA um default silencioso que poderia mudar a geometria
# calculada (item 6 do pedido da Etapa 2A).
REQUIRED_SETUP_FIELDS = (
    "layer", "thicknesses_cm", "openings_mode", "wall_mode",
    "level", "base_z_cm", "wall_height_cm",
)


class WallModelingBridgeError(Exception):
    """Erro de contrato/geometria do bridge - `setup_frozen` incompleto,
    menos de 2 linhas no layer escolhido, ou nenhum par de paredes formado.
    Nunca e' engolido: um bridge que devolve resultado vazio silenciosamente
    daria a impressao de "planta sem parede nenhuma"."""

    def __init__(self, message, diagnostics=None):
        super(WallModelingBridgeError, self).__init__(message)
        self.diagnostics = diagnostics or {}


def _validate_setup_frozen(input_real):
    setup_frozen = input_real.get("setup_frozen")
    if not isinstance(setup_frozen, dict):
        raise WallModelingBridgeError(
            "input_real.setup_frozen ausente ou invalido - o benchmark nao "
            "pode assumir escolhas interativas do ask_setup (layer, "
            "espessuras, nivel, altura, openings_mode, wall_mode)."
        )
    missing = [key for key in REQUIRED_SETUP_FIELDS if setup_frozen.get(key) in (None, "")]
    # thicknesses_cm=[] tambem e' invalido (lista vazia nao passa no `in
    # (None, "")` acima porque [] != None) - checa a parte.
    if not setup_frozen.get("thicknesses_cm"):
        missing.append("thicknesses_cm") if "thicknesses_cm" not in missing else None
    if missing:
        raise WallModelingBridgeError(
            "setup_frozen incompleto - faltando: {0}. O benchmark nao "
            "inventa default para nenhum destes campos porque cada um "
            "afeta a geometria calculada.".format(", ".join(sorted(set(missing))))
        )
    return dict(setup_frozen)


def _ft(module, value_cm):
    return float(value_cm) / 100.0 * module.FEET_PER_METER


def _line_from_segment(module, segment):
    start = segment["start"]
    end = segment["end"]
    return module.Line.CreateBound(
        module.XYZ(_ft(module, start[0]), _ft(module, start[1]), 0.0),
        module.XYZ(_ft(module, end[0]), _ft(module, end[1]), 0.0),
    )


def _op_from_dict(module, opening):
    """`input_real["openings"][i]` (cm, JSON puro - mesmo schema de
    `capture_export.openings_to_json`) -> dict `op` no formato que
    `merge_collinear_fragments`/`find_wall_pairs`/`assign_openings_to_walls`
    esperam (pes, com `XYZ` de verdade em `center_xy`)."""
    center_cm = opening["center_cm"]
    op = {
        "element_id": opening.get("element_id"),
        "center_xy": module.XYZ(_ft(module, center_cm[0]), _ft(module, center_cm[1]), 0.0),
        "width_ft": _ft(module, opening["width_cm"]),
        "sill_z_abs": _ft(module, opening["sill_cm"]),
        "head_z_abs": _ft(module, opening["head_cm"]),
    }
    bbox_center_cm = opening.get("bbox_center_cm")
    if bbox_center_cm is not None:
        op["bbox_center_xy"] = module.XYZ(
            _ft(module, bbox_center_cm[0]), _ft(module, bbox_center_cm[1]), 0.0
        )
    return op


def _classify_unused_line(module, line, walls_to_create, thicknesses_ft, tolerance_ft):
    """Motivo pelo qual uma linha do layer NAO virou parede - reconstruido
    GEOMETRICAMENTE depois do fato (item 9 do pedido: nao mexe na
    assinatura de `find_wall_pairs` para devolver provenance).

    So' testa a linha contra as PAREDES JA FORMADAS (walls_to_create) -
    e' informacao suficiente para diferenciar "nunca teve par nenhum perto"
    de "tinha vizinha, mas fora da espessura escolhida"."""
    best_distance_ft = None
    for centerline, _thickness_ft, _locks in walls_to_create:
        if not module.are_lines_parallel(line, centerline):
            continue
        if not module.lines_overlap_enough(line, centerline):
            continue
        distance_ft = module.get_distance_between_parallel_lines(line, centerline)
        if best_distance_ft is None or distance_ft < best_distance_ft:
            best_distance_ft = distance_ft

    if best_distance_ft is None:
        return "sem_linha_paralela_com_sobreposicao", None
    matched = any(abs(best_distance_ft - t) <= tolerance_ft for t in thicknesses_ft)
    if matched:
        # Sobrou mesmo tendo distancia compativel - so' pode ter perdido a
        # rodada gulosa de find_wall_pairs para outro par melhor (maior
        # sobreposicao) usando a MESMA linha vizinha.
        return "perdeu_rodada_para_outro_par", round(best_distance_ft / module.FEET_PER_METER * 100.0, 2)
    return "distancia_fora_das_espessuras_escolhidas", round(best_distance_ft / module.FEET_PER_METER * 100.0, 2)


def run_wall_modeling(input_real):
    """Executa, headless, a mesma sequencia de `core/wall_modeling.py`
    (secao 3-4d de `main()`) sobre `input_real`. Devolve um dict com tudo
    que `extract/wall_modeling_snapshot.py` precisa - ver o cabecalho deste
    modulo para a lista.

    Levanta `WallModelingBridgeError` (nunca devolve resultado parcial
    silencioso) se `setup_frozen` estiver incompleto, se o layer escolhido
    tiver menos de 2 linhas, ou se nenhum par de paredes for formado."""
    setup_frozen = _validate_setup_frozen(input_real)
    module = solver_bridge.engine()

    layer = setup_frozen["layer"]
    segments = [s for s in (input_real.get("segments") or []) if s.get("layer") == layer]
    if len(segments) < 2:
        raise WallModelingBridgeError(
            "layer '{0}' tem {1} linha(s) em input_real.segments - "
            "impossivel formar pares (precisa de pelo menos 2).".format(
                layer, len(segments))
        )
    lines = [_line_from_segment(module, s) for s in segments]

    openings_raw = list(input_real.get("openings") or [])
    ops = [_op_from_dict(module, o) for o in openings_raw]

    thicknesses_ft = sorted(_ft(module, cm) for cm in setup_frozen["thicknesses_cm"])

    # ---- merge_collinear_fragments (religa fragmentos colineares) -------
    lines_to_process = module.merge_collinear_fragments(
        lines, module.COLLINEAR_MATCH_TOLERANCE_FT, module.MAX_JUNCTION_GAP_FT,
        ops, module.OPENING_GAP_PERP_TOLERANCE_FT, module.OPENING_GAP_WIDTH_SLACK_FT,
    )
    if len(lines_to_process) < 2:
        raise WallModelingBridgeError(
            "apos merge_collinear_fragments sobraram {0} linha(s) - "
            "impossivel formar pares.".format(len(lines_to_process))
        )

    # ---- find_wall_pairs (forma os pares linha+linha -> parede) ---------
    detection_tolerance_ft = module.compute_detection_tolerance_ft(thicknesses_ft)
    pairing_diagnostics = {
        "parallel_pairs": 0, "min_dist_ft": None, "max_dist_ft": None,
        "offset_suspect_count": 0, "offset_suspect_max_ft": 0.0,
        "cap_clipped_count": 0,
    }
    walls_to_create, unused_lines = module.find_wall_pairs(
        lines_to_process, thicknesses_ft, detection_tolerance_ft,
        lines_to_process, ops, pairing_diagnostics,
    )
    if not walls_to_create:
        raise WallModelingBridgeError(
            "nenhum par valido de linhas encontrado para as espessuras "
            "{0}.".format(setup_frozen["thicknesses_cm"]),
            diagnostics={"wall_pairing": pairing_diagnostics},
        )

    # ---- deduplicate_walls (remove paredes duplicadas/sobrepostas) ------
    walls_to_create, duplicates_removed_count = module.deduplicate_walls(walls_to_create)

    # Geometria ANTES da extensao de pontas - preservada porque
    # `wall_modeling_snapshot.py` precisa gravar isso separado (item 3/4 do
    # pedido) e porque e' o unico ponto do pipeline em que a parede ainda
    # tem exatamente o comprimento que as duas linhas do CAD definiram.
    walls_before_extension = list(walls_to_create)

    # ---- extend_wall_ends_to_junctions (fecha encontros T/L) -------------
    walls_to_create, junction_map = module.extend_wall_ends_to_junctions(
        walls_to_create, module.JUNCTION_FACE_SEARCH_FT
    )

    # ---- build_wall_graph (classifica cada no' L/T/X/FREE_END) ----------
    wall_graph_nodes, wall_end_to_node = module.build_wall_graph(walls_to_create, junction_map)

    # Rede de seguranca identica a producao - so' CONTA, nao remove de novo.
    _, residual_duplicates_count = module.deduplicate_walls(walls_to_create)

    # ---- assign_openings_to_walls (abertura -> NO MAXIMO uma parede) ----
    opening_diagnostics = {
        "clamped_opening_count": 0,
        "opening_off_center_count": 0,
        "opening_center_gap_max_ft": 0.0,
        "unassigned_openings": [],
    }
    openings_per_wall = module.assign_openings_to_walls(walls_to_create, ops, opening_diagnostics)

    unused_lines_classified = []
    for line in unused_lines:
        reason, measured_thickness_cm = _classify_unused_line(
            module, line, walls_to_create, thicknesses_ft, detection_tolerance_ft
        )
        p0, p1 = line.GetEndPoint(0), line.GetEndPoint(1)
        unused_lines_classified.append({
            "start_cm": [p0.X / module.FEET_PER_METER * 100.0, p0.Y / module.FEET_PER_METER * 100.0],
            "end_cm": [p1.X / module.FEET_PER_METER * 100.0, p1.Y / module.FEET_PER_METER * 100.0],
            "reason": reason,
            "measured_thickness_cm": measured_thickness_cm,
        })

    return {
        "setup_frozen": setup_frozen,
        "module": module,
        "walls_to_create": walls_to_create,
        "walls_before_extension": walls_before_extension,
        "wall_graph_nodes": wall_graph_nodes,
        "wall_end_to_node": wall_end_to_node,
        "openings_per_wall": openings_per_wall,
        "unused_lines": unused_lines_classified,
        "diagnostics": {
            "wall_pairing": pairing_diagnostics,
            "openings": opening_diagnostics,
            "duplicates_removed_count": duplicates_removed_count,
            "residual_duplicates_count": residual_duplicates_count,
            "lines_in_layer": len(segments),
            "lines_after_merge": len(lines_to_process),
            "walls_created": len(walls_to_create),
            "unused_lines_count": len(unused_lines_classified),
        },
    }
