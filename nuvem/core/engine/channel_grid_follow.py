# -*- coding: utf-8 -*-
"""SECAO 86.12 (correcao do usuario 2026-10-05) - A CANALETA SEGUE A GRADE DA
FIADA DE MESMA PARIDADE ABAIXO.

Correcao do usuario (prints do Revit do `butanta testes`): "algumas canaletas de
34 e 39 nao estao alinhadas com a modulacao abaixo dela, assim quebrando o
prisma dos blocos". Medido no resultado da secao 86: de 621 canaletas sobre
alvenaria da fiada c-2, 184 nao coincidiam peca a peca com as pecas da fiada
c-2 (vergas f11, cintas f12 e contraverga da W0 f4). A verga/cinta era a fiada
que o motor resolveu como continua (sem a abertura) trocada peca a peca por
canaleta - a grade do pilarete (85.9/85.10) nao subia.

REGRA (REGRA OBRIGATORIA, mesma linha da 85.10 - "a grade inteira do pilarete
continua nas fiadas acima da verga e na propria verga ate' o topo; a fase que
nao fecha e' absorvida SOBRE O VAO, nunca no pilarete"):

- em toda fiada c com canaleta (contraverga, verga, cinta 86.7), na extensao de
  cada corrida, onde a fiada r = c-2 tem alvenaria as canaletas repetem PECA A
  PECA as pecas de r: B39->U39, B34->U34, B19->U19, B54 de preenchimento ->
  U34+U19 (como a 86.7), compensador fundido a' vizinha (51.3; compensador
  encostado no trecho livre e' absorvido por ele). Canaleta de r conta como o
  bloco equivalente;
- onde r nao tem alvenaria (vao abaixo) a grade e' livre: o trecho entre as
  partes alinhadas fecha com U39/U34/U19 e no maximo UM U_CUT, preferindo juntas
  desencontradas das fiadas c-1 e c+1 (regra #1), poucas pecas e nenhuma peca
  minuscula - o descasamento de fase fica ali;
- no quadrado do no' continua o bloco de amarracao (variante A / regra 75):
  canaleta nunca amarra, nenhum no' e' tocado. A corrida so' CRESCE (peca
  inteira) - o apoio da verga nunca diminui;
- os BLOCOS da propria fiada c na mesma faixa (entre a corrida e o no'/vao) tambem
  seguem r quando a grade de r e' limpa ate' la' (85.10); senao ficam como estao
  e a canaleta fecha a diferenca dentro da propria corrida.

Passe final unico (wall_modeling._apply_channel_grid_follow), nos dois caminhos
(strategy None e CHANNEL), depois da verga/contraverga, da cinta e do arranjo e
antes da reauditoria de amarracao. Nao muta `course_candidates`. Deterministico
(ordem por fiada, parede e eixo; o trecho livre e' escolhido no sentido canonico
do mundo, independente do sentido do eixo da parede). Compativel com IronPython
2.7 (sem f-string, sem nonlocal).
"""
import math

from core.engine.wall_stepper import _make_block_candidate, _wall_axis_and_length  # noqa: F401
from core.engine import opening_reinforcement as _orf

SECTION = "86.12"
TARGET_ROLES = (_orf.ROLE_ABOVE_OPENING, _orf.ROLE_BELOW_SILL, _orf.ROLE_TOP_BOND_BEAM)
OPENING_ROLES = (_orf.ROLE_ABOVE_OPENING, _orf.ROLE_BELOW_SILL)
BLOCK_OF_CHANNEL = {_orf.CHANNEL_U_39: "B39", _orf.CHANNEL_U_34: "B34", _orf.CHANNEL_U_19: "B19"}
FOLLOW_CODES = ("B39", "B34", "B19", "C04", "C09", "B54")
COMPENSATORS = ("C04", "C09")
FREE_STEPS = ((39.0, "B39"), (34.0, "B34"), (19.0, "B19"))
FREE_CUT = "FREE_CUT"
FREE_SHORT = "FREE_SHORT"
MERGEABLE = ("C04", "C09", FREE_SHORT)

DEFAULT_CHANNEL_GRID_FOLLOW_POLICY = {
    "policy_version": "CHANNEL-GRID-FOLLOW-2026-10-05-S86.12",
    "joint_cm": 1.0,
    # inicio/fim de peca de c x de r tidos como a mesma junta (faces no modulo de 5 cm)
    "sync_tolerance_cm": 0.6,
    # borda dura (jamba de vao ativo na fiada, ponta de parede): a peca nova nao passa dela
    "hard_edge_tolerance_cm": 0.05,
    # junta minima/maxima entre pecas contiguas (contiguous_gap_cm do CHANNEL)
    "min_joint_cm": 0.3,
    "max_joint_cm": 2.0,
    # folga entre duas pecas de r que ainda e' junta (larga) e nao trecho livre
    "wide_joint_cm": 2.5,
    # residuo do trecho livre absorvido pelas juntas (cada uma fica em [min, max])
    "fit_tolerance_cm": 0.6,
    # junta nova a menos disto de uma junta da fiada c-1/c+1 conta como coincidente
    # (BOND_JOINT_CLUSTER_TOLERANCE_CM)
    "coincident_joint_cm": 1.5,
    # U_CUT do trecho livre: minimo DURO = menor corte humano observado (51.3);
    # abaixo de small_cut_cm e' "peca minuscula" (penalizada)
    "min_cut_cm": 9.0,
    "small_cut_cm": 19.0,
    "max_cut_cm": 39.0,
    "max_extra_pieces": 3,
    "split_b54_lengths_cm": (34.0, 19.0),
    "node_square_margin_cm": 0.5,
}


def channel_grid_follow_policy(overrides=None):
    policy = dict(DEFAULT_CHANNEL_GRID_FOLLOW_POLICY)
    for key, value in (overrides or {}).items():
        policy[key] = value
    return policy


def _roles(cand):
    return list(((cand or {}).get("reinforcement") or {}).get("roles") or [])


def is_target_channel(cand):
    """Canaleta de verga/contraverga/cinta (as que a 86.12 alinha)."""
    return _orf.is_channel_code((cand or {}).get("logical_code")) and any(r in TARGET_ROLES for r in _roles(cand))


def _near(sorted_values, value, tol):
    for v in sorted_values:
        if v > value + tol:
            break
        if abs(v - value) < tol:
            return True
    return False


def _canonical_axis(walls_to_create, wall_idx):
    """True se o eixo da parede aponta no sentido canonico do mundo (+X; vertical:
    +Y). O trecho livre e' escolhido nesse sentido - o resultado nao depende do
    sentido em que a parede foi desenhada."""
    _p0, _p1, wall_dir, _len, _th = _wall_axis_and_length(walls_to_create, wall_idx)
    if abs(wall_dir.X) > 1e-6:
        return wall_dir.X > 0
    return wall_dir.Y > 0


