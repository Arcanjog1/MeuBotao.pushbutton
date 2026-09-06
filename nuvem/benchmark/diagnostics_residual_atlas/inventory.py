# -*- coding: utf-8 -*-
"""INVENTARIO FISICO dos achados (item 4 da CR) + assinaturas causais
iniciais (item 5). Le' o STATE_CURRENT gravado por run_state_current.py e
o `run.pkl` (objetos vivos do solver) e grava, por projeto:

    <SHORT>/inventory.json       um registro enriquecido por achado
    <SHORT>/wall_context.json    contexto geometrico de TODAS as paredes
    <SHORT>/compositions/<Wid>.txt  composicao solver x humano fiada a fiada
    inventory_summary.json       agregados por codigo / assinatura

Nunca reimplementa validador: os achados sao os dos validadores oficiais;
aqui so' se acrescenta CONTEXTO (no', abertura, banda, dono da peca,
placement_reason, composicao humana no mesmo trecho).
"""
import json
import os
import sys
from collections import Counter, defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas_lib as al  # noqa: E402

TOL_JOINT = 1.5


def _blocks_index(result_project):
    idx = {}
    for wall in result_project["walls"]:
        for row in wall["rows"]:
            for block in row["blocks"]:
                idx[block["id"]] = block
    return idx


def _row_joints(items, max_gap=5.0):
    joints = []
    for i in range(len(items) - 1):
        gap = items[i + 1]["t0"] - items[i]["t1"]
        if gap > max_gap:
            continue
        joints.append({"t": round((items[i]["t1"] + items[i + 1]["t0"]) / 2.0, 2),
                       "left": items[i], "right": items[i + 1]})
    return joints


def _human_rows(reference_wall, solver_wall):
    rows = {}
    if reference_wall is None:
        return rows
    for row in reference_wall.get("rows") or []:
        rows[row["row"]] = al.human_items_on_solver_axis(solver_wall, reference_wall, row["row"])
    return rows


def _fmt_items(items):
    return " ".join("[{0}-{1} {2}{3}]".format(int(round(it["t0"])), int(round(it["t1"])), it["code"],
                                              "" if it.get("is_own", True) else "*")
                    for it in items)


def _scope_outside(project_id):
    path = os.path.join(al.project_paths(project_id)["dir"], "scope_summary.json")
    if not os.path.isfile(path):
        return set()
    return set(al.read_json(path).get("outside_wall_ids") or [])


