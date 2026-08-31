# -*- coding: utf-8 -*-
"""EXTRATOR READ-ONLY do CATALOGO DE BLOCOS a partir dos TIPOS CARREGADOS.

Por que este modulo existe (Etapa 2B.1, pedido do usuario 2026-08-31): a
primeira baseline real usou o catalogo derivado do `reference.json`, ou
seja, das pecas que a PESSOA colocou. Isso e' vazamento do gabarito para a
entrada - o solver recebia, de graca, quais pecas a solucao humana usou.
Aceitavel como diagnostico, inaceitavel como baseline oficial.

Aqui o catalogo sai do PROPRIO documento INPUT, dos `FamilySymbol`
CARREGADOS - sem depender de nenhuma instancia colocada. E' exatamente o
que `core/wall_modeling.py::load_fixed_block_catalog` faz na producao, com
duas diferencas obrigatorias:

  1. `DOC_TITLE_PREFIX` explicito (nunca o documento ativo - ver
     `revit_input_real_dump.py`);
  2. **NENHUM `FamilySymbol.Activate()`** e nenhuma `Transaction`. A
     producao ativa os simbolos porque vai INSTANCIAR depois; aqui so' se
     le'. Consequencia real e registrada: `_extract_block_cells_local_from_symbol`
     precisa da symbol ATIVA para devolver os EdgeLoops, entao um tipo
     ainda nao ativado devolve `cells_local_cm: []` e sai marcado com
     `cells_source: "indisponivel_sem_activate"`. `solver_bridge.catalog_from_input`
     ja trata celula ausente reconstruindo-a simetricamente e registrando
     em `metadata.cells_reconstructed` - o que se perde e' so' o ajuste
     fino de alinhamento de celula das pecas assimetricas (B34/B54).

O catalogo canonico (os 6 codigos logicos, com nome EXATO de familia e de
tipo) NAO e' redefinido aqui: e' copiado de
`BLOCK_FAMILY_CATALOG_DEFINITIONS`, para nao existir uma segunda verdade
sobre o que e' um B34. Se a producao mudar a definicao, a copia tem que ser
revista junto.

Alem dos 6 codigos, o dump lista TODOS os `FamilySymbol` de Modelos
Genericos carregados no documento (`all_loaded_types`), para a comparacao
de catalogo INPUT x REFERENCE (item 5 do pedido) - que e' DIAGNOSTICO e
nunca altera o catalogo entregue ao solver.

CONTRATO DE SEGURANCA: nenhuma Transaction, nenhum Activate, nenhuma
escrita no documento; so' um .json no TEMP.
"""

import datetime


# Copia verbatim de `core/wall_modeling.py::BLOCK_FAMILY_CATALOG_DEFINITIONS`
# (2026-08-31). Nao inventar: nome EXATO de familia e de tipo, sem prefixo,
# sem heuristica, sem tolerancia.
BLOCK_FAMILY_CATALOG_DEFINITIONS = {
    "B39": {"family_name": "BLOCO INTEIRO - 14x19x39", "type_name": "BLOCO INTEIRO - 14x19x39",
            "is_special_bond": False, "is_compensator": False},
    "B34": {"family_name": "BLOCO 34 - 14x19x34", "type_name": "BLOCO 34 - 14x19x34",
            "is_special_bond": True, "is_compensator": False},
    "B54": {"family_name": "BLOCO 54 - 14x19x54", "type_name": "BLOCO 54 - 14x19x54",
            "is_special_bond": True, "is_compensator": False},
    "B19": {"family_name": "MEIO BLOCO - 14x19x19", "type_name": "MEIO BLOCO - 14x19x19",
            "is_special_bond": False, "is_compensator": False},
    "C09": {"family_name": "COMPENSADOR 14x19x9", "type_name": "COMPENSADOR 14x19x9",
            "is_special_bond": False, "is_compensator": True},
    "C04": {"family_name": "PASTILHA - 14x19X4", "type_name": "PASTILHA - 14x19X4",
            "is_special_bond": False, "is_compensator": True},
}


