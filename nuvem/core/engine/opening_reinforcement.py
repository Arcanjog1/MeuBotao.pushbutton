# -*- coding: utf-8 -*-
"""Estrategia de REFORCO DE ABERTURAS - somente CHANNEL (canaletas).

Arquitetura (docs/architecture/opening-reinforcement-strategies.md): UM motor
comum + OpeningReinforcementStrategy. Este modulo NAO resolve fiadas, nos nem
preenchimento - recebe as fiadas FISICAS ja' resolvidas pelo motor
(`course_candidates`) e planeja o reforco sobre elas.

Sistema fisico (evidencia BUTANTA R08_LT, regra 51 de REGRAS_MODULACAO_BLOCOS.md):

- o reforco e' uma FIADA INTEIRA de canaleta (19 cm), parte da grade modular -
  nao e' peca sobreposta de 9 cm;
- acima do vao: a fiada cuja BASE coincide com o topo do vao;
- abaixo do peitoril: a fiada cujo TOPO coincide com o peitoril (uma fiada so');
- a corrida e' composta pelas pecas da propria fiada: o layout (juntas,
  amarracoes, paridade) NAO muda - B39/B34/B19 viram canaleta 39/34/19 e os
  compensadores sao fundidos a uma vizinha como canaleta cortada no
  comprimento (LENGTH_CUT). Fundir so' REMOVE juntas; nunca cria junta nova,
  entao a regra #1 (prisma) nao pode piorar por causa do reforco;
- a corrida passa das jambas ate' o apoio preferencial e para em peca de
  amarracao de no' (B54/B34 de L/T/X), fim de parede ou vazio - nunca troca
  nem move uma amarracao;
- cinta de topo (TOP_BOND_BEAM) e' mecanismo SEPARADO e NAO e' gerada aqui
  (decisao pendente, DECISION-TOP-BOND-BEAM).

Compativel com IronPython 2.7 (sem f-string, sem math.isfinite).
"""

from core.engine.wall_stepper import (  # noqa: F401
    XYZ,
    _make_block_candidate,
    _wall_junction_nodes_and_ts_ft,
    _wall_axis_and_length,
    _candidate_t_range_on_wall,
    _cm_to_ft,
    _ft_to_cm,
    _candidate_obb,
    _obb_min_overlap,
    _obb_aabb,
    _collision_candidate_pairs,
    BOND_COLLISION_EPS_FT,
)

OPENING_REINFORCEMENT_CHANNEL = "CHANNEL"
# LINTEL_COUNTERLINTEL fica so' como nome reservado do contrato - NAO
# implementado (fora do escopo desta estrategia).
OPENING_REINFORCEMENT_STRATEGIES = (OPENING_REINFORCEMENT_CHANNEL,)

ROLE_ABOVE_OPENING = "ABOVE_OPENING"
ROLE_BELOW_SILL = "BELOW_SILL"

CHANNEL_U_39 = "CHANNEL_U_39"
CHANNEL_U_34 = "CHANNEL_U_34"
CHANNEL_U_19 = "CHANNEL_U_19"
CHANNEL_U_CUT = "CHANNEL_U_CUT"

# Catalogo LOGICO (nao e' nome de familia). Realizacao Revit em
# wall_modeling.CHANNEL_FAMILY_CATALOG_DEFINITIONS.
CHANNEL_LOGICAL_TYPES = {
    CHANNEL_U_39: {"nominal_length_cm": 39.0, "height_cm": 19.0, "width_cm": 14.0,
                   "profile": "U", "realization": "DEDICATED_TYPE"},
    CHANNEL_U_34: {"nominal_length_cm": 34.0, "height_cm": 19.0, "width_cm": 14.0,
                   "profile": "U", "realization": "DEDICATED_TYPE"},
    CHANNEL_U_19: {"nominal_length_cm": 19.0, "height_cm": 19.0, "width_cm": 14.0,
                   "profile": "U", "realization": "DEDICATED_TYPE"},
    # LENGTH_CUT de uma canaleta de 39: altura preservada, comprimento final
    # por peca (parametro de instancia na familia VAR).
    CHANNEL_U_CUT: {"nominal_length_cm": 39.0, "height_cm": 19.0, "width_cm": 14.0,
                    "profile": "U", "realization": "INSTANCE_LENGTH"},
}
CHANNEL_CODES = tuple(sorted(CHANNEL_LOGICAL_TYPES))

# Peca comum -> canaleta de MESMO comprimento (mesma junta, mesmo lugar).
COMMON_TO_CHANNEL = {"B39": CHANNEL_U_39, "B34": CHANNEL_U_34, "B19": CHANNEL_U_19}
# Pecas que nao tem canaleta de mesmo comprimento: fundidas (LENGTH_CUT).
COMPENSATOR_CODES = ("C09", "C04")
# Trecho do no' atravessado pela canaleta (ver _crossing_row): funde como
# compensador.
CROSSING_CODE = "NODE_CROSSING"
MERGEABLE_CODES = COMPENSATOR_CODES + (CROSSING_CODE,)
CROSSING_ABUTMENT_REASON = "T_INTERSECTION_INCOMING_CHANNEL_ABUTMENT"
# Parte de um B54 de no' dividido em duas canaletas (ver _tie_split_rows).
TIE_SPLIT_CODE = "TIE_SPLIT"
STANDARD_CHANNEL_BY_LENGTH = ((39.0, CHANNEL_U_39), (34.0, CHANNEL_U_34), (19.0, CHANNEL_U_19))

TIE_REASON_PREFIXES = ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION", "CORNER")

SEVERITY_ERROR = "ERROR"
SEVERITY_WARNING = "WARNING"
SEVERITY_INFO = "INFO"

