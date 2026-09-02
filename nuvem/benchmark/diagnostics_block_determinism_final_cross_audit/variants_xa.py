# -*- coding: utf-8 -*-
"""Variantes de entrada do CROSS-AUDIT FINAL, escritas do zero.

Duas familias, deliberadamente separadas (item 5 da missao):

  PERMUTACAO  - so' muda a ORDEM da lista `walls`. A planta fisica e'
                IDENTICA por construcao, entao qualquer divergencia de
                resultado e' nao-determinismo puro.
  REVERSAO    - muda o SENTIDO DE DESENHO de paredes. So' e' uma variante
                metamorfica valida se a planta FISICA resultante for a
                mesma - e e' ai' que a bateria antiga da CONTA 2 erra em
                projeto com `walls_already_extended: False`.

Por isso esta bateria traz DUAS reversoes:

  reversal_naive      - `t' = L_input - t` (o que `variants.py` da CONTA 2
                        faz). Reparametriza contra o comprimento do
                        `input.json`.
  reversal_geometric  - `t' = L_extendido - t`, onde `L_extendido` e' o
                        comprimento do eixo que o MOTOR realmente usa
                        depois de `extend_wall_ends_to_junctions`. E' a
                        reversao FISICAMENTE equivalente.

Com `walls_already_extended: True` as duas coincidem. Com `False`, so' a
segunda mede determinismo; a primeira compara plantas diferentes.
"""

import copy
import math
import random

OFFICIAL_SEEDS = (1, 2, 3, 10, 42)
EXTRA_SEEDS = (5, 7, 11, 13, 17, 23, 50, 99, 123, 999)


def _endpoints(wall):
    return tuple(wall["start_cm"]), tuple(wall["end_cm"])


def _input_length_cm(wall):
    (x0, y0), (x1, y1) = _endpoints(wall)
    return math.hypot(x1 - x0, y1 - y0)


def _is_horizontal(wall):
    (x0, y0), (x1, y1) = _endpoints(wall)
    return abs(x1 - x0) >= abs(y1 - y0)


def permuted(project, order):
    walls = project.get("walls") or []
    out = copy.deepcopy(project)
    out["walls"] = [copy.deepcopy(walls[i]) for i in order]
    return out


def shuffled_order(n, seed):
    order = list(range(n))
    random.Random(seed).shuffle(order)
    return order


def _reverse_one(wall, length_cm):
    """Troca as pontas e reparametriza as aberturas contra `length_cm`."""
    out = copy.deepcopy(wall)
    out["start_cm"], out["end_cm"] = wall["end_cm"], wall["start_cm"]
    openings = []
    for opening in wall.get("openings") or []:
        entry = dict(opening)
        entry["t_start_cm"] = length_cm - opening["t_end_cm"]
        entry["t_end_cm"] = length_cm - opening["t_start_cm"]
        openings.append(entry)
    out["openings"] = openings
    return out


def endpoint_reversal(project, indices=None, lengths_cm=None):
    """`lengths_cm[i]` = comprimento contra o qual reparametrizar a parede
    `i`. `None` -> o comprimento do proprio `input.json` (reversao INGENUA)."""
    out = copy.deepcopy(project)
    walls = out.get("walls") or []
    target = set(indices) if indices is not None else set(range(len(walls)))
    new_walls = []
    for i, wall in enumerate(walls):
        if i in target:
            length_cm = (lengths_cm or {}).get(i)
            if length_cm is None:
                length_cm = _input_length_cm(wall)
            new_walls.append(_reverse_one(wall, length_cm))
        else:
            new_walls.append(copy.deepcopy(wall))
    out["walls"] = new_walls
    return out


def engine_axis_lengths_cm(project, plan_func):
    """{wall_idx: comprimento do eixo ESTICADO, em cm} - o eixo que o motor
    usa para medir `t` das aberturas. `plan_func(project)` deve devolver a
    tupla `(nodes, walls_to_create, end_to_node, openings_per_wall)`."""
    _nodes, walls_to_create, _e2n, _op = plan_func(project)
    ft_to_cm = 100.0 * 0.3048
    out = {}
    for i, (line, _t, _l) in enumerate(walls_to_create):
        a, b = line.GetEndPoint(0), line.GetEndPoint(1)
        out[i] = math.hypot(b.X - a.X, b.Y - a.Y) * ft_to_cm
    return out


def build_permutation_variants(project):
    n = len(project.get("walls") or [])
    out = [("reversed_order", permuted(project, list(reversed(range(n)))))]
    for seed in OFFICIAL_SEEDS + EXTRA_SEEDS:
        out.append(("shuffle_seed_%d" % seed, permuted(project, shuffled_order(n, seed))))
    # ordenacao geometrica canonica (crescente e decrescente)
    def key(i):
        wall = project["walls"][i]
        a, b = sorted(_endpoints(wall))
        return (round(a[0], 2), round(a[1], 2), round(b[0], 2), round(b[1], 2),
                round(float(wall.get("thickness_cm") or 0.0), 2))
    order = sorted(range(n), key=key)
    out.append(("geometric_sort", permuted(project, order)))
    out.append(("geometric_sort_reversed", permuted(project, list(reversed(order)))))
    # embaralha DENTRO de cada orientacao, preservando as posicoes do grupo
    for seed in (1, 2):
        walls = project.get("walls") or []
        hs = [i for i, w in enumerate(walls) if _is_horizontal(w)]
        vs = [i for i, w in enumerate(walls) if not _is_horizontal(w)]
        rng = random.Random(seed)
        hh, vv = list(hs), list(vs)
        rng.shuffle(hh)
        rng.shuffle(vv)
        order = [None] * len(walls)
        for pos, src in zip(hs, hh):
            order[pos] = src
        for pos, src in zip(vs, vv):
            order[pos] = src
        out.append(("shuffle_within_orientation_seed_%d" % seed, permuted(project, order)))
    return out


def build_reversal_variants(project, lengths_cm):
    """`lengths_cm` = eixos ESTICADOS (de `engine_axis_lengths_cm`). Cada
    reversao aparece nas DUAS versoes: `_naive` e `_geometric`."""
    walls = project.get("walls") or []
    n = len(walls)
    subsets = [("all", list(range(n))),
               ("horizontal_only", [i for i, w in enumerate(walls) if _is_horizontal(w)]),
               ("vertical_only", [i for i, w in enumerate(walls) if not _is_horizontal(w)])]
    for seed in (1, 2):
        rng = random.Random(seed)
        subsets.append(("random_seed_%d" % seed,
                        [i for i in range(n) if rng.random() < 0.5]))
    out = []
    for name, idxs in subsets:
        out.append(("reversal_naive_%s" % name,
                    endpoint_reversal(project, idxs, None)))
        out.append(("reversal_geometric_%s" % name,
                    endpoint_reversal(project, idxs, lengths_cm)))
    return out
