# -*- coding: utf-8 -*-
"""Laboratorio da FINALIZACAO do CR-BLOCK-DETERMINISM (item 11 da missao:
"nao assuma a causa apenas pelo relatorio - reproduza voce mesmo").

Reusa, SEM duplicar, a bateria independente da CONTA 2
(`../diagnostics_block_determinism_audit/`): as mesmas 24 variantes, o
mesmo solver real, as mesmas metricas downstream. Acrescenta as DUAS
correcoes de METRICA que a propria cross-audit identificou como
necessarias (docs/BLOCK_DETERMINISM_CROSS_AUDIT.md, secoes
"wall_end_to_node" e item 40 da missao):

  1. `wall_end_to_node` CANONICO - identifica a ponta pelo endpoint `lo`/
     `hi` da parede, nunca pelo `end_index` cru (0/1), que TROCA de valor
     por definicao quando o eixo e' desenhado ao contrario;
  2. fingerprint FISICO de peca - identifica a peca pelas CELULAS dela em
     coordenadas de mundo, nunca por `origin_world`+`rotation_deg`. Uma
     peca simetrica (B39/B19/B54/C09/C04) colocada com direcao `d` ou
     `-d` no MESMO lugar e' A MESMA PECA fisica, mas tem `rotation_deg`
     diferente em 180 graus; uma peca ASSIMETRICA (B34) nao e' - e as
     celulas distinguem os dois casos sozinhas, sem lista fixa de codigo.

NENHUM arquivo de producao e' alterado por nada daqui; nenhum `out_*.json`
da auditoria da CONTA 2 e' sobrescrito.
"""

import os
import sys
import json
import math
import hashlib

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT = os.path.join(os.path.dirname(_HERE), "diagnostics_block_determinism_audit")
for _path in (_AUDIT, os.path.join(_AUDIT, "cross_audit")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import lib_det as L        # noqa: E402
import variants as V       # noqa: E402
import lib_cross as C      # noqa: E402

PRIMARY_PROJECT_ID = L.PRIMARY_PROJECT_ID
ROUND_CM = 1   # 1 casa decimal de cm = 1mm - bem abaixo de qualquer decisao


def _hash_rows(rows):
    blob = json.dumps(rows, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


# ---------------------------------------------------------------------
# Fingerprint FISICO de peca (item 40/41 da missao)
# ---------------------------------------------------------------------

def piece_physical_key(walls_to_create, course_index, candidate):
    """Identidade FISICA de uma peca: parede geometrica, fiada, codigo,
    CENTRO e o conjunto de CELULAS em coordenadas de mundo.

    As celulas sao o que resolve o item 41 (blocos assimetricos): num B34
    elas nao sao simetricas em relacao ao centro, entao a peca virada 180
    graus produz um conjunto DIFERENTE - continua sendo detectada como
    diferenca fisica de verdade. Num B39/B54/B19 elas sao simetricas,
    entao a mesma peca fisica gera a MESMA chave nos dois sentidos de
    representacao - deixa de contar como divergencia artificial."""
    wall_idx = candidate.get("wall_idx")
    wall_key = L.wall_geom_key(walls_to_create, wall_idx) if wall_idx is not None else None
    center = L.xyz_to_cm(candidate["origin_world"])
    cells = []
    for cell in candidate.get("cells_world") or []:
        cx_cm, cy_cm = L.xyz_to_cm(cell["point"])
        size_x, size_y = cell["size_local"]
        cells.append((
            round(cx_cm, ROUND_CM) + 0.0,
            round(cy_cm, ROUND_CM) + 0.0,
            round(abs(size_x) * L.FT_TO_CM, ROUND_CM),
            round(abs(size_y) * L.FT_TO_CM, ROUND_CM),
        ))
    return (
        wall_key,
        course_index,
        candidate["logical_code"],
        round(center[0], ROUND_CM) + 0.0,
        round(center[1], ROUND_CM) + 0.0,
        tuple(sorted(cells)),
    )


def layer_physical_block_layouts(run_data):
    walls = run_data["walls_to_create"]
    rows = sorted(
        piece_physical_key(walls, course_index, candidate)
        for course_index, candidate in L.physical_course_candidates(run_data["solve_result"])
    )
    return _hash_rows(rows), rows


def _physical_reason_rows(run_data, keep):
    walls = run_data["walls_to_create"]
    rows = []
    for course_index, candidate in L.physical_course_candidates(run_data["solve_result"]):
        reason = candidate.get("placement_reason") or ""
        if not keep(reason):
            continue
        rows.append(piece_physical_key(walls, course_index, candidate) + (reason,))
    rows.sort(key=lambda r: json.dumps(r, default=str))
    return rows


def layer_physical_standard_fill(run_data):
    rows = _physical_reason_rows(run_data, lambda r: r == "STANDARD_FILL")
    return _hash_rows(rows), rows


def layer_physical_opening_repair_fill(run_data):
    rows = _physical_reason_rows(run_data, lambda r: r == "OPENING_REPAIR_FILL")
    return _hash_rows(rows), rows


def layer_physical_ties(run_data):
    """Pecas de amarracao L/T/X (tudo que nao e' preenchimento comum nem
    reparo de abertura)."""
    rows = _physical_reason_rows(
        run_data, lambda r: r not in ("STANDARD_FILL", "OPENING_REPAIR_FILL"))
    return _hash_rows(rows), rows


def layer_canonical_wall_end_to_node(run_data):
    return C.canonical_wall_end_to_node(run_data)


FINAL_LAYER_FUNCS = (
    ("input_wall_geometry", L.layer_input_wall_geometry),
    ("wall_graph_node_positions", L.layer_node_positions),
    ("node_types", L.layer_node_types),
    ("node_arms", L.layer_node_arms),
    ("wall_end_to_node_canonical", layer_canonical_wall_end_to_node),
    ("midspan_crossings", L.layer_midspan_crossings),
    ("physical_ties", layer_physical_ties),
    ("physical_standard_fill", layer_physical_standard_fill),
    ("physical_opening_repair_fill", layer_physical_opening_repair_fill),
    ("physical_block_layouts", layer_physical_block_layouts),
)


def final_layered_fingerprints(run_data):
    out = {}
    rows_by_layer = {}
    for name, func in FINAL_LAYER_FUNCS:
        fp, rows = func(run_data)
        out[name] = {"fingerprint": fp, "n_rows": len(rows)}
        rows_by_layer[name] = rows
    blob = "|".join(out[name]["fingerprint"] for name, _ in FINAL_LAYER_FUNCS)
    out["global_result"] = {
        "fingerprint": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
        "n_rows": sum(v["n_rows"] for v in out.values()),
    }
    return out, rows_by_layer


def first_divergent_layer(baseline_layers, other_layers):
    for name, _func in FINAL_LAYER_FUNCS:
        if baseline_layers[name]["fingerprint"] != other_layers[name]["fingerprint"]:
            return name
    return None


def reason_counts(run_data):
    counts = {}
    for _ci, cand in L.physical_course_candidates(run_data["solve_result"]):
        reason = cand.get("placement_reason") or ""
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def downstream_metrics(run_data):
    metrics = L.downstream_metrics(run_data)
    metrics["by_placement_reason"] = reason_counts(run_data)
    codes = metrics.get("coverage_pieces_by_code") or {}
    for code in ("B39", "B34", "B54", "B19", "C09", "C04"):
        metrics[code] = codes.get(code, 0)
    return metrics


def out_path(*parts):
    return os.path.join(_HERE, *parts)


write_json = L.write_json
load_input = L.load_input
run_solver = L.run_solver