DEFAULT_CHANNEL_POLICY = {
    "policy_version": "CHANNEL-2026-09-14-BUTANTA-EVIDENCE",
    # Apoio preferencial de cada lado (jamba -> ponta da corrida), em cm.
    # Evidencia BUTANTA 1o PAV: 119/126 lados >= 19; os menores estao
    # encostados em no'/fim de parede. NAO e' o >=9 de verga (TORRE EASY).
    "min_support_cm": 19.0,
    # Tolerancia de cota para "base da fiada = topo do vao" / "topo da
    # fiada = peitoril" (mesma ordem de OPENING_COURSE_BAND_TOLERANCE_CM).
    "grid_tolerance_cm": 0.5,
    # Uma junta de assentamento (1 cm) entre o topo do vao e a base da fiada
    # (ou entre o topo da fiada e o peitoril) e' a MESMA solucao - BUTANTA
    # 6616547: vao ate' 220, canaleta em 221 (errata do acervo).
    "grid_joint_allowance_cm": 1.0,
    # Folga maxima entre duas pecas CONTIGUAS da mesma corrida (junta 1 cm).
    "contiguous_gap_cm": 1.5,
    "merge_compensators": True,
    "max_channel_length_cm": 39.0,
    # Menor canaleta cortada observada no humano (9 cm): abaixo disso vira
    # achado (a peca e' criada mesmo assim, nunca some em silencio).
    "observed_min_cut_length_cm": 9.0,
    # Vao sem peitoril com as DUAS jambas encostadas em amarracao de no':
    # passagem livre ate' o topo (BUTANTA K.1, PAR28). PADRAO OBSERVADO.
    "free_to_top_tie_bounded_passages": True,
    # Jamba "encostada" no no': distancia jamba -> eixo do no' <= meio B54
    # (27 cm) + folga. BUTANTA 1o PAV: so' os 2 vaos de PAR28 (27/27 cm).
    "tie_bounded_max_jamb_to_node_cm": 28.5,
    "tie_bounded_gap_cm": 1.5,
    # Canaleta ATRAVESSA o T (parede principal continua nesta fiada; a peca
    # da parede que chega encosta na face) quando, sem isso, o apoio daquele
    # lado seria <= este valor. BUTANTA 1o PAV: 3 vaos com jamba na face do T
    # (6599856, 6599933, 6644707), acima e abaixo - o humano atravessa em
    # todos (KV 14/24 sobre o no'). Com apoio > 0 (ex.: 4 cm) o humano para.
    "cross_tee_when_support_at_most_cm": 0.0,
    "course_joint_cm": 1.0,
    # Amarracao AO LONGO desta parede que cai sobre o vao (ou encosta na
    # jamba com apoio <= cross_tee_when_support_at_most_cm) na fiada da
    # canaleta: vira canaleta sem mudar a topologia do no' - B34/C09 com a
    # MESMA geometria; B54 dividido em duas canaletas com a junta nova o mais
    # longe possivel das juntas das fiadas vizinhas (minimo abaixo).
    "convert_blocking_along_ties": True,
    "tie_split_lengths_cm": (39.0, 34.0, 29.0, 24.0, 19.0, 14.0, 9.0),
    "tie_split_min_stagger_cm": 1.5,
}


def channel_policy(overrides=None):
    policy = dict(DEFAULT_CHANNEL_POLICY)
    for key, value in (overrides or {}).items():
        policy[key] = value
    return policy


def is_channel_code(code):
    return code in CHANNEL_LOGICAL_TYPES


def _is_tie(candidate):
    reason = str(candidate.get("placement_reason") or "")
    return any(reason.startswith(p) for p in TIE_REASON_PREFIXES)


def _along(candidate, wall_dir):
    x_dir = candidate.get("x_dir")
    if x_dir is None:
        return False
    return abs(x_dir.X * wall_dir.X + x_dir.Y * wall_dir.Y) > 0.99


def _eligible(candidate, wall_dir):
    """Peca que pode virar canaleta: preenchimento ao longo da parede."""
    if not _along(candidate, wall_dir) or _is_tie(candidate):
        return False
    code = candidate.get("logical_code")
    return code in COMMON_TO_CHANNEL or code in COMPENSATOR_CODES or is_channel_code(code)


def _wall_strip_pieces(course_pieces, walls_to_create, wall_idx):
    """Pecas de UMA fiada fisica que ocupam a faixa da parede, com extensao
    no eixo (cm). Transversais (amarracao da outra parede) entram como
    bloqueio, com a espessura como extensao."""
    p0, _p1, wall_dir, _len_ft, thickness_ft = _wall_axis_and_length(walls_to_create, wall_idx)
    normal = XYZ(-wall_dir.Y, wall_dir.X, 0.0)
    half_th_cm = _ft_to_cm(thickness_ft) / 2.0
    rows = []
    for cand in course_pieces:
        if cand.get("wall_idx") != wall_idx and cand.get("secondary_wall_idx") != wall_idx:
            continue
        if _along(cand, wall_dir):
            lo, hi = _candidate_t_range_on_wall(cand, p0, wall_dir)
        else:
            # transversal: so' conta se o comprimento dela entra na faixa da
            # parede (a peca recuada ate' a face, na travessia de T, nao entra).
            n_center = _ft_to_cm((cand["origin_world"] - p0).DotProduct(normal))
            n_half = (cand.get("length_cm") or 0.0) / 2.0
            if n_center + n_half <= -half_th_cm + 0.5 or n_center - n_half >= half_th_cm - 0.5:
                continue
            center = _ft_to_cm((cand["origin_world"] - p0).DotProduct(wall_dir))
            half = (cand.get("width_cm") or 14.0) / 2.0
            lo, hi = center - half, center + half
        rows.append({"cand": cand, "lo": lo, "hi": hi, "along": _along(cand, wall_dir),
                     "eligible": _eligible(cand, wall_dir), "tie": _is_tie(cand)})
    rows.sort(key=lambda r: (round(r["lo"], 4), round(r["hi"], 4)))
    return rows


def _course_for_head(head_z, course_band, num_courses, tol_ft, joint_ft=0.0):
    """Primeira fiada cuja base esta' no topo do vao (ou uma junta acima)."""
    for ci in range(num_courses):
        z_lo, _z_hi = course_band(ci)
        if z_lo >= head_z - tol_ft:
            return ci if z_lo - head_z <= joint_ft + tol_ft else None
    return None


def _course_for_sill(sill_z, course_band, num_courses, tol_ft, joint_ft=0.0):
    """Ultima fiada cujo topo esta' no peitoril (ou uma junta abaixo)."""
    found = None
    for ci in range(num_courses):
        _z_lo, z_hi = course_band(ci)
        if z_hi <= sill_z + tol_ft:
            found = ci
    if found is None:
        return None
    return found if sill_z - course_band(found)[1] <= joint_ft + tol_ft else None


def _opening_active(opening, z_lo, z_hi, tol_ft):
    lo = max(opening[2], z_lo)
    hi = min(opening[3], z_hi)
    return (hi - lo) > tol_ft