CATALOG_DUMP_SOURCE = r'''
# ---- CONFIGURACAO (sobrescrita pelo chamador prefixando atribuicoes) ----
DOC_TITLE_PREFIX = None    # OBRIGATORIO - nao ha fallback para o doc ativo
DEFINITIONS = None         # OBRIGATORIO - BLOCK_FAMILY_CATALOG_DEFINITIONS

import os
import json
import tempfile
import traceback
from datetime import datetime

FEET_TO_CM = 30.48


def S(v):
    if v is None:
        return None
    try:
        if isinstance(v, unicode):
            return v.encode("ascii", "replace")
        return str(v).decode("latin-1", "replace").encode("ascii", "replace")
    except Exception:
        return "?"


def EID(element_id):
    try:
        return int(element_id.IntegerValue)
    except Exception:
        try:
            return int(element_id.Value)
        except Exception:
            return -1


if not DOC_TITLE_PREFIX or not DEFINITIONS:
    raise Exception("DOC_TITLE_PREFIX e DEFINITIONS sao obrigatorios.")

_matches = [d for d in __revit__.Application.Documents
            if S(d.Title).startswith(DOC_TITLE_PREFIX)]
if len(_matches) != 1:
    raise Exception("DOC_TITLE_PREFIX '{0}' casou com {1} documento(s).".format(
        DOC_TITLE_PREFIX, len(_matches)))
target = _matches[0]


def type_param_cm(element, names):
    """core/wall_modeling.py::_type_param_cm - so' parametro Double."""
    for name in names:
        try:
            param = element.LookupParameter(name)
        except Exception:
            param = None
        if (param is not None and param.HasValue
                and param.StorageType == DB.StorageType.Double):
            return round(param.AsDouble() * FEET_TO_CM, 4)
    return None


def type_name_of(symbol):
    try:
        param = symbol.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
        return S(param.AsString()) if param else None
    except Exception:
        return None


def cells_local_cm(symbol):
    """core/wall_modeling.py::_extract_block_cells_local_from_symbol.

    Devolve (celulas, motivo). SEM Activate() a geometria costuma vir
    vazia - isso e' registrado, nunca disfarcado."""
    try:
        options = DB.Options()
        options.DetailLevel = DB.ViewDetailLevel.Fine
        options.IncludeNonVisibleObjects = False
        geometry = symbol.get_Geometry(options)
        if geometry is None:
            return [], "sem_geometria"
        solids = []

        def collect(geom_iterable):
            for item in geom_iterable:
                if isinstance(item, DB.Solid) and item.Volume > 1e-9:
                    solids.append(item)
                elif isinstance(item, DB.GeometryInstance):
                    collect(item.GetInstanceGeometry())

        collect(geometry)
        if not solids:
            return [], "indisponivel_sem_activate"

        top_face = None
        for solid in solids:
            for face in solid.Faces:
                if not isinstance(face, DB.PlanarFace):
                    continue
                normal = face.FaceNormal
                if abs(normal.Z) <= 0.99 or normal.Z <= 0:
                    continue
                if top_face is None or face.Area > top_face.Area:
                    top_face = face
        if top_face is None:
            return [], "sem_face_superior_plana"

        loops = top_face.EdgeLoops
        cells = []
        for index in range(loops.Size):
            if index == 0:
                continue  # contorno externo
            points = []
            for edge in loops.get_Item(index):
                for point in edge.Tessellate():
                    points.append(point)
            if not points:
                continue
            xs = [p.X for p in points]
            ys = [p.Y for p in points]
            cells.append({
                "center_cm": [round((min(xs) + max(xs)) / 2.0 * FEET_TO_CM, 4),
                              round((min(ys) + max(ys)) / 2.0 * FEET_TO_CM, 4)],
                "size_cm": [round((max(xs) - min(xs)) * FEET_TO_CM, 4),
                            round((max(ys) - min(ys)) * FEET_TO_CM, 4)],
            })
        return cells, "geometria_lida"
    except Exception:
        return [], "excecao_na_geometria"


result = {
    "schema_version": 1,
    "generated_at": datetime.now().isoformat(),
    "unit": "cm (1 ft = 30.48 cm)",
    "source_document": {
        "title": S(target.Title),
        "path": S(target.PathName),
        "role": "INPUT_REAL",
    },
    "catalog": {},
    "missing": [],
    "all_loaded_types": [],
    "warnings": [],
}

# ---- todos os tipos de Modelo Generico carregados (DIAGNOSTICO) --------
symbols_by_key = {}
try:
    collector = DB.FilteredElementCollector(target).OfClass(DB.FamilySymbol) \
        .OfCategory(DB.BuiltInCategory.OST_GenericModel)
    for symbol in collector:
        try:
            family_name = S(symbol.Family.Name) if symbol.Family else None
        except Exception:
            family_name = None
        tname = type_name_of(symbol)
        entry = {
            "symbol_id": EID(symbol.Id),
            "family": family_name,
            "type_name": tname,
            "is_active": bool(symbol.IsActive),
            "length_cm": type_param_cm(symbol, ["Comprimento_bloco", "Comprimento"]),
            "height_cm": type_param_cm(symbol, ["Altura_bloco", "Altura"]),
            "width_cm": type_param_cm(symbol, ["Largura_bloco", "Largura"]),
        }
        result["all_loaded_types"].append(entry)
        symbols_by_key[(family_name, tname)] = symbol
except Exception:
    result["warnings"].append("tipos carregados: " + S(traceback.format_exc()))

result["all_loaded_types"].sort(key=lambda e: (e["family"] or "", e["type_name"] or ""))

# ---- catalogo fixo dos 6 codigos logicos ------------------------------
for logical_code in sorted(DEFINITIONS):
    definition = DEFINITIONS[logical_code]
    symbol = symbols_by_key.get((definition["family_name"], definition["type_name"]))
    if symbol is None:
        result["missing"].append({
            "logical_code": logical_code,
            "family_name": definition["family_name"],
            "type_name": definition["type_name"],
            "reason": "familia/tipo nao esta carregado no documento INPUT.",
        })
        continue
    length_cm = type_param_cm(symbol, ["Comprimento_bloco"])
    if length_cm is None:
        result["missing"].append({
            "logical_code": logical_code,
            "family_name": definition["family_name"],
            "type_name": definition["type_name"],
            "reason": "carregada, mas sem o parametro de TIPO 'Comprimento_bloco'.",
        })
        continue
    cells, cells_source = cells_local_cm(symbol)
    result["catalog"][logical_code] = {
        "logical_code": logical_code,
        "family": definition["family_name"],
        "type_name": definition["type_name"],
        "symbol_id": EID(symbol.Id),
        "symbol_is_active": bool(symbol.IsActive),
        "length_cm": length_cm,
        "height_cm": type_param_cm(symbol, ["Altura_bloco"]),
        "width_cm": type_param_cm(symbol, ["Largura_bloco"]),
        "cells_local_cm": cells,
        "cells_source": cells_source,
        "is_special_bond": bool(definition["is_special_bond"]),
        "is_compensator": bool(definition["is_compensator"]),
        "origin": "FamilySymbol CARREGADO no documento INPUT (sem instancia, sem Activate)",
    }

OUT_PATH = os.path.join(
    tempfile.gettempdir(),
    "catalog_dump_{0}_{1}.json".format(
        "".join(ch if (ch.isalnum() or ch in "-_") else "_"
                for ch in (result["source_document"]["title"] or "doc"))[:40],
        datetime.now().strftime("%Y%m%d_%H%M%S"),
    ),
)
handle = open(OUT_PATH, "w")
try:
    json.dump(result, handle, ensure_ascii=True)
finally:
    handle.close()

print("EXTRACAO_CATALOGO_OK")
print("documento={0}".format(result["source_document"]["title"]))
print("codigos={0} faltando={1} tipos_carregados={2}".format(
    len(result["catalog"]), len(result["missing"]), len(result["all_loaded_types"])))
for code in sorted(result["catalog"]):
    entry = result["catalog"][code]
    print("  {0}: L={1} H={2} W={3} celulas={4} ({5}) ativo={6}".format(
        code, entry["length_cm"], entry["height_cm"], entry["width_cm"],
        len(entry["cells_local_cm"]), entry["cells_source"], entry["symbol_is_active"]))
for item in result["missing"]:
    print("  FALTA {0}: {1}".format(item["logical_code"], item["reason"]))
print("OUT_PATH={0}".format(OUT_PATH))
'''


