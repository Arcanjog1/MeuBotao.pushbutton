# -*- coding: utf-8 -*-
"""Diagnostico READ-ONLY de modulacao de alvenaria, para rodar contra
projetos Revit DE TERCEIROS via `mcp__revit-pyrevit__execute_revit_code`.

Ver o plano completo: `estou-quero-fazer-isso-wild-stardust.md`
(pasta de planos do Claude Code). Este arquivo NAO faz parte do pipeline
do botao (Script.py/core/wall_modeling.py) - e' uma ferramenta separada,
usada colando o CONTEUDO deste arquivo (ou lendo-o com a ferramenta Read
e passando como `code`) para `execute_revit_code`, um projeto aberto por
vez.

CONTRATO DE SEGURANCA (a regra inegociavel do usuario: nunca alterar os
arquivos .rvt de terceiros):
  - NENHUMA Transaction/SubTransaction/TransactionGroup e' aberta aqui.
  - NENHUM FamilySymbol.Activate() e' chamado - so' lemos geometria/
    parametros de simbolos que JA estao ativos por terem >=1 instancia
    colocada no modelo (isso e' automatico, nao precisamos ativar nada).
  - NENHUM override de cor/grafico de vista e' aplicado.
  - NENHUMA escrita no documento, em nenhuma hipotese.
  - Este script so' ESCREVE um arquivo .json no diretorio TEMP do
    Windows - nunca na pasta do projeto, nunca no proprio .rvt.
  - Depois de rodar, o chamador (Claude) fecha o documento com
    close_document(save=False) - este script nao fecha o documento
    sozinho (execute_revit_code nao deveria misturar isso).

Como usar (por projeto, um de cada vez):
  1. open_document(caminho_do_rvt, detach=True se for workshared)
  2. get_revit_model_info / get_revit_status como sanity check
  3. execute_revit_code(code=<conteudo deste arquivo>)
  4. Read(caminho do .json impresso no final da execucao)
  5. close_document(save=False)

Nada aqui e' garantido perfeito de primeira - a extracao de geometria de
celulas (EdgeLoops da face superior) segue o mesmo metodo ja validado em
core/wall_modeling.py (_extract_block_cells_local_from_symbol), mas
precisa ser confirmada ao vivo no primeiro projeto piloto, como toda
geometria deste repo sempre foi (ver memoria do projeto - "medido, nao
suposto"). Qualquer secao que falhar fica com "error" no proprio JSON,
nunca derruba o resto do diagnostico.
"""

import os
import json
import tempfile
import traceback
from datetime import datetime

FEET_TO_CM = 30.48

DIM_PARAM_CANDIDATES = {
    "length": ["Comprimento_bloco", "Comprimento", "Length", "Comprimento_Bloco"],
    "height": ["Altura_bloco", "Altura", "Height", "Altura_Bloco"],
    "width": ["Largura_bloco", "Largura", "Width", "Largura_Bloco"],
}
OPENING_WIDTH_PARAM_CANDIDATES = [
    "Largura_abertura", "Largura_vao", "Largura_Abertura", "Width",
]
OPENING_SILL_PARAM_CANDIDATES = ["Peitoril", "Sill Height", "Altura_peitoril"]
OPENING_HEIGHT_PARAM_CANDIDATES = ["Altura_abertura", "Height", "Altura_Abertura"]

result = {
    "generated_at": datetime.now().isoformat(),
    "document_title": None,
    "document_path": None,
    "warnings": [],
    "block_catalog_candidates": [],
    "walls": {"error": "nao processado ainda"},
    "openings": {"error": "nao processado ainda"},
    "block_instances": {"error": "nao processado ainda"},
    "levels": {"error": "nao processado ainda"},
}


