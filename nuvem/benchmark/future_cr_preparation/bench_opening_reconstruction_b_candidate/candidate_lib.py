# -*- coding: utf-8 -*-
"""CR-B / CANDIDATO — biblioteca comum.

NAO altera nada em `nuvem/benchmark/projects/**`, nao altera constante de
producao, nao altera o solver. Le' o gabarito oficial em modo LEITURA e
produz um CANDIDATO em diretorio isolado.

Procedencia do metodo: o criterio estrutural C1 e o embrulho de
`split_axis_into_walls` vem da branch diagnostica
`claude/reconciliacao-gabarito-aberturas-uynv0q`
(`bench_opening_reconstruction_b/projection_split.py`, §5.2/§6.2 do
relatorio de reconciliacao). Aqui eles sao reusados sem alteracao de
semantica; o que e' novo e' a materializacao do candidato em arquivo, o
mapeamento de identidade fisica e os invariantes por bloco.
"""
import hashlib
import json
import math
import os
import sys

ROOT = os.environ.get("REPO_ROOT", "/home/user/MeuBotao.pushbutton")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from nuvem.benchmark.extract import reconstruct  # noqa: E402

PROJECTS = ["torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"]
PROJECTS_DIR = os.path.join(ROOT, "nuvem", "benchmark", "projects")

# Tolerancia de CLASSIFICACAO (decide se a jamba coincide com a face de uma
# perpendicular). NUNCA vira coordenada gravada.
FACE_TOL_CM = 1.0
PERP_REACH_CM = 60.0

CANDIDATE_VERSION = "cand-B-2026-09-07.1"


# ------------------------------------------------------------------ geom
def axis(w):
    sx, sy = w["start_cm"]
    ex, ey = w["end_cm"]
    n = math.hypot(ex - sx, ey - sy)
    return (sx, sy), ((ex - sx) / n, (ey - sy) / n)


def pr(o, d, p):
    """(t, s) de `p` no referencial (origem `o`, direcao `d`)."""
    dx, dy = p[0] - o[0], p[1] - o[1]
    return dx * d[0] + dy * d[1], -dx * d[1] + dy * d[0]


def stable_key(wall):
    """Identidade FISICA de uma parede: as duas pontas em coordenada de
    mundo, ordenadas, arredondadas a 0,01cm. Imune a renumeracao `W0xx`."""
    a = (round(wall["start_cm"][0], 2), round(wall["start_cm"][1], 2))
    b = (round(wall["end_cm"][0], 2), round(wall["end_cm"][1], 2))
    lo, hi = (a, b) if a <= b else (b, a)
    return "S%.2f,%.2f>%.2f,%.2f" % (lo[0], lo[1], hi[0], hi[1])


def opening_key(wall, op):
    """Identidade FISICA de uma abertura: as duas jambas em mundo."""
    o, d = axis(wall)
    lo = (o[0] + d[0] * op["t_start_cm"], o[1] + d[1] * op["t_start_cm"])
    hi = (o[0] + d[0] * op["t_end_cm"], o[1] + d[1] * op["t_end_cm"])
    a = (round(lo[0], 2), round(lo[1], 2))
    b = (round(hi[0], 2), round(hi[1], 2))
    x, y = (a, b) if a <= b else (b, a)
    return "O%.2f,%.2f>%.2f,%.2f" % (x[0], x[1], y[0], y[1])


def block_key(b):
    """Identidade FISICA de um bloco humano: tipo + centro + cota."""
    return "%s|%.3f|%.3f|%.3f" % (b.get("type_name"), b["center_cm"][0],
                                  b["center_cm"][1], b["z_cm"])


# ----------------------------------------------------------- round-trip
def dump_from_reference(ref):
    """Dump sintetico a partir do proprio gabarito (round-trip provado
    identico em `roundtrip_probe.py` da branch de reconciliacao)."""
    types, index_of, instances = [], {}, []
    blocks = []
    for wall in ref.get("walls") or []:
        for row in wall.get("rows") or []:
            blocks.extend(row.get("blocks") or [])
    blocks.extend(ref.get("orphan_blocks") or [])
    for b in blocks:
        key = (b["type_name"], b["family"], b["length_cm"], b["height_cm"],
               b["width_cm"])
        if key not in index_of:
            index_of[key] = len(types)
            types.append({"index": len(types), "type_name": b["type_name"],
                          "family": b["family"], "length_cm": b["length_cm"],
                          "height_cm": b["height_cm"],
                          "width_cm": b["width_cm"]})
        instances.append([index_of[key], b["center_cm"][0], b["center_cm"][1],
                          b["z_cm"], b["rotation_deg"], bool(b["mirrored"])])
    return {"types": types, "instances": instances}


