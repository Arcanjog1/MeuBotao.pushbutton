# -*- coding: utf-8 -*-
"""POSICIONAMENTO - sobreposicao, peca fora da parede, eixo e orientacao.

Geometria pura, sem nenhuma regra de estilo: ou a peca cabe onde esta',
ou nao cabe.

* `POSITION_OVERLAP` - dois blocos da MESMA fiada ocupando o mesmo
  intervalo no eixo. E' a regra 18.7 ("proibido bloco dentro do volume de
  outro") medida em 1D, que e' onde ela de fato acontece: pecas da mesma
  fiada compartilham a mesma cota e a mesma espessura, entao sobrepor no
  eixo e' sobrepor no volume.
* `POSITION_OUTSIDE_WALL` - peca alem da ponta. Ligada a' regra #1 do
  ajuste geometrico (nunca aumentar a parede).
* `POSITION_OFF_AXIS` - o centro da peca esta' longe do eixo da parede.
  So' aparece na extracao do Revit (o solver, por construcao, coloca tudo
  no eixo) - e e' justamente por isso que vale a pena medir: e' o sinal de
  que a reconstrucao de eixos ou a modelagem humana tem algo fora do
  lugar.
* `POSITION_BAD_ORIENTATION` - a rotacao da peca nao e' paralela nem
  perpendicular ao eixo da parede.
* `POSITION_LENGTH_MISMATCH` - o intervalo ocupado nao bate com o
  comprimento declarado da peca.

Todas as tolerancias vem de `model.py`, nunca sao locais.
"""

from .. import analysis
from .. import model
from . import base

# Desvio angular aceito entre a peca e o eixo da parede. 3 graus e' o
# maximo que a soma dos arredondamentos de extracao produz numa peca de
# 4cm; acima disso a peca esta' de fato torta.
ORIENTATION_TOLERANCE_DEG = 3.0

# Diferenca aceita entre (t_end - t_start) e `length_cm` da peca.
LENGTH_TOLERANCE_CM = 1.0

# Quanto a peca pode passar da ponta da parede antes de virar achado.
# Uma peca de amarracao legitima avanca ate' a espessura da parede
# vizinha no encontro - por isso o limite e' a espessura, nao zero.
def _outside_allowance_cm(wall):
    return max(wall.get("thickness_cm") or 0.0, analysis.BLOCK_JOINT_CM)


def validate_wall(wall):
    findings = []
    direction, _length = model.direction_of(wall["start_cm"], wall["end_cm"])
    allowance = _outside_allowance_cm(wall)
    wall_axis_angle = model.normalize_axis_angle(wall["angle_deg"])

    for row in model.rows_sorted(wall):
        blocks = model.blocks_sorted(row)

        # ---- sobreposicao na mesma fiada -------------------------------
        for i in range(len(blocks)):
            for j in range(i + 1, len(blocks)):
                a, b = blocks[i], blocks[j]
                if b["t_start_cm"] >= a["t_end_cm"] - model.OVERLAP_TOLERANCE_CM:
                    break  # ordenado por t_start: os proximos tambem nao tocam
                overlap = analysis.interval_overlap_cm(
                    (a["t_start_cm"], a["t_end_cm"]),
                    (b["t_start_cm"], b["t_end_cm"]),
                )
                if overlap <= model.OVERLAP_TOLERANCE_CM:
                    continue
                findings.append(base.finding(
                    "POSITION_OVERLAP",
                    wall=wall["id"],
                    detail=(
                        "{0} ({1}) e {2} ({3}) se sobrepoem {4:.2f}cm na "
                        "fiada {5}".format(a.get("id"), a.get("code"),
                                           b.get("id"), b.get("code"),
                                           overlap, row["row"])
                    ),
                    row=row["row"],
                    blocks=[a.get("id"), b.get("id")],
                    codes=[a.get("code"), b.get("code")],
                    overlap_cm=round(overlap, 3),
                    t_cm=[round(max(a["t_start_cm"], b["t_start_cm"]), 2),
                          round(min(a["t_end_cm"], b["t_end_cm"]), 2)],
                ))

        for block in blocks:
            # ---- fora da parede ---------------------------------------
            over_start = -block["t_start_cm"]
            over_end = block["t_end_cm"] - wall["length_cm"]
            excess = max(over_start, over_end)
            if excess > allowance:
                findings.append(base.finding(
                    "POSITION_OUTSIDE_WALL",
                    wall=wall["id"],
                    detail=(
                        "{0} ({1}) passa {2:.1f}cm da ponta da parede "
                        "(fiada {3}, tolerancia {4:.1f}cm)".format(
                            block.get("id"), block.get("code"), excess,
                            row["row"], allowance)
                    ),
                    row=row["row"],
                    blocks=[block.get("id")],
                    excess_cm=round(excess, 2),
                    block_t_cm=[round(block["t_start_cm"], 2),
                                round(block["t_end_cm"], 2)],
                    wall_length_cm=wall["length_cm"],
                ))

            # ---- desvio perpendicular ---------------------------------
            _t, s = model.axial_coordinates(block["center_cm"], wall["start_cm"], direction)
            if abs(s) > model.BLOCK_TO_WALL_PERP_TOLERANCE_CM:
                findings.append(base.finding(
                    "POSITION_OFF_AXIS",
                    wall=wall["id"],
                    detail=(
                        "{0} a {1:.1f}cm do eixo da parede (limite "
                        "{2:.1f}cm)".format(block.get("id"), abs(s),
                                            model.BLOCK_TO_WALL_PERP_TOLERANCE_CM)
                    ),
                    row=row["row"],
                    blocks=[block.get("id")],
                    perpendicular_cm=round(s, 3),
                ))

            # ---- orientacao -------------------------------------------
            block_axis = model.normalize_axis_angle(block.get("rotation_deg") or 0.0)
            delta = abs(block_axis - wall_axis_angle)
            delta = min(delta, 180.0 - delta)
            perpendicular_delta = abs(delta - 90.0)
            if (delta > ORIENTATION_TOLERANCE_DEG
                    and perpendicular_delta > ORIENTATION_TOLERANCE_DEG):
                findings.append(base.finding(
                    "POSITION_BAD_ORIENTATION",
                    wall=wall["id"],
                    detail=(
                        "{0} girado {1:.1f} graus contra um eixo de {2:.1f} "
                        "graus".format(block.get("id"),
                                       block.get("rotation_deg") or 0.0,
                                       wall["angle_deg"])
                    ),
                    row=row["row"],
                    blocks=[block.get("id")],
                    rotation_deg=block.get("rotation_deg"),
                    wall_angle_deg=wall["angle_deg"],
                    delta_deg=round(delta, 2),
                ))

            # ---- comprimento ocupado x comprimento da peca -------------
            occupied = block["t_end_cm"] - block["t_start_cm"]
            declared = block.get("length_cm") or 0.0
            if declared > 0 and abs(occupied - declared) > LENGTH_TOLERANCE_CM:
                findings.append(base.finding(
                    "POSITION_LENGTH_MISMATCH",
                    wall=wall["id"],
                    detail=(
                        "{0} ocupa {1:.2f}cm mas a peca {2} tem {3:.2f}cm".format(
                            block.get("id"), occupied, block.get("code"), declared)
                    ),
                    row=row["row"],
                    blocks=[block.get("id")],
                    occupied_cm=round(occupied, 3),
                    declared_cm=round(declared, 3),
                ))
    return findings


def validate(project, context=None):
    findings = []
    for wall in project.get("walls") or []:
        findings.extend(validate_wall(wall))
    return findings


base.register("block_positions", validate)
