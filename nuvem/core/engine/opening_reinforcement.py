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
# Mecanismo aprovado pelo usuario (2026-09-14, regra 51.6): corrida de canaleta
# que atravessa o T quando o apoio efetivo seria <= 0. Classificacao PROPRIA -
# nao e' excecao generica do auditor de junta.
CHANNEL_THROUGH_T_PATTERN = "CHANNEL_THROUGH_T_SUPPORTED_PATTERN"
# Parte de um B54 de no' dividido em duas canaletas (ver _tie_split_rows).
TIE_SPLIT_CODE = "TIE_SPLIT"
STANDARD_CHANNEL_BY_LENGTH = ((39.0, CHANNEL_U_39), (34.0, CHANNEL_U_34), (19.0, CHANNEL_U_19))

TIE_REASON_PREFIXES = ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION", "CORNER")
# REGRA 76.1: o compensador que fecha um no' sem amarracao valida
# (wall_stepper.JUNCTION_UNRESOLVED_FILL_REASON) deixou de ser DESIGNADO
# amarracao, mas continua OCUPANDO a posicao do no': a canaleta nunca o absorve,
# nunca passa por cima dele e a corrida para nele - exatamente como antes da
# 76.1. Nenhuma regra nova de canaleta.
NODE_POSITION_FILL_REASONS = ("JUNCTION_UNRESOLVED_FILL",)

SEVERITY_ERROR = "ERROR"
SEVERITY_WARNING = "WARNING"
SEVERITY_INFO = "INFO"

# Ruido de ponto flutuante na comparacao de folga entre pecas contiguas.
CONTIGUOUS_GAP_EPSILON_CM = 1e-6

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
    # Folga maxima entre duas pecas CONTIGUAS da mesma corrida: junta de 1 cm
    # + ate' 1 cm da folga residual que a regra 30.8 distribui numa junta de
    # contorno de trecho entre nos (2026-09-14; antes 1,5 - a junta de 1,5 cm
    # do anel do vao 7719511 caia fora por ruido de ponto flutuante e a de
    # 2,0 cm das paredes de 86 cm quebrava a corrida).
    "contiguous_gap_cm": 2.0,
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
    #
    # REGRA 75 (2026-09-18, revisao visual humana): canaleta NUNCA exerce funcao
    # de amarracao em nenhum no' (L, T ou X). A conversao acima trocava a PECA DE
    # AMARRACAO por canaleta preservando so' a geometria - foi exatamente o que a
    # revisao reprovou (U34 no canto do no' 48, 8284584 x 8284590). DESLIGADA por
    # padrao: o conflito corrida x amarracao passa a ser CLASSIFICADO
    # (TIE_OVER_SPAN -> MISSING_REQUIRED_CHANNEL, NEEDS_RULE) e a amarracao fica.
    "convert_blocking_along_ties": False,
    # Limite de apoio para converter a amarracao AO LONGO que bloqueia a
    # corrida (topologia do no' preservada). BUTANTA 1o PAV: humano passa por
    # cima do no' com apoio que seria 4 cm (6627438, K34 sobre o no') e para
    # na amarracao com 14 cm (6620076, 6621711). PADRAO OBSERVADO (3 casos).
    "convert_along_tie_when_support_below_cm": 9.0,
    "tie_split_lengths_cm": (39.0, 34.0, 29.0, 24.0, 19.0, 14.0, 9.0),
    "tie_split_min_stagger_cm": 1.5,
    # REGRA 75 (2026-09-18): a travessia do T da regra 51.6 REMOVE o corpo do
    # B34 da parede que chega sobre o no' (recuado para peca de encosto) - isso
    # e' substituir amarracao por canaleta, o que a regra 75 proibe. SUSPENSA
    # por padrao; a evidencia humana da 51.6 (KV sobre o no' em jamba na face)
    # fica registrada e a reativacao e' decisao de usuario, nunca do solver.
    "channel_may_cross_node_tie": False,
}


def channel_policy(overrides=None):
    policy = dict(DEFAULT_CHANNEL_POLICY)
    for key, value in (overrides or {}).items():
        policy[key] = value
    return policy


def is_channel_code(code):
    return code in CHANNEL_LOGICAL_TYPES


def _is_tie(candidate):
    """Peca que ocupa a posicao do no': amarracao (qualquer variacao) ou o
    compensador de no' nao resolvido (regra 76.1)."""
    reason = str(candidate.get("placement_reason") or "")
    return reason in NODE_POSITION_FILL_REASONS or any(reason.startswith(p) for p in TIE_REASON_PREFIXES)


def channel_as_junction_bond(course_candidates, report=None):
    """REGRA 75 - hard gate CHANNEL_AS_JUNCTION_BOND: nenhuma canaleta pode
    exercer funcao de amarracao em encontro L, T ou X.

    Deteccao por FUNCAO, nunca por distancia (uma canaleta pode passar rente a
    um no' legitimamente):
      1. peca final com codigo de canaleta carregando razao de peca de no'
         (L_CORNER/T_INTERSECTION/X_INTERSECTION/CORNER) ou marcada como
         amarracao convertida;
      2. peca de travessia sobre o no' (CHANNEL_NODE_CROSSING / NODE_CROSSING);
      3. registro de conversao de amarracao (tie_conversions) ou de travessia
         (node_crossings) no laudo do reforco.

    Devolve a lista de violacoes; o resultado aceitavel e' SEMPRE lista vazia.
    """
    violations = []
    canal = set(CHANNEL_LOGICAL_TYPES) | set([TIE_SPLIT_CODE, CROSSING_CODE])
    for ci in sorted(course_candidates or {}):
        for cand in (course_candidates or {}).get(ci) or []:
            code = cand.get("logical_code")
            reason = str(cand.get("placement_reason") or "")
            if code not in canal:
                continue
            if _is_tie(cand) or cand.get("converted_tie") or reason == "CHANNEL_NODE_CROSSING":
                violations.append({"kind": "CHANNEL_PIECE_WITH_TIE_ROLE", "course_index": ci,
                                   "logical_code": code, "placement_reason": reason,
                                   "wall_idx": cand.get("wall_idx"),
                                   "node_index": cand.get("node_index")})
    rep = report or {}
    for x in rep.get("tie_conversions") or []:
        violations.append({"kind": "TIE_CONVERTED_TO_CHANNEL", "course_index": x.get("course_index"),
                           "logical_code": x.get("code"), "mode": x.get("mode"),
                           "wall_idx": x.get("wall_idx"), "node_index": x.get("node_index")})
    for x in rep.get("node_crossings") or []:
        violations.append({"kind": "CHANNEL_CROSSED_NODE_TIE", "course_index": x.get("course_index"),
                           "wall_idx": x.get("main_wall_idx"),
                           "incoming_wall_idx": x.get("incoming_wall_idx"),
                           "node_index": x.get("node_index")})
    return violations


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


