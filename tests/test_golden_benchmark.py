# -*- coding: utf-8 -*-
"""Testes do GOLDEN BENCHMARK (CR-BLOCK-GOLDEN-BENCHMARK, item 25 do
pedido). Tudo aqui e' sintetico e roda sem Revit e sem o solver real -
exatamente como `tests/regression/test_benchmark_infra.py`, que este
arquivo imita de proposito (mesmo estilo de planta desenhada a mao).

NAO importa nada de `core/engine/*` (wall_stepper.py, wall_pairing.py) -
este benchmark e' sobre o formato de SAIDA (`benchmark/model.py`), nunca
sobre o motor que a produz.
"""

import os
import sys

import pytest

# `nuvem/` precisa estar no sys.path para `benchmark.*` ser importavel -
# mesma busca de `tests/test_script.py` (nao ha' `conftest.py` na raiz de
# `tests/`, so' em `tests/regression/`, e este arquivo fica fora dali).
_HERE = os.path.dirname(os.path.abspath(__file__))
_NUVEM_DIR = os.path.join(os.path.dirname(_HERE), "nuvem")
if os.path.isfile(os.path.join(_NUVEM_DIR, "benchmark", "__init__.py")) \
        and _NUVEM_DIR not in sys.path:
    sys.path.insert(0, _NUVEM_DIR)

from benchmark import model, scoring
from benchmark.golden import (
    capabilities, compare, corpus, fingerprint, human_reference, inventory,
    manifest, metrics, pipeline_order, pipeline_trace, wall_diff, wall_order,
)
from benchmark.validators import base


# ------------------------------------------------------- helpers de planta
def _wall(start, end, thickness=14.0, wall_id="W001", rows=None):
    return model.make_wall(wall_id, start, end, thickness, rows=rows or [])


def _row_with_blocks(index, codes_and_extents):
    blocks = [
        model.make_block(code, end - start, ((start + end) / 2.0, 0.0), 0.0, 0.0,
                         start, end)
        for code, start, end in codes_and_extents
    ]
    return model.make_row(index, index * 20.0, blocks)


def _project(project_id, source, walls):
    return model.assign_ids(model.make_project(project_id, source, walls=walls))


def _one_wall_project(project_id, source, codes_and_extents_by_row,
                      start=(0, 0), end=(300, 0)):
    rows = [_row_with_blocks(index, extents)
           for index, extents in enumerate(codes_and_extents_by_row)]
    wall = _wall(start, end, rows=rows)
    return _project(project_id, source, [wall])


# ============================================================ FINGERPRINT
def test_fingerprint_e_deterministico_para_o_mesmo_projeto():
    a = _one_wall_project("p", "solver", [[("B39", 0, 39)], [("B39", 0, 39)]])
    b = _one_wall_project("p", "solver", [[("B39", 0, 39)], [("B39", 0, 39)]])
    assert fingerprint.canonical_fingerprint(a) == fingerprint.canonical_fingerprint(b)


def test_fingerprint_ignora_ordem_das_paredes_na_lista():
    wall_a = _wall((0, 0), (300, 0), wall_id="A",
                   rows=[_row_with_blocks(0, [("B39", 0, 39)])])
    wall_b = _wall((0, 300), (300, 300), wall_id="B",
                   rows=[_row_with_blocks(0, [("B34", 0, 34)])])
    p1 = _project("p", "solver", [wall_a, wall_b])
    p2 = _project("p", "solver", [wall_b, wall_a])
    assert fingerprint.canonical_fingerprint(p1) == fingerprint.canonical_fingerprint(p2)


def test_fingerprint_nao_muda_com_reversao_de_ponta():
    """Item 16/22: nunca depender de GetEndPoint(0)/GetEndPoint(1) cru - a
    MESMA parede FISICA desenhada ao contrario tem que dar o mesmo
    fingerprint. O bloco fisico ocupa x=[0,39] no mundo; desenhada
    (300,0)->(0,0), o MESMO bloco fica em t=[261,300] relativo a' nova
    origem (300 - 39 = 261, 300 - 0 = 300) - e' o espelhamento que
    `fingerprint._canonical_t_range` desfaz antes de assinar."""
    forward = _wall((0, 0), (300, 0), wall_id="W",
                    rows=[_row_with_blocks(0, [("B39", 0, 39)])])
    backward = _wall((300, 0), (0, 0), wall_id="W",
                     rows=[_row_with_blocks(0, [("B39", 261, 300)])])
    p1 = _project("p", "solver", [forward])
    p2 = _project("p", "solver", [backward])
    assert fingerprint.canonical_fingerprint(p1) == fingerprint.canonical_fingerprint(p2)


def test_fingerprint_reversao_de_ponta_realmente_espelha_nao_e_tautologia():
    """Guarda contra o proprio erro que este teste tinha antes de ser
    corrigido: se a parede reversa levar o MESMO t_start/t_end cru (sem
    espelhar), o fingerprint deve dar DIFERENTE - senao o teste anterior
    passaria so' porque comparava o bloco errado do lado errado, nunca
    provando reversao de verdade."""
    forward = _wall((0, 0), (300, 0), wall_id="W",
                    rows=[_row_with_blocks(0, [("B39", 0, 39)])])
    backward_sem_espelhar = _wall((300, 0), (0, 0), wall_id="W",
                                  rows=[_row_with_blocks(0, [("B39", 0, 39)])])
    p1 = _project("p", "solver", [forward])
    p2 = _project("p", "solver", [backward_sem_espelhar])
    assert fingerprint.canonical_fingerprint(p1) != fingerprint.canonical_fingerprint(p2)


def test_fingerprint_muda_quando_uma_peca_muda():
    a = _one_wall_project("p", "solver", [[("B39", 0, 39)]])
    b = _one_wall_project("p", "solver", [[("B34", 0, 34), ("B04", 34, 38)]])
    assert fingerprint.canonical_fingerprint(a) != fingerprint.canonical_fingerprint(b)