def build(project_id):
    short = al.SHORT[project_id]
    run = al.cached_run(project_id)
    state = al.load_state(short)
    result = state["result"]
    reference = al.load_reference(project_id)
    idx_to_id, id_to_idx, ambiguous = al.wall_maps(run, result)
    pairs = state["wall_pairs"]["solver_to_human"]
    ref_by_id = al.reference_wall_by_id(reference)
    res_by_id = al.result_wall_by_id(result)
    outside = _scope_outside(project_id)
    npi = al.node_pieces(run)
    contexts = {}
    for wall_idx in range(len(run["walls_to_create"])):
        ctx = al.wall_context(run, wall_idx, npi)
        ctx["wall_id"] = idx_to_id.get(wall_idx)
        ctx["human_wall"] = pairs.get(ctx["wall_id"])
        ctx["human_overlaps"] = None
        ctx["in_scope"] = ctx["wall_id"] not in outside
        contexts[wall_idx] = ctx
    blocks = _blocks_index(result)

    # composicoes por parede (solver x humano) - cache
    comp_dir = al.out_path(short, "compositions", "x")
    comp_dir = os.path.dirname(comp_dir)
    solver_rows_cache, human_rows_cache = {}, {}

    def solver_rows(wall_idx):
        if wall_idx not in solver_rows_cache:
            rows = {}
            for ci in range(run["num_courses"]):
                rows[ci] = al.wall_course_items(run, wall_idx, ci, include_secondary=True)
            solver_rows_cache[wall_idx] = rows
        return solver_rows_cache[wall_idx]

    bundle = al.Bundle(project_id)

    def human_rows(wall_idx):
        if wall_idx not in human_rows_cache:
            rows = {}
            for ci in range(run["num_courses"]):
                items = bundle.human_row(wall_idx, ci)
                if items is not None:
                    rows[ci] = items
            human_rows_cache[wall_idx] = rows
        return human_rows_cache[wall_idx]

    records = []
    for f in state["findings"]:
        wid = f.get("wall")
        wall_idx = id_to_idx.get(wid) if wid else None
        rec = {
            "project": short, "code": f["code"], "level": f["level"], "severity": f["severity"],
            "wall_id": wid, "wall_idx": wall_idx, "detail": f.get("detail"),
        }
        if wall_idx is None:
            rec["ctx"] = None
            records.append(rec)
            continue
        ctx = contexts[wall_idx]
        rec.update({
            "key": ctx["key"], "human_wall": ctx["human_wall"], "in_scope": ctx["in_scope"],
            "orientation": ctx["orientation"], "length_cm": ctx["length_cm"],
            "thickness_cm": ctx["thickness_cm"],
            "end0": ctx["ends"][0]["kind"] + ("_DEGRADED" if ctx["ends"][0].get("degraded") else ""),
            "end1": ctx["ends"][1]["kind"] + ("_DEGRADED" if ctx["ends"][1].get("degraded") else ""),
            "n_midspan": len(ctx["midspan_nodes"]),
            "midspan_kinds": [m["kind"] + ("_DEG" if m["degraded"] else "") for m in ctx["midspan_nodes"]],
            "n_openings": len(ctx["openings"]),
            "opening_kinds": [o["kind"] for o in ctx["openings"]],
        })
        # fiada(s)
        rows = []
        for k in ("row", "row_a", "row_b"):
            if f.get(k) is not None:
                rows.append(int(f[k]))
        if f.get("rows"):
            rows.extend(int(r) for r in f["rows"])
        rec["rows"] = sorted(set(rows))
        if rec["rows"]:
            r0 = rec["rows"][0]
            rec["course_letter"] = al.course_letter(r0)
            rec["band"] = al.band_of_course(run, r0)
            rec["openings_active"] = [o["kind"] for o in al.openings_active_in_course(ctx, run, r0)]
        # posicao t do achado
        t = None
        if f.get("joint_t_cm") is not None:
            t = float(f["joint_t_cm"])
        elif f.get("t_cm") is not None and not isinstance(f["t_cm"], list):
            t = float(f["t_cm"])
        elif f.get("t_cm") and isinstance(f["t_cm"], list):
            t = (float(f["t_cm"][0]) + float(f["t_cm"][1])) / 2.0
        elif f.get("gap_t_cm"):
            t = (float(f["gap_t_cm"][0]) + float(f["gap_t_cm"][1])) / 2.0
        elif f.get("block_t_cm"):
            t = (float(f["block_t_cm"][0]) + float(f["block_t_cm"][1])) / 2.0
        elif f.get("point_cm") is not None and f.get("junction_type"):
            # junction: t do ponto no eixo desta parede
            p0 = ctx["start_cm"]
            direction, _l = al.model.direction_of(ctx["start_cm"], ctx["end_cm"])
            t, _s = al.model.axial_coordinates(f["point_cm"], p0, direction)
        rec["t_cm"] = None if t is None else round(t, 2)
        if t is not None:
            feat = al.nearest_feature(ctx, t)
            rec["nearest_feature"] = feat[0]
            rec["nearest_feature_dist_cm"] = feat[1]
            rec["t_from_start_cm"] = round(t, 2)
            rec["t_from_end_cm"] = round(ctx["length_cm"] - t, 2)
        # pecas envolvidas
        reasons, codes, owners = [], [], []
        for bid in (f.get("blocks") or []):
            b = blocks.get(bid)
            if b is None:
                continue
            reasons.append(b.get("placement_reason"))
            codes.append(b.get("code"))
            owners.append(b.get("secondary_wall_id"))
        rec["block_reasons"] = reasons
        rec["block_codes"] = codes or f.get("codes") or []
        # humano no mesmo lugar
        hr = human_rows(wall_idx)
        rec["human_available"] = bool(hr)
        if hr and t is not None and rec["rows"]:
            hits = {}
            for r in rec["rows"][:2]:
                items = hr.get(r) or []
                js = _row_joints(items)
                near = [j for j in js if abs(j["t"] - t) <= TOL_JOINT]
                cover = [it for it in items if it["t0"] - 0.5 <= t <= it["t1"] + 0.5]
                hits[r] = {"joint_here": bool(near),
                           "covered_by": [it["code"] for it in cover],
                           "row_empty": not items}
            rec["human_at_t"] = hits
            if f["code"] == "PRISM_CONTINUOUS_JOINT" and len(rec["rows"]) == 2:
                ra, rb = rec["rows"]
                ja = hits.get(ra, {}).get("joint_here")
                jb = hits.get(rb, {}).get("joint_here")
                if ja and jb:
                    rec["human_verdict"] = "HUMAN_HAS_SAME_CONTINUOUS_JOINT"
                elif ja or jb:
                    rec["human_verdict"] = "HUMAN_JOINT_IN_ONE_ROW_ONLY"
                elif hits.get(ra, {}).get("row_empty") or hits.get(rb, {}).get("row_empty"):
                    rec["human_verdict"] = "HUMAN_ROW_EMPTY"
                else:
                    rec["human_verdict"] = "HUMAN_NO_JOINT_HERE"
        records.append(rec)

    # composicoes para paredes com achados de nivel 1 (e todas as com par humano)
    written = 0
    for wall_idx, ctx in contexts.items():
        wid = ctx["wall_id"]
        lines = ["# {0} {1} idx={2} human={3} len={4} thick={5} orient={6}".format(
            short, wid, wall_idx, ctx["human_wall"], ctx["length_cm"], ctx["thickness_cm"], ctx["orientation"])]
        lines.append("# end0: {0}  end1: {1}".format(json.dumps(al._sanitize(ctx["ends"][0]))[:400],
                                                    json.dumps(al._sanitize(ctx["ends"][1]))[:400]))
        lines.append("# midspan: {0}".format(json.dumps(al._sanitize(ctx["midspan_nodes"]))[:600]))
        lines.append("# openings: {0}".format(json.dumps(ctx["openings"])))
        sr = solver_rows(wall_idx)
        hr = human_rows(wall_idx)
        for ci in range(run["num_courses"]):
            lines.append("r{0:02d} {1} band{2} S: {3}".format(
                ci, al.course_letter(ci), al.band_of_course(run, ci), _fmt_items(sr.get(ci) or [])))
            if hr:
                lines.append("        H: {0}".format(_fmt_items(hr.get(ci) or [])))
        with open(os.path.join(comp_dir, "{0}.txt".format(wid)), "w", encoding="utf-8") as h:
            h.write("\n".join(lines) + "\n")
        written += 1

    al.write_json(al.out_path(short, "inventory.json"), records)
    al.write_json(al.out_path(short, "wall_context.json"), contexts)
    return records, contexts, ambiguous