# --------------------------------------------------------------------------
# trecho livre (sobre o vao): U39/U34/U19 + no maximo um U_CUT
# --------------------------------------------------------------------------
def _fill_free(s, e, flex_l, flex_r, adj_joints, pol, keep=None):
    """Melhor composicao de [s, e] (faces) com pecas de 39/34/19 e no maximo UMA
    cortada. `adj_joints` (ordenadas) = juntas das fiadas c-1 e c+1. `keep` =
    [(lo, hi, code_equivalente)] das pecas originais de c que ja' fecham
    exatamente o trecho (concorrem com o mesmo criterio; empate fica com elas).

    Criterio: juntas novas coincidentes com c-1/c+1, U_CUT, U_CUT minuscula,
    numero de pecas, numero de U19. Devolve {"pieces": [(lo, hi, code)],
    "key", "kept"} ou None se nao fecha."""
    j = pol["joint_cm"]
    tol_c = pol["coincident_joint_cm"]
    length = e - s
    if length < -1e-6:
        return None
    end_pos = e + j

    def coinc(t):
        return 1 if _near(adj_joints, t, tol_c) else 0

    n_cap = int(math.floor((length + j) / (19.0 + j) + 1e-9)) + 1
    n_min = int(math.ceil((length + j) / (39.0 + j) - 1e-9))
    n_cap = max(1, min(n_cap, n_min + int(pol["max_extra_pieces"])))

    def run_dp(start, sign):
        # sign=+1: de s para a direita; sign=-1: de end_pos para a esquerda
        table = {round(start, 2): (start, (0, 0, 0), ())}
        layer = [start]
        for _n in range(n_cap):
            updated = {}
            for p in sorted(layer, key=lambda v: sign * v):
                pos, cost, seq = table[round(p, 2)]
                # `pos` = inicio da peca seguinte (ida) / da peca mais a' esquerda
                # (volta): nos dois sentidos a junta nova fica em pos - j/2
                jc = coinc(pos - j / 2.0) if seq else 0
                for piece_len, _code in FREE_STEPS:
                    q = pos + sign * (piece_len + j)
                    if sign > 0 and q > end_pos + pol["fit_tolerance_cm"] + 1e-6:
                        continue
                    if sign < 0 and q < s - pol["fit_tolerance_cm"] - 1e-6:
                        continue
                    c2 = (cost[0] + jc, cost[1] + 1, cost[2] + (1 if piece_len < 20.0 else 0))
                    kq = round(q, 2)
                    old = table.get(kq)
                    if old is None or c2 < old[1]:
                        table[kq] = (q, c2, seq + (piece_len,))
                        updated[kq] = q
            layer = [updated[k] for k in sorted(updated)]
            if not layer:
                break
        return table

    fwd = run_dp(s, 1)
    bwd = run_dp(end_pos, -1)
    options = []
    # sem corte
    for kq in sorted(fwd):
        p, cost, seq = fwd[kq]
        if not seq:
            continue
        resid = end_pos - p
        if abs(resid) > pol["fit_tolerance_cm"] + 1e-9:
            continue
        n_abs = (len(seq) - 1) + (1 if flex_l else 0) + (1 if flex_r else 0)
        if n_abs == 0:
            if abs(resid) > pol["hard_edge_tolerance_cm"] + 1e-9:
                continue
            shift = 0.0
        else:
            shift = resid / float(n_abs)
            if j + shift < pol["min_joint_cm"] - 1e-9 or j + shift > pol["max_joint_cm"] + 1e-9:
                continue
        pieces = []
        cur = s + (shift if flex_l else 0.0)
        for piece_len in seq:
            pieces.append((cur, cur + piece_len, _free_code(piece_len)))
            cur += piece_len + j + shift
        key = (cost[0], 0, 0, cost[1], cost[2])
        options.append((key, 1, _seq_key(seq), pieces))
    # com um corte
    fkeys = sorted(fwd)
    bkeys = sorted(bwd)
    for ka in fkeys:
        a, ca, sa = fwd[ka]
        for kb in bkeys:
            b, cb, sb_ = bwd[kb]
            cut = b - j - a
            if cut < pol["min_cut_cm"] - 1e-6 or cut > pol["max_cut_cm"] - 0.05:
                continue
            if _orf._standard_code_for_length(cut) is not None:
                continue
            jc = (coinc(a - j / 2.0) if sa else 0) + (coinc(b - j / 2.0) if sb_ else 0)
            tiny = 1 if cut < pol["small_cut_cm"] - 1e-6 else 0
            key = (ca[0] + cb[0] + jc, 1, tiny, ca[1] + cb[1] + 1, ca[2] + cb[2])
            seq = tuple(sa) + (round(cut, 3),) + tuple(reversed(sb_))
            pieces = []
            cur = s
            for piece_len in sa:
                pieces.append((cur, cur + piece_len, _free_code(piece_len)))
                cur += piece_len + j
            pieces.append((a, a + cut, FREE_CUT))
            cur = b
            for piece_len in reversed(sb_):
                pieces.append((cur, cur + piece_len, _free_code(piece_len)))
                cur += piece_len + j
            options.append((key, 1, _seq_key(seq), pieces))
    if keep:
        joints = [(x[1] + y[0]) / 2.0 for x, y in zip(keep, keep[1:])]
        cuts = [x for x in keep if x[2] == FREE_CUT]
        key = (sum(coinc(t) for t in joints), len(cuts),
               1 if any((x[1] - x[0]) < pol["small_cut_cm"] - 1e-6 for x in cuts) else 0,
               len(keep), sum(1 for x in keep if x[2] == "B19"))
        options.append((key, 0, (), list(keep)))
    if not options:
        return None
    options.sort(key=lambda o: (o[0], o[1], o[2]))
    best = options[0]
    return {"pieces": best[3], "key": best[0], "kept": best[1] == 0}


def _free_code(piece_len):
    for nominal, code in FREE_STEPS:
        if abs(piece_len - nominal) <= 0.05:
            return code
    return FREE_CUT


def _seq_key(seq):
    # empate deterministico: pecas maiores primeiro (no sentido canonico)
    return tuple(-float(x) for x in seq)


def _fill_canonical(s, e, flex_l, flex_r, adj_joints, pol, keep, canonical, cache):
    """`_fill_free` no sentido canonico do mundo (espelha o trecho se o eixo da
    parede aponta para o outro lado). Memoizado por trecho."""
    ck = (round(s, 3), round(e, 3), bool(flex_l), bool(flex_r),
          tuple((round(x[0], 3), round(x[1], 3), x[2]) for x in (keep or [])))
    if ck in cache:
        return cache[ck]
    if canonical:
        out = _fill_free(s, e, flex_l, flex_r, adj_joints, pol, keep)
    else:
        mirrored_keep = [(-x[1], -x[0], x[2]) for x in reversed(keep or [])] or None
        out = _fill_free(-e, -s, flex_r, flex_l, sorted(-t for t in adj_joints), pol, mirrored_keep)
        if out is not None:
            out = {"pieces": [(-p[1], -p[0], p[2]) for p in reversed(out["pieces"])], "key": out["key"],
                   "kept": out["kept"]}
    cache[ck] = out
    return out


# --------------------------------------------------------------------------
# fileiras, faixas e ancoras
# --------------------------------------------------------------------------
def _replaceable(row, wall_idx, squares, margin):
    cand = row["cand"]
    if cand.get("wall_idx") != wall_idx or not row["along"] or row["tie"] or cand.get("converted_tie"):
        return False
    code = cand.get("logical_code")
    if not (code in FOLLOW_CODES or is_target_channel(cand)):
        return False
    return _orf._square_hit(row["lo"], row["hi"], squares, margin) is None


def _anchor_of(row, wall_idx, squares, margin):
    cand = row["cand"]
    if cand.get("wall_idx") != wall_idx or not row["along"] or row["tie"] or cand.get("converted_tie"):
        return None
    if _orf._square_hit(row["lo"], row["hi"], squares, margin) is not None:
        return None
    code = cand.get("logical_code")
    if code in FOLLOW_CODES:
        eq = code
    elif code in BLOCK_OF_CHANNEL:
        eq = BLOCK_OF_CHANNEL[code]
    elif code == _orf.CHANNEL_U_CUT:
        eq = _orf.CHANNEL_U_CUT
    else:
        return None
    return {"lo": row["lo"], "hi": row["hi"], "code": eq, "cand": cand}


