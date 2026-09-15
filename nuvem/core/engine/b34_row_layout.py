# -*- coding: utf-8 -*-
"""FILEIRA DE B34 ENTRE FIADAS - reordena as pecas de um trecho ja' resolvido
para preservar o VAZADO MENOR entre fiadas (secao 56 de REGRAS_MODULACAO_BLOCOS.md).

Medido no projeto humano BUTANTA R08_LT (parede de 494 cm sem abertura): o
humano poe FILEIRAS de B34 nas DUAS pontas do trecho, e a fiada vizinha - que
anda meio modulo - encontra B34 sobre B34 (vazado menor sobre vazado menor). O
solver punha os B34 so' num lado, e o vazado menor caia sobre B39: 155 das 336
violacoes da secao 52 sao B34 x B39.

Este passe NAO muda o conteudo do trecho: mantem as MESMAS pecas (mesmos
codigos, mesma quantidade, mesmas pontas, mesmo comprimento total) e so' troca a
ORDEM delas dentro do trecho - o que muda de lugar sao as juntas internas e os
vazados. Uma ordem nova so' e' aceita quando:

1. reduz ESTRITAMENTE as violacoes do vazado menor (secao 52) do trecho;
2. nao aumenta a coincidencia de junta com as fiadas vizinhas (regra #1);
3. nao aumenta compensador em sequencia (regra #2).

Deterministico: trechos em ordem de chave fisica, arranjos enumerados em ordem
canonica de codigo, empate mantem a ordem original. Nenhum ElementId, parede ou
coordenada especifica entra aqui.
"""
import math

try:  # Revit / dubles dos testes
    from Autodesk.Revit.DB import XYZ
except Exception:  # pragma: no cover - so' fora do Revit sem dubles
    XYZ = None

from core.engine import small_void_alignment as _sva

FEET_PER_CM = 1.0 / 30.48
CM_PER_FEET = 30.48
B34_ROW_LAYOUT_ENABLED = True
MAX_ARRANGEMENTS = 4000
RUN_MAX_GAP_CM = 2.5
JOINT_COINCIDENCE_TOLERANCE_CM = 0.6


def _t_center_cm(cand, p0, wall_dir):
    o = cand["origin_world"]
    return ((o.X - p0.X) * wall_dir.X + (o.Y - p0.Y) * wall_dir.Y) * CM_PER_FEET


def _extent_cm(cand, p0, wall_dir):
    center = _t_center_cm(cand, p0, wall_dir)
    half = float(cand.get("length_cm") or 0.0) / 2.0
    return center - half, center + half


def _is_movable(cand, catalog):
    if cand.get("node_index") is not None:
        return False
    entry = (catalog or {}).get(cand.get("logical_code")) or {}
    if entry.get("is_channel"):
        return False
    return bool(cand.get("length_cm"))


def move_candidate_to(cand, t_center_cm, p0, wall_dir):
    """Move a peca ao longo do eixo para o novo centro `t_center_cm`, mantendo
    orientacao e celulas (translacao rigida)."""
    delta_ft = (t_center_cm - _t_center_cm(cand, p0, wall_dir)) * FEET_PER_CM
    if abs(delta_ft) < 1e-12:
        return cand
    dx, dy = wall_dir.X * delta_ft, wall_dir.Y * delta_ft
    o = cand["origin_world"]
    cand["origin_world"] = XYZ(o.X + dx, o.Y + dy, o.Z)
    cells = []
    for cell in cand.get("cells_world") or []:
        p = cell["point"]
        cells.append({"point": XYZ(p.X + dx, p.Y + dy, p.Z), "size_local": cell["size_local"]})
    cand["cells_world"] = cells
    return cand


def _runs_of_wall(pieces, p0, wall_dir, catalog):
    """Corridas contiguas de pecas moveis (gap <= RUN_MAX_GAP_CM)."""
    ordered = sorted(((_extent_cm(c, p0, wall_dir), c) for c in pieces), key=lambda item: (item[0][0], item[0][1]))
    runs = []
    current = []
    last_hi = None
    for (lo, hi), cand in ordered:
        if not _is_movable(cand, catalog):
            if len(current) > 1:
                runs.append(current)
            current, last_hi = [], None
            continue
        if last_hi is not None and lo - last_hi > RUN_MAX_GAP_CM:
            if len(current) > 1:
                runs.append(current)
            current = []
        current.append((lo, hi, cand))
        last_hi = hi
    if len(current) > 1:
        runs.append(current)
    return runs


def _distinct_arrangements(codes, limit):
    """Permutacoes DISTINTAS de uma lista de codigos, em ordem canonica."""
    counts = {}
    for code in codes:
        counts[code] = counts.get(code, 0) + 1
    keys = sorted(counts)
    out = []

    def walk(prefix, remaining):
        if len(out) >= limit:
            return
        if not any(remaining.values()):
            out.append(tuple(prefix))
            return
        for key in keys:
            if remaining.get(key):
                remaining[key] -= 1
                prefix.append(key)
                walk(prefix, remaining)
                prefix.pop()
                remaining[key] += 1
                if len(out) >= limit:
                    return

    walk([], dict(counts))
    return out


