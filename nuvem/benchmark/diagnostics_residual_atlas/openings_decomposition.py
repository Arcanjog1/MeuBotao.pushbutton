# -*- coding: utf-8 -*-
"""ABERTURAS decompostas por causa (item 13)."""
import os
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas_lib as al  # noqa: E402


def build(project_id):
    b = al.Bundle(project_id)
    blocks = {}
    for w in b.result["walls"]:
        for r in w["rows"]:
            for bl in r["blocks"]:
                blocks[bl["id"]] = bl
    rows = []
    for f in b.findings():
        if not f["code"].startswith("OPENING_"):
            continue
        wi = b.idx(f["wall"])
        ctx = b.ctx(wi)
        rec = {"project": b.short, "code": f["code"], "wall_id": f["wall"], "human_wall": ctx["human_wall"],
               "row": f.get("row"), "opening": f.get("opening")}
        cause = "UNKNOWN"
        if f["code"] in ("OPENING_BLOCK_CROSSES_JAMB", "OPENING_BLOCK_INSIDE_DOOR", "OPENING_BLOCK_INSIDE_WINDOW"):
            bl = blocks.get((f.get("blocks") or [None])[0])
            reason = bl.get("placement_reason") if bl else None
            o_lo, o_hi = f["opening_t_cm"]
            nodes_inside = [m for m in ctx["midspan_nodes"] if o_lo - 1 <= m["t_cm"] <= o_hi + 1]
            ends_inside = [e for e in ctx["ends"].values() if e["kind"] not in ("NONE", "FREE_END") and o_lo - 1 <= e["t_cm"] <= o_hi + 1]
            if al.is_tie_reason(reason):
                if nodes_inside or ends_inside:
                    cause = "NODE_PIECE_AT_NODE_INSIDE_OPENING_SPAN"
                else:
                    cause = "NODE_PIECE_ROOM_CHECK_MISS"
            elif reason == "OPENING_REPAIR_FILL":
                cause = "REPAIR_PIECE_INVADES"
            else:
                cause = "FILL_PIECE_INVADES(" + str(reason) + ")"
            rec["placement_reason"] = reason
            rec["opening_width"] = round(o_hi - o_lo, 1)
            rec["human_confidence"] = None
            hw = b.ref_by_id.get(ctx["human_wall"])
            if hw:
                for op in hw["openings"]:
                    if abs(op["t_start_cm"] - o_lo) < 3 or abs(op["t_end_cm"] - o_hi) < 3:
                        rec["human_confidence"] = op.get("confidence")
        elif f["code"] == "OPENING_SOLID_BELOW_SILL_MISSING":
            nm = [x for x in b.run["solve_result"]["non_modular"] if x["wall_idx"] == wi and x["course"] == al.course_letter(f["row"])]
            cause = "NON_MODULAR_TRECHO(" + Counter(x.get("conflict") or "fit" for x in nm).most_common(1)[0][0] + ")" if nm else "UNKNOWN"
        elif f["code"] in ("OPENING_MISSING_LINTEL", "OPENING_MISSING_COUNTER_LINTEL"):
            cause = "CATALOG_SCOPE(no lintel/channel pieces in solver catalog)"
        rec["cause"] = cause
        rows.append(rec)
    al.write_json(al.out_path(b.short, "openings_decomposition.json"), rows)
    return rows


def main():
    out = {}
    for pid in al.PROJECT_IDS:
        rows = build(pid)
        s = {}
        for code in sorted(set(r["code"] for r in rows)):
            sub = [r for r in rows if r["code"] == code]
            s[code] = {"total": len(sub), "by_cause": Counter(r["cause"] for r in sub).most_common(),
                       "by_reason": Counter(r.get("placement_reason") for r in sub).most_common(5),
                       "human_conf": Counter(r.get("human_confidence") for r in sub).most_common(3)}
            print("==", al.SHORT[pid], code, s[code])
        out[al.SHORT[pid]] = s
    al.write_json(al.out_path("openings_decomposition_summary.json"), out)


if __name__ == "__main__":
    main()