def _segments(rows, wall_idx, squares, pol):
    """Faixas da fiada c: pecas substituiveis contiguas entre duas paradas (no',
    amarracao, peca de outra parede, vazio, ponta). Cada faixa: (i0, i1, prev_hi,
    next_lo) com prev_hi/next_lo da peca de parada CONTIGUA (None = borda dura)."""
    gap = pol["max_joint_cm"] + _orf.CONTIGUOUS_GAP_EPSILON_CM
    margin = pol["node_square_margin_cm"]
    out = []
    i = 0
    n = len(rows)
    while i < n:
        if not _replaceable(rows[i], wall_idx, squares, margin):
            i += 1
            continue
        i0 = i
        while i + 1 < n and _replaceable(rows[i + 1], wall_idx, squares, margin) and \
                rows[i + 1]["lo"] - rows[i]["hi"] <= gap:
            i += 1
        i1 = i
        prev_hi = rows[i0 - 1]["hi"] if i0 > 0 and 0.0 <= rows[i0]["lo"] - rows[i0 - 1]["hi"] <= gap else None
        next_lo = rows[i1 + 1]["lo"] if i1 + 1 < n and 0.0 <= rows[i1 + 1]["lo"] - rows[i1]["hi"] <= gap else None
        out.append((i0, i1, prev_hi, next_lo))
        i += 1
    return out


def _subzones(seg_rows, pol):
    """[lo, hi, [linhas]] de cada corrida de canaleta-alvo contigua da faixa
    (canaletas separadas por bloco formam zonas distintas)."""
    gap = pol["max_joint_cm"] + _orf.CONTIGUOUS_GAP_EPSILON_CM
    zones = []
    last = None
    for r in seg_rows:
        if not is_target_channel(r["cand"]):
            last = None
            continue
        if zones and last is not None and r["lo"] - zones[-1][1] <= gap:
            zones[-1][1] = r["hi"]
            zones[-1][2].append(r)
        else:
            zones.append([r["lo"], r["hi"], [r]])
        last = r
    return zones


def _overlaps_any(lo, hi, zones, eps=0.05):
    for z in zones:
        if min(hi, z[1]) - max(lo, z[0]) > eps:
            return True
    return False


# --------------------------------------------------------------------------
# layout de uma janela [x, y] da faixa
# --------------------------------------------------------------------------
def _build_items(x, y, x_prev_hi, y_next_lo, anchors, pol):
    """[("A", ancora) | ("F", s, e, flex_l, flex_r)] cobrindo [x, y]: ancoras de r
    inteiras dentro da janela, trechos livres entre elas. None quando a primeira/
    ultima ancora fica a menos de uma peca de uma borda DURA (jamba de vao ativo,
    ponta) sem encostar nela - nao ha' peca que feche essa folga."""
    j = pol["joint_cm"]
    wide = pol["wide_joint_cm"]
    sync = pol["sync_tolerance_cm"]
    lo_lim = (x_prev_hi + pol["min_joint_cm"]) if x_prev_hi is not None else (x - pol["hard_edge_tolerance_cm"])
    hi_lim = (y_next_lo - pol["min_joint_cm"]) if y_next_lo is not None else (y + pol["hard_edge_tolerance_cm"])
    inside = [a for a in anchors if a["lo"] >= lo_lim - 1e-6 and a["hi"] <= hi_lim + 1e-6]
    items = []
    cursor = None
    for a in inside:
        if cursor is None:
            if x_prev_hi is not None:
                ok = a["lo"] <= x_prev_hi + wide + 1e-6
            else:
                ok = a["lo"] <= x + sync + 1e-6
                if not ok and a["lo"] - j - x < sync:
                    return None
            if not ok:
                items.append(["F", x, a["lo"] - j, x_prev_hi is not None, True])
        else:
            gap = a["lo"] - cursor
            if gap > wide + 1e-6:
                items.append(["F", cursor + j, a["lo"] - j, True, True])
        items.append(["A", a])
        cursor = a["hi"]
    if cursor is None:
        items.append(["F", x, y, x_prev_hi is not None, y_next_lo is not None])
    else:
        if y_next_lo is not None:
            ok = cursor >= y_next_lo - wide - 1e-6
        else:
            ok = cursor >= y - sync - 1e-6
            if not ok and y - (cursor + j) < sync:
                return None
        if not ok:
            items.append(["F", cursor + j, y, True, y_next_lo is not None])
    return items


def _absorb_compensators(items, zones, pol, x, y, x_flex, y_flex):
    """Compensador de r encostado num trecho livre que NAO fecha comprimento padrao
    com a vizinha alinhada e' absorvido pelo trecho livre (51.3: fundido a' vizinha;
    a junta da grade do lado da vizinha fica). Na ponta da janela o trecho livre
    passa a comecar/terminar na propria ponta (`x`/`y`)."""
    gap = pol["max_joint_cm"] + _orf.CONTIGUOUS_GAP_EPSILON_CM
    changed = True
    while changed:
        changed = False
        for k, it in enumerate(items):
            if it[0] != "A" or it[1]["code"] not in COMPENSATORS:
                continue
            a = it[1]
            if not _overlaps_any(a["lo"], a["hi"], zones) and not any(
                    items[m][0] == "F" for m in (k - 1, k + 1) if 0 <= m < len(items)):
                continue
            left = items[k - 1] if k > 0 else None
            right = items[k + 1] if k + 1 < len(items) else None
            free_side = None
            if right is not None and right[0] == "F":
                free_side = "R"
            elif left is not None and left[0] == "F":
                free_side = "L"
            if free_side is None:
                continue
            other = left if free_side == "R" else right
            if other is not None and other[0] == "A" and other[1]["code"] in ("B39", "B34", "B19"):
                o = other[1]
                contiguous = (a["lo"] - o["hi"] <= gap) if free_side == "R" else (o["lo"] - a["hi"] <= gap)
                total = (a["hi"] - o["lo"]) if free_side == "R" else (o["hi"] - a["lo"])
                if contiguous and _orf._standard_code_for_length(total) is not None:
                    continue   # C04+B34 = U39: funde com a vizinha alinhada
            if free_side == "R":
                if left is None:
                    right[1] = x
                    right[3] = x_flex
                else:
                    right[1] = a["lo"]
                    right[3] = True   # junta com a peca anterior (flexivel)
                del items[k]
            else:
                if right is None:
                    left[2] = y
                    left[4] = y_flex
                else:
                    left[2] = a["hi"]
                    left[4] = True
                del items[k]
            changed = True
            break
    return items


def _channel_flags(items, zones):
    flags = []
    for it in items:
        if it[0] == "F":
            flags.append(True)
        else:
            flags.append(_overlaps_any(it[1]["lo"], it[1]["hi"], zones))
    return flags


def _islands(items, flags, zones):
    """Grupos de itens-canaleta consecutivos que NAO tocam nenhuma zona original
    (canaleta solta fora da corrida) - layout invalido."""
    k = 0
    n = len(items)
    while k < n:
        if not flags[k]:
            k += 1
            continue
        k0 = k
        while k + 1 < n and flags[k + 1]:
            k += 1
        lo = items[k0][1]["lo"] if items[k0][0] == "A" else items[k0][1]
        hi = items[k][1]["hi"] if items[k][0] == "A" else items[k][2]
        if not _overlaps_any(lo, hi, zones):
            return True
        k += 1
    return False


