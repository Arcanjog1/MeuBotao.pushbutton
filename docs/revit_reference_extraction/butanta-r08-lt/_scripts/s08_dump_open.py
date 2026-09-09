# -*- coding: utf-8 -*-
execfile(r"C:\Users\CIVIX\AppData\Local\Temp\claude\C--Users-CIVIX-OneDrive--rea-de-Trabalho-Scripts-extension-MinhaAba-tab-MeuPainel-panel-MeuBotao-pushbutton\df6a954f-fa93-4319-843a-30713f26ae76\scratchpad\rv\_lib.py")
import math
def pstr(e,n):
    p=e.LookupParameter(n)
    try: return p.AsString() if p else None
    except: return None
def pdbl(e,n):
    p=e.LookupParameter(n)
    try: return p.AsDouble()*FT if p else None
    except: return None

lvlname={}
for l in DB.FilteredElementCollector(doc).OfClass(DB.Level).ToElements():
    lvlname[eid(l)]=(nm(l), l.Elevation*FT)

rows=[]
col=DB.FilteredElementCollector(doc).OfClass(DB.FamilyInstance).WhereElementIsNotElementType()
for fi in col:
    try: fn=fi.Symbol.FamilyName
    except: continue
    if not fn.startswith(u"Abertura de janela"): continue
    loc=fi.Location; x=y=z=rot=None
    if isinstance(loc,DB.LocationPoint):
        p=loc.Point; x,y,z=p.X*FT,p.Y*FT,p.Z*FT
        try: rot=math.degrees(loc.Rotation)
        except: pass
    bb=None
    try:
        b=fi.get_BoundingBox(None)
        if b: bb=[b.Min.X*FT,b.Min.Y*FT,b.Min.Z*FT,b.Max.X*FT,b.Max.Y*FT,b.Max.Z*FT]
    except: pass
    lid=eid(fi.LevelId) if fi.LevelId else None
    lvn,lvz=lvlname.get(lid,(None,None))
    fo=None; ho=None
    try:
        v=fi.FacingOrientation; fo=[v.X,v.Y,v.Z]
        v2=fi.HandOrientation; ho=[v2.X,v2.Y,v2.Z]
    except: pass
    rows.append({
      "id":eid(fi),"uid":fi.UniqueId,"fam":fn,"typ":nm(fi.Symbol),
      "parede":pstr(fi,u"Parede"),"titulo":pstr(fi,u"T\u00edtulo_abertura"),
      "largura":pdbl(fi,u"Largura_abertura"),"altura":pdbl(fi,u"Altura_abertura"),
      "peitoril":pdbl(fi,u"Altura_peitoril"),"peitoril2":pdbl(fi,u"Peitoril"),
      "lvl_id":lid,"lvl":lvn,"lvl_z":lvz,"off":pdbl(fi,u"Deslocamento do hospedeiro"),
      "x":x,"y":y,"z":z,"rot":rot,"facing":fo,"hand":ho,"bb":bb})
w("openings_raw.json", rows)
print("N=%d"%len(rows))
tit={}
for r in rows: tit[r["titulo"]]=tit.get(r["titulo"],0)+1
print("TITULOS=%s"%tit)
lv={}
for r in rows: lv[r["lvl"]]=lv.get(r["lvl"],0)+1
for k in sorted(lv,key=lambda x:-lv[x]): print("  %4d %s"%(lv[k],(k or "?").encode("ascii","replace")))
