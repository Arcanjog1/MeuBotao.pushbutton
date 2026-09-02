# -*- coding: utf-8 -*-
"""Oráculo geométrico INDEPENDENTE de classificação de nós (missão item 8).

Reimplementação PRÓPRIA, do zero, a partir só da geometria bruta das
paredes (endpoints em cm + espessura). NÃO importa, NÃO chama e NÃO
reproduz `_classify_wall_node`/`build_wall_graph`/`_find_wall_midspan_crossings`
de `core/engine/wall_pairing.py` — este módulo foi escrito olhando para a
GEOMETRIA (o que significa "duas paredes se encontram formando um L"), não
para o código do motor, exatamente para servir de segunda opinião
independente sobre o que o motor decidiu.

Detalhe geométrico medido diretamente no projeto real (ver
`docs/BLOCK_DETERMINISM_AUDIT.md`, secao "oraculo"): as paredes em
`walls_to_create` chegam JA' ESTICADAS ate' a FACE da parede vizinha (nao
ate' o ponto de intersecao dos EIXOS) - um no' L_CORNER medido tinha as
duas pontas a ~7-8cm do ponto do no' (a metade da espessura de 14cm da
parede vizinha), NAO coincidentes entre si. Por isso o oraculo nao pode
clusterizar nos por proximidade direta de ENDPOINT (esse teste falhava:
0 L_CORNER encontrados, 87 AMBIGUOUS de 363 "pontos"); ele usa a
INTERSECAO DOS EIXOS (retas infinitas) como ponto candidato a no', e so'
depois verifica, para cada parede, se sua ponta REAL fica perto o
suficiente desse ponto (dentro de meia espessura da parede vizinha + folga)
para contar como "termina aqui", ou se o eixo da parede so' PASSA por ali
(no meio do vao) para contar como "atravessa".

Toda a matemática é 2D (planta baixa); Z é ignorado (mesma convenção do
motor: blocagem é por fiada/altura, o grafo de paredes é sempre planar).
"""

import math

FREE_END = "FREE_END"
STRAIGHT_CONTINUATION = "STRAIGHT_CONTINUATION"
L_CORNER = "L_CORNER"
T_INTERSECTION = "T_INTERSECTION"
X_INTERSECTION = "X_INTERSECTION"
AMBIGUOUS = "AMBIGUOUS"

DEFAULT_TOL_CM = 2.0               # folga adicional além de meia espessura
DEFAULT_COLLINEAR_COS_TOL = 0.05   # |dot - (-1)| <= tol  (quase 180 graus)
DEFAULT_PERP_COS_TOL = 0.08        # |dot| <= tol         (quase 90 graus)
DEFAULT_CLUSTER_TOL_CM = 10.0      # funde pontos-candidato quase iguais

# LIMITACAO CONHECIDA (documentada em docs/BLOCK_DETERMINISM_AUDIT.md): em
# `classify_all` (censo completo, TODOS os pontos de uma vez), paredes-toco
# muito curtas (ex.: ~4-5cm, trechos entre aberturas) podem cair dentro da
# margem de meia-espessura de um no' vizinho de verdade e inflar
# artificialmente `n_terminating` ali, virando AMBIGUOUS onde o motor viu
# um no' limpo. Isso NAO invalida `classify_point` aplicada a um ponto
# especifico (uso principal do oraculo: arbitrar nos DIVERGENTES entre
# variantes, missao item 8/9) - so' afeta a comparacao agregada de censo
# completo (censo usado como referencia adicional, nao como veredito
# unico).


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _norm(v):
    n = math.hypot(v[0], v[1])
    if n < 1e-9:
        return (0.0, 0.0)
    return (v[0] / n, v[1] / n)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class OracleWall(object):
    __slots__ = ("index", "p0", "p1", "thickness_cm", "length_cm", "direction")

    def __init__(self, index, p0, p1, thickness_cm):
        self.index = index
        self.p0 = p0
        self.p1 = p1
        self.thickness_cm = thickness_cm
        self.length_cm = _dist(p0, p1)
        self.direction = _norm(_sub(p1, p0))

    def t_of(self, point):
        """Posição (cm) da projeção de `point` sobre o EIXO desta parede,
        medida a partir de p0 (pode ser negativa ou > length_cm - a reta é
        infinita)."""
        return _dot(_sub(point, self.p0), self.direction)