def _physical_key(candidate):
    """Chave CANONICA e fisica de uma peca numa fiada (auditoria 2026-09-14:
    nada de `id()` nem ordem de dict no contrato - o Revit roda IronPython).
    Duas pecas com a mesma chave na mesma fiada ocupariam o mesmo volume."""
    o = candidate["origin_world"]
    x_dir = candidate.get("x_dir")
    direction = "%.4f,%.4f" % (x_dir.X, x_dir.Y) if x_dir is not None else "-"
    return "%s|%s|%s|%.5f|%.5f|%.5f|%.4f|%s|%s" % (
        candidate.get("logical_code"), candidate.get("wall_idx"), candidate.get("secondary_wall_idx"),
        o.X, o.Y, o.Z, candidate.get("length_cm") or 0.0, direction, candidate.get("placement_reason") or "")


def course_wall_buckets(course_candidates):
    """{course_index: {wall_idx: [pecas]}} com cada peca listada sob `wall_idx` e
    `secondary_wall_idx`, na ORDEM original da fiada. `_wall_strip_pieces`
    sobre o balde devolve exatamente o mesmo que sobre a fiada inteira (ela ja'
    filtra por essas duas chaves e ordena) - so' evita varrer a fiada toda a
    cada parede (desempenho, 2026-09-14)."""
    out = {}
    for ci in sorted(course_candidates or {}):
        by_wall = {}
        for cand in course_candidates.get(ci) or []:
            for key in (cand.get("wall_idx"), cand.get("secondary_wall_idx")):
                if key is None:
                    continue
                bucket = by_wall.setdefault(key, [])
                if not bucket or bucket[-1] is not cand:
                    bucket.append(cand)
        out[ci] = by_wall
    return out


def _bucket(buckets, ci, wall_idx):
    return (buckets.get(ci) or {}).get(wall_idx) or []


def cached_strip_rows(cache, tag, buckets, ci, wall_idx, walls_to_create):
    """Linhas de `_wall_strip_pieces` para (fiada, parede) calculadas UMA vez por
    fonte (`tag`) dentro de uma avaliacao - chave deterministica (tag, fiada,
    parede); o conjunto de pecas de uma fonte nao muda durante a avaliacao."""
    if cache is None:
        return _wall_strip_pieces(_bucket(buckets, ci, wall_idx), walls_to_create, wall_idx)
    key = (tag, ci, wall_idx)
    if key not in cache:
        cache[key] = _wall_strip_pieces(_bucket(buckets, ci, wall_idx), walls_to_create, wall_idx)
    return cache[key]


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
    rows.sort(key=lambda r: (round(r["lo"], 4), round(r["hi"], 4), _physical_key(r["cand"])))
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


def free_to_top_openings(walls_to_create, openings_per_wall, nodes, course_band, num_courses, base_z_abs,
                         policy=None):
    """Passagens livres ate' o topo (51.9), decididas pela GEOMETRIA (vao sem
    peitoril com as duas jambas a <= `tie_bounded_max_jamb_to_node_cm` do eixo
    de um no' L/T/X real), ANTES do solve.

    Correcao P0 da auditoria independente (2026-09-14): a versao anterior
    decidia depois do solve e REMOVIA peca inteira que tocasse o vao nas
    fiadas acima do topo - peca que cruzava a jamba sumia e a parede ficava
    aberta alem das jambas (vao 227-473 aberto 208-488). Agora o chamador
    resolve o motor com o vao estendido ate' o topo (`openings_extended_to_top`)
    e o recorte das jambas e' o MESMO do resto da altura da porta.
    Devolve [{"wall_idx", "opening_index", "from_course"}] em ordem estavel."""
    policy = channel_policy(policy)
    if not policy.get("free_to_top_tie_bounded_passages") or not nodes or num_courses <= 0:
        return []
    tol_ft = _cm_to_ft(policy["grid_tolerance_cm"])
    joint_ft = _cm_to_ft(policy["grid_joint_allowance_cm"])
    top_z = course_band(num_courses - 1)[1]
    max_cm = policy["tie_bounded_max_jamb_to_node_cm"]
    out = []
    for wall_idx in range(len(walls_to_create)):
        openings = openings_per_wall[wall_idx] if wall_idx < len(openings_per_wall) else []
        for oi, opening in enumerate(openings):
            _t_lo, _t_hi, sill_z, head_z = opening
            if (sill_z - base_z_abs) > tol_ft or head_z >= top_z - tol_ft:
                continue
            above_ci = _course_for_head(head_z, course_band, num_courses, tol_ft, joint_ft)
            if above_ci is None:
                continue
            if (_jamb_node_bounded(walls_to_create, nodes, wall_idx, opening, -1, max_cm) and
                    _jamb_node_bounded(walls_to_create, nodes, wall_idx, opening, +1, max_cm)):
                out.append({"wall_idx": wall_idx, "opening_index": oi, "from_course": above_ci})
    return out