def _arrangement_count(codes):
    counts = {}
    for code in codes:
        counts[code] = counts.get(code, 0) + 1
    total = math.factorial(len(codes))
    for value in counts.values():
        total //= math.factorial(value)
    return total


class _Context(object):
    """Pecas das fiadas vizinhas (fora do trecho) para medir vazado e junta."""

    def __init__(self, course_candidates, catalog, run_ids, courses):
        self.catalog = catalog
        self.by_course = {}
        for course_index, cands in (course_candidates or {}).items():
            self.by_course[course_index] = [c for c in cands or () if id(c) not in run_ids]
        self.courses = sorted(courses)
        self.neighbours = sorted(set(
            ci for course in self.courses for ci in (course - 1, course + 1)
            if ci in self.by_course))


def _neighbour_pieces(context, p0, wall_dir, lo_cm, hi_cm, margin_cm=60.0):
    out = {}
    for ci in context.neighbours:
        rows = []
        for cand in context.by_course[ci]:
            lo, hi = _extent_cm(cand, p0, wall_dir)
            if hi >= lo_cm - margin_cm and lo <= hi_cm + margin_cm:
                rows.append((lo, hi, cand))
        out[ci] = rows
    return out


def _joints_of(rows):
    joints = []
    ordered = sorted(rows, key=lambda item: (item[0], item[1]))
    for (a_lo, a_hi, _a), (b_lo, _b_hi, _b) in zip(ordered, ordered[1:]):
        if 0.0 <= b_lo - a_hi <= RUN_MAX_GAP_CM:
            joints.append((a_hi + b_lo) / 2.0)
    return joints


def _compensator_run_excess(codes, catalog):
    excess = 0
    streak = 0
    for code in codes:
        entry = (catalog or {}).get(code) or {}
        if entry.get("is_compensator"):
            streak += 1
        else:
            excess += max(0, streak - 1)
            streak = 0
    return excess + max(0, streak - 1)


def _small_void_points(cand):
    """Posicoes possiveis do vazado menor: a atual e a espelhada pelo centro
    (o passe de orientacao da secao 52 roda DEPOIS e escolhe uma das duas).
    Peca de no' nao gira: so' a atual."""
    cell = _sva.candidate_small_cell(cand)
    if cell is None:
        return []
    point = (cell["point"].X, cell["point"].Y)
    if cand.get("node_index") is not None or not _sva._is_orientable_small_void_piece(cand):
        return [point]
    o = cand["origin_world"]
    return [point, (2.0 * o.X - point[0], 2.0 * o.Y - point[1])]


def _covered_by(pieces, x_ft, y_ft, catalog):
    return [c for c in pieces if _sva._is_hollow_masonry(c, catalog) and _sva._contains(c, x_ft, y_ft)]


def _offers_small_void(cand, x_ft, y_ft, tol_ft):
    cell = _sva.candidate_small_cell(cand)
    if cell is None:
        return False
    for px, py in _small_void_points(cand):
        if abs(px - x_ft) <= 0 and abs(py - y_ft) <= 0:
            return True
    # ponto dentro da celula menor em alguma das orientacoes possiveis
    for px, py in _small_void_points(cand):
        size = cell["size_local"]
        # distancia no eixo da peca ate' o centro da celula naquela orientacao
        dx, dy = x_ft - px, y_ft - py
        xd = cand["x_dir"]
        yd = cand.get("y_dir") or XYZ(-xd.Y, xd.X, 0.0)
        u = dx * xd.X + dy * xd.Y
        v = dx * yd.X + dy * yd.Y
        if abs(u) <= size[0] / 2.0 + tol_ft and abs(v) <= size[1] / 2.0 + tol_ft:
            return True
    return False


def _violations_for(pieces_at, neighbours, tol_ft, catalog):
    """Violacoes do vazado menor que NENHUMA orientacao resolve, envolvendo as
    pecas do trecho, nas duas direcoes (o vazado da peca e o das vizinhas)."""
    count = 0
    for _ci, rows in neighbours.items():
        neighbour_pieces = [n for _l, _h, n in rows]
        for _lo, _hi, cand, _code in pieces_at:
            points = _small_void_points(cand)
            if not points or not _sva._is_orientable_small_void_piece(cand):
                continue
            ok = False
            for x_ft, y_ft in points:
                hits = _covered_by(neighbour_pieces, x_ft, y_ft, catalog)
                if not hits or any(_offers_small_void(h, x_ft, y_ft, tol_ft) for h in hits):
                    ok = True
                    break
            if not ok:
                count += 1
        run_pieces = [c for _lo, _hi, c, _code in pieces_at]
        for _l, _h, neighbour in rows:
            points = _small_void_points(neighbour)
            if not points or not _sva._is_orientable_small_void_piece(neighbour):
                continue
            ok = False
            for x_ft, y_ft in points:
                hits = _covered_by(run_pieces, x_ft, y_ft, catalog)
                if not hits or any(_offers_small_void(h, x_ft, y_ft, tol_ft) for h in hits):
                    ok = True
                    break
            if not ok:
                count += 1
    return count


