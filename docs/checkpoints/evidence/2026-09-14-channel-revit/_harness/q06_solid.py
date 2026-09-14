T = __revit__.ActiveUIDocument.Document
assert T.Title == "butanta testes"
el = T.GetElement(DB.ElementId(System.Int64(8093956)))
opt = DB.Options(); opt.DetailLevel = DB.ViewDetailLevel.Fine
pts = []
vol = 0.0
for g in el.get_Geometry(opt):
    items = g.GetInstanceGeometry() if isinstance(g, DB.GeometryInstance) else [g]
    for s in items:
        if isinstance(s, DB.Solid) and s.Volume > 1e-9:
            vol += s.Volume
            for e in s.Edges:
                for p in e.Tessellate():
                    pts.append((p.X*FT, p.Y*FT, p.Z*FT))
bb = el.get_BoundingBox(None)
p = el.LookupParameter("Comprimento_bloco")
res = dict(family=el.Symbol.FamilyName, param_cm=p.AsDouble()*FT, rot=el.Location.Rotation,
    solid=[min(x[0] for x in pts), min(x[1] for x in pts), min(x[2] for x in pts), max(x[0] for x in pts), max(x[1] for x in pts), max(x[2] for x in pts)],
    bbox=[bb.Min.X*FT, bb.Min.Y*FT, bb.Min.Z*FT, bb.Max.X*FT, bb.Max.Y*FT, bb.Max.Z*FT], volume_cm3=vol*FT**3)
dump("q06_solid.json", res)
print("ok")
