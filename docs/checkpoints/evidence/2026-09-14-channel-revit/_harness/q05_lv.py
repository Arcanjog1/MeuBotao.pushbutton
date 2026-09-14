T = __revit__.ActiveUIDocument.Document
assert T.Title == "butanta testes"
res = {}
for imp in DB.FilteredElementCollector(T).OfClass(DB.ImportInstance):
    lv = T.GetElement(imp.LevelId)
    bb = imp.get_BoundingBox(None)
    tp = T.GetElement(imp.GetTypeId())
    res[str(eid(imp.Id))] = dict(level=lv.Name if lv else None, pe=round(lv.ProjectElevation*FT,1) if lv else None, linked=imp.IsLinked, name=(tp.Category.Name if tp is not None and tp.Category else None),
        bbz=[round(bb.Min.Z*FT,1), round(bb.Max.Z*FT,1)] if bb else None, pinned=imp.Pinned)
levels = dict((str(eid(l.Id)), [l.Name, round(l.ProjectElevation*FT,1)]) for l in DB.FilteredElementCollector(T).OfClass(DB.Level))
gm = DB.FilteredElementCollector(T).OfCategory(DB.BuiltInCategory.OST_GenericModel).WhereElementIsNotElementType().GetElementCount()
dump("q05_lv.json", dict(imports=res, levels=levels, generic_models=gm, walls=DB.FilteredElementCollector(T).OfClass(DB.Wall).GetElementCount(), modified=T.IsModified))
print("ok")
