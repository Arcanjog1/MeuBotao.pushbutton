app = __revit__.Application
H = None
for d in app.Documents:
    if d.Title.startswith("BUTANT") and "R08_LT" in d.Title:
        H = d
assert H is not None
out = dict(modified_before=H.IsModified, pieces=[])
col = DB.FilteredElementCollector(H).OfCategory(DB.BuiltInCategory.OST_GenericModel).WhereElementIsNotElementType()
for el in col:
    bb = el.get_BoundingBox(None)
    if bb is None:
        continue
    cx = (bb.Min.X + bb.Max.X) / 2 * FT; cy = (bb.Min.Y + bb.Max.Y) / 2 * FT
    if 525 <= cx <= 665 and 910 <= cy <= 1020 and bb.Min.Z * FT < 400:
        try:
            fam = el.Symbol.FamilyName; typ = DB.Element.Name.GetValue(el.Symbol)
        except Exception:
            fam = typ = ""
        out["pieces"].append([fam, typ, round(bb.Min.X*FT, 1), round(bb.Min.Y*FT, 1), round(bb.Min.Z*FT, 1), round(bb.Max.X*FT, 1), round(bb.Max.Y*FT, 1), round(bb.Max.Z*FT, 1)])
out["modified_after"] = H.IsModified
dump("q07_ring_human.json", out)
print("ok", len(out["pieces"]))