def _flank_clean_left(x, x_prev_hi, zlo, anchors, pol):
    """A grade de r e' limpa de x ate' a corrida (ancoras contiguas, a primeira
    na junta de c em x)."""
    mj = pol["max_joint_cm"]
    wide = pol["wide_joint_cm"]
    lo_lim = (x_prev_hi + pol["min_joint_cm"]) if x_prev_hi is not None else (x - pol["hard_edge_tolerance_cm"])
    cands = [a for a in anchors if a["lo"] >= lo_lim - 1e-6]
    if not cands:
        return False
    first = cands[0]
    if x_prev_hi is not None:
        if first["lo"] > x_prev_hi + wide + 1e-6:
            return False
    elif first["lo"] > x + pol["sync_tolerance_cm"] + 1e-6:
        return False
    cur = first
    for a in cands[1:]:
        if cur["hi"] >= zlo - mj - 1e-6:
            return True
        if a["lo"] - cur["hi"] > wide + 1e-6:
            return False
        cur = a
    return cur["hi"] >= zlo - mj - 1e-6


def _flank_clean_right(y, y_next_lo, zhi, anchors, pol):
    mirrored = [{"lo": -a["hi"], "hi": -a["lo"]} for a in reversed(anchors)]
    return _flank_clean_left(-y, (-y_next_lo) if y_next_lo is not None else None, -zhi, mirrored, pol)


# --------------------------------------------------------------------------
# pecas finais
# --------------------------------------------------------------------------
def _split_b54(anchor, adj_joints, pol):
    """B54 de preenchimento sob canaleta -> U34+U19 (ou U19+U34) com a junta nova
    o mais longe possivel das juntas de c-1/c+1 (86.7). None sem desencontro."""
    j = pol["joint_cm"]
    best = None
    for l1 in pol["split_b54_lengths_cm"]:
        l2 = (anchor["hi"] - anchor["lo"]) - l1 - j
        if l2 < 18.95 or l2 > 39.05:
            continue
        joint = anchor["lo"] + l1 + j / 2.0
        stagger = min([abs(joint - t) for t in adj_joints] or [1e9])
        if stagger < pol["coincident_joint_cm"]:
            continue
        key = (round(stagger, 3), l1)
        if best is None or key > best[0]:
            best = (key, l1, l2)
    if best is None:
        return None
    _k, l1, l2 = best
    return [(anchor["lo"], anchor["lo"] + l1), (anchor["hi"] - l2, anchor["hi"])]


def _group_members(members, cpol):
    """51.3: compensador (e sobra curta do trecho livre) fundido a' vizinha
    CONTIGUA com comprimento final <= 39; prefere comprimento padrao, depois a
    esquerda. Sem fusao possivel vira canaleta cortada sozinha."""
    max_len = cpol["max_channel_length_cm"]
    gap = cpol["contiguous_gap_cm"] + _orf.CONTIGUOUS_GAP_EPSILON_CM
    groups = []
    k = 0
    n = len(members)
    while k < n:
        row = members[k]
        if row["code"] not in MERGEABLE:
            groups.append([row])
            k += 1
            continue
        options = []
        if groups and row["lo"] - groups[-1][-1]["hi"] <= gap:
            length = row["hi"] - groups[-1][0]["lo"]
            if length <= max_len + 0.05:
                options.append((0 if _orf._standard_code_for_length(length) else 1, 0, "LEFT"))
        if k + 1 < n and members[k + 1]["lo"] - row["hi"] <= gap:
            length = members[k + 1]["hi"] - row["lo"]
            if length <= max_len + 0.05:
                options.append((0 if _orf._standard_code_for_length(length) else 1, 1, "RIGHT"))
        options.sort()
        if not options:
            groups.append([row])
            k += 1
        elif options[0][2] == "LEFT":
            groups[-1].append(row)
            k += 1
        else:
            groups.append([row, members[k + 1]])
            k += 2
    return groups


def _inherit(lo, hi, originals):
    """Reforco herdado da canaleta original de maior sobreposicao (papel de
    abertura primeiro - ocupacao unica 51.10); fora da corrida, da mais proxima."""
    best = None
    for r in originals:
        ov = min(hi, r["hi"]) - max(lo, r["lo"])
        dist = 0.0 if ov > 0 else min(abs(lo - r["hi"]), abs(r["lo"] - hi))
        opening = any(x in OPENING_ROLES for x in _roles(r["cand"]))
        key = (0 if ov > 0.05 else 1, 0 if (opening and ov > 0.05) else 1, -max(ov, 0.0), dist, r["lo"])
        if best is None or key < best[0]:
            best = (key, r)
    return best[1] if best is not None else None


def _template(cand, course_value):
    out = dict(cand)
    out["course"] = course_value
    out.pop("reinforcement", None)
    out.pop("converted_tie", None)
    return out


# --------------------------------------------------------------------------
# uma faixa
# --------------------------------------------------------------------------
def _follow_segment(ctx, seg_rows, prev_hi, next_lo, anchors_all, adj_joints):
    """Janela escolhida da faixa: (avaliacao, None, None) ou (None, motivo, detalhe).

    Pontas candidatas = juntas de c entre a parada e a corrida. Ponta LIMPA = a
    grade de r e' contigua dali ate' a corrida (os blocos de c seguem r - 85.10);
    a mais larga limpa e' a escolhida. Sem ponta limpa (ou layout limpo que nao
    fecha), a melhor janela pelo criterio de `_evaluate`."""
    pol = ctx["pol"]
    zones = _subzones(seg_rows, pol)
    if not zones:
        return None, None, None
    zlo, zhi = zones[0][0], zones[-1][1]
    seg_lo, seg_hi = seg_rows[0]["lo"], seg_rows[-1]["hi"]
    anchors = [a for a in anchors_all if a["hi"] > seg_lo - 3.0 and a["lo"] < seg_hi + 3.0]
    if not any(min(a["hi"], zhi) - max(a["lo"], zlo) > 0.5 for a in anchors):
        return None, "NO_MASONRY_BELOW_RUN", None
    n = len(seg_rows)
    lefts = [(seg_lo, prev_hi, 0)]
    for i in range(1, n):
        if seg_rows[i]["lo"] <= zlo + 1e-6:
            lefts.append((seg_rows[i]["lo"], seg_rows[i - 1]["hi"], i))
    rights = [(seg_hi, next_lo, n - 1)]
    for i in range(n - 2, -1, -1):
        if seg_rows[i]["hi"] >= zhi - 1e-6:
            rights.append((seg_rows[i]["hi"], seg_rows[i + 1]["lo"], i))
    left = next((c for c in lefts if _flank_clean_left(c[0], c[1], zlo, anchors, pol)), None)
    right = next((c for c in rights if _flank_clean_right(c[0], c[1], zhi, anchors, pol)), None)
    chosen = None
    if left is not None and right is not None:
        # as duas pontas limpas: a faixa segue r de ponta a ponta (85.10)
        chosen = _evaluate(ctx, left, right, anchors, zones, seg_rows, adj_joints)
    if chosen is None:
        # alguma ponta sem grade limpa (ou o layout limpo nao fecha): melhor janela
        # entre as juntas de c possiveis, a ponta limpa primeiro
        best = None
        for l_opts, r_opts in (([left] if left is not None else lefts, [right] if right is not None else rights),
                               (lefts, rights)):
            for lc in l_opts:
                for rc in r_opts:
                    if lc is None or rc is None:
                        continue
                    ev = _evaluate(ctx, lc, rc, anchors, zones, seg_rows, adj_joints)
                    if ev is not None and (best is None or ev["score"] < best["score"]):
                        best = ev
            if best is not None:
                break
        if best is None:
            return None, "NO_VALID_LAYOUT", {"zone_cm": [round(zlo, 3), round(zhi, 3)]}
        chosen = best
    flank_note = []
    if left is None or chosen["window"][0] != left[0]:
        flank_note.append("L")
    if right is None or chosen["window"][1] != right[0]:
        flank_note.append("R")
    chosen["flank_mismatch"] = flank_note
    return chosen, None, None