# --------------------------------------------------- fingerprint: aberturas
def test_opening_signature_nao_muda_com_reversao_de_ponta():
    """Item 23: a MESMA abertura fisica (x=[100,150] no mundo, peitoril
    90) numa parede desenhada (0,0)->(300,0) ou (300,0)->(0,0) tem que
    gerar a mesma assinatura - t espelhado (300-150=150, 300-100=200)."""
    janela_fwd = model.make_opening(model.OPENING_WINDOW, 100, 150, 90, 200)
    wall_fwd = _wall((0, 0), (300, 0), wall_id="W")
    wall_fwd["openings"] = [janela_fwd]

    janela_bwd = model.make_opening(model.OPENING_WINDOW, 150, 200, 90, 200)
    wall_bwd = _wall((300, 0), (0, 0), wall_id="W")
    wall_bwd["openings"] = [janela_bwd]

    sig_fwd = fingerprint.canonical_opening_signatures(_project("p", "solver", [wall_fwd]))
    sig_bwd = fingerprint.canonical_opening_signatures(_project("p", "solver", [wall_bwd]))
    assert sig_fwd == sig_bwd
    assert sig_fwd[0]["kind"] == model.OPENING_WINDOW
    assert sig_fwd[0]["width_cm"] == 50.0


def test_opening_signature_entra_no_fingerprint_do_projeto():
    wall_com_abertura = _wall((0, 0), (300, 0), wall_id="W")
    wall_com_abertura["openings"] = [model.make_opening(model.OPENING_DOOR, 100, 180, 0, 210)]
    wall_sem_abertura = _wall((0, 0), (300, 0), wall_id="W")

    a = fingerprint.canonical_fingerprint(_project("p", "solver", [wall_com_abertura]))
    b = fingerprint.canonical_fingerprint(_project("p", "solver", [wall_sem_abertura]))
    assert a != b


# ---------------------------------------------------------- fingerprint: L/T/X
def test_junction_signature_agrupa_por_ponto_nunca_por_indice():
    """Item 22/24: `neighbors` no dado bruto e' um indice de lista da
    extracao (proibido). Mesmo com indices ERRADOS/trocados nas duas
    copias, agrupar pelo PONTO fisico (`point_cm`) + a CHAVE ESTAVEL de
    cada parede tem que continuar dando o no' certo."""
    wall_a = _wall((0, 0), (300, 0), wall_id="A")
    wall_a["junctions"] = [{
        "type": model.JUNCTION_L, "t_cm": 300.0, "point_cm": [300.0, 0.0],
        "neighbors": [999], "at_end": True,  # indice de lista propositalmente absurdo
    }]
    wall_b = _wall((300, 0), (300, 300), wall_id="B")
    wall_b["junctions"] = [{
        "type": model.JUNCTION_L, "t_cm": 0.0, "point_cm": [300.0, 0.0],
        "neighbors": [-7], "at_end": True,  # idem
    }]
    project = _project("p", "solver", [wall_a, wall_b])
    signatures = fingerprint.canonical_junction_signatures(project)
    assert len(signatures) == 1
    node = signatures[0]
    assert node["point_cm"] == [300.0, 0.0]
    assert node["type"] == [model.JUNCTION_L]
    assert len(node["walls"]) == 2  # as DUAS chaves de parede, nunca os indices 999/-7


def test_junction_signature_independe_da_ordem_das_paredes_na_lista():
    wall_a = _wall((0, 0), (300, 0), wall_id="A")
    wall_a["junctions"] = [{"type": model.JUNCTION_T, "point_cm": [300.0, 0.0], "neighbors": []}]
    wall_b = _wall((300, 0), (300, 300), wall_id="B")
    wall_b["junctions"] = [{"type": model.JUNCTION_T, "point_cm": [300.0, 0.0], "neighbors": []}]

    p1 = _project("p", "solver", [wall_a, wall_b])
    p2 = _project("p", "solver", [wall_b, wall_a])
    assert (fingerprint.canonical_junction_signatures(p1)
           == fingerprint.canonical_junction_signatures(p2))


def test_junction_signature_marca_conflito_de_tipo_em_vez_de_esconder():
    wall_a = _wall((0, 0), (300, 0), wall_id="A")
    wall_a["junctions"] = [{"type": model.JUNCTION_L, "point_cm": [300.0, 0.0], "neighbors": []}]
    wall_b = _wall((300, 0), (300, 300), wall_id="B")
    wall_b["junctions"] = [{"type": model.JUNCTION_T, "point_cm": [300.0, 0.0], "neighbors": []}]
    project = _project("p", "solver", [wall_a, wall_b])
    node = fingerprint.canonical_junction_signatures(project)[0]
    assert node["type"] == [model.JUNCTION_L, model.JUNCTION_T]


def test_component_fingerprints_tem_as_tres_partes_e_o_geral():
    project = _one_wall_project("p", "solver", [[("B39", 0, 39)]])
    parts = fingerprint.component_fingerprints(project)
    assert set(parts) == {"walls_blocks", "openings", "junctions", "overall"}
    assert parts["overall"] == fingerprint.canonical_fingerprint(project)


def test_multi_run_report_detecta_determinismo():
    runs = [_one_wall_project("p", "solver", [[("B39", 0, 39)]]) for _ in range(5)]
    report = fingerprint.multi_run_report(runs)
    assert report["runs"] == 5
    assert report["distinct_fingerprints"] == 1
    assert report["deterministic"] is True


def test_multi_run_report_detecta_nao_determinismo():
    runs = [
        _one_wall_project("p", "solver", [[("B39", 0, 39)]]),
        _one_wall_project("p", "solver", [[("B34", 0, 34), ("B04", 34, 38)]]),
    ]
    report = fingerprint.multi_run_report(runs)
    assert report["distinct_fingerprints"] == 2
    assert report["deterministic"] is False


# ================================================================ METRICS
def test_metricas_sem_nenhum_dado_saem_not_available_nunca_zero():
    """Item 26: dado incompleto -> NOT_AVAILABLE, nunca um zero inventado."""
    bundle = metrics.compute_metrics()
    assert bundle["blocks"]["total_blocks"]["status"] == metrics.STATUS_NOT_AVAILABLE
    assert bundle["blocks"]["total_blocks"]["value"] is None
    assert bundle["walls"]["total_walls"]["status"] == metrics.STATUS_NOT_AVAILABLE
    assert bundle["performance"]["runtime_seconds"]["value"] is None


