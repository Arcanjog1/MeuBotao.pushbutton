"""Prototipo: censo PRECISO de juntas NO'|FILL por fiada, deduzido antes do preenchimento,
e busca gulosa de paridade T/X que minimiza coincidencias NO'|FILL x NO'|FILL."""
import sys, os, json, time
root = os.path.abspath(sys.argv[1]); pid = sys.argv[2]; version = sys.argv[3] if len(sys.argv) > 3 else "v2"
os.chdir(root); sys.path.insert(0, root)
from nuvem.benchmark import runner, solver_bridge
paths = runner.project_paths(pid, version)
inp = runner._read_json(paths["input"]) or runner._read_json(runner.project_paths(pid)["input"])
m = solver_bridge.engine()
nodes, walls, end_to_node, openings = solver_bridge.plan_from_input(inp)
catalog, _r, _d = solver_bridge.catalog_from_input(inp)
J = m.BLOCK_JOINT_CM; TOL = m.VERTICAL_JOINT_STAGGER_TOLERANCE_CM
EXEMPT = m.OPENING_ALIGNED_EXEMPT_CODES; TOUCH = m.OPENING_ALIGNED_TOUCH_TOLERANCE_CM
MIN_FILL = 4.0

def cm(ft): return ft / m.FEET_PER_METER * 100.0

def census(inter):
    by_end = m._index_node_candidates_by_wall_end(nodes, inter["candidates"], walls, end_to_node)
    mid = m._index_node_candidates_midspan(nodes, inter["candidates"], walls, end_to_node)
    own = {}
    for c in inter["candidates"]:
        wi = c.get("wall_idx")
        if wi is None: continue
        p0, _p1, wdir, _l, _t = m._wall_axis_and_length(walls, wi)
        s, e = m._candidate_extent_on_wall_axis(c, p0, wdir)
        own.setdefault((wi, c["course"]), []).append((min(s, e), max(s, e), c["logical_code"]))
    out = {}
    for wi in range(len(walls)):
        length = cm(m._wall_axis_and_length(walls, wi)[3])
        ops = [(cm(o[0]), cm(o[1])) for o in (openings[wi] or [])]
        edges = [a for o in ops for a in o] + [0.0, length]
        for course in ("A", "B"):
            # obstaculos: reservas de ponta, intervalos de meio (todas as pecas do no', proprias ou nao)
            obst = []
            b0 = by_end.get((wi, 0, course)); b1 = by_end.get((wi, 1, course))
            if b0 is None:
                r, _j = m._wall_end_default_start_cm(nodes, end_to_node, walls, wi, 0); b0 = r - J  # fill comeca em r (junta 0 se livre)
            if b1 is None:
                r, _j = m._wall_end_default_start_cm(nodes, end_to_node, walls, wi, 1); b1 = length - r + J
            obst.append((-1e9, b0)); obst.append((b1, 1e9))
            for a, b in m._merge_intervals_cm(mid.get((wi, course), [])): obst.append((a, b))
            for a, b in ops: obst.append((a, b))
            joints = []
            for s, e, code in own.get((wi, course), []):
                exempt = code in EXEMPT and any(abs(s - x) <= TOUCH or abs(e - x) <= TOUCH for x in edges)
                if exempt: continue
                # lado esquerdo: corrida livre entre o obstaculo anterior e s
                prev_end = max([b for a, b in obst if b <= s + 1e-6 and b < s - 1e-6] + [-1e9])
                if s - J - (prev_end + J) >= MIN_FILL - 1e-6 and prev_end > -1e8:
                    joints.append(s - J / 2.0)
                elif prev_end <= -1e8 and s - J >= MIN_FILL:  # sem obstaculo a esquerda (ponta livre) - pouco provavel
                    joints.append(s - J / 2.0)
                next_start = min([a for a, b in obst if a >= e - 1e-6 and a > e + 1e-6] + [1e9])
                if (next_start - J) - (e + J) >= MIN_FILL - 1e-6 and next_start < 1e8:
                    joints.append(e + J / 2.0)
            out[(wi, course)] = sorted(joints)
    return out

def coincidences(cs):
    per_wall = {}
    for wi in range(len(walls)):
        ja = cs.get((wi, "A"), []); jb = cs.get((wi, "B"), [])
        co = sorted(set(round(a, 2) for a in ja if any(abs(a - b) <= TOL for b in jb)))
        if co: per_wall[wi] = co
    return per_wall

def solve():
    return m.solve_all_intersections(nodes, walls, catalog, openings_per_wall=openings, end_to_node=end_to_node)

def node_walls(nd):
    s = set(w for w, _e in (nd.get("arms") or []))
    for k in ("main_wall_idx", "incoming_wall_idx"):
        if nd.get(k) is not None: s.add(nd[k])
    s.update(w for w in (nd.get("crossing_walls") or []) if w is not None)
    return s

t0 = time.time()
inter = solve(); cs = census(inter); co = coincidences(cs)
t1 = time.time()
print("%s: censo inicial %.3fs; paredes com NF x NF: %d, coincidencias: %d" % (pid, t1 - t0, len(co), sum(len(v) for v in co.values())))
for wi in sorted(co):
    L = cm(m._wall_axis_and_length(walls, wi)[3])
    kinds = sorted(((nodes[ni]["kind"], round(cm(m._t_of_point_on_wall(walls, wi, nodes[ni]["point"])), 1)) for ni, nd in enumerate(nodes) if wi in node_walls(nd) and nd.get("point") is not None), key=lambda x: x[1])
    print("  idx %3d len %7.1f coinc %s nodes %s" % (wi, L, co[wi], kinds))

# busca gulosa T/X
total = lambda co: sum(len(v) for v in co.values())
best = total(co); flips = []; tried = 0
for _pass in range(2):
    improved = False
    cands = [ni for ni, nd in enumerate(nodes) if nd.get("kind") in ("T_INTERSECTION", "X_INTERSECTION") and node_walls(nd) & set(co)]
    cands.sort(key=lambda i: m._canonical_node_sort_key(nodes[i]) + (i,))
    for ni in cands:
        nd = nodes[ni]; nd["_tie_parity_flip"] = not nd.get("_tie_parity_flip", False); tried += 1
        inter2 = solve(); cs2 = census(inter2); co2 = coincidences(cs2)
        if total(co2) < best:
            best = total(co2); co = co2; flips.append(ni); improved = True
        else:
            nd["_tie_parity_flip"] = not nd.get("_tie_parity_flip", False)
            if not nd["_tie_parity_flip"]: nd.pop("_tie_parity_flip", None)
    if not improved: break
t2 = time.time()
print("busca: %d tentativas, %d flips aceitos, coincidencias %d -> %d, %.2fs" % (tried, len(flips), total(coincidences(census(solve()))) if False else 0, best, t2 - t1))
print("flips:", [(ni, nodes[ni]["kind"], round(nodes[ni]["point"].X * 30.48, 1), round(nodes[ni]["point"].Y * 30.48, 1)) for ni in flips])
print("residual:")
for wi in sorted(co):
    L = cm(m._wall_axis_and_length(walls, wi)[3])
    kinds = sorted(((nodes[ni]["kind"], round(cm(m._t_of_point_on_wall(walls, wi, nodes[ni]["point"])), 1)) for ni, nd in enumerate(nodes) if wi in node_walls(nd) and nd.get("point") is not None), key=lambda x: x[1])
    print("  idx %3d len %7.1f coinc %s nodes %s" % (wi, L, co[wi], kinds))
