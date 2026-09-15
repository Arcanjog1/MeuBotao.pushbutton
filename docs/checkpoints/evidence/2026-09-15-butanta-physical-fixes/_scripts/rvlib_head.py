# -*- coding: utf-8 -*-
import System
from Autodesk.Revit import DB
OUTDIR = "C:/Users/twitc/AppData/Local/Temp/claude/C--Users-twitc-Desktop-Scripts-extension-MinhaAba-tab-MeuPainel-panel-teste-perf-pushbutton/55d5e0b9-5f60-4a1f-886d-c0808e7c3ccd/scratchpad/rv/"
def _j(o):
    if o is None: return "null"
    if o is True: return "true"
    if o is False: return "false"
    if isinstance(o, (int, long)): return str(o)
    if isinstance(o, float): return repr(o)
    if isinstance(o, dict):
        return "{" + ",".join(_j(unicode(k)) + ":" + _j(v) for k, v in o.items()) + "}"
    if isinstance(o, (list, tuple)):
        return "[" + ",".join(_j(x) for x in o) + "]"
    s = unicode(o)
    BS = unichr(92); QT = unichr(34)
    r = [QT]
    for ch in s:
        c = ord(ch)
        if ch == QT: r.append(BS + QT)
        elif ch == BS: r.append(BS + BS)
        elif c < 32 or c > 126: r.append(BS + u'u%04x' % c)
        else: r.append(ch)
    r.append(QT)
    return u"".join(r)
def dump(name, obj):
    System.IO.File.WriteAllText(OUTDIR + name, _j(obj), System.Text.UTF8Encoding(False))
def eid(e):
    try: return e.Value
    except: return e.IntegerValue
FT = 30.48