def test_metricas_de_bloco_por_codigo_a_partir_do_projeto():
    project = _one_wall_project("p", "solver", [[("B39", 0, 39), ("B19", 40, 59)]])
    bundle = metrics.compute_metrics(project=project)
    assert bundle["blocks"]["B39"]["value"] == 1
    assert bundle["blocks"]["B19"]["value"] == 1
    assert bundle["blocks"]["total_blocks"]["value"] == 2
    assert bundle["blocks"]["B39"]["direction"] == metrics.CONTEXT_DEPENDENT


def test_direcao_de_colisao_e_lower_is_better():
    assert metrics.quality_metrics(score=None, findings=None)["collisions"]["direction"] \
        == metrics.LOWER_IS_BETTER


def test_critical_invariant_codes_vem_da_taxonomia_existente_nao_e_inventada():
    codes = metrics.critical_invariant_codes()
    assert "POSITION_OVERLAP" in codes
    assert "PRISM_CONTINUOUS_JOINT" in codes
    for code in codes:
        assert base.error_class(code).severity == base.SEVERITY_CRITICAL


# ================================================================ COMPARE
def test_metrica_higher_is_better_melhora_quando_sobe():
    row = compare.compare_metric_entry(
        "coverage_pct",
        {"value": 80.0, "direction": metrics.HIGHER_IS_BETTER, "unit": "%"},
        {"value": 91.0, "direction": metrics.HIGHER_IS_BETTER, "unit": "%"},
    )
    assert row["status"] == compare.STATUS_IMPROVED
    assert row["delta_abs"] == 11.0


def test_metrica_lower_is_better_piora_quando_sobe():
    row = compare.compare_metric_entry(
        "alignment_conflicts",
        {"value": 0, "direction": metrics.LOWER_IS_BETTER},
        {"value": 64, "direction": metrics.LOWER_IS_BETTER},
    )
    assert row["status"] == compare.STATUS_REGRESSED


def test_metrica_informational_nunca_regride_nem_melhora():
    row = compare.compare_metric_entry(
        "total_blocks",
        {"value": 100, "direction": metrics.CONTEXT_DEPENDENT},
        {"value": 400, "direction": metrics.CONTEXT_DEPENDENT},
    )
    assert row["status"] == compare.STATUS_INFORMATIONAL


def test_metrica_sem_valor_de_um_dos_lados_e_not_available():
    row = compare.compare_metric_entry(
        "coverage_pct",
        {"value": None, "direction": metrics.HIGHER_IS_BETTER},
        {"value": 50.0, "direction": metrics.HIGHER_IS_BETTER},
    )
    assert row["status"] == compare.STATUS_NOT_AVAILABLE


def _score_with_critical(critical_count, category_fail=0, wall_count=3):
    """Numero de PAREDES FIXO (`wall_count`) independente de quantos
    achados sao gerados - senao uma correcao (menos achados) mudaria por
    tabela o total de paredes do projeto sintetico, e uma metrica
    informativa (menos parede) contaminaria o veredito por um motivo que
    nao tem nada a ver com o que o teste quer provar."""
    findings = []
    for i in range(critical_count):
        findings.append(base.finding("POSITION_OVERLAP", wall="W{0:03d}".format(i),
                                     detail="colisao sintetica"))
    for i in range(category_fail):
        findings.append(base.finding("PRISM_STAGGER_BELOW_TARGET",
                                     wall="W{0:03d}".format(i), detail="stagger"))
    project = model.make_project("p", "solver", walls=[
        model.make_wall("W{0:03d}".format(i), (0, i * 300), (300, i * 300), 14)
        for i in range(wall_count)
    ])
    return scoring.score_project(project, findings)


def test_veredito_e_regressed_quando_critico_piora_mesmo_com_outras_metricas_iguais():
    """Item 14/13: regressao critica nunca pode ser escondida atras de
    uma media boa."""
    reference_score = _score_with_critical(0)
    current_score = _score_with_critical(2)
    result = compare.compare({"score": reference_score}, {"score": current_score})
    assert result["verdict"] == compare.VERDICT_REGRESSED
    assert result["critical_invariants"]["available"] is True
    assert result["critical_invariants"]["regressions"]


def test_veredito_e_improved_quando_critico_e_corrigido():
    reference_score = _score_with_critical(2)
    current_score = _score_with_critical(0)
    result = compare.compare({"score": reference_score}, {"score": current_score})
    assert result["verdict"] == compare.VERDICT_IMPROVED


def test_veredito_e_neutral_quando_nada_muda():
    score = _score_with_critical(0)
    result = compare.compare({"score": score}, {"score": score})
    assert result["verdict"] == compare.VERDICT_NEUTRAL


def test_veredito_e_mixed_quando_uma_metrica_melhora_e_outra_piora():
    reference_metrics = {
        "quality": {
            "collisions": {"value": 10, "direction": metrics.LOWER_IS_BETTER},
        },
        "prism": {
            "alignment_conflicts": {"value": 0, "direction": metrics.LOWER_IS_BETTER},
        },
    }
    current_metrics = {
        "quality": {
            "collisions": {"value": 2, "direction": metrics.LOWER_IS_BETTER},
        },
        "prism": {
            "alignment_conflicts": {"value": 5, "direction": metrics.LOWER_IS_BETTER},
        },
    }
    categories = compare.compare_bundles(reference_metrics, current_metrics)
    overall = compare._overall_counts(categories)  # noqa: SLF001 - teste interno
    verdict = compare._summarize_verdict(overall, None)  # noqa: SLF001
    assert verdict == compare.VERDICT_MIXED


# ============================================================== WALL_DIFF
def test_diff_de_bloco_classifica_added_removed_moved_changed_code():
    current = _one_wall_project("cur", "solver", [
        [("B39", 0, 39), ("B34", 40, 74)],   # linha 0: B34 novo em 40-74
    ])
    reference = _one_wall_project("ref", "revit_reference", [
        [("B54", 0, 39), ("B19", 80, 99)],   # linha 0: B54 vira B39 (mesmo lugar) e B19 sumiu
    ])
    comparison = wall_diff.compute_wall_diff(current, reference)
    wall_id = comparison["per_wall"][0]["wall"]
    diffs = wall_diff.block_diff_for_wall(comparison, wall_id)
    actions = sorted(d["action"] for d in diffs)
    assert wall_diff.ACTION_CHANGED_CODE in actions  # B39 no lugar do B54
    assert wall_diff.ACTION_ADDED in actions          # B34 novo
    assert wall_diff.ACTION_REMOVED in actions        # B19 sumiu


