# -*- coding: utf-8 -*-
"""Escada de escala do solver sobre a geometria REAL de um projeto de teste.

Missao claude/revit-scale-autofix: descobrir em que ponto, ao sair da bancada
de 2 paredes, o fluxo deixa de funcionar - e qual e' a MENOR diferenca que
transforma PASS em FAIL.

Roda FORA do Revit, em CPython 3, com os dubles de tests/revit_stubs.py -
mesma semantica de `/` (divisao real) do engine CPython do pyRevit que executa
o botao em producao. Os eixos vem de um JSON exportado do Revit pelo PROPRIO
pipeline do plugin (find_wall_pairs), nunca de um algoritmo improvisado aqui.

Nada neste arquivo altera regra fisica, tolerancia, baseline ou threshold.
"""

import argparse
import json
import os
import sys
import time
import traceback
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def _find_tests_dir(start):
    d = start
    for _ in range(8):
        cand = os.path.join(d, "tests", "load_script.py")
        if os.path.isfile(cand):
            return os.path.join(d, "tests")
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    raise RuntimeError("nao achei tests/load_script.py a partir de " + start)


REPO_TESTS = os.environ.get("SCALE_BENCH_TESTS") or _find_tests_dir(HERE)
if REPO_TESTS not in sys.path:
    sys.path.insert(0, REPO_TESTS)

import load_script  # noqa: E402

m = load_script.load()
import solver_bench as sb  # noqa: E402  (reusa o CATALOG real do projeto)

CATALOG = sb.CATALOG
XYZ = m.XYZ
Line = m.Line
F2CM = 30.48


# ----------------------------------------------------------------- entrada
def load_axes(path):
    with open(path, "r") as fh:
        data = json.load(fh)
    axes = []
    for a in sorted(data["axes"], key=lambda x: x["i"]):
        p0 = XYZ(*[float(v) for v in a["p0"]])
        p1 = XYZ(*[float(v) for v in a["p1"]])
        axes.append((Line.CreateBound(p0, p1), float(a["thickness_ft"]),
                     (bool(a["locks"][0]), bool(a["locks"][1]))))
    meta = {
        "base_z_abs": float(data["base_z_abs_ft"]),
        "wall_height_ft": float(data["wall_height_ft"]),
        "num_courses": int(data["num_courses"]),
        "openings_count": int(data.get("openings_count", 0)),
        "source_doc": data.get("source_doc"),
    }
    return axes, meta


def phys_key(line, thickness_ft):
    """Identidade FISICA estavel de um eixo - nunca indice/W0xx/ElementId.

    Extremos arredondados em 0,1cm e ordenados, entao inverter os pontos
    (reverse endpoints) ou reordenar a coleta devolve a MESMA chave.
    """
    p = line.GetEndPoint(0)
    q = line.GetEndPoint(1)
    a = (round(p.X * F2CM, 1), round(p.Y * F2CM, 1))
    b = (round(q.X * F2CM, 1), round(q.Y * F2CM, 1))
    if b < a:
        a, b = b, a
    return "%.1f,%.1f->%.1f,%.1f@%.1fcm" % (a[0], a[1], b[0], b[1],
                                            round(thickness_ft * F2CM, 1))


# ------------------------------------------------------- selecao de subsets
def build_adjacency(axes):
    """Adjacencia entre eixos por NO compartilhado, usando o grafo real."""
    walls, jmap = m.extend_wall_ends_to_junctions(list(axes), m.JUNCTION_FACE_SEARCH_FT)
    nodes, _e2n = m.build_wall_graph(walls, jmap)
    adj = defaultdict(set)
    for n in nodes:
        involved = set()
        for key in ("main_wall_idx", "incoming_wall_idx", "neighbor_wall_idx"):
            v = n.get(key)
            if isinstance(v, int):
                involved.add(v)
        for v in (n.get("crossing_walls") or []):
            if isinstance(v, int):
                involved.add(v)
        for arm in (n.get("arms") or []):
            v = arm.get("wall_idx") if isinstance(arm, dict) else None
            if isinstance(v, int):
                involved.add(v)
        for a in involved:
            for b in involved:
                if a != b:
                    adj[a].add(b)
    return adj, nodes


