# -*- coding: utf-8 -*-
# SOMENTE LEITURA: canaletas cortadas (U_CUT) e meias canaletas do lote novo - comprimento pelo parametro e pela caixa
import sys
from Autodesk.Revit.DB import FilteredElementCollector, FamilyInstance, BuiltInParameter, XYZ
wm = sys.modules["core.wall_modeling"]
T = [d for d in doc.Application.Documents if d.Title == u"butanta testes"][0]
FT = 30.48
out = {}
for el in FilteredElementCollector(T).OfClass(FamilyInstance).WhereElementIsNotElementType():
    fam = el.Symbol.FamilyName if el.Symbol else ""
    up = fam.upper()
    if "CANALETA" not in up or ("CORTAD" not in up and "MEIA" not in up):
        continue
    p = el.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    if not wm._parse_block_lot_stamp(p.AsString() if p is not None else None):
        continue
    par = None
    for nm in (u"Comprimento_bloco", u"Comprimento", u"Length"):
        q = el.LookupParameter(nm)
        if q is not None:
            try:
                par = round(q.AsDouble() * FT, 1)
                break
            except Exception:
                pass
    bb = el.get_BoundingBox(None)
    tr = el.GetTransform()
    xd = tr.BasisX
    ext = None
    if bb is not None:
        dx, dy = (bb.Max.X - bb.Min.X) * FT, (bb.Max.Y - bb.Min.Y) * FT
        ext = round(dx if abs(xd.X) > abs(xd.Y) else dy, 1)
    out.setdefault(fam, []).append((par, ext))
for fam, v in out.items():
    print(repr(fam), len(v), "param/caixa:", sorted(set(v))[:12])
