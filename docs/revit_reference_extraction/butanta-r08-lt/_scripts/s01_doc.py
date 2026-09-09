# -*- coding: utf-8 -*-
import clr
print("TITLE=%s" % doc.Title)
print("PATH=%s" % doc.PathName)
try:
    print("APPVER=%s" % doc.Application.VersionName)
    print("APPBUILD=%s" % doc.Application.VersionBuild)
    print("APPNUM=%s" % doc.Application.VersionNumber)
except Exception as e:
    print("APPVER_ERR=%s" % e)
print("ISFAMILY=%s" % doc.IsFamilyDocument)
print("ISWORKSHARED=%s" % doc.IsWorkshared)
# unidades
try:
    fo = doc.GetUnits().GetFormatOptions(DB.SpecTypeId.Length)
    print("LENGTH_UNIT=%s" % fo.GetUnitTypeId().TypeId)
except Exception as e:
    print("UNIT_ERR=%s" % e)
# niveis
lv = DB.FilteredElementCollector(doc).OfClass(DB.Level).ToElements()
print("NLEVELS=%d" % len(lv))
for l in lv:
    print("LEVEL|%s|%s|%.4f ft|%.2f cm" % (l.Id, l.Name, l.Elevation, l.Elevation*30.48))
# contagem total
allel = DB.FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()
print("NELEMENTS_INSTANCE=%d" % len(allel))
types = DB.FilteredElementCollector(doc).WhereElementIsElementType().ToElements()
print("NELEMENTS_TYPE=%d" % len(types))
