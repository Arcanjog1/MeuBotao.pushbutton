# -*- coding: utf-8 -*-
"""PAPEL FUNCIONAL DO ENCONTRO POR FIADA (secao 77 do REGRAS_MODULACAO_BLOCOS).

O grafo em planta (wall_pairing) diz "estas paredes se encontram em T/L/X" -
essa e' a TOPOLOGIA BASE e continua valendo. Este modulo responde a pergunta
que vem ANTES de "a peca de amarracao cabe?": nesta fiada, com as aberturas
ATIVAS nesta altura, o encontro EXISTE fisicamente? De que tipo?

Somente geometria (XY + Z + aberturas ativas). Nao escolhe peca, nao sabe se
a peca cabe, nao muda o no' do grafo: o tipo de base (`node["kind"]`) so' pode
ser REBAIXADO numa fiada, nunca promovido nem trocado de papel.

Criterio (nenhum limiar novo; ids de parede/no' nunca entram na logica)
----------------------------------------------------------------------
Para cada no' L/T/X e cada fiada c:

  1. faixa vertical da fiada = `course_band_ft(c)` (no motor:
     wall_modeling._free_to_top_band -> _course_z_band; fiada c = [20c+1,
     20c+20] cm, so' o bloco de 19 cm - FIRST_COURSE_Z_OFFSET_CM).
  2. aberturas ATIVAS na fiada = a MESMA regra do solve
     (wall_modeling._opening_active_in_course_band: sobreposicao em z maior
     que OPENING_COURSE_BAND_TOLERANCE_FT = 0,5 cm). `openings_per_wall` deve
     ser o modelo de aberturas do SOLVE (wall_modeling._effective_solve_
     openings: passagens livres ate' o topo e continuas estendidas), o mesmo
     que a auditoria 76.1 le.
  3. regiao do no' = wall_stepper._node_region_polygon(node, walls, banda);
     faixa de cada parede w no proprio eixo = wall_stepper._axis_t_range_ft.
  4. ABSENT (o `not_required` que ja' existia na auditoria 76.1, mesma
     condicao de wall_stepper.junction_bond_audit): uma abertura ativa cobre a
     faixa inteira de alguma parede do no' (folga `absent_fit_cm`, default a
     mesma PIER_PHYSICAL_FIT_TOLERANCE_CM da auditoria).
  5. BRACOS do no' pela TOPOLOGIA do grafo (nao por geometria): parede com a
     ponta no no' (em `arms`, ou a vizinha do L de ponta unica via
     `neighbor_end_index`) tem so' o lado interno; parede que passa
     (principal de T de uma ponta, cruzamento de meio de vao) tem os dois
     lados.
  6. corpo solido de cada braco = trecho solido CONTIGUO a' faixa, da borda
     da faixa ate' a proxima abertura ativa ou a ponta da parede.
  7. o braco DEIXA DE PARTICIPAR somente quando uma ABERTURA ATIVA nesta
     fiada consumiu esse corpo (corpo restante <= tol, tol =
     PIER_PHYSICAL_FIT_TOLERANCE_CM, 0,05 cm - a tolerancia fisica ja'
     aprovada, secao 74). A ponta natural de uma parede NUNCA desliga o
     braco: um toco curto de parede e' geometria de modelagem, nao
     abertura, e continua sendo encontro (decisao conservadora, secao 77.3
     - "existe corpo -> o braco existe; depois room_ok/fit/apoio decidem se
     a peca cabe").
  8. papel efetivo pelos bracos que participam (so' rebaixa):
        4 -> X ; 3 -> T ; 2 colineares -> NONE_CONTINUOUS (a parede que
        passa continua; so' e' consumido pelo solve quando essa parede passa
        pelo no' em meio de vao) ; 2 perpendiculares -> L ; 1 ->
        NONE_FREE_END (a parede desse braco termina LIVRE ali: a regiao do
        no' e' a ponta dela, ate' a face externa da vizinha) ; 0 ->
        NONE_EMPTY. Colinear/perpendicular usa WALL_GRAPH_COLLINEAR_
        TOLERANCE / WALL_GRAPH_PERPENDICULAR_TOLERANCE, as mesmas do grafo.
  9. diagnostico que NAO muda o papel: braco com corpo em (tol, menor peca
     do catalogo) -> STUB_BELOW_MIN_UNIT (registro para decisao de produto:
     PENDING_PRODUCT_DECISION); abertura que invade parte da faixa sem
     cobri-la -> STRIP_PARTIALLY_OPEN.
 10. parede do no' INTEIRA dentro da faixa (toco de modelagem de 14-15 cm,
     as duas pontas no no'): nao ha' braco dela para medir, mas ela esta'
     la' - o papel fica o da topologia base (WALL_INSIDE_NODE_STRIP). So'
     uma abertura ativa cobrindo a faixa (ABSENT) muda isso.
 11. NONE_FREE_END exige que a parede que sobra seja PERPENDICULAR aos
     bracos consumidos (WALL_GRAPH_PERPENDICULAR_TOLERANCE, a do grafo): ela
     termina livre NA FACE da que sumiu. Duas paredes paralelas sobrepostas
     (CAD cru) formam "T" no grafo mas nao tem face - papel base
     (ARMS_NOT_PERPENDICULAR).

O SOLVE consome apenas NONE_FREE_END (a parede que sobra termina livre na
face da vizinha, pelas regras normais de termino). NONE_CONTINUOUS (a
parede que chega foi consumida por abertura ativa; a que passa continua) e'
CLASSIFICACAO/diagnostico: a composicao de uma parede passando por uma
regiao de no' cujo encontro sumiu nao tem regra aprovada (secao 77.5) e o
no' fica como a topologia base - conservador.

Exigir amarracao (`bond_required`) so' para X/T/L. NONE_* e ABSENT ficam
fora do denominador do gate MISSING_REQUIRED_JUNCTION_BOND (razao
NO_FUNCTIONAL_JUNCTION - nao ha' encontro requerido).

IronPython 2.7: sem f-strings, sem estado global, sem dependencia do Revit.
"""

