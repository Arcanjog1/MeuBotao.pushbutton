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
    compare, fingerprint, inventory, manifest, metrics, pipeline_order,
    wall_diff, wall_order,
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
    """Item 16: nunca depender de GetEndPoint(0)/GetEndPoint(1) cru - a
    MESMA parede desenhada ao contrario tem que dar o mesmo fingerprint,
    porque a chave (`model.wall_stable_key`) ja' normaliza o sentido."""
    forward = _wall((0, 0), (300, 0), wall_id="W",
                    rows=[_row_with_blocks(0, [("B39", 0, 39)])])
    backward = _wall((300, 0), (0, 0), wall_id="W",
                     rows=[_row_with_blocks(0, [("B39", 0, 39)])])
    p1 = _project("p", "solver", [forward])
    p2 = _project("p", "solver", [backward])
    assert fingerprint.canonical_fingerprint(p1) == fingerprint.canonical_fingerprint(p2)


def test_fingerprint_muda_quando_uma_peca_muda():
    a = _one_wall_project("p", "solver", [[("B39", 0, 39)]])
    b = _one_wall_project("p", "solver", [[("B34", 0, 34), ("B04", 34, 38)]])
    assert fingerprint.canonical_fingerprint(a) != fingerprint.canonical_fingerprint(b)


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


def test_manifesto_oficial_classifica_baseline_como_legacy_nas_notas():
    data = manifest.load_default()
    torre = manifest.get(data, "torre_easy_lo_r00_tgd")
    assert torre is not None
    assert "LEGACY_BASELINE" in torre["notes"]


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
