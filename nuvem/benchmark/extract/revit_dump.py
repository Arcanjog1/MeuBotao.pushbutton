# -*- coding: utf-8 -*-
"""EXTRATOR READ-ONLY de um projeto Revit ja' modulado por uma pessoa.

Este arquivo NAO e' importado por ninguem: o CONTEUDO dele e' passado como
`code` para `mcp__revit-pyrevit__execute_revit_code` (ou colado num
console pyRevit). Ele roda dentro do Revit, em IronPython 2.7.

    1. open_document(caminho_do_rvt, detach=True se workshared)
    2. execute_revit_code(code=<conteudo deste arquivo>)
    3. Read(o .json cujo caminho e' impresso no fim)
    4. benchmark/extract/reconstruct.py transforma esse .json bruto em
       input.json + reference.json
    5. close_document(save=False)

CONTRATO DE SEGURANCA (a regra inegociavel do usuario - nunca alterar
.rvt de terceiros), o mesmo de `nuvem/diagnostico_modulacao_cross_projeto.py`:

  - NENHUMA Transaction/SubTransaction/TransactionGroup.
  - NENHUM FamilySymbol.Activate().
  - NENHUM override de cor/grafico de vista.
  - NENHUMA escrita no documento, em nenhuma hipotese.
  - So' escreve UM .json no diretorio TEMP do Windows.

DUAS ARMADILHAS REAIS DESTE AMBIENTE, ja' pagas:

  - **Acento quebra o `json.dumps` do IronPython 2.7** (`UnicodeDecodeError:
    'unknown' codec can't decode byte 0xc1`) - nomes de familia como
    "VEDACAO"/"PADRAO" tem acento no projeto real. Tudo passa por `S()`,
    que forca ASCII.
  - **`ElementId.IntegerValue` nao existe** nas versoes recentes (virou
    `.Value`), e `.Value` volta como `long`, que tambem nao serializa.
    `EID()` cobre os dois casos.

O que sai no JSON (schema bruto, versao 1):

    {"schema_version": 1, "document": "...", "level": {...},
     "types": [{"index", "type_name", "family", "length_cm", "height_cm",
                "width_cm", "symbol_id", "count"}],
     "instances": [[type_index, x_cm, y_cm, z_cm, rot_deg, mirrored], ...],
     "levels": [...], "walls": [...], "openings": [...], "warnings": [...]}

`walls`/`openings` saem vazios nos projetos ja' entregues (as paredes de
referencia e as portas/janelas nativas sao apagadas depois da modulacao -
ver PADRAO_MODULACAO.md); quando existirem, sao lidos e usados como
verdade, com o que a reconstrucao deduzir servindo so' de conferencia.
"""