def test_changed_wall_ids_ordena_pela_quantidade_de_mudanca():
    current = _project("cur", "solver", [
        _wall((0, 0), (300, 0), wall_id="A", rows=[_row_with_blocks(0, [("B39", 0, 39)])]),
        _wall((0, 300), (300, 300), wall_id="B", rows=[_row_with_blocks(0, [("B39", 0, 39)])]),
    ])
    reference = _project("ref", "revit_reference", [
        _wall((0, 0), (300, 0), wall_id="A", rows=[_row_with_blocks(0, [("B34", 0, 34)])]),
        _wall((0, 300), (300, 300), wall_id="B", rows=[_row_with_blocks(0, [("B39", 0, 39)])]),
    ])
    comparison = wall_diff.compute_wall_diff(current, reference)
    summary = wall_diff.changed_wall_ids(comparison)
    assert len(summary["changed"]) == 1


def test_course_diff_agrupa_por_fiada():
    current = _one_wall_project("cur", "solver", [
        [("B39", 0, 39)],
        [("B34", 0, 34)],
    ])
    reference = _one_wall_project("ref", "revit_reference", [
        [("B39", 0, 39)],
        [("B54", 0, 34)],
    ])
    comparison = wall_diff.compute_wall_diff(current, reference)
    wall_id = comparison["per_wall"][0]["wall"]
    by_course = wall_diff.course_diff_for_wall(comparison, wall_id)
    assert 0 not in by_course or not by_course.get(0)  # fiada 0 identica
    assert 1 in by_course and by_course[1]


def test_paredes_so_no_atual_ou_so_na_referencia_aparecem_como_added_removed():
    current = _project("cur", "solver", [_wall((0, 0), (300, 0), wall_id="A")])
    reference = _project("ref", "revit_reference", [_wall((0, 500), (300, 500), wall_id="B")])
    comparison = wall_diff.compute_wall_diff(current, reference)
    summary = wall_diff.changed_wall_ids(comparison)
    assert summary["added_walls"]
    assert summary["removed_walls"]


# =============================================================== MANIFEST
def test_manifest_recusa_golden_confirmed_sem_prova_de_validacao():
    entry = manifest.new_entry(
        project_id="x", name="x", reference_type=manifest.GOLDEN_CONFIRMED,
        source="teste", approved_by_human=False)
    problems = manifest.validate_entry(entry)
    assert problems, "GOLDEN_CONFIRMED sem validated_at/approved_by_human tem que reclamar"


def test_manifest_aceita_human_reference_available_sem_validacao_formal():
    entry = manifest.new_entry(
        project_id="x", name="x", reference_type=manifest.HUMAN_REFERENCE_AVAILABLE,
        source="teste")
    assert manifest.validate_entry(entry) == []


def test_manifest_oficial_do_repo_nao_tem_nenhum_golden_confirmed_inventado():
    """Item 6 do pedido: nao inventar golden. Nenhum projeto do repositorio
    tem hoje prova de aprovacao humana registrada - o manifesto tem que
    refletir isso e nao subir ninguem para GOLDEN_CONFIRMED sozinho."""
    data = manifest.load_default()
    for entry in data["projects"]:
        assert entry["reference_type"] != manifest.GOLDEN_CONFIRMED
        assert manifest.validate_entry(entry) == []


def test_manifesto_oficial_classifica_baseline_como_solver_low_nas_notas():
    """A partir do CR-BLOCK-REFERENCE-CORPUS, baseline.json e' descrito no
    manifesto pelos dois EIXOS (reference_kind=SOLVER, confidence=LOW),
    nao mais so' pelo rotulo legado LEGACY_BASELINE - mas o fato que
    importa (nunca e' tratado como golden) continua o mesmo."""
    data = manifest.load_default()
    torre = manifest.get(data, "torre_easy_lo_r00_tgd")
    assert torre is not None
    assert "SOLVER" in torre["notes"] and "LOW" in torre["notes"]


def test_get_de_projeto_inexistente_devolve_none_sem_lancar_excecao():
    data = manifest.load_default()
    assert manifest.get(data, "projeto-que-nao-existe") is None


def test_candidates_for_promotion_lista_so_referencia_humana():
    data = manifest.load_default()
    candidates = manifest.candidates_for_promotion(data)
    assert candidates
    for entry in candidates:
        assert entry["reference_type"] == manifest.HUMAN_REFERENCE_AVAILABLE


# ============================================================== INVENTORY
def test_inventory_scan_projeto_inexistente_nao_lanca_excecao():
    result = inventory.scan_project("projeto-que-nao-existe-de-verdade")
    assert result["files_present"] == []
    assert result["has_reference"] is False


def test_inventory_encontra_os_tres_projetos_do_repo():
    ids = set(p["project_id"] for p in inventory.scan_all())
    assert {"torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1", "piloto_sintetico_2x2"} <= ids


def test_inventory_marca_baseline_json_como_snapshot_do_solver():
    result = inventory.scan_project("piloto_sintetico_2x2")
    kinds = set(b["kind"] for b in result["legacy_baselines"])
    assert "solver_score_snapshot" in kinds


# =============================================================== WALL_ORDER
def test_classifica_parede_horizontal_vertical_inclinada():
    horizontal = _wall((0, 0), (300, 0))
    vertical = _wall((0, 0), (0, 300))
    inclined = _wall((0, 0), (300, 300))
    assert wall_order.classify_wall_kind(horizontal) == wall_order.KIND_HORIZONTAL
    assert wall_order.classify_wall_kind(vertical) == wall_order.KIND_VERTICAL
    assert wall_order.classify_wall_kind(inclined) == wall_order.KIND_INCLINED


def test_ordem_oficial_poe_horizontais_antes_de_verticais():
    horizontal = _wall((0, 0), (300, 0), wall_id="H")
    vertical = _wall((0, 0), (0, 300), wall_id="V")
    ordered = wall_order.official_order([vertical, horizontal])
    assert [w["id"] for w in ordered] == ["H", "V"]


def test_ordem_oficial_horizontais_de_cima_para_baixo():
    top = _wall((0, 300), (300, 300), wall_id="TOP")
    bottom = _wall((0, 0), (300, 0), wall_id="BOTTOM")
    ordered = wall_order.official_order([bottom, top])
    assert [w["id"] for w in ordered] == ["TOP", "BOTTOM"]