def walls_from_geom_rows(wall_geom_rows):
    """`wall_geom_rows`: lista de `(ax, ay, bx, by, thickness_cm)` já
    canônicos (`lib_det.wall_geom_key`) — usados como ENTRADA do oráculo
    para que ele nunca dependa de `wall_idx`."""
    out = []
    for i, row in enumerate(wall_geom_rows):
        ax, ay, bx, by, thickness_cm = row
        out.append(OracleWall(i, (ax, ay), (bx, by), thickness_cm))
    return out


def _line_intersection(wall_a, wall_b):
    """Interseção 2D de duas RETAS infinitas (eixos de `wall_a`/`wall_b`).
    None se paralelas (ou quase)."""
    x1, y1 = wall_a.p0
    dx1, dy1 = wall_a.direction
    x2, y2 = wall_b.p0
    dx2, dy2 = wall_b.direction
    denom = dx1 * dy2 - dy1 * dx2
    if abs(denom) < 1e-6:
        return None
    t = ((x2 - x1) * dy2 - (y2 - y1) * dx2) / denom
    return (x1 + dx1 * t, y1 + dy1 * t)


def _wall_margin_cm(other_thickness_cm, tol_cm):
    """Quanto a ponta REAL de uma parede pode estar deslocada do ponto de
    intersecao dos eixos, por ter sido esticada so' ate' a FACE da parede
    vizinha (nao ate' o eixo dela) - metade da espessura da OUTRA parede,
    mais uma folga de arredondamento/tolerancia geometrica."""
    return other_thickness_cm / 2.0 + tol_cm


def _find_candidate_points(walls, tol_cm):
    """Pontos-candidato a nó: interseção dos EIXOS (retas infinitas) de
    cada par de paredes NÃO PARALELAS cuja interseção cai perto o
    suficiente de onde as duas paredes de fato existem (dentro de meia
    espessura da outra + folga, para cada uma) - ou bem perto de uma PONTA,
    ou bem dentro do próprio vão (para o caso de cruzamento em midspan)."""
    raw_points = []
    n = len(walls)
    # Toda PONTA de toda parede entra como candidata direta - cobre
    # FREE_END (nenhuma outra parede por perto) e STRAIGHT_CONTINUATION
    # (2 pontas de paredes COLINEARES, cujos eixos sao paralelos e por
    # isso nunca geram interseccao de retas abaixo).
    for w in walls:
        if w.length_cm < 1e-6:
            continue
        raw_points.append(w.p0)
        raw_points.append(w.p1)
    for i in range(n):
        wi = walls[i]
        if wi.length_cm < 1e-6:
            continue
        for j in range(i + 1, n):
            wj = walls[j]
            if wj.length_cm < 1e-6:
                continue
            hit = _line_intersection(wi, wj)
            if hit is None:
                continue
            ti = wi.t_of(hit)
            tj = wj.t_of(hit)
            margin_i = _wall_margin_cm(wj.thickness_cm, tol_cm)
            margin_j = _wall_margin_cm(wi.thickness_cm, tol_cm)
            reaches_i = (-margin_i <= ti <= wi.length_cm + margin_i)
            reaches_j = (-margin_j <= tj <= wj.length_cm + margin_j)
            if reaches_i and reaches_j:
                raw_points.append(hit)
    return raw_points


def _cluster_points(points, tol_cm):
    """Une-encontra pontos a <= tol_cm um do outro; devolve os centróides."""
    n = len(points)
    if n == 0:
        return []
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(n):
        for j in range(i + 1, n):
            if _dist(points[i], points[j]) <= tol_cm:
                union(i, j)

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(points[i])

    centroids = []
    for members in groups.values():
        xs = [m[0] for m in members]
        ys = [m[1] for m in members]
        centroids.append((sum(xs) / len(xs), sum(ys) / len(ys)))
    return centroids


def _outward_dir(wall, end_index):
    if end_index == 0:
        return wall.direction
    return (-wall.direction[0], -wall.direction[1])


