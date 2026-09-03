# -*- coding: utf-8 -*-
"""Leituras geometricas compartilhadas pelos validadores.

Tudo aqui e' funcao pura sobre o dict de `model.py` - sem Revit, sem
estado global. Um validador que precise de uma leitura nova coloca ela
AQUI se outro validador puder aproveitar; regra especifica de UMA classe
de problema fica no proprio validador.

CONSTANTES ESPELHADAS DO MOTOR
------------------------------
Os limites abaixo sao os MESMOS que `core/wall_modeling.py` e
`core/engine/wall_stepper.py` usam. Estao repetidos aqui, e nao
importados, por um motivo concreto: importar o motor exige os dubles do
Revit (`tests/revit_stubs.py`), e o benchmark precisa rodar sobre JSON
puro, inclusive numa maquina sem nada do Revit instalado.

Repetir numero e' risco de divergencia silenciosa - por isso existe
`tests/regression/test_engine_constants_match.py`, que importa o motor de
verdade e falha se qualquer um destes valores sair do lugar. Se aquele
teste falhar, o certo e' entender qual dos dois mudou, nunca so'
atualizar o numero daqui.
"""

import math

from . import model

# --- espelhados de core/wall_modeling.py ------------------------------
BOND_JOINT_CLUSTER_TOLERANCE_CM = 1.5
BOND_CONTINUOUS_JOINT_MIN_COURSES = 4
BOND_CONTINUOUS_JOINT_RATIO = 0.6
BOND_ALTERNATING_JOINT_MIN_COURSES = 3
BOND_ALTERNATING_JOINT_RATIO = 0.6
BOND_STRIP_CLUSTER_TOLERANCE_CM = 6.0
BOND_STRIP_MIN_COURSES = 3
BOND_STRIP_RATIO = 0.5
BOND_STRIP_EDGE_EXEMPT_CM = 25.0
BOND_STRIP_OPENING_INFLUENCE_CM = 60.0
BOND_STRIP_NODE_EXEMPT_CM = 60.0
BOND_MAX_ADJACENT_GAP_CM = 5.0

# --- espelhados de core/engine/wall_stepper.py -------------------------
HALF_BLOCK_CODE = "B19"
MAX_COMPENSATORS_PER_TRECHO = 1
MAX_SPECIAL_BOND_PER_TRECHO = 1
OPENING_ALIGNED_EXEMPT_CODES = ("C04", "C09", "B19")
MIN_JOINT_STAGGER_TARGET_CM = 10.0
COMPENSATOR_CODES = ("C09", "C04")
SPECIAL_BOND_CODES = ("B34", "B54")

# --- espelhados de core/engine/modulation_math.py ----------------------
BLOCK_JOINT_CM = 1.0
BLOCK_OPENING_JOINT_CM = 0.0
PIER_MODULE_CM = 5.0
BLOCK_LENGTHS_CM = (39.0, 34.0, 19.0, 9.0, 4.0)

# --- espelhado de core/wall_modeling.py::FIRST_COURSE_Z_OFFSET_CM ------
# CR-BENCH-Z-ORIGIN: a Fiada 1 do motor NAO nasce em `base_z_abs` - nasce
# em `base_z_abs + FIRST_COURSE_Z_OFFSET_CM` (ver `_course_z_abs` no
# motor). E' a UNICA convencao vertical valida; `course_z_abs_cm` abaixo
# e' o unico lugar do benchmark que aplica esse offset - todo extrator
# que precisar da cota Z de uma fiada tem que passar por aqui, nunca
# reescrever `base_z_cm + n * course_step_cm` local.
FIRST_COURSE_Z_OFFSET_CM = 1.0

# Tolerancia de "encostado na abertura/ponta" da excecao da regra #1
# (secao 11.8) - `OPENING_ALIGNED_TOUCH_TOLERANCE_CM` no motor.
OPENING_ALIGNED_TOUCH_TOLERANCE_CM = 2.0


# --------------------------------------------------------------- leituras
def row_extents(row):
    """[(t_start, t_end, block)] da fiada, ordenado pelo inicio."""
    items = [(b["t_start_cm"], b["t_end_cm"], b) for b in row.get("blocks") or []]
    items.sort(key=lambda item: item[0])
    return items


