# -*- coding: utf-8 -*-
"""Corpus auditavel da SECAO 74 - reconstroi a geometria do BUTANTA sem Revit.

STATUS: EVIDENCIA / NAO NORMA.

Por que este modulo existe
--------------------------
As alegacoes da secao 74 (nos 24/44/46, controles 12/26, faltas de 4/15/20 cm,
parede 8284580, hash do snapshot) foram medidas sobre a geometria REAL do
projeto BUTANTA R08_LT, que nao estava versionada. Sem ela, uma auditoria
independente nao conseguia reproduzir nenhum desses numeros. Este modulo le a
geometria minima versionada em `reference_projects/butanta_r08_lt/s74_corpus/`
e a entrega as FUNCOES REAIS do motor.

A fronteira e' explicita
------------------------
NADA que decida "cabe / nao cabe", "qual peca", "qual fiada" e' reimplementado
aqui. Tudo isso vem do motor:

  * `assign_openings_to_walls`        (wall_modeling)
  * `extend_wall_ends_to_junctions`   (wall_modeling)
  * `build_wall_graph`                (wall_pairing)
  * `_t_intersection_room_assessment` (wall_stepper)  <- mede o espaco do T
  * `_t_intersection_room_ok`         (wall_stepper)  <- A DECISAO auditada
  * `solve_building_blocks_all_courses`

O que este modulo implementa e' so' REGUA DE COMPARACAO - contagem de pecas por
parede, zona do B34, divergencia e a normalizacao do snapshot. Sao medidas
sobre a saida do motor, nunca decisoes dentro dele.
"""
import collections
import contextlib
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CORPUS_DIR = os.path.join(ROOT, "reference_projects", "butanta_r08_lt", "s74_corpus")
TESTS_DIR = os.path.join(ROOT, "tests")

CM_PER_FT = 30.48
COURSES_RULER = 12          # fiadas 0-11: e' a faixa que os dois projetos constroem
COURSES_SOLVE = 17          # 340 cm de pe-direito
BLOCOS = ("B39", "B34", "B54", "B19")
ESPECIAIS = ("C09", "C04")
ZONA_CM = 20.0
PERTO_DA_PONTA = 60.0
NODE_TOL_CM = 30.0
SOLVER_CODE = {"B39": "B39", "B34": "B34", "B54": "B54", "B19": "B19",
               "C09": "C09", "C04": "C04", "CHANNEL_U_39": "K39", "CHANNEL_U_34": "K34",
               "CHANNEL_U_19": "K19", "CHANNEL_U_CUT": "KV"}

_ENGINE = {}


# ============================================================ motor e corpus
def engine():
    """(wall_modeling, wall_stepper) carregados fora do Revit pelos dubles."""
    if "ws" not in _ENGINE:          # a chave escrita por ULTIMO e' a que guarda
        if TESTS_DIR not in sys.path:
            sys.path.insert(0, TESTS_DIR)
        os.environ.setdefault("SCALE_BENCH_TESTS", TESTS_DIR)
        import load_script
        m = load_script.load()
        _ENGINE["m"] = m
        _ENGINE["ws"] = sys.modules["core.engine.wall_stepper"]
    return _ENGINE["m"], _ENGINE["ws"]


