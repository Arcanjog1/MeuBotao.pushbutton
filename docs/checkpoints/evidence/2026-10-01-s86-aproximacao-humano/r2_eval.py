# -*- coding: utf-8 -*-
"""Regua INDEPENDENTE da rodada 2 (sem o motor): avalia as fileiras de UMA parede (pecas reais com celulas
ao longo do eixo) e devolve os indicadores que o usuario pediu, para comparar antes x depois.

rows: {fiada: [[lo, hi, codigo, [[c_lo, c_hi], ...], element_id_ou_None], ...]} (formato do readback)
openings: [[lo, hi, peitoril_rel_cm, topo_rel_cm], ...]

Indicadores:
- broken / ok / full: celulas de vazado em coluna continua na altura inteira (mesma regua do render_svg:
  largura comum acumulada >= 8,94 cm; canaleta e vao atravessados so pela fase; vazado menor do B34
  (< 11,5) contra vazado principal (> 13) = quebra).
- sv: vazado menor de B34 sobre vazado principal da fiada vizinha (sobreposicao > 4 cm).
- septa_unsupported: septo (parede transversal entre dois vazados de um bloco, ou septo de ponta)
  cujo centro cai sobre um VAZADO da fiada de baixo (nao canaleta) - septo sem apoio.
- joints_coincident: juntas verticais de fiadas vizinhas a menos de 2 cm (pares de fiadas), sem isencao;
  joints_coincident_nonexempt: menos as juntas de peca de fechamento (C04/C09/B19) encostada no vao
  (11.8) - contada so' se a junta NAO for de fechamento nas duas fiadas.
- stacks3: juntas que se repetem em 3+ fiadas seguidas.
- comps: pastilhas/compensadores; b19_misplaced: B19 que nao encosta em vao da fiada, ponta da parede ou
  faixa de compensador encostada no vao.
- strips: faixa vertical de peca especial (B34/B54/C09/C04) - mesma leitura da auditoria de producao:
  centros agrupados a 6 cm, 3+ fiadas, >= metade das fiadas e 2+ fiadas adjacentes, fora de 25 cm das
  pontas, 60 cm das aberturas e 60 cm de no' de meio de parede.
- channel_at_node: canaleta sobre zona de no' (B54 de no' ou passagem da parede que cruza) - canaleta
  nunca serve de amarracao."""
TH, FULL = 8.94 - 1e-6, 13.9 - 1e-6
SMALL, MAIN = 11.5, 13.0
JOINT_TOL = 2.0
SPECIAL = ("B34", "B54", "C09", "C04")


def _covering(items, t):
    for it in items:
        if it[0] - 1e-6 <= t <= it[1] + 1e-6:
            return it
    return None


def _in_joint(items, t):
    prev = None
    for it in items:
        if it[0] > t:
            return prev is not None and it[0] - prev[1] <= 2.5
        prev = it
    return False


def column(rows, ci, cell):
    narrow = cell[1] - cell[0]
    for dj in (-1, 1):
        col = cell
        prev_w = cell[1] - cell[0]
        cj = ci + dj
        while cj in rows:
            mid = (col[0] + col[1]) / 2.0
            host = _covering(rows[cj], mid)
            if host is None:
                if _in_joint(rows[cj], mid):
                    return "broken"
                cj += dj
                continue
            if host[2].startswith("CHANNEL"):
                cj += dj
                continue
            best = None
            for it in rows[cj]:
                if it[1] < col[0] - 1 or it[0] > col[1] + 1:
                    continue
                for c2 in it[3]:
                    w2 = c2[1] - c2[0]
                    if min(prev_w, w2) < SMALL and max(prev_w, w2) > MAIN:
                        continue
                    w = min(col[1], c2[1]) - max(col[0], c2[0])
                    if best is None or w > best[0]:
                        best = (w, (max(col[0], c2[0]), min(col[1], c2[1])), w2)
            if best is None or best[0] < TH:
                return "broken"
            col = best[1]
            prev_w = best[2]
            narrow = min(narrow, col[1] - col[0])
            cj += dj
    return "full" if narrow >= FULL else "ok"


def _cut(course, openings):
    """aberturas que cortam a fiada (faixa z da fiada x peitoril/topo)."""
    z0, z1 = course * 20.0, course * 20.0 + 19.0
    return [(o[0], o[1]) for o in openings if z1 > o[2] + 0.5 and z0 < o[3] - 0.5]


def _joints(items):
    out = []
    for a, b in zip(items, items[1:]):
        if 0 <= b[0] - a[1] <= 2.5:
            out.append(((a[1] + b[0]) / 2.0, a, b))
    return out


