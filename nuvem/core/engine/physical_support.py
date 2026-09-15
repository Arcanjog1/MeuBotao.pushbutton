# -*- coding: utf-8 -*-
"""APOIO FISICO ENTRE FIADAS - validador somente leitura (2026-09-15, missao
BUTANTA; REGRAS_MODULACAO_BLOCOS.md secao 53).

Uma peca da fiada c (c >= 1) precisa assentar na fiada c-1. Mede-se, ao longo
do eixo da propria peca e na linha de centro dela, quanto do comprimento cai
sobre alguma peca da fiada de baixo (de qualquer parede) e quanto cai sobre um
VAO ativo naquela fiada (canaleta/verga sobre abertura nao e' "sem apoio":
e' reforco, auditado pela estrategia de aberturas). A peca e' reportada
quando o apoio e' menor que `SUPPORT_MIN_FRACTION` E o trecho sobre vao
tambem e' menor que essa fracao - a mesma regua usada na comparacao com o
projeto humano BUTANTA R08_LT (humano: 9 pecas em 34 paredes / 13 fiadas, todas
em pilarete de passagem e topo de vao; lote anterior do botao: 116).

- `UNSUPPORTED_SMALL_BLOCK`: B19/C09/C04 (peca pequena "voando").
- `UNSUPPORTED_BLOCK`: demais pecas.

Nada e' alterado. Deterministico: ordem por (fiada, chave fisica). Nenhum
ElementId, parede ou coordenada especifica.
"""
import math

SUPPORT_MIN_FRACTION = 0.5
SMALL_BLOCK_MAX_LENGTH_CM = 19.5
_GRID_CM = 40.0
_FT_TO_CM = 30.48


def _axis(candidate):
    xd = candidate["x_dir"]
    n = math.hypot(xd.X, xd.Y) or 1.0
    return xd.X / n, xd.Y / n


def _bbox_cm(candidate):
    o = candidate["origin_world"]
    ux, uy = _axis(candidate)
    half_len = float(candidate.get("length_cm") or 0.0) / 2.0
    half_w = float(candidate.get("width_cm") or 0.0) / 2.0
    hx = abs(ux) * half_len + abs(uy) * half_w
    hy = abs(uy) * half_len + abs(ux) * half_w
    cx, cy = o.X * _FT_TO_CM, o.Y * _FT_TO_CM
    return cx - hx, cy - hy, cx + hx, cy + hy


def _merge(intervals):
    out = []
    for a, b in sorted(intervals):
        if out and a <= out[-1][1] + 1e-6:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def _covered_along(piece, others):
    """Intervalos (u local da peca, cm) cobertos por `others` na linha de
    centro de `piece`. Cada vizinho e' tratado como retangulo orientado."""
    o = piece["origin_world"]
    px, py = o.X * _FT_TO_CM, o.Y * _FT_TO_CM
    ux, uy = _axis(piece)
    half = float(piece.get("length_cm") or 0.0) / 2.0
    spans = []
    for other in others:
        oo = other["origin_world"]
        ox, oy = oo.X * _FT_TO_CM, oo.Y * _FT_TO_CM
        vx, vy = _axis(other)
        ohl = float(other.get("length_cm") or 0.0) / 2.0
        ohw = float(other.get("width_cm") or 0.0) / 2.0
        # linha p(u) = (px, py) + u * (ux, uy); no local do vizinho:
        # a(u) = a0 + u * da (longitudinal), b(u) = b0 + u * db (transversal)
        rx, ry = px - ox, py - oy
        a0, da = rx * vx + ry * vy, ux * vx + uy * vy
        b0, db = -rx * vy + ry * vx, -ux * vy + uy * vx
        lo, hi = -half, half
        for c0, dc, lim in ((a0, da, ohl), (b0, db, ohw)):
            if abs(dc) < 1e-9:
                if abs(c0) > lim + 1e-6:
                    lo, hi = 1.0, 0.0
                    break
                continue
            t1, t2 = (-lim - c0) / dc, (lim - c0) / dc
            lo, hi = max(lo, min(t1, t2)), min(hi, max(t1, t2))
        if hi - lo > 1e-6:
            spans.append((lo, hi))
    return _merge(spans)


