# -*- coding: utf-8 -*-
"""VAZADO MENOR ENTRE FIADAS (secao 52 de REGRAS_MODULACAO_BLOCOS.md).

Regra do usuario (2026-09-15): se existe um B34 numa fiada, a fiada vizinha
precisa preservar o VAZADO MENOR dele. Medida no projeto humano BUTANTA R08_LT
(1o PAV, somente leitura): em 2.500 dos 2.541 pares B34 x peca de alvenaria da
fiada vizinha, o centro do vazado menor do B34 cai DENTRO do vazado menor de
outro B34 ou do vazado central do B54 da fiada de cima/baixo (a coluna de
graute segue vertical). O humano consegue isso escolhendo a ORIENTACAO de cada
B34 (em corridas de B34 deslocadas 20 cm entre fiadas, o B34 de uma fiada fica
girado 180 graus em relacao ao da outra). O solver usava uma convencao fixa de
orientacao no B34 de preenchimento e deixava ~72% dos pares desalinhados.

Este modulo e' GEOMETRICO e generico: o "vazado menor" de uma peca e' a celula
de MENOR area quando ela e' estritamente menor que as demais (B34: a de 10,75
cm; B54: a central); pecas de celulas iguais (B39, B19) nao tem vazado menor;
pecas sem celula (compensador, pastilha, canaleta) nao participam da regra.

- `b34_small_void_violations(course_candidates)`: o validador. Para cada peca
  com vazado menor ORIENTAVEL (hoje o B34 - peca de 2 celulas assimetricas) e
  cada fiada vizinha: a peca de ALVENARIA VAZADA que cobre o centro do vazado
  menor tem de oferecer ali um vazado menor. Sem peca vazada por cima/baixo
  (compensador, pastilha, canaleta, vao, topo), nao ha' restricao.
- `orient_small_voids(course_candidates, is_fixed)`: o corretor. Gira 180
  graus (mesmo contorno, mesmas juntas, mesmas colisoes) os B34 que nao sao
  peca de no' (a orientacao do no' e' regra da secao 5) quando isso reduz
  estritamente as violacoes locais. Guloso, deterministico (ordem por chave
  fisica, nunca por id()/ordem de lista), idempotente.

Nenhum ElementId, parede, comprimento ou coordenada especifica entra aqui.
"""
import math

try:  # Revit / dubles dos testes
    from Autodesk.Revit.DB import XYZ
except Exception:  # pragma: no cover - so' fora do Revit sem dubles
    XYZ = None

FEET_PER_CM = 1.0 / 30.48
SMALL_VOID_ALIGN_TOLERANCE_CM = 1.5
SMALL_VOID_ORIENTATION_ENABLED = True
SMALL_VOID_MAX_PASSES = 8
SMALL_VOID_MAX_AREA_RATIO = 0.9
_GRID_CM = 40.0


def _cell_area(cell):
    size = cell.get("size_local") or (0.0, 0.0)
    return float(size[0]) * float(size[1])


def candidate_small_cell(candidate):
    """Celula de menor area se for ESTRITAMENTE menor que as outras; senao None."""
    cells = candidate.get("cells_world") or []
    if len(cells) < 2:
        return None
    ordered = sorted(cells, key=_cell_area)
    # "estritamente menor" com folga relativa: celulas de mesmo desenho medidas
    # com ruido (15,7 x 15,8 cm num B39) nao viram "vazado menor"; o B34 real
    # (10,75 x 15,75 cm) e o B54 (12,5 x 15,75 cm) ficam bem abaixo do limite.
    if _cell_area(ordered[0]) > SMALL_VOID_MAX_AREA_RATIO * _cell_area(ordered[1]):
        return None
    return ordered[0]


def _is_orientable_small_void_piece(candidate):
    """Peca de DUAS celulas assimetricas (B34): girar 180 graus troca o lado do
    vazado menor. Peca de 3 celulas com a menor no centro (B54) nao muda."""
    cells = candidate.get("cells_world") or []
    return len(cells) == 2 and candidate_small_cell(candidate) is not None


