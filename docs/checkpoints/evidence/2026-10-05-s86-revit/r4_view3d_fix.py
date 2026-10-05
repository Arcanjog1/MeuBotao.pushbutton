# -*- coding: utf-8 -*-
# Rodada 4: a vista "S86 Pavimento 3D" ganha caixa de corte em volta dos blocos do lote novo (o resto do modelo
# - linhas/niveis/vinculos distantes - deixa a vista minuscula) e esconde categorias de anotacao/referencia.
import sys, System
wm = sys.modules["core.wall_modeling"]
from Autodesk.Revit.DB import (FilteredElementCollector, FamilyInstance, BuiltInParameter, BoundingBoxXYZ, XYZ,
                               Transaction, ElementId, BuiltInCategory, View3D)
T = [d for d in doc.Application.Documents if d.Title == u"butanta testes"][0]
S = wm._MCP_STATE
FT = 30.48
view = T.GetElement(ElementId(System.Int64(S["s86_views"][u"S86 Pavimento 3D"])))
lo = [1e18, 1e18, 1e18]
hi = [-1e18, -1e18, -1e18]
n = 0
for el in FilteredElementCollector(T).OfClass(FamilyInstance).WhereElementIsNotElementType():
    p = el.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    st = wm._parse_block_lot_stamp(p.AsString() if p is not None else None)
    if st is None:
        continue
    bb = el.get_BoundingBox(None)
    if bb is None:
        continue
    for k, (a, b) in enumerate(((bb.Min.X, bb.Max.X), (bb.Min.Y, bb.Max.Y), (bb.Min.Z, bb.Max.Z))):
        lo[k] = min(lo[k], a)
        hi[k] = max(hi[k], b)
    n += 1
m = 40.0 / FT
box = BoundingBoxXYZ()
box.Min = XYZ(lo[0] - m, lo[1] - m, lo[2] - 5.0 / FT)
box.Max = XYZ(hi[0] + m, hi[1] + m, hi[2] + 10.0 / FT)
t = Transaction(T, "S86 - caixa de corte da vista 3D do pavimento (Claude)")
t.Start()
try:
    view.IsSectionBoxActive = True
    view.SetSectionBox(box)
    hidden = []
    for cat in (BuiltInCategory.OST_Levels, BuiltInCategory.OST_Grids, BuiltInCategory.OST_Lines,
                BuiltInCategory.OST_CLines, BuiltInCategory.OST_SectionBox, BuiltInCategory.OST_Sections,
                BuiltInCategory.OST_Elev, BuiltInCategory.OST_Viewers, BuiltInCategory.OST_Floors,
                BuiltInCategory.OST_Roofs, BuiltInCategory.OST_Ceilings):
        try:
            cid = ElementId(cat)
            if view.CanCategoryBeHidden(cid):
                view.SetCategoryHidden(cid, True)
                hidden.append(str(cat))
        except Exception:
            pass
    print("commit", t.Commit())
except Exception:
    t.RollBack()
    raise
S["s86_views_only3d"] = {u"S86 Pavimento 3D": S["s86_views"][u"S86 Pavimento 3D"]}
print("blocos", n, "caixa cm", [round(v * FT) for v in lo], [round(v * FT) for v in hi], "ocultas", len(hidden))