def _over_openings(piece, walls_to_create, openings_per_wall, z_lo, z_hi, wall_axis):
    """Intervalos (u local, cm) da linha de centro de `piece` que caem num vao
    ativo na faixa [z_lo, z_hi) (ft) da parede dona ou secundaria."""
    spans = []
    o = piece["origin_world"]
    px, py = o.X * _FT_TO_CM, o.Y * _FT_TO_CM
    ux, uy = _axis(piece)
    half = float(piece.get("length_cm") or 0.0) / 2.0
    for key in ("wall_idx", "secondary_wall_idx"):
        wi = piece.get(key)
        if wi is None or wi >= len(openings_per_wall or []):
            continue
        p0x, p0y, dx, dy = wall_axis(wi)
        dot = ux * dx + uy * dy
        if abs(dot) < 0.5:
            continue  # peca atravessando a parede pela largura
        t_center = (px - p0x) * dx + (py - p0y) * dy
        for t_lo, t_hi, sill, head in openings_per_wall[wi] or ():
            if min(head, z_hi) - max(sill, z_lo) <= 1e-6:
                continue
            a, b = t_lo * _FT_TO_CM, t_hi * _FT_TO_CM
            u1, u2 = (a - t_center) / dot, (b - t_center) / dot
            lo, hi = max(-half, min(u1, u2)), min(half, max(u1, u2))
            if hi - lo > 1e-6:
                spans.append((lo, hi))
    return _merge(spans)


def unsupported_pieces(course_candidates, walls_to_create, openings_per_wall, course_band_ft,
                       min_fraction=SUPPORT_MIN_FRACTION):
    """Lista deterministica de {code, course, support, over_opening, point_cm,
    wall_idx, placement_reason, kind}. `course_band_ft(ci)` devolve a faixa
    vertical (z_lo, z_hi) em ft ocupada pela fiada `ci`."""
    axes = {}

    def wall_axis(wi):
        if wi not in axes:
            line = walls_to_create[wi][0]
            p0, p1 = line.GetEndPoint(0), line.GetEndPoint(1)
            dx, dy = p1.X - p0.X, p1.Y - p0.Y
            n = math.hypot(dx, dy) or 1.0
            axes[wi] = (p0.X * _FT_TO_CM, p0.Y * _FT_TO_CM, dx / n, dy / n)
        return axes[wi]

    buckets = {}
    for ci in sorted(course_candidates or {}):
        for cand in course_candidates[ci] or ():
            x0, y0, x1, y1 = _bbox_cm(cand)
            for gx in range(int(math.floor(x0 / _GRID_CM)), int(math.floor(x1 / _GRID_CM)) + 1):
                for gy in range(int(math.floor(y0 / _GRID_CM)), int(math.floor(y1 / _GRID_CM)) + 1):
                    buckets.setdefault((ci, gx, gy), []).append(cand)
    out = []
    for ci in sorted(course_candidates or {}):
        below = ci - 1
        if below not in course_candidates:
            continue
        z_lo, z_hi = course_band_ft(below)
        for cand in course_candidates[ci] or ():
            length = float(cand.get("length_cm") or 0.0)
            if length <= 0:
                continue
            x0, y0, x1, y1 = _bbox_cm(cand)
            seen = set()
            near = []
            for gx in range(int(math.floor(x0 / _GRID_CM)), int(math.floor(x1 / _GRID_CM)) + 1):
                for gy in range(int(math.floor(y0 / _GRID_CM)), int(math.floor(y1 / _GRID_CM)) + 1):
                    for other in buckets.get((below, gx, gy), ()):
                        if id(other) not in seen:
                            seen.add(id(other))
                            near.append(other)
            support = sum(b - a for a, b in _covered_along(cand, near)) / length
            if support >= min_fraction:
                continue
            over = sum(b - a for a, b in _over_openings(
                cand, walls_to_create, openings_per_wall, z_lo, z_hi, wall_axis)) / length
            if over >= min_fraction:
                continue
            o = cand["origin_world"]
            out.append({
                "kind": "UNSUPPORTED_SMALL_BLOCK" if length <= SMALL_BLOCK_MAX_LENGTH_CM else "UNSUPPORTED_BLOCK",
                "code": cand.get("logical_code"), "course": ci, "support": round(support, 3),
                "over_opening": round(over, 3), "wall_idx": cand.get("wall_idx"),
                "placement_reason": cand.get("placement_reason"),
                "point_cm": (round(o.X * _FT_TO_CM, 1), round(o.Y * _FT_TO_CM, 1)),
            })
    out.sort(key=lambda r: (r["course"], r["point_cm"], str(r["code"])))
    return out
