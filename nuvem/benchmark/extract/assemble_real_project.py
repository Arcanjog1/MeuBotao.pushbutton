# -*- coding: utf-8 -*-
"""Monta um projeto de benchmark REAL a partir dos tres dumps do Revit.

Etapa 2B.1. Existe para o caminho "dump bruto -> arquivos do projeto" ser
UM comando reproduzivel, e nao um script de sessao que ninguem mais
consegue repetir:

    dump INPUT   (revit_input_real_dump.py)  -> input_real.json
    dump CATALOGO(revit_catalog_dump.py)     -> catalog do input.json
    dump REFERENCE(revit_dump.py)            -> reference.json

Depois disso o ciclo normal do runner assume:

    runner.py --run <id> --wall-modeling-only   -> wall_modeling_snapshot.json
    (input_from_snapshot)                       -> input.json
    runner.py --run <id>                        -> result.json  (FULL)
    runner.py --run <id> --scoped               -> scoped_*     (SCOPED)

DUAS REGRAS QUE ESTE MODULO EXISTE PARA GARANTIR
------------------------------------------------
1. **O catalogo nunca vem do gabarito.** Ele vem dos `FamilySymbol`
   carregados no proprio documento INPUT. Passar o catalogo do
   `reference.json` daria ao solver, de graca, a informacao de quais pecas
   a pessoa usou - foi exatamente o vicio da primeira rodada (guardada em
   `provisional_2b/`).
2. **O reference e' gravado no referencial do INPUT**, aplicando a
   translacao MEDIDA, e o que foi aplicado fica registrado em
   `source_document.frame_transform_applied` para poder ser desfeito.

SERIALIZACAO (Etapa 2B.1 - hardening de higiene do commit, 2026-08-31)
------------------------------------------------------------------------
`reference.json` usa `model.save()` (uma linha por parede) pela mesma razao
documentada la': um pavimento real tem milhares de pecas, `indent=1` global
custa megabytes de espaco em branco e destroi o `git diff` (mexer numa
parede muda o arquivo inteiro, nao uma linha). `input_real.json` usa
`_write_input_real()`, que aplica a MESMA ideia aos dois arrays grandes
(`segments`, `openings`): uma linha por item. Medido no primeiro commit
real: `reference.json` caiu de 8.665 KB/328.340 linhas para ~5.567
KB/340 linhas com o MESMO conteudo (`json.load(antigo) == json.load(novo)`
confirmado antes de substituir).
"""

import io
import json
import os

from .. import model
from . import reconstruct
from . import revit_catalog_dump
from . import revit_input_real_dump


def _write(path, payload):
    """Uso GERAL, para payloads pequenos (`catalog_comparison.json`) onde
    `indent=1` nao pesa. NUNCA usar para `reference.json`/`input_real.json`
    - ver `_write_input_real()` e `model.save()`."""
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=1))
    return path


def _write_input_real(payload, path):
    """`input_real.json` com uma linha por item nos dois arrays grandes
    (`segments`, `openings`) - mesma tecnica de `model.save()`, adaptada
    porque este payload nao tem uma unica lista dominante chamada `walls`."""
    body = dict(payload)
    segments = body.pop("segments", None)
    openings = body.pop("openings", None)

    parts = [json.dumps(body, ensure_ascii=False, indent=1)[:-2]]
    if segments is not None:
        parts.append(',\n "segments": [\n')
        parts.append(",\n".join(
            "  " + json.dumps(item, ensure_ascii=False, separators=(",", ":"))
            for item in segments
        ))
        parts.append("\n ]")
    if openings is not None:
        parts.append(',\n "openings": [\n')
        parts.append(",\n".join(
            "  " + json.dumps(item, ensure_ascii=False, separators=(",", ":"))
            for item in openings
        ))
        parts.append("\n ]")
    parts.append("\n}\n")
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write("".join(parts))
    return path


