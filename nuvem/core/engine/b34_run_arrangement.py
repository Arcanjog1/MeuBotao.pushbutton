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
# SECAO 64.2: as pecas do REPARO de abertura (`OPENING_REPAIR_FILL`) entram nas
# corridas - jamba -> no' como UMA unidade. O reparo e' preenchimento comum para
# todos os efeitos (wall_stepper, OPENING_REPAIR_PLACEMENT_REASON), mas ficava
# congelado: a corrida parava na primeira peca de reparo e o arranjo nao
# alcancava as pecas junto da jamba. As pontas da corrida continuam fixas (a
# face da jamba nao se move); a orientacao dos compensadores e a validacao
# CHANNEL sao refeitas depois (secao 64.1) e entram na aceitacao por parede.
B34_RUN_OPENING_REPAIR_MOVABLE = True
_MOVABLE_REASONS = ("STANDARD_FILL", "OPENING_REPAIR_FILL")
MAX_ARRANGEMENTS_PER_RUN = 240
# SECAO 61: composicao de MESMO comprimento (a ate' 2 pecas trocadas, sem mais
# especiais), aceita por dominancia e, por parede, pelos validadores de producao.
B34_RUN_COMPOSITION_ENABLED = True
MAX_COMPOSITIONS_PER_RUN = 40
MAX_ARRANGEMENTS_PER_COMPOSITION = 60
# 3 desde a secao 63.2: `B39 B39 C09 -> B34 B34 B19` (ponta da parede 8284574
# junto a no' T, sem especial) so' existe tirando 3 pecas; sem a orientacao
# conjunta da 63 o 3 nao muda nada na BUTANTA (medido)
COMPOSITION_MAX_REMOVED = 3
COMPOSITION_MAX_ADDED = 3
JOINT_REGULAR_TOLERANCE_CM = 0.05
# SECAO 62: orientacao otima exata por parede. A descida gulosa da secao 52 gira
# uma peca (ou um par) por vez e para quando nenhuma melhora sozinha; em corridas
# longas de B34 encadeadas entre fiadas a orientacao tem de alternar ao longo da
# cadeia inteira, e um trecho "fora de fase" so' se corrige girando varias pecas
# juntas. A DP enxerga isso: o custo de cada B34-fonte depende so' da orientacao
# dele e dos B34 que podem cobrir o vazado dele (a menos de meia peca), entao,
# em ordem de posicao, cada fator envolve variaveis vizinhas.
B34_ORIENTATION_DP_ENABLED = True
ORIENTATION_DP_MAX_BAND = 12
# SECAO 63: orientacao CONJUNTA na avaliacao de cada ordem/composicao (60/61).
# A descida antiga girava so' os B34 da familia do trecho, um por vez; a ordem
# que o humano usa pode exigir girar JUNTO o B34 da fiada vizinha (vizinhos) e
# dois B34 de uma vez (pares). Medido na ponta da parede 8284574: a composicao
# sem especial valia 32 (pior que as 16 atuais) na descida antiga e 0 com os dois
# giros juntos. A 62 (DP) gira mas nao reordena - nenhuma das duas achava sozinha.
NEIGHBOUR_FLIPS_ENABLED = True
NEIGHBOUR_REACH_CM = 40.0
# pares de inversao (ver `_Wall._pair_flips`)
PAIR_FLIPS_ENABLED = True
PAIR_FLIP_REACH_CM = 25.0
# Duas etapas (custo: conjunta em todas as ordens = 342 s na bancada, contra
# 19 s): a descida barata avalia TODAS as ordens; a conjunta so' reavalia as
# REFINE_TOP_K que passam nas guardas geometricas (nao dependem de orientacao),
# nao dominaram, e cujo LIMITE INFERIOR de vazado (`_violations_lower_bound`)
# ainda pode dominar - ordenadas por esse limite. K=4 ja' da' o mesmo resultado
# de K=8/16 e da conjunta em todas.
REFINE_TOP_K = 4
# alcance para achar as fontes cobertas por uma peca (centro do vazado a ate'
# ~9 cm do centro do B34; folga para qualquer peca do catalogo)
COVER_REACH_CM = 30.0
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
# SECAO 84 (correcao do usuario, 2026-09-28): FAIXA DE COMPENSACAO NA JAMBA.
# Compensador (C09) e pastilha (C04) junto de porta/janela ficam ENCOSTADOS no
# vao e na MESMA faixa vertical em todas as fiadas da lateral, em vez de
# alternar entre "junto do vao" e "20/40/60 cm para dentro". As fiadas da
# lateral sao resolvidas EM CONJUNTO (familias de fiada), so' PERMUTANDO as
# pecas moveis da corrida jamba -> primeira peca fixa (nenhuma peca criada ou
# removida). Restricoes duras (nunca pioram): prisma dos vazados pela
# geometria real das celulas, vazado menor do B34 (secao 52), compensadores
# encostados, meio bloco perto de amarracao, compensador longo na ponta da
# parede, junta coincidente NOVA fora da faixa e junta empilhada em 3+ fiadas.
# A unica isencao e' a face INTERNA do compensador encostado na jamba.
JAMB_COMPENSATOR_ALIGNMENT_ENABLED = True
# alcance da corrida a partir da jamba = BOND_STRIP_OPENING_INFLUENCE_CM
JAMB_REACH_CM = 60.0
# encostado = OPENING_ALIGNED_TOUCH_TOLERANCE_CM (junta de 1 cm + arredondamento)
JAMB_TOUCH_TOLERANCE_CM = 2.0
# ponto logo DENTRO do vao para saber se a abertura corta esta fiada
JAMB_INSIDE_PROBE_CM = 2.0
# vazado alinhado entre fiadas: centro a ate' 2,0 cm do centro de um vazado da
# peca de baixo/cima (aparelho corrido real: B19 sobre B39 = 0,9 cm; B34 x B39
# chega a 1,75 cm - 1,5 cm cegava a medida)
PRISM_ALIGNED_DC_MAX_CM = 2.0
JAMB_MAX_ORDERS_PER_FAMILY = 120
JAMB_JOINT_MAX_COMBINATIONS = 4096
JAMB_DESCENT_ROUNDS = 4


class _Slot(object):
    __slots__ = ("lo", "hi", "code", "side", "movable", "node", "hollow", "orientable",
                 "void_off", "void_half", "compensator", "cells", "cell_side")

    def __init__(self):
        self.lo = self.hi = 0.0
        self.code = None
        self.side = 0
        self.movable = self.node = self.hollow = self.orientable = self.compensator = False
        self.void_off = self.void_half = None
        # SECAO 84: TODAS as celulas (deslocamento do centro de cada uma ate' o
        # centro da peca, meia largura) na orientacao `cell_side`
        self.cells = ()
        self.cell_side = 0

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


def _cells_geometry(cand, p0, wall_dir, lo, hi):
    """SECAO 84: ((deslocamento com sinal do centro de CADA celula ate' o centro
    da peca, meia largura), ...) lidos das `cells_world` REAIS da peca - a
    geometria da familia, nao uma suposicao pelo codigo."""
    mid = (lo + hi) / 2.0
    out = []
    for cell in cand.get("cells_world") or []:
        pt = cell["point"]
        t_cell = ((pt.X - p0.X) * wall_dir.X + (pt.Y - p0.Y) * wall_dir.Y) * CM_PER_FT
        out.append((t_cell - mid, float(cell["size_local"][0]) * CM_PER_FT / 2.0))
    out.sort()
    return tuple(out)


def _cell_centers(slot):
    """Centros (t_cm) das celulas de `slot` na orientacao ATUAL dele: a peca
    orientavel (B34) girada 180 graus espelha as celulas em torno do centro."""
    cells = slot.cells
    if not cells:
        return ()
    mid = (slot.lo + slot.hi) / 2.0
    if slot.orientable and slot.side and slot.cell_side and slot.side != slot.cell_side:
        return tuple(mid - off for off, _half in cells)
    return tuple(mid + off for off, _half in cells)


def _catalog_template(code, catalog):
    """Slot-modelo de `code` lido do CATALOGO (celulas locais, em pes, eixo X da
    peca ao longo da parede) - para codigos que ainda nao existem na parede."""
    entry = (catalog or {}).get(code) or {}
    length = float(entry.get("length_cm") or 0.0)
    if length <= 0.0:
        return None
    s = _Slot()
    s.code, s.lo, s.hi = code, 0.0, length
    s.compensator = bool(entry.get("is_compensator"))
    cells = entry.get("cells_local") or []
    s.hollow = bool(cells) and not s.compensator
    if len(cells) >= 2:
        ordered = sorted(cells, key=lambda c: float(c["size_local"][0]) * float(c["size_local"][1]))
        a0 = float(ordered[0]["size_local"][0]) * float(ordered[0]["size_local"][1])
        a1 = float(ordered[1]["size_local"][0]) * float(ordered[1]["size_local"][1])
        if a0 <= _sva.SMALL_VOID_MAX_AREA_RATIO * a1:
            s.void_off = float(ordered[0]["center_local"][0]) * CM_PER_FT
            s.void_half = float(ordered[0]["size_local"][0]) * CM_PER_FT / 2.0
            s.orientable = len(cells) == 2
    s.side = (1 if (s.void_off or 0.0) >= 0.0 else -1) if s.orientable else 0
    s.cells = tuple(sorted((float(c["center_local"][0]) * CM_PER_FT, float(c["size_local"][0]) * CM_PER_FT / 2.0)
                           for c in cells)) if s.hollow else ()
    s.cell_side = s.side
    return s


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
    """Pecas que tocam [lo, hi], em ordem (fatia: `lo` tambem e' crescente -
    uma lista em vez de gerador, que custava uma volta Python por peca)."""
    i = _first_hi_at_least(slots, lo)
    low, high = i, len(slots)
    while low < high:
        middle = (low + high) // 2
        if slots[middle].lo <= hi:
            low = middle + 1
        else:
            high = middle
    return slots[i:low]


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


