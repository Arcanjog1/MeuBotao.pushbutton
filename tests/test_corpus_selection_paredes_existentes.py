# -*- coding: utf-8 -*-
"""Secao 49.1 (2026-09-24, ciclo 2 / D5) - a regra 49 (cobertura pelo layer de
referencia estrutural) tambem no fluxo de PAREDES EXISTENTES, so' descarte
(nunca apara), e o registro do CORPUS DA RUN (detectados / selecionados /
excluidos com motivo) que toda execucao carrega.

Evidencia real: as 46 Walls do doc de teste de BUTANTA x as faces do layer
estrutural do projeto pronto (mesma evidencia versionada da secao 49). O
conjunto "alvenaria" vem do projeto HUMANO (>= 20 blocos no eixo) - nenhum ID
de parede entra no criterio nem neste arquivo.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pytest
import solver_bench as sb  # noqa: E402
import test_reference_layer_filter as ref  # noqa: E402

m = sb.m
ft, seg = sb.ft, sb.seg
F2CM = 30.48
CORE = os.path.join(os.path.dirname(HERE), "nuvem", "core")


def _cm(line):
    return line.Length * F2CM


def _faces(t0, t1, y, half=7.0):
    return [seg(t0, y + half, t1, y + half), seg(t0, y - half, t1, y - half)]


# ----------------------------------------------------------------- regra geral, 46 eixos reais
def test_regra_geral_separa_as_34_de_alvenaria_das_12_sem_aparar():
    axes, ids, faces, masonry = ref._butanta()
    by_axis = dict((i, [("wall%d" % ids[i], "cad")]) for i in range(len(axes)))
    walls, new_by_axis, new_ids, corpus = m.select_existing_axes_by_reference_layer(
        axes, by_axis, list(ids), faces, "ARQ-STR-BLOCO", axis_keys=["uid-%d" % i for i in ids])
    assert corpus["detected_axes"] == 46
    assert corpus["selected_axes"] == len(walls) == len(new_ids) == len(new_by_axis) == len(masonry) == 34
    assert corpus["excluded_axes"] == 12
    excluded_ids = set(item["wall_id"] for item in corpus["excluded"])
    assert excluded_ids == set(ids) - masonry, sorted(excluded_ids ^ (set(ids) - masonry))
    # os 34 selecionados sao exatamente os de alvenaria, na ordem original e INTACTOS
    assert set(new_ids) == masonry
    originais = dict((ids[i], axes[i]) for i in range(len(axes)))
    for entry, wid in zip(walls, new_ids):
        assert abs(_cm(entry[0]) - _cm(originais[wid][0])) < 1e-6, wid
        a, b = entry[0].GetEndPoint(0), originais[wid][0].GetEndPoint(0)
        assert abs(a.X - b.X) < 1e-9 and abs(a.Y - b.Y) < 1e-9, wid
    assert corpus["trimmed"] == []
    # reindexacao 0..33 e cada indice novo aponta para a Wall certa
    assert sorted(new_by_axis.keys()) == list(range(34))
    for new_idx, wid in enumerate(new_ids):
        assert new_by_axis[new_idx] == [("wall%d" % wid, "cad")]
    # margem: nenhum excluido perto do limiar, nenhum selecionado perto do limiar
    for item in corpus["excluded"]:
        assert item["geometry_summary"]["coverage"] < m.REFERENCE_LAYER_MIN_COVERAGE - 0.10
    cov = dict(corpus["coverage"])
    for i, wid in enumerate(ids):
        if wid in masonry:
            assert cov[i] > m.REFERENCE_LAYER_MIN_COVERAGE + 0.10, (wid, cov[i])


def test_registro_de_cada_exclusao_tem_motivo_regra_layer_e_geometria():
    axes, ids, faces, masonry = ref._butanta()
    _w, _b, _i, corpus = m.select_existing_axes_by_reference_layer(
        axes, {}, list(ids), faces, "ARQ-STR-BLOCO", axis_keys=["uid-%d" % i for i in ids])
    assert corpus["mode"] == "paredes existentes"
    assert corpus["rule_id"] == m.CORPUS_RULE_REFERENCE_LAYER == "REGRA_49_REFERENCE_LAYER_COVERAGE"
    assert corpus["reference_layer"] == "ARQ-STR-BLOCO"
    assert corpus["min_coverage"] == m.REFERENCE_LAYER_MIN_COVERAGE
    for item in corpus["excluded"]:
        assert item["axis_key"] == "uid-%d" % item["wall_id"]
        assert item["rule_id"] == m.CORPUS_RULE_REFERENCE_LAYER
        assert item["source_layer"] == "ARQ-STR-BLOCO"
        assert "secao 49" in item["reason"] and "cobertura" in item["reason"]
        geo = item["geometry_summary"]
        for key in ("length_cm", "p0_cm", "p1_cm", "width_cm", "coverage", "min_coverage"):
            assert key in geo, key
        assert geo["length_cm"] > 0 and 0.0 <= geo["coverage"] < geo["min_coverage"]


# ----------------------------------------------------------------- sintetico: entra / sai / limitrofes
def test_sintetico_entra_sai_e_limitrofes_sem_aparar():
    # 4 eixos de 400 cm: coberto inteiro (entra), sem face nenhuma (sai),
    # cobertura 0,25 (sai: abaixo do limiar) e cobertura 0,35 (entra, e NAO e' aparado)
    axes = [(seg(0, 0, 400, 0), ft(14.0), (False, False)),
            (seg(0, 100, 400, 100), ft(14.0), (False, False)),
            (seg(0, 200, 400, 200), ft(14.0), (False, False)),
            (seg(0, 300, 400, 300), ft(14.0), (False, False))]
    faces = _faces(0, 400, 0) + _faces(0, 100, 200) + _faces(0, 140, 300)
    walls, by_axis, ids, corpus = m.select_existing_axes_by_reference_layer(
        axes, {0: ["a"], 1: ["b"], 2: ["c"], 3: ["d"]}, [10, 11, 12, 13], faces, "REF")
    assert [item["wall_id"] for item in corpus["excluded"]] == [11, 12]
    assert ids == [10, 13] and by_axis == {0: ["a"], 1: ["d"]}
    assert (corpus["detected_axes"], corpus["selected_axes"], corpus["excluded_axes"]) == (4, 2, 2)
    # o eixo com 35% de cobertura continua com 400 cm (sem aparar ao envelope coberto)
    assert abs(_cm(walls[1][0]) - 400.0) < 0.5
    assert corpus["trimmed"] == []
    cov = dict(corpus["coverage"])
    assert abs(cov[2] - 0.25) < 0.02 and abs(cov[3] - 0.35) < 0.02


def test_clip_sem_aparar_e_o_mesmo_criterio_do_fluxo_cad():
    axes = [(seg(0, 0, 400, 0), ft(14.0), (False, False)), (seg(0, 100, 400, 100), ft(14.0), (False, False))]
    faces = _faces(0, 300, 0)
    kept_cad, rep_cad = m.clip_axes_to_reference_lines(axes, faces)
    kept_ex, rep_ex = m.clip_axes_to_reference_lines(axes, faces, trim=False)
    assert [d["index"] for d in rep_cad["dropped"]] == [d["index"] for d in rep_ex["dropped"]] == [1]
    assert rep_cad["coverage"] == rep_ex["coverage"]
    assert abs(_cm(kept_cad[0][0]) - 300.0) < 0.5      # CAD -> Walls apara
    assert abs(_cm(kept_ex[0][0]) - 400.0) < 0.5       # paredes existentes: intacto
    assert rep_ex["trimmed"] == [] and len(rep_cad["trimmed"]) == 1


# ----------------------------------------------------------------- sem referencia: corpus completo, registrado
def test_sem_layer_de_referencia_nada_e_excluido_e_o_corpus_e_registrado():
    axes, ids, _faces_, _masonry = ref._butanta()
    walls, by_axis, new_ids, corpus = m.select_existing_axes_by_reference_layer(
        axes, dict((i, [i]) for i in range(46)), list(ids), [], None)
    assert walls == list(axes) and new_ids == list(ids) and len(by_axis) == 46
    assert corpus["rule_id"] == m.CORPUS_RULE_NONE
    assert (corpus["detected_axes"], corpus["selected_axes"], corpus["excluded_axes"]) == (46, 46, 0)
    assert corpus["excluded"] == [] and corpus["reference_layer"] is None


# ----------------------------------------------------------------- relatorio e UI
def test_relatorio_do_solver_e_ui_mostram_detectados_selecionados_excluidos():
    from core import ui_state
    axes, ids, faces, _masonry = ref._butanta()
    _w, _b, _i, corpus = m.select_existing_axes_by_reference_layer(
        axes, {}, list(ids), faces, "ARQ-STR-BLOCO", axis_keys=["uid-%d" % i for i in ids])
    linhas = m._corpus_report_lines(corpus)
    assert linhas[0] == ("CORPUS DA RUN: DETECTED_AXES=46 SELECTED_AXES=34 EXCLUDED_AXES=12 "
                         "regra=REGRA_49_REFERENCE_LAYER_COVERAGE layer=ARQ-STR-BLOCO")
    assert sum(1 for l in linhas if l.startswith("  EXCLUDED axis_key=uid-")) == 12
    assert all(("rule_id=REGRA_49_REFERENCE_LAYER_COVERAGE" in l and "source_layer=ARQ-STR-BLOCO" in l
                and "coverage=" in l) for l in linhas[1:])
    ui = ui_state.corpus_lines({"corpus_selection": corpus})
    assert ui[0].startswith("Eixos: 46 detectados · 34 modulados · 12 excluídos (regra REGRA_49_REFERENCE_LAYER_COVERAGE")
    assert sum(1 for l in ui if l.startswith("  Excluído: parede ")) == 12
    # sem registro: a UI diz que nao ha' corpus, nunca inventa 0 exclusoes
    assert ui_state.corpus_lines({})[0].startswith("Eixos: corpus não registrado")
    assert m._corpus_report_lines(None)[0].startswith("CORPUS DA RUN: nao registrado")


def test_solve_result_carrega_o_corpus_do_setup_da_run():
    fonte = open(os.path.join(CORE, "wall_modeling.py"), encoding="utf-8").read()
    assert 'self.solve_result["corpus_selection"] = (getattr(self, "setup", None) or {}).get("corpus_selection")' in fonte
    assert '"corpus_selection": corpus_selection,' in fonte          # fluxo de paredes existentes (run_setup)
    assert 'setup["corpus_selection"] = corpus_selection_record(' in fonte   # fluxo CAD -> Walls
    assert fonte.count("select_existing_axes_by_reference_layer(") >= 2      # definicao + uso no fluxo
    # a selecao acontece ANTES do solver: antes das aberturas, do grafo e do handler
    i_sel = fonte.index("walls_to_create, created_walls_by_axis, wall_ids, corpus_selection = select_existing_axes_by_reference_layer(")
    i_open = fonte.index("openings_per_wall = assign_openings_to_walls(walls_to_create, all_openings, opening_diagnostics)\n    unassigned_openings")
    assert i_sel < i_open


# ----------------------------------------------------------------- ausencia de hardcode
def _codigo_sem_comentarios_nem_strings(path):
    """So' os tokens de CODIGO (nomes, numeros, operadores): comentarios e
    strings/docstrings ficam de fora - evidencia em comentario e' permitida,
    regra em codigo nao."""
    import io as _io
    import tokenize
    partes = []
    with _io.open(path, encoding="utf-8") as handle:
        for tok in tokenize.generate_tokens(handle.readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            if tok.type in (tokenize.NAME, tokenize.NUMBER, tokenize.OP):
                partes.append(tok.string)
            elif tok.type in (tokenize.NEWLINE, tokenize.NL):
                partes.append("\n")
    return " ".join(partes)


def test_nenhuma_regra_de_producao_cita_id_projeto_ou_coordenada():
    padroes = [re.compile(r"\b8(079|284)\d{3}\b"),            # ElementIds do corpus de BUTANTA
               re.compile(r"EXCLUDED_IDS"),
               re.compile(r"wall_id\s*==\s*\d"),
               re.compile(r"project\s*==\s*"),
               re.compile(r"butanta", re.I)]
    for name in ("wall_modeling.py", "ui_state.py", "ui_components.py", os.path.join("engine", "wall_pairing.py")):
        codigo = _codigo_sem_comentarios_nem_strings(os.path.join(CORE, name))
        for padrao in padroes:
            assert not padrao.search(codigo), (name, padrao.pattern, padrao.search(codigo).group(0))