def test_ordem_oficial_verticais_de_baixo_para_cima():
    low = _wall((0, 0), (0, 100), wall_id="LOW")
    high = _wall((0, 200), (0, 300), wall_id="HIGH")
    ordered = wall_order.official_order([high, low])
    assert [w["id"] for w in ordered] == ["LOW", "HIGH"]


def test_empate_desempata_esquerda_para_direita():
    left = _wall((0, 0), (100, 0), wall_id="LEFT")
    right = _wall((200, 0), (300, 0), wall_id="RIGHT")
    ordered = wall_order.official_order([right, left])
    assert [w["id"] for w in ordered] == ["LEFT", "RIGHT"]


def test_validate_wall_order_aponta_o_primeiro_desencontro():
    horizontal = _wall((0, 0), (300, 0), wall_id="H")
    vertical = _wall((0, 0), (0, 300), wall_id="V")
    result = wall_order.validate_wall_order([vertical, horizontal])
    assert result["ok"] is False
    assert result["first_mismatch_index"] == 0


def test_validate_wall_order_ok_quando_ja_esta_na_ordem_oficial():
    horizontal = _wall((0, 0), (300, 0), wall_id="H")
    vertical = _wall((0, 0), (0, 300), wall_id="V")
    result = wall_order.validate_wall_order([horizontal, vertical])
    assert result["ok"] is True


def test_sentido_interno_horizontal_esquerda_para_direita():
    ok_wall = _wall((0, 0), (300, 0), wall_id="OK")
    bad_wall = _wall((300, 0), (0, 0), wall_id="BAD")
    assert wall_order.wall_internal_direction_ok(ok_wall) is True
    assert wall_order.wall_internal_direction_ok(bad_wall) is False


def test_audit_internal_directions_lista_os_infratores():
    bad_wall = _wall((300, 0), (0, 0), wall_id="BAD")
    audit = wall_order.audit_internal_directions([bad_wall])
    assert audit["ok"] is False
    assert audit["offenders"] == ["BAD"]


# =========================================================== PIPELINE_ORDER
def test_continuous_first_evidence_sem_rastro_e_not_available():
    """Item 18/34: sem rastro do motor, a resposta e' SEMPRE 'nao sei' -
    nunca um 'sim' inventado a partir do resultado final."""
    evidence = pipeline_order.continuous_first_evidence()
    assert evidence["status"] == pipeline_order.STATUS_NOT_AVAILABLE
    assert evidence["observed_stage_order"] is None


def test_continuous_first_evidence_compara_rastro_quando_existe():
    matching = pipeline_order.continuous_first_evidence(
        list(pipeline_order.EXPECTED_STAGE_ORDER))
    assert matching["status"] == pipeline_order.STATUS_MATCHES

    diverging = pipeline_order.continuous_first_evidence(["opening", "full_wall"])
    assert diverging["status"] == pipeline_order.STATUS_DIVERGES


# ================================================================== CLI
def test_manifest_json_existe_e_carrega_sem_erro():
    assert os.path.isfile(manifest.DEFAULT_MANIFEST_PATH)
    data = manifest.load_default()
    assert data["schema_version"] == manifest.SCHEMA_VERSION
    assert len(data["projects"]) >= 3


# ======================================================================
# CR-BLOCK-REFERENCE-CORPUS - a partir daqui
# ======================================================================

# ------------------------------------------------- dois eixos do manifesto
def test_new_entry_deriva_kind_e_confidence_do_rotulo_legado():
    """Item 16/48: chamada NO FORMATO ANTIGO (so' reference_type, sem
    reference_kind/confidence) continua funcionando - os dois eixos novos
    saem de LEGACY_TO_AXES sozinhos."""
    entry = manifest.new_entry(
        project_id="x", name="x", reference_type=manifest.HUMAN_REFERENCE_AVAILABLE,
        source="teste")
    assert entry["reference_kind"] == manifest.KIND_HUMAN
    assert entry["confidence"] == manifest.CONFIDENCE_MEDIUM
    assert entry["reproducible"] is True


def test_projeto_nao_golden_participa_normalmente():
    """Item 39: reference_type != GOLDEN_CONFIRMED nao impede nada - so'
    muda o nivel de confianca. Um HUMAN_REFERENCE_AVAILABLE tem que
    validar limpo e ser 'reproducible'."""
    entry = manifest.new_entry(
        project_id="x", name="x", reference_type=manifest.HUMAN_REFERENCE_AVAILABLE,
        source="teste")
    assert manifest.validate_entry(entry) == []
    assert entry["reproducible"] is True
    assert entry["reference_type"] != manifest.GOLDEN_CONFIRMED


def test_projeto_golden_participa_normalmente():
    entry = manifest.new_entry(
        project_id="x", name="x", reference_type=manifest.GOLDEN_CONFIRMED,
        source="teste", validated_at="2026-09-02", approved_by_human=True)
    assert manifest.validate_entry(entry) == []
    assert entry["confidence"] == manifest.CONFIDENCE_GOLDEN


def test_analysis_only_exige_missing_requirements_e_nao_reproduzivel():
    entry = manifest.new_entry(
        project_id="x", name="x", reference_type=manifest.ANALYSIS_ONLY_REFERENCE,
        source="teste")
    problems = manifest.validate_entry(entry)
    assert any("missing_requirements" in p for p in problems)

    entry["missing_requirements"] = ["input.json com geometria"]
    assert manifest.validate_entry(entry) == []
    assert entry["reproducible"] is False


def test_filter_by_reference_kind_e_confidence():
    data = manifest.load_default()
    human = manifest.filter_by_reference_kind(data, manifest.KIND_HUMAN)
    assert {"torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"} <= set(
        e["project_id"] for e in human)

    medium_or_above = manifest.filter_by_confidence(data, minimum=manifest.CONFIDENCE_MEDIUM)
    for entry in medium_or_above:
        assert manifest.CONFIDENCE_RANK[entry["confidence"]] >= manifest.CONFIDENCE_RANK[manifest.CONFIDENCE_MEDIUM]

    none_only = manifest.filter_by_confidence(data, exact=manifest.CONFIDENCE_NONE)
    assert all(e["confidence"] == manifest.CONFIDENCE_NONE for e in none_only)


