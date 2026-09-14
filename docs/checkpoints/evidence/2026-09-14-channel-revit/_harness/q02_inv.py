app = __revit__.Application
res = {}
for d in app.Documents:
    key = "HUMAN" if d.Title.startswith("BUTANT") and "R08_LT" in d.Title else ("TARGET" if d.Title == "butanta testes" else "OTHER")
    syms = []
    for s in DB.FilteredElementCollector(d).OfClass(DB.FamilySymbol):
        try:
            cat = s.Category.Name if s.Category else ""
            bic = eid(s.Category.Id) if s.Category else 0
        except: cat = ""; bic = 0
        if bic not in (-2000151, -2000080):  # generic model, furniture
            continue
        n = DB.FilteredElementCollector(d).WhereElementIsNotElementType().WherePasses(DB.FamilyInstanceFilter(d, s.Id)).GetElementCount()
        params = []
        for p in s.Parameters:
            try:
                params.append([p.Definition.Name, p.AsValueString() or p.AsString() or ""])
            except: pass
        syms.append(dict(fam=s.FamilyName, typ=DB.Element.Name.GetValue(s), cat=bic, n=n, active=s.IsActive, id=eid(s.Id), tparams=params))
    imports = []
    for imp in DB.FilteredElementCollector(d).OfClass(DB.ImportInstance):
        try:
            imports.append(dict(id=eid(imp.Id), linked=imp.IsLinked, name=d.GetElement(imp.GetTypeId()).Category.Name if d.GetElement(imp.GetTypeId()) is not None and d.GetElement(imp.GetTypeId()).Category else "", owner_view=eid(imp.OwnerViewId), level=eid(imp.LevelId)))
        except Exception as e:
            imports.append(dict(err=str(e)))
    res[key] = dict(title=d.Title, symbols=syms, imports=imports, wall_types=[DB.Element.Name.GetValue(t) for t in DB.FilteredElementCollector(d).OfClass(DB.WallType)][:30])
dump("q02_inv.json", res)
print("ok")
