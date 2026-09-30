# -*- coding: utf-8 -*-
"""PRISMA POR AREA LIVRE COMUM (secao 85 de REGRAS_MODULACAO_BLOCOS.md,
correcao do usuario em 2026-09-29).

"Preservar o prisma" = manter o alinhamento vertical REAL dos vaos internos
(celulas) dos blocos entre as fiadas - por eles passam graute e vergalhoes,
principalmente nas laterais das janelas. Centro de celula "parecido" nao prova
passagem: a regua mede a AREA LIVRE COMUM entre a celula de uma fiada e a da
fiada vizinha, pela geometria real das familias (`cells_world` de cada peca,
com rotacao e espelhamento ja' aplicados), e a coluna inteira junto de cada
jamba.

- Interface = duas fiadas vizinhas da mesma parede, ambas de bloco vazado na
  posicao da celula. Canaleta (U) nao tem celula vertical no catalogo: a
  interface com ela nao entra na conta (nao se declara passagem atraves dela);
  a FASE atraves da canaleta e' medida a parte (fiada de baixo x fiada de cima).
- Celula interrompida = cai sobre peca macica (compensador), sobre uma junta,
  ou nao tem sobreposicao nenhuma com celula da vizinha.
- Celula estreita = a largura livre comum ao longo da parede e' menor que
  `PRISM_MIN_COMMON_WIDTH_CM`, a MENOR dimensao de celula do catalogo real
  (8,99 cm - vazado menor do B34 na espessura). E' um limiar geometrico
  derivado das familias, NAO um dimensionamento de armadura: diametro/folga do
  projeto estrutural nao sao inventados aqui.
- Coluna da jamba = a coluna de celulas mais proxima de cada borda de abertura,
  seguida fiada a fiada nas fiadas em que a abertura esta' ativa; a largura
  comum dela e' a intersecao de todas as celulas da coluna.

- Coluna contínua (`column_census`) = a celula e TODAS as que a continuam,
  fiada a fiada, na altura inteira da parede (abaixo e acima de janela, acima
  de porta; canaleta e vao atravessados so' pela fase), com a intersecao
  ACUMULADA >= limiar. E' a regua do pedido "uma correcao so' conta se nao
  transferir a quebra do prisma para outro ponto": reduzir quebras numa
  interface enquanto a coluna quebra noutra fiada nao cria passagem.

Modulo puro (so' geometria dos candidatos); usado pela secao 84 (restricao
dura da faixa de jamba), pela auditoria e pelo relatorio.
"""
import bisect

CM_PER_FT = 30.48
PRISM_CELL_MIN_DIMENSION_CM = 8.99
# SECAO 85.9 (2026-09-30): tolerancia GEOMETRICA do limiar (0,5 mm). Dois B34
# em amarracao com o vazado menor sobre o vazado menor (desencontro de 20 cm,
# um virado para cada lado) deixam 10,759 - 1,773 = 8,986 cm livres - 0,04 mm
# abaixo de 8,99, ruido das celulas medidas nas familias (3-4 casas). Sem a
# tolerancia a regua nunca aceitava a grade de B34 do desenho do usuario (W4,
# pilarete 945-1144) e contava toda coluna de vazado menor como quebrada. O
# vazado menor sobre vazado PRINCIPAL continua recusado pela regra 85.8, que
# nao depende do limiar.
PRISM_WIDTH_TOLERANCE_CM = 0.05
PRISM_MIN_COMMON_WIDTH_CM = PRISM_CELL_MIN_DIMENSION_CM - PRISM_WIDTH_TOLERANCE_CM
JAMB_COLUMN_REACH_CM = 30.0
JOINT_MAX_GAP_CM = 2.5
# Secao 85.8 (correcao do usuario, 2026-09-30): vazado MENOR do B34 (10,75 cm ao
# longo da parede) sobre vazado PRINCIPAL (> 13 cm) nao forma coluna, mesmo com
# 9 cm de area comum; vazado menor x menor e menor x central do B54 (12,5) valem.
SMALL_CELL_MAX_CM = 11.5
MAIN_CELL_MIN_CM = 13.0