JAMB_CLOSURES = ((4.0, ("C04",)), (9.0, ("C09",)), (14.0, ("C09", "C04")))


def _short_kind(items, flags, k, s, e, fl, fr, pol, catalog):
    """Destino da sobra curta [s, e] (item k): ("MERGE", padrao?) fundida a' canaleta
    alinhada vizinha; ("CLOSURE", codigos, lado) compensador da jamba numa borda
    dura (C09 na face, 84/86.6); None se nenhum serve."""
    length = e - s
    merge_std = merge_any = False
    for m in (k - 1, k + 1):
        if 0 <= m < len(items) and items[m][0] == "A" and flags[m] and items[m][1]["code"] != "B54":
            a = items[m][1]
            total = (e - a["lo"]) if m == k - 1 else (a["hi"] - s)
            if total <= pol["max_cut_cm"] + 0.05:
                merge_any = True
                if _orf._standard_code_for_length(total) is not None:
                    merge_std = True
    if merge_std:
        return ("MERGE", True)
    hard_left = k == 0 and not fl
    hard_right = k == len(items) - 1 and not fr
    if (hard_left or hard_right) and catalog:
        for nominal, codes in JAMB_CLOSURES:
            if abs(length - nominal) <= pol["sync_tolerance_cm"] and all(c in catalog for c in codes):
                ordered = tuple(codes) if hard_left else tuple(reversed(codes))
                return ("CLOSURE", ordered, "L" if hard_left else "R")
    if merge_any:
        return ("MERGE", False)
    return None


def _closure_candidates(ctx, closure, s, e, template, course_value, wall_idx):
    """Compensadores da jamba (bloco) em [s, e], encostados na borda dura."""
    catalog = ctx.get("catalog") or {}
    pol = ctx["pol"]
    p0, _p1, wall_dir, _len_ft, _th = _wall_axis_and_length(ctx["walls"], wall_idx)
    codes, side = closure[1], closure[2]
    lengths = [float(catalog[c]["length_cm"]) for c in codes]
    total = sum(lengths) + pol["joint_cm"] * (len(lengths) - 1)
    start = s if side == "L" else e - total
    rel = template["origin_world"] - p0
    t_tpl = rel.DotProduct(wall_dir)
    out = []
    cur = start
    for code, length in zip(codes, lengths):
        center = cur + length / 2.0
        origin = template["origin_world"] + wall_dir * (_orf._cm_to_ft(center) - t_tpl)
        cand = _make_block_candidate(code, catalog[code], course_value, origin, template.get("x_dir") or wall_dir,
                                     "STANDARD_FILL", wall_idx=wall_idx)
        out.append((cur, cur + length, cand))
        cur += length + pol["joint_cm"]
    return out


def _evaluate(ctx, lc, rc, anchors, zones, seg_rows, adj_joints):
    """Layout completo da janela [lc, rc]: itens, trechos livres preenchidos e
    pontuacao. None se invalido (canaleta solta, trecho que nao fecha)."""
    pol = ctx["pol"]
    x, x_prev_hi, i_first = lc
    y, y_next_lo, i_last = rc
    if i_first > i_last or x >= y:
        return None
    items = _build_items(x, y, x_prev_hi, y_next_lo, anchors, pol)
    if items is None:
        return None
    items = _absorb_compensators(items, zones, pol, x, y, x_prev_hi is not None, y_next_lo is not None)
    flags = _channel_flags(items, zones)
    if _islands(items, flags, zones):
        return None
    window_rows = seg_rows[i_first:i_last + 1]
    total = [0, 0, 0, 0, 0]
    flank_free = 0
    fills = []
    for it, is_channel in zip(items, flags):
        if it[0] == "A":
            if not is_channel and it[1]["code"] == _orf.CHANNEL_U_CUT:
                return None   # U_CUT de r sob bloco: sem bloco equivalente
            fills.append(None)
            continue
        s, e, fl, fr = it[1], it[2], it[3], it[4]
        zone_span = [[zones[0][0], zones[-1][1]]]
        if not _overlaps_any(s, e, zone_span, 0.5):
            flank_free += 1
        if e - s < pol["min_cut_cm"] - 1e-6:
            # sobra curta (menor que a menor canaleta cortada): fundida a' canaleta
            # vizinha (51.3) ou, encostada numa borda dura (jamba de vao ativo),
            # fechada pelo compensador da jamba (84); senao o layout nao serve
            if e - s <= 0.0:
                return None
            k = len(fills)
            short = _short_kind(items, flags, k, s, e, fl, fr, pol, ctx.get("catalog"))
            if short is None:
                return None
            if short[0] == "CLOSURE":
                flags[k] = False
                fills.append({"pieces": [(s, e, "CLOSURE")], "closure": short, "key": (0, 0, 0, 1, 0),
                              "kept": False})
                total[3] += len(short[1])
                continue
            fills.append({"pieces": [(s, e, FREE_SHORT)], "key": (0, 1, 1, 1, 0), "kept": False})
            if not short[1]:
                total[1] += 1
                total[2] += 1
            continue
        keep = []
        for r in window_rows:
            if r["lo"] >= s - pol["sync_tolerance_cm"] and r["hi"] <= e + pol["sync_tolerance_cm"] and \
                    is_target_channel(r["cand"]):
                code = r["cand"].get("logical_code")
                keep.append((r["lo"], r["hi"], BLOCK_OF_CHANNEL.get(code, FREE_CUT)))
        if not keep or abs(keep[0][0] - s) > pol["sync_tolerance_cm"] or \
                abs(keep[-1][1] - e) > pol["sync_tolerance_cm"] or any(
                    b[0] - a[1] > pol["max_joint_cm"] + 1e-6 for a, b in zip(keep, keep[1:])):
            keep = None
        res = _fill_canonical(s, e, fl, fr, adj_joints, pol, keep, ctx["canonical"], ctx["fill_cache"])
        if res is None:
            return None
        fills.append(res)
        for k in range(5):
            total[k] += res["key"][k]
    lo = items[0][1]["lo"] if items[0][0] == "A" else items[0][1]
    hi = items[-1][1]["hi"] if items[-1][0] == "A" else items[-1][2]
    ch_lo = min([(it[1]["lo"] if it[0] == "A" else it[1]) for it, f in zip(items, flags) if f] or [lo])
    ch_hi = max([(it[1]["hi"] if it[0] == "A" else it[2]) for it, f in zip(items, flags) if f] or [hi])
    growth = max(0.0, zones[0][0] - ch_lo) + max(0.0, ch_hi - zones[-1][1])
    width = y - x
    score = (total[0], total[2], total[1], flank_free, round(growth, 3), -round(width, 3), total[3], total[4])
    return {"items": items, "flags": flags, "fills": fills, "score": score, "window": (x, y),
            "window_idx": (i_first, i_last), "x_prev_hi": x_prev_hi, "y_next_lo": y_next_lo}