# ------------------------------------------------------------ criterio
def c1_cases(project):
    """Vaos cujas DUAS jambas coincidem com a face INTERNA de uma parede
    perpendicular (reserva de no' nos dois lados). SEM limiar de largura.

    Devolve tambem QUAIS perpendiculares confirmaram cada jamba - e' o que
    a analise T->L usa como participantes do no'."""
    hits = []
    for host in project["walls"]:
        o, d = axis(host)
        for op in host.get("openings") or []:
            lo_perp, hi_perp = [], []
            for w in project["walls"]:
                if w["id"] == host["id"]:
                    continue
                o2, d2 = axis(w)
                if abs(d2[0] * d[0] + d2[1] * d[1]) > 0.05:
                    continue
                t0, s0 = pr(o, d, w["start_cm"])
                t1, s1 = pr(o, d, w["end_cm"])
                if not (min(s0, s1) - PERP_REACH_CM <= 0 <= max(s0, s1) + PERP_REACH_CM):
                    continue
                tc = (t0 + t1) / 2.0
                half = (w.get("thickness_cm") or 14.0) / 2.0
                if abs((tc + half) - op["t_start_cm"]) <= FACE_TOL_CM:
                    lo_perp.append({"id": w["id"], "stable_key": stable_key(w),
                                    "t_centro": round(tc, 3),
                                    "residuo_cm": round((tc + half) - op["t_start_cm"], 4)})
                if abs((tc - half) - op["t_end_cm"]) <= FACE_TOL_CM:
                    hi_perp.append({"id": w["id"], "stable_key": stable_key(w),
                                    "t_centro": round(tc, 3),
                                    "residuo_cm": round((tc - half) - op["t_end_cm"], 4)})
            if lo_perp and hi_perp:
                hits.append({
                    "host_id": host["id"],
                    "host_stable_key": stable_key(host),
                    "opening_key": opening_key(host, op),
                    "kind": op.get("kind"),
                    "confidence": op.get("confidence"),
                    "source_element_id": op.get("source_element_id"),
                    "t_range": [op["t_start_cm"], op["t_end_cm"]],
                    "z_range": [op.get("z_start_cm"), op.get("z_end_cm")],
                    "largura_cm": round(op["t_end_cm"] - op["t_start_cm"], 2),
                    "xy_lo": [round(o[0] + d[0] * op["t_start_cm"], 3),
                              round(o[1] + d[1] * op["t_start_cm"], 3)],
                    "xy_hi": [round(o[0] + d[0] * op["t_end_cm"], 3),
                              round(o[1] + d[1] * op["t_end_cm"], 3)],
                    "perp_lo": lo_perp, "perp_hi": hi_perp,
                })
    return hits


# --------------------------------------------------------- construcao
def build_with_splits(dump, project_id, cortes_xy, metadata=None):
    """`build_project` com `split_axis_into_walls` embrulhado para cortar
    tambem nos intervalos de `cortes_xy`. Nenhuma constante alterada."""
    original = reconstruct.split_axis_into_walls

    def wrapped(group):
        walls = original(group)
        out = []
        for w in walls:
            o = w["start_cm"]
            d = w["direction"]
            pontos = []
            for lo_xy, hi_xy in cortes_xy:
                tlo, slo = pr(o, d, lo_xy)
                thi, shi = pr(o, d, hi_xy)
                if abs(slo) > 2.0 or abs(shi) > 2.0:
                    continue
                a, b = min(tlo, thi), max(tlo, thi)
                comp = math.hypot(w["end_cm"][0] - o[0], w["end_cm"][1] - o[1])
                if a > 1.0 and b < comp - 1.0:
                    pontos.append((a, b))
            if not pontos:
                out.append(w)
                continue
            pontos.sort()
            restantes = list(w["blocks"])
            fronteiras = [-1e9] + [p for pair in pontos for p in pair] + [1e9]
            for i in range(0, len(fronteiras) - 1, 2):
                lo, hi = fronteiras[i], fronteiras[i + 1]
                bl = []
                for b in restantes:
                    tc, _s = pr(o, d, b["center_cm"])
                    if lo <= tc <= hi:
                        bl.append(b)
                if not bl:
                    continue
                ext = []
                for b in bl:
                    tc, _s = pr(o, d, b["center_cm"])
                    ext.append((tc - b["length_cm"] / 2.0,
                                tc + b["length_cm"] / 2.0))
                t_lo = min(e[0] for e in ext)
                t_hi = max(e[1] for e in ext)
                if t_hi - t_lo < reconstruct.MIN_WALL_LENGTH_CM:
                    continue
                out.append({
                    "start_cm": (o[0] + d[0] * t_lo, o[1] + d[1] * t_lo),
                    "end_cm": (o[0] + d[0] * t_hi, o[1] + d[1] * t_hi),
                    "direction": d, "blocks": bl, "t_offset": t_lo,
                })
        return out

    reconstruct.split_axis_into_walls = wrapped
    try:
        return reconstruct.build_project(dump, project_id,
                                         source="revit_reference",
                                         metadata=metadata)
    finally:
        reconstruct.split_axis_into_walls = original


# ---------------------------------------------------------------- io
def load_reference(proj):
    with open(os.path.join(PROJECTS_DIR, proj, "reference.json"),
              encoding="utf-8") as h:
        return json.load(h)


def load_input(proj):
    with open(os.path.join(PROJECTS_DIR, proj, "input.json"),
              encoding="utf-8") as h:
        return json.load(h)


def write_json(path, payload):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, "w", encoding="utf-8") as h:
        json.dump(payload, h, ensure_ascii=False, indent=1, sort_keys=True)
    return path


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def all_blocks(project):
    for w in project.get("walls") or []:
        for r in w.get("rows") or []:
            for b in r.get("blocks") or []:
                yield w, r, b


def build_project_plain(dump, project_id, metadata=None):
    """`build_project` sem nenhuma injecao — o round-trip de controle."""
    return reconstruct.build_project(dump, project_id,
                                     source="revit_reference",
                                     metadata=metadata)