def cells_compatible(a, b):
    wa, wb = a[1] - a[0], b[1] - b[0]
    return not (min(wa, wb) < SMALL_CELL_MAX_CM and max(wa, wb) > MAIN_CELL_MIN_CM)
FACE_ALIGN_CM = 1e-6


def _is_channel_code(code):
    return str(code or "").upper().startswith("CHANNEL")


def _axis(walls_to_create, wall_idx):
    from core.engine.wall_stepper import _wall_axis_and_length
    p0, _p1, wall_dir, length_ft, thickness_ft = _wall_axis_and_length(walls_to_create, wall_idx)
    return p0, wall_dir, length_ft * CM_PER_FT, thickness_ft * CM_PER_FT


def piece_cells(cand, p0, wall_dir):
    """[(t_lo, t_hi, n_lo, n_hi)] em cm: retangulo de cada celula da peca no
    referencial da parede (t ao longo do eixo, n na espessura), lido de
    `cells_world` (centro real) e `size_local` (x ao longo da peca, y na
    espessura) - peca perpendicular a' parede troca as dimensoes."""
    out = []
    xd = cand.get("x_dir")
    along = True
    if xd is not None:
        along = abs(xd.X * wall_dir.X + xd.Y * wall_dir.Y) >= 0.5
    nx, ny = -wall_dir.Y, wall_dir.X
    for cell in cand.get("cells_world") or []:
        pt = cell["point"]
        t = ((pt.X - p0.X) * wall_dir.X + (pt.Y - p0.Y) * wall_dir.Y) * CM_PER_FT
        n = ((pt.X - p0.X) * nx + (pt.Y - p0.Y) * ny) * CM_PER_FT
        sx = float(cell["size_local"][0]) * CM_PER_FT
        sy = float(cell["size_local"][1]) * CM_PER_FT
        a, b = (sx, sy) if along else (sy, sx)
        out.append((t - a / 2.0, t + a / 2.0, n - b / 2.0, n + b / 2.0))
    return out


def wall_rows(course_candidates, walls_to_create, wall_idx):
    """{fiada: [(lo, hi, code, cells)]} das pecas DA parede, ordenadas por lo."""
    from core.engine.wall_stepper import _candidate_extent_on_wall_axis
    p0, wall_dir, _length, _thick = _axis(walls_to_create, wall_idx)
    rows = {}
    for ci in sorted(course_candidates or {}):
        items = []
        for cand in course_candidates[ci] or ():
            if cand.get("wall_idx") != wall_idx:
                continue
            lo, hi = _candidate_extent_on_wall_axis(cand, p0, wall_dir)
            items.append((lo, hi, cand.get("logical_code"), piece_cells(cand, p0, wall_dir)))
        items.sort(key=lambda it: (it[0], it[1]))
        if items:
            rows[ci] = items
    return rows


def _covering(items, t):
    for it in items:
        if it[0] - FACE_ALIGN_CM <= t <= it[1] + FACE_ALIGN_CM:
            return it
    return None


def _in_joint(items, t):
    prev = None
    for it in items:
        if it[0] > t:
            return prev is not None and it[0] - prev[1] <= JOINT_MAX_GAP_CM
        prev = it
    return False


def common_rect(a, b):
    """(largura ao longo da parede, largura na espessura) comuns a duas celulas."""
    return (max(0.0, min(a[1], b[1]) - max(a[0], b[0])), max(0.0, min(a[3], b[3]) - max(a[2], b[2])))


def cell_continuity(cell, items):
    """('ok'|'narrow'|'interrupted'|'skip', largura comum, area comum) da celula
    contra a fileira vizinha."""
    tc = (cell[0] + cell[1]) / 2.0
    host = _covering(items, tc)
    if host is None:
        if _in_joint(items, tc):
            return "interrupted", 0.0, 0.0
        return "skip", None, None  # vao de abertura ou fora da parede
    if _is_channel_code(host[2]):
        return "skip", None, None
    best = (0.0, 0.0)
    for it in items:
        if it[1] < cell[0] or it[0] > cell[1]:
            continue
        for other in it[3]:
            if not cells_compatible(cell, other):
                continue
            w, d = common_rect(cell, other)
            if w * d > best[0] * best[1]:
                best = (w, d)
    if best[0] <= 0.0 or best[1] <= 0.0:
        return "interrupted", 0.0, 0.0
    status = "ok" if best[0] >= PRISM_MIN_COMMON_WIDTH_CM - 1e-6 else "narrow"
    return status, round(best[0], 2), round(best[0] * best[1], 1)


