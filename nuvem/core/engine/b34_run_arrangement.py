# -*- coding: utf-8 -*-
"""ARRANJO CONJUNTO DAS CORRIDAS DE PREENCHIMENTO (secao 60 de
REGRAS_MODULACAO_BLOCOS.md) - vazado menor do B34 entre fiadas.

Medido no BUTANTA (34 paredes, fiadas 0-11): das 316 violacoes que restavam
depois da orientacao da secao 52, 157 sao B34 sobre B39 e 114 sao B34 sobre B34
num deslocamento que so' alinharia com a orientacao OPOSTA - sinal de que a
posicao dos B34 dentro da corrida, e nao a rotacao, e' o que falta. O humano
resolve na ORDEM das mesmas pecas: parede 8284543, trecho 815-964 cm, o solver
assentava `B34 B39 B39 B34` e o humano `B34 B34 B39 B39`, encaixando a corrida de
B34 na corrida da fiada vizinha, deslocada ~20 cm e girada 180 graus.

O que este passe faz, parede por parede:

1. agrupa as fiadas FISICAS em familias (fiadas com a mesma fileira, peca por
   peca) e conta quantas vezes cada par de familias fica em fiadas vizinhas;
2. em cada corrida de preenchimento (pecas STANDARD_FILL encostadas, fora de
   no', canaleta e peca compartilhada entre familias), enumera as ordens
   DISTINTAS das MESMAS pecas - mesmas pontas, mesmas juntas, mesmo
   comprimento - e a orientacao dos B34 de cada ordem;
3. fica com a ordem que reduz ESTRITAMENTE as violacoes do vazado menor contra
   as familias vizinhas, sem piorar nenhuma guarda: face repetida entre fiadas
   vizinhas, junta empilhada em 3+ fiadas, compensadores encostados (regra #2 e
   56.2) e compensador longo como peca extrema da parede (secao 58);
4. repete ate' estabilizar (no maximo `MAX_PASSES`), entao a escolha de uma
   corrida enxerga a escolha ja' feita nas corridas vizinhas - a diferenca para
   a tentativa rejeitada da secao 57, que decidia cada corrida uma vez so',
   contra vizinhas que ainda iam se mover.

Geometria: o "vazado menor" e' a celula de menor area (`candidate_small_cell`,
secao 52), lida das `cells_world` de cada peca. Nenhum codigo de familia,
parede, comprimento ou coordenada especifica entra aqui. Deterministico
(paredes por indice, familias pela primeira fiada, corridas pela posicao,
ordens em ordem lexicografica, empate pela menor quantidade de pecas trocadas)
e idempotente (uma segunda passada nao encontra melhoria).
"""
import bisect
import collections

try:  # Revit / dubles dos testes
    from Autodesk.Revit.DB import XYZ
except Exception:  # pragma: no cover - so' fora do Revit sem dubles
    XYZ = None

from core.engine import small_void_alignment as _sva

B34_RUN_ARRANGEMENT_ENABLED = True
# O legado (strategy=None) fica IDENTICO a' main por padrao: ele nao refaz a
# auditoria de amarracao depois do solve. Ligar so' para medir o corpus legado.
B34_RUN_ARRANGEMENT_LEGACY = False
MAX_ARRANGEMENTS_PER_RUN = 240
MAX_PASSES = 3
RUN_MAX_GAP_CM = 2.5
FACE_TOLERANCE_CM = 0.6
EDGE_TOLERANCE_CM = 1.0
TOUCH_TOLERANCE_CM = 1.6
# Alcance do custo local de um trecho: o centro do vazado menor fica a menos de
# meia peca do centro dela, e a peca vizinha que o cobre tem no maximo 54 cm.
WINDOW_PAD_CM = 60.0
WALL_END_TOLERANCE_CM = 2.0
# Compensador a partir deste comprimento e' "longo" (C09); o humano nunca termina
# uma fiada com ele, mas termina com C04 (secao 58).
LONG_COMPENSATOR_MIN_CM = 6.0
CM_PER_FT = 30.48


