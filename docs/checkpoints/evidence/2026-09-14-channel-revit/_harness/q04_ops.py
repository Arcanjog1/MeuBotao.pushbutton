T = __revit__.ActiveUIDocument.Document
assert T.Title == "butanta testes"
rows = []
for el in DB.FilteredElementCollector(T).OfCategory(DB.BuiltInCategory.OST_Furniture).WhereElementIsNotElementType():
    lv = T.GetElement(el.LevelId)
    bb = el.get_BoundingBox(None)
    def pv(n):
        p = el.LookupParameter(n)
        if p is None: return None
        try: return round(p.AsDouble() * FT, 2)
        except: return p.AsString()
    host = el.Host.Name if el.Host is not None else None
    rows.append(dict(id=eid(el.Id), level=lv.Name if lv else None, lvl_pe=round(lv.ProjectElevation*FT,1) if lv else None, loc=[round(v*FT,1) for v in (el.Location.Point.X, el.Location.Point.Y, el.Location.Point.Z)],
        bbz=[round(bb.Min.Z*FT,1), round(bb.Max.Z*FT,1)], larg=pv("Largura_abertura"), alt=pv("Altura_abertura"), peit=pv("Peitoril"), peit2=pv("Altura_peitoril"), off=pv("Deslocamento do hospedeiro"), elev=pv("Eleva\u00e7\u00e3o do n\u00edvel"), host=host, parede=pv("Parede")))
dump("q04_ops.json", rows)
print(len(rows))
