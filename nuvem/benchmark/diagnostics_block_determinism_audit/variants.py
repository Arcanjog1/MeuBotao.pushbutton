# -*- coding: utf-8 -*-
"""Gerador de VARIANTES de entrada — mesma geometria, ordens diferentes
(missão itens 4 e 5). Opera direto sobre `input_project["walls"]` (a lista
crua do `input.json`, ANTES de qualquer chamada ao motor), nunca sobre
`walls_to_create`/`wall_idx` (que só existem depois de `plan_from_input`).

As 8 variantes "oficiais" (baseline, reversed, endpoint_reversal, shuffle
seeds 1/2/3/10/42) + variantes adicionais pedidas na missão para não deixar
uma correção futura fazer overfit nas 8 conhecidas.
"""

import copy
import random

OFFICIAL_SEEDS = (1, 2, 3, 10, 42)
EXTRA_SEEDS = (5, 7, 11, 13, 17, 23, 50, 99, 123, 999)


def _wall_endpoints(wall):
    return tuple(wall["start_cm"]), tuple(wall["end_cm"])


def _is_horizontal(wall):
    (x0, y0), (x1, y1) = _wall_endpoints(wall)
    return abs(x1 - x0) >= abs(y1 - y0)


def permuted(input_project, order):
    walls = input_project.get("walls") or []
    new_project = copy.deepcopy(input_project)
    new_project["walls"] = [copy.deepcopy(walls[i]) for i in order]
    return new_project


def reversed_order(n):
    return list(reversed(range(n)))


def shuffled_order(n, seed):
    order = list(range(n))
    random.Random(seed).shuffle(order)
    return order


def _reverse_wall_endpoints(wall):
    """Troca start_cm/end_cm de UMA parede, re-parametrizando as aberturas
    (`novo_t = comprimento - t_antigo`, início/fim trocados) — o mesmo
    sentido de desenho invertido, geometria idêntica."""
    start_cm = wall["start_cm"]
    end_cm = wall["end_cm"]
    length_cm = ((end_cm[0] - start_cm[0]) ** 2 + (end_cm[1] - start_cm[1]) ** 2) ** 0.5
    new_wall = copy.deepcopy(wall)
    new_wall["start_cm"], new_wall["end_cm"] = end_cm, start_cm
    new_openings = []
    for opening in wall.get("openings") or []:
        new_opening = dict(opening)
        new_opening["t_start_cm"] = length_cm - opening["t_end_cm"]
        new_opening["t_end_cm"] = length_cm - opening["t_start_cm"]
        new_openings.append(new_opening)
    new_wall["openings"] = new_openings
    return new_wall


def endpoint_reversal(input_project, indices=None):
    """Inverte start_cm/end_cm nas paredes de `indices` (todas, por
    padrão)."""
    new_project = copy.deepcopy(input_project)
    walls = new_project.get("walls") or []
    target = set(indices) if indices is not None else set(range(len(walls)))
    new_project["walls"] = [
        _reverse_wall_endpoints(w) if i in target else copy.deepcopy(w)
        for i, w in enumerate(walls)
    ]
    return new_project


def reverse_horizontal_only(input_project):
    walls = input_project.get("walls") or []
    idxs = [i for i, w in enumerate(walls) if _is_horizontal(w)]
    return endpoint_reversal(input_project, idxs)


def reverse_vertical_only(input_project):
    walls = input_project.get("walls") or []
    idxs = [i for i, w in enumerate(walls) if not _is_horizontal(w)]
    return endpoint_reversal(input_project, idxs)


def random_endpoint_reversal(input_project, seed):
    """Reversão de endpoints de um SUBCONJUNTO aleatório (~metade) das
    paredes — mistura direção de desenho, não só ordem de lista."""
    walls = input_project.get("walls") or []
    rng = random.Random(seed)
    idxs = [i for i in range(len(walls)) if rng.random() < 0.5]
    return endpoint_reversal(input_project, idxs)


def shuffle_within_orientation(input_project, seed):
    """Preserva as POSIÇÕES na lista ocupadas por paredes horizontais vs
    verticais, mas embaralha a ordem DENTRO de cada grupo — testa se a
    ordem relativa dentro do mesmo eixo (não entre eixos) já basta para
    mudar o resultado."""
    walls = input_project.get("walls") or []
    h_positions = [i for i, w in enumerate(walls) if _is_horizontal(w)]
    v_positions = [i for i, w in enumerate(walls) if not _is_horizontal(w)]
    rng = random.Random(seed)
    h_shuffled = list(h_positions)
    rng.shuffle(h_shuffled)
    v_shuffled = list(v_positions)
    rng.shuffle(v_shuffled)

    order = [None] * len(walls)
    for pos, src in zip(h_positions, h_shuffled):
        order[pos] = src
    for pos, src in zip(v_positions, v_shuffled):
        order[pos] = src
    return permuted(input_project, order)


def _geom_sort_key(wall):
    (x0, y0), (x1, y1) = _wall_endpoints(wall)
    a, b = sorted([(x0, y0), (x1, y1)])
    return (round(a[0], 2), round(a[1], 2), round(b[0], 2), round(b[1], 2),
            round(float(wall.get("thickness_cm") or 0.0), 2))


def geometric_sort(input_project, reverse=False):
    """Ordena `walls` por uma chave geométrica CANÔNICA (independente da
    ordem de entrada original) — o experimento de 'sort falso' do item 10
    da missão."""
    walls = input_project.get("walls") or []
    order = sorted(range(len(walls)), key=lambda i: _geom_sort_key(walls[i]),
                    reverse=reverse)
    return permuted(input_project, order)


def build_official_variants(input_project):
    """As 8 variantes oficiais (missão item 4), na ordem pedida."""
    n = len(input_project.get("walls") or [])
    variants = [
        ("reversed", permuted(input_project, reversed_order(n))),
        ("endpoint_reversal", endpoint_reversal(input_project)),
    ]
    for seed in OFFICIAL_SEEDS:
        variants.append(("shuffle_seed_%d" % seed,
                          permuted(input_project, shuffled_order(n, seed))))
    return variants


def build_extra_variants(input_project):
    """Bateria adicional (missão item 5) — seeds extras + variantes
    estruturais, para não deixar uma correção futura fazer overfit nas 8
    variantes conhecidas."""
    n = len(input_project.get("walls") or [])
    variants = []
    for seed in EXTRA_SEEDS:
        variants.append(("shuffle_seed_%d" % seed,
                          permuted(input_project, shuffled_order(n, seed))))
    variants.append(("reverse_horizontal_only", reverse_horizontal_only(input_project)))
    variants.append(("reverse_vertical_only", reverse_vertical_only(input_project)))
    variants.append(("shuffle_within_orientation_seed_1",
                      shuffle_within_orientation(input_project, 1)))
    variants.append(("shuffle_within_orientation_seed_2",
                      shuffle_within_orientation(input_project, 2)))
    variants.append(("random_endpoint_reversal_seed_1",
                      random_endpoint_reversal(input_project, 1)))
    variants.append(("random_endpoint_reversal_seed_2",
                      random_endpoint_reversal(input_project, 2)))
    return variants


def build_all_variants(input_project):
    """baseline (ordem original) + oficiais + extras. `baseline` fica de
    fora da lista (o chamador já roda separado como referência)."""
    return build_official_variants(input_project) + build_extra_variants(input_project)


CANONICAL_SORT_VARIANTS = (
    ("geometric_sort", lambda p: geometric_sort(p, reverse=False)),
    ("geometric_sort_reversed", lambda p: geometric_sort(p, reverse=True)),
)