ROLE_X = "X"
ROLE_T = "T"
ROLE_L = "L"
ROLE_NONE_FREE_END = "NONE_FREE_END"
ROLE_NONE_CONTINUOUS = "NONE_CONTINUOUS"
ROLE_NONE_EMPTY = "NONE_EMPTY"
ROLE_ABSENT = "ABSENT"
BOND_ROLES = (ROLE_X, ROLE_T, ROLE_L)
BASE_ROLE_BY_KIND = {"X_INTERSECTION": ROLE_X, "T_INTERSECTION": ROLE_T, "L_CORNER": ROLE_L}
NODE_KINDS = ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION")
_RANK = {ROLE_X: 4, ROLE_T: 3, ROLE_L: 2, ROLE_NONE_CONTINUOUS: 1, ROLE_NONE_FREE_END: 1,
         ROLE_NONE_EMPTY: 0, ROLE_ABSENT: 0}
LIMIT_WALL_END = "WALL_END"
LIMIT_OPENING = "OPENING"


def _line_frame(wall):
    line = wall[0]
    p0 = line.GetEndPoint(0)
    p1 = line.GetEndPoint(1)
    dx, dy = p1.X - p0.X, p1.Y - p0.Y
    length = (dx * dx + dy * dy) ** 0.5
    if length <= 0.0:
        return None
    return length, (dx / length, dy / length)


def _ends_at_node(node, wall_idx):
    """Indices de ponta (0/1) de `wall_idx` que estao NESTE no', pela topologia
    do grafo: `arms` e, no L de ponta unica, a vizinha (`neighbor_end_index`)."""
    ends = set()
    for w, e in (node.get("arms") or []):
        if w == wall_idx:
            ends.add(e)
    if (node.get("kind") == "L_CORNER" and node.get("neighbor_wall_idx") == wall_idx
            and node.get("neighbor_end_index") is not None and not ends):
        ends.add(node.get("neighbor_end_index"))
    return ends


def _wall_label(node, wall_idx):
    if node.get("kind") == "T_INTERSECTION":
        if wall_idx == node.get("main_wall_idx"):
            return "main"
        if wall_idx == node.get("incoming_wall_idx"):
            return "incoming"
        if wall_idx == node.get("neighbor_wall_idx"):
            return "main2"
    return "arm"