def build_code(doc_title_prefix, definitions=None):
    """Codigo pronto para `execute_revit_code`."""
    if not doc_title_prefix:
        raise ValueError("doc_title_prefix e' obrigatorio - ver o cabecalho do modulo.")
    header = "DOC_TITLE_PREFIX = {0!r}\nDEFINITIONS = {1!r}\n".format(
        doc_title_prefix, definitions or BLOCK_FAMILY_CATALOG_DEFINITIONS)
    lines = []
    for line in CATALOG_DUMP_SOURCE.splitlines():
        stripped = line.strip()
        if any(stripped.startswith(name + " =")
               for name in ("DOC_TITLE_PREFIX", "DEFINITIONS")):
            line = "# " + line
        lines.append(line)
    return header + "\n".join(lines)


def build_catalog(dump):
    """Dump bruto -> o dict `catalog` do `input.json` (schema do `model.py`).

    Cada item leva `origin`, para o relatorio nunca deixar duvida de onde a
    dimensao veio. Funcao PURA."""
    source = dict(dump.get("source_document") or {})
    if not source.get("title"):
        raise ValueError("dump sem source_document.title - proveniencia e' obrigatoria")

    catalog = {}
    for code, entry in (dump.get("catalog") or {}).items():
        catalog[code] = {
            "logical_code": code,
            "length_cm": entry["length_cm"],
            "height_cm": entry["height_cm"],
            "width_cm": entry["width_cm"],
            "cells_local_cm": entry.get("cells_local_cm") or [],
            "is_special_bond": entry["is_special_bond"],
            "is_compensator": entry["is_compensator"],
            "family": entry.get("family"),
            "type_name": entry.get("type_name"),
            "origin": entry.get("origin"),
            "cells_source": entry.get("cells_source"),
            "source_document": source.get("title"),
        }
    return catalog


