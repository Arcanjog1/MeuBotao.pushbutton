# -*- coding: utf-8 -*-
execfile(r"C:\Users\CIVIX\AppData\Local\Temp\claude\C--Users-CIVIX-OneDrive--rea-de-Trabalho-Scripts-extension-MinhaAba-tab-MeuPainel-panel-MeuBotao-pushbutton\df6a954f-fa93-4319-843a-30713f26ae76\scratchpad\rv\_lib.py")
import math, time

def pstr(e, name):
    p = e.LookupParameter(name)
    if p is None: return None
    try: return p.AsString()
    except: return None

def pdbl(e, name):
    p = e.LookupParameter(name)
    if p is None: return None
    try:
        v = p.AsDouble()
        return None if v is None else v * FT
    except: return None

def pint(e, name):
    p = e.LookupParameter(name)
    if p is None: return None
    try: return p.AsInteger()
    except: return None

lvlname = {}
for l in DB.FilteredElementCollector(doc).OfClass(DB.Level).ToElements():
    lvlname[eid(l)] = (nm(l), l.Elevation * FT)

typecache = {}
def typedims(sym):
    k = eid(sym)
    if k in typecache: return typecache[k]
    v = (pdbl(sym, u"Comprimento_bloco"), pdbl(sym, u"Altura_bloco"),
         pdbl(sym, u"Largura_bloco"), pstr(sym, u"Sigla"),
         sym.FamilyName, nm(sym))
    typecache[k] = v
    return v

t0 = time.time()
f = codecs.open(OUT + "\pieces.jsonl", "w", "utf-8")
col = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_GenericModel)\
        .OfClass(DB.FamilyInstance).WhereElementIsNotElementType()
n = 0; nobb = 0; noloc = 0
for fi in col:
    n += 1
    sym = fi.Symbol
    tL, tH, tW, sigla, famn, typn = typedims(sym)
    iL = pdbl(fi, u"Comprimento_bloco"); iH = pdbl(fi, u"Altura_bloco"); iW = pdbl(fi, u"Largura_bloco")
    L = iL if iL else tL
    H = iH if iH else tH
    W = iW if iW else tW
    lid = eid(fi.LevelId) if fi.LevelId else None
    lvn, lvz = lvlname.get(lid, (None, None))
    off = pdbl(fi, u"Deslocamento do hospedeiro")
    if off is None:
        p = fi.get_Parameter(DB.BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)
        off = p.AsDouble() * FT if p else None
    x = y = z = rot = None
    loc = fi.Location
    if isinstance(loc, DB.LocationPoint):
        pt = loc.Point
        x, y, z = pt.X * FT, pt.Y * FT, pt.Z * FT
        try: rot = math.degrees(loc.Rotation)
        except: rot = None
    else:
        noloc += 1
    bb = None
    try:
        b = fi.get_BoundingBox(None)
        if b:
            bb = [b.Min.X*FT, b.Min.Y*FT, b.Min.Z*FT, b.Max.X*FT, b.Max.Y*FT, b.Max.Z*FT]
        else: nobb += 1
    except: nobb += 1
    row = {
        "id": eid(fi), "uid": fi.UniqueId, "fam": famn, "typ": typn, "sigla": sigla,
        "parede": pstr(fi, u"Parede"), "local": pstr(fi, u"R\u00c9GGA_LOCAL"),
        "lvl_id": lid, "lvl": lvn, "lvl_z": lvz, "off": off,
        "x": x, "y": y, "z": z, "rot": rot,
        "L": L, "H": H, "W": W,
        "lintel": pint(fi, u"Lintel"), "arranque": pint(fi, u"Arranque"),
        "bb": bb,
    }
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
f.close()
print("PIECES=%d  no_bbox=%d  no_locpoint=%d  secs=%.1f" % (n, nobb, noloc, time.time()-t0))