REVIT_DUMP_SOURCE = r'''
# ---- CONFIGURACAO (sobrescrita pelo chamador prefixando atribuicoes) ----
DOC_TITLE_PREFIX = None    # None = documento ativo
LEVEL_NAME = None          # None = TODOS os niveis
MAX_INSTANCES = 0          # 0 = sem teto

import os
import json
import tempfile
import math
import traceback
from datetime import datetime

FEET_TO_CM = 30.48

DIM_PARAMS = {
    "length": ["Comprimento_bloco", "Comprimento", "Length", "Comprimento_Bloco"],
    "height": ["Altura_bloco", "Altura", "Height", "Altura_Bloco"],
    "width": ["Largura_bloco", "Largura", "Width", "Largura_Bloco"],
}


def S(v):
    """ASCII puro sempre - ver o cabecalho do modulo (json.dumps do
    IronPython 2.7 quebra com acento)."""
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
    """ElementId -> int. `.IntegerValue` sumiu nas versoes novas; `.Value`
    volta long, que o json nao serializa."""
    try:
        return int(element_id.IntegerValue)
    except Exception:
        try:
            return int(element_id.Value)
        except Exception:
            return -1


def param_cm(element, names):
    for name in names:
        try:
            p = element.LookupParameter(name)
        except Exception:
            p = None
        if p is not None and p.HasValue:
            try:
                return round(p.AsDouble() * FEET_TO_CM, 3)
            except Exception:
                continue
    return None


result = {
    "schema_version": 1,
    "generated_at": datetime.now().isoformat(),
    "document": None,
    "document_path": None,
    "level_filter": LEVEL_NAME,
    "levels": [],
    "types": [],
    "instances": [],
    "walls": [],
    "openings": [],
    "warnings": [],
}

target = doc
try:
    if DOC_TITLE_PREFIX:
        for d in doc.Application.Documents:
            if S(d.Title).startswith(DOC_TITLE_PREFIX):
                target = d
                break
    result["document"] = S(target.Title)
    result["document_path"] = S(target.PathName)
except Exception as exc:
    result["warnings"].append("documento: " + S(exc))

OUT_PATH = os.path.join(
    tempfile.gettempdir(),
    "benchmark_dump_{0}_{1}.json".format(
        "".join(ch if (ch.isalnum() or ch in "-_") else "_"
                for ch in (result["document"] or "doc"))[:40],
        datetime.now().strftime("%Y%m%d_%H%M%S"),
    ),
)


def write_partial():
    """Grava depois de cada secao - uma chamada MCP que estoure o tempo
    nunca pode levar junto tudo o que ja' foi lido."""
    try:
        handle = open(OUT_PATH, "w")
        try:
            json.dump(result, handle, ensure_ascii=True)
        finally:
            handle.close()
    except Exception:
        pass


# ---------------------------------------------------------------- niveis
level_by_id = {}
try:
    levels = DB.FilteredElementCollector(target).OfClass(DB.Level).ToElements()
    for lv in levels:
        entry = {
            "id": EID(lv.Id),
            "name": S(lv.Name),
            "elevation_cm": round(lv.Elevation * FEET_TO_CM, 2),
        }
        level_by_id[entry["id"]] = entry
        result["levels"].append(entry)
    result["levels"].sort(key=lambda e: e["elevation_cm"])
except Exception:
    result["warnings"].append("niveis: " + S(traceback.format_exc()))
write_partial()

target_level_ids = None
if LEVEL_NAME:
    target_level_ids = set(
        entry["id"] for entry in result["levels"] if entry["name"] == LEVEL_NAME
    )
    if not target_level_ids:
        result["warnings"].append("nivel '{0}' nao existe".format(S(LEVEL_NAME)))

# ------------------------------------------------------- blocos (pecas)
try:
    collector = DB.FilteredElementCollector(target) \
        .OfCategory(DB.BuiltInCategory.OST_GenericModel) \
        .WhereElementIsNotElementType().ToElements()

    type_index_by_symbol = {}
    types = []
    instances = []

    for inst in collector:
        try:
            if not isinstance(inst, DB.FamilyInstance):
                continue
            level_id = EID(inst.LevelId)
            if target_level_ids is not None and level_id not in target_level_ids:
                continue

            symbol = inst.Symbol
            symbol_id = EID(symbol.Id)
            index = type_index_by_symbol.get(symbol_id)
            if index is None:
                index = len(types)
                type_index_by_symbol[symbol_id] = index
                # `symbol.Name` levanta neste ambiente (property ambigua
                # no IronPython); `inst.Name` devolve o nome do TIPO, que
                # e' o que interessa.
                try:
                    family_name = S(symbol.Family.Name)
                except Exception:
                    family_name = None
                types.append({
                    "index": index,
                    "symbol_id": symbol_id,
                    "type_name": S(inst.Name),
                    "family": family_name,
                    "length_cm": param_cm(symbol, DIM_PARAMS["length"]),
                    "height_cm": param_cm(symbol, DIM_PARAMS["height"]),
                    "width_cm": param_cm(symbol, DIM_PARAMS["width"]),
                    "count": 0,
                })
            types[index]["count"] += 1

            location = inst.Location
            point = location.Point
            try:
                rotation_deg = round(math.degrees(location.Rotation) % 360.0, 3)
            except Exception:
                rotation_deg = 0.0
            try:
                mirrored = 1 if inst.Mirrored else 0
            except Exception:
                mirrored = 0

            instances.append([
                index,
                round(point.X * FEET_TO_CM, 2),
                round(point.Y * FEET_TO_CM, 2),
                round(point.Z * FEET_TO_CM, 2),
                rotation_deg,
                mirrored,
                level_id,
            ])
            if MAX_INSTANCES and len(instances) >= MAX_INSTANCES:
                result["warnings"].append(
                    "teto de {0} instancias atingido - dump PARCIAL".format(MAX_INSTANCES))
                break
        except Exception:
            continue

    result["types"] = types
    result["instances"] = instances
except Exception:
    result["warnings"].append("blocos: " + S(traceback.format_exc()))
write_partial()

# --------------------------------------------- paredes nativas (se houver)
try:
    for wall in DB.FilteredElementCollector(target).OfClass(DB.Wall).ToElements():
        try:
            location = wall.Location
            if not isinstance(location, DB.LocationCurve):
                continue
            level_id = EID(wall.LevelId)
            if target_level_ids is not None and level_id not in target_level_ids:
                continue
            curve = location.Curve
            p0 = curve.GetEndPoint(0)
            p1 = curve.GetEndPoint(1)
            result["walls"].append({
                "element_id": EID(wall.Id),
                "start_cm": [round(p0.X * FEET_TO_CM, 2), round(p0.Y * FEET_TO_CM, 2)],
                "end_cm": [round(p1.X * FEET_TO_CM, 2), round(p1.Y * FEET_TO_CM, 2)],
                "base_z_cm": round(min(p0.Z, p1.Z) * FEET_TO_CM, 2),
                "thickness_cm": round((wall.Width or 0.0) * FEET_TO_CM, 2),
                "level_id": level_id,
            })
        except Exception:
            continue
except Exception:
    result["warnings"].append("paredes: " + S(traceback.format_exc()))
write_partial()

# ------------------------------------------ portas/janelas nativas (idem)
try:
    for category in (DB.BuiltInCategory.OST_Doors, DB.BuiltInCategory.OST_Windows):
        for inst in DB.FilteredElementCollector(target).OfCategory(category) \
                .WhereElementIsNotElementType().ToElements():
            try:
                level_id = EID(inst.LevelId)
                if target_level_ids is not None and level_id not in target_level_ids:
                    continue
                bbox = inst.get_BoundingBox(None)
                host_id = EID(inst.Host.Id) if inst.Host is not None else -1
                width_cm = param_cm(inst, ["Largura_abertura", "Largura", "Width"])
                if width_cm is None and inst.Symbol is not None:
                    width_cm = param_cm(inst.Symbol, ["Largura_abertura", "Largura", "Width"])
                sill_cm = param_cm(inst, ["Peitoril", "Sill Height", "Altura_peitoril"])
                result["openings"].append({
                    "element_id": EID(inst.Id),
                    "kind": "door" if category == DB.BuiltInCategory.OST_Doors else "window",
                    "host_wall_id": host_id,
                    "level_id": level_id,
                    "width_cm": width_cm,
                    "sill_cm": sill_cm,
                    "bbox_cm": None if bbox is None else [
                        round(bbox.Min.X * FEET_TO_CM, 2), round(bbox.Min.Y * FEET_TO_CM, 2),
                        round(bbox.Min.Z * FEET_TO_CM, 2), round(bbox.Max.X * FEET_TO_CM, 2),
                        round(bbox.Max.Y * FEET_TO_CM, 2), round(bbox.Max.Z * FEET_TO_CM, 2),
                    ],
                })
            except Exception:
                continue
except Exception:
    result["warnings"].append("aberturas: " + S(traceback.format_exc()))
write_partial()

print("EXTRACAO_OK")
print("instancias={0} tipos={1} paredes={2} aberturas={3}".format(
    len(result["instances"]), len(result["types"]),
    len(result["walls"]), len(result["openings"])))
print("OUT_PATH={0}".format(OUT_PATH))
'''


def build_code(doc_title_prefix=None, level_name=None, max_instances=0):
    """Codigo pronto para `execute_revit_code`, com a configuracao no
    topo. Escrever a configuracao como codigo (em vez de um parametro do
    MCP) e' o que mantem o script rodavel tambem colado a mao num console
    pyRevit, sem nenhuma adaptacao."""
    header = "DOC_TITLE_PREFIX = {0!r}\nLEVEL_NAME = {1!r}\nMAX_INSTANCES = {2!r}\n".format(
        doc_title_prefix, level_name, int(max_instances or 0)
    )
    # Comenta as tres linhas de default do corpo (elas existem para o
    # arquivo continuar rodavel colado a mao, sem header nenhum).
    lines = []
    for line in REVIT_DUMP_SOURCE.splitlines():
        stripped = line.strip()
        if any(stripped.startswith(name + " =")
               for name in ("DOC_TITLE_PREFIX", "LEVEL_NAME", "MAX_INSTANCES")):
            line = "# " + line
        lines.append(line)
    return header + "\n".join(lines)


if __name__ == "__main__":
    print(build_code())