def _out_path():
    safe_title = "documento"
    try:
        safe_title = "".join(
            ch if (ch.isalnum() or ch in "-_") else "_"
            for ch in doc.Title
        )[:60]
    except Exception:
        pass
    filename = "modulacao_diagnostico_{}_{}.json".format(
        safe_title, datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    return os.path.join(tempfile.gettempdir(), filename)


OUT_PATH = _out_path()


def _write_partial():
    """Grava o estado atual do `result` - chamado apos cada secao, para
    nunca perder tudo se uma chamada MCP der timeout no meio (mesmo
    padrao ja usado no pipeline principal com log incremental em
    %TEMP%). ensure_ascii=True de proposito: evita o bug ja conhecido
    do IronPython 2.7 gravando texto acentuado em modo ascii (ver
    _save_log_to_file em core/wall_modeling.py) - o JSON fica 100% ASCII
    (acentos viram \\uXXXX), decodificavel por qualquer leitor json."""
    try:
        with open(OUT_PATH, "w") as handle:
            json.dump(result, handle, ensure_ascii=True, indent=2)
    except Exception:
        pass


def _param_value_cm(element, names):
    for name in names:
        try:
            p = element.LookupParameter(name)
        except Exception:
            p = None
        if p is not None and p.HasValue:
            try:
                return p.AsDouble() * FEET_TO_CM, name
            except Exception:
                continue
    return None, None


def _find_dim_params_on_symbol(symbol):
    found = {}
    param_names_used = {}
    for key, candidates in DIM_PARAM_CANDIDATES.items():
        val, used_name = _param_value_cm(symbol, candidates)
        if val is not None:
            found[key] = round(val, 3)
            param_names_used[key] = used_name
    return found, param_names_used


# ---------------------------------------------------------------------
# 0) Identificacao do documento (sempre primeiro, nao pode falhar)
# ---------------------------------------------------------------------
try:
    result["document_title"] = doc.Title
    result["document_path"] = doc.PathName
except Exception as exc:
    result["warnings"].append("Falha lendo titulo/caminho: {}".format(exc))
_write_partial()


# ---------------------------------------------------------------------
# A) Catalogo de blocos candidatos - so' tipos com >=1 instancia colocada
#    e >=2 dos 3 parametros de dimensao plausiveis. NUNCA ativa simbolo.
# ---------------------------------------------------------------------
try:
    all_generic = DB.FilteredElementCollector(doc) \
        .OfCategory(DB.BuiltInCategory.OST_GenericModel) \
        .WhereElementIsNotElementType() \
        .ToElements()

    by_symbol = {}
    for inst in all_generic:
        if not isinstance(inst, DB.FamilyInstance):
            continue
        sym = inst.Symbol
        if sym is None:
            continue
        key = sym.Id.ToString()
        by_symbol.setdefault(key, []).append(inst)

    candidates = []
    for sym_id, insts in by_symbol.items():
        symbol = insts[0].Symbol
        dims, param_names = _find_dim_params_on_symbol(symbol)
        if len(dims) < 2:
            continue
        try:
            family_name = symbol.Family.Name
        except Exception:
            family_name = None
        try:
            type_name = symbol.Name
        except Exception:
            type_name = None
        candidates.append({
            "symbol_id": sym_id,
            "family_name": family_name,
            "type_name": type_name,
            "instance_count": len(insts),
            "dims_cm": dims,
            "param_names_used": param_names,
            "representative_instance_id": insts[0].Id.ToString(),
        })

    candidates.sort(key=lambda c: -c["instance_count"])
    result["block_catalog_candidates"] = candidates
except Exception:
    result["warnings"].append(
        "Falha no catalogo de blocos: {}".format(traceback.format_exc())
    )
_write_partial()


# ---------------------------------------------------------------------
# A2) Geometria de celulas (EdgeLoops da face superior) por candidato -
#     best-effort, so' sobre a instancia representativa, simbolo JA
#     ativo (tem instancia colocada). Falha isolada nao derruba o resto.
# ---------------------------------------------------------------------
def _top_face_edge_loops_local_cm(instance):
    opt = DB.Options()
    opt.ComputeReferences = False
    opt.DetailLevel = DB.ViewDetailLevel.Fine
    geom = instance.get_Geometry(opt)
    if geom is None:
        return None
    inv = instance.GetTransform().Inverse
    best_face = None
    best_z_local = None
    for gobj in geom:
        if not isinstance(gobj, DB.Solid) or gobj.Faces.Size == 0:
            continue
        for face in gobj.Faces:
            try:
                normal = face.ComputeNormal(DB.UV(0.5, 0.5))
            except Exception:
                continue
            if normal.Z < 0.9:
                continue
            bbox = face.GetBoundingBox()
            mid_uv = DB.UV(
                (bbox.Min.U + bbox.Max.U) / 2.0,
                (bbox.Min.V + bbox.Max.V) / 2.0,
            )
            z_local = inv.OfPoint(face.Evaluate(mid_uv)).Z
            if best_z_local is None or z_local > best_z_local:
                best_z_local = z_local
                best_face = face
    if best_face is None:
        return None
    loops_cm = []
    for loop in best_face.EdgeLoops:
        pts = []
        for edge in loop:
            for pt in edge.Tessellate():
                local = inv.OfPoint(pt)
                pts.append([round(local.X * FEET_TO_CM, 2), round(local.Y * FEET_TO_CM, 2)])
        loops_cm.append(pts)
    return loops_cm


try:
    for cand in result["block_catalog_candidates"]:
        try:
            inst = doc.GetElement(DB.ElementId(int(cand["representative_instance_id"])))
            loops = _top_face_edge_loops_local_cm(inst) if inst else None
            cand["top_face_loops_local_cm"] = loops
            cand["cell_count"] = (len(loops) - 1) if loops else None
        except Exception as exc:
            cand["top_face_loops_local_cm"] = None
            cand["cell_geometry_error"] = str(exc)
except Exception:
    result["warnings"].append(
        "Falha geral extraindo celulas: {}".format(traceback.format_exc())
    )
_write_partial()


# ---------------------------------------------------------------------
# B) Paredes reais - comprimento, espessura, distribuicao de ultimo
#    digito (para testar a hipotese "termina em 0/1/6/9" vs aritmetica
#    bloco+junta, sem presumir qual bate).
# ---------------------------------------------------------------------
try:
    walls = DB.FilteredElementCollector(doc).OfClass(DB.Wall).ToElements()
    lengths_cm = []
    thickness_counts = {}
    last_digit_counts = {}
    for w in walls:
        try:
            loc = w.Location
            if not isinstance(loc, DB.LocationCurve):
                continue
            length_cm = round(loc.Curve.Length * FEET_TO_CM, 2)
            lengths_cm.append(length_cm)
            thickness_cm = round(w.Width * FEET_TO_CM, 1)
            thickness_counts[thickness_cm] = thickness_counts.get(thickness_cm, 0) + 1
            digit = int(round(length_cm)) % 10
            last_digit_counts[digit] = last_digit_counts.get(digit, 0) + 1
        except Exception:
            continue

    result["walls"] = {
        "count": len(lengths_cm),
        "thickness_cm_histogram": thickness_counts,
        "last_digit_histogram": last_digit_counts,
        "length_cm_sample": sorted(lengths_cm)[:30],
    }
except Exception:
    result["walls"] = {"error": traceback.format_exc()}
_write_partial()


# ---------------------------------------------------------------------
# C) Aberturas (portas/janelas) - largura, digito, nome do parametro
#    usado de fato neste projeto.
# ---------------------------------------------------------------------
try:
    opening_cats = [DB.BuiltInCategory.OST_Doors, DB.BuiltInCategory.OST_Windows]
    widths_cm = []
    last_digit_counts = {}
    param_name_votes = {}
    for cat in opening_cats:
        insts = DB.FilteredElementCollector(doc) \
            .OfCategory(cat).WhereElementIsNotElementType().ToElements()
        for inst in insts:
            width_cm, used_name = _param_value_cm(inst, OPENING_WIDTH_PARAM_CANDIDATES)
            if width_cm is None:
                width_cm, used_name = _param_value_cm(inst.Symbol, OPENING_WIDTH_PARAM_CANDIDATES) if inst.Symbol else (None, None)
            if width_cm is None:
                continue
            widths_cm.append(round(width_cm, 2))
            digit = int(round(width_cm)) % 10
            last_digit_counts[digit] = last_digit_counts.get(digit, 0) + 1
            param_name_votes[used_name] = param_name_votes.get(used_name, 0) + 1

    result["openings"] = {
        "count": len(widths_cm),
        "width_param_names_seen": param_name_votes,
        "last_digit_histogram": last_digit_counts,
        "width_cm_sample": sorted(widths_cm)[:30],
    }
except Exception:
    result["openings"] = {"error": traceback.format_exc()}
_write_partial()


# ---------------------------------------------------------------------
# D) Instancias de bloco ja colocadas (dos tipos candidatos da secao A)
#    - distribuicao de cota Z (fiadas) e amostra de posicoes, para depois
#    (fora do Revit) medir junta/desencontro sem precisar reabrir o doc.
# ---------------------------------------------------------------------
try:
    block_symbol_ids = set(c["symbol_id"] for c in result["block_catalog_candidates"])
    z_values_cm = []
    sample_positions = []
    for sym_id in block_symbol_ids:
        insts = by_symbol.get(sym_id, [])
        for inst in insts[:500]:  # teto de amostra por tipo, projeto pode ter milhares
            try:
                origin = inst.GetTransform().Origin
                z_cm = round(origin.Z * FEET_TO_CM, 2)
                z_values_cm.append(z_cm)
                if len(sample_positions) < 200:
                    sample_positions.append({
                        "symbol_id": sym_id,
                        "x_cm": round(origin.X * FEET_TO_CM, 2),
                        "y_cm": round(origin.Y * FEET_TO_CM, 2),
                        "z_cm": z_cm,
                        "rotation_rad": getattr(inst, "Rotation", None),
                    })
            except Exception:
                continue

    result["block_instances"] = {
        "total_sampled": len(sample_positions),
        "z_cm_distinct_sorted": sorted(set(round(z, 1) for z in z_values_cm)),
        "sample_positions": sample_positions,
    }
except Exception:
    result["block_instances"] = {"error": traceback.format_exc()}
_write_partial()


# ---------------------------------------------------------------------
# E) Niveis - pe-direito tipico entre niveis consecutivos.
# ---------------------------------------------------------------------
try:
    levels = DB.FilteredElementCollector(doc).OfClass(DB.Level).ToElements()
    levels_sorted = sorted(levels, key=lambda lv: lv.Elevation)
    level_info = [
        {"name": lv.Name, "elevation_cm": round(lv.Elevation * FEET_TO_CM, 1)}
        for lv in levels_sorted
    ]
    deltas_cm = [
        round(level_info[i + 1]["elevation_cm"] - level_info[i]["elevation_cm"], 1)
        for i in range(len(level_info) - 1)
    ]
    result["levels"] = {"levels": level_info, "deltas_cm": deltas_cm}
except Exception:
    result["levels"] = {"error": traceback.format_exc()}
_write_partial()


print("DIAGNOSTICO_OK")
print("OUT_PATH={}".format(OUT_PATH))