# ------------------------------------------------------------- promocao
def test_promote_recusa_promocao_sem_evidencia():
    entry = manifest.new_entry(
        project_id="x", name="x", reference_type=manifest.HUMAN_REFERENCE_AVAILABLE,
        source="teste")
    with pytest.raises(manifest.PromotionError):
        manifest.promote(entry, manifest.CONFIDENCE_HIGH, evidence="")


def test_promote_recusa_degradar_confianca():
    entry = manifest.new_entry(
        project_id="x", name="x", reference_type=manifest.HUMAN_REFERENCE_AVAILABLE,
        source="teste")
    with pytest.raises(manifest.PromotionError):
        manifest.promote(entry, manifest.CONFIDENCE_LOW, evidence="tentativa invalida")


def test_promote_medium_para_high_registra_verified_at_e_historico():
    entry = manifest.new_entry(
        project_id="x", name="x", reference_type=manifest.HUMAN_REFERENCE_AVAILABLE,
        source="teste")
    promoted = manifest.promote(
        entry, manifest.CONFIDENCE_HIGH,
        evidence="revisei a extracao contra o .rvt original, bate 100%",
        by="alguem@escritorio")
    assert promoted["confidence"] == manifest.CONFIDENCE_HIGH
    assert promoted["verified_at"]
    assert len(promoted["promotion_history"]) == 1
    assert manifest.validate_entry(promoted) == []
    # original NAO foi mutado (item 33: nao sobrescrever historia em silencio)
    assert entry["confidence"] == manifest.CONFIDENCE_MEDIUM


def test_promote_high_para_golden_exige_approved_by_human():
    entry = manifest.new_entry(
        project_id="x", name="x", reference_type=manifest.HUMAN_REFERENCE_AVAILABLE,
        source="teste", confidence=manifest.CONFIDENCE_HIGH, verified_at="2026-09-01")
    with pytest.raises(manifest.PromotionError):
        manifest.promote(entry, manifest.CONFIDENCE_GOLDEN, evidence="sem aprovacao formal ainda")

    promoted = manifest.promote(
        entry, manifest.CONFIDENCE_GOLDEN,
        evidence="aprovado formalmente pelo responsavel tecnico em reuniao registrada",
        by="responsavel_tecnico", extra_fields={"approved_by_human": True})
    assert promoted["confidence"] == manifest.CONFIDENCE_GOLDEN
    assert promoted["approved_by_human"] is True
    assert manifest.validate_entry(promoted) == []


def test_promocao_invalida_para_golden_sem_kind_human_e_recusada():
    """GOLDEN so' faz sentido com reference_kind=HUMAN (item 3/38)."""
    entry = manifest.new_entry(
        project_id="x", name="x", reference_type=manifest.SOLVER_GENERATED_ONLY,
        source="teste", reference_kind=manifest.KIND_SOLVER,
        confidence=manifest.CONFIDENCE_HIGH, verified_at="2026-09-01")
    with pytest.raises(manifest.PromotionError):
        manifest.promote(
            entry, manifest.CONFIDENCE_GOLDEN, evidence="tentativa invalida",
            extra_fields={"approved_by_human": True})


def test_manifesto_oficial_nao_tem_nenhum_confidence_golden_inventado():
    """Item 6/39 continua valendo com os dois eixos: nenhum projeto do
    repositorio tem confidence=GOLDEN hoje."""
    data = manifest.load_default()
    for entry in data["projects"]:
        assert entry["confidence"] != manifest.CONFIDENCE_GOLDEN


# ---------------------------------------------------------- capabilities
def test_infer_capabilities_sem_scan_e_vazio():
    assert capabilities.infer_capabilities(None) == []


def test_infer_capabilities_detecta_abertura_prisma_e_ltx():
    wall = _wall((0, 0), (300, 0), wall_id="W",
                rows=[_row_with_blocks(0, [("B39", 0, 39)]),
                     _row_with_blocks(1, [("B39", 0, 39)])])
    wall["openings"] = [model.make_opening(model.OPENING_DOOR, 100, 180, 0, 210)]
    wall["junctions"] = [{"type": model.JUNCTION_L, "point_cm": [300.0, 0.0], "neighbors": []}]
    project = _project("p", "solver", [wall])

    caps = capabilities.infer_capabilities(
        {"has_reference": True, "has_input": True}, reference_kind=manifest.KIND_HUMAN,
        reference_project=project)
    assert capabilities.CAN_TEST_WALL_COVERAGE in caps
    assert capabilities.CAN_TEST_BLOCK_LAYOUT in caps
    assert capabilities.CAN_TEST_PRISM in caps
    assert capabilities.CAN_TEST_OPENINGS in caps
    assert capabilities.CAN_TEST_LTX in caps
    assert capabilities.CAN_COMPARE_TO_HUMAN in caps
    assert capabilities.CAN_TEST_DETERMINISM in caps


def test_infer_capabilities_projeto_sem_abertura_nem_ltx_nao_reclama():
    wall = _wall((0, 0), (300, 0), wall_id="W", rows=[_row_with_blocks(0, [("B39", 0, 39)])])
    project = _project("p", "solver", [wall])
    caps = capabilities.infer_capabilities({"has_input": True}, reference_project=project)
    assert capabilities.CAN_TEST_OPENINGS not in caps
    assert capabilities.CAN_TEST_LTX not in caps
    assert capabilities.CAN_TEST_PRISM not in caps  # so' 1 fiada


def test_manifesto_oficial_reflete_capabilities_reais():
    data = manifest.load_default()
    tgd = manifest.get(data, "torre_easy_lo_r00_tgd")
    for cap in (capabilities.CAN_TEST_WALL_COVERAGE, capabilities.CAN_TEST_OPENINGS,
               capabilities.CAN_TEST_LTX, capabilities.CAN_COMPARE_TO_HUMAN):
        assert cap in tgd["capabilities"]
    analysis_only = manifest.get(data, "chacara_torre_easy_lo_tropicale")
    assert analysis_only["capabilities"] == []


# --------------------------------------------------------------- corpus
def test_reference_corpus_lista_os_projetos_do_manifesto():
    rc = corpus.ReferenceCorpus.load_default()
    ids = set(rc.list_projects())
    assert {"torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1",
           "piloto_sintetico_2x2"} <= ids


