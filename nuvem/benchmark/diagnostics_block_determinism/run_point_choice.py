# -*- coding: utf-8 -*-
"""CR-BLOCK-DETERMINISM - ESCOLHA DO PONTO DO NO' e DA ORDEM DOS BRACOS.

Duas decisoes ficaram em aberto depois de fechar o agrupamento, e as duas
sao legitimas em teoria. Este script mede as duas, lado a lado, com o
MESMO benchmark oficial - para escolher por evidencia e nao por gosto:

  PONTO DO NO' (grupos com mais de uma ancora distinta)
    centroide   - a estimativa nao-enviesada do lugar do encontro;
    min_ancora  - a ancora canonicamente menor: mantem o no' EM CIMA de
                  um cruzamento de eixos de verdade (que e' o que uma
                  ancora e'), em vez de num ponto medio que nao e'
                  cruzamento de nada;
    legacy      - group[0]: o que estava na main (dependente da ordem).

  ORDEM DOS BRACOS
    enum        - canonizacao da enumeracao que ja' existia (chave
                  geometrica da parede + qual extremidade);
    angulo      - sistema de rotacao (angulo de saida, anti-horario).

Saida: para cada combinacao, os fingerprints distintos nas 8 variantes e
as regressoes criticas do benchmark oficial contra o baseline versionado.
"""
import math
import sys

import lib_det as L
import run_ablation as AB


def point_centroid(group):
    seen = []
    for arm in group:
        anchor = arm.get("anchor") or arm["point"]
        key = (anchor.X, anchor.Y)
        if key not in seen:
            seen.append(key)
    if len(seen) == 1:
        return AB.L.engine().XYZ(seen[0][0], seen[0][1], 0.0)
    seen.sort()
    tx = ty = 0.0
    for x, y in seen:
        tx += x
        ty += y
    return AB.L.engine().XYZ(tx / len(seen), ty / len(seen), 0.0)


def point_min_anchor(group):
    best = None
    for arm in group:
        anchor = arm.get("anchor") or arm["point"]
        key = (anchor.X, anchor.Y)
        if best is None or key < best:
            best = key
    return AB.L.engine().XYZ(best[0], best[1], 0.0)


def arm_key_enum(walls_to_create, arm):
    module = AB.graph_module()
    wall_key = module._wall_graph_wall_key(walls_to_create, arm["wall_idx"])
    line = walls_to_create[arm["wall_idx"]][0]
    p0 = line.GetEndPoint(0)
    p1 = line.GetEndPoint(1)
    a = (p0.X, p0.Y)
    b = (p1.X, p1.Y)
    mine = a if arm["end_index"] == 0 else b
    lo = a if a <= b else b
    return (wall_key, 0 if mine == lo else 1)


def arm_key_angle(walls_to_create, arm):
    module = AB.graph_module()
    direction = arm["outward_dir"]
    angle = math.atan2(direction.Y, direction.X)
    if angle < 0.0:
        angle += 2.0 * math.pi
    anchor = arm["anchor"]
    point = arm["point"]
    return (angle, anchor.X, anchor.Y, point.X, point.Y,
            module._wall_graph_wall_key(walls_to_create, arm["wall_idx"]))


def arm_key_length(walls_to_create, arm):
    """Parede MAIS LONGA primeiro. Racional de dominio: num encontro, o
    trecho longo e' o que "manda" (e' nele que o preenchimento corre); o
    trecho curto e' quem chega. Desempata pela chave geometrica."""
    module = AB.graph_module()
    line = walls_to_create[arm["wall_idx"]][0]
    length = line.GetEndPoint(0).DistanceTo(line.GetEndPoint(1))
    return (-length, module._wall_graph_wall_key(walls_to_create, arm["wall_idx"]),
            arm_key_enum(walls_to_create, arm)[1])


POINTS = {"centroide": point_centroid, "min_ancora": point_min_anchor,
          "legacy_group0": AB._legacy_group_point}
ARM_KEYS = {"enum": arm_key_enum, "angulo": arm_key_angle,
            "comprimento": arm_key_length}


def run(project_id=None, combos=None):
    project_id = project_id or L.PRIMARY_PROJECT_ID
    module = AB.graph_module()
    input_project = L.load_input(project_id)
    rows = []
    combos = combos or [(pk, ak) for ak in ARM_KEYS for pk in POINTS]
    for point_name, arm_name in combos:
        module._wall_node_group_point = POINTS[point_name]
        module._wall_graph_arm_key = ARM_KEYS[arm_name]
        fps_nodes, fps_blocks = set(), set()
        for _vname, project in L.build_variants(input_project):
            run_data = L.run_full(project)
            fps_nodes.add(L.graph_layers(run_data)["fp_nodes"])
            fps_blocks.add(L.block_layers(run_data)["fp_blocks"])
        critical = AB._critical_codes(project_id)
        rows.append({"ponto": point_name, "ordem_bracos": arm_name,
                     "fingerprints_grafo": len(fps_nodes),
                     "fingerprints_blocos": len(fps_blocks),
                     "regressoes_criticas": critical})
        print("  ponto=%-14s bracos=%-7s grafo=%d blocos=%d crit=%s"
              % (point_name, arm_name, len(fps_nodes), len(fps_blocks), critical))
    return {"project_id": project_id, "combinacoes": rows}


def main():
    result = run(sys.argv[1] if len(sys.argv) > 1 else None)
    L.write_json(L.out_path("out_point_choice.json"), result)
    return result


if __name__ == "__main__":
    main()