class _Slot(object):
    __slots__ = ("lo", "hi", "code", "side", "movable", "node", "hollow", "orientable",
                 "void_off", "void_half", "compensator")

    def __init__(self):
        self.lo = self.hi = 0.0
        self.code = None
        self.side = 0
        self.movable = self.node = self.hollow = self.orientable = self.compensator = False
        self.void_off = self.void_half = None

    @property
    def mid(self):
        return (self.lo + self.hi) / 2.0

    def copy(self):
        other = _Slot()
        for name in _Slot.__slots__:
            setattr(other, name, getattr(self, name))
        return other


def _is_channel_code(code):
    try:
        from core.engine import opening_reinforcement as _reinforcement
        return bool(_reinforcement.is_channel_code(code))
    except Exception:  # pragma: no cover - modulo sempre presente no motor
        return str(code or "").upper().startswith("CHANNEL")


def _axis(walls_to_create, wall_idx):
    from core.engine.wall_stepper import _wall_axis_and_length
    p0, _p1, wall_dir, length_ft, _t = _wall_axis_and_length(walls_to_create, wall_idx)
    return p0, wall_dir, length_ft * CM_PER_FT


def _extent_cm(cand, p0, wall_dir):
    from core.engine.wall_stepper import _candidate_t_range_on_wall
    a, b = _candidate_t_range_on_wall(cand, p0, wall_dir)
    return min(a, b), max(a, b)


def _void_geometry(cand, p0, wall_dir, lo, hi):
    """(deslocamento com sinal do centro da celula menor ate' o centro da peca,
    meia largura dela ao longo da parede) - ou (None, None) sem celula menor."""
    cell = _sva.candidate_small_cell(cand)
    if cell is None:
        return None, None
    pt = cell["point"]
    t_cell = ((pt.X - p0.X) * wall_dir.X + (pt.Y - p0.Y) * wall_dir.Y) * CM_PER_FT
    half = float(cell["size_local"][0]) * CM_PER_FT / 2.0
    return t_cell - (lo + hi) / 2.0, half


def _void_center(slot):
    if slot.void_off is None:
        return None
    if not slot.orientable:
        return slot.mid + slot.void_off
    return slot.mid + slot.side * abs(slot.void_off)


def _offers(slot, t, tol_cm):
    if not slot.hollow:
        return None
    c = _void_center(slot)
    if c is None:
        return False
    return c - slot.void_half - tol_cm <= t <= c + slot.void_half + tol_cm


def _first_hi_at_least(slots, t):
    """Indice da primeira peca com hi >= t (as pecas de uma fileira estao em
    ordem de posicao e nao se sobrepoem, entao hi tambem e' crescente)."""
    low, high = 0, len(slots)
    while low < high:
        middle = (low + high) // 2
        if slots[middle].hi + 1e-6 < t:
            low = middle + 1
        else:
            high = middle
    return low


def _covering(slots, t):
    i = _first_hi_at_least(slots, t)
    if i < len(slots) and slots[i].lo - 1e-6 <= t:
        return slots[i]
    return None


def _in_window(slots, lo, hi):
    i = _first_hi_at_least(slots, lo)
    while i < len(slots) and slots[i].lo <= hi:
        yield slots[i]
        i += 1


def _violations_between(lower, upper, tol_cm, window=None):
    count = 0
    for src, dst in ((lower, upper), (upper, lower)):
        pieces = src if window is None else _in_window(src, window[0], window[1])
        for p in pieces:
            if not p.orientable:
                continue
            t = _void_center(p)
            h = _covering(dst, t)
            if h is not None and _offers(h, t, tol_cm) is False:
                count += 1
    return count