def test_reference_corpus_get_project_inexistente_e_none():
    rc = corpus.ReferenceCorpus.load_default()
    assert rc.get_project("nao-existe-de-verdade") is None


def test_reference_corpus_filter_by_capability():
    rc = corpus.ReferenceCorpus.load_default()
    entries = rc.filter_by_capability(capabilities.CAN_COMPARE_TO_HUMAN)
    assert entries
    for entry in entries:
        assert capabilities.CAN_COMPARE_TO_HUMAN in entry["capabilities"]


def test_reference_corpus_golden_projects_vazio_hoje():
    rc = corpus.ReferenceCorpus.load_default()
    assert rc.golden_projects() == []


def test_reference_corpus_analysis_only_projects_nao_reproducible():
    rc = corpus.ReferenceCorpus.load_default()
    entries = rc.analysis_only_projects()
    assert entries
    for entry in entries:
        assert entry["reproducible"] is False


def test_run_corpus_marca_analysis_only_como_not_comparable_com_motivo():
    rc = corpus.ReferenceCorpus.load_default()
    rows = corpus.run_corpus(rc, project_ids=["chacara_torre_easy_lo_tropicale"])
    assert len(rows) == 1
    assert rows[0]["comparable"] is False
    assert rows[0]["reason"]


def test_run_corpus_projeto_reproduzivel_compara_baseline_consigo_mesmo():
    rc = corpus.ReferenceCorpus.load_default()
    rows = corpus.run_corpus(rc, project_ids=["piloto_sintetico_2x2"],
                             reference_artifact="baseline", current_artifact="baseline")
    assert rows[0]["comparable"] is True
    assert rows[0]["comparison"]["verdict"] == compare.VERDICT_NEUTRAL


def test_summarize_corpus_run_nunca_esconde_regressao_critica_atras_de_media():
    """Item 19, literal: 2 projetos melhoram/ficam neutros, 1 tem
    regressao critica -> overall NUNCA pode ser IMPROVED/NEUTRAL."""
    reference_score = _score_with_critical(0, wall_count=3)
    current_score_ok = _score_with_critical(0, wall_count=3)
    current_score_critical = _score_with_critical(2, wall_count=3)

    rows = [
        {"project_id": "bom_1", "comparable": True, "reason": None,
         "comparison": compare.compare({"score": reference_score}, {"score": current_score_ok})},
        {"project_id": "bom_2", "comparable": True, "reason": None,
         "comparison": compare.compare({"score": reference_score}, {"score": current_score_ok})},
        {"project_id": "quebrou_porta", "comparable": True, "reason": None,
         "comparison": compare.compare({"score": reference_score}, {"score": current_score_critical})},
    ]
    summary = corpus.summarize_corpus_run(rows)
    assert summary["overall"] == corpus.CRITICAL_REGRESSION_PRESENT
    assert summary["critical_regressions"]
    assert summary["critical_regressions"][0]["project_id"] == "quebrou_porta"


def test_build_matrix_marca_not_comparable_quando_projeto_nao_comparavel():
    rows = [{"project_id": "x", "comparable": False, "reason": "sem dado", "comparison": None}]
    matrix = corpus.build_matrix(rows)
    assert matrix["rows"][0]["cells"]["coverage"] == corpus.NOT_COMPARABLE


def test_teste_fundamental_corpus_com_human_solver_e_synthetic_sem_nenhum_golden():
    """Item 45, literal: um corpus com 1 HUMAN_REFERENCE, 1 SOLVER_REFERENCE
    (aqui: LEGACY_BASELINE, que e' reference_kind=SOLVER) e 1
    SYNTHETIC_REFERENCE executa os tres - nenhum precisa ser
    GOLDEN_CONFIRMED."""
    human_entry = manifest.new_entry(
        project_id="humano", name="humano", reference_type=manifest.HUMAN_REFERENCE_AVAILABLE,
        source="teste", available_metrics=["quality"])
    solver_entry = manifest.new_entry(
        project_id="solver", name="solver", reference_type=manifest.LEGACY_BASELINE,
        source="teste", available_metrics=["quality"])
    synthetic_entry = manifest.new_entry(
        project_id="sintetico", name="sintetico", reference_type=manifest.SOLVER_GENERATED_ONLY,
        reference_kind=manifest.KIND_SYNTHETIC, confidence=manifest.CONFIDENCE_NONE,
        source="teste", available_metrics=["quality"])

    for entry in (human_entry, solver_entry, synthetic_entry):
        assert entry["reference_type"] != manifest.GOLDEN_CONFIRMED
        assert entry["confidence"] != manifest.CONFIDENCE_GOLDEN
        assert manifest.validate_entry(entry) == []

    rc = corpus.ReferenceCorpus(manifest.make_manifest(
        [human_entry, solver_entry, synthetic_entry]))
    assert rc.list_projects() == ["humano", "solver", "sintetico"]
    assert len(rc.human_reference_projects()) == 1
    assert len(rc.filter_by_reference_kind(manifest.KIND_SOLVER)) == 1
    assert len(rc.filter_by_reference_kind(manifest.KIND_SYNTHETIC)) == 1
    assert rc.golden_projects() == []

    # Todos os tres sao reproduzeis o bastante para "executar" (item 45)
    # mesmo sem golden - reproducible e' derivado do EIXO, nunca de golden.
    assert all(e["reproducible"] for e in rc.all_entries())


# ---------------------------------------------------------- pipeline_trace
def test_pipeline_trace_evento_com_estagio_desconhecido_e_rejeitado():
    with pytest.raises(ValueError):
        pipeline_trace.make_trace_event("W001", "ESTAGIO_INVENTADO", 1)


def test_pipeline_trace_ordem_correta_valida_ok():
    events = [
        pipeline_trace.make_trace_event("W001", pipeline_trace.STAGE_WALL_START, 1),
        pipeline_trace.make_trace_event("W001", pipeline_trace.STAGE_INTERSECTIONS_RESOLVED, 2),
        pipeline_trace.make_trace_event("W001", pipeline_trace.STAGE_CONTINUOUS_FILL, 3),
        pipeline_trace.make_trace_event("W001", pipeline_trace.STAGE_PRISM_VALIDATED, 4),
        pipeline_trace.make_trace_event("W001", pipeline_trace.STAGE_OPENING_APPLIED, 5, opening_id="O1"),
        pipeline_trace.make_trace_event("W001", pipeline_trace.STAGE_CONFLICTING_BLOCK_REMOVED, 6, opening_id="O1"),
        pipeline_trace.make_trace_event("W001", pipeline_trace.STAGE_LOCAL_REPAIR, 7, opening_id="O1"),
        pipeline_trace.make_trace_event("W001", pipeline_trace.STAGE_FINAL_VALIDATION, 8),
    ]
    result = pipeline_trace.validate_trace(events)
    assert result["ok"] is True
    assert result["walls_checked"] == 1