def node_arms(node, walls_to_create, ws, band_width_ft=None):
    """Geometria fixa (independente de fiada) de um no' L/T/X, ou None.

    {"poly", "walls": [w], "strip_ft": {w: (a, b)}, "length_ft": {w: L},
     "arms": [{"wall_idx", "side" ('-' ou '+'), "label", "dir": (ux, uy)}]}"""
    if node.get("kind") not in NODE_KINDS:
        return None
    poly = ws._node_region_polygon(node, walls_to_create, band_width_ft)
    if not poly or ws._poly_area(poly) <= 0.0:
        return None
    walls = [w for w in sorted(ws._node_wall_indices(node)) if 0 <= w < len(walls_to_create)]
    strip, length, arms, inside = {}, {}, [], []
    for w in walls:
        frame = _line_frame(walls_to_create[w])
        if frame is None:
            continue
        L, u = frame
        strip[w] = ws._axis_t_range_ft(walls_to_create[w], poly)
        length[w] = L
        ends = _ends_at_node(node, w)
        if 0 in ends and 1 in ends:
            # parede INTEIRA dentro da regiao do no' (toco de modelagem): nao tem
            # braco para medir, mas esta' la' - nunca rebaixa o papel (item 10)
            sides = []
            inside.append(w)
        elif 0 in ends:
            sides = ["+"]
        elif 1 in ends:
            sides = ["-"]
        else:
            sides = ["-", "+"]
        for side in sides:
            sgn = 1.0 if side == "+" else -1.0
            arms.append({"wall_idx": w, "side": side, "label": _wall_label(node, w),
                         "dir": (sgn * u[0], sgn * u[1])})
    return {"poly": poly, "walls": walls, "strip_ft": strip, "length_ft": length, "arms": arms,
            "inside": inside}


def _solid_from_strip(side, a, b, length, rows, tol_ft):
    """(corpo solido contiguo em ft, o que o limita, abertura invade a faixa
    mais que `tol_ft`?) do lado `side` da faixa [a, b], ate' a proxima
    abertura ativa ou a ponta da parede. `o que o limita` e' LIMIT_WALL_END ou
    (LIMIT_OPENING, lo, hi)."""
    intrudes = False
    if side == "+":
        limit, what = length, LIMIT_WALL_END
        for r in rows:
            if r[1] > b and r[0] < limit:
                limit, what = r[0], (LIMIT_OPENING, r[0], r[1])
        if b - limit > tol_ft:
            intrudes = True
        return max(0.0, limit - b), what, intrudes
    limit, what = 0.0, LIMIT_WALL_END
    for r in rows:
        if r[0] < a and r[1] > limit:
            limit, what = r[1], (LIMIT_OPENING, r[0], r[1])
    if limit - a > tol_ft:
        intrudes = True
    return max(0.0, a - limit), what, intrudes


def _role_from_arms(alive, ws):
    n = len(alive)
    if n >= 4:
        return ROLE_X
    if n == 3:
        return ROLE_T
    if n == 2:
        d0, d1 = alive[0]["dir"], alive[1]["dir"]
        dot = d0[0] * d1[0] + d0[1] * d1[1]
        if dot <= -1.0 + ws.WALL_GRAPH_COLLINEAR_TOLERANCE:
            return ROLE_NONE_CONTINUOUS
        if abs(dot) <= ws.WALL_GRAPH_PERPENDICULAR_TOLERANCE:
            return ROLE_L
        return None
    if n == 1:
        return ROLE_NONE_FREE_END
    return ROLE_NONE_EMPTY


def _catalog_min_unit_cm(catalog):
    vals = []
    for entry in (catalog or {}).values():
        try:
            v = float((entry or {}).get("length_cm") or 0.0)
        except (TypeError, ValueError):
            continue
        if v > 0.0:
            vals.append(v)
    return min(vals) if vals else None