def _has_value_near(sorted_values, value, tolerance):
    """True se `sorted_values` tem algum valor a ate' `tolerance` de `value`."""
    i = bisect.bisect_left(sorted_values, value - tolerance)
    return i < len(sorted_values) and sorted_values[i] <= value + tolerance


def _internal_faces(slots, wall_len, edges, window=None):
    """Faces internas da fileira, sem ponta de parede nem borda de vao.
    `edges` tem de estar ORDENADA (feito uma vez em `_Wall`)."""
    out = []
    for s in (slots if window is None else _in_window(slots, window[0], window[1])):
        for f in (s.lo, s.hi):
            if f <= EDGE_TOLERANCE_CM or f >= wall_len - EDGE_TOLERANCE_CM:
                continue
            if _has_value_near(edges, f, EDGE_TOLERANCE_CM):
                continue
            out.append(f)
    out.sort()
    return out


def _coincident(fa, fb):
    j = n = 0
    for f in fa:
        while j < len(fb) and fb[j] < f - FACE_TOLERANCE_CM:
            j += 1
        if j < len(fb) and fb[j] <= f + FACE_TOLERANCE_CM:
            n += 1
    return n


def _compensator_guard(slots, wall_len):
    n = 0
    for a, b in zip(slots, slots[1:]):
        if a.compensator and b.compensator and 0.0 <= b.lo - a.hi <= TOUCH_TOLERANCE_CM:
            n += 1
    if slots:
        first, last = slots[0], slots[-1]
        if first.compensator and first.hi - first.lo >= LONG_COMPENSATOR_MIN_CM and \
                first.lo <= WALL_END_TOLERANCE_CM:
            n += 1
        if last.compensator and last.hi - last.lo >= LONG_COMPENSATOR_MIN_CM and \
                last.hi >= wall_len - WALL_END_TOLERANCE_CM:
            n += 1
    return n


def _half_blocks_near_ties(slots, ties, half_code, max_gap_cm):
    """Meio bloco a ate' `max_gap_cm` de uma amarracao da parede - a MESMA
    regra de `HALF_BLOCK_NEAR_TIE` da auditoria de amarracao (regra #2)."""
    if not ties or not half_code:
        return 0
    n = 0
    for s in slots:
        if s.code != half_code:
            continue
        for t in ties:
            gap = s.lo - t if t < s.lo else (t - s.hi if t > s.hi else 0.0)
            if gap <= max_gap_cm:
                n += 1
                break
    return n


def _stacks(fam, course_fam, wall_len, edges):
    """Juntas que se repetem em 3 ou mais fiadas seguidas."""
    by_family = {}
    for f in set(course_fam.values()):
        by_family[f] = _internal_faces(fam[f], wall_len, edges)
    faces = dict((c, by_family[course_fam[c]]) for c in course_fam)
    empty = []
    n = 0
    for c in sorted(faces):
        for f in faces[c]:
            if _has_value_near(faces.get(c - 1, empty), f, FACE_TOLERANCE_CM):
                continue
            length, cc = 1, c
            while _has_value_near(faces.get(cc + 1, empty), f, FACE_TOLERANCE_CM):
                length += 1
                cc += 1
            if length >= 3:
                n += 1
    return n


def _runs(slots):
    out, cur = [], []
    for i, s in enumerate(slots):
        if s.movable and (not cur or s.lo - slots[cur[-1]].hi <= RUN_MAX_GAP_CM):
            cur.append(i)
            continue
        if len(cur) > 1:
            out.append(cur)
        cur = [i] if s.movable else []
    if len(cur) > 1:
        out.append(cur)
    return out


def _arrangements(slots, run):
    """Ordens DISTINTAS do multiconjunto de codigos, geradas direto (sem varrer
    n!), em ordem lexicografica, com teto."""
    counts = collections.Counter(slots[i].code for i in run)
    keys = sorted(counts)
    n = len(run)
    out, cur = [], []

    def rec():
        if len(out) >= MAX_ARRANGEMENTS_PER_RUN:
            return
        if len(cur) == n:
            out.append(tuple(cur))
            return
        for k in keys:
            if counts[k]:
                counts[k] -= 1
                cur.append(k)
                rec()
                cur.pop()
                counts[k] += 1

    rec()
    return out