def summarize(records):
    by_code = Counter(r["code"] for r in records)
    by_code_scope = Counter((r["code"], r.get("in_scope", True)) for r in records)
    by_code_human = Counter((r["code"], r.get("human_verdict")) for r in records if r.get("human_verdict"))
    by_code_feat = Counter((r["code"], r.get("nearest_feature")) for r in records if r.get("nearest_feature"))
    by_code_reason = Counter((r["code"], tuple(sorted(set(str(x) for x in r.get("block_reasons") or [])))) for r in records)
    walls_by_code = defaultdict(Counter)
    for r in records:
        walls_by_code[r["code"]][r.get("wall_id")] += 1
    return {
        "by_code": dict(by_code),
        "by_code_in_scope": {"{0}|{1}".format(k[0], k[1]): v for k, v in by_code_scope.items()},
        "by_code_human_verdict": {"{0}|{1}".format(k[0], k[1]): v for k, v in by_code_human.items()},
        "by_code_nearest_feature": {"{0}|{1}".format(k[0], k[1]): v for k, v in by_code_feat.items()},
        "by_code_block_reasons": {"{0}|{1}".format(k[0], "+".join(k[1])): v for k, v in by_code_reason.items()},
        "top_walls_by_code": {code: c.most_common(12) for code, c in walls_by_code.items()},
    }


def main(argv=None):
    ids = al.PROJECT_IDS if not argv else tuple(argv)
    summary = {}
    for pid in ids:
        records, contexts, ambiguous = build(pid)
        s = summarize(records)
        s["ambiguous_wall_maps"] = ambiguous
        summary[al.SHORT[pid]] = s
        print("==", al.SHORT[pid], "findings", len(records), "walls", len(contexts))
        for k, v in sorted(s["by_code"].items()):
            print("   {0:34s} {1:6d}".format(k, v))
    al.write_json(al.out_path("inventory_summary.json"), summary)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
