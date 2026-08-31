# -*- coding: utf-8 -*-
"""ABERTURAS - vao livre, jambas, verga, contraverga e solidez fora do vao.

A regra mais dura do projeto esta' aqui: **porta com peitoril 0 nunca
pode receber bloco dentro do vao** (secao 3, zona de exclusao absoluta).
Nao ha' tolerancia "por pouco": qualquer sobreposicao acima do ruido de
arredondamento (`OVERLAP_TOLERANCE_CM`) e' erro critico.

Os achados, do mais grave ao menos:

* `OPENING_BLOCK_INSIDE_DOOR` / `OPENING_BLOCK_INSIDE_WINDOW` - peca
  inteiramente (ou quase) dentro do vao, na faixa vertical em que ele
  esta' ativo.
* `OPENING_BLOCK_CROSSES_JAMB` - peca que entra parcialmente no vao,
  atravessando a jamba. Separado do anterior de proposito: a causa e'
  outra (fechamento do pilarete, nao vao ignorado) e a correcao tambem.
* `OPENING_SOLID_BELOW_SILL_MISSING` - a fiada abaixo do peitoril de uma
  janela ficou vazia. E' o erro inverso, e igualmente real: janela nao
  interrompe a fiada de baixo (secao 4).
* `OPENING_MISSING_LINTEL` / `OPENING_MISSING_COUNTER_LINTEL` - nivel 2.
  Sao PREFERENCIA porque o projeto usa dois sistemas legitimos (secao
  10.1: verga/contraverga dedicada, ou canaleta) e nem toda abertura em
  todo projeto recebe os dois.
"""

from .. import analysis
from .. import model
from . import base

# Fracao do comprimento da peca que precisa cair dentro do vao para ela
# contar como "dentro" em vez de "atravessando a jamba".
INSIDE_RATIO = 0.9

# Fiadas acima da verga em que se procura a peca de verga/canaleta.
LINTEL_SEARCH_ROWS = 1

LINTEL_ROLES = (model.ROLE_LINTEL, model.ROLE_CHANNEL_BLOCK)
COUNTER_LINTEL_ROLES = (model.ROLE_COUNTER_LINTEL, model.ROLE_CHANNEL_BLOCK)


def _row_covering_elevation(wall, z_cm, block_height_cm):
    for row in model.rows_sorted(wall):
        if row["elevation_cm"] <= z_cm + 1e-6 < row["elevation_cm"] + block_height_cm:
            return row
    return None