def _is_hollow_masonry(candidate, catalog=None):
    """Peca de alvenaria VAZADA (tem celulas e nao e' compensador/pastilha no
    catalogo). Canaleta sai com `cells_world=[]` e fica de fora."""
    if not candidate.get("cells_world"):
        return False
    entry = (catalog or {}).get(candidate.get("logical_code")) or {}
    return not entry.get("is_compensator")


def _local(candidate, x_ft, y_ft):
    o = candidate["origin_world"]
    xd = candidate["x_dir"]
    yd = candidate.get("y_dir") or XYZ(-xd.Y, xd.X, 0.0)
    dx, dy = x_ft - o.X, y_ft - o.Y
    return dx * xd.X + dy * xd.Y, dx * yd.X + dy * yd.Y


def _contains(candidate, x_ft, y_ft, eps_ft=1e-6):
    u, v = _local(candidate, x_ft, y_ft)
    half_len = float(candidate.get("length_cm") or 0.0) * FEET_PER_CM / 2.0
    half_w = float(candidate.get("width_cm") or 0.0) * FEET_PER_CM / 2.0
    return abs(u) <= half_len + eps_ft and abs(v) <= half_w + eps_ft


def _cell_contains(candidate, cell, x_ft, y_ft, tol_ft):
    xd = candidate["x_dir"]
    yd = candidate.get("y_dir") or XYZ(-xd.Y, xd.X, 0.0)
    p = cell["point"]
    dx, dy = x_ft - p.X, y_ft - p.Y
    u = dx * xd.X + dy * xd.Y
    v = dx * yd.X + dy * yd.Y
    sx, sy = cell["size_local"]
    return abs(u) <= sx / 2.0 + tol_ft and abs(v) <= sy / 2.0 + tol_ft


def _footprint_bbox_ft(candidate):
    o = candidate["origin_world"]
    xd = candidate["x_dir"]
    half_len = float(candidate.get("length_cm") or 0.0) * FEET_PER_CM / 2.0
    half_w = float(candidate.get("width_cm") or 0.0) * FEET_PER_CM / 2.0
    hx = abs(xd.X) * half_len + abs(xd.Y) * half_w
    hy = abs(xd.Y) * half_len + abs(xd.X) * half_w
    return o.X - hx, o.Y - hy, o.X + hx, o.Y + hy


class _CourseIndex(object):
    def __init__(self, course_candidates, catalog=None):
        self.cell_ft = _GRID_CM * FEET_PER_CM
        self.buckets = {}
        self.occurrences = {}
        for course_index in sorted(course_candidates or {}):
            for cand in course_candidates[course_index] or ():
                if not _is_hollow_masonry(cand, catalog):
                    continue
                key = id(cand)
                entry = self.occurrences.get(key)
                if entry is None:
                    entry = self.occurrences[key] = (cand, set())
                entry[1].add(course_index)
                x0, y0, x1, y1 = _footprint_bbox_ft(cand)
                for gx in range(int(math.floor(x0 / self.cell_ft)), int(math.floor(x1 / self.cell_ft)) + 1):
                    for gy in range(int(math.floor(y0 / self.cell_ft)), int(math.floor(y1 / self.cell_ft)) + 1):
                        self.buckets.setdefault((course_index, gx, gy), []).append(cand)

    def covering(self, course_index, x_ft, y_ft):
        key = (course_index, int(math.floor(x_ft / self.cell_ft)), int(math.floor(y_ft / self.cell_ft)))
        found = []
        for cand in self.buckets.get(key, ()):
            if _contains(cand, x_ft, y_ft):
                found.append(cand)
        return found

    def near(self, course_index, candidate):
        x0, y0, x1, y1 = _footprint_bbox_ft(candidate)
        seen = set()
        out = []
        for gx in range(int(math.floor(x0 / self.cell_ft)), int(math.floor(x1 / self.cell_ft)) + 1):
            for gy in range(int(math.floor(y0 / self.cell_ft)), int(math.floor(y1 / self.cell_ft)) + 1):
                for cand in self.buckets.get((course_index, gx, gy), ()):
                    if id(cand) not in seen:
                        seen.add(id(cand))
                        out.append(cand)
        return out