class _Wall(object):
    def __init__(self, wall_idx, rows, walls_to_create, openings_per_wall, catalog, tol_cm,
                 ties=None, half_code=None, half_tie_gap_cm=0.0):
        self.wall_idx = wall_idx
        self.tol = tol_cm
        self.ties = list(ties or [])
        self.half_code = half_code
        self.half_tie_gap = half_tie_gap_cm
        self.p0, self.dir, self.length = _axis(walls_to_create, wall_idx)
        self.edges = []
        ops = (openings_per_wall or [])
        for op in (ops[wall_idx] if wall_idx < len(ops) else None) or ():
            self.edges.extend([float(op[0]) * CM_PER_FT, float(op[1]) * CM_PER_FT])
        self.edges.sort()
        self.rows = rows
        self.catalog = catalog or {}
        self._build()

    def _entry_movable(self, entry, family):
        """Preenchimento comum que e' BLOCO VAZADO de alvenaria ou COMPENSADOR do
        catalogo. A etiqueta STANDARD_FILL sozinha nao basta: a canaleta do
        reforco CHANNEL herda a etiqueta da peca que substituiu (medido: o
        arranjo reordenou canaletas da fiada 3 da parede 8284502), e canaleta
        e' posicao de vao/verga, nunca peca de ajuste de corrida."""
        cand, _lo, _hi, courses = entry
        code = cand.get("logical_code")
        cat = self.catalog.get(code) or {}
        if cat.get("is_channel") or _is_channel_code(code):
            return False
        if not (_sva._is_hollow_masonry(cand, self.catalog) or cat.get("is_compensator")):
            return False
        return (cand.get("placement_reason") == "STANDARD_FILL" and cand.get("node_index") is None
                and bool(cand.get("length_cm"))
                and all(self.course_fam.get(cc) == family for cc in courses))

    def _slot(self, entry):
        cand, lo, hi, courses = entry
        s = _Slot()
        s.lo, s.hi, s.code = lo, hi, cand.get("logical_code")
        cat = self.catalog.get(s.code) or {}
        s.compensator = bool(cat.get("is_compensator"))
        s.node = cand.get("node_index") is not None
        s.hollow = _sva._is_hollow_masonry(cand, self.catalog)
        s.orientable = _sva._is_orientable_small_void_piece(cand)
        s.void_off, s.void_half = _void_geometry(cand, self.p0, self.dir, lo, hi)
        s.side = (1 if (s.void_off or 0.0) >= 0.0 else -1) if s.orientable else 0
        return s

    def _build(self):
        sig_of = {}
        for c, entries in self.rows.items():
            sig_of[c] = tuple((round(lo, 1), round(hi, 1), cand.get("logical_code"),
                               1 if _sva._is_orientable_small_void_piece(cand) and
                               (_void_geometry(cand, self.p0, self.dir, lo, hi)[0] or 0.0) >= 0.0 else 0)
                              for cand, lo, hi, _courses in entries)
        order = sorted(set(sig_of.values()), key=lambda sig: min(c for c in sig_of if sig_of[c] == sig))
        name = dict((sig, i) for i, sig in enumerate(order))
        self.course_fam = dict((c, name[sig_of[c]]) for c in sig_of)
        self.fam, self.fam_rows = {}, {}
        for c in sorted(self.rows):
            f = self.course_fam[c]
            if f in self.fam:
                continue
            members = [cc for cc in sorted(self.rows) if self.course_fam[cc] == f]
            slots = []
            for index, entry in enumerate(self.rows[c]):
                s = self._slot(entry)
                # Movel so' se, em TODAS as fiadas desta familia, o objeto nesta
                # posicao for preenchimento comum que nao aparece em fiada de outra
                # familia. Conferir so' a primeira fiada deixava mover um objeto
                # compartilhado com outra familia (medido: B19 levado para cima de
                # uma amarracao na fiada 3 da parede 8284502).
                s.movable = all(self._entry_movable(self.rows[cc][index], f) for cc in members)
                slots.append(s)
            self.fam[f] = slots
        self.weights = collections.Counter()
        courses = sorted(self.course_fam)
        for c in courses:
            if c + 1 in self.course_fam:
                self.weights[(self.course_fam[c], self.course_fam[c + 1])] += 1
        self.count = collections.Counter(self.course_fam.values())
        # Template por codigo = COPIA congelada: a busca reescreve os slots vivos
        # (codigo, comprimento), e um template que fosse o proprio slot mudaria
        # de comprimento no meio da busca (bug medido: B34 com 39 cm, trecho
        # deslocado 5 cm e buraco de 6 cm na parede 8284502).
        self.template = {}
        for f in sorted(self.fam):
            for s in self.fam[f]:
                if s.code not in self.template:
                    self.template[s.code] = s.copy()

    # ------------------------------------------------------------ custo
    def _window(self, f, run):
        slots = self.fam[f]
        return (slots[run[0]].lo - WINDOW_PAD_CM, slots[run[-1]].hi + WINDOW_PAD_CM)

    def _local(self, f, run):
        """Custo so' na JANELA do trecho: as outras familias nao mudam durante a
        avaliacao, entao a diferenca entre duas ordens e' exata."""
        window = self._window(f, run)
        v = co = 0
        faces_f = _internal_faces(self.fam[f], self.length, self.edges, window)
        wider = (window[0] - FACE_TOLERANCE_CM, window[1] + FACE_TOLERANCE_CM)
        for (a, b), k in self.weights.items():
            if f not in (a, b):
                continue
            v += k * _violations_between(self.fam[a], self.fam[b], self.tol, window)
            other = b if a == f else a
            if other != f:
                co += k * _coincident(faces_f, _internal_faces(self.fam[other], self.length, self.edges, wider))
        near = list(_in_window(self.fam[f], window[0], window[1]))
        cp = _compensator_guard(near, self.length) * self.count[f]
        ht = _half_blocks_near_ties(near, self.ties, self.half_code, self.half_tie_gap) * self.count[f]
        return v, co, cp, ht

    def totals(self):
        v = co = cp = 0
        for (a, b), k in self.weights.items():
            v += k * _violations_between(self.fam[a], self.fam[b], self.tol)
            co += k * _coincident(_internal_faces(self.fam[a], self.length, self.edges),
                                  _internal_faces(self.fam[b], self.length, self.edges))
        ht = 0
        for f in self.fam:
            cp += _compensator_guard(self.fam[f], self.length) * self.count[f]
            ht += _half_blocks_near_ties(self.fam[f], self.ties, self.half_code, self.half_tie_gap) * self.count[f]
        return {"violations": v, "coincident_faces": co, "compensator_guard": cp,
                "half_block_near_tie": ht,
                "stacked_joints": _stacks(self.fam, self.course_fam, self.length, self.edges)}

    # ------------------------------------------------------------ busca
    def _apply(self, f, run, codes, sides):
        slots = self.fam[f]
        gaps = [slots[run[k + 1]].lo - slots[run[k]].hi for k in range(len(run) - 1)]
        cur = slots[run[0]].lo
        for k, i in enumerate(run):
            tpl = self.template[codes[k]]
            length = tpl.hi - tpl.lo
            s = slots[i]
            s.lo, s.hi, s.code = cur, cur + length, codes[k]
            s.compensator, s.hollow, s.orientable = tpl.compensator, tpl.hollow, tpl.orientable
            s.void_off, s.void_half = tpl.void_off, tpl.void_half
            s.side = sides[k] if tpl.orientable else 0
            cur += length + (gaps[k] if k < len(gaps) else 0.0)

    def _snap(self, f, run):
        return [self.fam[f][i].copy() for i in run]

    def _restore(self, f, run, snap):
        for i, s in zip(run, snap):
            self.fam[f][i] = s.copy()

    def _best_sides(self, f, run):
        """Descida coordenada na orientacao dos B34 do trecho. Inverter UMA peca
        so' muda violacoes perto dela: cada teste mede so' a janela da propria
        peca (delta exato, as demais pecas ficam paradas durante o teste)."""
        slots = self.fam[f]
        pieces = [i for i in run if slots[i].orientable]
        touching = [(a, b, k) for (a, b), k in self.weights.items() if f in (a, b)]

        def cost(window):
            return sum(k * _violations_between(self.fam[a], self.fam[b], self.tol, window)
                       for a, b, k in touching)
        for _round in range(4):
            improved = False
            for i in pieces:
                window = (slots[i].lo - WINDOW_PAD_CM, slots[i].hi + WINDOW_PAD_CM)
                before = cost(window)
                slots[i].side = -slots[i].side
                if cost(window) < before:
                    improved = True
                else:
                    slots[i].side = -slots[i].side
            if not improved:
                break

    def optimize(self):
        runs = [(f, r) for f in sorted(self.fam) for r in _runs(self.fam[f])]
        changed_runs = set()
        for _pass in range(MAX_PASSES):
            changed = False
            for f, run in runs:
                orig = self._snap(f, run)
                ref = self._local(f, run)
                if ref[0] == 0:
                    continue
                ranked = []
                for index, codes in enumerate(self._arrangements_for(f, run)):
                    self._apply(f, run, codes, [s.side or 1 for s in orig])
                    self._best_sides(f, run)
                    cost = self._local(f, run)
                    if cost[0] < ref[0] and cost[1] <= ref[1] and cost[2] <= ref[2] and cost[3] <= ref[3]:
                        moved = sum(1 for o, i in zip(orig, run) if o.code != self.fam[f][i].code)
                        ranked.append((cost, moved, index, self._snap(f, run)))
                    self._restore(f, run, orig)
                if not ranked:
                    continue
                ranked.sort(key=lambda item: (item[0], item[1], item[2]))
                stacks_ref = _stacks(self.fam, self.course_fam, self.length, self.edges)
                for _cost, _moved, _index, snap in ranked:
                    self._restore(f, run, snap)
                    if _stacks(self.fam, self.course_fam, self.length, self.edges) <= stacks_ref:
                        changed = True
                        changed_runs.add((f, tuple(run)))
                        break
                    self._restore(f, run, orig)
            if not changed:
                break
        return changed_runs

    def _arrangements_for(self, f, run):
        return _arrangements(self.fam[f], run)