def validate_wall(wall, block_height_cm):
    findings = []
    openings = wall.get("openings") or []
    if not openings:
        return findings

    for row in model.rows_sorted(wall):
        active = analysis.active_opening_intervals(wall, row, block_height_cm)
        for block in row.get("blocks") or []:
            extent = (block["t_start_cm"], block["t_end_cm"])
            length = max(1e-6, extent[1] - extent[0])
            for o_start, o_end, opening in active:
                overlap = analysis.interval_overlap_cm(extent, (o_start, o_end))
                if overlap <= model.OVERLAP_TOLERANCE_CM:
                    continue
                # Verga/contraverga/canaleta APOIAM-SE sobre o vao de
                # proposito (secao 10.3: o apoio passa da largura do vao)
                # - nao sao invasao.
                if block.get("role") in (model.ROLE_LINTEL, model.ROLE_COUNTER_LINTEL,
                                         model.ROLE_CHANNEL_BLOCK):
                    continue
                is_door = opening.get("kind") == model.OPENING_DOOR
                if overlap >= INSIDE_RATIO * length:
                    code = ("OPENING_BLOCK_INSIDE_DOOR" if is_door
                            else "OPENING_BLOCK_INSIDE_WINDOW")
                    detail = (
                        "bloco {0} ({1}) dentro do vao de {2} em "
                        "t={3:.1f}..{4:.1f}cm, fiada {5}".format(
                            block.get("id"), block.get("code"),
                            opening.get("id") or opening.get("kind"),
                            o_start, o_end, row["row"])
                    )
                else:
                    code = "OPENING_BLOCK_CROSSES_JAMB"
                    detail = (
                        "bloco {0} ({1}) invade {2:.1f}cm do vao de {3} "
                        "(fiada {4})".format(
                            block.get("id"), block.get("code"), overlap,
                            opening.get("id") or opening.get("kind"), row["row"])
                    )
                findings.append(base.finding(
                    code,
                    wall=wall["id"],
                    detail=detail,
                    row=row["row"],
                    blocks=[block.get("id")],
                    opening=opening.get("id"),
                    opening_kind=opening.get("kind"),
                    overlap_cm=round(overlap, 3),
                    block_t_cm=[round(extent[0], 2), round(extent[1], 2)],
                    opening_t_cm=[round(o_start, 2), round(o_end, 2)],
                ))

    # ---- fiada abaixo do peitoril tem que ser SOLIDA -------------------
    for opening in openings:
        if opening.get("kind") != model.OPENING_WINDOW:
            continue
        if opening["sill_cm"] <= wall.get("base_z_cm", 0.0) + 1e-6:
            continue
        for row in model.rows_sorted(wall):
            if analysis.opening_active_in_row(opening, row["elevation_cm"], block_height_cm):
                continue
            if row["elevation_cm"] >= opening["sill_cm"]:
                continue  # so' interessa o que esta' ABAIXO do peitoril
            covered = analysis.merge_intervals(
                [(b["t_start_cm"], b["t_end_cm"]) for b in row.get("blocks") or []],
                tolerance_cm=analysis.BOND_MAX_ADJACENT_GAP_CM,
            )
            span = (opening["t_start_cm"], opening["t_end_cm"])
            missing = analysis.subtract_intervals(span, covered)
            uncovered = sum(end - start for start, end in missing)
            if uncovered > analysis.PIER_MODULE_CM:
                findings.append(base.finding(
                    "OPENING_SOLID_BELOW_SILL_MISSING",
                    wall=wall["id"],
                    detail=(
                        "fiada {0} (elev {1:.0f}cm) esta' abaixo do peitoril de "
                        "{2} (peitoril {3:.0f}cm) e ficou {4:.1f}cm sem "
                        "bloco".format(row["row"], row["elevation_cm"],
                                       opening.get("id") or "janela",
                                       opening["sill_cm"], uncovered)
                    ),
                    row=row["row"],
                    opening=opening.get("id"),
                    uncovered_cm=round(uncovered, 2),
                    gaps_t_cm=[[round(a, 2), round(b, 2)] for a, b in missing],
                ))

    # ---- verga / contraverga (nivel 2) ---------------------------------
    for opening in openings:
        head_row = _row_covering_elevation(wall, opening["head_cm"], block_height_cm)
        rows_by_index = analysis.wall_rows_by_index(wall)
        if head_row is not None:
            candidates = []
            for offset in range(0, LINTEL_SEARCH_ROWS + 1):
                row = rows_by_index.get(head_row["row"] + offset)
                if row is None:
                    continue
                for block in row.get("blocks") or []:
                    if block.get("role") not in LINTEL_ROLES:
                        continue
                    if analysis.interval_overlap_cm(
                            (block["t_start_cm"], block["t_end_cm"]),
                            (opening["t_start_cm"], opening["t_end_cm"])) > 0:
                        candidates.append(block)
            if not candidates:
                findings.append(base.finding(
                    "OPENING_MISSING_LINTEL",
                    wall=wall["id"],
                    detail=(
                        "sem verga/canaleta sobre {0} (verga em {1:.0f}cm, "
                        "fiada {2})".format(opening.get("id") or "abertura",
                                            opening["head_cm"], head_row["row"])
                    ),
                    opening=opening.get("id"),
                    row=head_row["row"],
                ))
        if opening.get("kind") == model.OPENING_WINDOW:
            sill_row = _row_covering_elevation(
                wall, opening["sill_cm"] - block_height_cm, block_height_cm)
            if sill_row is not None:
                has_counter = any(
                    block.get("role") in COUNTER_LINTEL_ROLES
                    and analysis.interval_overlap_cm(
                        (block["t_start_cm"], block["t_end_cm"]),
                        (opening["t_start_cm"], opening["t_end_cm"])) > 0
                    for block in sill_row.get("blocks") or []
                )
                if not has_counter:
                    findings.append(base.finding(
                        "OPENING_MISSING_COUNTER_LINTEL",
                        wall=wall["id"],
                        detail=(
                            "janela {0} sem contraverga na fiada {1}".format(
                                opening.get("id") or "?", sill_row["row"])
                        ),
                        opening=opening.get("id"),
                        row=sill_row["row"],
                    ))
    return findings


def validate(project, context=None):
    block_height = analysis.block_height_of(project)
    findings = []
    for wall in project.get("walls") or []:
        findings.extend(validate_wall(wall, block_height))
    return findings


base.register("openings", validate)
