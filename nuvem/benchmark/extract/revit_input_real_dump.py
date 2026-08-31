# -*- coding: utf-8 -*-
"""EXTRATOR READ-ONLY do lado INPUT do benchmark: o projeto CRU.

Irmao de `revit_dump.py` (que extrai o lado REFERENCE, ja' modulado).
Enquanto `revit_dump.py` le' BLOCOS ja' colocados, este aqui le' o que
existe ANTES da modulacao - as linhas do CAD por layer e as aberturas - e
produz o payload `input_real` que `wall_modeling_bridge.run_wall_modeling`
consome (ver `nuvem/benchmark/README.md`, secao "Wall Modeling (Etapa 2A)").

DOIS DOCUMENTOS ABERTOS AO MESMO TEMPO (pedido do usuario, 2026-08-31)
---------------------------------------------------------------------
Nesta bancada o Revit tem o projeto CRU e o projeto JA MODULADO abertos na
MESMA instancia. Por isso `DOC_TITLE_PREFIX` e' OBRIGATORIO aqui - ao
contrario de `revit_dump.py`, este extrator NAO tem fallback para o
documento ativo. Trocar de aba no Revit no meio da extracao nao pode mudar
de onde os dados vieram; se o prefixo nao casar com exatamente UM documento
aberto, o script levanta em vez de adivinhar.

Todo payload carrega `source_document` (`title`, `path`, `role`) - nenhum
artefato do benchmark pode existir sem dizer de qual .rvt ele saiu.

CONTRATO DE SEGURANCA (identico ao de `revit_dump.py`):
  - NENHUMA Transaction/SubTransaction/TransactionGroup.
  - NENHUM FamilySymbol.Activate().
  - NENHUM override de cor/grafico de vista.
  - NENHUMA escrita no documento, em nenhuma hipotese.
  - So' escreve UM .json no diretorio TEMP do Windows.

FIDELIDADE A PRODUCAO
---------------------
As funcoes copiadas de `core/wall_modeling.py` sao reproduzidas com o mesmo
comportamento, porque qualquer desvio muda a GEOMETRIA de entrada:

  - `extract_lines_by_layer` - desce em GeometryInstance e explode PolyLine
    (parede desenhada como polilinha no CAD chega como UM objeto).
  - `_param_value_as_feet` - Largura_abertura/Altura_abertura/Peitoril podem
    ser parametro de NUMERO (valor digitado em cm) ou de COMPRIMENTO (ja' em
    pes); tratar um como o outro faz uma abertura de 91cm virar 91 PES.
  - `_opening_center_from_geometry` - o ponto de insercao destas familias
    fica deslocado do centro do vao de forma sistematica por tipo (17,0cm /
    23,0cm / 24,5cm, medido em 71 de 71 instancias). Usar a insercao
    desloca lateralmente toda verga/peitoril.

A copia e' deliberada: `core/wall_modeling.py` so' roda dentro do botao, com
`doc` global e as janelas de setup; aqui precisamos das MESMAS regras com
`Document` explicito e sem UI. Se alguma delas mudar na producao, esta copia
tem que ser revisada junto.

USO
---
    py -3 -c "import sys; sys.path.insert(0,'nuvem'); \
      from benchmark.extract import revit_input_real_dump as r; \
      print(r.build_code('TESTE', 'Arquitetura'))"

Passar a saida como `code` para `mcp__revit-pyrevit__execute_revit_code`, ler
o `.json` do `OUT_PATH` impresso, e converter com `build_input_real()`
(funcao pura, roda em CPython fora do Revit).
"""

import datetime