def _collect_rows(course_candidates, walls_to_create):
    """{wall_idx: {course: [(cand, lo, hi, courses)]}} ordenado por lo."""
    occ = {}
    for c in sorted(course_candidates or {}):
        for cand in course_candidates[c] or ():
            if cand.get("wall_idx") is None:
                continue
            occ.setdefault(id(cand), [cand, set()])[1].add(c)
    axes = {}
    walls = collections.defaultdict(lambda: collections.defaultdict(list))
    for cand, courses in occ.values():
        wi = cand["wall_idx"]
        if wi >= len(walls_to_create or ()):
            continue
        if wi not in axes:
            p0, wall_dir, _length = _axis(walls_to_create, wi)
            axes[wi] = (p0, wall_dir)
        p0, wall_dir = axes[wi]
        lo, hi = _extent_cm(cand, p0, wall_dir)
        frozen = frozenset(courses)
        for c in courses:
            walls[wi][c].append((cand, lo, hi, frozen))
    for wi in walls:
        for c in walls[wi]:
            walls[wi][c].sort(key=lambda e: (e[1], e[2], e[0].get("logical_code") or ""))
    return walls


def _translate(cand, delta_cm, wall_dir):
    d_ft = delta_cm / CM_PER_FT
    dx, dy = wall_dir.X * d_ft, wall_dir.Y * d_ft
    o = cand["origin_world"]
    cand["origin_world"] = XYZ(o.X + dx, o.Y + dy, o.Z)
    cells = []
    for cell in cand.get("cells_world") or []:
        p = cell["point"]
        cells.append({"point": XYZ(p.X + dx, p.Y + dy, p.Z), "size_local": cell["size_local"]})
    cand["cells_world"] = cells


