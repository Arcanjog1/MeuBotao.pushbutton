# -*- coding: utf-8 -*-
# SOMENTE LEITURA no projeto humano: todos os Modelos genericos do 1o PAVIMENTO (blocos/canaletas/compensadores)
# + aberturas do 1o PAVIMENTO. Grava %TEMP%/s85r4/ref_1pav.json.
import json, os, codecs
from Autodesk.Revit.DB import FilteredElementCollector, FamilyInstance, BuiltInCategory, BuiltInParameter
FT = 30.48
def U(x):
    if x is None:
        return u""
    try:
        return unicode(x)
    except Exception:
        return x.decode("cp1252", "replace")
def tname(sym):
    p = sym.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
    return U(p.AsString()) if p else u""
def pd(e, name):
    p = e.LookupParameter(name)
    try:
        return round(p.AsDouble() * FT, 3) if p else None
    except Exception:
        return None
R = [d for d in doc.Application.Documents if d.Title.startswith(u"BUTANT") and u"R08_LT" in d.Title][0]
LVL = 6265066
pieces, openings = [], []
for fi in FilteredElementCollector(R).OfClass(FamilyInstance).WhereElementIsNotElementType():
    if not fi.LevelId or int(fi.LevelId.Value) != LVL:
        continue
    cat = U(fi.Category.Name) if fi.Category else u""
    fam = U(fi.Symbol.FamilyName) if fi.Symbol else u""
    if u"Abertura" in fam:
        bb = fi.get_BoundingBox(None)
        openings.append({"id": int(fi.Id.Value), "fam": fam, "typ": tname(fi.Symbol),
                         "bb": [round(v * FT, 2) for v in (bb.Min.X, bb.Min.Y, bb.Min.Z, bb.Max.X, bb.Max.Y, bb.Max.Z)],
                         "w": pd(fi, u"Largura_abertura"), "h": pd(fi, u"Altura_abertura"), "sill": pd(fi, u"Peitoril")})
        continue
    if fi.Category is None or fi.Category.Id.Value != int(BuiltInCategory.OST_GenericModel):
        continue
    tr = fi.GetTransform()
    lp = fi.Location.Point if hasattr(fi.Location, "Point") else None
    bb = fi.get_BoundingBox(None)
    pieces.append({"id": int(fi.Id.Value), "fam": fam, "typ": tname(fi.Symbol),
                   "o": [round(lp.X * FT, 3), round(lp.Y * FT, 3), round(lp.Z * FT, 3)] if lp else None,
                   "bx": [round(tr.BasisX.X, 4), round(tr.BasisX.Y, 4)], "by": [round(tr.BasisY.X, 4), round(tr.BasisY.Y, 4)],
                   "mir": bool(fi.Mirrored),
                   "bb": [round(v * FT, 2) for v in (bb.Min.X, bb.Min.Y, bb.Min.Z, bb.Max.X, bb.Max.Y, bb.Max.Z)] if bb else None,
                   "L": pd(fi, u"Comprimento_bloco") or pd(fi.Symbol, u"Comprimento_bloco"),
                   "H": pd(fi, u"Altura_bloco") or pd(fi.Symbol, u"Altura_bloco")})
p = os.path.join(u"C:\\", u"Users", u"CIVIX", u"AppData", u"Local", u"Temp", u"s85r4", u"ref_1pav.json")
codecs.open(p, "w", "utf-8").write(json.dumps({"level": LVL, "pieces": pieces, "openings": openings}, ensure_ascii=False))
fams = {}
for x in pieces:
    k = x["fam"] + u" | " + x["typ"]
    fams[k] = fams.get(k, 0) + 1
print("pecas", len(pieces), "aberturas", len(openings))
for k, v in sorted(fams.items(), key=lambda kv: -kv[1]):
    print(repr(k), v)