def row_joints(row, max_gap_cm=BOND_MAX_ADJACENT_GAP_CM):
    """Juntas VERTICAIS entre pecas encostadas da mesma fiada.

    Cada junta e' `{"t_cm", "left", "right", "gap_cm"}`. Pecas separadas
    por mais que `max_gap_cm` NAO formam junta: entre elas ha' um vao (ou
    outro vazio), nao uma junta de assentamento - a mesma decisao que
    `audit_wall_bond_quality` toma no motor."""
    extents = row_extents(row)
    joints = []
    for i in range(len(extents) - 1):
        gap = extents[i + 1][0] - extents[i][1]
        if gap > max_gap_cm:
            continue
        joints.append({
            "t_cm": (extents[i][1] + extents[i + 1][0]) / 2.0,
            "left": extents[i][2],
            "right": extents[i + 1][2],
            "gap_cm": gap,
        })
    return joints


def opening_edges_cm(wall):
    edges = []
    for opening in wall.get("openings") or []:
        edges.append(opening["t_start_cm"])
        edges.append(opening["t_end_cm"])
    return edges


def joint_is_opening_aligned_exempt(joint, wall,
                                    tolerance_cm=OPENING_ALIGNED_TOUCH_TOLERANCE_CM):
    """EXCECAO da regra #1 (REGRAS_MODULACAO_BLOCOS.md secao 11.8): a junta
    que separa uma peca PEQUENA DE FECHAMENTO (C04/C09/B19) encostada numa
    abertura - ou na PONTA do proprio eixo - pode ficar alinhada entre
    fiadas sem ser a "junta corrida" que a regra proibe.

    Mesma logica de `_joint_is_opening_aligned_exempt` no motor: basta que
    UMA das duas pecas da junta seja de fechamento E tenha uma de suas
    bordas coincidindo com uma borda de vao ou com uma ponta do eixo."""
    limits = opening_edges_cm(wall) + [0.0, wall["length_cm"]]
    for block in (joint["left"], joint["right"]):
        if block.get("code") not in OPENING_ALIGNED_EXEMPT_CODES:
            continue
        for edge in limits:
            if (abs(block["t_start_cm"] - edge) <= tolerance_cm
                    or abs(block["t_end_cm"] - edge) <= tolerance_cm):
                return True
    return False


def opening_active_in_row(opening, row_elevation_cm, block_height_cm):
    """A abertura corta esta fiada? Uma janela so' esvazia a FAIXA
    VERTICAL do seu vao - abaixo do peitoril e acima da verga a fiada
    continua solida (regra da secao 4). Uma porta (peitoril 0) esvazia
    desde a base.

    A fiada ocupa [elevacao, elevacao + altura_do_bloco); ha' interseccao
    quando essa faixa cruza [peitoril, verga)."""
    row_lo = float(row_elevation_cm)
    row_hi = row_lo + float(block_height_cm)
    return (opening["sill_cm"] < row_hi - 1e-6
            and opening["head_cm"] > row_lo + 1e-6)


def active_opening_intervals(wall, row, block_height_cm):
    """[(t_start, t_end, opening)] das aberturas ATIVAS nesta fiada."""
    result = []
    for opening in wall.get("openings") or []:
        if opening_active_in_row(opening, row["elevation_cm"], block_height_cm):
            result.append((opening["t_start_cm"], opening["t_end_cm"], opening))
    result.sort(key=lambda item: item[0])
    return result


def merge_intervals(intervals, tolerance_cm=0.0):
    """Funde intervalos `(a, b)` que se tocam (folga `tolerance_cm`)."""
    ordered = sorted((float(a), float(b)) for a, b in intervals)
    merged = []
    for start, end in ordered:
        if merged and start - merged[-1][1] <= tolerance_cm:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def subtract_intervals(whole, holes):
    """`whole` (a, b) menos a lista `holes` - devolve os pedacos que
    sobram, na ordem."""
    remaining = [(float(whole[0]), float(whole[1]))]
    for hole_start, hole_end in merge_intervals(holes):
        next_remaining = []
        for start, end in remaining:
            if hole_end <= start or hole_start >= end:
                next_remaining.append((start, end))
                continue
            if hole_start > start:
                next_remaining.append((start, hole_start))
            if hole_end < end:
                next_remaining.append((hole_end, end))
        remaining = next_remaining
    return remaining


def interval_overlap_cm(a, b):
    """Quanto dois intervalos se sobrepoem (0 se nao se tocam)."""
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


