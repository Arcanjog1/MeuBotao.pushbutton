# -*- coding: utf-8 -*-
"""REGRAS secao 88.7 (regra obrigatoria do usuario, 2026-10-23): o compensador que
a 76.1 poe num no' sem amarracao valida (JUNCTION_UNRESOLVED_FILL) NUNCA e'
materializado - a peca e' pulada, o no' fica em `unresolved_junctions` e a RUN
deixa de ser "estruturalmente resolvida". Mesmos dubles de
test_materializacao_e_estado_da_run (handler REAL, dois canais)."""
import pytest

import load_script

m = load_script.load()
from core.engine import wall_stepper as stepper
from test_materializacao_e_estado_da_run import beta, bloco, pecas_criadas  # noqa: F401

FILL = stepper.JUNCTION_UNRESOLVED_FILL_REASON


def test_constante_e_chave_de_produto():
    assert m.UNRESOLVED_JUNCTION_FILL_RULE_ID == FILL
    assert m.UNRESOLVED_JUNCTION_FILL_IS_SKIPPED is True


def test_plano_pula_o_compensador_do_no_e_registra_o_no(beta):
    handler = beta([[bloco(100, "C09", FILL, node=41), bloco(140, "B39", "STANDARD_FILL")]], porta=None)
    plano = m.materialization_plan(handler.solve_result, m.controlled_beta_preflight(
        handler.solve_result, handler.walls_to_create, handler.openings_per_wall, handler.catalog, 0.0))
    assert len(plano["skip"]) == 1
    rec = plano["skip"][0][2]
    assert rec["rule_id"] == FILL and rec["severity"] == "BOND_UNRESOLVED" and rec["requires_human_review"]
    assert rec["structural_role"] is None                      # regra 76: compensador nao amarra
    assert plano["unresolved_bonds"] == []                     # ...entao nao e' "amarracao rejeitada"
    assert [u["node_index"] for u in plano["unresolved_junctions"]] == [41]


def test_criacao_nao_materializa_o_compensador_do_no(beta):
    handler = beta([[bloco(100, "C09", FILL, node=41), bloco(140, "B39", "STANDARD_FILL")],
                    [bloco(100, "C09", FILL, node=41), bloco(140, "B39", "STANDARD_FILL")]], porta=None)
    handler._execute_create(__import__("test_beta_atomic_creation").Document())
    cr = handler.create_result
    assert cr["created_count"] == 2 and cr["skipped_count"] == 2
    assert all(r["rule_id"] == FILL for r in cr["skipped"])
    assert [u["course_index"] for u in cr["unresolved_junctions"]] == [0, 1]
    assert cr["structurally_resolved"] is False
    assert all(c["logical_code"] == "B39" for _ci, c in pecas_criadas(handler))


def test_chave_desligada_volta_ao_comportamento_da_76_1(beta, monkeypatch):
    monkeypatch.setattr(m, "UNRESOLVED_JUNCTION_FILL_IS_SKIPPED", False)
    handler = beta([[bloco(100, "C09", FILL, node=41)]], porta=None)
    plano = m.materialization_plan(handler.solve_result, m.controlled_beta_preflight(
        handler.solve_result, handler.walls_to_create, handler.openings_per_wall, handler.catalog, 0.0))
    assert plano["skip"] == [] and plano["unresolved_junctions"] == []


def test_invasao_de_porta_pelo_compensador_continua_uma_unica_pulada(beta):
    """Compensador de no' que TAMBEM invade a porta: uma peca, dois motivos, sem duplicar."""
    handler = beta([[bloco(40, "C09", FILL, node=41)]])          # porta padrao 30..80
    plano = m.materialization_plan(handler.solve_result, m.controlled_beta_preflight(
        handler.solve_result, handler.walls_to_create, handler.openings_per_wall, handler.catalog, 0.0))
    assert len(plano["skip"]) == 1
    assert set(plano["skip"][0][2]["rules"]) == {m.OPENING_INVASION_RULE_ID, FILL}
    assert len(plano["unresolved_junctions"]) == 1
