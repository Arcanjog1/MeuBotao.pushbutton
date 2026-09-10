# -*- coding: utf-8 -*-
execfile(r"C:\Users\CIVIX\AppData\Local\Temp\claude\C--Users-CIVIX-OneDrive--rea-de-Trabalho-Scripts-extension-MinhaAba-tab-MeuPainel-panel-MeuBotao-pushbutton\df6a954f-fa93-4319-843a-30713f26ae76\scratchpad\rv\_lib.py")
opt = DB.Options(); opt.ComputeReferences = False
opt.DetailLevel = DB.ViewDetailLevel.Fine
opt.IncludeNonVisibleObjects = False

def solids(el):
    out = []
    ge = el.get_Geometry(opt)
    if ge is None: return out
    def rec(g):
        for o in g:
            if isinstance(o, DB.Solid):
                if o.Volume > 1e-9: out.append(o)
            elif isinstance(o, DB.GeometryInstance):
                rec(o.GetInstanceGeometry())
    rec(ge)
    return out

def pdbl(e, n):
    p = e.LookupParameter(n)
    try: return p.AsDouble()*FT if p else None
    except: return None

seen = {}
for fi in DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_GenericModel)\
         .OfClass(DB.FamilyInstance).WhereElementIsNotElementType():
    try: fn = fi.Symbol.FamilyName
    except: continue
    if fn in seen: continue
    seen[fn] = fi

res = []
for fn in sorted(seen):
    fi = seen[fn]; sym = fi.Symbol
    ss = solids(fi)
    vol = sum(s.Volume for s in ss) * (FT**3)
    # bbox do solido
    mn = [1e18]*3; mx = [-1e18]*3
    for s in ss:
        for e2 in s.Edges:
            for pt in [e2.AsCurve().GetEndPoint(0), e2.AsCurve().GetEndPoint(1)]:
                v = [pt.X*FT, pt.Y*FT, pt.Z*FT]
                for i in range(3):
                    mn[i] = min(mn[i], v[i]); mx[i] = max(mx[i], v[i])
    b = fi.get_BoundingBox(None)
    bb = [b.Min.X*FT, b.Min.Y*FT, b.Min.Z*FT, b.Max.X*FT, b.Max.Y*FT, b.Max.Z*FT] if b else None
    L = pdbl(fi, u"Comprimento_bloco") or pdbl(sym, u"Comprimento_bloco")
    H = pdbl(fi, u"Altura_bloco") or pdbl(sym, u"Altura_bloco")
    W = pdbl(fi, u"Largura_bloco") or pdbl(sym, u"Largura_bloco")
    res.append({"fam": fn, "sample_id": eid(fi), "n_solids": len(ss),
                "solid_vol_cm3": round(vol, 1),
                "solid_dims_cm": [round(mx[i]-mn[i], 2) for i in range(3)] if ss else None,
                "bbox_dims_cm": [round(bb[3]-bb[0], 2), round(bb[4]-bb[1], 2), round(bb[5]-bb[2], 2)] if bb else None,
                "param_LHW_cm": [round(L, 2) if L else None, round(H, 2) if H else None, round(W, 2) if W else None]})
w("solid_check.json", res)
print("%-38s %-10s %-22s %-22s %-20s" % ("FAMILIA", "vol_cm3", "solido(dx,dy,dz)", "bbox(dx,dy,dz)", "param(L,H,W)"))
for r in res:
    print("%-38s %-10s %-22s %-22s %-20s" % (r["fam"].encode("ascii","replace")[:38],
          r["solid_vol_cm3"], r["solid_dims_cm"], r["bbox_dims_cm"], r["param_LHW_cm"]))