def _materialize(ctx, chosen, seg_rows, zones, adj_joints, wall_idx, course_index, source_course):
    """Pecas finais (candidatos) da janela escolhida. Devolve (pecas, info) ou
    (None, motivo)."""
    pol = ctx["pol"]
    cpol = ctx["cpol"]
    walls = ctx["walls"]
    i_first, i_last = chosen["window_idx"]
    window_rows = seg_rows[i_first:i_last + 1]
    course_value = window_rows[0]["cand"].get("course")
    originals = [r for r in seg_rows if is_target_channel(r["cand"])]
    opening_zone = any(any(x in OPENING_ROLES for x in _roles(r["cand"])) for r in originals)
    template_c = originals[0]["cand"] if originals else window_rows[0]["cand"]
    by_extent = {}
    for r in window_rows:
        by_extent[(r["cand"].get("logical_code"), round(r["lo"], 1), round(r["hi"], 1))] = r["cand"]
    # sequencia de membros (lo, hi, code, cand_template, kind, channel)
    members = []
    findings = []
    for it, is_channel, fill in zip(chosen["items"], chosen["flags"], chosen["fills"]):
        if it[0] == "A":
            a = it[1]
            if is_channel and a["code"] == "B54":
                parts = _split_b54(a, adj_joints, pol)
                if parts is None:
                    if opening_zone:
                        return None, "B54_SPLIT_NO_STAGGER"
                    findings.append({"code": "GRID_FOLLOW_B54_SPLIT_NO_STAGGER", "lo_cm": round(a["lo"], 3),
                                     "hi_cm": round(a["hi"], 3)})
                    members.append({"lo": a["lo"], "hi": a["hi"], "code": "B54", "cand": a["cand"],
                                    "kind": "FOLLOW", "channel": False})
                    continue
                for lo, hi in parts:
                    members.append({"lo": lo, "hi": hi, "code": "TIE_SPLIT", "cand": a["cand"],
                                    "kind": "FOLLOW", "channel": True, "split": True})
                continue
            members.append({"lo": a["lo"], "hi": a["hi"], "code": a["code"], "cand": a["cand"],
                            "kind": "FOLLOW", "channel": is_channel})
        else:
            if fill.get("closure"):
                members.append({"lo": it[1], "hi": it[2], "code": "CLOSURE", "cand": None, "kind": "CLOSURE",
                                "channel": False, "closure": fill["closure"]})
                continue
            if fill.get("kept"):
                for lo, hi, code in fill["pieces"]:
                    orig = None
                    for r in window_rows:
                        if abs(r["lo"] - lo) <= 0.01 and abs(r["hi"] - hi) <= 0.01:
                            orig = r["cand"]
                    members.append({"lo": lo, "hi": hi, "code": "KEEP", "cand": orig, "kind": "KEEP",
                                    "channel": True})
                continue
            for lo, hi, code in fill["pieces"]:
                members.append({"lo": lo, "hi": hi, "code": code, "cand": template_c, "kind": "FREE",
                                "channel": True})
    # pecas: blocos copiados de r, canaletas agrupadas pela 51.3
    pieces = []
    info = {"follow": 0, "free": 0, "cuts": 0, "kept": 0, "blocks_from_below": 0}
    k = 0
    while k < len(members):
        m = members[k]
        if m["kind"] == "CLOSURE":
            made = _closure_candidates(ctx, m["closure"], m["lo"], m["hi"], template_c, course_value, wall_idx)
            for lo, hi, cand in made:
                orig = by_extent.get((cand.get("logical_code"), round(lo, 1), round(hi, 1)))
                pieces.append((lo, hi, orig if orig is not None else cand))
            info["jamb_closures"] = info.get("jamb_closures", 0) + len(made)
            findings.append({"code": "GRID_FOLLOW_JAMB_CLOSURE", "codes": list(m["closure"][1]),
                             "lo_cm": round(m["lo"], 3), "hi_cm": round(m["hi"], 3)})
            k += 1
            continue
        if not m["channel"]:
            orig = by_extent.get((m["code"], round(m["lo"], 1), round(m["hi"], 1)))
            if orig is not None:
                pieces.append((m["lo"], m["hi"], orig))
            else:
                src = m["cand"]
                code = src.get("logical_code")
                if _orf.is_channel_code(code):
                    eq = BLOCK_OF_CHANNEL.get(code)
                    catalog = ctx.get("catalog") or {}
                    if eq is None or eq not in catalog:
                        return None, "CHANNEL_BELOW_UNDER_BLOCK"
                    new = _make_block_candidate(eq, catalog[eq], course_value, src["origin_world"], src["x_dir"],
                                                "STANDARD_FILL", wall_idx=wall_idx)
                else:
                    new = _template(src, course_value)
                pieces.append((m["lo"], m["hi"], new))
                info["blocks_from_below"] += 1
            k += 1
            continue
        k1 = k
        while k1 + 1 < len(members) and members[k1 + 1]["channel"]:
            k1 += 1
        run = members[k:k1 + 1]
        k = k1 + 1
        groups = []
        buf = []
        for x in run:
            if x["kind"] == "KEEP":
                if buf:
                    groups.extend(_group_members(buf, cpol))
                    buf = []
                groups.append([x])
            else:
                buf.append(x)
        if buf:
            groups.extend(_group_members(buf, cpol))
        for g in groups:
            lo, hi = g[0]["lo"], g[-1]["hi"]
            if g[0]["kind"] == "KEEP":
                if g[0]["cand"] is None:
                    return None, "KEPT_PIECE_LOST"
                pieces.append((lo, hi, g[0]["cand"]))
                info["kept"] += 1
                continue
            if len(g) == 1 and g[0]["code"] == FREE_SHORT:
                # sobra curta sem vizinha para fundir: nenhuma peca minuscula nova
                return None, "FREE_SHORT_UNMERGED"
            src_codes = []
            rows = []
            for x in g:
                tpl = _template(x["cand"], course_value)
                if x["kind"] == "FREE" or x["code"] in (FREE_CUT, FREE_SHORT):
                    tpl["logical_code"] = x["code"] if x["code"] in ("B39", "B34", "B19") else FREE_CUT
                    src_codes.append("FREE")
                elif x.get("split"):
                    tpl["logical_code"] = "TIE_SPLIT"
                    src_codes.append("B54_SPLIT")
                else:
                    tpl["logical_code"] = x["code"] if x["code"] != _orf.CHANNEL_U_CUT else FREE_CUT
                    src_codes.append(x["code"])
                rows.append({"cand": tpl, "lo": x["lo"], "hi": x["hi"]})
            heir = _inherit(lo, hi, originals)
            rein = dict((heir["cand"].get("reinforcement") or {})) if heir is not None else {}
            record = {"roles": list(rein.get("roles") or [_orf.ROLE_TOP_BOND_BEAM]),
                      "run_id": rein.get("run_id"), "opening_indices": list(rein.get("opening_indices") or [])}
            piece_policy = dict(cpol)
            piece_policy["policy_version"] = rein.get("policy_version") or cpol.get("policy_version")
            new = _orf._channel_candidate_from_group(rows, walls, wall_idx, record, piece_policy)
            orig = by_extent.get((new["logical_code"], round(lo, 1), round(hi, 1)))
            if orig is not None and is_target_channel(orig):
                pieces.append((lo, hi, orig))
                info["kept"] += 1
                continue
            cut = new["reinforcement"].get("cut")
            new_rein = dict(rein)
            new_rein["source_codes"] = src_codes
            new_rein["cut"] = cut
            new_rein["grid_follow"] = {"section": SECTION, "source_course": source_course,
                                       "kind": "FREE" if all(c == "FREE" for c in src_codes) else (
                                           "FOLLOW" if "FREE" not in src_codes else "FOLLOW+FREE")}
            if not new_rein.get("strategy"):
                new_rein["strategy"] = _orf.OPENING_REINFORCEMENT_CHANNEL
            if not new_rein.get("policy_version"):
                new_rein["policy_version"] = piece_policy["policy_version"]
            new["reinforcement"] = new_rein
            new["placement_reason"] = (heir["cand"].get("placement_reason") if heir is not None
                                       else new.get("placement_reason")) or "STANDARD_FILL"
            pieces.append((lo, hi, new))
            if new["logical_code"] == _orf.CHANNEL_U_CUT:
                info["cuts"] += 1
            if "FREE" in src_codes:
                info["free"] += 1
            else:
                info["follow"] += 1
    info["findings"] = findings
    return pieces, info


