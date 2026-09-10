# -*- coding: utf-8 -*-
execfile(r"C:\Users\CIVIX\AppData\Local\Temp\claude\C--Users-CIVIX-OneDrive--rea-de-Trabalho-Scripts-extension-MinhaAba-tab-MeuPainel-panel-MeuBotao-pushbutton\df6a954f-fa93-4319-843a-30713f26ae76\scratchpad\rv\_lib.py")
KEYS = [u"VERGA", u"CONTRAVERGA", u"LINTEL", u"COUNTER", u"CINTA", u"OMBREIRA", u"BONECA"]
# instancias por tipo
cnt = {}
for fi in DB.FilteredElementCollector(doc).OfClass(DB.FamilyInstance).WhereElementIsNotElementType():
    try: k = eid(fi.Symbol)
    except: continue
    cnt[k] = cnt.get(k, 0) + 1
found = []
for s in DB.FilteredElementCollector(doc).OfClass(DB.FamilySymbol).ToElements():
    try:
        fam = s.FamilyName; typ = nm(s)
    except: continue
    hay = (u"%s %s" % (fam, typ)).upper()
    if any(k in hay for k in KEYS):
        found.append({"fam": fam, "typ": typ, "type_id": eid(s), "cat": catname(s),
                      "instances": cnt.get(eid(s), 0)})
print("FAMILIAS/TIPOS COM VERGA/CONTRAVERGA/LINTEL/CINTA = %d" % len(found))
for f in found:
    print(u"  %-45s | %-28s | %-22s | inst=%d" % (f["fam"], f["typ"], f["cat"], f["instances"]))
w("verga_search.json", found)
# todas as Family (documento) com esses nomes
fams = []
for f in DB.FilteredElementCollector(doc).OfClass(DB.Family).ToElements():
    n2 = nm(f)
    if n2 and any(k in n2.upper() for k in KEYS):
        fams.append(n2)
print("FAMILIES (doc) = %s" % [x.encode("ascii","replace") for x in fams])
# parametro 'Lintel': quantas instancias com valor 1?
n1 = 0; n0 = 0; nn = 0
for fi in DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_GenericModel).OfClass(DB.FamilyInstance).WhereElementIsNotElementType():
    p = fi.LookupParameter(u"Lintel")
    if p is None: nn += 1
    elif p.AsInteger() == 1: n1 += 1
    else: n0 += 1
print("param Lintel: =1 -> %d ; =0 -> %d ; ausente -> %d" % (n1, n0, nn))