INPUT_REAL_DUMP_SOURCE = r'''
# ---- CONFIGURACAO (sobrescrita pelo chamador prefixando atribuicoes) ----
DOC_TITLE_PREFIX = None    # OBRIGATORIO - nao ha fallback para o doc ativo
LAYER_FILTER = None        # None = TODOS os layers do CAD
IMPORT_TYPE_NAME = None    # None = TODOS os ImportInstance do documento
LEVEL_NAME = None          # None = nao filtra aberturas por nivel

import os
import json
import math
import tempfile
import traceback
from datetime import datetime

FEET_TO_CM = 30.48
FEET_PER_METER = 1.0 / 0.3048

OPENING_WIDTH_PARAM = "Largura_abertura"
OPENING_HEIGHT_PARAM = "Altura_abertura"
OPENING_SILL_PARAM = "Peitoril"
OPENING_LEVEL_OFFSET_PARAM = "Elevacao do nivel"
OPENING_GEOMETRY_WIDTH_TOLERANCE_FT = 0.02 * FEET_PER_METER


def S(v):
    """ASCII puro - json.dumps do IronPython 2.7 quebra com acento, e os
    layers deste projeto tem ("Sanitario", "Mobiliario")."""
    if v is None:
        return None
    try:
        if isinstance(v, unicode):
            return v.encode("ascii", "replace")
        return str(v).decode("latin-1", "replace").encode("ascii", "replace")
    except Exception:
        try:
            return repr(v)[:80]
        except Exception:
            return "?"


def EID(element_id):
    """`.IntegerValue` sumiu nas versoes novas; `.Value` volta long."""
    try:
        return int(element_id.IntegerValue)
    except Exception:
        try:
            return int(element_id.Value)
        except Exception:
            return -1


def cm(value_ft):
    return round(value_ft * FEET_TO_CM, 4)


# ------------------------------------------------ documento EXPLICITO
if not DOC_TITLE_PREFIX:
    raise Exception(
        "DOC_TITLE_PREFIX e' obrigatorio: ha' mais de um documento aberto e "
        "este extrator nunca usa o documento ATIVO (ver cabecalho do modulo)."
    )

_matches = [d for d in __revit__.Application.Documents
            if S(d.Title).startswith(DOC_TITLE_PREFIX)]
if len(_matches) != 1:
    raise Exception(
        "DOC_TITLE_PREFIX '{0}' casou com {1} documento(s): {2}. "
        "Precisa casar com exatamente 1.".format(
            DOC_TITLE_PREFIX, len(_matches), [S(d.Title) for d in _matches])
    )
target = _matches[0]

result = {
    "schema_version": 1,
    "generated_at": datetime.now().isoformat(),
    "unit": "cm (1 ft = 30.48 cm)",
    "source_document": {
        "title": S(target.Title),
        "path": S(target.PathName),
        "role": "INPUT_REAL",
        "is_family_document": bool(target.IsFamilyDocument),
        "is_workshared": bool(target.IsWorkshared),
    },
    "layer_filter": LAYER_FILTER,
    "import_type_filter": IMPORT_TYPE_NAME,
    "level_filter": LEVEL_NAME,
    "levels": [],
    "imports": [],
    "segments": [],
    "openings": [],
    "layer_summary": {},
    "warnings": [],
}

OUT_PATH = os.path.join(
    tempfile.gettempdir(),
    "input_real_dump_{0}_{1}.json".format(
        "".join(ch if (ch.isalnum() or ch in "-_") else "_"
                for ch in (result["source_document"]["title"] or "doc"))[:40],
        datetime.now().strftime("%Y%m%d_%H%M%S"),
    ),
)


def write_partial():
    try:
        handle = open(OUT_PATH, "w")
        try:
            json.dump(result, handle, ensure_ascii=True)
        finally:
            handle.close()
    except Exception:
        pass


# ---------------------------------------------------------------- niveis
try:
    for lv in DB.FilteredElementCollector(target).OfClass(DB.Level) \
            .WhereElementIsNotElementType().ToElements():
        result["levels"].append({
            "id": EID(lv.Id),
            "name": S(lv.Name),
            "elevation_cm": cm(lv.Elevation),
        })
    result["levels"].sort(key=lambda e: e["elevation_cm"])
except Exception:
    result["warnings"].append("niveis: " + S(traceback.format_exc()))
write_partial()


# ------------------------------- linhas do CAD por layer (Document explicito)
def get_layer_name(geom_obj, document):
    """core/wall_modeling.py::get_layer_name, com `document` explicito no
    lugar do `doc` global."""
    style_id = geom_obj.GraphicsStyleId
    if style_id and style_id != DB.ElementId.InvalidElementId:
        style = document.GetElement(style_id)
        if isinstance(style, DB.GraphicsStyle):
            if style.GraphicsStyleCategory:
                return S(style.GraphicsStyleCategory.Name)
            return S(style.Name)
    return None


def extract_lines_by_layer(geom_element, lines_by_layer, document):
    """core/wall_modeling.py::extract_lines_by_layer, verbatim salvo o
    `document` explicito - inclusive a explosao de PolyLine e o descarte de
    curvas degeneradas."""
    for geom_obj in geom_element:
        if isinstance(geom_obj, DB.GeometryInstance):
            extract_lines_by_layer(geom_obj.GetInstanceGeometry(), lines_by_layer, document)
            continue

        if isinstance(geom_obj, DB.Line):
            if geom_obj.ApproximateLength < 1e-6:
                continue
            layer = get_layer_name(geom_obj, document)
            if layer:
                lines_by_layer.setdefault(layer, []).append(
                    (geom_obj.GetEndPoint(0), geom_obj.GetEndPoint(1)))
            continue

        if isinstance(geom_obj, DB.PolyLine):
            layer = get_layer_name(geom_obj, document)
            if not layer:
                continue
            points = list(geom_obj.GetCoordinates())
            for i in range(len(points) - 1):
                p0, p1 = points[i], points[i + 1]
                if p0.DistanceTo(p1) < 1e-6:
                    continue
                lines_by_layer.setdefault(layer, []).append((p0, p1))


try:
    options = DB.Options()
    options.ComputeReferences = False
    options.IncludeNonVisibleObjects = False

    lines_by_layer = {}
    for inst in DB.FilteredElementCollector(target).OfClass(DB.ImportInstance) \
            .WhereElementIsNotElementType().ToElements():
        symbol = target.GetElement(inst.GetTypeId())
        type_name = None
        try:
            p = symbol.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
            if p:
                type_name = S(p.AsString())
        except Exception:
            pass
        if IMPORT_TYPE_NAME and type_name != IMPORT_TYPE_NAME:
            continue
        transform = inst.GetTotalTransform()
        result["imports"].append({
            "element_id": EID(inst.Id),
            "type_name": type_name,
            "pinned": bool(inst.Pinned),
            "origin_cm": [cm(transform.Origin.X), cm(transform.Origin.Y),
                          cm(transform.Origin.Z)],
            "basis_x": [transform.BasisX.X, transform.BasisX.Y, transform.BasisX.Z],
            "basis_y": [transform.BasisY.X, transform.BasisY.Y, transform.BasisY.Z],
            "basis_z": [transform.BasisZ.X, transform.BasisZ.Y, transform.BasisZ.Z],
        })
        extract_lines_by_layer(inst.get_Geometry(options), lines_by_layer, target)

    for layer in sorted(lines_by_layer):
        pairs = lines_by_layer[layer]
        total_cm = 0.0
        for p0, p1 in pairs:
            total_cm += math.sqrt((p1.X - p0.X) ** 2 + (p1.Y - p0.Y) ** 2) * FEET_TO_CM
        result["layer_summary"][layer] = {
            "count": len(pairs),
            "total_length_cm": round(total_cm, 2),
        }
        if LAYER_FILTER and layer != LAYER_FILTER:
            continue
        for p0, p1 in pairs:
            result["segments"].append({
                "layer": layer,
                "start": [cm(p0.X), cm(p0.Y)],
                "end": [cm(p1.X), cm(p1.Y)],
            })
except Exception:
    result["warnings"].append("linhas do CAD: " + S(traceback.format_exc()))
write_partial()


# ------------------------------------------------------------- aberturas
def param_value_as_feet(param):
    """core/wall_modeling.py::_param_value_as_feet, verbatim. Distingue
    parametro de NUMERO (valor digitado em cm) de parametro de COMPRIMENTO
    (ja' em pes) comparando AsDouble() com AsValueString()."""
    raw = param.AsDouble()
    try:
        display_str = param.AsValueString()
        display_num = float(display_str.strip().split()[0].replace(".", "").replace(",", "."))
    except Exception:
        return raw
    if abs(raw - display_num) < 0.001:
        return (raw / 100.0) * FEET_PER_METER
    return raw


def lookup_param_value(instance, param_names):
    """core/wall_modeling.py::_lookup_param_value - procura na INSTANCIA e,
    se nao achar, no Symbol (parametro de TIPO)."""
    for name in param_names:
        param = instance.LookupParameter(name)
        if param is not None and param.HasValue:
            return param_value_as_feet(param)
    symbol = getattr(instance, "Symbol", None)
    if symbol is not None:
        for name in param_names:
            param = symbol.LookupParameter(name)
            if param is not None and param.HasValue:
                return param_value_as_feet(param)
    return None


def collect_instance_geometry_points(inst):
    """core/wall_modeling.py::_collect_instance_geometry_points."""
    opts = DB.Options()
    opts.IncludeNonVisibleObjects = True
    opts.DetailLevel = DB.ViewDetailLevel.Fine
    points = []

    def walk(geom_element):
        for geom_obj in geom_element:
            if isinstance(geom_obj, DB.GeometryInstance):
                walk(geom_obj.GetInstanceGeometry())
            elif isinstance(geom_obj, DB.Curve):
                points.append(geom_obj.GetEndPoint(0))
                points.append(geom_obj.GetEndPoint(1))
            elif isinstance(geom_obj, DB.Solid) and geom_obj.Volume > 1e-9:
                for edge in geom_obj.Edges:
                    curve = edge.AsCurve()
                    points.append(curve.GetEndPoint(0))
                    points.append(curve.GetEndPoint(1))

    geom = inst.get_Geometry(opts)
    if geom is not None:
        walk(geom)
    return points


def opening_center_from_geometry(inst, width_ft):
    """core/wall_modeling.py::_opening_center_from_geometry. Projeta a
    geometria nos eixos LOCAIS da instancia (robusto a rotacao) e devolve
    (center, largura_medida) para quem chama conferir contra
    Largura_abertura antes de confiar no centro."""
    points = collect_instance_geometry_points(inst)
    if not points:
        return None, None
    transform = inst.GetTransform()
    origin = DB.XYZ(transform.Origin.X, transform.Origin.Y, 0.0)
    basis_x = DB.XYZ(transform.BasisX.X, transform.BasisX.Y, 0.0)
    if basis_x.GetLength() < 1e-9:
        return None, None
    basis_x = basis_x.Normalize()
    basis_y = DB.XYZ(-basis_x.Y, basis_x.X, 0.0)

    us, vs = [], []
    for p in points:
        rel = DB.XYZ(p.X, p.Y, 0.0) - origin
        us.append(rel.DotProduct(basis_x))
        vs.append(rel.DotProduct(basis_y))
    u_mid = (min(us) + max(us)) / 2.0
    v_mid = (min(vs) + max(vs)) / 2.0
    center = origin + basis_x * u_mid + basis_y * v_mid
    return center, (max(us) - min(us))


try:
    level_by_id = dict((e["id"], e) for e in result["levels"])
    for inst in DB.FilteredElementCollector(target).OfClass(DB.FamilyInstance) \
            .WhereElementIsNotElementType():
        try:
            width_ft = lookup_param_value(inst, [OPENING_WIDTH_PARAM])
            height_ft = lookup_param_value(inst, [OPENING_HEIGHT_PARAM])
            sill_ft = lookup_param_value(inst, [OPENING_SILL_PARAM])
            # Modo AUTOMATICO (allow_bbox_fallback=False): sem os 3
            # parametros nao ha' como afirmar que a familia e' abertura.
            if width_ft is None or height_ft is None or sill_ft is None:
                continue
            if width_ft <= 1e-6 or height_ft <= 1e-6:
                continue

            level_id = EID(inst.LevelId)
            if LEVEL_NAME is not None:
                entry = level_by_id.get(level_id)
                if entry is None or entry["name"] != LEVEL_NAME:
                    continue

            bbox = inst.get_BoundingBox(None)
            bbox_center_cm = None
            if bbox is not None:
                mid = (bbox.Min + bbox.Max) * 0.5
                bbox_center_cm = [cm(mid.X), cm(mid.Y)]

            location = inst.Location
            if hasattr(location, "Point"):
                insertion = location.Point
            elif bbox is not None:
                insertion = (bbox.Min + bbox.Max) * 0.5
            else:
                continue

            center = DB.XYZ(insertion.X, insertion.Y, 0.0)
            center_source = "insercao"
            geom_center, measured_ft = opening_center_from_geometry(inst, width_ft)
            if (geom_center is not None and measured_ft is not None and
                    abs(measured_ft - width_ft) <= OPENING_GEOMETRY_WIDTH_TOLERANCE_FT):
                center = geom_center
                center_source = "geometria"

            level = level_by_id.get(level_id)
            level_elevation_ft = (level["elevation_cm"] / FEET_TO_CM) if level else insertion.Z
            level_offset_ft = lookup_param_value(
                # Escapes em vez do literal acentuado: o codigo gerado por
                # `build_code` e' gravado e lido de volta por `execfile` no
                # IronPython 2.7, que sem cookie de encoding quebra em
                # qualquer byte nao-ASCII do fonte.
                inst, [OPENING_LEVEL_OFFSET_PARAM,
                       u"Eleva\u00e7\u00e3o do n\u00edvel", u"Elevacao"]
            ) or 0.0
            sill_z_abs = level_elevation_ft + level_offset_ft + sill_ft
            head_z_abs = sill_z_abs + height_ft

            result["openings"].append({
                "element_id": str(EID(inst.Id)),
                "center_cm": [cm(center.X), cm(center.Y)],
                "insertion_cm": [cm(insertion.X), cm(insertion.Y)],
                "bbox_center_cm": bbox_center_cm,
                "width_cm": cm(width_ft),
                "height_cm": cm(height_ft),
                "sill_cm": cm(sill_z_abs),
                "head_cm": cm(head_z_abs),
                "sill_param_cm": cm(sill_ft),
                "center_source": center_source,
                "level_id": level_id,
                "level_name": (level["name"] if level else None),
                "type_name": S(inst.Name),
                "category": S(inst.Category.Name) if inst.Category else None,
            })
        except Exception:
            continue
except Exception:
    result["warnings"].append("aberturas: " + S(traceback.format_exc()))
write_partial()

print("EXTRACAO_INPUT_REAL_OK")
print("documento={0}".format(result["source_document"]["title"]))
print("segmentos={0} layers={1} imports={2} aberturas={3}".format(
    len(result["segments"]), len(result["layer_summary"]),
    len(result["imports"]), len(result["openings"])))
print("OUT_PATH={0}".format(OUT_PATH))
'''