def _offers_small_void_at(candidate, x_ft, y_ft, tol_ft):
    cell = candidate_small_cell(candidate)
    return cell is not None and _cell_contains(candidate, cell, x_ft, y_ft, tol_ft)


def _pair_violation(index, piece, other_course, tol_ft):
    """(violou, peca_vizinha) para o vazado menor de `piece` x `other_course`."""
    cell = candidate_small_cell(piece)
    if cell is None:
        return False, None
    x_ft, y_ft = cell["point"].X, cell["point"].Y
    hits = index.covering(other_course, x_ft, y_ft)
    if not hits:
        return False, None
    for hit in hits:
        if _offers_small_void_at(hit, x_ft, y_ft, tol_ft):
            return False, hit
    return True, hits[0]


def _valid_course(course_candidates, course_index):
    return course_index in (course_candidates or {})


def b34_small_void_violations(course_candidates, catalog=None, tolerance_cm=SMALL_VOID_ALIGN_TOLERANCE_CM):
    """Lista de violacoes {course, other_course, wall_idx, logical_code,
    neighbor_code, point_cm} - ordem deterministica (fiada, chave fisica)."""
    index = _CourseIndex(course_candidates, catalog)
    tol_ft = tolerance_cm * FEET_PER_CM
    out = []
    for key in sorted(index.occurrences, key=lambda k: _physical_key(index.occurrences[k][0])):
        cand, courses = index.occurrences[key]
        if not _is_orientable_small_void_piece(cand):
            continue
        cell = candidate_small_cell(cand)
        for course_index in sorted(courses):
            for other in (course_index - 1, course_index + 1):
                if not _valid_course(course_candidates, other):
                    continue
                violated, hit = _pair_violation(index, cand, other, tol_ft)
                if violated:
                    out.append({
                        "course": course_index, "other_course": other,
                        "wall_idx": cand.get("wall_idx"), "logical_code": cand.get("logical_code"),
                        "placement_reason": cand.get("placement_reason"),
                        "neighbor_code": hit.get("logical_code") if hit is not None else None,
                        "point_cm": (round(cell["point"].X * 30.48, 1), round(cell["point"].Y * 30.48, 1)),
                    })
    return out


def _physical_key(candidate):
    o = candidate["origin_world"]
    return (round(o.X * 30.48, 1), round(o.Y * 30.48, 1), round(o.Z * 30.48, 1), str(candidate.get("logical_code")),
            round(float(candidate.get("rotation_deg") or 0.0), 1))


def _local_cost(index, candidate, courses, tol_ft):
    """Violacoes em que `candidate` participa: o proprio vazado menor contra
    as fiadas vizinhas e o vazado menor dos B34 vizinhos que caem dentro dele."""
    cost = 0
    own_cell = candidate_small_cell(candidate)
    for course_index in courses:
        for other in (course_index - 1, course_index + 1):
            if other not in index.course_set:
                continue
            if own_cell is not None:
                violated, _hit = _pair_violation(index, candidate, other, tol_ft)
                if violated:
                    cost += 1
            for neighbor in index.near(other, candidate):
                if not _is_orientable_small_void_piece(neighbor):
                    continue
                ncell = candidate_small_cell(neighbor)
                nx, ny = ncell["point"].X, ncell["point"].Y
                if not _contains(candidate, nx, ny):
                    continue
                # o vizinho so' e' afetado por ESTA peca se ela for a que cobre o ponto
                if not _offers_small_void_at(candidate, nx, ny, tol_ft):
                    cost += 1
    return cost


