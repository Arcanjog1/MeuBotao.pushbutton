# -*- coding: utf-8 -*-
"""C02 / MODO A - reproduceres MINIMOS e sinteticos do room check de
amarracao em no' X, independentes do corpus (TGD/TP1/Piloto).

Cada reproducer monta uma planta com UM cruzamento em X, controlando
exatamente a folga (`room_cm`) que o solver vai medir, e roda as FUNCOES
REAIS de producao (`_x_intersection_wall_room_ft`, `solve_x_intersection`)
- nunca uma reimplementacao.

GEOMETRIA (vista de cima), "H deitado":

        |               |          verticais longas (esquerda/direita),
        |               |          amarram as pontas da barra curta
        +------X--------+          barra HORIZONTAL curta de comprimento L
        |               |
        |               |
              |
              |  vertical CENTRAL, cruza a barra no meio -> no' X midspan
              |

A folga medida na barra curta e' `L/2 - CORNER_B34_ROOM_FT (34cm)` de cada
lado, porque as duas pontas dela tem encontro (a reserva de 34cm do
vizinho e' o obstaculo que fecha o room - medido, ver
`c02_deficit_origin.json`: em 100% dos casos reais do corpus o limite e'
`RESERVA_OU_PONTA`, nunca `ABERTURA`).

    room_cm desejado  ->  L = 2 * (room_cm + 34)

Uso:  python3 minimal_reproducers.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# raiz do repositorio: este diretorio vive em nuvem/benchmark/diagnostics_c02/
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from nuvem.benchmark import solver_bridge as SB  # noqa: E402

# Os valores que o CR exige cobrir, mais os vizinhos imediatos do limite.
ROOM_CASES_CM = [
    28.10, 28.00, 27.997, 27.99, 27.98, 27.96, 27.95, 27.94,
    27.90, 27.00, 17.00, 7.00, 0.00,
]

TOL_CANDIDATE_CM = 0.05   # ROOM_CHECK_NOISE_TOLERANCE_CM candidato (C02)
X_REQUIRED_CM = 28.0      # 27 (metade do B54) + 1 (BLOCK_JOINT_CM)


def _mod():
    return SB.engine()


def build_plan(room_cm, transform=None, reverse_ends=False, swap_walls=False):
    """Planta sintetica com UM no' X cuja folga na barra curta e'
    `room_cm` em cada sentido. `transform(x, y) -> (x, y)` aplica
    translacao/rotacao/espelho ANTES de construir as linhas."""
    module = _mod()
    # As pontas da barra encostam nas verticais: `extend_wall_ends_to_
    # junctions` estica cada ponta ate' a FACE da vizinha (+espessura/2),
    # entao o comprimento EFETIVO da barra ja' inclui esse acrescimo.
    thickness_cm = 14.0
    bar_len = 2.0 * (room_cm + 34.0 - thickness_cm / 2.0)
    half = bar_len / 2.0
    long_len = 400.0

    # barra curta horizontal, centrada na origem
    bar = ((-half, 0.0), (half, 0.0))
    # verticais nas duas pontas da barra (dao o encontro que cria a reserva)
    left = ((-half, -long_len / 2.0), (-half, long_len / 2.0))
    right = ((half, -long_len / 2.0), (half, long_len / 2.0))
    # vertical central: cruza a barra no MEIO -> X midspan
    center = ((0.0, -long_len / 2.0), (0.0, long_len / 2.0))

    segments = [bar, left, right, center]
    if swap_walls:
        segments = [center, right, left, bar]

    walls = []
    for (a, b) in segments:
        if reverse_ends:
            a, b = b, a
        if transform is not None:
            a = transform(*a)
            b = transform(*b)
        walls.append({"start_cm": [a[0], a[1]], "end_cm": [b[0], b[1]],
                      "thickness_cm": thickness_cm, "openings": []})
    return {
        "project_id": "c02_repro_room_%s" % room_cm,
        "walls": walls,
        "catalog": _catalog(),
        "settings": {"base_z_cm": 0.0, "course_step_cm": 20.0,
                     "num_courses": 2, "expected_rows": 2,
                     "walls_already_extended": True},
    }


def _catalog():
    """Catalogo minimo com os codigos que o X usa (B54 e a degradacao)."""
    return {
        "B39": {"length_cm": 39.0, "width_cm": 14.0, "height_cm": 19.0},
        "B34": {"length_cm": 34.0, "width_cm": 14.0, "height_cm": 19.0},
        "B54": {"length_cm": 54.0, "width_cm": 14.0, "height_cm": 19.0},
        "B19": {"length_cm": 19.0, "width_cm": 14.0, "height_cm": 19.0},
        "C09": {"length_cm": 9.0, "width_cm": 14.0, "height_cm": 19.0},
        "C04": {"length_cm": 4.0, "width_cm": 14.0, "height_cm": 19.0},
    }


def measure(project):
    """Roda as funcoes REAIS: devolve, para o no' X encontrado,
    (room_cm medido, codigo escolhido em cada parede)."""
    module = _mod()
    ws = sys.modules["core.engine.wall_stepper"]
    nodes, walls, end_to_node, openings = SB.plan_from_input(project)
    catalog, _rc, _dc = SB.catalog_from_input(project)

    out = []
    for node_index, node in enumerate(nodes):
        if node.get("kind") != "X_INTERSECTION":
            continue
        pair = node.get("crossing_walls")
        if not pair or pair[0] is None or pair[1] is None:
            continue
        rooms = []
        for widx in pair:
            rp, rm = ws._x_intersection_wall_room_ft(
                walls, openings, widx, node["point"], nodes, end_to_node, node_index)
            rooms.append(min(rp, rm) / module.FEET_PER_METER * 100.0)
        result = ws.solve_x_intersection(node, walls, catalog, node_index=node_index,
                                         openings_per_wall=openings, nodes=nodes,
                                         end_to_node=end_to_node)
        codes = tuple(sorted(
            (result.get(k) or {}).get("logical_code") for k in ("course_a", "course_b")
            if result.get(k) is not None))
        out.append({"node_cm": [node["point"].X / module.FEET_PER_METER * 100.0,
                                node["point"].Y / module.FEET_PER_METER * 100.0],
                    "room_cm": round(min(rooms), 6),
                    "ok": bool(result.get("ok")),
                    "codes": list(codes)})
    return out


# ---------------------------------------------------------------- casos --

def case_room_ladder():
    """Escada de folgas: qual peca sai em cada `room_cm`, hoje (sem
    tolerancia) e com o candidato de 0,05cm."""
    rows = []
    for room_cm in ROOM_CASES_CM:
        found = measure(build_plan(room_cm))
        deficit = X_REQUIRED_CM - room_cm
        rows.append({
            "room_cm": room_cm,
            "required_cm": X_REQUIRED_CM,
            "deficit_cm": round(deficit, 6),
            "b54_hoje": deficit <= 0,
            "b54_com_tol_005": deficit <= TOL_CANDIDATE_CM,
            "classe": ("cabe" if deficit <= 0 else
                       "ruido<=0.05" if deficit <= 0.05 else
                       "borderline<=0.30" if deficit <= 0.30 else
                       "geometria insuficiente"),
            "x_nodes": found,
        })
    return rows


def case_invariance():
    """A MESMA geometria sob translacao, rotacao, espelho, reversao de
    extremidades e permutacao das paredes: a folga medida tem de ser
    IDENTICA nas cinco. Se nao for, o defeito e' na MEDICAO, nao no teto."""
    import math

    def rot(deg):
        rad = math.radians(deg)
        c, s = math.cos(rad), math.sin(rad)
        return lambda x, y: (x * c - y * s, x * s + y * c)

    variants = {
        "identidade": {},
        "translacao_+1234.567_-987.654": {"transform": lambda x, y: (x + 1234.567, y - 987.654)},
        "rotacao_90": {"transform": rot(90)},
        "rotacao_37": {"transform": rot(37)},
        "espelho_x": {"transform": lambda x, y: (-x, y)},
        "espelho_y": {"transform": lambda x, y: (x, -y)},
        "reversao_pontas": {"reverse_ends": True},
        "permutacao_paredes": {"swap_walls": True},
    }
    out = {}
    for room_cm in (28.00, 27.997, 27.98, 27.90, 17.00):
        per_variant = {}
        for name, kwargs in variants.items():
            found = measure(build_plan(room_cm, **kwargs))
            per_variant[name] = {
                "room_cm": round(found[0]["room_cm"], 6) if found else None,
                "codes": found[0]["codes"] if found else None,
                "x_nodes": len(found),
            }
        rooms = set(v["room_cm"] for v in per_variant.values())
        codes = set(tuple(v["codes"] or ()) for v in per_variant.values())
        out[str(room_cm)] = {
            "variants": per_variant,
            "room_invariante": len(rooms) == 1,
            "peca_invariante": len(codes) == 1,
            "rooms_distintos": sorted(r for r in rooms if r is not None),
        }
    return out


def main():
    report = {
        "contract": {"x_required_cm": X_REQUIRED_CM,
                     "tolerance_candidate_cm": TOL_CANDIDATE_CM},
        "room_ladder": case_room_ladder(),
        "invariance": case_invariance(),
    }
    print(json.dumps(report, indent=1, ensure_ascii=False))
    with open(os.path.join(HERE, "c02_minimal_reproducers.json"), "w",
              encoding="utf-8") as h:
        json.dump(report, h, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