def build_code(doc_title_prefix, layer_filter=None,
               import_type_name=None, level_name=None):
    """Codigo pronto para `execute_revit_code`, com a configuracao no topo.

    `doc_title_prefix` e' POSICIONAL e obrigatorio de proposito: o extrator
    nunca cai no documento ativo (ver cabecalho do modulo)."""
    if not doc_title_prefix:
        raise ValueError(
            "doc_title_prefix e' obrigatorio - com dois .rvt abertos, deixar "
            "o extrator escolher o documento ATIVO e' exatamente o erro que "
            "este modulo existe para impedir."
        )
    header = (
        "DOC_TITLE_PREFIX = {0!r}\n"
        "LAYER_FILTER = {1!r}\n"
        "IMPORT_TYPE_NAME = {2!r}\n"
        "LEVEL_NAME = {3!r}\n"
    ).format(doc_title_prefix, layer_filter, import_type_name, level_name)

    lines = []
    for line in INPUT_REAL_DUMP_SOURCE.splitlines():
        stripped = line.strip()
        if any(stripped.startswith(name + " =")
               for name in ("DOC_TITLE_PREFIX", "LAYER_FILTER",
                            "IMPORT_TYPE_NAME", "LEVEL_NAME")):
            line = "# " + line
        lines.append(line)
    return header + "\n".join(lines)