def _node_other_wall_thickness_cm(walls_to_create, node, wall_idx):
    involved = set(arm[0] for arm in (node.get("arms") or []) if arm)
    for key in ("main_wall_idx", "incoming_wall_idx", "neighbor_wall_idx"):
        if node.get(key) is not None:
            involved.add(node[key])
    for other in (node.get("crossing_walls") or []):
        if other is not None:
            involved.add(other)
    involved.discard(wall_idx)
    widths = [_ft_to_cm(walls_to_create[w][1]) for w in involved if 0 <= w < len(walls_to_create)]
    return max(widths) if widths else None


def continuous_free_passages(walls_to_create, openings_per_wall, nodes, free_to_top, policy=None):
    """PASSAGEM LIVRE CONTINUA (decisao do usuario 2026-09-14, padrao BUTANTA
    PAR28): duas ou mais passagens livres da MESMA parede, com a mesma fiada de
    topo, encadeadas por um pilar que contem UM unico no' T do qual esta parede
    e' a PRINCIPAL, com as duas jambas do pilar a <= tie_bounded_max_jamb_to_
    node_cm desse no'. Acima do topo o humano deixa aberto de FACE DE NO' A FACE
    DE NO' (nos externos) e nao reconstroi o pilar: a parede que chega no no'
    intermediario termina na face da principal.

    Deteccao so' pela geometria (vaos, nos e espessuras) - nunca por id,
    coordenada ou nome. Passagem livre isolada continua abrindo so' o vao.
    Devolve [{"wall_idx", "opening_indices", "from_course", "region_cm",
    "outer_node_t_cm", "inner": [{"node_t_cm", "incoming_wall_idx",
    "incoming_region_cm"}]}] em ordem estavel."""
    policy = channel_policy(policy)
    max_cm = policy["tie_bounded_max_jamb_to_node_cm"]
    by_wall = {}
    for f in free_to_top or []:
        by_wall.setdefault(f["wall_idx"], []).append(f)
    passages = []
    for wall_idx in sorted(by_wall):
        decisions = sorted(by_wall[wall_idx], key=lambda f: openings_per_wall[wall_idx][f["opening_index"]][0])
        if len(decisions) < 2:
            continue
        junctions = []
        for node, t_ft in _wall_junction_nodes_and_ts_ft(walls_to_create, nodes, wall_idx):
            junctions.append((_ft_to_cm(t_ft), node))
        junctions.sort(key=lambda item: item[0])

        def _span(f):
            op = openings_per_wall[wall_idx][f["opening_index"]]
            return _ft_to_cm(op[0]), _ft_to_cm(op[1])

        chains = [[decisions[0]]]
        inner_nodes = [[]]
        for prev, nxt in zip(decisions, decisions[1:]):
            _a, prev_hi = _span(prev)
            next_lo, _b = _span(nxt)
            pier = [(t, node) for t, node in junctions if prev_hi < t < next_lo]
            ok = (prev["from_course"] == nxt["from_course"] and len(pier) == 1
                  and pier[0][1].get("kind") == "T_INTERSECTION"
                  and pier[0][1].get("main_wall_idx") == wall_idx
                  and pier[0][1].get("incoming_wall_idx") is not None
                  and pier[0][0] - prev_hi <= max_cm and next_lo - pier[0][0] <= max_cm)
            if ok:
                chains[-1].append(nxt)
                inner_nodes[-1].append(pier[0])
            else:
                chains.append([nxt])
                inner_nodes.append([])
        main_half_cm = _ft_to_cm(walls_to_create[wall_idx][1]) / 2.0
        p0, _p1, wall_dir, _len_ft, _th = _wall_axis_and_length(walls_to_create, wall_idx)
        for chain, inner in zip(chains, inner_nodes):
            if len(chain) < 2:
                continue
            first_lo, _x = _span(chain[0])
            _y, last_hi = _span(chain[-1])
            left = [(t, node) for t, node in junctions if t <= first_lo + 0.5 and first_lo - t <= max_cm]
            right = [(t, node) for t, node in junctions if t >= last_hi - 0.5 and t - last_hi <= max_cm]
            if not left or not right:
                continue
            left_t, left_node = max(left, key=lambda item: item[0])
            right_t, right_node = min(right, key=lambda item: item[0])
            left_half = (_node_other_wall_thickness_cm(walls_to_create, left_node, wall_idx) or 0.0) / 2.0
            right_half = (_node_other_wall_thickness_cm(walls_to_create, right_node, wall_idx) or 0.0) / 2.0
            inner_out = []
            valid = True
            for node_t, node in inner:
                incoming = node["incoming_wall_idx"]
                end_index = None
                for arm in node.get("arms") or []:
                    if arm and arm[0] == incoming:
                        end_index = arm[1]
                if end_index is None:
                    valid = False
                    break
                ip0, _ip1, idir, ilen_ft, _ith = _wall_axis_and_length(walls_to_create, incoming)
                point = p0 + wall_dir * _cm_to_ft(node_t)
                t_axis = _ft_to_cm((point - ip0).DotProduct(idir))
                ilen = _ft_to_cm(ilen_ft)
                # dentro do eixo da parede que chega (vao alem da ponta deixava a
                # parede inteira sem recorte valido no motor)
                if end_index == 1:
                    region = (t_axis - main_half_cm, ilen)
                else:
                    region = (0.0, t_axis + main_half_cm)
                inner_out.append({"node_t_cm": round(node_t, 3), "incoming_wall_idx": incoming,
                                  "incoming_region_cm": [round(region[0], 3), round(region[1], 3)]})
            if not valid:
                continue
            passages.append({
                "wall_idx": wall_idx,
                "opening_indices": [f["opening_index"] for f in chain],
                "from_course": chain[0]["from_course"],
                "region_cm": [round(left_t + left_half, 3), round(right_t - right_half, 3)],
                "outer_node_t_cm": [round(left_t, 3), round(right_t, 3)],
                "inner": inner_out,
            })
    return passages