def build_reference(reference_dump, project_id, transform_cm,
                    evidence=None):
    """Dump de blocos -> `reference.json` JA no referencial do INPUT.

    A translacao e' aplicada nas INSTANCIAS, antes de `build_project`, para
    que tudo o que e' derivado delas (eixos, fiadas, encontros) saia
    coerente - transformar so' as paredes no fim deixaria os blocos num
    referencial e os eixos noutro."""
    dx, dy, dz = transform_cm
    dump = dict(reference_dump)
    dump["instances"] = [
        list(row[:1]) + [round(row[1] - dx, 3), round(row[2] - dy, 3),
                         round(row[3] - dz, 3)] + list(row[4:])
        for row in (reference_dump.get("instances") or [])
    ]

    document_path = dump.get("document_path")
    document_filename = (
        document_path.replace("\\", "/").rsplit("/", 1)[-1]
        if document_path else None
    )
    project = reconstruct.build_project(
        dump, project_id, source="revit_reference",
        metadata={
            "level": dump.get("level_filter"),
            "source_kind": "projeto entregue e aprovado, modulado por pessoa",
            "document": dump.get("document"),
            # `document_path` (caminho absoluto local) NAO e' gravado - so'
            # o nome do arquivo, mesma sanitizacao de
            # `revit_input_real_dump.redact_source_document`. Nenhum codigo
            # do benchmark le este campo para decidir nada (ver o motivo
            # completo no docstring daquela funcao).
            "document_filename": document_filename,
            "level_filter": dump.get("level_filter"),
            "extracted_instances": len(dump["instances"]),
            "dump_warnings": dump.get("warnings") or [],
            "openings_source": "reconstructed_from_blocks",
            "walls_source": "reconstructed_from_blocks",
            "frame": "INPUT",
        })
    project["source_document"] = {
        "title": dump.get("document"),
        "filename": document_filename,
        "original_path_redacted": bool(document_path),
        "role": "HUMAN_REFERENCE",
        "level": dump.get("level_filter"),
        "native_frame": "coordenadas internas do .rvt do REFERENCE",
        "frame_transform_applied": {
            "note": "coordenadas GRAVADAS AQUI ja estao no referencial do "
                    "INPUT; para voltar ao referencial nativo, SOMAR translation",
            "translation_cm": [dx, dy, dz],
            "rotation_deg": 0.0,
            "scale": 1.0,
            "evidence": evidence,
        },
    }
    return project


def assemble(project_dir, input_dump, catalog_dump, reference_dump,
             project_id, transform_cm, setup_frozen_extra=None,
             pair_evidence=None):
    """Grava `input_real.json`, `reference.json` e `catalog_comparison.json`.

    Devolve o dict com os tres payloads. NAO grava `input.json` - esse sai
    do `wall_modeling_snapshot.json`, que so' existe depois da FASE A."""
    if not os.path.isdir(project_dir):
        os.makedirs(project_dir)

    if not str(input_dump.get("source_document", {}).get("title") or ""):
        raise ValueError("dump de INPUT sem proveniencia")
    if catalog_dump.get("missing"):
        raise ValueError(
            "catalogo do INPUT incompleto - faltam {0}. Sem os 6 codigos o "
            "benchmark NAO pode cair no catalogo do gabarito (seria vazamento "
            "da solucao humana); carregue as familias no documento INPUT ou "
            "use um catalogo versionado independente.".format(
                [item["logical_code"] for item in catalog_dump["missing"]]))

    catalog = revit_catalog_dump.build_catalog(catalog_dump)

    reference = build_reference(reference_dump, project_id, transform_cm,
                                evidence=pair_evidence)

    levels = input_dump.get("levels") or []
    level_name = levels[0]["name"] if levels else None
    setup_frozen = {
        "layer": "Arquitetura",
        "thicknesses_cm": [14.0],
        "openings_mode": "auto",
        "wall_mode": "segmented",
        "level": level_name,
        "base_z_cm": levels[0]["elevation_cm"] if levels else 0.0,
        "wall_height_cm": None,
        "num_courses": reference["settings"].get("num_courses"),
    }
    setup_frozen.update(setup_frozen_extra or {})
    if setup_frozen.get("wall_height_cm") is None:
        # Altura DOMINANTE do gabarito. E' uma escolha de `ask_setup` (o
        # pe-direito do pavimento), nao a solucao do problema - mas vem do
        # gabarito, e por isso fica registrado aqui em vez de implicito.
        heights = {}
        for wall in reference["walls"]:
            height = wall.get("height_cm")
            if height:
                heights[height] = heights.get(height, 0) + 1
        setup_frozen["wall_height_cm"] = (
            max(heights.items(), key=lambda kv: kv[1])[0] if heights else None)

    input_real = revit_input_real_dump.build_input_real(
        input_dump, project_id, setup_frozen,
        metadata={"source_kind": "projeto CRU (CAD + aberturas, sem nenhum bloco)"})
    input_real["catalog"] = catalog
    input_real["metadata"]["catalog_source"] = (
        "documento INPUT (FamilySymbol carregados, sem instancia, sem "
        "Activate) - NENHUMA informacao do gabarito")
    input_real["metadata"]["setup_frozen_from_reference"] = [
        "wall_height_cm", "num_courses",
    ]

    comparison = revit_catalog_dump.compare_catalogs(catalog, reference["catalog"])
    comparison["input_catalog_origin"] = "FamilySymbol carregados no documento INPUT"
    comparison["reference_catalog_origin"] = "tipos das pecas colocadas pela pessoa"

    _write_input_real(input_real, os.path.join(project_dir, "input_real.json"))
    model.save(reference, os.path.join(project_dir, "reference.json"))
    _write(os.path.join(project_dir, "catalog_comparison.json"), comparison)

    return {"input_real": input_real, "reference": reference,
            "catalog": catalog, "catalog_comparison": comparison}