def _closure_joints(items, cut, length):
    """(faixa, b19): juntas do lado de dentro das pecas de fechamento encostadas num vao da fiada ou na ponta
    da parede. `faixa` = juntas de compensador (C04/C09) da faixa encostada (isentas mesmo nas duas fiadas);
    `b19` = junta do lado de dentro do B19 de fechamento (encostado ou logo atras da faixa) - isenta so' contra
    uma junta que nao e' de fechamento de B19 (11.8 + excecao da secao 2; B19 sobre B19 = a prumo)."""
    strip, b19 = set(), set()
    edges = [(lo, -1) for lo, _hi in cut] + [(hi, 1) for _lo, hi in cut] + [(0.0, 1), (length, -1)]
    for e, d in edges:
        idx = None
        for k, it in enumerate(items):
            face = it[0] if d > 0 else it[1]
            if abs(face - e) <= 1.5:
                idx = k
                break
        if idx is None:
            continue
        k = idx
        while 0 <= k < len(items) and items[k][2] in ("C04", "C09", "B19"):
            nb = k + d
            if 0 <= nb < len(items):
                a, b = (items[k], items[nb]) if d > 0 else (items[nb], items[k])
                if 0 <= b[0] - a[1] <= 2.5:
                    (b19 if items[k][2] == "B19" else strip).add(round((a[1] + b[0]) / 2.0, 1))
            if items[k][2] == "B19":
                break
            k = nb
    return strip, b19