def _jamb_node_bounded(walls_to_create, nodes, wall_idx, opening, side, max_cm):
    """True se a jamba `side` fica a <= max_cm do eixo de um no' L/T/X REAL
    da parede, do lado de fora do vao (geometria do grafo, nao das pecas)."""
    t_jamb = _ft_to_cm(opening[0] if side < 0 else opening[1])
    for _node, t_ft in _wall_junction_nodes_and_ts_ft(walls_to_create, nodes, wall_idx):
        t_node = _ft_to_cm(t_ft)
        outside = (t_node <= t_jamb + 0.5) if side < 0 else (t_node >= t_jamb - 0.5)
        if outside and abs(t_node - t_jamb) <= max_cm:
            return True
    return False


def _jamb_tie_bounded(course_candidates, walls_to_create, wall_idx, opening, course_band, num_courses,
                      side, gap_cm, tol_ft):
    """Sem grafo: True se, em alguma fiada que atravessa o vao, a peca
    imediatamente fora da jamba `side` e' amarracao de no'."""
    t_lo = _ft_to_cm(opening[0])
    t_hi = _ft_to_cm(opening[1])
    for ci in range(num_courses):
        z_lo, z_hi = course_band(ci)
        if not _opening_active(opening, z_lo, z_hi, tol_ft):
            continue
        rows = _wall_strip_pieces(course_candidates.get(ci) or [], walls_to_create, wall_idx)
        if side < 0:
            near = [r for r in rows if r["hi"] <= t_lo + gap_cm and t_lo - r["hi"] <= gap_cm]
        else:
            near = [r for r in rows if r["lo"] >= t_hi - gap_cm and r["lo"] - t_hi <= gap_cm]
        if any(r["tie"] for r in near):
            return True
    return False


def _extend_run(rows, i0, i1, t_lo, t_hi, policy, cross=None):
    """Estende [i0, i1] (indices em `rows`) peca a peca ate' o apoio
    preferencial. `cross(j, support_cm)` pode transformar a amarracao `rows[j]`
    em trecho atravessavel (devolve True). Devolve (i0, i1, lim_esq, lim_dir)."""
    gap = policy["contiguous_gap_cm"]
    need = policy["min_support_cm"]
    limits = [None, None]
    while t_lo - rows[i0]["lo"] < need - 1e-6:
        j = i0 - 1
        if j < 0:
            limits[0] = "WALL_END"
            break
        prev = rows[j]
        if rows[i0]["lo"] - prev["hi"] > gap:
            limits[0] = "GAP"
            break
        if prev["tie"] and cross is not None:
            added = cross(j, t_lo - rows[i0]["lo"])
            if added:
                i0 += added - 1
                i1 += added - 1
                continue
        if prev["tie"]:
            limits[0] = "JUNCTION_TIE"
            break
        if not prev["eligible"]:
            limits[0] = "INELIGIBLE_PIECE"
            break
        i0 = j
    while rows[i1]["hi"] - t_hi < need - 1e-6:
        j = i1 + 1
        if j >= len(rows):
            limits[1] = "WALL_END"
            break
        nxt = rows[j]
        if nxt["lo"] - rows[i1]["hi"] > gap:
            limits[1] = "GAP"
            break
        if nxt["tie"] and cross is not None:
            if cross(j, rows[i1]["hi"] - t_hi):
                continue
        if nxt["tie"]:
            limits[1] = "JUNCTION_TIE"
            break
        if not nxt["eligible"]:
            limits[1] = "INELIGIBLE_PIECE"
            break
        i1 = j
    return i0, i1, limits[0], limits[1]


def _standard_code_for_length(length_cm, tol=0.05):
    for nominal, code in STANDARD_CHANNEL_BY_LENGTH:
        if abs(length_cm - nominal) <= tol:
            return code
    return None


def _group_run_members(members, policy):
    """Agrupa as pecas da corrida (ordenadas no eixo) em canaletas.

    Peca comum -> um grupo proprio. Compensador -> fundido a uma vizinha
    CONTIGUA se o comprimento final <= max_channel_length_cm; prefere a
    fusao que da' canaleta de comprimento padrao (39/34/19), depois a da
    esquerda. Sem fusao possivel, vira canaleta cortada sozinho."""
    max_len = policy["max_channel_length_cm"]
    gap = policy["contiguous_gap_cm"]
    groups = []
    k = 0
    n = len(members)
    while k < n:
        row = members[k]
        code = row["cand"].get("logical_code")
        if code not in MERGEABLE_CODES or not policy.get("merge_compensators", True):
            groups.append([row])
            k += 1
            continue
        options = []
        if groups:
            last = groups[-1]
            if row["lo"] - last[-1]["hi"] <= gap:
                length = row["hi"] - last[0]["lo"]
                if length <= max_len + 0.05:
                    options.append((0 if _standard_code_for_length(length) else 1, 0, "LEFT"))
        if k + 1 < n:
            nxt = members[k + 1]
            if nxt["lo"] - row["hi"] <= gap:
                length = nxt["hi"] - row["lo"]
                if length <= max_len + 0.05:
                    options.append((0 if _standard_code_for_length(length) else 1, 1, "RIGHT"))
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


def _channel_candidate_from_group(group, walls_to_create, wall_idx, run_record, policy):
    p0, _p1, wall_dir, _len_ft, _th = _wall_axis_and_length(walls_to_create, wall_idx)
    first = group[0]["cand"]
    lo = group[0]["lo"]
    hi = group[-1]["hi"]
    length = hi - lo
    source_codes = [g["cand"].get("logical_code") for g in group]
    if len(group) == 1 and source_codes[0] in COMMON_TO_CHANNEL:
        code = COMMON_TO_CHANNEL[source_codes[0]]
        cut = None
    else:
        code = _standard_code_for_length(length) or CHANNEL_U_CUT
        cut = None
        if code == CHANNEL_U_CUT:
            cut = {"kind": "LENGTH_CUT", "axis": "LOCAL_U",
                   "original_dimension_cm": CHANNEL_LOGICAL_TYPES[CHANNEL_U_CUT]["nominal_length_cm"],
                   "final_dimension_cm": round(length, 4)}
    new = dict(first)
    # Centro no eixo da parede preservando a posicao lateral e o Z da peca original.
    old_center_t = (first["origin_world"] - p0).DotProduct(wall_dir)
    new_center_t = _cm_to_ft((lo + hi) / 2.0)
    new["origin_world"] = first["origin_world"] + wall_dir * (new_center_t - old_center_t)
    new["logical_code"] = code
    new["length_cm"] = length if code == CHANNEL_U_CUT else CHANNEL_LOGICAL_TYPES[code]["nominal_length_cm"]
    new["cells_world"] = []
    # Canaleta U e' simetrica: a orientacao de compensador (regra #3) nao
    # se aplica a ela.
    new["mirrored"] = False
    if first.get("logical_code") == CROSSING_CODE:
        new["placement_reason"] = "STANDARD_FILL"
    new["instance_length_cm"] = round(length, 4) if code == CHANNEL_U_CUT else None
    new["reinforcement"] = {
        "strategy": OPENING_REINFORCEMENT_CHANNEL,
        "roles": list(run_record["roles"]),
        "run_id": run_record["run_id"],
        "opening_indices": list(run_record["opening_indices"]),
        "source_codes": source_codes,
        "cut": cut,
        "policy_version": policy["policy_version"],
    }
    return new


