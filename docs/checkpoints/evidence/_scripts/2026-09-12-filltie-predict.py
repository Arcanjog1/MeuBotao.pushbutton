import sys, os, time
root = os.path.abspath(sys.argv[1]); pid = sys.argv[2]; version = sys.argv[3]
os.chdir(root); sys.path.insert(0, root)
from nuvem.benchmark import runner, solver_bridge
paths = runner.project_paths(pid, version)
inp = runner._read_json(paths["input"]) or runner._read_json(runner.project_paths(pid)["input"])
m = solver_bridge.engine()
nodes, walls, e2n, openings = solver_bridge.plan_from_input(inp)
catalog, _r, _d = solver_bridge.catalog_from_input(inp)
t0 = time.time()
inter = m.solve_all_intersections(nodes, walls, catalog, openings_per_wall=openings, end_to_node=e2n)
t1 = time.time()
cm = lambda ft: ft / m.FEET_PER_METER * 100.0
print(pid, "solve_all_intersections com paridade: %.3fs" % (t1 - t0), "flips", len(inter["tie_parity_flips"]), "conflicts", len(inter["tie_parity_conflicts"]))
for ni in inter["tie_parity_flips"]:
    nd = nodes[ni]; print("  flip", ni, nd["kind"], round(nd["point"].X*30.48,1), round(nd["point"].Y*30.48,1))
for c in inter["tie_parity_conflicts"]:
    wi = c["wall_idx"]; print("  conflict wall idx", wi, "len", round(cm(m._wall_axis_and_length(walls, wi)[3]),1), "t", c["t_cm"], c["reason"], "nodes", [(n, nodes[n]["kind"]) for n in c["nodes"]])
census = m._node_fill_boundary_joint_census(nodes, walls, e2n, openings, inter["candidates"], catalog)
print("  coincidencias residuais no censo:", len(m._census_coincidences(census, len(walls))))
# segunda chamada (marcas ja' aplicadas) - custo e idempotencia
t2 = time.time(); inter2 = m.solve_all_intersections(nodes, walls, catalog, openings_per_wall=openings, end_to_node=e2n); t3 = time.time()
print("  segunda chamada: %.3fs flips %d (deve ser 0) conflicts %d" % (t3 - t2, len(inter2["tie_parity_flips"]), len(inter2["tie_parity_conflicts"])))