def test_pipeline_trace_parede_sem_abertura_pode_pular_estagios_de_abertura():
    events = [
        pipeline_trace.make_trace_event("W002", pipeline_trace.STAGE_WALL_START, 1),
        pipeline_trace.make_trace_event("W002", pipeline_trace.STAGE_CONTINUOUS_FILL, 2),
        pipeline_trace.make_trace_event("W002", pipeline_trace.STAGE_PRISM_VALIDATED, 3),
        pipeline_trace.make_trace_event("W002", pipeline_trace.STAGE_FINAL_VALIDATION, 4),
    ]
    assert pipeline_trace.validate_trace(events)["ok"] is True


def test_pipeline_trace_estagio_fora_de_ordem_e_apontado():
    events = [
        pipeline_trace.make_trace_event("W003", pipeline_trace.STAGE_OPENING_APPLIED, 1),
        pipeline_trace.make_trace_event("W003", pipeline_trace.STAGE_WALL_START, 2),
    ]
    result = pipeline_trace.validate_trace(events)
    assert result["ok"] is False
    assert result["problems"][0]["wall_id"] == "W003"


def test_pipeline_trace_sequence_repetida_e_apontada():
    events = [
        pipeline_trace.make_trace_event("W004", pipeline_trace.STAGE_WALL_START, 1),
        pipeline_trace.make_trace_event("W004", pipeline_trace.STAGE_CONTINUOUS_FILL, 1),
    ]
    result = pipeline_trace.validate_trace(events)
    assert result["ok"] is False


def test_pipeline_trace_parse_trace_reporta_evento_malformado_sem_derrubar_os_outros():
    raw = [
        {"wall_id": "W001", "stage": pipeline_trace.STAGE_WALL_START, "sequence": 1},
        {"wall_id": "W001", "stage": "NAO_EXISTE", "sequence": 2},
        {"stage": pipeline_trace.STAGE_FINAL_VALIDATION, "sequence": 3},  # sem wall_id
    ]
    events, problems = pipeline_trace.parse_trace(raw)
    assert len(events) == 1
    assert len(problems) == 2


def test_pipeline_order_from_trace_sem_eventos_e_not_available():
    result = pipeline_order.continuous_first_evidence_from_trace()
    assert result["status"] == pipeline_order.STATUS_NOT_AVAILABLE


def test_pipeline_order_from_trace_com_eventos_ok_da_matches():
    events = [
        pipeline_trace.make_trace_event("W001", pipeline_trace.STAGE_WALL_START, 1),
        pipeline_trace.make_trace_event("W001", pipeline_trace.STAGE_FINAL_VALIDATION, 2),
    ]
    result = pipeline_order.continuous_first_evidence_from_trace(events)
    assert result["status"] == pipeline_order.STATUS_MATCHES


def test_pipeline_order_from_trace_com_eventos_fora_de_ordem_da_diverges():
    events = [
        pipeline_trace.make_trace_event("W001", pipeline_trace.STAGE_FINAL_VALIDATION, 1),
        pipeline_trace.make_trace_event("W001", pipeline_trace.STAGE_WALL_START, 2),
    ]
    result = pipeline_order.continuous_first_evidence_from_trace(events)
    assert result["status"] == pipeline_order.STATUS_DIVERGES
    assert result["problems"]


# ------------------------------------------------------- human_reference
def test_classify_difference_changed_code_sem_findings_e_equivalent():
    diff = {"action": wall_diff.ACTION_CHANGED_CODE, "wall": "W001"}
    assert human_reference.classify_difference(diff) == human_reference.CLASS_EQUIVALENT


def test_classify_difference_layout_sem_findings_e_unknown_nunca_adivinhado():
    """Item 41: nao inventar equivalencia sem base - sem achados para
    checar nivel 1, ADDED/REMOVED/MOVED fica UNKNOWN, nunca DIFFERENT_VALID."""
    diff = {"action": wall_diff.ACTION_ADDED, "wall": "W001"}
    assert human_reference.classify_difference(diff) == human_reference.CLASS_UNKNOWN


def test_classify_difference_layout_com_nivel1_e_potential_regression():
    diff = {"action": wall_diff.ACTION_MOVED, "wall": "W001"}
    findings = [base.finding("POSITION_OVERLAP", wall="W001", detail="colisao")]
    assert (human_reference.classify_difference(diff, findings=findings)
           == human_reference.CLASS_POTENTIAL_REGRESSION)


def test_classify_difference_layout_sem_nivel1_e_different_valid():
    diff = {"action": wall_diff.ACTION_ADDED, "wall": "W001"}
    findings = [base.finding("PRISM_STAGGER_BELOW_TARGET", wall="W001", detail="nivel 2")]
    assert (human_reference.classify_difference(diff, findings=findings)
           == human_reference.CLASS_DIFFERENT_VALID)


def test_classify_difference_changed_code_com_nivel1_e_rule_violation():
    diff = {"action": wall_diff.ACTION_CHANGED_CODE, "wall": "W001"}
    findings = [base.finding("JUNCTION_MISSING_BINDING", wall="W001", detail="sem amarracao")]
    assert (human_reference.classify_difference(diff, findings=findings)
           == human_reference.CLASS_RULE_VIOLATION)


def test_human_vs_solver_report_conta_por_classe():
    current = _one_wall_project("cur", "solver", [[("B39", 0, 39), ("B19", 40, 59)]])
    reference = _one_wall_project("ref", "revit_reference", [[("B34", 0, 39)]])
    comparison = wall_diff.compute_wall_diff(current, reference)
    wall_diff_result = wall_diff.wall_diff_report(comparison)
    report = human_reference.human_vs_solver_report(wall_diff_result, findings=None)
    assert report["findings_available"] is False
    assert sum(report["totals"].values()) > 0


# =================================================================== fim

