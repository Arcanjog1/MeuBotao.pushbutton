# -*- coding: utf-8 -*-
# Rodada 4 (humano): vistas do PAVIMENTO INTEIRO no 'butanta testes' (por titulo; a referencia nunca e' tocada):
# um corte de elevacao por parede modulada (34, comprimento inteiro) + uma vista 3D do pavimento. Sem Walls e sem
# imports, detalhe fino. Nomes "S86 ...": recria se ja' existir. Guarda os ids em S["s86_views"].
import sys
wm = sys.modules["core.wall_modeling"]
from core.engine import wall_stepper as ws
from Autodesk.Revit.DB import (FilteredElementCollector, ViewFamilyType, ViewFamily, ViewSection, View3D, View,
                               Transaction, BoundingBoxXYZ, Transform, XYZ, ElementId, BuiltInCategory,
                               ImportInstance, ViewDetailLevel, DisplayStyle)
from System.Collections.Generic import List
T = [d for d in doc.Application.Documents if d.Title == u"butanta testes"][0]
S = wm._MCP_STATE; h = S["h"]
FT = 30.48
vsec = [v for v in FilteredElementCollector(T).OfClass(ViewFamilyType) if v.ViewFamily == ViewFamily.Section][0]
v3d = [v for v in FilteredElementCollector(T).OfClass(ViewFamilyType) if v.ViewFamily == ViewFamily.ThreeDimensional][0]
H = h.wall_height_ft * FT


def hide_noise(view):
    view.SetCategoryHidden(ElementId(BuiltInCategory.OST_Walls), True)
    imps = List[ElementId]([i.Id for i in FilteredElementCollector(T).OfClass(ImportInstance) if i.CanBeHidden(view)])
    if imps.Count:
        view.HideElements(imps)
    view.DetailLevel = ViewDetailLevel.Fine


out = {}
t = Transaction(T, "S86 - vistas do pavimento inteiro (Claude)")
t.Start()
try:
    old = [v.Id for v in FilteredElementCollector(T).OfClass(View).ToElements()
           if not v.IsTemplate and v.Name.startswith(u"S86 ")]
    for vid in old:
        T.Delete(vid)
    for wi in range(len(h.walls_to_create)):
        p0, _p1, d, L, _th = ws._wall_axis_and_length(h.walls_to_create, wi)
        Lcm = L * FT
        name = u"S86 W%02d (%d cm)" % (wi, int(round(Lcm)))
        mid = L / 2.0
        origin = XYZ(p0.X + d.X * mid, p0.Y + d.Y * mid, h.base_z_abs + (H / 2.0) / FT)
        right = XYZ(d.X, d.Y, 0.0).Normalize()
        up = XYZ(0, 0, 1)
        view_dir = right.CrossProduct(up)
        tr = Transform.Identity
        tr.Origin = origin
        tr.BasisX = right
        tr.BasisY = up
        tr.BasisZ = view_dir
        box = BoundingBoxXYZ()
        box.Transform = tr
        half = (Lcm / 2.0 + 25.0) / FT
        box.Min = XYZ(-half, -(H / 2.0 + 15.0) / FT, -12.0 / FT)
        box.Max = XYZ(half, (H / 2.0 + 15.0) / FT, 12.0 / FT)
        view = ViewSection.CreateSection(T, vsec.Id, box)
        view.Name = name
        hide_noise(view)
        view.Scale = 25
        out[name] = wm._eid_int(view.Id)
    iso = View3D.CreateIsometric(T, v3d.Id)
    iso.Name = u"S86 Pavimento 3D"
    hide_noise(iso)
    iso.DisplayStyle = DisplayStyle.ShadingWithEdges
    out[u"S86 Pavimento 3D"] = wm._eid_int(iso.Id)
    print("commit", t.Commit())
except Exception:
    t.RollBack()
    raise
S["s86_views"] = out
print(len(out), "vistas")
