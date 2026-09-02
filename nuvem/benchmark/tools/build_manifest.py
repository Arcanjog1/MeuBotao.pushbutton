# -*- coding: utf-8 -*-
"""Gera `nuvem/benchmark/golden/manifest.json` (item 31 do pedido: "corpus
deve crescer continuamente" - adicionar um projeto deve exigir dado +
metadata, nao editar codigo em 10 lugares).

Este arquivo E' o "1 lugar" - a lista `ENTRIES` abaixo. Adicionar um
projeto novo ao corpus e':

1. Colocar os dados em `nuvem/benchmark/projects/<id>/` (ou registrar como
   `ANALYSIS_ONLY_REFERENCE` se so' houver resumo/censo, sem geometria).
2. Acrescentar uma linha em `ENTRIES` aqui, com a classificacao HUMANA
   (`reference_type`, `reference_kind`, `confidence`, `notes`) - isso NUNCA
   e' inferido sozinho (item 32).
3. Rodar `py -3 nuvem/benchmark/tools/build_manifest.py`.

O que ESTE SCRIPT infere sozinho (mecanico, item 32): `capabilities`
(via `golden/capabilities.py`, olhando o que o projeto realmente tem em
disco) e o `available_metrics` legado. Nunca `confidence`/`reference_kind`/
`approved_by_human` - esses continuam vindo so' de `ENTRIES`.
"""

import json
import os
import sys

if __package__ in (None, ""):  # rodando como script solto
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
    __package__ = "benchmark.tools"

from .. import runner as benchmark_runner  # noqa: E402
from ..golden import capabilities as capabilities_module  # noqa: E402
from ..golden import inventory  # noqa: E402
from ..golden import manifest  # noqa: E402


def _load_json_or_none(path):
    if not path or not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


# Metricas disponiveis para os 3 projetos reproduzíveis - todos rodam os
# mesmos 6 validadores (ver docs/GOLDEN_BENCHMARK.md); "performance" nunca
# entra aqui porque nenhum projeto tem tempo de execucao gravado ainda.
_STANDARD_METRICS = ("blocks", "courses", "junctions", "openings", "prism",
                    "quality", "walls")

