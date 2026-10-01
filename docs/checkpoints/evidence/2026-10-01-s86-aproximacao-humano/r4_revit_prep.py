# -*- coding: utf-8 -*-
# Rodada 4 (humano): no 'butanta testes' (por TITULO; a referencia nunca e' tocada) devolve as 19 aberturas
# deslocadas pelo microajuste para a posicao ORIGINAL (R1) e poe as 46 paredes com 260 cm (13 fiadas, R5).
# DRY=1 so' mostra.
import json, os, codecs
from Autodesk.Revit.DB import (FilteredElementCollector, Wall, ElementId, ElementTransformUtils, XYZ, Transaction,
                               BuiltInParameter)
import System
FT = 30.48
DRY = False
D = [d for d in doc.Application.Documents if d.Title == u"butanta testes"]
assert len(D) == 1
D = D[0]
P = os.path.join(u"C:\\", u"Users", u"CIVIX", u"AppData", u"Local", u"Temp", u"s85r4", u"revert_plan.json")
plan = json.loads(codecs.open(P, "r", "utf-8").read())
H = 260.0
log = []
t = Transaction(D, "S86 R1/R5: aberturas na posicao original + paredes 260 cm")
t.Start()
try:
    for p in plan:
        el = D.GetElement(ElementId(System.Int64(p["element_id"])))
        dx, dy = p["delta_xy_cm"]
        ElementTransformUtils.MoveElement(D, el.Id, XYZ(dx / FT, dy / FT, 0.0))
        c = el.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if c is not None and not c.IsReadOnly:
            c.Set(u"")
        log.append((p["element_id"], dx, dy))
    nw = 0
    for w in FilteredElementCollector(D).OfClass(Wall):
        top = w.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)
        if top is not None and top.AsElementId() != ElementId.InvalidElementId:
            log.append(("parede com restricao de topo", int(w.Id.Value)))
            continue
        hp = w.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)
        if abs(hp.AsDouble() * FT - H) > 0.01:
            hp.Set(H / FT)
            nw += 1
    if DRY:
        t.RollBack()
    else:
        t.Commit()
except Exception as ex:
    t.RollBack()
    raise
print("aberturas movidas", len([x for x in log if isinstance(x[0], int)]), "paredes ajustadas", nw, "dry", DRY)
print([x for x in log if not isinstance(x[0], int)][:5])