def _host(items, t):
    return _covering(items, t)


def _target_course(rows, ci, dj, t):
    """Fiada vizinha no sentido `dj` para a celula em `t`, atravessando a
    canaleta (U, sem celula vertical no catalogo): a FASE da coluna e' medida
    contra a primeira fiada de bloco vazado alem dela. A passagem de graute
    atraves da U nao e' declarada - so' o alinhamento abaixo x acima."""
    cj = ci + dj
    crossed = 0
    while cj in rows:
        host = _host(rows[cj], t)
        if host is None or not _is_channel_code(host[2]):
            return cj, crossed
        crossed += 1
        cj += dj
    return None, crossed


def wall_prism_report(course_candidates, walls_to_create, openings_per_wall, wall_idx,
                      course_height_cm=20.0, first_course_z_cm=1.0, base_z_ft=0.0):
    rows = wall_rows(course_candidates, walls_to_create, wall_idx)
    rep = {"wall_idx": wall_idx, "cells": 0, "ok": 0, "narrow": 0, "interrupted": 0, "worst": [],
           "jamb_columns": [], "common_width_sum_cm": 0.0}
    courses = sorted(rows)
    for ci in courses:
        for dj in (-1, 1):
            for lo, hi, code, cells in rows[ci]:
                if _is_channel_code(code):
                    continue
                for cell in cells:
                    tc = (cell[0] + cell[1]) / 2.0
                    cj, crossed = _target_course(rows, ci, dj, tc)
                    if cj is None:
                        continue
                    status, width, area = cell_continuity(cell, rows[cj])
                    if status == "skip":
                        continue
                    rep["cells"] += 1
                    rep[status] += 1
                    rep["common_width_sum_cm"] += width or 0.0
                    if status != "ok" and len(rep["worst"]) < 400:
                        rep["worst"].append({"course": ci, "other": cj, "through_channel": crossed, "t": round(tc, 2),
                                             "code": code, "status": status, "common_width_cm": width,
                                             "common_area_cm2": area})
    rep["common_width_sum_cm"] = round(rep["common_width_sum_cm"], 1)
    ops = (openings_per_wall or [])
    for op in (ops[wall_idx] if wall_idx < len(ops) else None) or ():
        t_lo, t_hi = float(op[0]) * CM_PER_FT, float(op[1]) * CM_PER_FT
        sill = (float(op[2]) - base_z_ft) * CM_PER_FT
        head = (float(op[3]) - base_z_ft) * CM_PER_FT
        active = [ci for ci in courses
                  if first_course_z_cm + course_height_cm * ci < head - 0.5
                  and first_course_z_cm + course_height_cm * ci + course_height_cm - 1.0 > sill + 0.5]
        for edge, side in ((t_lo, -1), (t_hi, 1)):
            col = jamb_column(rows, edge, side, courses)
            col["opening_courses"] = active
            rep["jamb_columns"].append(col)
    return rep