def block_height_of(project, default_cm=19.0):
    """Altura fisica da peca comum. Sai do catalogo quando ele existe;
    senao, do proprio passo entre fiadas medido no projeto."""
    heights = [
        entry.get("height_cm")
        for entry in (project.get("catalog") or {}).values()
        if entry.get("height_cm")
    ]
    if heights:
        # A altura DOMINANTE, nao a maior: canaleta J tem 29cm e nao pode
        # definir o passo das fiadas comuns.
        counts = {}
        for height in heights:
            counts[round(float(height), 1)] = counts.get(round(float(height), 1), 0) + 1
        return max(counts.items(), key=lambda kv: (kv[1], -kv[0]))[0]
    settings = project.get("settings") or {}
    if settings.get("block_height_cm"):
        return float(settings["block_height_cm"])
    return default_cm


def course_step_cm(project, default_cm=20.0):
    settings = project.get("settings") or {}
    if settings.get("course_step_cm"):
        return float(settings["course_step_cm"])
    return default_cm


def course_z_abs_cm(base_z_cm, course_index, course_step_cm_value):
    """Cota Z absoluta (cm) da fiada `course_index` (0-based) - MESMA
    convencao/formula do motor (`core/wall_modeling.py::_course_z_abs`,
    so' em cm em vez de ft): a Fiada 1 (course_index=0) nasce em
    `base_z_cm + FIRST_COURSE_Z_OFFSET_CM`, nunca em `base_z_cm`.

    CR-BENCH-Z-ORIGIN: esta e' a UNICA formula de origem vertical do
    benchmark - qualquer extrator que precise da cota de uma fiada usa
    esta funcao, nunca `base_z_cm + course_index * course_step_cm` direto
    (foi exatamente essa omissao, em `extract/from_solver.py`, que fazia
    o benchmark medir 1cm de sobreposicao fisica que nao existe)."""
    return base_z_cm + FIRST_COURSE_Z_OFFSET_CM + course_index * course_step_cm_value


def is_compensator(block):
    return block.get("code") in COMPENSATOR_CODES or block.get("role") == model.ROLE_COMPENSATOR


def is_special_bond(block):
    return block.get("code") in SPECIAL_BOND_CODES


def cluster_1d(points, tolerance_cm):
    """Agrupa `(valor, carga)` por proximidade em 1D. Devolve
    `[{"center", "items"}]`. Mesmo algoritmo de `_cluster_1d` no motor -
    o agrupamento das juntas por coordenada depende disso."""
    ordered = sorted(points, key=lambda item: item[0])
    clusters = []
    for value, payload in ordered:
        if clusters and value - clusters[-1]["values"][-1] <= tolerance_cm:
            clusters[-1]["values"].append(value)
            clusters[-1]["items"].append(payload)
        else:
            clusters.append({"values": [value], "items": [payload]})
    for cluster in clusters:
        cluster["center"] = sum(cluster["values"]) / float(len(cluster["values"]))
    return clusters


def wall_rows_by_index(wall):
    return dict((row["row"], row) for row in wall.get("rows") or [])


def consecutive_row_pairs(wall):
    """[(row_a, row_b)] de fiadas FISICAMENTE consecutivas (indice n e
    n+1). Fiadas faltando quebram o par de proposito: o prisma so' faz
    sentido entre fiadas que de fato se apoiam uma na outra."""
    by_index = wall_rows_by_index(wall)
    pairs = []
    for index in sorted(by_index):
        if index + 1 in by_index:
            pairs.append((by_index[index], by_index[index + 1]))
    return pairs