def _place(run, order, p0, wall_dir, joint_cm):
    """(lo, hi, cand, code) de cada peca na ordem `order`, do inicio do trecho."""
    by_code = {}
    for _lo, _hi, cand in run:
        by_code.setdefault(cand["logical_code"], []).append(cand)
    start = run[0][0]
    placed = []
    cursor = start
    for code in order:
        cand = by_code[code].pop(0)
        length = float(cand.get("length_cm") or 0.0)
        placed.append((cursor, cursor + length, cand, code))
        cursor += length + joint_cm
    return placed


def _apply(placed, p0, wall_dir):
    for lo, hi, cand, _code in placed:
        move_candidate_to(cand, (lo + hi) / 2.0, p0, wall_dir)


def reorder_b34_rows(course_candidates, walls_to_create, catalog, joint_cm=1.0,
                     tolerance_cm=_sva.SMALL_VOID_ALIGN_TOLERANCE_CM, max_arrangements=MAX_ARRANGEMENTS):
    """Reordena as corridas para preservar o vazado menor entre fiadas.
    Devolve {"runs": n, "reordered": k, "skipped_large": s}."""
    from core.engine.wall_stepper import _wall_axis_and_length
    tol_ft = tolerance_cm * FEET_PER_CM
    groups = {}
    for course_index in sorted(course_candidates or {}):
        for cand in course_candidates[course_index] or ():
            wall_idx = cand.get("wall_idx")
            if wall_idx is None or not _is_movable(cand, catalog):
                continue
            key = (wall_idx, id(cand))
            groups.setdefault(key[0], {}).setdefault(id(cand), [cand, set()])[1].add(course_index)
    summary = {"runs": 0, "reordered": 0, "skipped_large": 0}
    for wall_idx in sorted(groups):
        if wall_idx >= len(walls_to_create or ()):
            continue
        p0, _p1, wall_dir, _len_ft, _thickness = _wall_axis_and_length(walls_to_create, wall_idx)
        by_courses = {}
        for cand, courses in groups[wall_idx].values():
            by_courses.setdefault(frozenset(courses), []).append(cand)
        for courses in sorted(by_courses, key=lambda cs: (sorted(cs), len(cs))):
            pieces = by_courses[courses]
            for run in _runs_of_wall(pieces, p0, wall_dir, catalog):
                summary["runs"] += 1
                codes = [cand["logical_code"] for _lo, _hi, cand in run]
                if len(set(codes)) < 2:
                    continue
                if _arrangement_count(codes) > max_arrangements:
                    summary["skipped_large"] += 1
                    continue
                run_ids = set(id(cand) for _lo, _hi, cand in run)
                context = _Context(course_candidates, catalog, run_ids, courses)
                if not context.neighbours:
                    continue
                neighbours = _neighbour_pieces(context, p0, wall_dir, run[0][0], run[-1][1])
                current_order = tuple(codes)
                span = run[-1][1] - run[0][0]
                lengths = sum(float(cand.get("length_cm") or 0.0) for _lo, _hi, cand in run)
                run_joint_cm = (span - lengths) / max(1, len(run) - 1)
                if run_joint_cm < 0.5 or run_joint_cm > 3.0:
                    continue  # espacamento irregular: nao e' uma corrida de juntas normais
                best = None
                current_score = None
                for order in _distinct_arrangements(codes, max_arrangements):
                    placed = _place(run, order, p0, wall_dir, run_joint_cm)
                    if abs(placed[-1][1] - run[-1][1]) > 0.5:
                        continue  # a ordem nova nao fecha no mesmo envelope
                    violations = _violations_for(placed, neighbours, tol_ft, catalog)
                    joints = _joints_of([(lo, hi, cand) for lo, hi, cand, _c in placed])
                    coincidences = 0
                    for ci, rows in neighbours.items():
                        others = _joints_of(rows)
                        for joint in joints:
                            if any(abs(joint - other) <= JOINT_COINCIDENCE_TOLERANCE_CM for other in others):
                                coincidences += 1
                    score = (violations, coincidences, _compensator_run_excess(order, catalog))
                    if order == current_order:
                        current_score = score
                    if best is None or score < best[0] or (score == best[0] and order == current_order):
                        best = (score, order, placed)
                if best is None or current_score is None:
                    continue
                if best[1] == current_order or best[0] >= current_score:
                    continue
                _apply(best[2], p0, wall_dir)
                summary["reordered"] += 1
    return summary