def load(name):
    with open(os.path.join(CORPUS_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


def geometry():
    return load("geometry.json")


def t_nodes_expected():
    return load("t_nodes.json")


def wall_case():
    return load("wall_8284580.json")


def snapshot_expected():
    return load("snapshot_v1.json")


# ================================================== reconstrucao da geometria
def build_context(geo, translate=(0.0, 0.0), order=None, swap_ends=()):
    """Reconstroi o contexto do motor a partir da geometria versionada.

    `translate` (cm), `order` (permutacao da lista de paredes) e `swap_ends`
    (chaves de parede com as pontas invertidas) existem para os testes de
    invariancia - nao mudam a fisica, so' como a geometria e' apresentada.
    """
    m, _ws = engine()
    XYZ, Line = m.XYZ, m.Line
    dx, dy = translate

    walls = list(geo["walls"])
    if order is not None:
        walls = [walls[i] for i in order]

    walls_to_create, keys = [], []
    for w in walls:
        p0, p1 = list(w["p0_cm"]), list(w["p1_cm"])
        if w["key"] in swap_ends:
            p0, p1 = p1, p0
        line = Line.CreateBound(
            XYZ((p0[0] + dx) / CM_PER_FT, (p0[1] + dy) / CM_PER_FT, 0.0),
            XYZ((p1[0] + dx) / CM_PER_FT, (p1[1] + dy) / CM_PER_FT, 0.0))
        walls_to_create.append((line, w["thickness_cm"] / CM_PER_FT, (False, False)))
        keys.append(w["key"])

    ops = []
    for o in geo["openings"]:
        ops.append({
            "center_xy": XYZ((o["center_cm"][0] + dx) / CM_PER_FT, (o["center_cm"][1] + dy) / CM_PER_FT, 0.0),
            "center_source": "geometria",
            "insertion_xy": XYZ((o["insertion_cm"][0] + dx) / CM_PER_FT, (o["insertion_cm"][1] + dy) / CM_PER_FT, 0.0),
            "bbox_center_xy": XYZ((o["center_cm"][0] + dx) / CM_PER_FT, (o["center_cm"][1] + dy) / CM_PER_FT, 0.0),
            "hand_xy": XYZ(o["hand"][0], o["hand"][1], 0.0),
            "width_ft": o["width_cm"] / CM_PER_FT,
            "sill_z_abs": o["sill_cm"] / CM_PER_FT,
            "head_z_abs": o["head_cm"] / CM_PER_FT,
            "element_id": str(o["key"]),
            "element_id_obj": o["key"],
        })

    diag = {"clamped_opening_count": 0, "opening_center_gap_max_ft": 0.0,
            "opening_off_center_count": 0, "assignments": [], "unassigned_openings": []}
    openings_per_wall = m.assign_openings_to_walls(walls_to_create, ops, diag)
    original = list(walls_to_create)
    extended, jmap = m.extend_wall_ends_to_junctions(walls_to_create, m.JUNCTION_FACE_SEARCH_FT)
    nodes, e2n = m.build_wall_graph(extended, jmap)
    return {"walls": extended, "original_axes": original, "nodes": nodes, "e2n": e2n,
            "openings_per_wall": openings_per_wall, "keys": keys, "ops": ops, "diag": diag,
            "translate": (dx, dy)}


def with_opening_variant(geo, nome):
    """Devolve a geometria com uma VARIANTE de posicao de abertura aplicada.

    `original` e' o estado do arquivo (o mesmo para o qual o reset devolve as 44
    aberturas). `post_micro_adjustment_s66` e' o estado DEPOIS do microajuste da
    secao 66, em que tres aberturas andaram 10 cm - foi sobre esse estado que a
    varredura de tolerancia do checkpoint mediu os totais da regua. As duas estao
    versionadas para que os dois conjuntos de numeros sejam reproduziveis.
    """
    if nome == "original":
        return geo
    variante = (geo.get("opening_variants") or {}).get(nome)
    if variante is None:
        raise KeyError("variante de abertura desconhecida: %s" % nome)
    novas = []
    por_chave = dict((v["key"], v) for v in variante)
    for o in geo["openings"]:
        v = por_chave.get(o["key"])
        novas.append(dict(o, center_cm=v["center_cm"], insertion_cm=v["insertion_cm"]) if v else o)
    return dict(geo, openings=novas)


def catalog(geo=None):
    """Catalogo REAL das familias do projeto (celulas lidas da geometria)."""
    geo = geo or geometry()
    out = {}
    for code, e in geo["catalog"].items():
        out[code] = dict(e, symbol=None, logical_code=code, source_instance_id=None,
                         cells_local=[{"center_local": tuple(c["center_local"]),
                                       "size_local": tuple(c["size_local"])}
                                      for c in e["cells_local"]])
    return out


# ================================================ o encontro T e a decisao
def tee_nodes(ctx):
    """[(indice, no)] dos T_INTERSECTION, na ordem em que o motor os montou."""
    return [(i, n) for i, n in enumerate(ctx["nodes"]) if n.get("kind") == "T_INTERSECTION"]


def node_key(ctx, index, translate_back=True):
    """Chave LOGICA estavel do no: posicao arredondada, independente de
    ElementId, de indice de lista e da ordem de entrada das paredes."""
    node = ctx["nodes"][index]
    p = node["point"]
    dx, dy = ctx.get("translate", (0.0, 0.0))
    x = p.X * CM_PER_FT - (dx if translate_back else 0.0)
    y = p.Y * CM_PER_FT - (dy if translate_back else 0.0)
    return "T@%.1f,%.1f" % (round(x, 1) + 0.0, round(y, 1) + 0.0)


def assessment_cm(ctx, index):
    """Chama `_t_intersection_room_assessment` REAL e devolve em centimetros."""
    _m, ws = engine()
    a = ws._t_intersection_room_assessment(
        ctx["nodes"][index], ctx["walls"], ctx["openings_per_wall"],
        nodes=ctx["nodes"], end_to_node=ctx["e2n"], node_index=index)
    if a is None:
        return None
    return {"room_plus_cm": a["room_plus_ft"] * CM_PER_FT,
            "room_minus_cm": a["room_minus_ft"] * CM_PER_FT,
            "room_min_cm": min(a["room_plus_ft"], a["room_minus_ft"]) * CM_PER_FT,
            "room_incoming_cm": a["room_incoming_ft"] * CM_PER_FT}


def room_ok(ctx, index, physical_tolerance):
    """Chama `_t_intersection_room_ok` REAL com a flag da secao 74 ligada ou
    desligada. Salva e restaura a flag - nenhum estado global vaza."""
    _m, ws = engine()
    antes = ws.T_ROOM_PHYSICAL_TOLERANCE
    ws.T_ROOM_PHYSICAL_TOLERANCE = bool(physical_tolerance)
    try:
        return bool(ws._t_intersection_room_ok(
            ctx["nodes"][index], ctx["walls"], ctx["openings_per_wall"],
            nodes=ctx["nodes"], end_to_node=ctx["e2n"], node_index=index))
    finally:
        ws.T_ROOM_PHYSICAL_TOLERANCE = antes


def exige_cm():
    """Exigencias do motor, em cm (27 cm de cada lado para o B54; 34 para o B34)."""
    _m, ws = engine()
    return (ws.T_INTERSECTION_B54_HALF_ROOM_FT * CM_PER_FT,
            ws.CORNER_B34_ROOM_FT * CM_PER_FT)


def tolerance_cm():
    """A tolerancia fisica da secao 74, lida da constante do motor."""
    _m, ws = engine()
    return ws.PIER_PHYSICAL_FIT_TOLERANCE_CM


@contextlib.contextmanager
def forced_tolerance_cm(valor_cm):
    """Roda o motor com OUTRA tolerancia, so' para a varredura de saturacao.

    NAO altera `PIER_PHYSICAL_FIT_TOLERANCE_CM` nem o codigo do motor: troca
    temporariamente a funcao `_t_intersection_room_tolerance_ft`, que e' o unico
    ponto onde a tolerancia entra. A DECISAO continua sendo a do motor - o que
    varia e' so' o parametro. Serve para responder "existe precipicio perto de
    0,05 cm?", nunca para produzir o resultado de producao.
    """
    _m, ws = engine()
    antes_fn = ws._t_intersection_room_tolerance_ft
    antes_flag = ws.T_ROOM_PHYSICAL_TOLERANCE
    def _forcada():
        # preserva o ramo DESLIGADO: sem a secao 74 vale o epsilon historico
        if not ws.T_ROOM_PHYSICAL_TOLERANCE:
            return 1e-6
        return valor_cm / 100.0 * ws.FEET_PER_METER

    ws._t_intersection_room_tolerance_ft = _forcada
    ws.T_ROOM_PHYSICAL_TOLERANCE = True
    try:
        yield
    finally:
        ws._t_intersection_room_tolerance_ft = antes_fn
        ws.T_ROOM_PHYSICAL_TOLERANCE = antes_flag


# ============================================================= solve completo
def solve(ctx, physical_tolerance, geo=None, courses=COURSES_SOLVE, strategy="CHANNEL",
          regra76_d1=None, regra76_nao_resolvido=None, papel_por_fiada=None,
          tolerancias_fisicas=None, regras_de_encontro=None):
    """Solve REAL das 34 paredes. A secao 74 e' ligada/desligada pela flag do
    PRODUTO (`CHANNEL_T_ROOM_PHYSICAL_TOLERANCE_ENABLED`), nao por monkeypatch:
    e' o mesmo caminho que o botao percorre no Revit.

    `regra76_d1` (None = o que o produto faz) liga/desliga a correcao D1 da
    regra 76 pela flag do PRODUTO (`CHANNEL_T_DEGRADED_L_ROOM_FROM_CONTACT_
    ENABLED`). Serve para reproduzir o motor ANTERIOR a' regra 76: com a D1, o
    contrafactual "sem a secao 74" resgata o no' 46 como L degradado, entao o
    efeito isolado da secao 74 so' aparece contra o motor sem a D1.

    `regra76_nao_resolvido` (None = produto) liga/desliga a regra 76.1 pela flag
    do PRODUTO (`CHANNEL_UNRESOLVED_JUNCTION_FILL_ENABLED`): compensador da
    escada de no' deixa de ser designado amarracao. So' classificacao - as
    pecas sao as mesmas.

    `papel_por_fiada` (None = produto) liga/desliga a secao 77 pela flag do
    PRODUTO (`CHANNEL_COURSE_AWARE_JUNCTION_ROLE_ENABLED`): papel funcional do
    encontro por fiada. Os casos historicos do snapshot (anteriores a' secao
    77) sao medidos com False; a variante `course_aware_junction_role` com True."""
    m, _ws = engine()
    # `tolerancias_fisicas` (None = produto) liga/desliga a secao 78 pela flag do
    # PRODUTO (`PHYSICAL_MODULATION_TOLERANCES_ENABLED`): tolerancias fisicas de
    # fechamento (30.8 + 51.13) em qualquer estrategia. Os casos HISTORICOS do
    # legado (anteriores a secao 78, quando so o CHANNEL as tinha) sao medidos
    # com False; motor antigo sem a flag -> ignorado.
    antes_78 = getattr(m, "PHYSICAL_MODULATION_TOLERANCES_ENABLED", None)
    if tolerancias_fisicas is not None and antes_78 is not None:
        m.PHYSICAL_MODULATION_TOLERANCES_ENABLED = bool(tolerancias_fisicas)
    # `regras_de_encontro` (None = produto) liga/desliga a secao 79 pela flag do
    # PRODUTO (`JUNCTION_PHYSICAL_RULES_ENABLED`): regras fisicas de encontro no
    # caminho sem reforco. Os casos HISTORICOS do legado sao medidos com False.
    antes_79 = getattr(m, "JUNCTION_PHYSICAL_RULES_ENABLED", None)
    if regras_de_encontro is not None and antes_79 is not None:
        m.JUNCTION_PHYSICAL_RULES_ENABLED = bool(regras_de_encontro)
    antes = m.CHANNEL_T_ROOM_PHYSICAL_TOLERANCE_ENABLED
    antes_d1 = m.CHANNEL_T_DEGRADED_L_ROOM_FROM_CONTACT_ENABLED
    antes_761 = m.CHANNEL_UNRESOLVED_JUNCTION_FILL_ENABLED
    antes_77 = getattr(m, "CHANNEL_COURSE_AWARE_JUNCTION_ROLE_ENABLED", None)
    if papel_por_fiada is not None and antes_77 is not None:
        m.CHANNEL_COURSE_AWARE_JUNCTION_ROLE_ENABLED = bool(papel_por_fiada)
    m.CHANNEL_T_ROOM_PHYSICAL_TOLERANCE_ENABLED = bool(physical_tolerance)
    if regra76_d1 is not None:
        m.CHANNEL_T_DEGRADED_L_ROOM_FROM_CONTACT_ENABLED = bool(regra76_d1)
    if regra76_nao_resolvido is not None:
        m.CHANNEL_UNRESOLVED_JUNCTION_FILL_ENABLED = bool(regra76_nao_resolvido)
    try:
        res = m.solve_building_blocks_all_courses(
            ctx["nodes"], ctx["walls"], ctx["e2n"], ctx["openings_per_wall"],
            catalog(geo), 0.0, courses,
            variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE,
            opening_reinforcement_strategy=strategy)
    finally:
        m.CHANNEL_T_ROOM_PHYSICAL_TOLERANCE_ENABLED = antes
        m.CHANNEL_T_DEGRADED_L_ROOM_FROM_CONTACT_ENABLED = antes_d1
        m.CHANNEL_UNRESOLVED_JUNCTION_FILL_ENABLED = antes_761
        if antes_77 is not None:
            m.CHANNEL_COURSE_AWARE_JUNCTION_ROLE_ENABLED = antes_77
        if antes_78 is not None:
            m.PHYSICAL_MODULATION_TOLERANCES_ENABLED = antes_78
        if antes_79 is not None:
            m.JUNCTION_PHYSICAL_RULES_ENABLED = antes_79
    res["num_courses"] = courses
    return res


def solve_on_fresh_context(geo, physical_tolerance, courses=COURSES_SOLVE, strategy="CHANNEL",
                           regra76_d1=None, regra76_nao_resolvido=None, papel_por_fiada=None,
                           tolerancias_fisicas=None, regras_de_encontro=None):
    """Solve sobre um grafo de nos NOVO - e' assim que se deve medir.

    O motor MUTA os nos durante o solve: a secao 72 grava nos proprios nos uma
    marca de decisao unica por planta (`_tie_parity_fill_done`) e a inversao de
    paridade aplicada. Reaproveitar o mesmo `ctx` entre configuracoes faria a
    busca de paridade rodar de verdade so' na PRIMEIRA e ser curto-circuitada nas
    seguintes - o que compararia coisas diferentes. Medido: com grafo novo por
    solve os hashes do corpus sao os mesmos, entao isto nao muda resultado
    nenhum; muda a validade do metodo.

    Devolve (ctx, res) porque a regua precisa do ctx que produziu o resultado.
    """
    ctx = build_context(geo)
    return ctx, solve(ctx, physical_tolerance, geo=geo, courses=courses, strategy=strategy,
                      regra76_d1=regra76_d1, regra76_nao_resolvido=regra76_nao_resolvido,
                      papel_por_fiada=papel_por_fiada, tolerancias_fisicas=tolerancias_fisicas,
                      regras_de_encontro=regras_de_encontro)


def hard_gates(res):
    sup = (res.get("physical_support") or {}).get("counts") or {}
    return {"collisions": len(res.get("collisions") or []),
            "non_modular": len(res.get("non_modular") or []),
            "unsupported": sup.get("UNSUPPORTED_BLOCK", 0) + sup.get("UNSUPPORTED_SMALL_BLOCK", 0),
            "opening_invasion": len(res.get("opening_invasions") or []),
            # REGRA 75 (2026-09-18): canaleta nunca exerce funcao de amarracao
            "channel_as_junction_bond": len(res.get("channel_as_junction_bond") or [])}


# ====================================================== REGUA DE COMPARACAO
# Daqui para baixo nao ha' decisao do motor - so' medida sobre a saida dele.
class _Axis(object):
    """Eixo ORIGINAL da parede (antes da extensao aos nos) - a regua comum."""

    def __init__(self, key, p0, p1):
        self.key, self.p0, self.p1 = key, p0, p1
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        self.L = math.hypot(dx, dy)
        self.u = (dx / self.L, dy / self.L)
        self.n = (-self.u[1], self.u[0])

    def t_of(self, x, y):
        return (x - self.p0[0]) * self.u[0] + (y - self.p0[1]) * self.u[1]

    def lat_of(self, x, y):
        return (x - self.p0[0]) * self.n[0] + (y - self.p0[1]) * self.n[1]


def axes(geo):
    return dict((w["key"], _Axis(w["key"], w["p0_cm"], w["p1_cm"])) for w in geo["walls"])


def junctions(geo, tol=NODE_TOL_CM):
    """{chave: [{t, kind, others}]} - encontros medidos entre os eixos
    ORIGINAIS. Geometria pura; nao usa nenhum campo do motor."""
    A = axes(geo)
    out = collections.defaultdict(list)
    for a in A.values():
        for b in A.values():
            if a is b:
                continue
            if abs(a.u[0] * b.u[0] + a.u[1] * b.u[1]) > 0.9:
                continue
            det = a.u[0] * (-b.u[1]) - a.u[1] * (-b.u[0])
            if abs(det) < 1e-9:
                continue
            rx, ry = b.p0[0] - a.p0[0], b.p0[1] - a.p0[1]
            ta = (rx * (-b.u[1]) - ry * (-b.u[0])) / det
            tb = (a.u[0] * ry - a.u[1] * rx) / det
            if not (-tol <= ta <= a.L + tol and -tol <= tb <= b.L + tol):
                continue
            px, py = a.p0[0] + a.u[0] * ta, a.p0[1] + a.u[1] * ta
            tc = max(0.0, min(b.L, b.t_of(px, py)))
            qx, qy = b.p0[0] + b.u[0] * tc, b.p0[1] + b.u[1] * tc
            if math.hypot(px - qx, py - qy) > tol:
                continue
            a_passa = (ta > tol) and (ta < a.L - tol)
            b_passa = (tb > tol) and (tb < b.L - tol)
            kind = "CROSS" if (a_passa and b_passa) else ("TEE" if (a_passa or b_passa) else "CORNER")
            out[a.key].append({"t": ta, "kind": kind, "other": b.key})
    for key in out:
        out[key].sort(key=lambda d: d["t"])
        fundidos = []
        for d in out[key]:
            if fundidos and abs(fundidos[-1]["t"] - d["t"]) <= 5.0:
                fundidos[-1]["others"].append(d["other"])
                if d["kind"] == "CROSS" or len(fundidos[-1]["others"]) >= 2:
                    fundidos[-1]["kind"] = "CROSS"
                continue
            fundidos.append({"t": d["t"], "kind": d["kind"], "others": [d["other"]]})
        out[key] = fundidos
    return out


def openings_by_wall(geo):
    """{chave: [(t_lo, t_hi, sill, head)]} pelo vao real, no eixo ORIGINAL."""
    A = axes(geo)
    out = collections.defaultdict(list)
    for o in geo["openings"]:
        cx, cy = o["center_cm"]
        melhor = None
        for a in A.values():
            lat = abs(a.lat_of(cx, cy))
            if lat > 10.0:
                continue
            tc = a.t_of(cx, cy)
            if tc < -5 or tc > a.L + 5:
                continue
            if melhor is None or lat < melhor[0]:
                melhor = (lat, a, tc)
        if melhor is None:
            continue
        _lat, a, tc = melhor
        out[a.key].append((tc - o["width_cm"] / 2.0, tc + o["width_cm"] / 2.0,
                           o["sill_cm"], o["head_cm"]))
    for key in out:
        out[key].sort()
    return out


def _dist_span_ponto(lo, hi, t):
    if lo <= t <= hi:
        return 0.0
    return min(abs(lo - t), abs(hi - t))


def jambas_ativas(O, key, course):
    z = 20.0 * course + 10.0
    fora = []
    for tl, th, sill, head in O.get(key, ()):
        if sill - 0.5 <= z <= head + 0.5:
            fora += [tl, th]
    return fora


def zona(lo, hi, axis, nos, jambas):
    """END_ZONE / OPENING_ZONE / JUNCTION_ZONE / CENTER_JUNCTION_ZONE /
    FREE_MID_WALL - classificacao GEOMETRICA da peca, igual para humano e
    solver."""
    d_end = max(0.0, min(abs(lo - 0.0), abs(axis.L - hi)))
    if d_end <= ZONA_CM:
        return "END_ZONE"
    if jambas and min(_dist_span_ponto(lo, hi, t) for t in jambas) <= ZONA_CM:
        return "OPENING_ZONE"
    perto = [n for n in nos if _dist_span_ponto(lo, hi, n["t"]) <= ZONA_CM]
    if perto:
        n = min(perto, key=lambda n: _dist_span_ponto(lo, hi, n["t"]))
        if n["t"] <= PERTO_DA_PONTA or n["t"] >= axis.L - PERTO_DA_PONTA:
            return "JUNCTION_ZONE"
        return "CENTER_JUNCTION_ZONE"
    return "FREE_MID_WALL"


def solver_rows(ctx, res, geo, max_course=COURSES_RULER):
    """Pecas do solver na regua comum: (chave, fiada, codigo, lo, hi) medidas
    sobre o eixo ORIGINAL da parede."""
    A = axes(geo)
    saida = []
    for ci, cands in (res.get("course_candidates") or {}).items():
        if ci >= max_course:
            continue
        for c in cands:
            wi = c.get("wall_idx")
            if wi is None:
                continue
            key = ctx["keys"][wi]
            axis = A.get(key)
            if axis is None:
                continue
            code = SOLVER_CODE.get(c["logical_code"], c["logical_code"])
            o = c["origin_world"]
            cx, cy = o.X * CM_PER_FT, o.Y * CM_PER_FT
            dx, dy = ctx.get("translate", (0.0, 0.0))
            length = float(c.get("length_cm") or 0.0)
            t = axis.t_of(cx - dx, cy - dy)
            saida.append((key, ci, code, t - length / 2.0, t + length / 2.0))
    return saida


def wall_counts(rows, geo, key):
    """Composicao de UMA parede na regua: contagem por codigo + as zonas do
    B34 (`Z_<zona>`), exatamente as chaves que a divergencia consome."""
    A = axes(geo)
    J = junctions(geo)
    O = openings_by_wall(geo)
    axis, nos = A[key], J.get(key, [])
    contagem = collections.Counter()
    for k, course, code, lo, hi in rows:
        if k != key:
            continue
        contagem[code] += 1
        if code == "B34":
            contagem["Z_" + zona(lo, hi, axis, nos, jambas_ativas(O, key, course))] += 1
    return dict(contagem)


def divergence(H, S):
    """Distancia explicavel entre duas composicoes da MESMA parede.

    Definicao (versionada aqui para poder ser auditada):
        tot_h = pecas humanas na parede (chaves Z_ nao contam)
        comp  = soma de |S[k] - H[k]| sobre B39/B34/B54/B19/C09/C04
        livre = |S[Z_FREE_MID_WALL] - H[Z_FREE_MID_WALL]|
        esp   = |(S[C09]+S[C04]) - (H[C09]+H[C04])|
        div   = 100 * comp / tot_h + 2 * livre + 1 * esp
    """
    tot_h = sum(v for k, v in H.items() if not k.startswith("Z_")) or 1
    comp = sum(abs(S.get(k, 0) - H.get(k, 0)) for k in BLOCOS + ESPECIAIS)
    livre = abs(S.get("Z_FREE_MID_WALL", 0) - H.get("Z_FREE_MID_WALL", 0))
    esp = abs(sum(S.get(k, 0) for k in ESPECIAIS) - sum(H.get(k, 0) for k in ESPECIAIS))
    return {"div": round(100.0 * comp / tot_h + 2.0 * livre + 1.0 * esp, 1),
            "comp_delta": comp, "free_mid_delta": livre, "esp_delta": esp,
            "human_pieces": tot_h}


# ======================================================= snapshot normalizado
SNAPSHOT_NORMALIZATION = "S74_SNAPSHOT_V1"


def normalized_snapshot(ctx, res):
    """Conjunto FISICO de pecas, normalizado para ser comparavel entre
    execucoes e entre maquinas.

    S74_SNAPSHOT_V1: uma linha por peca,
        "<fiada>|<chave da parede>|<codigo>|<x>|<y>|<dx>|<dy>|<comprimento>|<espelhada>"
    com x/y em cm arredondados a 4 casas, direcao a 6 casas e comprimento a 3;
    linhas ordenadas. Nao entra nenhum identificador de execucao, tempo,
    ponteiro ou indice de lista - so' fisica.
    """
    linhas = []
    for ci, cands in (res.get("course_candidates") or {}).items():
        for c in cands:
            wi = c.get("wall_idx")
            key = ctx["keys"][wi] if wi is not None else "-"
            o, xd = c["origin_world"], c["x_dir"]
            dx, dy = ctx.get("translate", (0.0, 0.0))
            linhas.append("%d|%s|%s|%.4f|%.4f|%.6f|%.6f|%.3f|%d" % (
                ci, key, c["logical_code"],
                o.X * CM_PER_FT - dx, o.Y * CM_PER_FT - dy,
                float(xd.X), float(xd.Y), float(c.get("length_cm") or 0.0),
                1 if c.get("mirrored") else 0))
    linhas.sort()
    return linhas


def snapshot_sha256(linhas):
    return hashlib.sha256("\n".join(linhas).encode("utf-8")).hexdigest()