def compare_catalogs(input_catalog, reference_catalog, tolerance_cm=0.5):
    """DIAGNOSTICO puro (item 5 do pedido). NUNCA altera o catalogo
    entregue ao solver - so' diz se as duas leituras sao consistentes."""
    in_codes = set(input_catalog or {})
    ref_codes = set(reference_catalog or {})

    divergent = []
    for code in sorted(in_codes & ref_codes):
        a, b = input_catalog[code], reference_catalog[code]
        for field in ("length_cm", "height_cm", "width_cm"):
            av, bv = a.get(field), b.get(field)
            if av is None or bv is None:
                divergent.append({"code": code, "field": field,
                                  "input": av, "reference": bv,
                                  "reason": "ausente em um dos lados"})
            elif abs(float(av) - float(bv)) > tolerance_cm:
                divergent.append({"code": code, "field": field,
                                  "input": av, "reference": bv,
                                  "delta_cm": round(float(av) - float(bv), 3)})

    # Aliases: mesmo tamanho (LxHxW) sob codigos diferentes - o sinal de que
    # o gabarito chamou de outro nome a MESMA peca.
    def dims(entry):
        return (round(float(entry.get("length_cm") or 0), 1),
                round(float(entry.get("height_cm") or 0), 1),
                round(float(entry.get("width_cm") or 0), 1))

    by_dims = {}
    for code in sorted(in_codes):
        by_dims.setdefault(dims(input_catalog[code]), []).append(("input", code))
    for code in sorted(ref_codes):
        by_dims.setdefault(dims(reference_catalog[code]), []).append(("reference", code))
    aliases = [
        {"dims_cm": list(key), "codes": entries}
        for key, entries in sorted(by_dims.items())
        if len(set(code for _side, code in entries)) > 1
    ]

    return {
        "in_both": sorted(in_codes & ref_codes),
        "only_in_input": sorted(in_codes - ref_codes),
        "only_in_reference": sorted(ref_codes - in_codes),
        "divergent_dimensions": divergent,
        "aliases_same_dimensions": aliases,
        "note": "comparacao e' DIAGNOSTICO: nao altera o catalogo entregue ao solver",
        "compared_at": datetime.datetime.now().strftime("%Y-%m-%d"),
    }