def _violations_lower_bound(lower, upper, tol_cm, window=None):
    """Limite INFERIOR das violacoes sobre qualquer orientacao das pecas moveis:
    conta so' o vazado que nenhuma combinacao de lado (da fonte e da peca que a
    cobre, quando moveis e orientaveis) alinha. Ignora o acoplamento entre pares
    (uma peca e' fonte e cobertura ao mesmo tempo), por isso e' so' limite."""
    count = 0
    for src, dst in ((lower, upper), (upper, lower)):
        pieces = src if window is None else _in_window(src, window[0], window[1])
        for p in pieces:
            if not p.orientable:
                continue
            p_sides = (-1, 1) if p.movable else (p.side,)
            saved_p = p.side
            aligned = False
            for p_side in p_sides:
                p.side = p_side
                t = _void_center(p)
                h = _covering(dst, t)
                if h is None:
                    aligned = True
                    break
                h_sides = (-1, 1) if (h.orientable and h.movable) else (h.side,)
                saved_h = h.side
                for h_side in h_sides:
                    h.side = h_side
                    if _offers(h, t, tol_cm) is not False:
                        aligned = True
                        break
                h.side = saved_h
                if aligned:
                    break
            p.side = saved_p
            if not aligned:
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
    """Compensadores encostados (regra #2 e 56.2)."""
    n = 0
    for a, b in zip(slots, slots[1:]):
        if a.compensator and b.compensator and 0.0 <= b.lo - a.hi <= TOUCH_TOLERANCE_CM:
            n += 1
    return n


def _long_compensator_extremes(slots, wall_len):
    """Compensador LONGO como peca extrema da parede (secao 58). Guarda separada
    da de compensadores encostados: somadas, a busca trocava um par encostado
    por um C09 na ponta - e o humano nao faz nenhuma das duas."""
    n = 0
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


def _combinations_with_replacement(items, size):
    """itertools.combinations_with_replacement (existe no 2.7, mas mantido
    explicito e deterministico)."""
    out = []

    def rec(start, cur):
        if len(cur) == size:
            out.append(tuple(cur))
            return
        for i in range(start, len(items)):
            cur.append(items[i])
            rec(i, cur)
            cur.pop()
    rec(0, [])
    return out