# Cada entrada: os kwargs de `manifest.new_entry` + de onde ler
# `reference.json`/`input.json` para inferir `capabilities` (relativo a'
# pasta do projeto em `nuvem/benchmark/projects/<id>/`, ou `None` quando o
# projeto e' ANALYSIS_ONLY e nao tem pasta nenhuma).
ENTRIES = [
    {
        "kwargs": dict(
            project_id="torre_easy_lo_r00_tgd",
            name="TORRE EASY-LO-R00 - nivel 04. TGD (input medido x referencia humana reconstruida)",
            reference_type=manifest.HUMAN_REFERENCE_AVAILABLE,
            source="PAR de documentos Revit reais (TESTE MODULACAO (2026) = input medido; "
                   "TORRE EASY-LO-R00_desanexado_joaoC9CL7.rvt nivel 04. TGD = projeto entregue) - "
                   "extraidos via mcp__revit-pyrevit__execute_revit_code, READ-ONLY",
            created_at="2026-08-31",
            has_revit_model=True,
            produced_by_solver=False,
            approved_by_human=False,
            available_metrics=_STANDARD_METRICS,
            notes=(
                "reference.json e RECONSTRUIDO a partir do layout dos blocos (o .rvt entregue nao tem "
                "mais Wall/Door/Window nativos - 0 de cada, ver metadata.json). Os blocos em si foram "
                "posicionados por uma PESSOA (nao pelo solver): e por isso reference_kind=HUMAN. Nao ha, "
                "porem, nenhum registro de aprovacao formal (data/responsavel/processo de sign-off) em "
                "metadata.json - por isso confidence=MEDIUM (nao HIGH/GOLDEN). Promover para HIGH exige "
                "'verified_at' (alguem revisar a extracao contra a fonte); para GOLDEN exige aprovacao "
                "formal (item 38). baseline.json e baselines/baseline_real_v1.json sao "
                "reference_kind=SOLVER confidence=LOW (saida do proprio solver, congelada para "
                "regressao/determinismo) - nunca entram como reference.json deste projeto."
            ),
        ),
        "reference_file": "reference.json",
        "input_file": "input.json",
    },
    {
        "kwargs": dict(
            project_id="torre_easy_lo_r00_tp1",
            name="TORRE EASY-LO-R00 (JARDIM DA COSTA BEACH CLUB) - nivel 05. TP1",
            reference_type=manifest.HUMAN_REFERENCE_AVAILABLE,
            source="Projeto Revit entregue e aprovado no fluxo do escritorio, extraido via "
                   "mcp__revit-pyrevit__execute_revit_code (READ-ONLY)",
            created_at="2026-08-31",
            has_revit_model=True,
            produced_by_solver=False,
            approved_by_human=False,
            available_metrics=_STANDARD_METRICS,
            notes=(
                "reference.json e RECONSTRUIDO (mesma limitacao do TGD: 0 Wall/Door/Window nativos no "
                ".rvt entregue). aberturas marcadas confidence=reconstructed. Blocos posicionados por "
                "pessoa => reference_kind=HUMAN, confidence=MEDIUM (sem registro de aprovacao formal). "
                "input.json deste projeto (diferente do TGD) e RECONSTRUIDO a partir do proprio gabarito "
                "(reconstruct.input_from_reference), nao medido - ver README secao \"Como extrair\"."
            ),
        ),
        "reference_file": "reference.json",
        "input_file": "input.json",
    },
    {
        "kwargs": dict(
            project_id="piloto_sintetico_2x2",
            name="Grade sintetica 2x2 - 12 eixos, 8 fiadas",
            reference_type=manifest.SOLVER_GENERATED_ONLY,
            reference_kind=manifest.KIND_SYNTHETIC,
            confidence=manifest.CONFIDENCE_NONE,
            source="Gerado por benchmark/extract/synthetic.py - nao e projeto real, sem par humano",
            created_at="2026-08-31",
            has_revit_model=False,
            produced_by_solver=True,
            available_metrics=_STANDARD_METRICS,
            notes=(
                "Sem reference.json (\"SEM GABARITO\" no metadata.json) - so existe input.json + o que o "
                "solver decide agora. reference_kind=SYNTHETIC (nao SOLVER): a ENTRADA e' gerada "
                "proceduralmente, o solver so' resolve ela. Nao serve para comparar com humano "
                "(CAN_COMPARE_TO_HUMAN ausente) - serve para determinismo, invariantes e casos "
                "controlados (item 35)."
            ),
        ),
        "reference_file": None,
        "input_file": "input.json",
    },
    {
        # ANALYSIS_ONLY (item 7/36): so' existe censo agregado (contagem de
        # pecas por tipo, por nivel), sem geometria por parede/bloco. Achado
        # pela varredura do repositorio (CR-BLOCK-REFERENCE-CORPUS, item 5).
        "kwargs": dict(
            project_id="chacara_torre_easy_lo_tropicale",
            name='CHACARA-TORRE EASY-LO ("TROPICALE BEACH CLUB") - censo bruto',
            reference_type=manifest.ANALYSIS_ONLY_REFERENCE,
            source="nuvem/diagnosticos/CHACARA-TORRE-EASY-LO.md - gerado via "
                   "mcp__revit-pyrevit__execute_revit_code (100% leitura), sem Wall/Door/Window "
                   "nativos (ja excluidos no documento)",
            created_at="2026-08-27",
            has_revit_model=True,
            produced_by_solver=False,
            missing_requirements=[
                "input.json/input_real.json (linhas de CAD por layer + aberturas medidas)",
                "reference.json (posicao XY/Z, rotacao e codigo de CADA instancia de bloco, nao so' "
                "a contagem agregada por tipo)",
                "wall_modeling_snapshot.json (eixos/nos L-T-X reconstruidos)",
                "confirmacao de qual dos 22 niveis ('00. FUN' a '21. COB') vira o par input/reference, "
                "como foi feito para TGD/TP1 dentro de TORRE_EASY-LO-R00",
            ],
            notes=(
                "Projeto Revit DIFERENTE de torre_easy_lo_r00_* - confirmado explicitamente pelo "
                "usuario apesar do nome de arquivo parecido (ver nuvem/PADRAO_MODULACAO.md linha 23 e "
                "o cabecalho do proprio diagnostico). Hoje so' tem contagem agregada de pecas por "
                "codigo/dimensao (bate com o catalogo fixo de REGRAS_MODULACAO_BLOCOS.md - primeira "
                "confirmacao cross-projeto do catalogo nucleo) e observacoes de pe-direito/junta - "
                "ZERO geometria por parede ou por bloco. Nao pode ser rodado nem comparado "
                "estruturalmente ainda; ver 'missing_requirements'."
            ),
        ),
        "reference_file": None,
        "input_file": None,
    },
    {
        "kwargs": dict(
            project_id="torre_easy_lo_r00_full_building",
            name="TORRE EASY-LO-R00 (JARDIM DA COSTA BEACH CLUB) - edificio inteiro, 21 niveis - censo bruto",
            reference_type=manifest.ANALYSIS_ONLY_REFERENCE,
            source="nuvem/diagnosticos/TORRE_EASY-LO-R00.md - gerado via mcp__revit-pyrevit__execute_revit_code "
                   "(100% leitura), sem Wall/Door/Window nativos (ja excluidos no documento)",
            created_at="2026-08-24",
            has_revit_model=True,
            produced_by_solver=False,
            missing_requirements=[
                "extracao (input_real.json + reference.json) de cada um dos ~19 niveis alem de "
                "04. TGD e 05. TP1 (ja catalogados como torre_easy_lo_r00_tgd/torre_easy_lo_r00_tp1)",
                "confirmacao de pareamento input x referencia por nivel, como foi feito para TGD",
            ],
            notes=(
                "E' o EDIFICIO INTEIRO de origem de torre_easy_lo_r00_tgd (nivel 04) e "
                "torre_easy_lo_r00_tp1 (nivel 05) - 67.712 instancias em 21 niveis ('01. TER' a "
                "'21. COB'), so' 2 deles ja' viraram projeto reproduzivel no corpus. Esta entrada "
                "cataloga os ~19 niveis RESTANTES, que hoje so' tem censo agregado (contagem de pecas "
                "por tipo, sem posicao XY por instancia) - nao um projeto novo do zero, e sim o que "
                "falta extrair do MESMO edificio para o corpus crescer sem nova coleta de campo."
            ),
        ),
        "reference_file": None,
        "input_file": None,
    },
]