def redact_source_document(source):
    """Troca `path` (caminho absoluto local - `C:\\Users\\...`, share de
    rede `T:\\...`) por `filename` (so' o nome do arquivo) +
    `original_path_redacted: true`.

    Etapa 2B.1, passo de higiene (2026-08-31): o caminho absoluto nao e'
    necessario para identificar o projeto geometricamente - `title` +
    `filename` + `role` ja bastam, e ninguem no codigo LE `path`/
    `document_path` para decidir nada (busca confirmada em
    `nuvem/benchmark/*.py` antes desta mudanca). Manter o caminho local
    so' acopla o artefato versionado a uma maquina/rede especifica,
    sem ganho nenhum.

    NAO apaga proveniencia: `title` continua completo, e
    `original_path_redacted: true` deixa explicito que a informacao existia
    e foi removida de proposito - diferente de nunca ter sido capturada."""
    source = dict(source)
    path = source.pop("path", None)
    if path:
        filename = path.replace("\\", "/").rsplit("/", 1)[-1]
        source["filename"] = filename
        source["original_path_redacted"] = True
    return source


def build_input_real(dump, project_id, setup_frozen, metadata=None):
    """Converte o dump bruto no payload `input_real` que
    `wall_modeling_bridge.run_wall_modeling` consome. Funcao PURA - roda em
    CPython, fora do Revit.

    `setup_frozen` e' a versao congelada das escolhas de `ask_setup`; este
    modulo NAO inventa nenhuma delas (o bridge rejeita campo faltando, de
    proposito - um default errado mudaria a geometria)."""
    raw_source = dict(dump.get("source_document") or {})
    if not raw_source.get("title"):
        raise ValueError("dump sem source_document.title - proveniencia e' obrigatoria")
    raw_source.setdefault("role", "INPUT_REAL")
    source = redact_source_document(raw_source)

    payload = {
        "schema_version": 1,
        "project_id": project_id,
        "source": "input_real",
        "source_document": source,
        "setup_frozen": dict(setup_frozen),
        "segments": list(dump.get("segments") or []),
        "openings": [
            {
                "element_id": o["element_id"],
                "center_cm": o["center_cm"],
                "bbox_center_cm": o.get("bbox_center_cm"),
                "width_cm": o["width_cm"],
                "sill_cm": o["sill_cm"],
                "head_cm": o["head_cm"],
                "center_source": o.get("center_source"),
            }
            for o in (dump.get("openings") or [])
        ],
        "metadata": dict(metadata or {}),
    }
    payload["metadata"].update({
        "extracted_at": dump.get("generated_at"),
        "extracted_by": "benchmark/extract/revit_input_real_dump.py via "
                        "mcp__revit-pyrevit__execute_revit_code (READ-ONLY)",
        "converted_at": datetime.datetime.now().strftime("%Y-%m-%d"),
        "document": source.get("title"),
        "document_filename": source.get("filename"),
        "role": source.get("role"),
        "layer_summary": dump.get("layer_summary"),
        "imports": dump.get("imports"),
        "levels": dump.get("levels"),
        "segments_total": len(payload["segments"]),
        "openings_total": len(payload["openings"]),
        "openings_source": "revit_family_params (Largura_abertura/"
                           "Altura_abertura/Peitoril) - modo automatico",
        "dump_warnings": dump.get("warnings") or [],
    })
    return payload