def growth_order(axes, adj, seed):
    """Ordem de crescimento CONEXA a partir de um eixo semente (BFS).

    Crescer por conexidade e' o que reproduz a escalada real: cada parede
    acrescentada traz encontros novos, em vez de um conjunto solto sem no'.
    Empates resolvidos por chave fisica, para a ordem ser determinista e
    independente da ordem de coleta.
    """
    order = [seed]
    seen = {seed}
    frontier = sorted(adj.get(seed, ()), key=lambda i: phys_key(*axes[i][:2]))
    while frontier:
        nxt = frontier.pop(0)
        if nxt in seen:
            continue
        seen.add(nxt)
        order.append(nxt)
        for nb in sorted(adj.get(nxt, ()), key=lambda i: phys_key(*axes[i][:2])):
            if nb not in seen and nb not in frontier:
                frontier.append(nb)
    # eixos desconexos entram no fim, por chave fisica
    rest = sorted((i for i in range(len(axes)) if i not in seen),
                  key=lambda i: phys_key(*axes[i][:2]))
    return order + rest


# ------------------------------------------------------------------ rodada
def run_subset(axes, idxs, meta, label="", want_audit=True, timeout_note=None):
    """Executa o caminho real: extend -> grafo -> aberturas -> solve ->
    preflight -> auditoria de amarracao. Devolve um dicionario de medida."""
    sub = [axes[i] for i in idxs]
    out = {"label": label, "n_in": len(idxs),
           "keys": [phys_key(*axes[i][:2]) for i in idxs]}
    t0 = time.time()
    try:
        walls, jmap = m.extend_wall_ends_to_junctions(list(sub), m.JUNCTION_FACE_SEARCH_FT)
        nodes, e2n = m.build_wall_graph(walls, jmap)
        out["t_graph"] = time.time() - t0
        kinds = defaultdict(int)
        for n in nodes:
            kinds[n["kind"]] += 1
        out["kinds"] = dict(kinds)
        out["n_nodes"] = len(nodes)

        od = {"clamped_opening_count": 0, "opening_off_center_count": 0,
              "opening_center_gap_max_ft": 0.0, "unassigned_openings": []}
        opw = m.assign_openings_to_walls(walls, [], od)

        t1 = time.time()
        res = m.solve_building_blocks_all_courses(
            nodes, walls, e2n, opw, CATALOG, meta["base_z_abs"], meta["num_courses"],
            variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
        out["t_solve"] = time.time() - t1
        res["num_courses"] = meta["num_courses"]

        cc = res.get("course_candidates") or {}
        out["solve_error"] = res.get("error")
        out["n_candidates"] = len(res.get("candidates") or [])
        out["courses_solved"] = len(cc)
        out["pieces"] = sum(len(v) for v in cc.values())
        out["collisions"] = len(res.get("collisions") or [])
        out["intersection_failures"] = len(res.get("intersection_failures") or [])
        out["non_modular"] = len(res.get("non_modular") or [])
        out["door_void"] = len(res.get("door_void_violations") or [])

        t2 = time.time()
        pf = m.controlled_beta_preflight(res, walls, opw, CATALOG, meta["base_z_abs"])
        out["t_preflight"] = time.time() - t2
        out["preflight_ok"] = bool(pf["ok"])
        out["pf_errors"] = list(pf["errors"])[:8]
        out["pf_opening_violations"] = len(pf["opening_violations"])
        out["pf_collisions"] = len(pf["collisions"])

        if want_audit:
            # A auditoria de amarracao (ETAPA 4C) JA' roda dentro de
            # solve_building_blocks_all_courses e volta no resultado - nunca
            # chamar de novo aqui (seria uma segunda implementacao paralela,
            # que poderia divergir do que a Tela 2 realmente consome).
            audits = res.get("wall_bond_audits") or {}
            reproved = {wi: a for wi, a in audits.items() if not a["ok"]}
            out["bond_audited"] = len(audits)
            out["bond_reproved"] = len(reproved)
            problems = []
            for a in reproved.values():
                problems.extend(a.get("problems") or [])
            out["bond_reasons"] = sorted({str(p)[:110] for p in problems})[:6]
            # Quem foi reprovado, por IDENTIDADE FISICA (nunca por indice):
            # o indice local do subset nao significa nada fora dele.
            out["bond_reproved_walls"] = [
                {"key": phys_key(*walls[wi][:2]),
                 "len_cm": round(walls[wi][0].Length * F2CM, 1),
                 "problems": [str(p)[:150] for p in (a.get("problems") or [])]}
                for wi, a in sorted(reproved.items())
            ]
            out["alternating_strips"] = sum(
                len(a.get("alternating_strips") or []) for a in audits.values())
        out["t_total"] = time.time() - t0
        # PASS = solver fechou, preflight limpo, nada reprovado
        out["verdict"] = "PASS" if (
            not out["solve_error"]
            and out["preflight_ok"]
            and out["courses_solved"] == meta["num_courses"]
            and out["collisions"] == 0
            and out["intersection_failures"] == 0
            and out["door_void"] == 0
            and out.get("bond_reproved", 0) == 0
        ) else "FAIL"
    except Exception as ex:
        out["t_total"] = time.time() - t0
        out["verdict"] = "ERROR"
        out["exception"] = "%s: %s" % (type(ex).__name__, ex)
        out["traceback"] = traceback.format_exc()[-2500:]
    return out


def fmt(o, verbose=False):
    base = ("%-26s n=%-4d nos=%-4s %-5s  solve=%7.3fs tot=%7.3fs  pecas=%-6s "
            "cand=%-5s fiadas=%-5s col=%-3s ifail=%-3s nmod=%-3s bond=%-3s pf=%s")
    line = base % (
        o.get("label", ""), o["n_in"], o.get("n_nodes", "-"), o.get("verdict"),
        o.get("t_solve", 0.0), o.get("t_total", 0.0), o.get("pieces", "-"),
        o.get("n_candidates", "-"), o.get("courses_solved", "-"),
        o.get("collisions", "-"), o.get("intersection_failures", "-"),
        o.get("non_modular", "-"), o.get("bond_reproved", "-"),
        o.get("preflight_ok"))
    if o.get("verdict") == "ERROR":
        line += "\n    EXCECAO: %s" % o.get("exception")
        if verbose:
            line += "\n" + o.get("traceback", "")
    if o.get("solve_error"):
        line += "\n    solve_error: %s" % o["solve_error"]
    if o.get("pf_errors"):
        line += "\n    preflight: %s" % (o["pf_errors"],)
    if o.get("bond_reasons"):
        line += "\n    bond: %s" % (o["bond_reasons"],)
    if o.get("kinds"):
        line += "\n    nos: %s" % (o["kinds"],)
    return line


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--axes", required=True)
    ap.add_argument("--ladder", default="2,5,10,20,30,50,75,100,150,0",
                    help="0 = todos")
    ap.add_argument("--seed-key", default=None,
                    help="chave fisica do eixo semente (default: o eixo da bancada)")
    ap.add_argument("--indices", default=None,
                    help="roda UM subset com estes indices (delta debugging)")
    ap.add_argument("--no-audit", action="store_true")
    ap.add_argument("--no-stop", action="store_true",
                    help="nao para no primeiro FAIL (mapeia o quadro inteiro)")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    axes, meta = load_axes(args.axes)
    print("engine    : %s" % m.__file__)
    print("python    : %s" % sys.version.split()[0])
    print("eixos     : %d | fiadas=%d | base_z=%.4f ft | aberturas=%d"
          % (len(axes), meta["num_courses"], meta["base_z_abs"], meta["openings_count"]))

    if args.indices:
        idxs = [int(x) for x in args.indices.split(",") if x.strip()]
        o = run_subset(axes, idxs, meta, "idx[%d]" % len(idxs), not args.no_audit)
        print(fmt(o, args.verbose))
        if args.verbose:
            for k in o["keys"]:
                print("      %s" % k)
        return

    adj, _nodes = build_adjacency(axes)
    if args.seed_key:
        seed = next(i for i in range(len(axes)) if phys_key(*axes[i][:2]) == args.seed_key)
    else:
        # semente = eixo mais longo com vizinho (canto rico, cresce depressa)
        seed = max(range(len(axes)),
                   key=lambda i: (len(adj.get(i, ())) > 0, axes[i][0].Length))
    print("semente   : #%d %s (grau=%d)" % (seed, phys_key(*axes[seed][:2]), len(adj.get(seed, ()))))
    order = growth_order(axes, adj, seed)

    steps = []
    for tok in args.ladder.split(","):
        k = int(tok)
        steps.append(len(axes) if k == 0 else min(k, len(axes)))
    results = []
    for k in steps:
        o = run_subset(axes, order[:k], meta, "K=%d" % k, not args.no_audit)
        results.append(o)
        print(fmt(o, args.verbose))
        sys.stdout.flush()
        if o["verdict"] != "PASS" and not args.no_stop:
            print("")
            print(">>> PRIMEIRO NAO-PASS em K=%d - parando a escalada (item 9 da missao)." % k)
            break

    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump({"meta": meta, "order": order, "results": results}, fh, indent=1)
        print("\njson: %s" % args.json_out)


if __name__ == "__main__":
    main()