def evaluate(rows, openings, length, ties=()):
    rows = dict((int(c), sorted(v)) for c, v in rows.items())
    courses = sorted(rows)
    res = {"full": 0, "ok": 0, "broken": 0, "sv": 0, "septa_unsupported": 0, "joints_coincident": 0,
           "joints_coincident_nonexempt": 0, "stacks3": 0, "comps": 0, "b19_misplaced": 0, "strips": 0,
           "channel_at_node": 0, "pieces": 0, "comps_off_jamb": 0}
    broken_cells = []
    joints_by_course = {}
    closure_by_course = {}
    for ci in courses:
        items = rows[ci]
        cut = _cut(ci, openings)
        joints_by_course[ci] = [j[0] for j in _joints(items)]
        closure_by_course[ci] = _closure_joints(items, cut, length)
        for it in items:
            res["pieces"] += 1
            code = it[2]
            if code in ("C04", "C09"):
                res["comps"] += 1
                # pastilha so' encostada no vao da fiada (direto ou pela faixa), na ponta da parede ou num
                # encontro (B54 de no' / passagem da parede que cruza) - 85.8
                k = items.index(it)
                ok = it[0] <= 1.5 or it[1] >= length - 1.5
                for dd in (-1, 1):
                    j = k
                    while not ok and 0 <= j < len(items) and items[j][2] in ("C04", "C09"):
                        face = items[j][0] if dd < 0 else items[j][1]
                        if any(abs(face - hi) <= 1.5 for _lo, hi in cut) if dd < 0 else                                 any(abs(face - lo) <= 1.5 for lo, _hi in cut):
                            ok = True
                        nb = j + dd
                        if 0 <= nb < len(items):
                            gap = (items[j][0] - items[nb][1]) if dd < 0 else (items[nb][0] - items[j][1])
                            if items[nb][2] == "B54" and gap <= 2.5:
                                ok = True
                            if 12.5 <= gap <= 17.5:
                                ok = True  # encosta na parede que cruza
                        elif face <= 1.5 or face >= length - 1.5:
                            ok = True
                        j = nb
                if not ok:
                    res["comps_off_jamb"] += 1
            if code.startswith("CHANNEL"):
                continue
            for c2 in it[3]:
                st = column(rows, ci, c2)
                res[st] += 1
                if st == "broken":
                    broken_cells.append((ci, round((c2[0] + c2[1]) / 2.0, 1)))
                if code == "B34" and c2[1] - c2[0] < SMALL:
                    for cj in (ci - 1, ci + 1):
                        for it2 in rows.get(cj, ()):
                            for c3 in it2[3]:
                                if min(c2[1], c3[1]) - max(c2[0], c3[0]) > 4.0 and c3[1] - c3[0] > MAIN:
                                    res["sv"] += 1
            pass
            if code == "B19":
                ok = False
                for lo, hi in cut:
                    if abs(it[1] - lo) <= 1.5 or abs(it[0] - hi) <= 1.5:
                        ok = True
                if it[0] <= 1.5 or it[1] >= length - 1.5:
                    ok = True
                if not ok:
                    # logo atras da faixa de compensador encostada
                    k = items.index(it)
                    for d in (-1, 1):
                        j = k + d
                        while 0 <= j < len(items) and items[j][2] in ("C04", "C09"):
                            far = items[j][0] if d < 0 else items[j][1]
                            touch = any(abs(far - lo) <= 1.5 or abs(far - hi) <= 1.5 for lo, hi in cut)
                            if touch:
                                ok = True
                            j += d
                if not ok:
                    res["b19_misplaced"] += 1
            if code.startswith("CHANNEL"):
                pass
        cells = sorted(c2 for it in items if not it[2].startswith("CHANNEL") for c2 in it[3])
        below = rows.get(ci - 1)
        if below and not all(it2[2].startswith("CHANNEL") for it2 in below):
            for a, b in zip(cells, cells[1:]):
                if b[0] - a[1] > 30.0:
                    continue  # vao/abertura entre eles
                mid = (a[1] + b[0]) / 2.0
                if _covering(items, mid) is None and not _in_joint(items, mid):
                    continue  # nao ha' alvenaria ali (abertura)
                host = _covering(below, mid)
                if host is None or host[2].startswith("CHANNEL"):
                    continue
                if any(c3[0] + 0.5 < mid < c3[1] - 0.5 for c3 in host[3]):
                    res["septa_unsupported"] += 1
        for it in items:
            if it[2].startswith("CHANNEL"):
                for t in ties:
                    if it[0] + 2.0 < t < it[1] - 2.0:
                        res["channel_at_node"] += 1
    # juntas coincidentes entre fiadas vizinhas
    for ci in courses:
        cj = ci + 1
        if cj not in joints_by_course:
            continue
        for j in joints_by_course[ci]:
            if any(abs(j - k) < JOINT_TOL for k in joints_by_course[cj]):
                res["joints_coincident"] += 1
                sa, ba = closure_by_course[ci]
                sb, bb = closure_by_course[cj]
                near = lambda xs: any(abs(j - x) <= 1.0 for x in xs)
                if near(sa) or near(sb):
                    continue  # junta da faixa de compensador encostada (isenta)
                if near(ba) != near(bb):
                    continue  # junta do B19 de fechamento contra junta comum (11.8)
                res["joints_coincident_nonexempt"] += 1
    # juntas em 3+ fiadas seguidas (menos as da faixa de compensador encostada no vao - mesma isencao da
    # guarda do motor `_stacks_nonexempt` e da auditoria 11.8)
    for ci in courses:
        strip_ci = closure_by_course[ci][0]
        joints_by_course[ci] = [j for j in joints_by_course[ci] if not any(abs(j - x) <= 1.0 for x in strip_ci)]
    for ci in courses:
        for j in joints_by_course[ci]:
            if ci - 1 in joints_by_course and any(abs(j - k) < JOINT_TOL for k in joints_by_course[ci - 1]):
                continue
            n, cj = 1, ci + 1
            while cj in joints_by_course and any(abs(j - k) < JOINT_TOL for k in joints_by_course[cj]):
                n += 1
                cj += 1
            if n >= 3:
                res["stacks3"] += 1
    # faixa vertical de peca especial (espelho da auditoria de producao)
    pts = []
    ncourses = max(courses) + 1 if courses else 0
    for ci in courses:
        for it in rows[ci]:
            if it[2] not in SPECIAL:
                continue
            mid = (it[0] + it[1]) / 2.0
            if mid <= 25.0 or mid >= length - 25.0:
                continue
            if any(abs(mid - e) <= 60.0 for o in openings for e in (o[0], o[1])):
                continue
            if any(abs(mid - t) <= 60.0 for t in ties if 0.5 < t < length - 0.5):
                continue
            pts.append((mid, ci))
    pts.sort()
    clusters, cur = [], []
    for p in pts:
        if cur and p[0] - cur[-1][0] > 6.0:
            clusters.append(cur)
            cur = []
        cur.append(p)
    if cur:
        clusters.append(cur)
    for cl in clusters:
        cs = sorted(set(c for _t, c in cl))
        if len(cs) < 3 or ncourses == 0 or len(cs) / float(ncourses) < 0.5:
            continue
        best = run = 1
        for a, b in zip(cs, cs[1:]):
            run = run + 1 if b == a + 1 else 1
            best = max(best, run)
        if best >= 2:
            res["strips"] += 1
    res["broken_cells"] = broken_cells
    return res


def ties_from_rows(rows):
    """posicoes de amarracao: centro dos B54 (no') e das folgas de 12,5-17,5 cm (parede que cruza)."""
    ties = set()
    for ci, items in rows.items():
        its = sorted(items)
        for it in its:
            if it[2] == "B54":
                ties.add(round((it[0] + it[1]) / 2.0))
        for a, b in zip(its, its[1:]):
            if 12.5 <= b[0] - a[1] <= 17.5:
                ties.add(round((a[1] + b[0]) / 2.0))
    return sorted(ties)


KEYS = ("broken", "sv", "septa_unsupported", "joints_coincident_nonexempt", "stacks3", "comps", "comps_off_jamb",
        "b19_misplaced", "strips", "channel_at_node")


def regressions(before, after):
    """indicadores que pioraram (todos sao 'menor e' melhor')."""
    return [k for k in KEYS if after[k] > before[k]]
