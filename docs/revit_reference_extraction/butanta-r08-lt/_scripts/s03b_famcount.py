# -*- coding: utf-8 -*-
execfile(r"C:\Users\CIVIX\AppData\Local\Temp\claude\C--Users-CIVIX-OneDrive--rea-de-Trabalho-Scripts-extension-MinhaAba-tab-MeuPainel-panel-MeuBotao-pushbutton\df6a954f-fa93-4319-843a-30713f26ae76\scratchpad\rv\_lib.py")

rows = {}
col = DB.FilteredElementCollector(doc).OfClass(DB.FamilyInstance).WhereElementIsNotElementType()
n = 0
errs = {}
for fi in col:
    n += 1
    try:
        sym = fi.Symbol
        fam = sym.FamilyName
        typ = nm(sym)
    except Exception, ex:
        fam, typ = "<err>", "<err>"
        errs[str(ex)[:120]] = errs.get(str(ex)[:120], 0) + 1
    cn = catname(fi)
    k = u"%s||%s||%s" % (cn, fam, typ)
    rows[k] = rows.get(k, 0) + 1
print("N_FAMILYINSTANCE=%d" % n)
print("N_DISTINCT=%d" % len(rows))
print("ERRS=%s" % errs)
w("famtype_counts.json", rows)
tot = {}
for k, v in rows.items():
    cn = k.split(u"||")[0]
    tot[cn] = tot.get(cn, 0) + v
for k in sorted(tot, key=lambda x: -tot[x]):
    print("%8d  %s" % (tot[k], k.encode("ascii", "replace")))
