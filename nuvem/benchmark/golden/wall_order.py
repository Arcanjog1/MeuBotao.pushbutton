# -*- coding: utf-8 -*-
"""ORDEM OFICIAL das paredes (item 17 do pedido) - infraestrutura de
VALIDACAO, preparada para o futuro.

Regra oficial (definida pelo usuario, item 17 do pedido desta tarefa):

    HORIZONTAIS - primeiro; cima -> baixo; empate esquerda -> direita;
                  sentido interno (o proprio eixo start->end) esquerda -> direita.
    VERTICAIS   - depois; baixo -> cima; empate esquerda -> direita;
                  sentido interno baixo -> cima.
    INCLINADAS  - depois; ordem por geometria canonica.

Este modulo SO' VALIDA - nao ordena nada em producao, nao e' chamado por
`solver_bridge.py`/`wall_stepper.py`/`wall_pairing.py`. E' a "capacidade
de validar esta sequencia no futuro" que o item 17 pede, pronta para
quando (se) a producao decidir adotar esta ordem.

Convencao de eixos assumida (a mesma do resto do benchmark, ver
`model.py`): X cresce para a direita, Y cresce "para cima" na planta -
por isso "cima -> baixo" e' Y decrescente.
"""

from .. import model

KIND_HORIZONTAL = "horizontal"
KIND_VERTICAL = "vertical"
KIND_INCLINED = "inclined"

DEFAULT_ANGLE_TOLERANCE_DEG = 1.0


def classify_wall_kind(wall, angle_tolerance_deg=DEFAULT_ANGLE_TOLERANCE_DEG):
    """Horizontal/vertical/inclinada a partir do ANGULO DE EIXO (0 e 180
    sao a mesma direcao - `model.normalize_axis_angle` ja trata isso)."""
    angle = model.normalize_axis_angle(wall["angle_deg"])
    if angle <= angle_tolerance_deg or angle >= 180.0 - angle_tolerance_deg:
        return KIND_HORIZONTAL
    if abs(angle - 90.0) <= angle_tolerance_deg:
        return KIND_VERTICAL
    return KIND_INCLINED


def _extent(wall):
    x0, y0 = wall["start_cm"]
    x1, y1 = wall["end_cm"]
    return min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1)


def official_sort_key(wall, angle_tolerance_deg=DEFAULT_ANGLE_TOLERANCE_DEG):
    """Chave de ordenacao da regra oficial. Grupo (H=0, V=1, inclinada=2)
    primeiro, depois o criterio de cada grupo, com empate por X esquerda.
    Determinista: paredes com a MESMA chave sao geometricamente
    indistinguiveis para esta regra (empate legitimo)."""
    kind = classify_wall_kind(wall, angle_tolerance_deg)
    xmin, _xmax, ymin, ymax = _extent(wall)
    if kind == KIND_HORIZONTAL:
        # cima -> baixo: Y maior primeiro, por isso o sinal negativo.
        return (0, round(-ymax, 3), round(xmin, 3))
    if kind == KIND_VERTICAL:
        # baixo -> cima: Y menor primeiro.
        return (1, round(ymin, 3), round(xmin, 3))
    # Inclinadas: "ordem por geometria canonica" = a propria chave
    # estavel de `model.py`, que ja e' determinista e invariante a
    # reversao de ponta.
    return (2, model.wall_stable_key(wall["start_cm"], wall["end_cm"],
                                     wall.get("thickness_cm", 0.0)))


def official_order(walls, angle_tolerance_deg=DEFAULT_ANGLE_TOLERANCE_DEG):
    """A lista de paredes, na ordem oficial (nunca muda a entrada -
    devolve uma lista nova)."""
    return sorted(walls, key=lambda w: official_sort_key(w, angle_tolerance_deg))


def validate_wall_order(walls, angle_tolerance_deg=DEFAULT_ANGLE_TOLERANCE_DEG):
    """A lista de paredes, NA ORDEM QUE FOI PASSADA, respeita a regra
    oficial? Devolve o primeiro ponto de divergencia, para investigacao -
    nao so' um booleano cego (mesmo principio do item 13: nunca esconder
    o "onde" atras do "sim/nao")."""
    expected = official_order(walls, angle_tolerance_deg)
    expected_ids = [w.get("id") or w.get("key") for w in expected]
    actual_ids = [w.get("id") or w.get("key") for w in walls]

    first_mismatch = None
    for index, (actual, official) in enumerate(zip(actual_ids, expected_ids)):
        if actual != official:
            first_mismatch = index
            break

    return {
        "ok": actual_ids == expected_ids,
        "wall_count": len(walls),
        "expected_order": expected_ids,
        "actual_order": actual_ids,
        "first_mismatch_index": first_mismatch,
    }


def wall_internal_direction_ok(wall, angle_tolerance_deg=DEFAULT_ANGLE_TOLERANCE_DEG):
    """'Sentido interno' (item 17): o proprio eixo start_cm->end_cm da
    parede segue a convencao (horizontal: esquerda->direita; vertical:
    baixo->cima). Paredes inclinadas nao tem sentido interno definido
    pela regra - sempre `True` (nada a checar)."""
    kind = classify_wall_kind(wall, angle_tolerance_deg)
    (x0, y0), (x1, y1) = wall["start_cm"], wall["end_cm"]
    if kind == KIND_HORIZONTAL:
        return x1 >= x0
    if kind == KIND_VERTICAL:
        return y1 >= y0
    return True


def audit_internal_directions(walls, angle_tolerance_deg=DEFAULT_ANGLE_TOLERANCE_DEG):
    """Paredes cujo `start_cm`/`end_cm` esta' no sentido CONTRARIO ao
    'sentido interno' da regra oficial - lista, nao so' contagem."""
    offenders = []
    for wall in walls:
        if not wall_internal_direction_ok(wall, angle_tolerance_deg):
            offenders.append(wall.get("id") or wall.get("key"))
    return {
        "ok": not offenders,
        "wall_count": len(walls),
        "offenders": offenders,
    }