def _multiset_orders(counts, n, cap):
    keys = sorted(counts)
    counts = dict(counts)
    out, cur = [], []

    def rec():
        if len(out) >= cap:
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
                 ties=None, half_code=None, half_tie_gap_cm=0.0, fill_codes=(),
                 joint_identity_guard=False, jamb_alignment=False):
        self.wall_idx = wall_idx
        # SECAO 84: faixa de compensacao na jamba (so' quando o chamador liga)
        self.jamb_alignment = bool(jamb_alignment) and JAMB_COMPENSATOR_ALIGNMENT_ENABLED
        self.jamb_conflicts = []
        # SECAO 81.1: com a guarda, nenhuma troca pode criar junta coincidente
        # entre fiadas vizinhas numa POSICAO onde ela nao existia (a guarda de
        # contagem da janela aceitava trocar junta isenta junto da jamba por junta
        # a prumo de verdade no meio da parede)
        self.joint_guard = bool(joint_identity_guard)
        self.tol = tol_cm
        # SECAO 77: `ties` pode vir por fiada ({fiada: [t_cm]}) quando um no'
        # da parede nao e' encontro em alguma fiada
        self.ties_by_course = ties if isinstance(ties, dict) else None
        self.ties = [] if isinstance(ties, dict) else list(ties or [])
        self.half_code = half_code
        self.half_tie_gap = half_tie_gap_cm
        self.fill_codes = sorted(fill_codes or ())
        self.p0, self.dir, self.length = _axis(walls_to_create, wall_idx)
        self.edges = []
        self.openings_cm = []
        ops = (openings_per_wall or [])
        for op in (ops[wall_idx] if wall_idx < len(ops) else None) or ():
            lo_cm, hi_cm = float(op[0]) * CM_PER_FT, float(op[1]) * CM_PER_FT
            self.edges.extend([lo_cm, hi_cm])
            self.openings_cm.append((min(lo_cm, hi_cm), max(lo_cm, hi_cm)))
        self.edges.sort()
        self.openings_cm.sort()
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
        reason = cand.get("placement_reason")
        movable_reason = (reason in _MOVABLE_REASONS) if B34_RUN_OPENING_REPAIR_MOVABLE \
            else reason == "STANDARD_FILL"
        return (movable_reason and cand.get("node_index") is None
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
        s.cells = _cells_geometry(cand, self.p0, self.dir, lo, hi) if s.hollow else ()
        s.cell_side = s.side
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
    def _half_near_ties(self, slots, f):
        """HALF_BLOCK_NEAR_TIE da familia `f`: por fiada quando as posicoes de
        amarracao dependem da fiada (secao 77), senao a conta de sempre."""
        if self.ties_by_course is None:
            return _half_blocks_near_ties(slots, self.ties, self.half_code, self.half_tie_gap) * self.count[f]
        return sum(_half_blocks_near_ties(slots, self.ties_by_course.get(c) or [], self.half_code,
                                          self.half_tie_gap)
                   for c in sorted(self.course_fam) if self.course_fam[c] == f)

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
            # vazado: TODAS as interfaces na janela - um vizinho girado junto
            # pode mexer na interface dele com uma terceira familia
            v += k * _violations_between(self.fam[a], self.fam[b], self.tol, window)
            if f not in (a, b):
                continue
            other = b if a == f else a
            if other != f:
                co += k * _coincident(faces_f, _internal_faces(self.fam[other], self.length, self.edges, wider))
        near = list(_in_window(self.fam[f], window[0], window[1]))
        cp = _compensator_guard(near, self.length) * self.count[f]
        ht = self._half_near_ties(near, f)
        # extremo da parede: olha a fileira inteira (a janela pode nao conter a ponta)
        ex = _long_compensator_extremes(self.fam[f], self.length) * self.count[f]
        return v, co, cp, ht, ex

    def _coincident_positions(self, f, window):
        """[(face, familia vizinha)] das faces da familia `f` na janela que
        coincidem com uma face de uma familia de fiada VIZINHA (secao 81.1)."""
        faces_f = _internal_faces(self.fam[f], self.length, self.edges, window)
        wider = (window[0] - FACE_TOLERANCE_CM, window[1] + FACE_TOLERANCE_CM)
        out = []
        for other in sorted(set(b if a == f else a for (a, b) in self.weights if f in (a, b))):
            if other == f:
                continue
            faces_o = _internal_faces(self.fam[other], self.length, self.edges, wider)
            for face in faces_f:
                if _has_value_near(faces_o, face, FACE_TOLERANCE_CM):
                    out.append((face, other))
        return out

    def _creates_joint(self, f, window, ref_positions):
        """True se a familia `f` passou a ter junta coincidente numa posicao
        (contra uma familia vizinha) que nao existia em `ref_positions`."""
        if not self.joint_guard:
            return False
        for face, other in self._coincident_positions(f, window):
            if not any(o == other and abs(face - q) <= FACE_TOLERANCE_CM for q, o in ref_positions):
                return True
        return False

    def _local_bound(self, f, run):
        window = self._window(f, run)
        return sum(k * _violations_lower_bound(self.fam[a], self.fam[b], self.tol, window)
                   for (a, b), k in sorted(self.weights.items()))

    def totals(self):
        v = co = cp = 0
        for (a, b), k in self.weights.items():
            v += k * _violations_between(self.fam[a], self.fam[b], self.tol)
            co += k * _coincident(_internal_faces(self.fam[a], self.length, self.edges),
                                  _internal_faces(self.fam[b], self.length, self.edges))
        ht = ex = 0
        for f in self.fam:
            cp += _compensator_guard(self.fam[f], self.length) * self.count[f]
            ex += _long_compensator_extremes(self.fam[f], self.length) * self.count[f]
            ht += self._half_near_ties(self.fam[f], f)
        out = {"violations": v, "coincident_faces": co, "compensator_guard": cp,
               "long_compensator_extremes": ex, "half_block_near_tie": ht,
               "stacked_joints": _stacks(self.fam, self.course_fam, self.length, self.edges)}
        if self.jamb_alignment:
            out["jamb_compensator_distance"] = round(sum(self._jamb_distance(f) * self.count[f]
                                                         for f in self.fam), 3)
        return out

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
            s.cells, s.cell_side = tpl.cells, tpl.cell_side
            s.side = sides[k] if tpl.orientable else 0
            cur += length + (gaps[k] if k < len(gaps) else 0.0)

    def _snap(self, f, run):
        return [self.fam[f][i].copy() for i in run]

    def _restore(self, f, run, snap):
        for i, s in zip(run, snap):
            self.fam[f][i] = s.copy()

    def _best_sides(self, f, run, joint=False):
        """Descida coordenada na orientacao dos B34 do trecho - e, com
        NEIGHBOUR_FLIPS_ENABLED, dos B34 de preenchimento das outras familias que
        se sobrepoem ao trecho. Inverter UMA peca so' muda violacoes perto dela:
        cada teste mede a janela da propria peca em TODAS as interfaces."""
        slots = self.fam[f]
        pieces = [(slots[i], f) for i in run if slots[i].orientable]
        if joint and NEIGHBOUR_FLIPS_ENABLED and run:
            lo = slots[run[0]].lo - NEIGHBOUR_REACH_CM
            hi = slots[run[-1]].hi + NEIGHBOUR_REACH_CM
            for other in sorted(self.fam):
                if other == f:
                    continue
                for slot in _in_window(self.fam[other], lo, hi):
                    if slot.orientable and slot.movable:
                        pieces.append((slot, other))
        # interfaces de cada familia: inverter pecas das familias `families` so'
        # muda essas parcelas (as outras sao iguais antes e depois do teste)
        touching = collections.defaultdict(list)
        for (a, b), k in sorted(self.weights.items()):
            touching[a].append((a, b, k))
            if b != a:
                touching[b].append((a, b, k))

        def cost(items):
            return self._flip_cost(items, touching)
        for _round in range(4):
            improved = False
            for item in pieces:
                slot = item[0]
                before = cost((item,))
                slot.side = -slot.side
                if cost((item,)) < before:
                    improved = True
                else:
                    slot.side = -slot.side
            if joint and PAIR_FLIPS_ENABLED and not improved:
                improved = self._pair_flips(pieces, cost)
            if not improved:
                break

    def _flip_cost(self, items, touching):
        """Violacoes que PODEM mudar quando as pecas `items` [(slot, familia)]
        giram: cada peca como FONTE (contra a peca que cobre o vazado dela) e
        cada fonte que ELA cobre. Inverter so' muda o centro do vazado da propria
        peca, entao a diferenca antes/depois e' exatamente a da janela inteira.
        Chave por (interface, sentido, fonte): cada fonte tem uma cobertura so'."""
        counted = {}
        for p, g in items:
            for a, b, k in touching.get(g, ()):
                for direction, (src_family, dst_family) in enumerate(((a, b), (b, a))):
                    if src_family == g:
                        key = (a, b, direction, id(p))
                        if key not in counted:
                            t = _void_center(p)
                            h = _covering(self.fam[dst_family], t)
                            counted[key] = k if (h is not None and _offers(h, t, self.tol) is False) else 0
                    if dst_family == g:
                        for q in _in_window(self.fam[src_family], p.lo - COVER_REACH_CM, p.hi + COVER_REACH_CM):
                            if not q.orientable:
                                continue
                            key = (a, b, direction, id(q))
                            if key in counted:
                                continue
                            t = _void_center(q)
                            if _covering(self.fam[dst_family], t) is not p:
                                continue
                            counted[key] = k if _offers(p, t, self.tol) is False else 0
        return sum(counted.values())

    def _pair_flips(self, pieces, cost):
        """Inverte DUAS pecas de FAMILIAS DIFERENTES, uma sobre a outra (centros a
        ate' PAIR_FLIP_REACH_CM), de uma vez - primeira melhora, ordem fixa.
        Minimo local medido na parede 8284574 (ponta junto a no' T): o vazado
        menor do B34 da fiada par so' alinha se o B34 da impar logo acima girar
        JUNTO - cada inversao isolada fica em 32 ou sobe para 64; o par vai a 0."""
        ordered = sorted(pieces, key=lambda item: (item[0].lo, item[1]))
        for a in range(len(ordered)):
            pa, fa = ordered[a]
            mid_a = (pa.lo + pa.hi) / 2.0
            for b in range(a + 1, len(ordered)):
                pb, fb = ordered[b]
                if (pb.lo + pb.hi) / 2.0 - mid_a > PAIR_FLIP_REACH_CM:
                    break
                if fa == fb:
                    continue
                pair = (ordered[a], ordered[b])
                before = cost(pair)
                if before == 0:
                    continue
                pa.side, pb.side = -pa.side, -pb.side
                if cost(pair) < before:
                    return True
                pa.side, pb.side = -pa.side, -pb.side
        return False

    def optimize(self):
        runs = [(f, r) for f in sorted(self.fam) for r in _runs(self.fam[f])]
        changed_runs = set()
        for _pass in range(MAX_PASSES):
            changed = False
            for f, run in runs:
                orig = self._snap(f, run)
                neighbour_sides = self._neighbour_sides(f, run)
                ref = self._local(f, run)
                if ref[0] == 0:
                    continue
                window = self._window(f, run)
                ref_joints = self._coincident_positions(f, window) if self.joint_guard else ()
                ranked, pool = [], []
                sides0 = [s.side or 1 for s in orig]
                for index, codes in enumerate(self._arrangements_for(f, run)):
                    self._apply(f, run, codes, sides0)
                    self._best_sides(f, run)
                    cost = self._local(f, run)
                    if all(cost[k] <= ref[k] for k in range(1, len(ref))) and \
                            not self._creates_joint(f, window, ref_joints):
                        if cost[0] < ref[0]:
                            moved = sum(1 for o, i in zip(orig, run) if o.code != self.fam[f][i].code)
                            ranked.append((cost, moved, index, self._snap(f, run), self._neighbour_sides(f, run)))
                        else:
                            bound = self._local_bound(f, run)
                            if bound < ref[0]:
                                pool.append((bound, cost[0], index, codes))
                    self._restore(f, run, orig)
                    self._set_neighbour_sides(neighbour_sides)
                if REFINE_TOP_K and (NEIGHBOUR_FLIPS_ENABLED or PAIR_FLIPS_ENABLED):
                    for _bound, _v, index, codes in sorted(pool)[:REFINE_TOP_K]:
                        self._apply(f, run, codes, sides0)
                        self._best_sides(f, run, joint=True)
                        cost = self._local(f, run)
                        if cost[0] < ref[0] and not self._creates_joint(f, window, ref_joints):
                            moved = sum(1 for o, i in zip(orig, run) if o.code != self.fam[f][i].code)
                            ranked.append((cost, moved, index, self._snap(f, run), self._neighbour_sides(f, run)))
                        self._restore(f, run, orig)
                        self._set_neighbour_sides(neighbour_sides)
                if not ranked:
                    continue
                ranked.sort(key=lambda item: (item[0], item[1], item[2]))
                stacks_ref = _stacks(self.fam, self.course_fam, self.length, self.edges)
                for _cost, _moved, _index, snap, sides in ranked:
                    self._restore(f, run, snap)
                    self._set_neighbour_sides(sides)
                    if _stacks(self.fam, self.course_fam, self.length, self.edges) <= stacks_ref:
                        changed = True
                        changed_runs.add((f, tuple(run)))
                        break
                    self._restore(f, run, orig)
                    self._set_neighbour_sides(neighbour_sides)
            if not changed:
                break
        return changed_runs

    def _neighbour_sides(self, f, run):
        """[(slot, lado)] dos B34 de preenchimento das OUTRAS familias ao alcance."""
        if not NEIGHBOUR_FLIPS_ENABLED or not run:
            return []
        lo = self.fam[f][run[0]].lo - NEIGHBOUR_REACH_CM
        hi = self.fam[f][run[-1]].hi + NEIGHBOUR_REACH_CM
        out = []
        for other in sorted(self.fam):
            if other == f:
                continue
            for slot in _in_window(self.fam[other], lo, hi):
                if slot.orientable and slot.movable:
                    out.append((slot, slot.side))
        return out

    def _set_neighbour_sides(self, sides):
        for slot, side in sides:
            slot.side = side

    def _arrangements_for(self, f, run):
        return _arrangements(self.fam[f], run)

    # ------------------------------------------------------------ composicao (secao 61)
    def _tpl(self, code):
        if code not in self.template:
            tpl = _catalog_template(code, self.catalog)
            if tpl is None:
                return None
            self.template[code] = tpl
        return self.template[code]

    def _neighbour_multisets(self, codes, joint):
        """Multiconjuntos a ate' COMPOSITION_MAX_REMOVED pecas trocadas por ate'
        COMPOSITION_MAX_ADDED pecas de MESMO comprimento (juntas incluidas), sem
        aumentar o numero de especiais (compensadores). Ordem deterministica."""
        units = {}
        for code in self.fill_codes:
            tpl = self._tpl(code)
            if tpl is not None:
                units[code] = int(round((tpl.hi - tpl.lo + joint) * 10.0))
        if any(c not in units for c in codes):
            return []
        base = collections.Counter(codes)
        pool = sorted(units)
        adds = []
        for size in range(1, COMPOSITION_MAX_ADDED + 1):
            adds.extend(_combinations_with_replacement(pool, size))
        removes = []
        for size in range(1, COMPOSITION_MAX_REMOVED + 1):
            for rem in _combinations_with_replacement(sorted(base), size):
                need = collections.Counter(rem)
                if all(base[k] >= v for k, v in need.items()):
                    removes.append(rem)
        seen, out = set(), []
        for rem in removes:
            total = sum(units[k] for k in rem)
            specials = sum(1 for k in rem if self._tpl(k).compensator)
            for add in adds:
                if sorted(add) == sorted(rem) or sum(units[k] for k in add) != total:
                    continue
                if sum(1 for k in add if self._tpl(k).compensator) > specials:
                    continue
                new = base - collections.Counter(rem) + collections.Counter(add)
                key = tuple(sorted(new.elements()))
                if key not in seen:
                    seen.add(key)
                    out.append(key)
                    if len(out) >= MAX_COMPOSITIONS_PER_RUN:
                        return out
        return out

    def _splice(self, f, run, codes, joint):
        slots = self.fam[f]
        cur = slots[run[0]].lo
        new = []
        for code in codes:
            tpl = self._tpl(code)
            s = tpl.copy()
            s.lo, s.hi = cur, cur + (tpl.hi - tpl.lo)
            s.movable, s.node = True, False
            new.append(s)
            cur = s.hi + joint
        self.fam[f] = slots[:run[0]] + new + slots[run[-1] + 1:]
        return list(range(run[0], run[0] + len(new)))

    def _compose(self, f, run):
        slots = self.fam[f]
        gaps = [slots[run[k + 1]].lo - slots[run[k]].hi for k in range(len(run) - 1)]
        if not gaps or any(abs(g - gaps[0]) > JOINT_REGULAR_TOLERANCE_CM for g in gaps):
            return False
        joint = gaps[0]
        codes = [slots[i].code for i in run]
        ref = self._local(f, run)
        ref_specials = sum(1 for i in run if slots[i].compensator)
        if ref[0] == 0 and ref_specials == 0:
            return False  # nada a ganhar: dominancia exige menos vazado ou menos especiais
        original = list(slots)
        neighbour_sides = self._neighbour_sides(f, run)
        best = None
        pool = []
        # a composicao cobre o MESMO trecho (pontas fixas): a janela da corrida
        # original contem a nova
        window = self._window(f, run)
        ref_joints = self._coincident_positions(f, window) if self.joint_guard else ()

        def consider(order, specials, ms_index, arr_index, joint_sides):
            new_run = self._splice(f, run, order, joint)
            self._best_sides(f, new_run, joint=joint_sides)
            cost = self._local(f, new_run)
            guards_ok = all(cost[k] <= ref[k] for k in range(1, len(ref))) and \
                not self._creates_joint(f, window, ref_joints)
            dominates = ((cost[0] < ref[0] and specials <= ref_specials)
                         or (cost[0] <= ref[0] and specials < ref_specials))
            found = None
            bound = None
            if guards_ok and not dominates and not joint_sides:
                bound = self._local_bound(f, new_run)
            if guards_ok and dominates:
                found = ((cost[0], specials, len(order), ms_index, arr_index),
                         [x.copy() for x in self.fam[f]], self._neighbour_sides(f, new_run))
            self.fam[f] = list(original)
            self._set_neighbour_sides(neighbour_sides)
            return found, guards_ok, bound
        for ms_index, multiset in enumerate(self._neighbour_multisets(codes, joint)):
            specials = sum(1 for code in multiset if self._tpl(code).compensator)
            counts = collections.Counter(multiset)
            for arr_index, order in enumerate(_multiset_orders(counts, len(multiset),
                                                                MAX_ARRANGEMENTS_PER_COMPOSITION)):
                found, guards_ok, bound = consider(order, specials, ms_index, arr_index, False)
                if found is not None:
                    if best is None or found[0] < best[0]:
                        best = found
                elif guards_ok and bound is not None and (
                        (bound < ref[0] and specials <= ref_specials)
                        or (bound <= ref[0] and specials < ref_specials)):
                    pool.append((bound, specials, ms_index, arr_index, tuple(order)))
        if REFINE_TOP_K and (NEIGHBOUR_FLIPS_ENABLED or PAIR_FLIPS_ENABLED):
            for _bound, specials, ms_index, arr_index, order in sorted(pool)[:REFINE_TOP_K]:
                found, _ok, _v2 = consider(list(order), specials, ms_index, arr_index, True)
                if found is not None and (best is None or found[0] < best[0]):
                    best = found
        if best is None:
            return False
        stacks_ref = _stacks(self.fam, self.course_fam, self.length, self.edges)
        self.fam[f] = best[1]
        self._set_neighbour_sides(best[2])
        if _stacks(self.fam, self.course_fam, self.length, self.edges) <= stacks_ref:
            return True
        self.fam[f] = original
        self._set_neighbour_sides(neighbour_sides)
        return False

    # ------------------------------------------------------------ orientacao exata (secao 62)
    def _source_violations(self, f, i, weights_by_family):
        """Violacoes em que o B34 (f, i) e' a FONTE, contra as familias vizinhas,
        ja' multiplicadas pela quantidade de interfaces."""
        p = self.fam[f][i]
        t = _void_center(p)
        n = 0
        for other, k in weights_by_family.get(f, ()):
            h = _covering(self.fam[other], t)
            if h is not None and _offers(h, t, self.tol) is False:
                n += k
        return n

    def orient_exact(self):
        """Orientacao otima dos B34 de preenchimento (movel, orientavel) desta
        parede. Devolve quantas orientacoes mudaram (0 se o otimo nao for
        ESTRITAMENTE melhor ou se a banda passar do teto)."""
        if not B34_ORIENTATION_DP_ENABLED:
            return 0
        weights_by_family = collections.defaultdict(list)
        for (a, b), k in sorted(self.weights.items()):
            weights_by_family[a].append((b, k))
            if a != b:
                weights_by_family[b].append((a, k))
        variables = []
        for f in sorted(self.fam):
            for i, slot in enumerate(self.fam[f]):
                if slot.orientable and slot.movable and slot.void_off is not None:
                    variables.append((slot.mid, f, i))
        if not variables:
            return 0
        variables.sort()
        position = dict(((f, i), n) for n, (_mid, f, i) in enumerate(variables))
        # fatores: um por B34-fonte (variavel ou fixo) que dependa de alguma variavel
        factors = collections.defaultdict(list)
        band = 0
        for f in sorted(self.fam):
            for i, slot in enumerate(self.fam[f]):
                if not slot.orientable or slot.void_off is None:
                    continue
                involved = set()
                if (f, i) in position:
                    involved.add(position[(f, i)])
                saved = slot.side
                for side in (-1, 1):
                    slot.side = side
                    t = _void_center(slot)
                    for other, _k in weights_by_family.get(f, ()):
                        j = _first_hi_at_least(self.fam[other], t)
                        if j < len(self.fam[other]) and self.fam[other][j].lo - 1e-6 <= t and \
                                (other, j) in position:
                            involved.add(position[(other, j)])
                    if (f, i) not in position:
                        break  # fonte fixa: o lado dela nao muda
                slot.side = saved
                if not involved:
                    continue
                low, high = min(involved), max(involved)
                band = max(band, high - low)
                factors[high].append((f, i, sorted(involved)))
        if band > ORIENTATION_DP_MAX_BAND:
            return 0
        slots_of = [self.fam[f][i] for _mid, f, i in variables]
        current = [s.side for s in slots_of]
        # TABELA por fator: custo para cada combinacao dos lados das variaveis
        # envolvidas (no maximo a fonte e os B34 que podem cobrir o vazado).
        # A DP so' consulta a tabela - nada de geometria dentro do laco.
        tables = collections.defaultdict(list)
        current_cost = 0
        for at in sorted(factors):
            for f, i, positions in factors[at]:
                table = []
                for mask in range(1 << len(positions)):
                    for bit, q in enumerate(positions):
                        slots_of[q].side = 1 if (mask >> bit) & 1 else -1
                    table.append(self._source_violations(f, i, weights_by_family))
                for q in positions:
                    slots_of[q].side = current[q]
                tables[at].append((positions, table))
                mask = 0
                for bit, q in enumerate(positions):
                    if current[q] > 0:
                        mask |= 1 << bit
                current_cost += table[mask]

        def factor_cost(at, full):
            total = 0
            for positions, table in tables.get(at, ()):
                mask = 0
                for bit, q in enumerate(positions):
                    if (full >> (at - q)) & 1:
                        mask |= 1 << bit
                total += table[mask]
            return total

        # Estado = MASCARA DE BITS das ultimas `band` variaveis: bit j = lado da
        # variavel n-j (1 = lado positivo). Mesmo resultado da versao com tuplas,
        # mas aritmetica inteira - o IronPython 2.7 do Revit roda a DP ~3x mais
        # rapido so' com a tabela de fatores e bem mais com a mascara.
        keep_mask = (1 << band) - 1
        layer = {0: (0, None)}
        history = []
        for n in range(len(slots_of)):
            nxt = {}
            # ordem ORDENADA: empate entre caminhos de mesmo custo decide igual em
            # qualquer runtime (dict do IronPython 2.7 nao guarda ordem de insercao)
            for state, (cost, _prev) in sorted(layer.items()):
                shifted = state << 1
                for bit in (0, 1):
                    full = shifted | bit
                    total = cost + factor_cost(n, full)
                    key = full & keep_mask
                    if key not in nxt or total < nxt[key][0]:
                        nxt[key] = (total, (state, bit))
            history.append(nxt)
            layer = nxt
        best_state = min(sorted(layer), key=lambda st: layer[st][0])
        best_cost = layer[best_state][0]
        if best_cost >= current_cost:
            for slot, side in zip(slots_of, current):
                slot.side = side
            return 0
        chosen = [0] * len(slots_of)
        state = best_state
        for n in range(len(slots_of) - 1, -1, -1):
            _total, (prev, bit) = history[n][state]
            chosen[n] = 1 if bit else -1
            state = prev
        changed = 0
        for slot, side, old in zip(slots_of, chosen, current):
            slot.side = side
            if side != old:
                changed += 1
        return changed

    def compose(self):
        """Uma composicao aceita muda os indices da familia: recomeca as corridas
        dela. Teto de iteracoes por parede, deterministico."""
        if not B34_RUN_COMPOSITION_ENABLED or not self.fill_codes:
            return 0
        accepted = 0
        for f in sorted(self.fam):
            for _guard in range(64):
                changed = False
                for run in _runs(self.fam[f]):
                    if self._compose(f, run):
                        accepted += 1
                        changed = True
                        break
                if not changed:
                    break
        return accepted

    # ------------------------------------------------------------ faixa de jamba (secao 84)
    def _active_jamb_edges(self, f):
        """[(t_cm da borda, sentido)] das jambas ATIVAS na familia `f` - a fileira
        nao tem peca logo dentro do vao (a abertura corta esta fiada). Sentido
        -1: as pecas ficam antes da borda (borda inicial do vao); +1: depois."""
        slots = self.fam[f]
        out = []
        for lo, hi in self.openings_cm:
            if hi - lo <= 2.0 * JAMB_INSIDE_PROBE_CM:
                continue
            if _covering(slots, lo + JAMB_INSIDE_PROBE_CM) is None:
                out.append((lo, -1))
            if _covering(slots, hi - JAMB_INSIDE_PROBE_CM) is None:
                out.append((hi, 1))
        return out

    @staticmethod
    def _distance_to_edge(slot, edge, d):
        """Distancia (cm) da face de `slot` voltada para a jamba ate' a borda
        (0 = encostado, contando a junta dentro da tolerancia)."""
        return (slot.lo - edge) if d > 0 else (edge - slot.hi)

    def _strip_distance(self, f, i, edges):
        """Distancia (cm) do compensador `self.fam[f][i]` ate' a jamba ativa mais
        proxima do lado dele, SEM contar os compensadores entre ele e o vao: um
        par C04+C09 encostado e' UMA faixa (os dois contam 0). None fora do
        alcance de 2x JAMB_REACH_CM ou do lado errado da borda."""
        slots = self.fam[f]
        s = slots[i]
        best = None
        for edge, d in edges:
            raw = self._distance_to_edge(s, edge, d)
            if raw < -JAMB_TOUCH_TOLERANCE_CM or raw > 2.0 * JAMB_REACH_CM:
                continue
            strip = 0.0
            k = i - d
            while 0 <= k < len(slots):
                q = slots[k]
                if self._distance_to_edge(q, edge, d) < -JAMB_TOUCH_TOLERANCE_CM:
                    break
                if q.compensator:
                    # comprimento do compensador + a junta do lado de fora dele
                    strip += (slots[k + 1].lo - q.lo) if d > 0 else (q.hi - slots[k - 1].hi)
                k -= d
            dist = max(raw - strip, 0.0)
            if best is None or dist < best:
                best = dist
        return best

    def _jamb_distance(self, f):
        """Soma das distancias dos compensadores da familia `f` ate' a jamba ativa
        mais proxima do lado deles (teto JAMB_REACH_CM). Encostado (ou atras de
        outro compensador encostado) conta 0 - a folga da junta nao penaliza."""
        edges = self._active_jamb_edges(f)
        if not edges:
            return 0.0
        total = 0.0
        for i, s in enumerate(self.fam[f]):
            if not s.compensator:
                continue
            best = self._strip_distance(f, i, edges)
            if best is None or best <= JAMB_TOUCH_TOLERANCE_CM:
                continue
            total += min(best, JAMB_REACH_CM)
        return round(total, 3)

    def _jamb_strip_faces(self, f):
        """Faces ISENTAS da familia `f`: as DUAS faces da junta interna da faixa
        de compensadores (C09/C04) encostada numa jamba ativa - a do compensador
        mais de dentro e a da peca vizinha do outro lado da mesma junta. Nao vale
        para a junta seguinte (depois do B19/B39) nem para ponta de no'."""
        out = []
        edges = self._active_jamb_edges(f)
        slots = self.fam[f]
        for edge, d in edges:
            i = self._touching_index(slots, edge, d)
            if i is None or not slots[i].compensator:
                continue
            # anda pela faixa (compensadores encostados) ate' a ultima peca dela;
            # as juntas ENTRE compensadores da faixa (C04|C09) tambem sao dela
            j = i
            while 0 <= j + d < len(slots) and slots[j + d].compensator:
                gap = (slots[j + d].lo - slots[j].hi) if d > 0 else (slots[j].lo - slots[j + d].hi)
                if gap > RUN_MAX_GAP_CM:
                    break
                out.extend([slots[j].hi, slots[j + d].lo] if d > 0 else [slots[j].lo, slots[j + d].hi])
                j += d
            last = slots[j]
            out.append(last.hi if d > 0 else last.lo)
            if 0 <= j + d < len(slots):
                nxt = slots[j + d]
                gap = (nxt.lo - last.hi) if d > 0 else (last.lo - nxt.hi)
                if gap <= RUN_MAX_GAP_CM:
                    out.append(nxt.lo if d > 0 else nxt.hi)
        out.sort()
        return out

    @staticmethod
    def _touching_index(slots, edge, d):
        for i, s in enumerate(slots):
            face = s.lo if d > 0 else s.hi
            if abs(face - edge) <= JAMB_TOUCH_TOLERANCE_CM:
                return i
        return None

    def _courses_of(self, f):
        return [c for c in sorted(self.course_fam) if self.course_fam[c] == f]

    def _jamb_units(self):
        """({chave: [(familia, indices em ordem de posicao, [(borda, sentido)])]},
        [conflitos de peca fixa]). A unidade e' a corrida MOVEL contigua que sai
        da jamba (ate' JAMB_REACH_CM ou a primeira peca fixa: no', canaleta, verga)
        e contem compensador. Num pilarete as corridas das duas jambas que se
        sobrepoem viram UMA unidade (o compensador vai para a jamba mais perto)."""
        units = collections.defaultdict(list)
        blocked = []
        for f in sorted(self.fam):
            slots = self.fam[f]
            per_edge = []
            for edge, d in self._active_jamb_edges(f):
                i0 = self._touching_index(slots, edge, d)
                if i0 is None:
                    continue
                idx = []
                j = i0
                while 0 <= j < len(slots):
                    s = slots[j]
                    if self._distance_to_edge(s, edge, d) >= JAMB_REACH_CM or not s.movable:
                        break
                    if idx:
                        prev = slots[idx[-1]]
                        gap = (s.lo - prev.hi) if d > 0 else (prev.lo - s.hi)
                        if gap < -FACE_TOLERANCE_CM or gap > RUN_MAX_GAP_CM:
                            break
                    idx.append(j)
                    j += d
                # compensador ao alcance, mas atras de peca fixa: permutar nao chega nele
                behind = []
                k = j
                while 0 <= k < len(slots):
                    s = slots[k]
                    dist = self._distance_to_edge(s, edge, d)
                    if dist >= JAMB_REACH_CM:
                        break
                    if s.compensator and dist >= -JAMB_TOUCH_TOLERANCE_CM:
                        behind.append(k)
                    k += d
                if behind:
                    blocked.append({"wall_idx": self.wall_idx, "edges_cm": [round(edge, 1)], "side": d,
                                    "courses": self._courses_of(f),
                                    "distance_cm": round(min(self._distance_to_edge(slots[k2], edge, d)
                                                             for k2 in behind), 1),
                                    "codes": [slots[k2].code for k2 in behind],
                                    "reasons": ["FIXED_PIECE_BETWEEN"]})
                if len(idx) < 2 or not any(slots[i].compensator for i in idx):
                    continue
                per_edge.append((sorted(idx), [(edge, d)]))
            merged = []
            for idx, edges in sorted(per_edge):
                if merged and set(idx) & set(merged[-1][0]):
                    merged[-1] = (sorted(set(idx) | set(merged[-1][0])), merged[-1][1] + edges)
                else:
                    merged.append((idx, edges))
            for idx, edges in merged:
                key = tuple(sorted((round(e, 1), d) for e, d in edges))
                units[key].append((f, idx, edges))
        return units, blocked

    def _prism_misaligned(self, a, b, window):
        """Vazados (centro de CADA celula, geometria real) de uma fiada que NAO
        continuam na fiada vizinha: caem sobre peca macica (compensador), sobre
        uma junta, ou a mais de PRISM_ALIGNED_DC_MAX_CM do centro de um vazado da
        peca de cima/baixo. Canaleta e vao nao contam (nao sao prisma de bloco)."""
        n = 0
        for src, dst in ((a, b), (b, a)):
            dst_slots = self.fam[dst]
            for p in _in_window(self.fam[src], window[0], window[1]):
                for c in _cell_centers(p):
                    if c < window[0] or c > window[1]:
                        continue
                    h = _covering(dst_slots, c)
                    if h is None:
                        i = _first_hi_at_least(dst_slots, c)
                        if 0 < i < len(dst_slots) and dst_slots[i].lo - dst_slots[i - 1].hi <= RUN_MAX_GAP_CM:
                            n += 1  # vazado sobre a junta
                        continue
                    if _is_channel_code(h.code):
                        continue
                    cells = _cell_centers(h)
                    if not cells or min(abs(c - q) for q in cells) > PRISM_ALIGNED_DC_MAX_CM:
                        n += 1
        return n

    def _coincident_nonexempt(self, a, b, window):
        """Faces da familia `a` na janela que coincidem com uma face da `b` - menos
        a junta da faixa de jamba. Mesma leitura da auditoria de producao (secao
        11.8): a junta da peca de fechamento encostada no vao e' isenta na PROPRIA
        fiada, e isso ja' interrompe a sequencia vertical - vale quando a face e'
        da faixa em pelo menos uma das duas fiadas (ex.: a junta entre as canaletas
        da verga logo acima da faixa). So' a junta da faixa: nenhuma outra."""
        faces_a = _internal_faces(self.fam[a], self.length, self.edges, window)
        faces_b = _internal_faces(self.fam[b], self.length, self.edges,
                                  (window[0] - FACE_TOLERANCE_CM, window[1] + FACE_TOLERANCE_CM))
        strip_a, strip_b = self._jamb_strip_faces(a), self._jamb_strip_faces(b)
        out = []
        for face in faces_a:
            if not _has_value_near(faces_b, face, FACE_TOLERANCE_CM):
                continue
            if _has_value_near(strip_a, face, FACE_TOLERANCE_CM) or \
                    _has_value_near(strip_b, face, FACE_TOLERANCE_CM):
                continue
            out.append(face)
        return out

    def _stacks_nonexempt(self, window):
        """Juntas NAO isentas que se repetem em 3+ fiadas seguidas, na janela."""
        cache = {}
        faces = {}
        for c in sorted(self.course_fam):
            f = self.course_fam[c]
            if f not in cache:
                strip = self._jamb_strip_faces(f)
                cache[f] = [x for x in _internal_faces(self.fam[f], self.length, self.edges, window)
                            if not _has_value_near(strip, x, FACE_TOLERANCE_CM)]
            faces[c] = cache[f]
        empty = []
        n = 0
        for c in sorted(faces):
            for face in faces[c]:
                if _has_value_near(faces.get(c - 1, empty), face, FACE_TOLERANCE_CM):
                    continue
                length, cc = 1, c
                while _has_value_near(faces.get(cc + 1, empty), face, FACE_TOLERANCE_CM):
                    length += 1
                    cc += 1
                if length >= 3:
                    n += 1
        return n

    @staticmethod
    def _unmatched(intervals_a, intervals_b):
        """Compensadores de `a` sem compensador de `b` na mesma faixa vertical
        (sobreposicao >= metade do menor): quebras da coluna entre as fiadas."""
        n = 0
        for lo, hi in intervals_a:
            if not any(min(hi, hi2) - max(lo, lo2) >= 0.5 * min(hi - lo, hi2 - lo2)
                       for lo2, hi2 in intervals_b):
                n += 1
        return n

    def _jamb_measure(self, fams, idx_of, edges, pairs, window, base_codes):
        dist = 0.0
        comp_iv = {}
        moved = 0
        for f in fams:
            ivs = []
            for n_pos, i in enumerate(idx_of[f]):
                s = self.fam[f][i]
                if s.code != base_codes[f][n_pos]:
                    moved += self.count[f]
                if not s.compensator:
                    continue
                best = self._strip_distance(f, i, edges)
                if best is not None and best > JAMB_TOUCH_TOLERANCE_CM:
                    dist += min(best, JAMB_REACH_CM) * self.count[f]
                ivs.append((s.lo, s.hi))
            comp_iv[f] = ivs
        breaks = 0
        for a, b, k in pairs:
            if a != b and a in comp_iv and b in comp_iv:
                breaks += k * (self._unmatched(comp_iv[a], comp_iv[b]) + self._unmatched(comp_iv[b], comp_iv[a]))
        cp = ht = ex = 0
        wide = (window[0] - WINDOW_PAD_CM, window[1] + WINDOW_PAD_CM)
        for f in fams:
            near = _in_window(self.fam[f], wide[0], wide[1])
            cp += _compensator_guard(near, self.length) * self.count[f]
            ht += self._half_near_ties(near, f)
            ex += _long_compensator_extremes(self.fam[f], self.length) * self.count[f]
        sv = prism = 0
        joints = set()
        for a, b, k in pairs:
            sv += k * _violations_between(self.fam[a], self.fam[b], self.tol, window)
            prism += k * self._prism_misaligned(a, b, window)
            if a != b:
                for face in self._coincident_nonexempt(a, b, window):
                    joints.add((round(face, 1), min(a, b), max(a, b)))
        return {"dist": round(dist, 3), "breaks": breaks, "cp": cp, "ht": ht, "ex": ex, "sv": sv,
                "prism": prism, "joints": joints, "stacks": self._stacks_nonexempt(window), "moved": moved}

    @staticmethod
    def _jamb_failures(m, base):
        fails = []
        if m["prism"] > base["prism"]:
            fails.append("PRISM_39_19_WOULD_BREAK")
        if m["sv"] > base["sv"]:
            fails.append("B34_SMALL_VOID_WOULD_BREAK")
        if m["cp"] > base["cp"]:
            fails.append("ADJACENT_COMPENSATORS")
        if m["ht"] > base["ht"]:
            fails.append("HALF_BLOCK_NEAR_TIE")
        if m["ex"] > base["ex"]:
            fails.append("LONG_COMPENSATOR_AT_WALL_END")
        if not m["joints"] <= base["joints"]:
            fails.append("NEW_COINCIDENT_JOINT")
        if m["stacks"] > base["stacks"]:
            fails.append("STACKED_JOINT")
        return fails

    def _solve_jamb_unit(self, key, members):
        """Resolve UMA lateral (ou pilarete) com TODAS as familias de fiada dela
        juntas. Devolve True se mudou alguma peca."""
        fams = [f for f, _idx, _edges in members]
        idx_of = dict((f, idx) for f, idx, _edges in members)
        edges = sorted(set((e, d) for _f, _idx, es in members for e, d in es))
        lo = min(self.fam[f][idx_of[f][0]].lo for f in fams)
        hi = max(self.fam[f][idx_of[f][-1]].hi for f in fams)
        window = (lo - 1.0, hi + 1.0)
        pairs = sorted((a, b, k) for (a, b), k in self.weights.items() if a in idx_of or b in idx_of)
        orig = dict((f, self._snap(f, idx_of[f])) for f in fams)
        base_codes = dict((f, [s.code for s in orig[f]]) for f in fams)
        options = {}
        for f in fams:
            current = tuple((s.code, s.side if s.orientable else 0) for s in orig[f])
            orders = _multiset_orders(collections.Counter(current), len(current), JAMB_MAX_ORDERS_PER_FAMILY)
            if current in orders:
                orders.remove(current)
            options[f] = [current] + orders

        def apply(assign):
            for f in fams:
                order = assign[f]
                self._apply(f, idx_of[f], [c for c, _side in order], [side or 1 for _c, side in order])

        def restore():
            for f in fams:
                self._restore(f, idx_of[f], orig[f])

        memo = {}

        def measure(assign):
            sig = tuple(assign[f] for f in fams)
            if sig not in memo:
                apply(assign)
                memo[sig] = self._jamb_measure(fams, idx_of, edges, pairs, window, base_codes)
                restore()
            return memo[sig]

        def objective(m, assign):
            return (m["dist"], m["breaks"], m["prism"], m["sv"], m["moved"],
                    tuple(options[f].index(assign[f]) for f in fams))

        start = dict((f, options[f][0]) for f in fams)
        base = measure(start)
        total = 1
        for f in fams:
            total *= len(options[f])
        best = (objective(base, start), start)
        best_any = best
        if total <= JAMB_JOINT_MAX_COMBINATIONS:
            assigns = [{}]
            for f in fams:
                assigns = [_merged(a, f, o) for a in assigns for o in options[f]]
            candidates = assigns
        else:
            candidates = None
        if candidates is not None:
            for assign in candidates:
                m = measure(assign)
                obj = objective(m, assign)
                if obj < best_any[0]:
                    best_any = (obj, assign)
                if not self._jamb_failures(m, base) and obj < best[0]:
                    best = (obj, assign)
        else:
            current = dict(start)
            for _round in range(JAMB_DESCENT_ROUNDS):
                improved = False
                for f in fams:
                    for o in options[f]:
                        trial = dict(current)
                        trial[f] = o
                        m = measure(trial)
                        obj = objective(m, trial)
                        if obj < best_any[0]:
                            best_any = (obj, trial)
                        if not self._jamb_failures(m, base) and obj < best[0]:
                            best = (obj, trial)
                            current = trial
                            improved = True
                if not improved:
                    break
        chosen_obj, chosen = best
        changed = chosen_obj[:2] < objective(base, start)[:2]
        # tudo o que usa `measure` (aplica, mede e RESTAURA) vem antes de aplicar
        final = measure(chosen)
        reasons = ["NO_PERMUTATION_REACHES_JAMB"]
        detail = {}
        if final["dist"] > 0.0 and best_any[0][0] < chosen_obj[0]:
            blocked_by = measure(best_any[1])
            reasons = self._jamb_failures(blocked_by, base) or reasons
            new_joints = sorted(set(j[0] for j in blocked_by["joints"] - base["joints"]))
            if new_joints:
                detail["new_joint_faces_cm"] = new_joints
            if blocked_by["prism"] > base["prism"]:
                detail["prism_misaligned_delta"] = blocked_by["prism"] - base["prism"]
        if changed:
            apply(chosen)
        if final["dist"] > 0.0:
            # a faixa nao fechou: registra para revisao com o motivo real
            for f in fams:
                far = [self._strip_distance(f, i, edges) for i in idx_of[f] if self.fam[f][i].compensator]
                far = [x for x in far if x is not None and x > JAMB_TOUCH_TOLERANCE_CM]
                if far:
                    self.jamb_conflicts.append({
                        "wall_idx": self.wall_idx, "edges_cm": [round(e, 1) for e, _d in edges],
                        "side": edges[0][1] if len(edges) == 1 else 0, "courses": self._courses_of(f),
                        "distance_cm": round(min(far), 1), "codes": [self.fam[f][i].code for i in idx_of[f]],
                        "reasons": reasons, "detail": dict(detail)})
        return bool(changed)

    def align_jamb_compensators(self):
        """SECAO 84: faixa de compensacao na jamba, lateral por lateral, com as
        fiadas em conjunto. Devolve quantas laterais mudaram; os casos que nao
        fecham ficam em `self.jamb_conflicts` com o motivo."""
        self.jamb_conflicts = []
        if not self.jamb_alignment:
            return 0
        units, blocked = self._jamb_units()
        self.jamb_conflicts.extend(blocked)
        changed = 0
        for key in sorted(units):
            if self._solve_jamb_unit(key, units[key]):
                changed += 1
        return changed


def _merged(assign, family, order):
    out = dict(assign)
    out[family] = order
    return out


def jamb_strip_census(course_candidates, walls_to_create, openings_per_wall, catalog=None):
    """SECAO 84 - regua INDEPENDENTE do passe (validacao/relatorio): para cada
    lateral de abertura, a distancia do compensador mais perto da jamba em cada
    fiada em que a abertura corta a fileira. `alternating` = a lateral tem
    compensador em alguma fiada e ele nao fica na mesma posicao em todas;
    `touching_all` = em toda fiada com compensador ele encosta no vao."""
    out = {"sides": 0, "sides_with_compensator": 0, "alternating": 0, "touching_all": 0, "details": []}
    rows_by_wall = _collect_rows(course_candidates, walls_to_create)
    ops = openings_per_wall or []
    for wi in sorted(rows_by_wall):
        openings = []
        for op in (ops[wi] if wi < len(ops) else None) or ():
            lo_cm, hi_cm = float(op[0]) * CM_PER_FT, float(op[1]) * CM_PER_FT
            openings.append((min(lo_cm, hi_cm), max(lo_cm, hi_cm)))
        if not openings:
            continue
        rows = rows_by_wall[wi]
        for lo_cm, hi_cm in sorted(openings):
            for edge, d in ((lo_cm, -1), (hi_cm, 1)):
                per_course = {}
                for c in sorted(rows):
                    entries = rows[c]
                    probe = edge + JAMB_INSIDE_PROBE_CM if d < 0 else edge - JAMB_INSIDE_PROBE_CM
                    if any(elo - 1e-6 <= probe <= ehi + 1e-6 for _cand, elo, ehi, _cc in entries):
                        continue  # a abertura nao corta esta fiada
                    best = None
                    for cand, elo, ehi, _cc in entries:
                        entry = (catalog or {}).get(cand.get("logical_code")) or {}
                        if not entry.get("is_compensator") or cand.get("wall_idx") != wi:
                            continue
                        dist = (elo - edge) if d > 0 else (edge - ehi)
                        if -JAMB_TOUCH_TOLERANCE_CM <= dist < JAMB_REACH_CM and (best is None or dist < best):
                            best = dist
                    per_course[c] = None if best is None else max(0.0, round(best, 1))
                if not per_course:
                    continue
                out["sides"] += 1
                with_comp = [v for v in per_course.values() if v is not None]
                if not with_comp:
                    continue
                out["sides_with_compensator"] += 1
                touching = [v <= JAMB_TOUCH_TOLERANCE_CM for v in with_comp]
                positions = set(0.0 if v <= JAMB_TOUCH_TOLERANCE_CM else v for v in with_comp)
                alternating = len(positions) > 1
                if alternating:
                    out["alternating"] += 1
                if all(touching):
                    out["touching_all"] += 1
                out["details"].append({"wall_idx": wi, "edge_cm": round(edge, 1), "side": d,
                                       "distance_by_course": dict((str(c), v) for c, v in sorted(per_course.items())),
                                       "alternating": alternating, "touching_all": all(touching)})
    return out


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


def _runs_by_start(slots):
    return dict((round(slots[r[0]].lo, 3), r) for r in _runs(slots))


def _write_back(wall, base_fam, course_candidates, catalog):
    """Leva o estado final do modelo para os candidatos reais, trecho a trecho
    (identificado pela ponta inicial, que nunca muda): reaproveita o objeto
    quando o codigo coincide (so' move/gira), cria peca nova com o construtor do
    solver quando falta e remove a que sobra."""
    from core.engine.wall_stepper import _place_pier_layout
    moved = rotated = created = removed = 0
    done = set()
    for f in sorted(wall.fam):
        old, new = base_fam[f], wall.fam[f]
        old_runs, new_runs = _runs_by_start(old), _runs_by_start(new)
        for start in sorted(old_runs):
            orun, nrun = old_runs[start], new_runs.get(start)
            if nrun is None:
                continue
            if [(old[i].code, round(old[i].lo, 3), old[i].side) for i in orun] == \
                    [(new[i].code, round(new[i].lo, 3), new[i].side) for i in nrun]:
                continue
            for c in sorted(wall.course_fam):
                if wall.course_fam[c] != f:
                    continue
                originals = [wall.rows[c][i][0] for i in orun]
                model = originals[0]
                pools = collections.defaultdict(list)
                for cand in originals:
                    pools[cand.get("logical_code")].append(cand)
                for i in nrun:
                    slot = new[i]
                    if pools[slot.code]:
                        cand = pools[slot.code].pop(0)
                        if id(cand) not in done:
                            done.add(id(cand))
                            lo, _hi = _extent_cm(cand, wall.p0, wall.dir)
                            if abs(slot.lo - lo) > 1e-6:
                                _translate(cand, slot.lo - lo, wall.dir)
                                moved += 1
                    else:
                        cand = _place_pier_layout([(slot.code, slot.lo, slot.hi)], catalog, wall.p0, wall.dir,
                                                  model.get("course"), wall.wall_idx)[0]
                        for key in ("course_variant",):
                            if key in model:
                                cand[key] = model[key]
                        course_candidates[c].append(cand)
                        done.add(id(cand))
                        created += 1
                    if slot.orientable and id(cand) in done:
                        lo, hi = _extent_cm(cand, wall.p0, wall.dir)
                        off, _half = _void_geometry(cand, wall.p0, wall.dir, lo, hi)
                        if (1 if (off or 0.0) >= 0.0 else -1) != slot.side:
                            _sva.rotate_candidate_180(cand)
                            rotated += 1
                for leftovers in pools.values():
                    for cand in leftovers:
                        done.add(id(cand))
                        lst = course_candidates[c]
                        for k in range(len(lst)):
                            if lst[k] is cand:
                                del lst[k]
                                removed += 1
                                break
    rotated += _sync_orientation(wall, base_fam, done)
    return moved, rotated, created, removed


def _sync_orientation(wall, base_fam, done):
    """Gira os candidatos cujo slot manteve codigo e posicao mas mudou de lado
    (orientacao exata, secao 62) - inclusive B34 isolado, que nao forma corrida.
    Casamento por (codigo, posicao): as listas podem ter mudado de tamanho."""
    rotated = 0
    for f in sorted(wall.fam):
        old_index = dict(((s.code, round(s.lo, 3)), i) for i, s in enumerate(base_fam[f]))
        for slot in wall.fam[f]:
            if not slot.orientable:
                continue
            i = old_index.get((slot.code, round(slot.lo, 3)))
            if i is None or base_fam[f][i].side == slot.side:
                continue
            for c in sorted(wall.course_fam):
                if wall.course_fam[c] != f or i >= len(wall.rows[c]):
                    continue
                cand = wall.rows[c][i][0]
                if id(cand) in done:
                    continue
                done.add(id(cand))
                lo, hi = _extent_cm(cand, wall.p0, wall.dir)
                off, _half = _void_geometry(cand, wall.p0, wall.dir, lo, hi)
                if (1 if (off or 0.0) >= 0.0 else -1) != slot.side:
                    _sva.rotate_candidate_180(cand)
                    rotated += 1
    return rotated


def _snapshot_wall(course_candidates, wall_idx):
    lists = []
    geometry = {}
    for c in sorted(course_candidates or {}):
        lst = course_candidates[c]
        if any(cand.get("wall_idx") == wall_idx for cand in lst):
            lists.append((c, list(lst)))
            for cand in lst:
                if cand.get("wall_idx") == wall_idx and id(cand) not in geometry:
                    geometry[id(cand)] = (cand, cand["origin_world"], list(cand.get("cells_world") or []),
                                          cand.get("x_dir"), cand.get("y_dir"), cand.get("rotation_deg"))
    return lists, geometry


def _restore_wall(course_candidates, snapshot):
    lists, geometry = snapshot
    for c, saved in lists:
        course_candidates[c][:] = saved
    for cand, origin, cells, x_dir, y_dir, rotation in geometry.values():
        cand["origin_world"], cand["cells_world"] = origin, cells
        cand["x_dir"], cand["y_dir"], cand["rotation_deg"] = x_dir, y_dir, rotation


def _validation_worse(after, before):
    """Qualquer tipo de problema da auditoria que aumenta, apoio pior, qualquer
    problema CHANNEL que aumenta ou canaleta casada que some."""
    if after is None or before is None:
        return False
    for kind, count in (after.get("audit") or {}).items():
        if count > (before.get("audit") or {}).get(kind, 0):
            return True
    if (after.get("unsupported") or 0) > (before.get("unsupported") or 0):
        return True
    channel_after, channel_before = after.get("channel"), before.get("channel")
    if channel_after is not None and channel_before is not None:
        for kind, count in sorted(channel_after.items()):
            if kind == "matched":
                if any(a < b for a, b in zip(count, channel_before.get("matched") or (0, 0))):
                    return True
            elif count > channel_before.get(kind, 0):
                return True
    return False


def _fill_codes(course_candidates, catalog):
    """Codigos que o solver ja' usa como preenchimento comum (bloco vazado ou
    compensador) em alguma parede - a composicao nunca inventa familia nova.
    Com B34_RUN_OPENING_REPAIR_MOVABLE, as pecas do reparo de abertura contam
    (sao as mesmas pecas moveis das corridas)."""
    reasons = _MOVABLE_REASONS if B34_RUN_OPENING_REPAIR_MOVABLE else ("STANDARD_FILL",)
    codes = set()
    for c in course_candidates or {}:
        for cand in course_candidates[c] or ():
            code = cand.get("logical_code")
            cat = (catalog or {}).get(code) or {}
            if cand.get("placement_reason") not in reasons or cand.get("node_index") is not None:
                continue
            if cat.get("is_channel") or _is_channel_code(code):
                continue
            if _sva._is_hollow_masonry(cand, catalog) or cat.get("is_compensator"):
                codes.add(code)
    return sorted(codes)


def arrange_b34_runs(course_candidates, walls_to_create, openings_per_wall, catalog=None,
                     tolerance_cm=_sva.SMALL_VOID_ALIGN_TOLERANCE_CM, tie_positions_by_wall=None,
                     half_block_code=None, half_block_tie_gap_cm=0.0, validate_wall=None,
                     only_walls=None, joint_identity_guard=False, jamb_compensator_alignment=False):
    """Aplica o arranjo conjunto. Devolve o resumo por parede alterada e os
    totais das guardas antes/depois (as guardas nunca pioram por construcao).
    `joint_identity_guard` (secao 81.1): nenhuma troca cria junta coincidente
    entre fiadas vizinhas numa posicao nova. `jamb_compensator_alignment`
    (secao 84): faixa de compensacao encostada e alinhada na jamba."""
    summary = {"walls_changed": 0, "runs_changed": 0, "moved": 0, "rotated": 0,
               "before": {"violations": 0, "coincident_faces": 0, "compensator_guard": 0,
                          "long_compensator_extremes": 0, "half_block_near_tie": 0, "stacked_joints": 0},
               "after": {"violations": 0, "coincident_faces": 0, "compensator_guard": 0,
                         "long_compensator_extremes": 0, "half_block_near_tie": 0, "stacked_joints": 0},
               "walls": []}
    jamb_on = bool(jamb_compensator_alignment) and JAMB_COMPENSATOR_ALIGNMENT_ENABLED
    if jamb_on:
        summary["before"]["jamb_compensator_distance"] = 0
        summary["after"]["jamb_compensator_distance"] = 0
        summary.update({"jamb_sides_changed": 0, "jamb_conflicts_by_wall": {}})
    if not B34_RUN_ARRANGEMENT_ENABLED or not course_candidates or XYZ is None:
        return summary
    rows_by_wall = _collect_rows(course_candidates, walls_to_create)
    fill_codes = _fill_codes(course_candidates, catalog)
    summary.update({"compositions": 0, "created": 0, "removed": 0, "walls_rejected_by_validation": []})
    support_total = None
    for wi in sorted(rows_by_wall):
        if only_walls is not None and wi not in only_walls:
            # passe seguinte (secao 65): so' as paredes que o passe anterior mexeu
            continue
        wall = _Wall(wi, rows_by_wall[wi], walls_to_create, openings_per_wall, catalog, tolerance_cm,
                     ties=(tie_positions_by_wall or {}).get(wi), half_code=half_block_code,
                     half_tie_gap_cm=half_block_tie_gap_cm, fill_codes=fill_codes,
                     joint_identity_guard=joint_identity_guard, jamb_alignment=jamb_on)
        before = wall.totals()
        base_fam = dict((f, [s.copy() for s in slots]) for f, slots in wall.fam.items())
        aligned = 0
        if jamb_on:
            # SECAO 84 = passe FINAL so' de permutacao, por cima do arranjo ja'
            # convergido (ordem 60, composicao 61, orientacao 62): a contagem de
            # pecas e' a da busca, toda composicao que TIRA compensador ja'
            # aconteceu (regra 5 do pedido) e nada depois desfaz a faixa
            changed, compositions, oriented = set(), 0, 0
            aligned = wall.align_jamb_compensators()
        else:
            changed = wall.optimize() if before["violations"] else set()
            compositions = wall.compose()
            oriented = wall.orient_exact() if wall.totals()["violations"] else 0
        if oriented:
            summary["orientation_dp_changes"] = summary.get("orientation_dp_changes", 0) + oriented
        if jamb_on:
            summary["jamb_conflicts_by_wall"][wi] = list(wall.jamb_conflicts)
        if not changed and not compositions and not oriented and not aligned:
            for key in summary["before"]:
                summary["before"][key] += before[key]
                summary["after"][key] += before[key]
            continue
        after = wall.totals()
        snapshot = _snapshot_wall(course_candidates, wi)
        checked_before = None
        if validate_wall is not None:
            # o apoio fisico e' global: o "antes" desta parede e' o "depois" da
            # anterior (so' recalcula a auditoria, que e' por parede)
            checked_before = validate_wall(wi, support=support_total is None)
            if support_total is not None:
                checked_before["unsupported"], checked_before["channel"] = support_total
        moved, rotated, created, removed = _write_back(wall, base_fam, course_candidates, catalog)
        checked_after = validate_wall(wi) if validate_wall is not None else None
        if checked_after is not None:
            if checked_after.get("channel") is None and checked_before is not None:
                # parede sem abertura: a validacao CHANNEL nao muda
                checked_after["channel"] = checked_before.get("channel")
            support_total = (checked_after["unsupported"], checked_after.get("channel"))
        if _validation_worse(checked_after, checked_before):
            # a busca e' um modelo; quem decide e' o validador de producao
            _restore_wall(course_candidates, snapshot)
            support_total = (checked_before["unsupported"], checked_before.get("channel"))
            summary["walls_rejected_by_validation"].append(
                {"wall_idx": wi, "before": checked_before, "after": checked_after})
            after = before
            moved = rotated = created = removed = 0
            compositions = oriented = 0
            changed = set()
            if jamb_on and aligned:
                # a faixa desta parede nao passou no validador de producao
                summary["jamb_conflicts_by_wall"][wi] = [{
                    "wall_idx": wi, "edges_cm": [], "side": 0, "courses": [], "distance_cm": None,
                    "codes": [], "reasons": ["PRODUCTION_VALIDATION_REJECTED"]}]
            aligned = 0
        for key in summary["before"]:
            summary["before"][key] += before[key]
            summary["after"][key] += after[key]
        if not changed and not compositions and not oriented and not aligned:
            continue
        if jamb_on:
            summary["jamb_sides_changed"] += aligned
        summary["walls_changed"] += 1
        summary["runs_changed"] += len(changed)
        summary["compositions"] += compositions
        summary["moved"] += moved
        summary["rotated"] += rotated
        summary["created"] += created
        summary["removed"] += removed
        summary["walls"].append({"wall_idx": wi, "before": before, "after": after})
    return summary
