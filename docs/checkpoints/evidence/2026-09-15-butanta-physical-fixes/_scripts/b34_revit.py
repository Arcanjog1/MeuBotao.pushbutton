import os, sys, collections
sys.path.insert(0, ".")
import phys, pmodel, b34rule, evalsolve
T = phys.load(os.environ.get("TARGET_JSON", "target_1pav.clean.json"))
H = phys.load("human_1pav.clean.json")
walls = [phys.Wall(w["id"], w["p0"], w["p1"], w["uid"]) for w in phys.load("target_1pav.clean.json")["walls"]]
mas = evalsolve.masonry_wall_ids()
for doc, stamp, label in ((H, False, "HUMANO"), (T, True, "TARGET")):
    recs = [phys.piece_record(p) for p in doc["pieces"]]
    phys.assign_walls(recs, walls, by_stamp=stamp)
    pcs = [p for p in pmodel.from_revit(recs) if p.course < 13 and p.wall in mas]
    out = b34rule.classify(pcs, 13)
    print(label, out[0] if isinstance(out, tuple) else out)