class OccupancyIndex(object):
    """Onde ha' PECA no projeto inteiro, independente de a que parede ela
    pertence.

    Existe por causa de um falso positivo real, medido no projeto humano
    TORRE EASY-LO-R00 (nivel 05. TP1): 1.619 "vazios" de menos de 20cm
    apontados num projeto entregue e aprovado. Investigando um deles, a
    peca que preenchia o vazio existia - era um B34 girado 270 graus,
    pertencente a' parede PERPENDICULAR que amarra ali. Olhando so' as
    pecas da propria parede, a amarracao da vizinha vira buraco.

    Perguntar "ha' peca neste ponto, de QUALQUER parede?" e' a pergunta
    fisicamente certa, e nao depende de a reconstrucao de encontros ter
    achado aquele no' - por isso substitui, e nao complementa, a heuristica
    de zona de amarracao.

    Indice por (fiada por cota, celula de 50cm) - varredura linear sobre
    12 mil pecas por vazio seria inviavel."""

    CELL_CM = 50.0

    def __init__(self, project, z_tolerance_cm=model.COURSE_Z_TOLERANCE_CM):
        self.z_tolerance_cm = z_tolerance_cm
        self._cells = {}
        for wall in project.get("walls") or []:
            for row in wall.get("rows") or []:
                for block in row.get("blocks") or []:
                    self._add(wall, block)

    def _key(self, z_cm, x_cm, y_cm):
        return (round(float(z_cm) / max(1e-6, self.z_tolerance_cm)),
                int(math.floor(x_cm / self.CELL_CM)),
                int(math.floor(y_cm / self.CELL_CM)))

    def _add(self, wall, block):
        reach = (block.get("length_cm") or 0.0) / 2.0 + (block.get("width_cm") or 14.0) / 2.0
        cx, cy = block["center_cm"]
        z = block["z_cm"]
        x_lo = int(math.floor((cx - reach) / self.CELL_CM))
        x_hi = int(math.floor((cx + reach) / self.CELL_CM))
        y_lo = int(math.floor((cy - reach) / self.CELL_CM))
        y_hi = int(math.floor((cy + reach) / self.CELL_CM))
        z_key = round(float(z) / max(1e-6, self.z_tolerance_cm))
        for gx in range(x_lo, x_hi + 1):
            for gy in range(y_lo, y_hi + 1):
                self._cells.setdefault((z_key, gx, gy), []).append((wall, block))

    def blocks_near(self, z_cm, x_cm, y_cm, radius_cm=0.0):
        """Pecas na mesma fiada e nas celulas que cobrem o raio pedido."""
        found, seen = [], set()
        z_key = round(float(z_cm) / max(1e-6, self.z_tolerance_cm))
        x_lo = int(math.floor((x_cm - radius_cm) / self.CELL_CM))
        x_hi = int(math.floor((x_cm + radius_cm) / self.CELL_CM))
        y_lo = int(math.floor((y_cm - radius_cm) / self.CELL_CM))
        y_hi = int(math.floor((y_cm + radius_cm) / self.CELL_CM))
        for gx in range(x_lo, x_hi + 1):
            for gy in range(y_lo, y_hi + 1):
                for wall, block in self._cells.get((z_key, gx, gy)) or []:
                    marker = id(block)
                    if marker in seen:
                        continue
                    seen.add(marker)
                    found.append((wall, block))
        return found

    def foreign_coverage_on_axis(self, wall, row, t_lo, t_hi):
        """Intervalos de `[t_lo, t_hi]` do eixo de `wall` ocupados por pecas
        de OUTRAS paredes naquela fiada.

        A peca vizinha entra girada; o que ela ocupa NO EIXO desta parede e'
        a projecao do retangulo dela na direcao do eixo - por isso a conta
        usa `|u.d|` e `|v.d|`, e nao o comprimento cru da peca."""
        direction, _length = model.direction_of(wall["start_cm"], wall["end_cm"])
        mid_t = (t_lo + t_hi) / 2.0
        center = (wall["start_cm"][0] + direction[0] * mid_t,
                  wall["start_cm"][1] + direction[1] * mid_t)
        radius = (t_hi - t_lo) / 2.0 + 60.0
        covered = []
        for other_wall, block in self.blocks_near(row["elevation_cm"],
                                                  center[0], center[1], radius):
            if other_wall.get("id") == wall.get("id"):
                continue
            angle = math.radians(block.get("rotation_deg") or 0.0)
            ux, uy = math.cos(angle), math.sin(angle)
            vx, vy = -uy, ux
            half_length = (block.get("length_cm") or 0.0) / 2.0
            half_width = (block.get("width_cm") or 14.0) / 2.0
            t_center, s_center = model.axial_coordinates(
                block["center_cm"], wall["start_cm"], direction)
            along = half_length * abs(ux * direction[0] + uy * direction[1]) \
                + half_width * abs(vx * direction[0] + vy * direction[1])
            across = half_length * abs(-ux * direction[1] + uy * direction[0]) \
                + half_width * abs(-vx * direction[1] + vy * direction[0])
            # So' conta a peca que de fato entra na FAIXA da parede.
            if abs(s_center) > across + (wall.get("thickness_cm") or 14.0) / 2.0:
                continue
            piece = (max(t_lo, t_center - along), min(t_hi, t_center + along))
            if piece[1] - piece[0] > 0:
                covered.append(piece)
        return merge_intervals(covered, tolerance_cm=BLOCK_JOINT_CM)


def distance_point_to_segment_cm(point, start, end):
    px, py = float(point[0]), float(point[1])
    ax, ay = float(start[0]), float(start[1])
    bx, by = float(end[0]), float(end[1])
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    if length_sq < 1e-12:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))
