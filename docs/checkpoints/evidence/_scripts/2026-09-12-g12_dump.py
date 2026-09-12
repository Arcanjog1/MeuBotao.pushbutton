import sys, os, json, copy
root = os.path.abspath(sys.argv[1]); label = sys.argv[2]
os.chdir(root); sys.path.insert(0, root); sys.path.insert(0, os.path.join(root, "tests"))
import test_cross_band_joint_propagation_cr_g12 as G
m = G.m
projeto = G._subplano()
(solve_result, walls, nodes, opw, catalog, base_z_ft, num_courses, _n) = G.solver_bridge.run_solver(projeto)
rp = G.from_solver.project_from_solver("repro", solve_result, walls, nodes, opw, catalog, base_z_ft, num_courses, metadata={})
findings, _e = G.validators.run_all(rp, {})
print(label, "PRISM findings:", [(f["wall"], f.get("detail","")[:90]) for f in findings if f["code"]=="PRISM_CONTINUOUS_JOINT"])
for w in rp["walls"]:
    print(label, w["id"], w["key"], "len", w["length_cm"], "openings", [(o["kind"], o["t_start_cm"], o["t_end_cm"], o["sill_cm"], o["head_cm"]) for o in w["openings"]], "junctions", [(j["type"], j["t_cm"]) for j in w["junctions"]])
    for row in w["rows"]:
        if 100 <= row["elevation_cm"] <= 262:
            print("   z", row["elevation_cm"], [(b["code"], round(b["t_start_cm"],1), round(b["t_end_cm"],1), (b.get("placement_reason") or "")[:14]) for b in row["blocks"] if b["t_start_cm"] < 200])