def _crossing_row(row, walls_to_create, wall_idx):
    """Linha pseudo-peca que representa a canaleta passando sobre o trecho
    do no' ocupado pela amarracao transversal `row` (parede que chega)."""
    p0, _p1, wall_dir, _len_ft, thickness_ft = _wall_axis_and_length(walls_to_create, wall_idx)
    tie = row["cand"]
    center = p0 + wall_dir * _cm_to_ft((row["lo"] + row["hi"]) / 2.0)
    origin = XYZ(center.X, center.Y, tie["origin_world"].Z)
    pseudo = {
        "logical_code": CROSSING_CODE, "course": tie.get("course"), "origin_world": origin,
        "x_dir": wall_dir, "y_dir": XYZ(-wall_dir.Y, wall_dir.X, 0.0),
        "length_cm": row["hi"] - row["lo"], "width_cm": _ft_to_cm(thickness_ft), "cells_world": [],
        "placement_reason": "CHANNEL_NODE_CROSSING", "node_index": tie.get("node_index"),
        "wall_idx": wall_idx, "secondary_wall_idx": tie.get("wall_idx"),
        "rotation_deg": tie.get("rotation_deg"),
    }
    return {"cand": pseudo, "lo": row["lo"], "hi": row["hi"], "along": True, "eligible": True,
            "tie": False, "crossing_of": tie}


def _incoming_abutment_piece(tie, walls_to_create, main_wall_idx, catalog, policy):
    """Peca que substitui a amarracao da parede que chega quando a canaleta
    atravessa o T: mesma ponta de fora, recuada ate' a face da principal +
    junta. None se nao houver peca de catalogo com o comprimento resultante."""
    incoming_idx = tie.get("wall_idx")
    if incoming_idx is None or catalog is None:
        return None
    main_p0, _mp1, _mdir, _mlen, main_thickness_ft = _wall_axis_and_length(walls_to_create, main_wall_idx)
    ip0, _ip1, idir, _ilen, _ith = _wall_axis_and_length(walls_to_create, incoming_idx)
    lo, hi = _candidate_t_range_on_wall(tie, ip0, idir)
    # t (na parede que chega) do eixo da principal.
    t_main = _ft_to_cm((main_p0 - ip0).DotProduct(idir))
    new_len = (hi - lo) - _ft_to_cm(main_thickness_ft) - policy["course_joint_cm"]
    code = None
    for c in sorted(catalog):
        entry = catalog[c]
        if abs((entry.get("length_cm") or 0.0) - new_len) <= 0.05 and not entry.get("is_special_bond"):
            code = c
            break
    if code is None:
        return None
    if abs(lo - t_main) <= abs(hi - t_main):
        new_lo, new_hi = hi - new_len, hi
    else:
        new_lo, new_hi = lo, lo + new_len
    shift = _cm_to_ft((new_lo + new_hi) / 2.0 - (lo + hi) / 2.0)
    origin = tie["origin_world"] + idir * shift
    return _make_block_candidate(code, catalog[code], tie.get("course"), origin, tie["x_dir"],
                                 CROSSING_ABUTMENT_REASON, node_index=tie.get("node_index"),
                                 wall_idx=incoming_idx, secondary_wall_idx=main_wall_idx)


def _row_joints_cm(rows, gap_cm):
    joints = []
    for a, b in zip(rows, rows[1:]):
        if 0.0 <= b["lo"] - a["hi"] <= gap_cm:
            joints.append((a["hi"] + b["lo"]) / 2.0)
    return joints


def _tie_split_rows(row, walls_to_create, wall_idx, adjacent_joints, policy):
    """Divide a amarracao ao longo `row` (B54) em duas pseudo-linhas de
    canaleta. None se nenhuma divisao respeita o desencontro minimo."""
    p0, _p1, wall_dir, _len_ft, _th = _wall_axis_and_length(walls_to_create, wall_idx)
    joint = policy["course_joint_cm"]
    total = row["hi"] - row["lo"]
    best = None
    for l1 in policy["tie_split_lengths_cm"]:
        l2 = total - l1 - joint
        if l2 < min(policy["tie_split_lengths_cm"]) - 0.05 or l2 > policy["max_channel_length_cm"] + 0.05:
            continue
        j = row["lo"] + l1 + joint / 2.0
        stagger = min([abs(j - a) for a in adjacent_joints] or [1e9])
        if stagger < policy["tie_split_min_stagger_cm"]:
            continue
        key = (round(stagger, 3), round(min(l1, l2), 3), l1)
        if best is None or key > best[0]:
            best = (key, l1, l2)
    if best is None:
        return None
    _key, l1, l2 = best
    tie = row["cand"]
    old_center_t = (tie["origin_world"] - p0).DotProduct(wall_dir)
    parts = []
    for lo, hi in ((row["lo"], row["lo"] + l1), (row["hi"] - l2, row["hi"])):
        cand = dict(tie)
        cand["logical_code"] = TIE_SPLIT_CODE
        cand["length_cm"] = hi - lo
        cand["cells_world"] = []
        cand["origin_world"] = tie["origin_world"] + wall_dir * (_cm_to_ft((lo + hi) / 2.0) - old_center_t)
        parts.append({"cand": cand, "lo": lo, "hi": hi, "along": True, "eligible": True, "tie": False,
                      "split_of": tie})
    return parts