def _write_back(wall, base_fam, changed_runs):
    """Leva a ordem escolhida para os candidatos reais de TODAS as fiadas da
    familia: cada objeto so' troca de lugar (e gira), nenhum e' recriado."""
    moved = rotated = 0
    done = set()
    for f, run in sorted(changed_runs):
        new = wall.fam[f]
        for c in sorted(wall.course_fam):
            if wall.course_fam[c] != f:
                continue
            entries = wall.rows[c]
            pools = collections.defaultdict(list)
            for i in run:
                pools[entries[i][0].get("logical_code")].append(entries[i][0])
            for i in run:
                cand = pools[new[i].code].pop(0)
                if id(cand) in done:
                    continue
                done.add(id(cand))
                lo, hi = _extent_cm(cand, wall.p0, wall.dir)
                delta = new[i].lo - lo
                if abs(delta) > 1e-6:
                    _translate(cand, delta, wall.dir)
                    moved += 1
                if new[i].orientable:
                    off, _half = _void_geometry(cand, wall.p0, wall.dir, new[i].lo, new[i].hi)
                    side = 1 if (off or 0.0) >= 0.0 else -1
                    if side != new[i].side:
                        _sva.rotate_candidate_180(cand)
                        rotated += 1
    return moved, rotated


def arrange_b34_runs(course_candidates, walls_to_create, openings_per_wall, catalog=None,
                     tolerance_cm=_sva.SMALL_VOID_ALIGN_TOLERANCE_CM, tie_positions_by_wall=None,
                     half_block_code=None, half_block_tie_gap_cm=0.0):
    """Aplica o arranjo conjunto. Devolve o resumo por parede alterada e os
    totais das guardas antes/depois (as guardas nunca pioram por construcao)."""
    summary = {"walls_changed": 0, "runs_changed": 0, "moved": 0, "rotated": 0,
               "before": {"violations": 0, "coincident_faces": 0, "compensator_guard": 0,
                          "half_block_near_tie": 0, "stacked_joints": 0},
               "after": {"violations": 0, "coincident_faces": 0, "compensator_guard": 0,
                         "half_block_near_tie": 0, "stacked_joints": 0},
               "walls": []}
    if not B34_RUN_ARRANGEMENT_ENABLED or not course_candidates or XYZ is None:
        return summary
    rows_by_wall = _collect_rows(course_candidates, walls_to_create)
    for wi in sorted(rows_by_wall):
        wall = _Wall(wi, rows_by_wall[wi], walls_to_create, openings_per_wall, catalog, tolerance_cm,
                     ties=(tie_positions_by_wall or {}).get(wi), half_code=half_block_code,
                     half_tie_gap_cm=half_block_tie_gap_cm)
        before = wall.totals()
        base_fam = dict((f, [s.copy() for s in slots]) for f, slots in wall.fam.items())
        changed = wall.optimize() if before["violations"] else set()
        after = wall.totals() if changed else before
        for key in summary["before"]:
            summary["before"][key] += before[key]
            summary["after"][key] += after[key]
        if not changed:
            continue
        moved, rotated = _write_back(wall, base_fam, changed)
        summary["walls_changed"] += 1
        summary["runs_changed"] += len(changed)
        summary["moved"] += moved
        summary["rotated"] += rotated
        summary["walls"].append({"wall_idx": wi, "before": before, "after": after})
    return summary
