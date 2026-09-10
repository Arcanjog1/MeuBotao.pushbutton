# -*- coding: utf-8 -*-
import json, codecs
OUT = r"C:\Users\CIVIX\AppData\Local\Temp\claude\C--Users-CIVIX-OneDrive--rea-de-Trabalho-Scripts-extension-MinhaAba-tab-MeuPainel-panel-MeuBotao-pushbutton\df6a954f-fa93-4319-843a-30713f26ae76\scratchpad\out"
FT = 30.48  # ft -> cm

def w(name, obj):
    f = codecs.open(OUT + "\\" + name, "w", "utf-8")
    f.write(json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True))
    f.close()

def eid(e):
    """ElementId -> int, compativel 2024+ e legado."""
    if e is None:
        return None
    i = e.Id if hasattr(e, "Id") else e
    if i is None:
        return None
    try:
        return int(i.Value)
    except Exception:
        pass
    try:
        return int(i.IntegerValue)
    except Exception:
        return None

def nm(e):
    """Nome do elemento, robusto no IronPython."""
    if e is None:
        return None
    try:
        return DB.Element.Name.GetValue(e)
    except Exception:
        pass
    try:
        return e.Name
    except Exception:
        pass
    try:
        p = e.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
        if p:
            return p.AsString()
    except Exception:
        pass
    return None

def catname(e):
    try:
        c = e.Category
        return c.Name if c else None
    except Exception:
        return None

def catbic(e):
    try:
        c = e.Category
        return eid(c) if c else None
    except Exception:
        return None
