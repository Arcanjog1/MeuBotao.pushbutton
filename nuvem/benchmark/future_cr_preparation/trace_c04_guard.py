"""Instrumenta a funcao REAL de producao _layout_fitted_to_physical_span."""
import collections, json, os, sys
ROOT=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,ROOT)
from nuvem.benchmark import runner, solver_bridge
eng = solver_bridge.engine()          # carrega o motor com os dubles do Revit
ws = sys.modules["core.engine.wall_stepper"]   # dono real dos globals do call site
assert ws._solve_repair_subsegments.__globals__ is ws.__dict__
print("modulo instrumentado:", ws.__name__)
mm = sys.modules[ws.__name__.rsplit(".",1)[0] + ".modulation_math"] if False else None

PHYS = ws.PIER_PHYSICAL_FIT_TOLERANCE_CM
floored = ws.pier_cm_floored_to_module
EVENTS=[]
_orig = ws._layout_fitted_to_physical_span

def traced(layout, pier_cm, sub, layout_for_span):
    out = _orig(layout, pier_cm, sub, layout_for_span)
    end_in  = ws._layout_physical_end_cm(layout) if layout else None
    fired = (layout is not None and sub.get("trailing_open")
             and end_in is not None and end_in - pier_cm > PHYS)
    if fired:
        EVENTS.append({
            "lo": round(float(sub.get("lo")),4), "hi": round(float(sub.get("hi")),4),
            "pier_cm": round(float(pier_cm),4),
            "leading_open": bool(sub.get("leading_open")),
            "trailing_open": bool(sub.get("trailing_open")),
            "excesso_cm": round(end_in - pier_cm, 4),
            "left_opening": sub.get("left_opening"), "right_opening": sub.get("right_opening"),
            "layout_in":  [[c, round(a,3), round(b,3)] for c,a,b in (layout or [])],
            "layout_out": ([[c, round(a,3), round(b,3)] for c,a,b in out] if out else None),
            "floored_cm": floored(pier_cm, 0.0, 0.0),
            "resultado": ("VAZIO_None" if out is None else
                          ("REMONTADO" if list(map(list,out)) != list(map(list,layout)) else "INALTERADO")),
        })
    return out

ws._layout_fitted_to_physical_span = traced
pid, outp = sys.argv[1], sys.argv[2]
paths = runner.project_paths(pid)
solver_bridge.run_solver(json.load(open(paths["input"], encoding="utf-8")))
json.dump(EVENTS, open(outp,"w",encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"{pid}: {len(EVENTS)} disparos reais da guarda")
print("  resultado:", dict(collections.Counter(e["resultado"] for e in EVENTS)))
print("  leading_open:", dict(collections.Counter(e["leading_open"] for e in EVENTS)))
if EVENTS:
    ex=[e["excesso_cm"] for e in EVENTS]
    print(f"  excesso_cm: min={min(ex)} max={max(ex)} distintos={sorted(set(ex))[:12]}")
    perda=[round(e["pier_cm"] - (ws._layout_physical_end_cm([tuple(x) for x in e['layout_out']]) if e["layout_out"] else 0.0),3) for e in EVENTS]
    print(f"  sobra deixada contra a fronteira (cm): {sorted(set(perda))}")
