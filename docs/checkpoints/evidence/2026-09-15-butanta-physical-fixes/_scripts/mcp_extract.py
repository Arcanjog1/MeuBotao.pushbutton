# -*- coding: utf-8 -*-
# Enviado ao MCP (IronPython 2.7). SOMENTE LEITURA. Extrai pecas de alvenaria,
# aberturas e Walls de UM documento (por Title exato) e UM nivel para JSON.
# Parametros: DOC_TITLE, LEVEL_NAME, OUT_PATH (definidos antes deste corpo).
import io, json, time

t0 = time.time()
D = None
for _d in doc.Application.Documents:
    if _d.Title == DOC_TITLE:
        D = _d
assert D is not None, "doc nao encontrado"
modified_before = D.IsModified

lv_id = None
lv_elev = None
for l in DB.FilteredElementCollector(D).OfClass(DB.Level).ToElements():
    if l.Name == LEVEL_NAME:
        lv_id = l.Id.Value
        lv_elev = l.ProjectElevation
assert lv_id is not None, "nivel nao encontrado"

F = 30.48
BIP = DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS
PIECE_PREFIXES = (u"BLOCO", u"MEIO", u"COMPENSADOR", u"PASTILHA", u"CANALETA", u"MEIA CANALETA")
type_info = {}


def _tname(sym):
    if sym is None:
        return u"?"
    p = sym.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME)
    return p.AsString() if p is not None else u"?"


def tinfo(tid):
    k = tid.Value
    if k not in type_info:
        sym = D.GetElement(tid)
        type_info[k] = (sym.FamilyName if sym is not None else u"?", _tname(sym))
    return type_info[k]


def pval(el, name):
    p = el.LookupParameter(name)
    if p is None:
        return None
    try:
        if p.StorageType == DB.StorageType.Double:
            return p.AsDouble()
        if p.StorageType == DB.StorageType.Integer:
            return int(p.AsInteger())
        return p.AsString()
    except Exception:
        return None


pieces = []
openings = []
ids = list(DB.FilteredElementCollector(D).OfClass(DB.FamilyInstance).WhereElementIsNotElementType().ToElementIds())
for eid in ids:
    el = D.GetElement(eid)
    if el.LevelId.Value != lv_id:
        continue
    fam, typ = tinfo(el.GetTypeId())
    is_piece = fam.upper().startswith(PIECE_PREFIXES)
    is_opening = (el.LookupParameter(u"Largura_abertura") is not None)
    if not (is_piece or is_opening):
        continue
    tr = el.GetTransform()
    bb = el.get_BoundingBox(None)
    rec = {
        "id": int(eid.Value), "fam": fam, "typ": typ,
        "o": [tr.Origin.X * F, tr.Origin.Y * F, (tr.Origin.Z - lv_elev) * F],
        "bx": [tr.BasisX.X, tr.BasisX.Y, tr.BasisX.Z],
        "by": [tr.BasisY.X, tr.BasisY.Y, tr.BasisY.Z],
        "mir": bool(el.Mirrored), "hf": bool(el.HandFlipped), "ff": bool(el.FacingFlipped),
        "bb": ([bb.Min.X * F, bb.Min.Y * F, (bb.Min.Z - lv_elev) * F, bb.Max.X * F, bb.Max.Y * F, (bb.Max.Z - lv_elev) * F]
               if bb is not None else None),
    }
    if is_piece:
        c = el.get_Parameter(BIP)
        rec["cm"] = c.AsString() if c is not None else None
        lb = pval(el, u"Comprimento_bloco")
        rec["len_param"] = (lb * F if isinstance(lb, float) else None)
        pieces.append(rec)
    else:
        for nm in (u"Largura_abertura", u"Altura_abertura", u"Peitoril"):
            v = pval(el, nm)
            rec[nm] = (v * F if isinstance(v, float) else v)
        # vao real: pontos da geometria projetados nos eixos locais
        pts = []
        opt = DB.Options()
        opt.IncludeNonVisibleObjects = False
        geo = el.get_Geometry(opt)
        if geo is not None:
            for g in geo:
                inst_geo = g.GetInstanceGeometry() if isinstance(g, DB.GeometryInstance) else [g]
                for s in inst_geo:
                    if isinstance(s, DB.Solid) and s.Volume > 1e-9:
                        for e in s.Edges:
                            for p in e.Tessellate():
                                pts.append((p.X, p.Y, p.Z))
        if pts:
            ox, oy = tr.Origin.X, tr.Origin.Y
            bxx, bxy = tr.BasisX.X, tr.BasisX.Y
            us = [((x - ox) * bxx + (y - oy) * bxy) * F for (x, y, z) in pts]
            zs = [(z - lv_elev) * F for (x, y, z) in pts]
            rec["geo_u"] = [min(us), max(us)]
            rec["geo_z"] = [min(zs), max(zs)]
        openings.append(rec)

walls = []
for w in DB.FilteredElementCollector(D).OfCategory(DB.BuiltInCategory.OST_Walls).WhereElementIsNotElementType().ToElements():
    if w.LevelId.Value != lv_id:
        continue
    loc = w.Location
    if not isinstance(loc, DB.LocationCurve):
        continue
    c = loc.Curve
    p0, p1 = c.GetEndPoint(0), c.GetEndPoint(1)
    walls.append({"id": int(w.Id.Value), "uid": w.UniqueId, "typ": _tname(w.WallType),
                  "p0": [p0.X * F, p0.Y * F], "p1": [p1.X * F, p1.Y * F], "width": w.Width * F})

def _asc(v):
    # IronPython: json.dumps tropeca em str nao-ASCII; escapa manualmente.
    if isinstance(v, basestring):
        return u"".join((ch if ord(ch) < 128 else ("\\u%04x" % ord(ch))) for ch in unicode(v))
    if isinstance(v, dict):
        return dict((_asc(k), _asc(x)) for k, x in v.items())
    if isinstance(v, (list, tuple)):
        return [_asc(x) for x in v]
    return v


out = {"doc": D.Title, "level": LEVEL_NAME, "level_elev_cm": lv_elev * F, "pieces": pieces,
       "openings": openings, "walls": walls, "modified_before": modified_before}
with io.open(OUT_PATH, "w", encoding="utf-8") as fh:
    fh.write(unicode(json.dumps(_asc(out), ensure_ascii=True)))
print("doc=%s pieces=%d openings=%d walls=%d em %.1fs modified_before=%s modified_after=%s" % (
    D.Title.encode("ascii", "backslashreplace"), len(pieces), len(openings), len(walls),
    time.time() - t0, modified_before, D.IsModified))