def rotate_candidate_180(candidate):
    """Gira a peca 180 graus em torno do proprio centro (origin_world e' o
    centro geometrico, secao 1): contorno, juntas e colisoes inalterados."""
    o = candidate["origin_world"]
    xd = candidate["x_dir"]
    new_x = XYZ(-xd.X, -xd.Y, 0.0)
    candidate["x_dir"] = new_x
    candidate["y_dir"] = XYZ(-new_x.Y, new_x.X, 0.0)
    candidate["rotation_deg"] = (float(candidate.get("rotation_deg") or 0.0) + 180.0) % 360.0
    cells = []
    for cell in candidate.get("cells_world") or []:
        p = cell["point"]
        cells.append({"point": XYZ(2.0 * o.X - p.X, 2.0 * o.Y - p.Y, p.Z), "size_local": cell["size_local"]})
    candidate["cells_world"] = cells
    return candidate


def orient_small_voids(course_candidates, catalog=None, is_fixed=None,
                       tolerance_cm=SMALL_VOID_ALIGN_TOLERANCE_CM, max_passes=SMALL_VOID_MAX_PASSES):
    """Gira 180 graus os B34 orientaveis (nao fixos) quando reduz estritamente
    as violacoes locais. Devolve {"rotated": n, "passes": k, "before": a, "after": b}."""
    if is_fixed is None:
        def is_fixed(candidate):
            return candidate.get("node_index") is not None
    before = len(b34_small_void_violations(course_candidates, catalog, tolerance_cm))
    index = _CourseIndex(course_candidates, catalog)
    index.course_set = set(course_candidates or {})
    tol_ft = tolerance_cm * FEET_PER_CM
    movable = []
    for key in index.occurrences:
        cand, courses = index.occurrences[key]
        if _is_orientable_small_void_piece(cand) and not is_fixed(cand):
            movable.append((cand, sorted(courses)))
    movable.sort(key=lambda item: (item[1][0], _physical_key(item[0])))
    rotated = set()
    passes = 0
    changed = True
    while changed and passes < max_passes:
        changed = False
        passes += 1
        for cand, courses in movable:
            current = _local_cost(index, cand, courses, tol_ft)
            if current == 0:
                continue
            rotate_candidate_180(cand)
            flipped = _local_cost(index, cand, courses, tol_ft)
            if flipped < current:
                changed = True
                if id(cand) in rotated:
                    rotated.discard(id(cand))
                else:
                    rotated.add(id(cand))
            else:
                rotate_candidate_180(cand)
    # GIRO EM PAR (2026-09-15): dois B34 sobrepostos em fiadas vizinhas com
    # deslocamento de 15-20 cm so' alinham os DOIS vazados menores girando os
    # dois juntos (humano: corridas de B34 deslocadas entre fiadas com
    # orientacao oposta). Girar um so' nao reduz estritamente a violacao e o
    # passe guloso acima para. Aqui, para cada par (peca movel, vizinha movel
    # sobreposta na fiada de cima), gira os dois quando a soma das violacoes
    # locais cai estritamente. Mesma ordem deterministica.
    pair_passes = 0
    changed = True
    by_id = dict((id(cand), (cand, courses)) for cand, courses in movable)
    while changed and pair_passes < max_passes:
        changed = False
        pair_passes += 1
        for cand, courses in movable:
            partners = []
            for course_index in courses:
                for neighbor in index.near(course_index + 1, cand):
                    entry = by_id.get(id(neighbor))
                    if entry is None or neighbor is cand:
                        continue
                    partners.append(entry)
            partners.sort(key=lambda item: (item[1][0], _physical_key(item[0])))
            for other, other_courses in partners:
                current = _local_cost(index, cand, courses, tol_ft) + _local_cost(index, other, other_courses, tol_ft)
                if current == 0:
                    continue
                rotate_candidate_180(cand)
                rotate_candidate_180(other)
                flipped = _local_cost(index, cand, courses, tol_ft) + _local_cost(index, other, other_courses, tol_ft)
                if flipped < current:
                    changed = True
                    for piece in (cand, other):
                        if id(piece) in rotated:
                            rotated.discard(id(piece))
                        else:
                            rotated.add(id(piece))
                else:
                    rotate_candidate_180(cand)
                    rotate_candidate_180(other)
    after = len(b34_small_void_violations(course_candidates, catalog, tolerance_cm))
    return {"rotated": len(rotated), "passes": passes, "pair_passes": pair_passes, "before": before, "after": after}