def openings_extended_to_top(openings_per_wall, free_to_top, course_band, num_courses, passages=None):
    """Copia de `openings_per_wall` para o SOLVE: o topo das passagens livres
    isoladas vai ao topo da ultima fiada (o motor trata o vao como porta ate' o
    topo). Passagem livre CONTINUA (`continuous_free_passages`): os vaos mantem o
    topo e ganham, acima dele, um vao sintetico de face de no' a face de no' na
    principal e um no trecho final de cada parede que chega no no' intermediario
    (termina na face da principal). Os vaos sinteticos vao no FIM da lista de
    cada parede - os indices dos vaos reais nao mudam."""
    if not free_to_top or num_courses <= 0:
        return openings_per_wall
    top_z = course_band(num_courses - 1)[1]
    marked = set((f["wall_idx"], f["opening_index"]) for f in free_to_top)
    grouped = set()
    extra = {}
    for passage in passages or []:
        wall_idx = passage["wall_idx"]
        head_z = max(openings_per_wall[wall_idx][oi][3] for oi in passage["opening_indices"])
        for oi in passage["opening_indices"]:
            grouped.add((wall_idx, oi))
        lo, hi = passage["region_cm"]
        extra.setdefault(wall_idx, []).append((_cm_to_ft(lo), _cm_to_ft(hi), head_z, top_z))
        for inner in passage["inner"]:
            a, b = inner["incoming_region_cm"]
            extra.setdefault(inner["incoming_wall_idx"], []).append((_cm_to_ft(a), _cm_to_ft(b), head_z, top_z))
    out = []
    for wall_idx, openings in enumerate(openings_per_wall):
        row = []
        for oi, opening in enumerate(openings):
            if (wall_idx, oi) in marked and (wall_idx, oi) not in grouped:
                row.append((opening[0], opening[1], opening[2], max(opening[3], top_z)))
            else:
                row.append(opening)
        row.extend(extra.get(wall_idx, []))
        out.append(row)
    return out


def _footprint_on_wall(candidate, p0, wall_dir):
    """(t_lo, t_hi, n_lo, n_hi) em cm da peca projetada no eixo/normal de uma
    parede - geometria real (comprimento no x_dir, largura no normal da peca)."""
    x_dir = candidate.get("x_dir") or wall_dir
    y_dir = XYZ(-x_dir.Y, x_dir.X, 0.0)
    normal = XYZ(-wall_dir.Y, wall_dir.X, 0.0)
    center = candidate["origin_world"] - p0
    c_t = _ft_to_cm(center.DotProduct(wall_dir))
    c_n = _ft_to_cm(center.DotProduct(normal))
    half_l = (candidate.get("length_cm") or 0.0) / 2.0
    half_w = (candidate.get("width_cm") or 14.0) / 2.0
    ext_t = abs(x_dir.DotProduct(wall_dir)) * half_l + abs(y_dir.DotProduct(wall_dir)) * half_w
    ext_n = abs(x_dir.DotProduct(normal)) * half_l + abs(y_dir.DotProduct(normal)) * half_w
    return c_t - ext_t, c_t + ext_t, c_n - ext_n, c_n + ext_n


def _pieces_in_wall_region(pieces, walls_to_create, wall_idx, lo_cm, hi_cm, margin_cm=0.5):
    p0, _p1, wall_dir, _len_ft, thickness_ft = _wall_axis_and_length(walls_to_create, wall_idx)
    half = _ft_to_cm(thickness_ft) / 2.0
    found = []
    for cand in pieces:
        t_lo, t_hi, n_lo, n_hi = _footprint_on_wall(cand, p0, wall_dir)
        if t_hi > lo_cm + margin_cm and t_lo < hi_cm - margin_cm and n_hi > -half + margin_cm \
                and n_lo < half - margin_cm:
            found.append((round(t_lo, 3), round(t_hi, 3), cand.get("logical_code"), cand.get("wall_idx")))
    return sorted(found)


def _unique_passages(passage_of):
    seen, out = set(), []
    for key in sorted(passage_of):
        passage = passage_of[key]
        ident = (passage["wall_idx"], tuple(passage["region_cm"]))
        if ident not in seen:
            seen.add(ident)
            out.append(passage)
    return out


def _jamb_outside_gap_cm(rows, t_jamb, side, reach_cm=80.0):
    """Distancia da jamba ate' a peca mais proxima do lado de FORA do vao
    (qualquer peca da faixa, inclusive amarracao transversal). `reach_cm`
    quando nao ha' peca nenhuma ate' essa distancia."""
    if side < 0:
        edges = [r["hi"] for r in rows if t_jamb - reach_cm <= r["hi"] <= t_jamb + 0.5]
        return max(0.0, t_jamb - max(edges)) if edges else reach_cm
    edges = [r["lo"] for r in rows if t_jamb - 0.5 <= r["lo"] <= t_jamb + reach_cm]
    return max(0.0, min(edges) - t_jamb) if edges else reach_cm