def junction_roles(nodes, walls_to_create, openings_per_wall, course_band_ft, num_courses, ws,
                   tol_cm=None, opening_active=None, opening_tol_ft=None, band_width_ft=None,
                   catalog=None, min_unit_cm=None, courses=None, absent_fit_cm=None):
    """Papel funcional de cada no' L/T/X em cada fiada. Lista de dicts:

        {node_index, course_index, base_kind, base_role, effective_role,
         bond_required, changed, reason, s_by_wall: {wall_idx: {lado: cm}},
         absent_walls, stub_flags, arms, free_end_wall, continuous_walls,
         z_band_cm}

    `opening_active(sill, head, z_lo, z_hi)` e' a regra de atividade do solve
    (wall_modeling._opening_active_in_course_band). Sem ela, usa
    `opening_tol_ft` na mesma formula; sem nenhum dos dois -> ValueError
    (nao se inventa uma regra diferente da do solve).
    `band_width_ft` limita a regiao do no' a' largura da alvenaria como a
    auditoria 76.1 faz (None = espessura da parede).
    `catalog`/`min_unit_cm` so' alimentam o diagnostico STUB_BELOW_MIN_UNIT.
    `tol_cm` (None = PIER_PHYSICAL_FIT_TOLERANCE_CM) e' o limiar de corpo do
    braco. `absent_fit_cm` (None = PIER_PHYSICAL_FIT_TOLERANCE_CM, o
    `fit_tol_cm` default da auditoria 76.1) e' a folga da regra ABSENT - fica
    SEPARADA de `tol_cm` para que variar o limiar de corpo nao mexa na regra
    de `not_required` que ja' existia.
    """
    if opening_active is None:
        if opening_tol_ft is None:
            raise ValueError("junction_roles: passe opening_active (regra do solve) ou opening_tol_ft")
        tol_z = float(opening_tol_ft)

        def opening_active(sill, head, z_lo, z_hi):
            return (min(head, z_hi) - max(sill, z_lo)) > tol_z
    tol = ws.PIER_PHYSICAL_FIT_TOLERANCE_CM if tol_cm is None else float(tol_cm)
    tol_ft = ws._cm_to_ft(tol)
    fit = ws.PIER_PHYSICAL_FIT_TOLERANCE_CM if absent_fit_cm is None else float(absent_fit_cm)
    fit_ft = ws._cm_to_ft(fit)
    if min_unit_cm is None:
        min_unit_cm = _catalog_min_unit_cm(catalog)
    course_list = list(range(num_courses)) if courses is None else list(courses)
    geo = []
    for ni, node in enumerate(nodes or []):
        g = node_arms(node, walls_to_create, ws, band_width_ft)
        if g is not None:
            geo.append((ni, node, g))
    out = []
    for ci in course_list:
        z_lo, z_hi = course_band_ft(ci)
        active_cache = {}
        for ni, node, g in geo:
            active = {}
            for w in g["walls"]:
                if w not in active_cache:
                    rows = openings_per_wall[w] if w < len(openings_per_wall) else ()
                    active_cache[w] = [r for r in rows if opening_active(r[2], r[3], z_lo, z_hi)]
                active[w] = active_cache[w]
            covered = []
            for w in g["walls"]:
                a, b = g["strip_ft"][w]
                for r in active[w]:
                    if r[0] <= a + fit_ft and r[1] >= b - fit_ft:
                        covered.append(w)
                        break
            s_by_wall, arm_out, alive, stubs = {}, [], [], []
            partial = []
            for arm in g["arms"]:
                w, side = arm["wall_idx"], arm["side"]
                a, b = g["strip_ft"][w]
                s_ft, what, intrudes = _solid_from_strip(side, a, b, g["length_ft"][w], active[w], tol_ft)
                s_cm = ws._ft_to_cm(s_ft)
                s_by_wall.setdefault(w, {})[side] = round(s_cm, 3)
                # item 7 do criterio: so' uma ABERTURA ATIVA consome o braco;
                # a ponta natural da parede nunca o desliga
                consumed_by_opening = (what != LIMIT_WALL_END) and (s_cm <= tol)
                ok = not consumed_by_opening
                if intrudes and w not in covered and w not in partial:
                    partial.append(w)
                if ok and min_unit_cm is not None and s_cm < min_unit_cm:
                    stubs.append("STUB_BELOW_MIN_UNIT:%s:w%d%s:%.2f" % (arm["label"], w, side, s_cm))
                lim = (what if what == LIMIT_WALL_END
                       else [round(ws._ft_to_cm(what[1]), 2), round(ws._ft_to_cm(what[2]), 2)])
                arm_out.append({"wall_idx": w, "side": side, "label": arm["label"], "s_cm": round(s_cm, 3),
                                "participates": ok, "limit": lim})
                if ok:
                    alive.append(arm)
            for w in partial:
                stubs.append("STRIP_PARTIALLY_OPEN:w%d" % w)
            base_role = BASE_ROLE_BY_KIND.get(node.get("kind"))
            free_end, continuous = None, []
            if covered:
                role, reason, absent = ROLE_ABSENT, "OPENING_COVERS_NODE_STRIP", list(covered)
            elif g["inside"]:
                # uma parede do no' esta' inteira dentro da faixa (toco): nao ha'
                # braco dela para medir - o encontro fica como a topologia base diz
                role = base_role
                stubs.append("WALL_INSIDE_NODE_STRIP:" + ",".join("w%d" % w for w in g["inside"]))
                dead = [x for x in arm_out if not x["participates"]]
                reason = "ALL_ARMS_SOLID" if not dead else "NO_BODY:" + ",".join(
                    "%s%s" % (x["label"] if x["label"] != "arm" else "arm%d" % x["wall_idx"], x["side"])
                    for x in dead)
                absent = []
            else:
                role = _role_from_arms(alive, ws)
                if role is None or _RANK.get(role, 0) > _RANK.get(base_role, 0):
                    stubs.append("ARMS_INCONSISTENT_WITH_BASE:%d_alive" % len(alive))
                    role = base_role
                dead = [x for x in arm_out if not x["participates"]]
                reason = "ALL_ARMS_SOLID" if not dead else "NO_BODY:" + ",".join(
                    "%s%s" % (x["label"] if x["label"] != "arm" else "arm%d" % x["wall_idx"], x["side"])
                    for x in dead)
                alive_walls = set(x["wall_idx"] for x in alive)
                absent = [w for w in g["walls"] if w not in alive_walls and w in s_by_wall]
                if role == ROLE_NONE_FREE_END:
                    # item 11: a parede que sobra termina livre NA FACE da que
                    # sumiu - isso so' faz sentido se ela e' perpendicular aos
                    # bracos consumidos. Paredes paralelas sobrepostas (CAD cru)
                    # formam "T" no grafo mas nao tem face para terminar: o papel
                    # fica o da base (ARMS_NOT_PERPENDICULAR).
                    d_alive = alive[0]["dir"]
                    for arm in g["arms"]:
                        if arm["wall_idx"] == alive[0]["wall_idx"]:
                            continue
                        dot = d_alive[0] * arm["dir"][0] + d_alive[1] * arm["dir"][1]
                        if abs(dot) > ws.WALL_GRAPH_PERPENDICULAR_TOLERANCE:
                            stubs.append("ARMS_NOT_PERPENDICULAR:w%d" % arm["wall_idx"])
                            role = base_role
                            break
                if role == ROLE_NONE_FREE_END:
                    free_end = alive[0]["wall_idx"]
                elif role == ROLE_NONE_CONTINUOUS:
                    continuous = sorted(alive_walls)
            out.append({
                "node_index": ni, "course_index": ci, "base_kind": node.get("kind"), "base_role": base_role,
                "effective_role": role, "bond_required": role in BOND_ROLES, "changed": role != base_role,
                "reason": reason, "s_by_wall": s_by_wall, "absent_walls": absent, "stub_flags": stubs,
                "arms": arm_out, "free_end_wall": free_end, "continuous_walls": continuous,
                "z_band_cm": [round(ws._ft_to_cm(z_lo), 2), round(ws._ft_to_cm(z_hi), 2)]})
    out.sort(key=lambda r: (r["node_index"], r["course_index"]))
    return out


def roles_index(records):
    """{(node_index, course_index): registro}."""
    return dict(((r["node_index"], r["course_index"]), r) for r in records)


def summarize(records):
    """Contagens por papel efetivo, mudancas base -> efetivo e os tocos
    (PENDING_PRODUCT_DECISION: corpo entre a tolerancia e a menor peca)."""
    by_role, changes, stubs = {}, {}, []
    for r in records:
        by_role[r["effective_role"]] = by_role.get(r["effective_role"], 0) + 1
        if r["changed"]:
            k = "%s->%s" % (r["base_role"], r["effective_role"])
            changes[k] = changes.get(k, 0) + 1
        for f in r.get("stub_flags") or ():
            if str(f).startswith("STUB_BELOW_MIN_UNIT"):
                stubs.append((r["node_index"], r["course_index"], f))
    return {"by_role": by_role, "changes": changes, "total": len(records),
            "bond_required": sum(1 for r in records if r["bond_required"]),
            "pending_product_decision": stubs}