def build():
    entries = []
    for spec in ENTRIES:
        kwargs = dict(spec["kwargs"])
        project_id = kwargs["project_id"]
        scan = inventory.scan_project(project_id)

        reference_project = None
        input_project = None
        if spec.get("reference_file"):
            paths = benchmark_runner.project_paths(project_id)
            reference_project = _load_json_or_none(
                os.path.join(paths["dir"], spec["reference_file"]))
        if spec.get("input_file"):
            paths = benchmark_runner.project_paths(project_id)
            input_project = _load_json_or_none(
                os.path.join(paths["dir"], spec["input_file"]))

        reference_kind = kwargs.get("reference_kind")
        if reference_kind is None:
            reference_kind = manifest.LEGACY_TO_AXES.get(
                kwargs["reference_type"], (manifest.KIND_UNKNOWN, None))[0]

        caps = capabilities_module.infer_capabilities(
            scan, reference_kind=reference_kind,
            reference_project=reference_project, input_project=input_project)
        kwargs.setdefault("capabilities", caps)

        entries.append(manifest.new_entry(**kwargs))

    return manifest.make_manifest(entries)


def main():
    data = build()
    path = manifest.DEFAULT_MANIFEST_PATH
    manifest.save(data, path)
    print("manifest gravado em {0} ({1} projeto(s))".format(path, len(data["projects"])))
    for entry in data["projects"]:
        print("  {0:<38} kind={1:<12} confidence={2:<7} capabilities={3}".format(
            entry["project_id"], entry["reference_kind"], entry["confidence"],
            len(entry["capabilities"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