def _extend_run(rows, i0, i1, t_lo, t_hi, policy, cross=None):
    """Estende [i0, i1] (indices em `rows`) peca a peca ate' o apoio
    preferencial. `cross(j, support_cm)` pode transformar a amarracao `rows[j]`
    em trecho atravessavel (devolve True). Devolve (i0, i1, lim_esq, lim_dir)."""
    gap = policy["contiguous_gap_cm"] + CONTIGUOUS_GAP_EPSILON_CM
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
    gap = policy["contiguous_gap_cm"] + CONTIGUOUS_GAP_EPSILON_CM
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


def _bearing_cm(rows, lo_cm, hi_cm):
    """Comprimento de [lo_cm, hi_cm] efetivamente apoiado sobre pecas
    (uniao das extensoes de `rows`, fiada imediatamente abaixo)."""
    if hi_cm <= lo_cm:
        return 0.0
    spans = sorted((max(lo_cm, r["lo"]), min(hi_cm, r["hi"])) for r in rows
                   if r["hi"] > lo_cm and r["lo"] < hi_cm)
    total = 0.0
    cursor = lo_cm
    for a, b in spans:
        a = max(a, cursor)
        if b > a:
            total += b - a
            cursor = b
    return total


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
                               num_courses, base_z_abs, policy=None, nodes=None, catalog=None,
                               free_to_top=None):
    """Planeja CHANNEL sobre fiadas fisicas ja' resolvidas.

    `course_candidates`: {course_index: [candidato]} (NAO e' mutado).
    `course_band(ci) -> (z_lo_ft, z_hi_ft)`: faixa ocupada pela fiada fisica.
    `openings_per_wall[wi]`: [(t_lo_ft, t_hi_ft, sill_z_abs_ft, head_z_abs_ft)].
    `nodes` (grafo de encontros) habilita a deteccao de passagem livre pela
    distancia jamba -> no'; `catalog` (codigo -> entrada com length_cm e
    cells_local) habilita a travessia de T. `free_to_top`: decisoes de
    `free_to_top_openings` JA' aplicadas ao solve (vao estendido ate' o topo).
    O planejador NUNCA remove peca: passagem livre detectada sem ter sido
    aplicada ao solve vira `FREE_TO_TOP_NOT_PRESOLVED` (erro) e nao recebe
    canaleta superior.

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
    presolved = free_to_top is not None
    decided = (list(free_to_top) if presolved else
               free_to_top_openings(walls_to_create, openings_per_wall, nodes, course_band, num_courses,
                                    base_z_abs, policy))
    decided_keys = dict(((f["wall_idx"], f["opening_index"]), f) for f in decided)
    passage_of = {}
    for passage in (continuous_free_passages(walls_to_create, openings_per_wall, nodes, decided, policy)
                    if presolved else []):
        for oi in passage["opening_indices"]:
            passage_of[(passage["wall_idx"], oi)] = passage
    free_to_top = [dict(f) for f in decided] if presolved else []
    top_z = course_band(num_courses - 1)[1] if num_courses > 0 else None

    for wall_idx in range(len(walls_to_create)):
        openings = list(openings_per_wall[wall_idx] if wall_idx < len(openings_per_wall) else [])
        if not openings:
            continue
        demands = {}   # course_index -> [(opening_index, role)]
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
                decision = decided_keys.get((wall_idx, oi))
                if decision is not None and presolved:
                    rec["above"] = {"status": "FREE_TO_TOP", "course_index": above_ci}
                    passage = passage_of.get((wall_idx, oi))
                    if passage is not None:
                        rec["above"]["continuous_passage_region_cm"] = list(passage["region_cm"])
                elif decision is not None:
                    rec["above"] = {"status": "FREE_TO_TOP_NOT_PRESOLVED", "course_index": above_ci}
                    findings.append({"code": "FREE_TO_TOP_NOT_PRESOLVED", "severity": SEVERITY_ERROR,
                                     "classification": "ACTUAL_ERROR", "wall_idx": wall_idx, "opening_index": oi,
                                     "detail": "passagem livre precisa do vao estendido ate' o topo no solve; "
                                               "nenhuma peca removida"})
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
                    if problem == "TIE_OVER_SPAN":
                        # rastreio (secao 80): QUAL amarracao impede a corrida (regra 75)
                        rec[side_key]["tie_nodes"] = sorted(set(
                            rows[i]["cand"].get("node_index") for i in hits
                            if rows[i]["tie"] and rows[i]["cand"].get("node_index") is not None))
                    findings.append({"code": "MISSING_REQUIRED_CHANNEL", "severity": SEVERITY_ERROR,
                                     "classification": ("NEEDS_RULE" if problem == "TIE_OVER_SPAN"
                                                        else "ACTUAL_ERROR"),
                                     "wall_idx": wall_idx, "opening_index": oi,
                                     "course_index": ci, "role": role, "detail": problem})
                    continue
                def _cross(j, support_cm, rows=rows, ci=ci, t_lo=t_lo, t_hi=t_hi):
                    row = rows[j]
                    tie = row["cand"]
                    geometric_support_cm = support_cm
                    # Apoio EFETIVO: o que fica sobre alvenaria da fiada de baixo
                    # (um vazio junto a' jamba nao apoia nada).
                    if ci > 0:
                        below = _wall_strip_pieces(out_cc[ci - 1], walls_to_create, wall_idx)
                        if row["hi"] <= t_lo + 0.5 and j + 1 < len(rows):
                            support_cm = min(support_cm, _bearing_cm(below, rows[j + 1]["lo"], t_lo))
                        elif j - 1 >= 0:
                            support_cm = min(support_cm, _bearing_cm(below, t_hi, rows[j - 1]["hi"]))
                    if row["along"]:
                        if support_cm >= policy["convert_along_tie_when_support_below_cm"] - 1e-6:
                            return 0
                        return _convert_along_tie(j)
                    if support_cm > policy["cross_tee_when_support_at_most_cm"] + 1e-6:
                        return 0
                    if not policy.get("channel_may_cross_node_tie"):
                        # REGRA 75: nunca atravessar POR CIMA da amarracao do no'.
                        return 0
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
                    findings.append({"code": CHANNEL_THROUGH_T_PATTERN, "severity": SEVERITY_INFO,
                                     "classification": "SUPPORTED_PATTERN", "wall_idx": wall_idx,
                                     "course_index": ci, "incoming_wall_idx": tie.get("wall_idx"),
                                     "node_index": tie.get("node_index"),
                                     "detail": "canaleta atravessa o T; a parede que chega encosta na face "
                                               "nesta fiada (junta na face repete nas fiadas vizinhas, "
                                               "como no BUTANTA humano)"})
                    crossings.append({"course_index": ci, "main_wall_idx": wall_idx,
                                      "incoming_wall_idx": tie.get("wall_idx"), "node_index": tie.get("node_index"),
                                      "opening_index": oi, "role": role,
                                      "geometric_support_cm": round(geometric_support_cm, 3),
                                      "removed": tie, "added": abut,
                                      "lo_cm": round(row["lo"], 3), "hi_cm": round(row["hi"], 3)})
                    return 1

                i0, i1, lim_l, lim_r = _extend_run(rows, hits[0], hits[-1], t_lo, t_hi, policy, cross=_cross)
                # No' e orientacao da amarracao que limitou a corrida (usado pela
                # tentativa de paridade do CHANNEL, wall_modeling).
                blockers = {}
                for side, lim, j in (("l", lim_l, i0 - 1), ("r", lim_r, i1 + 1)):
                    if lim == "JUNCTION_TIE" and 0 <= j < len(rows):
                        blockers[side] = {"node_index": rows[j]["cand"].get("node_index"),
                                          "along": bool(rows[j]["along"])}
                # por IDENTIDADE da linha: conversoes de demandas seguintes
                # podem inserir linhas e deslocar indices.
                spans.append([rows[i0], rows[i1], oi, role, lim_l, lim_r, blockers])
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
                        replacements[_physical_key(src["cand"])] = (_physical_key(g[0]["cand"]), piece,
                                                                    round(g[0]["lo"], 4))
                for sp in run["items"]:
                    oi, role, lim_l, lim_r, blockers = sp[2], sp[3], sp[4], sp[5], sp[6]
                    opening = openings[oi]
                    t_lo = _ft_to_cm(opening[0])
                    t_hi = _ft_to_cm(opening[1])
                    support_l = round(t_lo - rows[sp[0]]["lo"], 3)
                    support_r = round(rows[sp[1]]["hi"] - t_hi, 3)
                    if ci > 0:
                        below_rows = _wall_strip_pieces(out_cc[ci - 1], walls_to_create, wall_idx)
                        bearing_l = round(_bearing_cm(below_rows, rows[sp[0]]["lo"], t_lo), 3)
                        bearing_r = round(_bearing_cm(below_rows, t_hi, rows[sp[1]]["hi"]), 3)
                    else:
                        bearing_l, bearing_r = support_l, support_r
                    side_key = "above" if role == ROLE_ABOVE_OPENING else "below"
                    rec = [r for r in openings_report if r["wall_idx"] == wall_idx and r["opening_index"] == oi][0]
                    rec[side_key] = {"status": "CHANNEL", "course_index": ci, "run_id": run_id,
                                     "support_l_cm": support_l, "support_r_cm": support_r,
                                     "bearing_l_cm": bearing_l, "bearing_r_cm": bearing_r,
                                     "limited_l": lim_l, "limited_r": lim_r,
                                     "blocker_l": blockers.get("l"), "blocker_r": blockers.get("r")}
                    for side, sup, bearing, lim in (("L", support_l, bearing_l, lim_l),
                                                    ("R", support_r, bearing_r, lim_r)):
                        if sup < policy["min_support_cm"] - 1e-6:
                            # 19 cm e' PREFERENCIAL (decisao B). Classificacao objetiva
                            # (auditoria 2026-09-14): sem assentamento = erro; abaixo do
                            # limiar de verga-na-canaleta (9 cm) = limitacao conhecida;
                            # entre 9 cm e o preferencial, assentado = alternativa.
                            if bearing <= 0.5:
                                classification = "ACTUAL_ERROR"
                            elif min(sup, bearing) < policy["convert_along_tie_when_support_below_cm"] - 1e-6:
                                classification = "KNOWN_LIMITATION"
                            else:
                                classification = "VALID_ALTERNATIVE"
                            findings.append({"code": "CHANNEL_SUPPORT_LIMITED", "severity": SEVERITY_WARNING,
                                             "classification": classification,
                                             "wall_idx": wall_idx, "opening_index": oi, "course_index": ci,
                                             "role": role, "side": side, "support_cm": sup,
                                             "bearing_cm": bearing, "limited_by": lim})
                runs.append(record)
            crossed = dict((_physical_key(x["removed"]), x) for x in crossings
                           if x["course_index"] == ci and x["main_wall_idx"] == wall_idx)
            split_removed = set(_physical_key(x["removed"]) for x in tie_conversions
                                if x["course_index"] == ci and x["wall_idx"] == wall_idx and x["mode"] == "SPLIT")
            if replacements or crossed:
                present = set(_physical_key(c) for c in out_cc[ci])
                rebuilt = []
                for cand in out_cc[ci]:
                    key = _physical_key(cand)
                    if key in split_removed:
                        continue
                    if key in crossed:
                        rebuilt.append(crossed[key]["added"])
                        continue
                    rep = replacements.get(key)
                    if rep is None:
                        rebuilt.append(cand)
                    elif rep[0] == key:
                        rebuilt.append(rep[1])
                # grupos cuja primeira peca e' o trecho atravessado (pseudo,
                # nao existe na fiada original): ordem canonica (corrida, eixo)
                seen = set()
                heads = sorted(set((rep[1]["reinforcement"]["run_id"], rep[2], rep[0])
                                   for rep in replacements.values() if rep[0] not in present))
                by_head = dict((rep[0], rep[1]) for rep in replacements.values())
                for _run_id, _lo, head_key in heads:
                    piece = by_head[head_key]
                    piece_key = _physical_key(piece)
                    if piece_key not in seen:
                        seen.add(piece_key)
                        rebuilt.append(piece)
                out_cc[ci] = rebuilt

    for x in crossings:
        x["removed_code"] = x.pop("removed").get("logical_code")
        x["added_code"] = x.pop("added").get("logical_code")
    for x in tie_conversions:
        x.pop("removed")
    return {"strategy": OPENING_REINFORCEMENT_CHANNEL, "policy": policy, "course_candidates": out_cc,
            "runs": runs, "openings": openings_report, "findings": findings, "free_to_top": free_to_top,
            "continuous_passages": _unique_passages(passage_of),
            "node_crossings": crossings, "tie_conversions": tie_conversions}


def validate_channel_reinforcement(course_candidates, walls_to_create, openings_per_wall, course_band,
                                   num_courses, base_z_abs, free_to_top=None, policy=None,
                                   reference_course_candidates=None, nodes=None, strip_cache=None):
    """Validador INDEPENDENTE do planejador (recalcula a demanda a partir das
    aberturas e confere as pecas). Devolve {"counts": {...}, "items": [...]}.

    MISSING_REQUIRED_CHANNEL / EXTRA_CHANNEL / CHANNEL_WRONG_COURSE /
    CHANNEL_INVADES_OPENING / CHANNEL_COLLISION / CHANNEL_SUPPORT_BELOW_POLICY.

    Abertura real x jambas (auditoria 2026-09-14): `CHANNEL_OPENING_OVERCUT`
    quando o vazio junto a uma jamba (distancia ate' a peca mais proxima do
    lado de fora) e' maior que na referencia - a mesma fiada antes do reforco
    (`reference_course_candidates`) ou, acima de uma passagem livre, a fiada
    de mesma paridade logo abaixo do topo do vao. `CHANNEL_FREE_TO_TOP_NOT_OPEN`
    quando sobra peca dentro do vao acima de uma passagem livre;
    `CHANNEL_ORPHAN_PIECE` para compensador solto (sem vizinha contigua) nessas
    fiadas. Nao basta nao haver peca DENTRO do vao."""
    policy = channel_policy(policy)
    tol_ft = _cm_to_ft(policy["grid_tolerance_cm"])
    joint_ft = _cm_to_ft(policy["grid_joint_allowance_cm"])
    gap = policy["contiguous_gap_cm"] + CONTIGUOUS_GAP_EPSILON_CM
    exempt = set((f["wall_idx"], f["opening_index"]) for f in (free_to_top or []))
    ftt_from = dict(((f["wall_idx"], f["opening_index"]), f["from_course"]) for f in (free_to_top or []))
    passages = continuous_free_passages(walls_to_create, openings_per_wall, nodes, free_to_top, policy) \
        if (free_to_top and nodes) else []
    in_passage = set((pa["wall_idx"], oi) for pa in passages for oi in pa["opening_indices"])
    counts = {"MISSING_REQUIRED_CHANNEL": 0, "EXTRA_CHANNEL": 0, "CHANNEL_WRONG_COURSE": 0,
              "CHANNEL_INVADES_OPENING": 0, "CHANNEL_COLLISION": 0, "CHANNEL_SUPPORT_BELOW_POLICY": 0,
              "CHANNEL_OPENING_OVERCUT": 0, "CHANNEL_FREE_TO_TOP_NOT_OPEN": 0, "CHANNEL_ORPHAN_PIECE": 0,
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

    buckets = course_wall_buckets(course_candidates)
    ref_buckets = course_wall_buckets(reference_course_candidates) if reference_course_candidates is not None else None
    if strip_cache is None:
        strip_cache = {}
    # ---- abertura real x jambas
    for wi in range(len(walls_to_create)):
        openings = openings_per_wall[wi] if wi < len(openings_per_wall) else []
        for oi, opening in enumerate(openings):
            t_lo = _ft_to_cm(opening[0])
            t_hi = _ft_to_cm(opening[1])
            from_ci = ftt_from.get((wi, oi))
            for ci in range(num_courses):
                z_lo, z_hi = course_band(ci)
                upper = from_ci is not None and ci >= from_ci
                if not upper and not _opening_active(opening, z_lo, z_hi, tol_ft):
                    continue
                if upper and (wi, oi) in in_passage:
                    continue  # validado pela regiao da passagem continua (abaixo)
                rows = cached_strip_rows(strip_cache, "now", buckets, ci, wi, walls_to_create)
                ref_rows = None
                if upper:
                    ref_ci = next((cj for cj in range(from_ci - 1, -1, -1)
                                   if cj % 2 == ci % 2 and _opening_active(opening, *(course_band(cj) + (tol_ft,)))),
                                  None)
                    if ref_ci is not None:
                        ref_rows = cached_strip_rows(strip_cache, "now", buckets, ref_ci, wi, walls_to_create)
                    inside = [r for r in rows if r["hi"] > t_lo + 0.5 and r["lo"] < t_hi - 0.5]
                    if inside:
                        counts["CHANNEL_FREE_TO_TOP_NOT_OPEN"] += len(inside)
                        items.append({"code": "CHANNEL_FREE_TO_TOP_NOT_OPEN", "wall_idx": wi, "course_index": ci,
                                      "opening_index": oi,
                                      "pieces": [[round(r["lo"], 3), round(r["hi"], 3)] for r in inside]})
                    for k, r in enumerate(rows):
                        if not r["along"] or r["tie"] or r["hi"] - r["lo"] >= 9.5:
                            continue
                        left_ok = k > 0 and 0.0 <= r["lo"] - rows[k - 1]["hi"] <= gap
                        right_ok = k + 1 < len(rows) and 0.0 <= rows[k + 1]["lo"] - r["hi"] <= gap
                        if not left_ok and not right_ok:
                            counts["CHANNEL_ORPHAN_PIECE"] += 1
                            items.append({"code": "CHANNEL_ORPHAN_PIECE", "wall_idx": wi, "course_index": ci,
                                          "opening_index": oi, "lo_cm": round(r["lo"], 3),
                                          "hi_cm": round(r["hi"], 3), "piece": r["cand"].get("logical_code")})
                elif reference_course_candidates is not None:
                    ref_rows = cached_strip_rows(strip_cache, "reference", ref_buckets, ci, wi, walls_to_create)
                if ref_rows is None:
                    continue
                for side, t_jamb in ((-1, t_lo), (1, t_hi)):
                    now = _jamb_outside_gap_cm(rows, t_jamb, side)
                    ref = _jamb_outside_gap_cm(ref_rows, t_jamb, side)
                    if now > ref + 0.5:
                        counts["CHANNEL_OPENING_OVERCUT"] += 1
                        items.append({"code": "CHANNEL_OPENING_OVERCUT", "wall_idx": wi, "course_index": ci,
                                      "opening_index": oi, "side": "L" if side < 0 else "R",
                                      "gap_cm": round(now, 3), "reference_gap_cm": round(ref, 3)})

    # ---- passagem livre continua: regiao de face de no' a face de no'
    for passage in passages:
        wi = passage["wall_idx"]
        lo, hi = passage["region_cm"]
        for ci in range(passage["from_course"], num_courses):
            pieces = course_candidates.get(ci) or []
            inside = _pieces_in_wall_region(pieces, walls_to_create, wi, lo, hi)
            for inner in passage["inner"]:
                a, b = inner["incoming_region_cm"]
                inside += _pieces_in_wall_region(pieces, walls_to_create, inner["incoming_wall_idx"], a, b)
            if inside:
                counts["CHANNEL_FREE_TO_TOP_NOT_OPEN"] += len(inside)
                items.append({"code": "CHANNEL_FREE_TO_TOP_NOT_OPEN", "wall_idx": wi, "course_index": ci,
                              "continuous_passage": [lo, hi], "pieces": inside})
            rows = cached_strip_rows(strip_cache, "now", buckets, ci, wi, walls_to_create)
            checks = [(rows, lo, -1), (rows, hi, 1)]
            for inner in passage["inner"]:
                a, b = inner["incoming_region_cm"]
                inc_rows = cached_strip_rows(strip_cache, "now", buckets, ci, inner["incoming_wall_idx"],
                                             walls_to_create)
                checks.append((inc_rows, a, -1) if a > 0 else (inc_rows, b, 1))
            for rows_k, t_edge, side in checks:
                edge_gap = _jamb_outside_gap_cm(rows_k, t_edge, side)
                if edge_gap > gap:
                    counts["CHANNEL_OPENING_OVERCUT"] += 1
                    items.append({"code": "CHANNEL_OPENING_OVERCUT", "wall_idx": wi, "course_index": ci,
                                  "continuous_passage": [lo, hi], "edge_cm": round(t_edge, 3),
                                  "gap_cm": round(edge_gap, 3)})
            for k, r in enumerate(rows):
                if not r["along"] or r["tie"] or r["hi"] - r["lo"] >= 9.5:
                    continue
                if r["hi"] < lo - 60.0 or r["lo"] > hi + 60.0:
                    continue
                left_ok = k > 0 and 0.0 <= r["lo"] - rows[k - 1]["hi"] <= gap
                right_ok = k + 1 < len(rows) and 0.0 <= rows[k + 1]["lo"] - r["hi"] <= gap
                if not left_ok and not right_ok:
                    counts["CHANNEL_ORPHAN_PIECE"] += 1
                    items.append({"code": "CHANNEL_ORPHAN_PIECE", "wall_idx": wi, "course_index": ci,
                                  "lo_cm": round(r["lo"], 3), "hi_cm": round(r["hi"], 3)})

    for ci in range(num_courses):
        pieces = course_candidates.get(ci) or []
        z_lo, z_hi = course_band(ci)
        channel_idx = set(i for i, c in enumerate(pieces) if is_channel_code(c.get("logical_code")))
        counts["channel_pieces"] += len(channel_idx)
        counts["channel_cut_pieces"] += sum(1 for c in pieces if c.get("logical_code") == CHANNEL_U_CUT)
        for wi in range(len(walls_to_create)):
            rows = cached_strip_rows(strip_cache, "now", buckets, ci, wi, walls_to_create)
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
        if channel_idx:
            boxes = [_candidate_obb(c) for c in pieces]
            aabbs = [_obb_aabb(b) for b in boxes]
            for i, j in sorted(_collision_candidate_pairs(range(len(pieces)), aabbs, 0.0)):
                if i not in channel_idx and j not in channel_idx:
                    continue
                if _obb_min_overlap(boxes[i], boxes[j]) > BOND_COLLISION_EPS_FT:
                    counts["CHANNEL_COLLISION"] += 1
                    items.append({"code": "CHANNEL_COLLISION", "course_index": ci,
                                  "a": pieces[i].get("logical_code"), "b": pieces[j].get("logical_code")})
    return {"counts": counts, "items": items}
