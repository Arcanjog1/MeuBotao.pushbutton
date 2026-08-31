# -*- coding: utf-8 -*-
"""PRISMA - junta vertical indevidamente alinhada entre fiadas.

E' o erro mais grave da modulacao: uma junta que atravessa fiadas
consecutivas divide a parede em dois prismas independentes, e e'
exatamente o que separa alvenaria ESTRUTURAL amarrada de um empilhamento
de blocos.

Tres achados diferentes, de proposito (o pedido, item 8, quer saber
QUAL problema, nao so' "falhou"):

* `PRISM_CONTINUOUS_JOINT` - a mesma junta aparece em duas fiadas
  consecutivas. Erro direto, nivel 1.
* `PRISM_JOINT_STACK` - a mesma coordenada de junta se repete em muitas
  fiadas da parede (nao necessariamente vizinhas). E' o padrao que
  `audit_wall_bond_quality` chama de junta corrida, medido pelos mesmos
  limites (`BOND_CONTINUOUS_JOINT_*`).
* `PRISM_STAGGER_BELOW_TARGET` - as juntas nao coincidem, mas o
  desencontro ficou abaixo do alvo de 10cm. Nivel 2: nao reprova nada,
  so' registra que a amarracao ficou "por pouco".

EXCECAO respeitada (secao 11.8): junta que separa peca pequena de
fechamento (C04/C09/B19) encostada num vao ou na ponta do eixo - ver
`analysis.joint_is_opening_aligned_exempt`.
"""

from .. import analysis
from .. import model
from . import base


def _joint_signature(joint):
    return {
        "t_cm": round(joint["t_cm"], 2),
        "left_code": joint["left"].get("code"),
        "right_code": joint["right"].get("code"),
        "left_block": joint["left"].get("id"),
        "right_block": joint["right"].get("id"),
    }


def validate_wall(wall, tolerance_cm=model.JOINT_ALIGNMENT_TOLERANCE_CM):
    findings = []
    rows = model.rows_sorted(wall)
    if len(rows) < 2:
        return findings

    joints_by_row = {}
    for row in rows:
        joints_by_row[row["row"]] = [
            joint for joint in analysis.row_joints(row)
            if not analysis.joint_is_opening_aligned_exempt(joint, wall)
        ]

    # ---- 1) junta corrida entre fiadas CONSECUTIVAS --------------------
    for row_a, row_b in analysis.consecutive_row_pairs(wall):
        for joint_a in joints_by_row.get(row_a["row"], []):
            for joint_b in joints_by_row.get(row_b["row"], []):
                delta = abs(joint_a["t_cm"] - joint_b["t_cm"])
                if delta > tolerance_cm:
                    continue
                findings.append(base.finding(
                    "PRISM_CONTINUOUS_JOINT",
                    wall=wall["id"],
                    detail=(
                        "junta em t={0:.1f}cm alinhada entre as fiadas {1} e "
                        "{2} (desencontro {3:.2f}cm, limite {4:.2f}cm)".format(
                            joint_a["t_cm"], row_a["row"], row_b["row"],
                            delta, tolerance_cm)
                    ),
                    row_a=row_a["row"], row_b=row_b["row"],
                    joint_t_cm=round(joint_a["t_cm"], 2),
                    stagger_cm=round(delta, 3),
                    blocks=[
                        joint_a["left"].get("id"), joint_a["right"].get("id"),
                        joint_b["left"].get("id"), joint_b["right"].get("id"),
                    ],
                    joint_a=_joint_signature(joint_a),
                    joint_b=_joint_signature(joint_b),
                ))

    # ---- 2) faixa vertical de juntas na mesma coordenada ---------------
    num_courses = len(rows)
    if num_courses >= analysis.BOND_CONTINUOUS_JOINT_MIN_COURSES:
        points = []
        for row_index, joints in joints_by_row.items():
            for joint in joints:
                points.append((joint["t_cm"], row_index))
        for cluster in analysis.cluster_1d(points, analysis.BOND_JOINT_CLUSTER_TOLERANCE_CM):
            course_indices = sorted(set(cluster["items"]))
            ratio = len(course_indices) / float(num_courses)
            if (len(course_indices) >= analysis.BOND_CONTINUOUS_JOINT_MIN_COURSES
                    and ratio >= analysis.BOND_CONTINUOUS_JOINT_RATIO):
                findings.append(base.finding(
                    "PRISM_JOINT_STACK",
                    wall=wall["id"],
                    detail=(
                        "junta em t={0:.1f}cm se repete em {1} de {2} fiadas "
                        "({3:.0f}%)".format(cluster["center"], len(course_indices),
                                            num_courses, 100.0 * ratio)
                    ),
                    joint_t_cm=round(cluster["center"], 2),
                    rows=course_indices,
                    ratio=round(ratio, 3),
                ))

    # ---- 3) desencontro abaixo do alvo (nivel 2) -----------------------
    for row_a, row_b in analysis.consecutive_row_pairs(wall):
        for joint_a in joints_by_row.get(row_a["row"], []):
            nearest = None
            for joint_b in joints_by_row.get(row_b["row"], []):
                delta = abs(joint_a["t_cm"] - joint_b["t_cm"])
                if nearest is None or delta < nearest:
                    nearest = delta
            if nearest is None:
                continue
            if tolerance_cm < nearest < analysis.MIN_JOINT_STAGGER_TARGET_CM:
                findings.append(base.finding(
                    "PRISM_STAGGER_BELOW_TARGET",
                    wall=wall["id"],
                    detail=(
                        "desencontro de {0:.1f}cm em t={1:.1f}cm entre as "
                        "fiadas {2} e {3} (alvo {4:.0f}cm)".format(
                            nearest, joint_a["t_cm"], row_a["row"], row_b["row"],
                            analysis.MIN_JOINT_STAGGER_TARGET_CM)
                    ),
                    row_a=row_a["row"], row_b=row_b["row"],
                    joint_t_cm=round(joint_a["t_cm"], 2),
                    stagger_cm=round(nearest, 3),
                ))
    return findings


def validate(project, context=None):
    findings = []
    for wall in project.get("walls") or []:
        findings.extend(validate_wall(wall))
    return findings


base.register("prism", validate)
