"""Reproduz SO' o setup dos dois testes ARM que falharam, com a paridade ligada e desligada."""
import sys, os, json, time
root = os.path.abspath(sys.argv[1]); which = sys.argv[2]
os.chdir(root); sys.path.insert(0, root); sys.path.insert(0, os.path.join(root, "tests"))
import test_block_arm_role_candidate_safety_contract as T
m = T.m
ws = sys.modules["core.engine.wall_stepper"]
out = {}
for enabled in (True, False):
    ws.ABUTTING_TIE_PARITY_ENABLED = enabled
    t0 = time.time()
    if which == "tgd":
        result, nodes, walls, e2n, op, cat, bz, nc = T._run_tgd(enabled=True)
        audits = result.get("wall_bond_audits")
        forced = sorted(w for w in range(len(walls)) if m._wall_has_forced_corner_prism(w, audits))
        arm = result.get("arm_role_safe_repair") or {}
        out[str(enabled)] = {"seconds": round(time.time()-t0,1), "accepted": arm.get("accepted"), "rejected_n": len(arm.get("rejected") or []),
            "forced_prism_walls": forced, "forced_prism_n": len(forced), "wall23_forced": m._wall_has_forced_corner_prism(23, audits),
            "tie_parity_flips": result.get("tie_parity_flips"), "tie_parity_conflicts": result.get("tie_parity_conflicts"),
            "isolated_edges_now": [e["wall_idx"] for e in m._arm_role_isolated_edges(nodes)],
            "pinned_nodes": [i for i, n in enumerate(nodes) if n.get("_arm_role_pinned")],
            "critical_like": {"collisions": len(result.get("collisions") or []), "non_modular": len(result.get("non_modular") or []), "audits_failing": sum(1 for a in (audits or {}).values() if not a.get("ok"))}}
    else:
        import test_block_arm_role_prism_stagger as P
        input_project, solve_result, walls_to_create, result_project = P._run("torre_easy_lo_r00_tp1")
        wall_idx = next(i for i, w in enumerate(input_project["walls"]) if w["id"] == "W076")
        wall = P._wall_by_id(result_project, "W076")
        ja, jb = P._wall_row_joints(wall, 0), P._wall_row_joints(wall, 1)
        arm = solve_result.get("arm_role_safe_repair") or {}
        audits = solve_result.get("wall_bond_audits")
        forced = sorted(w for w in range(len(walls_to_create)) if m._wall_has_forced_corner_prism(w, audits))
        out[str(enabled)] = {"seconds": round(time.time()-t0,1), "W076_wall_idx": wall_idx, "joints_row0": sorted(ja), "joints_row1": sorted(jb), "coincide": sorted(ja & jb),
            "accepted": arm.get("accepted"), "rejected_n": len(arm.get("rejected") or []), "forced_prism_walls": forced, "forced_prism_n": len(forced),
            "tie_parity_flips": solve_result.get("tie_parity_flips"), "tie_parity_conflicts": solve_result.get("tie_parity_conflicts"),
            "critical_like": {"collisions": len(solve_result.get("collisions") or []), "non_modular": len(solve_result.get("non_modular") or []), "audits_failing": sum(1 for a in (audits or {}).values() if not a.get("ok"))}}
    print(which, "paridade", enabled, json.dumps(out[str(enabled)], default=str)[:1500], flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "arm_check_%s.json" % which), "w"), indent=1, default=str)