def _check_invariants(ctx, pieces, chosen, seg_rows, zones, squares):
    """Conferencia final (independente do construtor): sem sobreposicao, dentro dos
    limites da janela, nenhuma canaleta no quadrado de no', corrida nunca encolhe."""
    pol = ctx["pol"]
    x, y = chosen["window"]
    lo_lim = (chosen["x_prev_hi"] + pol["min_joint_cm"]) if chosen["x_prev_hi"] is not None else (
        x - pol["hard_edge_tolerance_cm"])
    hi_lim = (chosen["y_next_lo"] - pol["min_joint_cm"]) if chosen["y_next_lo"] is not None else (
        y + pol["hard_edge_tolerance_cm"])
    if not pieces:
        return "EMPTY"
    if pieces[0][0] < lo_lim - 1e-6 or pieces[-1][1] > hi_lim + 1e-6:
        return "OUT_OF_WINDOW"
    for a, b in zip(pieces, pieces[1:]):
        if b[0] - a[1] < pol["min_joint_cm"] - 1e-6 or b[0] - a[1] > pol["wide_joint_cm"] + 1e-6:
            return "BAD_JOINT"
    margin = pol["node_square_margin_cm"]
    for lo, hi, cand in pieces:
        if _orf.is_channel_code(cand.get("logical_code")) and _orf._square_hit(lo, hi, squares, margin) is not None:
            return "CHANNEL_AT_NODE"
    for z in zones:
        if not any(_orf.is_channel_code(c.get("logical_code")) for lo, hi, c in pieces
                   if min(hi, z[1]) - max(lo, z[0]) > 0.05):
            return "ZONE_LOST"
        covered_lo = min([lo for lo, hi, c in pieces if _orf.is_channel_code(c.get("logical_code"))
                          and hi > z[0] - 3.0 and lo < z[1] + 3.0] or [1e9])
        covered_hi = max([hi for lo, hi, c in pieces if _orf.is_channel_code(c.get("logical_code"))
                          and hi > z[0] - 3.0 and lo < z[1] + 3.0] or [-1e9])
        if covered_lo > z[0] + 0.05 or covered_hi < z[1] - 0.05:
            return "RUN_SHRANK"
    return None


# --------------------------------------------------------------------------
# entrada
# --------------------------------------------------------------------------
def plan_channel_grid_follow(course_candidates, walls_to_create, num_courses, nodes=None, channel_overrides=None,
                             policy=None, catalog=None):
    """SECAO 86.12 - alinha as canaletas (verga, contraverga, cinta) a' grade da
    fiada de mesma paridade abaixo (r = c-2). Nao muta `course_candidates`.

    Devolve {"course_candidates", "policy", "windows", "unresolved", "findings",
    "counts", "source_courses", "runs_touched"}. `source_courses` = fiadas tocadas
    como eram ANTES (a paridade 82.1 mede a grade do motor, nunca a deste passe)."""
    pol = channel_grid_follow_policy(policy)
    cpol = _orf.channel_policy(channel_overrides)
    out_cc = dict((ci, list(pcs or [])) for ci, pcs in (course_candidates or {}).items())
    counts = {"courses_checked": 0, "segments_checked": 0, "windows_changed": 0, "pieces_removed": 0,
              "pieces_created": 0, "channel_pieces_created": 0, "block_pieces_from_below": 0,
              "cuts_created": 0, "free_fills": 0, "jamb_closures": 0, "unresolved": 0, "flank_mismatch": 0}
    report = {"enabled": True, "section": SECTION, "policy": pol, "windows": [], "unresolved": [],
              "findings": [], "counts": counts, "source_courses": {}, "runs_touched": [],
              "course_candidates": out_cc}
    courses = sorted(ci for ci in out_cc if any(is_target_channel(c) for c in out_cc.get(ci) or []))
    runs_touched = set()
    for ci in courses:
        counts["courses_checked"] += 1
        r = ci - 2
        needed = [k for k in (ci, r, ci - 1, ci + 1) if k in out_cc]
        buckets = _orf.course_wall_buckets(dict((k, out_cc[k]) for k in needed))
        changed_course = False
        new_course = list(out_cc[ci])
        for wall_idx in range(len(walls_to_create)):
            own = _orf._bucket(buckets, ci, wall_idx)
            if not any(is_target_channel(c) and c.get("wall_idx") == wall_idx for c in own):
                continue
            if r < 0 or r not in out_cc:
                counts["unresolved"] += 1
                report["unresolved"].append({"wall_idx": wall_idx, "course_index": ci,
                                             "reason": "NO_SAME_PARITY_COURSE_BELOW"})
                continue
            squares = _orf._node_squares_cm(walls_to_create, nodes, wall_idx)
            rows_c = _orf._wall_strip_pieces(own, walls_to_create, wall_idx)
            rows_r = _orf._wall_strip_pieces(_orf._bucket(buckets, r, wall_idx), walls_to_create, wall_idx)
            adj = []
            if ci - 1 in out_cc:
                adj.extend(_orf._row_joints_cm(
                    _orf._wall_strip_pieces(_orf._bucket(buckets, ci - 1, wall_idx), walls_to_create, wall_idx),
                    pol["max_joint_cm"]))
            if ci + 1 in out_cc:
                # a fiada de cima ainda vai passar por este passe onde tiver canaleta-alvo
                # (copia c-1 sobre alvenaria, e' livre sobre o vao): so' as juntas entre
                # pecas que ficam contam
                above = _orf._wall_strip_pieces(_orf._bucket(buckets, ci + 1, wall_idx), walls_to_create,
                                                wall_idx)
                for ra, rb in zip(above, above[1:]):
                    if 0.0 <= rb["lo"] - ra["hi"] <= pol["max_joint_cm"] and \
                            not is_target_channel(ra["cand"]) and not is_target_channel(rb["cand"]):
                        adj.append((ra["hi"] + rb["lo"]) / 2.0)
            adj.sort()
            margin = pol["node_square_margin_cm"]
            anchors = [a for a in (_anchor_of(x, wall_idx, squares, margin) for x in rows_r) if a is not None]
            ctx = {"pol": pol, "cpol": cpol, "walls": walls_to_create, "catalog": catalog,
                   "canonical": _canonical_axis(walls_to_create, wall_idx), "fill_cache": {}}
            for i0, i1, prev_hi, next_lo in _segments(rows_c, wall_idx, squares, pol):
                seg_rows = rows_c[i0:i1 + 1]
                zones = _subzones(seg_rows, pol)
                if not zones:
                    continue
                counts["segments_checked"] += 1
                chosen, reason, detail = _follow_segment(ctx, seg_rows, prev_hi, next_lo, anchors, adj)
                if chosen is None:
                    if reason is not None:
                        counts["unresolved"] += 1
                        item = {"wall_idx": wall_idx, "course_index": ci, "source_course": r, "reason": reason,
                                "zone_cm": [round(zones[0][0], 3), round(zones[-1][1], 3)]}
                        if detail:
                            item.update(detail)
                        report["unresolved"].append(item)
                    continue
                pieces, info = _materialize(ctx, chosen, seg_rows, zones, adj, wall_idx, ci, r)
                if pieces is None:
                    counts["unresolved"] += 1
                    report["unresolved"].append({"wall_idx": wall_idx, "course_index": ci, "source_course": r,
                                                 "reason": info,
                                                 "zone_cm": [round(zones[0][0], 3), round(zones[-1][1], 3)]})
                    continue
                broken = _check_invariants(ctx, pieces, chosen, seg_rows, zones, squares)
                if broken is not None:
                    counts["unresolved"] += 1
                    report["unresolved"].append({"wall_idx": wall_idx, "course_index": ci, "source_course": r,
                                                 "reason": "INVARIANT_" + broken,
                                                 "zone_cm": [round(zones[0][0], 3), round(zones[-1][1], 3)]})
                    continue
                i_first, i_last = chosen["window_idx"]
                old = [x["cand"] for x in seg_rows[i_first:i_last + 1]]
                new = [p[2] for p in pieces]
                if len(old) == len(new) and all(a is b for a, b in zip(old, new)):
                    continue
                # troca na fiada (as pecas novas no lugar da primeira removida)
                old_ids = set(id(c) for c in old)
                rebuilt = []
                inserted = False
                for cand in new_course:
                    if id(cand) in old_ids:
                        if not inserted:
                            rebuilt.extend(new)
                            inserted = True
                        continue
                    rebuilt.append(cand)
                if not inserted:
                    rebuilt.extend(new)
                new_course = rebuilt
                changed_course = True
                kept_ids = set(id(c) for c in new)
                removed = [c for c in old if id(c) not in kept_ids]
                created = [c for c in new if id(c) not in old_ids]
                counts["windows_changed"] += 1
                counts["pieces_removed"] += len(removed)
                counts["pieces_created"] += len(created)
                counts["channel_pieces_created"] += sum(1 for c in created if _orf.is_channel_code(c.get("logical_code")))
                counts["block_pieces_from_below"] += info["blocks_from_below"]
                counts["cuts_created"] += info["cuts"]
                counts["jamb_closures"] += info.get("jamb_closures", 0)
                counts["free_fills"] += sum(1 for it in chosen["items"] if it[0] == "F")
                if chosen.get("flank_mismatch"):
                    counts["flank_mismatch"] += 1
                for c in new:
                    rid = (c.get("reinforcement") or {}).get("run_id")
                    if rid:
                        runs_touched.add(rid)
                for f in info.get("findings") or []:
                    report["findings"].append(dict(f, wall_idx=wall_idx, course_index=ci))
                report["windows"].append({
                    "wall_idx": wall_idx, "course_index": ci, "source_course": r,
                    "window_cm": [round(chosen["window"][0], 3), round(chosen["window"][1], 3)],
                    "zone_cm": [round(zones[0][0], 3), round(zones[-1][1], 3)],
                    "flank_mismatch": list(chosen.get("flank_mismatch") or []),
                    "free_cm": [[round(it[1], 3), round(it[2], 3)] for it in chosen["items"] if it[0] == "F"],
                    "before": [[x["cand"].get("logical_code"), round(x["lo"], 2), round(x["hi"], 2)]
                               for x in seg_rows[i_first:i_last + 1]],
                    "after": [[p[2].get("logical_code"), round(p[0], 2), round(p[1], 2)] for p in pieces],
                    "removed": len(removed), "created": len(created)})
        if changed_course:
            report["source_courses"][ci] = out_cc[ci]
            out_cc[ci] = new_course
    report["runs_touched"] = sorted(runs_touched)
    return report