def plan_channel_reinforcement(course_candidates, walls_to_create, openings_per_wall, course_band,
                               num_courses, base_z_abs, policy=None, nodes=None, catalog=None):
    """Planeja CHANNEL sobre fiadas fisicas ja' resolvidas.

    `course_candidates`: {course_index: [candidato]} (NAO e' mutado).
    `course_band(ci) -> (z_lo_ft, z_hi_ft)`: faixa ocupada pela fiada fisica.
    `openings_per_wall[wi]`: [(t_lo_ft, t_hi_ft, sill_z_abs_ft, head_z_abs_ft)].
    `nodes` (grafo de encontros) habilita a deteccao de passagem livre pela
    distancia jamba -> no'; `catalog` (codigo -> entrada com length_cm e
    cells_local) habilita a travessia de T.

    Devolve {"course_candidates": novo dict (listas novas, dicts trocados so'
    onde houve reforco), "runs", "openings", "findings", "free_to_top",
    "policy"}. Deterministico: ordem por parede, fiada e eixo."""
    policy = channel_policy(policy)
    tol_ft = _cm_to_ft(policy["grid_tolerance_cm"])
    joint_ft = _cm_to_ft(policy["grid_joint_allowance_cm"])
    out_cc = dict((ci, list(course_candidates.get(ci) or [])) for ci in range(num_courses))
    crossings = []
    tie_conversions = []
    runs = []
    openings_report = []
    findings = []
    free_to_top = []
    top_z = course_band(num_courses - 1)[1] if num_courses > 0 else None

    for wall_idx in range(len(walls_to_create)):
        openings = list(openings_per_wall[wall_idx] if wall_idx < len(openings_per_wall) else [])
        if not openings:
            continue
        demands = {}   # course_index -> [(opening_index, role)]
        removals = {}  # course_index -> [(t_lo_cm, t_hi_cm)]
        for oi, opening in enumerate(openings):
            t_lo, t_hi, sill_z, head_z = opening
            rec = {"wall_idx": wall_idx, "opening_index": oi,
                   "t_lo_cm": round(_ft_to_cm(t_lo), 3), "t_hi_cm": round(_ft_to_cm(t_hi), 3),
                   "sill_rel_cm": round(_ft_to_cm(sill_z - base_z_abs), 3),
                   "head_rel_cm": round(_ft_to_cm(head_z - base_z_abs), 3),
                   "has_sill": (sill_z - base_z_abs) > tol_ft,
                   "above": None, "below": None}
            # ---- acima
            above_ci = _course_for_head(head_z, course_band, num_courses, tol_ft, joint_ft)
            if top_z is not None and head_z >= top_z - tol_ft:
                rec["above"] = {"status": "REACHES_WALL_TOP"}
            elif above_ci is None:
                rec["above"] = {"status": "HEAD_OFF_GRID"}
                findings.append({"code": "CHANNEL_HEAD_OFF_GRID", "severity": SEVERITY_WARNING,
                                 "classification": "NEEDS_RULE", "wall_idx": wall_idx, "opening_index": oi,
                                 "detail": "topo do vao fora da grade de fiadas; nenhuma canaleta superior planejada"})
            else:
                bounded = False
                if policy.get("free_to_top_tie_bounded_passages") and not rec["has_sill"] and nodes:
                    max_cm = policy["tie_bounded_max_jamb_to_node_cm"]
                    bounded = (_jamb_node_bounded(walls_to_create, nodes, wall_idx, opening, -1, max_cm) and
                               _jamb_node_bounded(walls_to_create, nodes, wall_idx, opening, +1, max_cm))
                elif policy.get("free_to_top_tie_bounded_passages") and not rec["has_sill"]:
                    gap_cm = policy["tie_bounded_gap_cm"]
                    bounded = (_jamb_tie_bounded(course_candidates, walls_to_create, wall_idx, opening,
                                                 course_band, num_courses, -1, gap_cm, tol_ft) and
                               _jamb_tie_bounded(course_candidates, walls_to_create, wall_idx, opening,
                                                 course_band, num_courses, +1, gap_cm, tol_ft))
                if bounded:
                    rec["above"] = {"status": "FREE_TO_TOP", "course_index": above_ci}
                    for ci in range(above_ci, num_courses):
                        removals.setdefault(ci, []).append((_ft_to_cm(t_lo), _ft_to_cm(t_hi)))
                    free_to_top.append({"wall_idx": wall_idx, "opening_index": oi, "from_course": above_ci})
                else:
                    rec["above"] = {"status": "PLANNED", "course_index": above_ci}
                    demands.setdefault(above_ci, []).append((oi, ROLE_ABOVE_OPENING))
            # ---- abaixo
            if rec["has_sill"]:
                below_ci = _course_for_sill(sill_z, course_band, num_courses, tol_ft, joint_ft)
                if below_ci is None:
                    rec["below"] = {"status": "SILL_OFF_GRID"}
                    findings.append({"code": "CHANNEL_SILL_OFF_GRID", "severity": SEVERITY_WARNING,
                                     "classification": "NEEDS_RULE", "wall_idx": wall_idx, "opening_index": oi,
                                     "detail": "peitoril fora da grade de fiadas; nenhuma canaleta inferior planejada"})
                else:
                    rec["below"] = {"status": "PLANNED", "course_index": below_ci}
                    demands.setdefault(below_ci, []).append((oi, ROLE_BELOW_SILL))
            openings_report.append(rec)

        # ---- remocao das pecas acima de passagem livre (antes das corridas)
        for ci in sorted(removals):
            spans = removals[ci]
            rows = _wall_strip_pieces(out_cc[ci], walls_to_create, wall_idx)
            drop = set()
            for r in rows:
                if r["tie"] or not r["along"]:
                    continue
                if any(r["hi"] > lo + 0.5 and r["lo"] < hi - 0.5 for lo, hi in spans):
                    drop.add(id(r["cand"]))
            if drop:
                out_cc[ci] = [c for c in out_cc[ci] if id(c) not in drop]
                for item in free_to_top:
                    if item["wall_idx"] == wall_idx:
                        item.setdefault("removed_by_course", {})[ci] = len(drop)

        # ---- corridas por fiada
        for ci in sorted(demands):
            rows = _wall_strip_pieces(out_cc[ci], walls_to_create, wall_idx)
            spans = []  # (i0, i1, opening_index, role, info)
            for oi, role in sorted(demands[ci]):
                opening = openings[oi]
                t_lo = _ft_to_cm(opening[0])
                t_hi = _ft_to_cm(opening[1])
                side_key = "above" if role == ROLE_ABOVE_OPENING else "below"
                rec = [r for r in openings_report if r["wall_idx"] == wall_idx and r["opening_index"] == oi][0]

                def _adjacent_joints(ci=ci):
                    found = []
                    for cj in (ci - 1, ci + 1):
                        if 0 <= cj < num_courses:
                            found.extend(_row_joints_cm(_wall_strip_pieces(out_cc[cj], walls_to_create, wall_idx),
                                                        policy["contiguous_gap_cm"]))
                    return found

                def _convert_along_tie(j, rows=rows, ci=ci):
                    """0 = nao converteu; 1 = mesma geometria; 2 = B54 dividido."""
                    row = rows[j]
                    tie = row["cand"]
                    if not policy.get("convert_blocking_along_ties") or not row["along"] or not row["tie"]:
                        return 0
                    code = tie.get("logical_code")
                    if code in COMMON_TO_CHANNEL or code in COMPENSATOR_CODES:
                        new_rows = [dict(row, eligible=True, tie=False, converted_tie=True)]
                    elif code == "B54":
                        new_rows = _tie_split_rows(row, walls_to_create, wall_idx, _adjacent_joints(), policy)
                        if new_rows is None:
                            findings.append({"code": "CHANNEL_TIE_SPLIT_NO_STAGGER", "severity": SEVERITY_WARNING,
                                             "classification": "NEEDS_RULE", "wall_idx": wall_idx,
                                             "course_index": ci, "lo_cm": round(row["lo"], 3),
                                             "detail": "B54 de no' sem divisao com desencontro minimo"})
                            return 0
                    else:
                        return 0
                    rows[j:j + 1] = new_rows
                    tie_conversions.append({"course_index": ci, "wall_idx": wall_idx,
                                            "node_index": tie.get("node_index"), "removed": tie,
                                            "mode": "SPLIT" if len(new_rows) == 2 else "SAME_GEOMETRY",
                                            "code": code, "lo_cm": round(row["lo"], 3),
                                            "hi_cm": round(row["hi"], 3),
                                            "parts_cm": [[round(r["lo"], 3), round(r["hi"], 3)] for r in new_rows]})
                    return len(new_rows)

                k = 0
                while k < len(rows):
                    r = rows[k]
                    if r["tie"] and r["along"] and r["hi"] > t_lo + 0.5 and r["lo"] < t_hi - 0.5:
                        k += max(1, _convert_along_tie(k))
                    else:
                        k += 1
                hits = [i for i, r in enumerate(rows) if r["hi"] > t_lo + 0.5 and r["lo"] < t_hi - 0.5]
                problem = None
                if not hits:
                    problem = "NO_PIECES_OVER_SPAN"
                else:
                    if any(rows[i]["tie"] for i in hits):
                        problem = "TIE_OVER_SPAN"
                    elif any(not rows[i]["eligible"] for i in hits):
                        problem = "INELIGIBLE_PIECE_OVER_SPAN"
                    # A junta de 1 cm pode cair exatamente sobre a jamba.
                    edge = policy["contiguous_gap_cm"]
                    covered = rows[hits[0]]["lo"] <= t_lo + edge and rows[hits[-1]]["hi"] >= t_hi - edge
                    for a, b in zip(hits, hits[1:]):
                        if rows[b]["lo"] - rows[a]["hi"] > policy["contiguous_gap_cm"]:
                            covered = False
                    if not covered and problem is None:
                        problem = "SPAN_NOT_COVERED"
                if problem is not None:
                    rec[side_key] = {"status": "MISSING", "course_index": ci, "reason": problem}
                    findings.append({"code": "MISSING_REQUIRED_CHANNEL", "severity": SEVERITY_ERROR,
                                     "classification": ("NEEDS_RULE" if problem == "TIE_OVER_SPAN"
                                                        else "ACTUAL_ERROR"),
                                     "wall_idx": wall_idx, "opening_index": oi,
                                     "course_index": ci, "role": role, "detail": problem})
                    continue
                def _cross(j, support_cm, rows=rows, ci=ci):
                    row = rows[j]
                    tie = row["cand"]
                    if support_cm > policy["cross_tee_when_support_at_most_cm"] + 1e-6:
                        return 0
                    if row["along"]:
                        return _convert_along_tie(j)
                    if not str(tie.get("placement_reason") or "").startswith(
                            "T_INTERSECTION_INCOMING"):
                        return False
                    if tie.get("secondary_wall_idx") != wall_idx:
                        return 0
                    abut = _incoming_abutment_piece(tie, walls_to_create, wall_idx, catalog, policy)
                    if abut is None:
                        findings.append({"code": "CHANNEL_CROSSING_NO_ABUTMENT_PIECE",
                                         "severity": SEVERITY_WARNING, "classification": "MISSING_CATALOG",
                                         "wall_idx": wall_idx, "course_index": ci,
                                         "detail": "sem peca de catalogo para recuar a amarracao da parede que chega"})
                        return 0
                    rows[j] = _crossing_row(row, walls_to_create, wall_idx)
                    crossings.append({"course_index": ci, "main_wall_idx": wall_idx,
                                      "incoming_wall_idx": tie.get("wall_idx"), "node_index": tie.get("node_index"),
                                      "removed": tie, "added": abut,
                                      "lo_cm": round(row["lo"], 3), "hi_cm": round(row["hi"], 3)})
                    return 1

                i0, i1, lim_l, lim_r = _extend_run(rows, hits[0], hits[-1], t_lo, t_hi, policy, cross=_cross)
                # por IDENTIDADE da linha: conversoes de demandas seguintes
                # podem inserir linhas e deslocar indices.
                spans.append([rows[i0], rows[i1], oi, role, lim_l, lim_r])
            if not spans:
                continue

            def _index_of(row_obj, rows=rows):
                for k, r in enumerate(rows):
                    if r is row_obj:
                        return k
                raise ValueError("linha da corrida perdida")

            spans = sorted([[_index_of(sp[0]), _index_of(sp[1])] + sp[2:] for sp in spans])
            merged = []
            for sp in spans:
                if merged and sp[0] <= merged[-1]["i1"] + 1:
                    cur = merged[-1]
                    cur["i1"] = max(cur["i1"], sp[1])
                    cur["items"].append(sp)
                else:
                    merged.append({"i0": sp[0], "i1": sp[1], "items": [sp]})
            replacements = {}
            for run in merged:
                members = rows[run["i0"]:run["i1"] + 1]
                lo = members[0]["lo"]
                hi = members[-1]["hi"]
                run_id = "W{}:C{}:{:.1f}-{:.1f}".format(wall_idx, ci, lo, hi)
                roles = sorted(set(sp[3] for sp in run["items"]))
                record = {"run_id": run_id, "wall_idx": wall_idx, "course_index": ci,
                          "lo_cm": round(lo, 3), "hi_cm": round(hi, 3), "roles": roles,
                          "opening_indices": sorted(set(sp[2] for sp in run["items"])), "pieces": []}
                groups = _group_run_members(members, policy)
                new_pieces = [_channel_candidate_from_group(g, walls_to_create, wall_idx, record, policy)
                              for g in groups]
                for g, piece in zip(groups, new_pieces):
                    record["pieces"].append({"code": piece["logical_code"],
                                             "lo_cm": round(g[0]["lo"], 3), "hi_cm": round(g[-1]["hi"], 3),
                                             "source_codes": piece["reinforcement"]["source_codes"]})
                    if piece["logical_code"] == CHANNEL_U_CUT and \
                            piece["instance_length_cm"] < policy["observed_min_cut_length_cm"] - 1e-6:
                        findings.append({"code": "CHANNEL_CUT_BELOW_OBSERVED_MIN", "severity": SEVERITY_WARNING,
                                         "classification": "NEEDS_RULE", "wall_idx": wall_idx,
                                         "course_index": ci, "run_id": run_id,
                                         "detail": "canaleta cortada de {:.1f} cm (< {:.1f} cm observado)".format(
                                             piece["instance_length_cm"], policy["observed_min_cut_length_cm"])})
                    for src in g:
                        replacements[id(src["cand"])] = (id(g[0]["cand"]), piece)
                for sp in run["items"]:
                    oi, role, lim_l, lim_r = sp[2], sp[3], sp[4], sp[5]
                    opening = openings[oi]
                    t_lo = _ft_to_cm(opening[0])
                    t_hi = _ft_to_cm(opening[1])
                    support_l = round(t_lo - rows[sp[0]]["lo"], 3)
                    support_r = round(rows[sp[1]]["hi"] - t_hi, 3)
                    side_key = "above" if role == ROLE_ABOVE_OPENING else "below"
                    rec = [r for r in openings_report if r["wall_idx"] == wall_idx and r["opening_index"] == oi][0]
                    rec[side_key] = {"status": "CHANNEL", "course_index": ci, "run_id": run_id,
                                     "support_l_cm": support_l, "support_r_cm": support_r,
                                     "limited_l": lim_l, "limited_r": lim_r}
                    for side, sup, lim in (("L", support_l, lim_l), ("R", support_r, lim_r)):
                        if sup < policy["min_support_cm"] - 1e-6:
                            findings.append({"code": "CHANNEL_SUPPORT_LIMITED", "severity": SEVERITY_WARNING,
                                             "classification": "VALID_ALTERNATIVE" if sup > 0 else "ACTUAL_ERROR",
                                             "wall_idx": wall_idx, "opening_index": oi, "course_index": ci,
                                             "role": role, "side": side, "support_cm": sup, "limited_by": lim})
                runs.append(record)
            crossed = dict((id(x["removed"]), x) for x in crossings
                           if x["course_index"] == ci and x["main_wall_idx"] == wall_idx)
            split_removed = set(id(x["removed"]) for x in tie_conversions
                                if x["course_index"] == ci and x["wall_idx"] == wall_idx and x["mode"] == "SPLIT")
            if replacements or crossed:
                present = set(id(c) for c in out_cc[ci])
                rebuilt = []
                for cand in out_cc[ci]:
                    if id(cand) in split_removed:
                        continue
                    if id(cand) in crossed:
                        rebuilt.append(crossed[id(cand)]["added"])
                        continue
                    rep = replacements.get(id(cand))
                    if rep is None:
                        rebuilt.append(cand)
                    elif rep[0] == id(cand):
                        rebuilt.append(rep[1])
                # grupos cuja primeira peca e' o trecho atravessado (pseudo,
                # nao existe na fiada original)
                seen = set()
                for key in sorted(replacements, key=lambda k: replacements[k][1]["reinforcement"]["run_id"]):
                    head_id, piece = replacements[key]
                    if head_id not in present and id(piece) not in seen:
                        seen.add(id(piece))
                        rebuilt.append(piece)
                out_cc[ci] = rebuilt

    for x in crossings:
        x["removed_code"] = x.pop("removed").get("logical_code")
        x["added_code"] = x.pop("added").get("logical_code")
    for x in tie_conversions:
        x.pop("removed")
    return {"strategy": OPENING_REINFORCEMENT_CHANNEL, "policy": policy, "course_candidates": out_cc,
            "runs": runs, "openings": openings_report, "findings": findings, "free_to_top": free_to_top,
            "node_crossings": crossings, "tie_conversions": tie_conversions}


