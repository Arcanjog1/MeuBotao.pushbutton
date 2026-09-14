app = __revit__.Application
active = __revit__.ActiveUIDocument.Document if __revit__.ActiveUIDocument else None
out = []
for d in app.Documents:
    gm = DB.FilteredElementCollector(d).OfCategory(DB.BuiltInCategory.OST_GenericModel).WhereElementIsNotElementType().GetElementCount()
    walls = DB.FilteredElementCollector(d).OfClass(DB.Wall).GetElementCount()
    furn = DB.FilteredElementCollector(d).OfCategory(DB.BuiltInCategory.OST_Furniture).WhereElementIsNotElementType().GetElementCount()
    lv = sorted([[l.Name, round(l.Elevation*FT,1), round(l.ProjectElevation*FT,1)] for l in DB.FilteredElementCollector(d).OfClass(DB.Level)], key=lambda x:x[2])
    out.append(dict(title=d.Title, path=d.PathName, modified=d.IsModified, linked=d.IsLinked, family=d.IsFamilyDocument,
        workshared=d.IsWorkshared, readonly=d.IsReadOnly, active=(active is not None and d.Equals(active)),
        generic_models=gm, walls=walls, furniture=furn, levels=lv, hash=d.GetHashCode()))
dump("q01_docs.json", dict(version=app.VersionNumber + " " + app.VersionBuild, docs=out))
print("ok %d" % len(out))