def _cluster_directions(dirs, cos_tol):
    groups = []
    for d in dirs:
        placed = False
        for g in groups:
            if _dot(d, g[0]) >= 1.0 - cos_tol:
                g.append(d)
                placed = True
                break
        if not placed:
            groups.append([d])
    return groups


def _wall_status_at_point(wall, point, other_max_thickness_cm, tol_cm):
    """Para UMA parede e UM ponto-candidato a nó: 'end0'/'end1' (termina
    ali), 'pass' (o eixo dela atravessa ali, em pleno vão) ou None (não
    tem nada a ver com este ponto)."""
    margin = _wall_margin_cm(other_max_thickness_cm, tol_cm)
    d0 = _dist(wall.p0, point)
    d1 = _dist(wall.p1, point)
    if d0 <= margin and d0 <= d1:
        return "end0"
    if d1 <= margin:
        return "end1"
    t = wall.t_of(point)
    perp = _dist(point, (wall.p0[0] + wall.direction[0] * t, wall.p0[1] + wall.direction[1] * t))
    if perp > margin:
        return None
    if margin <= t <= wall.length_cm - margin:
        return "pass"
    return None


def classify_point(walls, point, tol_cm=DEFAULT_TOL_CM,
                    collinear_cos_tol=DEFAULT_COLLINEAR_COS_TOL,
                    perp_cos_tol=DEFAULT_PERP_COS_TOL):
    """Classificação INDEPENDENTE de um ponto candidato a nó, examinando
    TODAS as paredes do projeto (não só o par que originou o ponto) —
    cobre nós de 3+ braços corretamente.

    Devolve dict: {kind, n_terminating, n_passing, n_unique_directions,
    terminating_walls, passing_walls, reason}."""
    max_thickness = max((w.thickness_cm for w in walls), default=0.0)

    terminating_arms = []  # (wall_idx, end_index)
    passing = []
    for w in walls:
        status = _wall_status_at_point(w, point, max_thickness, tol_cm)
        if status == "end0":
            terminating_arms.append((w.index, 0))
        elif status == "end1":
            terminating_arms.append((w.index, 1))
        elif status == "pass":
            passing.append(w)

    by_index = dict((w.index, w) for w in walls)
    term_dirs = [_outward_dir(by_index[w], e) for w, e in terminating_arms]
    pass_dirs = []
    for w in passing:
        pass_dirs.append(w.direction)
        pass_dirs.append((-w.direction[0], -w.direction[1]))

    all_dirs = term_dirs + pass_dirs
    n_term = len(terminating_arms)
    n_pass = len(passing)
    unique_dir_groups = _cluster_directions(all_dirs, collinear_cos_tol) if all_dirs else []

    result = {
        "point_cm": point,
        "n_terminating": n_term,
        "n_passing": n_pass,
        "n_unique_directions": len(unique_dir_groups),
        "terminating_walls": sorted(set(w for w, _e in terminating_arms)),
        "passing_walls": sorted(w.index for w in passing),
    }

    if n_term == 0 and n_pass == 0:
        result["kind"] = AMBIGUOUS
        result["reason"] = "nenhuma parede termina nem passa por este ponto"
        return result

    if n_pass == 0 and n_term == 1:
        result["kind"] = FREE_END
        result["reason"] = "1 ponta, nenhuma outra parede encosta"
        return result

    if n_pass >= 1 and n_term == 0 and n_pass < 2:
        result["kind"] = STRAIGHT_CONTINUATION
        result["reason"] = "apenas 1 parede passando, sem ponta encostando (ponto arbitrario do vao)"
        return result

    if n_term == 2 and n_pass == 0:
        dot = _dot(term_dirs[0], term_dirs[1])
        if dot <= -1.0 + collinear_cos_tol:
            result["kind"] = STRAIGHT_CONTINUATION
            result["reason"] = "2 pontas colineares e opostas (dot=%.4f)" % dot
        elif abs(dot) <= perp_cos_tol:
            result["kind"] = L_CORNER
            result["reason"] = "2 pontas quase perpendiculares (dot=%.4f)" % dot
        else:
            result["kind"] = AMBIGUOUS
            result["reason"] = "2 pontas em angulo nem colinear nem perpendicular (dot=%.4f)" % dot
        return result

    if n_term == 1 and n_pass == 1:
        dot = _dot(term_dirs[0], passing[0].direction)
        if abs(dot) <= perp_cos_tol:
            result["kind"] = T_INTERSECTION
            result["reason"] = "1 ponta perpendicular a 1 parede continua (dot=%.4f)" % dot
        else:
            result["kind"] = AMBIGUOUS
            result["reason"] = "1 ponta + 1 parede continua, mas nao perpendiculares (dot=%.4f)" % dot
        return result

    if n_term == 0 and n_pass == 2:
        dot = _dot(passing[0].direction, passing[1].direction)
        if abs(dot) <= perp_cos_tol:
            result["kind"] = X_INTERSECTION
            result["reason"] = "2 paredes continuas se cruzando quase perpendiculares (dot=%.4f)" % dot
        else:
            result["kind"] = AMBIGUOUS
            result["reason"] = "2 paredes cruzando mas nao perpendiculares (dot=%.4f)" % dot
        return result

    if n_term == 3 and n_pass == 0:
        for third in range(3):
            a, b = [i for i in range(3) if i != third]
            dot_ab = _dot(term_dirs[a], term_dirs[b])
            if dot_ab > -1.0 + collinear_cos_tol:
                continue
            dot_third = _dot(term_dirs[a], term_dirs[third])
            if abs(dot_third) > perp_cos_tol:
                continue
            result["kind"] = T_INTERSECTION
            result["reason"] = ("3 pontas: 2 colineares opostas (dot=%.4f) + 1 perpendicular "
                                 "(dot=%.4f) - parede continua quebrada em 2 trechos" % (dot_ab, dot_third))
            return result
        result["kind"] = AMBIGUOUS
        result["reason"] = "3 pontas, nenhum par colinear+perpendicular consistente com T"
        return result

    if n_term == 4 and n_pass == 0:
        remaining = list(range(4))
        pairs = []
        ok = True
        while remaining:
            i = remaining.pop(0)
            best_j, best_dot = None, None
            for j in remaining:
                dot = _dot(term_dirs[i], term_dirs[j])
                if best_dot is None or dot < best_dot:
                    best_dot, best_j = dot, j
            if best_j is None or best_dot > -1.0 + collinear_cos_tol:
                ok = False
                break
            pairs.append((i, best_j))
            remaining.remove(best_j)
        if ok and len(pairs) == 2:
            cross_dot = _dot(term_dirs[pairs[0][0]], term_dirs[pairs[1][0]])
            if abs(cross_dot) <= perp_cos_tol:
                result["kind"] = X_INTERSECTION
                result["reason"] = "4 pontas formando 2 pares colineares perpendiculares entre si (cross_dot=%.4f)" % cross_dot
                return result
        result["kind"] = AMBIGUOUS
        result["reason"] = "4 pontas, nao formam cruz consistente"
        return result

    result["kind"] = AMBIGUOUS
    result["reason"] = "combinacao nao coberta (%d pontas, %d passando)" % (n_term, n_pass)
    return result


def classify_all(wall_geom_rows, extra_query_points=None, tol_cm=DEFAULT_TOL_CM,
                  cluster_tol_cm=DEFAULT_CLUSTER_TOL_CM):
    """Classifica TODOS os pontos-candidato a nó de uma geometria de
    paredes: interseção dos EIXOS de cada par não-paralelo que realmente
    fica perto de onde as duas paredes existem (ver `_find_candidate_points`),
    mais quaisquer `extra_query_points` (pontos que o motor decidiu como nó
    e que o auditor quer conferir mesmo que não tenham sido gerados aqui)."""
    walls = walls_from_geom_rows(wall_geom_rows)
    raw_points = _find_candidate_points(walls, tol_cm)
    points = _cluster_points(raw_points, cluster_tol_cm)

    if extra_query_points:
        for p in extra_query_points:
            if not any(_dist(p, q) <= cluster_tol_cm for q in points):
                points.append(p)

    return [classify_point(walls, p, tol_cm=tol_cm) for p in points]