def jamb_column(rows, edge, side, courses):
    """Coluna de celulas junto da borda `edge` (lado `side` = +1 pecas depois
    da borda, -1 antes) em TODA a altura da parede (fiadas abaixo e acima da
    abertura inclusive; canaleta atravessada so' pela fase): a coluna parte da
    celula mais proxima da borda numa fiada da abertura e segue, fiada a fiada,
    a celula que mais se sobrepoe a ela. Largura comum = intersecao da coluna
    inteira; `broken_at` = fiadas onde nenhuma celula continua a coluna."""
    out = {"edge_cm": round(edge, 1), "side": side, "courses": list(courses), "common_width_cm": None,
           "common_area_cm2": None, "broken_at": [], "narrow_at": []}
    seq = [ci for ci in courses if ci in rows]
    if not seq:
        return out
    seed = None
    for ci in seq:
        for lo, hi, code, cells in rows[ci]:
            if _is_channel_code(code):
                continue
            for cell in cells:
                dist = (cell[0] - edge) if side > 0 else (edge - cell[1])
                if -0.5 <= dist <= JAMB_COLUMN_REACH_CM and (seed is None or dist < seed[0]):
                    seed = (dist, cell)
        if seed is not None:
            break
    if seed is None:
        return out
    col = seed[1]
    prev_cell = seed[1]
    for ci in seq:
        best = None
        channel_only = True
        for lo, hi, code, cells in rows[ci]:
            if hi < col[0] - 1.0 or lo > col[1] + 1.0:
                continue
            if _is_channel_code(code):
                continue
            channel_only = False
            for cell in cells:
                if prev_cell is not None and not cells_compatible(prev_cell, cell):
                    continue
                w, d = common_rect(col, cell)
                if w > 0.0 and d > 0.0 and (best is None or w * d > best[0]):
                    best = (w * d, cell)
        host = _host(rows[ci], (col[0] + col[1]) / 2.0)
        if host is not None and _is_channel_code(host[2]):
            continue  # canaleta: so' fase
        if best is None:
            if host is None and channel_only and not _in_joint(rows[ci], (col[0] + col[1]) / 2.0):
                continue  # vao da abertura nesta fiada
            out["broken_at"].append(ci)
            continue
        cell = best[1]
        prev_cell = cell
        col = (max(col[0], cell[0]), min(col[1], cell[1]), max(col[2], cell[2]), min(col[3], cell[3]))
        if col[1] - col[0] < PRISM_MIN_COMMON_WIDTH_CM - 1e-6:
            out["narrow_at"].append(ci)
    if not out["broken_at"]:
        out["common_width_cm"] = round(col[1] - col[0], 2)
        out["common_area_cm2"] = round((col[1] - col[0]) * (col[3] - col[2]), 1)
    return out


def prism_census(course_candidates, walls_to_create, openings_per_wall, base_z_ft=0.0):
    """Totais da planta + por parede: celulas ok / estreitas / interrompidas e
    colunas de jamba (continuas com largura >= limiar, estreitas, quebradas)."""
    total = {"cells": 0, "ok": 0, "narrow": 0, "interrupted": 0, "jamb_columns": 0, "jamb_ok": 0,
             "jamb_narrow": 0, "jamb_broken": 0, "jamb_full_width": 0, "common_width_sum_cm": 0.0,
             "min_common_width_cm": PRISM_MIN_COMMON_WIDTH_CM, "walls": []}
    walls = set(c.get("wall_idx") for lst in (course_candidates or {}).values() for c in lst or ()
                if isinstance(c.get("wall_idx"), int))
    for wi in sorted(walls):
        if wi >= len(walls_to_create or ()):
            continue
        rep = wall_prism_report(course_candidates, walls_to_create, openings_per_wall, wi, base_z_ft=base_z_ft)
        for key in ("cells", "ok", "narrow", "interrupted", "common_width_sum_cm"):
            total[key] += rep[key]
        for col in rep["jamb_columns"]:
            if not col["courses"]:
                continue
            total["jamb_columns"] += 1
            if col["broken_at"]:
                total["jamb_broken"] += 1
            elif col["common_width_cm"] is not None and col["common_width_cm"] >= PRISM_MIN_COMMON_WIDTH_CM - 1e-6:
                total["jamb_ok"] += 1
                if col["common_width_cm"] >= 13.9:
                    total["jamb_full_width"] += 1
            else:
                total["jamb_narrow"] += 1
        total["walls"].append({"wall_idx": wi, "cells": rep["cells"], "ok": rep["ok"], "narrow": rep["narrow"],
                               "interrupted": rep["interrupted"], "common_width_sum_cm": rep["common_width_sum_cm"],
                               "jamb_columns": rep["jamb_columns"], "worst": rep["worst"][:60]})
    total["common_width_sum_cm"] = round(total["common_width_sum_cm"], 1)
    return total