def validate_channel_reinforcement(course_candidates, walls_to_create, openings_per_wall, course_band,
                                   num_courses, base_z_abs, free_to_top=None, policy=None):
    """Validador INDEPENDENTE do planejador (recalcula a demanda a partir das
    aberturas e confere as pecas). Devolve {"counts": {...}, "items": [...]}.

    MISSING_REQUIRED_CHANNEL / EXTRA_CHANNEL / CHANNEL_WRONG_COURSE /
    CHANNEL_INVADES_OPENING / CHANNEL_COLLISION / CHANNEL_SUPPORT_BELOW_POLICY."""
    policy = channel_policy(policy)
    tol_ft = _cm_to_ft(policy["grid_tolerance_cm"])
    joint_ft = _cm_to_ft(policy["grid_joint_allowance_cm"])
    gap = policy["contiguous_gap_cm"]
    exempt = set((f["wall_idx"], f["opening_index"]) for f in (free_to_top or []))
    counts = {"MISSING_REQUIRED_CHANNEL": 0, "EXTRA_CHANNEL": 0, "CHANNEL_WRONG_COURSE": 0,
              "CHANNEL_INVADES_OPENING": 0, "CHANNEL_COLLISION": 0, "CHANNEL_SUPPORT_BELOW_POLICY": 0,
              "channel_top_expected": 0, "channel_top_matched": 0,
              "channel_bottom_expected": 0, "channel_bottom_matched": 0, "channel_pieces": 0,
              "channel_cut_pieces": 0}
    items = []
    top_z = course_band(num_courses - 1)[1] if num_courses > 0 else None
    demand_courses = {}  # wall_idx -> {course: [(t_lo, t_hi, role, oi)]}
    for wi in range(len(walls_to_create)):
        for oi, opening in enumerate(openings_per_wall[wi] if wi < len(openings_per_wall) else []):
            t_lo, t_hi, sill_z, head_z = opening
            span = (_ft_to_cm(t_lo), _ft_to_cm(t_hi))
            if (wi, oi) not in exempt and not (top_z is not None and head_z >= top_z - tol_ft):
                ci = _course_for_head(head_z, course_band, num_courses, tol_ft, joint_ft)
                if ci is not None:
                    demand_courses.setdefault(wi, {}).setdefault(ci, []).append(span + (ROLE_ABOVE_OPENING, oi))
            if (sill_z - base_z_abs) > tol_ft:
                ci = _course_for_sill(sill_z, course_band, num_courses, tol_ft, joint_ft)
                if ci is not None:
                    demand_courses.setdefault(wi, {}).setdefault(ci, []).append(span + (ROLE_BELOW_SILL, oi))

    for ci in range(num_courses):
        pieces = course_candidates.get(ci) or []
        z_lo, z_hi = course_band(ci)
        channel_ids = set(id(c) for c in pieces if is_channel_code(c.get("logical_code")))
        counts["channel_pieces"] += len(channel_ids)
        counts["channel_cut_pieces"] += sum(1 for c in pieces if c.get("logical_code") == CHANNEL_U_CUT)
        for wi in range(len(walls_to_create)):
            rows = _wall_strip_pieces(pieces, walls_to_create, wi)
            along_channel = [r for r in rows if r["along"] and is_channel_code(r["cand"].get("logical_code"))
                             and r["cand"].get("wall_idx") == wi]
            demands = demand_courses.get(wi, {}).get(ci, [])
            # invasao de vao ativo nesta fiada
            for r in along_channel:
                for oi, opening in enumerate(openings_per_wall[wi]):
                    if not _opening_active(opening, z_lo, z_hi, tol_ft):
                        continue
                    if r["hi"] > _ft_to_cm(opening[0]) + 0.5 and r["lo"] < _ft_to_cm(opening[1]) - 0.5:
                        counts["CHANNEL_INVADES_OPENING"] += 1
                        items.append({"code": "CHANNEL_INVADES_OPENING", "wall_idx": wi, "course_index": ci,
                                      "opening_index": oi, "lo_cm": r["lo"], "hi_cm": r["hi"]})
            # demanda atendida?
            for t_lo, t_hi, role, oi in demands:
                key = "channel_top" if role == ROLE_ABOVE_OPENING else "channel_bottom"
                counts[key + "_expected"] += 1
                over = [r for r in rows if r["hi"] > t_lo + 0.5 and r["lo"] < t_hi - 0.5]
                ok = bool(over) and all(r["along"] and is_channel_code(r["cand"].get("logical_code"))
                                        for r in over)
                if ok:
                    ok = over[0]["lo"] <= t_lo + gap and over[-1]["hi"] >= t_hi - gap and all(
                        b["lo"] - a["hi"] <= gap for a, b in zip(over, over[1:]))
                if ok:
                    counts[key + "_matched"] += 1
                    # apoio medido na corrida contigua de canaletas
                    idx = [i for i, r in enumerate(rows) if r in over]
                    i0, i1 = idx[0], idx[-1]
                    while i0 - 1 >= 0 and rows[i0 - 1]["along"] and is_channel_code(
                            rows[i0 - 1]["cand"].get("logical_code")) and rows[i0]["lo"] - rows[i0 - 1]["hi"] <= gap:
                        i0 -= 1
                    while i1 + 1 < len(rows) and rows[i1 + 1]["along"] and is_channel_code(
                            rows[i1 + 1]["cand"].get("logical_code")) and rows[i1 + 1]["lo"] - rows[i1]["hi"] <= gap:
                        i1 += 1
                    for side, sup in (("L", t_lo - rows[i0]["lo"]), ("R", rows[i1]["hi"] - t_hi)):
                        if sup < policy["min_support_cm"] - 1e-6:
                            counts["CHANNEL_SUPPORT_BELOW_POLICY"] += 1
                            items.append({"code": "CHANNEL_SUPPORT_BELOW_POLICY", "wall_idx": wi,
                                          "course_index": ci, "opening_index": oi, "role": role,
                                          "side": side, "support_cm": round(sup, 3)})
                else:
                    counts["MISSING_REQUIRED_CHANNEL"] += 1
                    items.append({"code": "MISSING_REQUIRED_CHANNEL", "wall_idx": wi, "course_index": ci,
                                  "opening_index": oi, "role": role})
            # canaleta sem demanda
            for r in along_channel:
                if not demands:
                    counts["CHANNEL_WRONG_COURSE"] += 1
                    items.append({"code": "CHANNEL_WRONG_COURSE", "wall_idx": wi, "course_index": ci,
                                  "lo_cm": r["lo"], "hi_cm": r["hi"]})
                    continue
            if demands and along_channel:
                # componentes contiguas de canaleta que nao cobrem vao nenhum
                comps = []
                for r in along_channel:
                    if comps and r["lo"] - comps[-1][-1]["hi"] <= gap:
                        comps[-1].append(r)
                    else:
                        comps.append([r])
                for comp in comps:
                    lo, hi = comp[0]["lo"], comp[-1]["hi"]
                    if not any(hi > t_lo + 0.5 and lo < t_hi - 0.5 for t_lo, t_hi, _r, _o in demands):
                        counts["EXTRA_CHANNEL"] += len(comp)
                        items.append({"code": "EXTRA_CHANNEL", "wall_idx": wi, "course_index": ci,
                                      "lo_cm": lo, "hi_cm": hi, "pieces": len(comp)})
        # colisao envolvendo canaleta (mesma fiada)
        if channel_ids:
            boxes = [_candidate_obb(c) for c in pieces]
            aabbs = [_obb_aabb(b) for b in boxes]
            for i, j in sorted(_collision_candidate_pairs(range(len(pieces)), aabbs, 0.0)):
                if id(pieces[i]) not in channel_ids and id(pieces[j]) not in channel_ids:
                    continue
                if _obb_min_overlap(boxes[i], boxes[j]) > BOND_COLLISION_EPS_FT:
                    counts["CHANNEL_COLLISION"] += 1
                    items.append({"code": "CHANNEL_COLLISION", "course_index": ci,
                                  "a": pieces[i].get("logical_code"), "b": pieces[j].get("logical_code")})
    return {"counts": counts, "items": items}
