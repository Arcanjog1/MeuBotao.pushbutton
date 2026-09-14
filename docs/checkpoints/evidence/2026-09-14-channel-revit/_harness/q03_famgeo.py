app = __revit__.Application
H = None
for d in app.Documents:
    if d.Title.startswith("BUTANT") and "R08_LT" in d.Title and not d.IsModified:
        H = d
assert H is not None
want = ["CANALETA INTEIRA - 14x19x39", "CANALETA 34 - 14x19x34", "MEIA CANALETA - 14x19x19", "BLOCO CANALETA CORTADO - 14x19xVAR",
        "BLOCO INTEIRO - 14x19x39", "BLOCO 34 - 14x19x34", "MEIO BLOCO - 14x19x19", "COMPENSADOR 14x19x9", "PASTILHA - 14x19X4", "CANALETA J - 14x9-19x19"]
lvl1 = None
for l in DB.FilteredElementCollector(H).OfClass(DB.Level):
    if abs(l.ProjectElevation) < 1e-6: lvl1 = l
res = {}
opt = DB.Options(); opt.DetailLevel = DB.ViewDetailLevel.Fine
for fam in want:
    items = []
    col = DB.FilteredElementCollector(H).OfCategory(DB.BuiltInCategory.OST_GenericModel).WhereElementIsNotElementType().OfClass(DB.FamilyInstance)
    for inst in col:
        if inst.Symbol.FamilyName != fam: continue
        if inst.LevelId != lvl1.Id: continue
        lp = inst.Location.Point
        bb = inst.get_BoundingBox(None)
        ip = []
        for p in inst.Parameters:
            try:
                if p.StorageType == DB.StorageType.Double:
                    ip.append([p.Definition.Name, round(p.AsDouble()*FT, 3) if "ngulo" not in p.Definition.Name else p.AsDouble()])
                elif p.StorageType == DB.StorageType.String:
                    ip.append([p.Definition.Name, p.AsString()])
            except: pass
        # solid extents in world
        sx = []
        for g in inst.get_Geometry(opt):
            gi = g.GetInstanceGeometry() if isinstance(g, DB.GeometryInstance) else [g]
            for s in gi:
                if isinstance(s, DB.Solid) and s.Volume > 1e-9:
                    bs = s.GetBoundingBox(); tr = bs.Transform
                    for pt in (bs.Min, bs.Max):
                        w = tr.OfPoint(pt); sx.append([w.X*FT, w.Y*FT, w.Z*FT])
        sol = None
        if sx:
            sol = [min(p[0] for p in sx), min(p[1] for p in sx), min(p[2] for p in sx), max(p[0] for p in sx), max(p[1] for p in sx), max(p[2] for p in sx)]
        items.append(dict(id=eid(inst.Id), loc=[lp.X*FT, lp.Y*FT, lp.Z*FT], rot=inst.Location.Rotation, hand=[inst.HandOrientation.X, inst.HandOrientation.Y],
            facing=[inst.FacingOrientation.X, inst.FacingOrientation.Y], mirrored=inst.Mirrored, bb=[bb.Min.X*FT, bb.Min.Y*FT, bb.Min.Z*FT, bb.Max.X*FT, bb.Max.Y*FT, bb.Max.Z*FT], solid=sol, iparams=ip))
        if len(items) >= 4: break
    sym = None
    for s in DB.FilteredElementCollector(H).OfClass(DB.FamilySymbol):
        if s.FamilyName == fam: sym = s; break
    tp = []
    if sym is not None:
        for p in sym.Parameters:
            try:
                if p.StorageType == DB.StorageType.Double: tp.append([p.Definition.Name, round(p.AsDouble()*FT, 3)])
                elif p.StorageType == DB.StorageType.String: tp.append([p.Definition.Name, p.AsString()])
            except: pass
    res[fam] = dict(instances=items, type_params=tp)
dump("q03_famgeo.json", dict(doc=H.Title, modified_after=H.IsModified, res=res))
print("ok", H.IsModified)