def _near(rows, los, ci, a, b):
    i = max(0, bisect.bisect_left(los[ci], a - 60.0))
    for it in rows[ci][i:]:
        if it[0] > b + 1.0:
            break
        if it[1] >= a - 1.0:
            yield it


def _column_continuous(rows, los, ci, cell):
    """True se a coluna que passa pela `cell` da fiada `ci` fica com largura
    comum acumulada >= limiar em TODAS as fiadas da parede."""
    for dj in (-1, 1):
        col = cell
        prev = cell
        cj = ci + dj
        while cj in rows:
            mid = (col[0] + col[1]) / 2.0
            host = _covering(rows[cj], mid)
            if host is None:
                if _in_joint(rows[cj], mid):
                    return False  # vazado sobre a junta
                cj += dj
                continue  # vao da abertura / fora da parede: so' a fase segue
            if _is_channel_code(host[2]):
                cj += dj
                continue  # canaleta: so' fase
            best = None
            for it in _near(rows, los, cj, col[0], col[1]):
                for other in it[3]:
                    if not cells_compatible(prev, other):
                        continue
                    w, d = common_rect(col, other)
                    if w > 0.0 and d > 0.0 and (best is None or w * d > best[0]):
                        best = (w * d, other)
            if best is None:
                return False  # peca macica (compensador), nenhuma celula ou vazado menor x principal
            o = best[1]
            prev = o
            col = (max(col[0], o[0]), min(col[1], o[1]), max(col[2], o[2]), min(col[3], o[3]))
            if col[1] - col[0] < PRISM_MIN_COMMON_WIDTH_CM - 1e-6:
                return False
            cj += dj
    return True


def _stacked_joints(rows, min_courses=3):
    """Juntas verticais (faces encostadas a ate' JOINT_MAX_GAP_CM) que sobem
    `min_courses`+ fiadas seguidas na mesma posicao - todas, sem isencao: e' a
    face 'amarracao' da mesma regua (vazado alinhado nao pode vir de junta a
    prumo)."""
    faces = {}
    for ci in rows:
        items = rows[ci]
        faces[ci] = sorted((a[1] + b[0]) / 2.0 for a, b in zip(items, items[1:]) if b[0] - a[1] <= JOINT_MAX_GAP_CM)

    def has(c, x):
        lst = faces.get(c) or []
        i = bisect.bisect_left(lst, x - 0.6)
        return i < len(lst) and lst[i] <= x + 0.6
    n = 0
    for ci in sorted(faces):
        for x in faces[ci]:
            if has(ci - 1, x):
                continue
            length, c2 = 1, ci
            while has(c2 + 1, x):
                length += 1
                c2 += 1
            if length >= min_courses:
                n += 1
    return n


def column_census(course_candidates, walls_to_create, wall_indices=None):
    """Celulas cuja COLUNA inteira e' continua (intersecao acumulada >= limiar),
    celulas quebradas e juntas a prumo em 3+ fiadas - por parede e no total."""
    out = {"cells": 0, "continuous": 0, "broken": 0, "stacked_joints_3plus": 0, "walls": {}}
    if wall_indices is None:
        wall_indices = sorted(set(c.get("wall_idx") for lst in (course_candidates or {}).values()
                                  for c in lst or () if isinstance(c.get("wall_idx"), int)))
    for wi in wall_indices:
        if wi >= len(walls_to_create or ()):
            continue
        rows = wall_rows(course_candidates, walls_to_create, wi)
        if not rows:
            continue
        los = dict((c, [it[0] for it in rows[c]]) for c in rows)
        tot = cont = 0
        for ci in sorted(rows):
            for _lo, _hi, code, cells in rows[ci]:
                if _is_channel_code(code):
                    continue
                for cell in cells:
                    tot += 1
                    if _column_continuous(rows, los, ci, cell):
                        cont += 1
        st = _stacked_joints(rows)
        out["cells"] += tot
        out["continuous"] += cont
        out["broken"] += tot - cont
        out["stacked_joints_3plus"] += st
        out["walls"][wi] = {"cells": tot, "continuous": cont, "broken": tot - cont, "stacked_joints_3plus": st}
    return out