# --------------------------------------------------------------------------
# relatorio do reforco depois do passe
# --------------------------------------------------------------------------
def refresh_plan_records(plan, course_candidates, walls_to_create, runs_touched):
    """Atualiza `plan["runs"]` (extensao e pecas) e o apoio/assentamento das
    aberturas das corridas tocadas pela 86.12 - o rastreio das aberturas
    (_attach_opening_structural_trace) le o plano. O apoio so' pode crescer: valor
    menor que o anterior fica registrado em `grid_follow_support_drop`."""
    if not plan or not runs_touched:
        return []
    touched = set(runs_touched)
    gap = (plan.get("policy") or {}).get("contiguous_gap_cm", 2.0) + _orf.CONTIGUOUS_GAP_EPSILON_CM
    drops = []
    cache = {}

    def rows_of(ci, wi):
        key = (ci, wi)
        if key not in cache:
            cache[key] = _orf._wall_strip_pieces(course_candidates.get(ci) or [], walls_to_create, wi)
        return cache[key]

    for rec in plan.get("runs") or []:
        if rec.get("run_id") not in touched:
            continue
        rows = [r for r in rows_of(rec["course_index"], rec["wall_idx"])
                if (r["cand"].get("reinforcement") or {}).get("run_id") == rec["run_id"]
                and r["cand"].get("wall_idx") == rec["wall_idx"]]
        if not rows:
            continue
        rec["lo_cm"] = round(rows[0]["lo"], 3)
        rec["hi_cm"] = round(rows[-1]["hi"], 3)
        rec["pieces"] = [{"code": r["cand"].get("logical_code"), "lo_cm": round(r["lo"], 3),
                          "hi_cm": round(r["hi"], 3),
                          "source_codes": list((r["cand"].get("reinforcement") or {}).get("source_codes") or [])}
                         for r in rows]
        rec["grid_follow"] = SECTION
    for orec in plan.get("openings") or []:
        for side_key in ("above", "below"):
            side = orec.get(side_key) or {}
            if side.get("status") != "CHANNEL" or side.get("run_id") not in touched:
                continue
            ci, wi = side.get("course_index"), orec.get("wall_idx")
            t_lo, t_hi = orec.get("t_lo_cm"), orec.get("t_hi_cm")
            rows = [r for r in rows_of(ci, wi)
                    if r["along"] and _orf.is_channel_code(r["cand"].get("logical_code"))
                    and r["cand"].get("wall_idx") == wi]
            if not rows or side.get("support_l_cm") is None or side.get("support_r_cm") is None:
                continue
            # mesma semantica do planejador: a ponta da corrida DESTA abertura vai
            # ate' a peca (agora alinhada a' fiada c-2) que cobre a ponta antiga
            old_lo = t_lo - side["support_l_cm"]
            old_hi = t_hi + side["support_r_cm"]
            left_row = next((r for r in rows if r["lo"] <= old_lo + 0.5 + 1e-6 and r["hi"] >= old_lo + 0.5), None)
            if left_row is None:
                left_row = next((r for r in rows if r["lo"] >= old_lo - gap), None)
            right_row = None
            for r in rows:
                if r["hi"] >= old_hi - 0.5 - 1e-6 and r["lo"] <= old_hi - 0.5:
                    right_row = r
            if right_row is None:
                right_row = next((r for r in reversed(rows) if r["hi"] <= old_hi + gap), None)
            if left_row is None or right_row is None:
                continue
            sup_l = round(t_lo - left_row["lo"], 3)
            sup_r = round(right_row["hi"] - t_hi, 3)
            for name, new_value in (("support_l_cm", sup_l), ("support_r_cm", sup_r)):
                old_value = side.get(name)
                if old_value is not None and new_value < old_value - 0.05:
                    drops.append({"wall_idx": wi, "opening_index": orec.get("opening_index"), "side": side_key,
                                  "field": name, "before": old_value, "after": new_value})
                    side.setdefault("grid_follow_support_drop", []).append(name)
                    continue
                side[name] = new_value
            if ci is not None and ci > 0:
                below = rows_of(ci - 1, wi)
                side["bearing_l_cm"] = round(_orf._bearing_cm(below, t_lo - side["support_l_cm"], t_lo), 3)
                side["bearing_r_cm"] = round(_orf._bearing_cm(below, t_hi, t_hi + side["support_r_cm"]), 3)
            side["grid_follow"] = SECTION
    return drops
