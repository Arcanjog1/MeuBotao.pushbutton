# -*- coding: utf-8 -*-
"""Testes da FASE A do benchmark de Wall Modeling (Etapa 2A):

    input_real -> wall_modeling_bridge.run_wall_modeling()
               -> extract/wall_modeling_snapshot.py

Todos rodam headless (dubles de `tests/revit_stubs.py`, via
`solver_bridge.engine()` - o MESMO motor que os testes de
`tests/test_script.py` exercitam), sem nenhum `.rvt` e sem Transaction.
Geometria pequena e sintetica, de proposito (item 13 do pedido)."""

import os

import pytest

from benchmark import model, solver_bridge, wall_modeling_bridge
from benchmark.extract import wall_modeling_snapshot as snap
from benchmark.wall_modeling_bridge import WallModelingBridgeError

LAYER = "A-PAREDE"


def _setup(**overrides):
    setup = {
        "layer": LAYER,
        "thicknesses_cm": [14.0],
        "openings_mode": "auto",
        "wall_mode": "segmented",
        "level": "TESTE",
        "base_z_cm": 0.0,
        "wall_height_cm": 280.0,
        "num_courses": 14,
    }
    setup.update(overrides)
    return setup


def _seg(x0, y0, x1, y1, layer=LAYER):
    return {"layer": layer, "start": [float(x0), float(y0)], "end": [float(x1), float(y1)]}


def _opening(center_cm, width_cm, sill_cm, head_cm, element_id="OP1"):
    return {
        "element_id": element_id,
        "center_cm": [float(center_cm[0]), float(center_cm[1])],
        "width_cm": float(width_cm),
        "sill_cm": float(sill_cm),
        "head_cm": float(head_cm),
        "center_source": "geometria",
    }


def _input_real(segments, openings=None, **setup_overrides):
    return {
        "schema_version": 1,
        "project_id": "teste_wall_modeling",
        "setup_frozen": _setup(**setup_overrides),
        "segments": segments,
        "openings": openings or [],
        "metadata": {},
    }


# --------------------------------------------------------- setup_frozen
def test_setup_frozen_obrigatorio():
    """Sem setup_frozen (ou incompleto), o bridge tem que FALHAR - nunca
    inventar layer/espessura/altura por conta propria (item 6 do pedido)."""
    incompleto = _input_real([_seg(0, 0, 300, 0), _seg(0, 14, 300, 14)])
    del incompleto["setup_frozen"]["wall_height_cm"]
    with pytest.raises(WallModelingBridgeError):
        wall_modeling_bridge.run_wall_modeling(incompleto)


def test_setup_frozen_ausente_por_completo():
    payload = {"segments": [_seg(0, 0, 300, 0), _seg(0, 14, 300, 14)]}
    with pytest.raises(WallModelingBridgeError):
        wall_modeling_bridge.run_wall_modeling(payload)


# ------------------------------------------------------------ parede simples
def test_parede_simples():
    payload = _input_real([_seg(0, 0, 300, 0), _seg(0, 14, 300, 14)])
    result = wall_modeling_bridge.run_wall_modeling(payload)
    assert len(result["walls_to_create"]) == 1
    module = result["module"]
    centerline, thickness_ft, _locks = result["walls_to_create"][0]
    thickness_cm = thickness_ft / module.FEET_PER_METER * 100.0
    assert abs(thickness_cm - 14.0) < 0.01
    p0, p1 = centerline.GetEndPoint(0), centerline.GetEndPoint(1)
    y_cm = sorted([p0.Y, p1.Y])
    # eixo no meio das duas faces (y=0 e y=14) -> y=7
    assert abs(y_cm[0] / module.FEET_PER_METER * 100.0 - 7.0) < 0.01
    assert abs(y_cm[1] / module.FEET_PER_METER * 100.0 - 7.0) < 0.01


def test_nenhum_par_valido_levanta_erro_explicito():
    """Linhas paralelas existem, mas a 25cm de distancia - fora das
    espessuras escolhidas (so' 14cm) - tem que falhar de forma explicita,
    nunca devolver um resultado vazio silencioso."""
    payload = _input_real([_seg(0, 0, 300, 0), _seg(0, 25, 300, 25)])
    with pytest.raises(WallModelingBridgeError) as excinfo:
        wall_modeling_bridge.run_wall_modeling(payload)
    assert excinfo.value.diagnostics


# ----------------------------------------------------------- boneca curta
def test_boneca_curta_ainda_vira_parede():
    """Trecho de so' 15cm (acima do piso absoluto de 2cm, sobreposicao
    100%) tem que continuar virando parede - e' uma boneca legitima, nao
    ruido geometrico."""
    payload = _input_real([_seg(0, 0, 15, 0), _seg(0, 14, 15, 14)])
    result = wall_modeling_bridge.run_wall_modeling(payload)
    assert len(result["walls_to_create"]) == 1
    module = result["module"]
    centerline, _t, _l = result["walls_to_create"][0]
    length_cm = centerline.GetEndPoint(0).DistanceTo(centerline.GetEndPoint(1)) \
        / module.FEET_PER_METER * 100.0
    assert length_cm >= 15.0 - 0.5


# --------------------------------------------------------------- dedup
def test_deduplicacao_remove_linha_de_hachura_repetida():
    """Uma terceira linha quase coincidente com uma das faces (hachura/cota
    duplicada no mesmo Layer) nao pode gerar uma SEGUNDA parede empilhada."""
    payload = _input_real([
        _seg(0, 0, 300, 0), _seg(0, 14, 300, 14),
        _seg(0, 0.5, 300, 0.5), _seg(0, 14.5, 300, 14.5),
    ])
    result = wall_modeling_bridge.run_wall_modeling(payload)
    assert len(result["walls_to_create"]) == 1
    assert result["diagnostics"]["duplicates_removed_count"] >= 1


# ------------------------------------------------------------ encontro L
def test_encontro_l_um_unico_no():
    payload = _input_real([
        _seg(0, -7, 300, -7), _seg(0, 7, 300, 7),      # parede horizontal
        _seg(-7, 0, -7, 300), _seg(7, 0, 7, 300),      # parede vertical
    ])
    result = wall_modeling_bridge.run_wall_modeling(payload)
    assert len(result["walls_to_create"]) == 2
    corners = [n for n in result["wall_graph_nodes"] if n["kind"] == "L_CORNER"]
    assert len(corners) == 1, [n["kind"] for n in result["wall_graph_nodes"]]


# ------------------------------------------------------------ encontro T
def test_encontro_t_um_unico_no():
    payload = _input_real([
        _seg(0, -7, 400, -7), _seg(0, 7, 400, 7),        # parede principal
        _seg(193, 0, 193, 300), _seg(207, 0, 207, 300),  # parede que chega no meio
    ])
    result = wall_modeling_bridge.run_wall_modeling(payload)
    tees = [n for n in result["wall_graph_nodes"] if n["kind"] == "T_INTERSECTION"]
    assert len(tees) == 1, [n["kind"] for n in result["wall_graph_nodes"]]


# ------------------------------------------------------------ encontro X
def test_encontro_x_e_reconhecido():
    payload = _input_real([
        _seg(0, -7, 400, -7), _seg(0, 7, 400, 7),          # parede horizontal
        _seg(193, -200, 193, 200), _seg(207, -200, 207, 200),  # parede vertical cruzando no meio
    ])
    result = wall_modeling_bridge.run_wall_modeling(payload)
    kinds = [n["kind"] for n in result["wall_graph_nodes"]]
    assert "X_INTERSECTION" in kinds, kinds


# ------------------------------------------------------- extensao de ponta
def test_extensao_de_ponta_estica_ate_a_face_oposta():
    """A ponta da parede horizontal, que para no EIXO da vertical antes da
    extensao, tem que avancar ate' a FACE OPOSTA dela depois."""
    payload = _input_real([
        _seg(0, -7, 293, -7), _seg(0, 7, 293, 7),      # para exatamente no eixo x=293
        _seg(286, 0, 286, 300), _seg(300, 0, 300, 300),  # parede vertical: faces 286/300
    ])
    result = wall_modeling_bridge.run_wall_modeling(payload)
    module = result["module"]
    # acha a parede horizontal (a mais longa) pelo antes/depois
    for index, (centerline, _t, _l) in enumerate(result["walls_to_create"]):
        before_line, _bt, _bl = result["walls_before_extension"][index]
        before_len = before_line.GetEndPoint(0).DistanceTo(before_line.GetEndPoint(1))
        after_len = centerline.GetEndPoint(0).DistanceTo(centerline.GetEndPoint(1))
        if abs(before_len / module.FEET_PER_METER * 100.0 - 293.0) < 1.0:
            assert after_len > before_len, "a ponta tinha que ter esticado"
            return
    pytest.fail("parede horizontal nao encontrada")


# ------------------------------------------------------------- aberturas
def test_abertura_atribuida_a_parede():
    payload = _input_real(
        [_seg(0, 0, 300, 0), _seg(0, 14, 300, 14)],
        openings=[_opening((100, 7), 80, 0, 210)],
    )
    result = wall_modeling_bridge.run_wall_modeling(payload)
    assert len(result["openings_per_wall"]) == 1
    assert len(result["openings_per_wall"][0]) == 1
    assert not result["diagnostics"]["openings"]["unassigned_openings"]


def test_abertura_nao_atribuida_fica_registrada():
    payload = _input_real(
        [_seg(0, 0, 300, 0), _seg(0, 14, 300, 14)],
        openings=[_opening((100, 500), 80, 0, 210)],  # longe de qualquer parede
    )
    result = wall_modeling_bridge.run_wall_modeling(payload)
    assert result["openings_per_wall"] == [[]]
    assert len(result["diagnostics"]["openings"]["unassigned_openings"]) == 1


# ---------------------------------------------------------- unused_lines
def test_linha_sem_par_fica_em_unused_lines_com_motivo():
    payload = _input_real([
        _seg(0, 0, 300, 0), _seg(0, 14, 300, 14),   # par valido
        _seg(0, 100, 300, 100),                     # sobra, sem parceira
    ])
    result = wall_modeling_bridge.run_wall_modeling(payload)
    assert len(result["unused_lines"]) == 1
    assert result["unused_lines"][0]["reason"]


# --------------------------------------------------------- ordem preservada
def test_ordem_de_walls_to_create_e_estavel_entre_execucoes():
    payload = _input_real([
        _seg(0, -7, 400, -7), _seg(0, 7, 400, 7),
        _seg(193, 0, 193, 300), _seg(207, 0, 207, 300),
        _seg(0, 500, 200, 500), _seg(0, 514, 200, 514),
    ])
    r1 = wall_modeling_bridge.run_wall_modeling(payload)
    r2 = wall_modeling_bridge.run_wall_modeling(payload)
    keys1 = [_wall_key(r1["module"], w) for w in r1["walls_to_create"]]
    keys2 = [_wall_key(r2["module"], w) for w in r2["walls_to_create"]]
    assert keys1 == keys2


def _wall_key(module, wall_tuple):
    centerline, thickness_ft, _locks = wall_tuple
    p0, p1 = centerline.GetEndPoint(0), centerline.GetEndPoint(1)
    to_cm = lambda v: v / module.FEET_PER_METER * 100.0
    return model.wall_stable_key(
        (to_cm(p0.X), to_cm(p0.Y)), (to_cm(p1.X), to_cm(p1.Y)), to_cm(thickness_ft)
    )


# -------------------------------------------------------------- snapshot
def _build_snapshot(payload, project_id="teste_wall_modeling"):
    result = wall_modeling_bridge.run_wall_modeling(payload)
    return snap.build_snapshot(result, project_id)


def test_snapshot_e_deterministico():
    payload = _input_real([
        _seg(0, -7, 400, -7), _seg(0, 7, 400, 7),
        _seg(193, 0, 193, 300), _seg(207, 0, 207, 300),
    ], openings=[_opening((100, 7), 80, 0, 210)])
    s1 = _build_snapshot(payload)
    s2 = _build_snapshot(payload)
    assert s1["walls"] == s2["walls"]
    assert s1["nodes"] == s2["nodes"]
    assert s1["openings_per_wall"] == s2["openings_per_wall"]
    assert s1["end_to_node"] == s2["end_to_node"]


def test_chaves_estaveis_sao_deterministicas():
    payload = _input_real([_seg(0, 0, 300, 0), _seg(0, 14, 300, 14)])
    s1 = _build_snapshot(payload)
    s2 = _build_snapshot(payload)
    assert [w["key"] for w in s1["walls"]] == [w["key"] for w in s2["walls"]]


def test_snapshot_registra_unused_lines():
    payload = _input_real([
        _seg(0, 0, 300, 0), _seg(0, 14, 300, 14),
        _seg(0, 100, 300, 100),
    ])
    snapshot = _build_snapshot(payload)
    assert len(snapshot["unused_lines"]) == 1


def test_snapshot_settings_walls_already_extended():
    payload = _input_real([_seg(0, 0, 300, 0), _seg(0, 14, 300, 14)])
    snapshot = _build_snapshot(payload)
    assert snapshot["settings"]["walls_already_extended"] is True


def test_serializacao_e_deserializacao_preserva_geometria(tmp_path):
    payload = _input_real([
        _seg(0, -7, 400, -7), _seg(0, 7, 400, 7),
        _seg(193, 0, 193, 300), _seg(207, 0, 207, 300),
    ])
    snapshot = _build_snapshot(payload)
    path = os.path.join(str(tmp_path), "snapshot.json")
    snap.save(snapshot, path)
    reloaded = snap.load(path)
    assert reloaded["walls"] == snapshot["walls"]
    assert reloaded["nodes"] == snapshot["nodes"]
    assert reloaded["schema_version"] == snap.SCHEMA_VERSION


# ---------------------------------------- walls_already_extended (item 7)
def test_walls_already_extended_nao_causa_dupla_extensao():
    """O snapshot ja' representa paredes depois de
    extend_wall_ends_to_junctions - alimentar isso de volta no
    solver_bridge.plan_from_input NAO pode esticar de novo."""
    payload = _input_real([
        _seg(0, -7, 293, -7), _seg(0, 7, 293, 7),
        _seg(286, 0, 286, 300), _seg(300, 0, 300, 300),
    ])
    snapshot = _build_snapshot(payload)
    input_project = snap.to_solver_input(snapshot)
    assert input_project["settings"]["walls_already_extended"] is True

    nodes, walls_to_create, end_to_node, openings_per_wall = (
        solver_bridge.plan_from_input(input_project)
    )
    module = solver_bridge.engine()
    to_cm = lambda v: v / module.FEET_PER_METER * 100.0

    # comprimento de cada parede reconstruida tem que bater com o que o
    # snapshot ja' gravava - se tivesse esticado de novo, a mais longa
    # (a horizontal, que ja' chegou na face oposta da vertical) cresceria
    # mais ainda.
    snapshot_lengths = sorted(round(w["length_cm"], 1) for w in snapshot["walls"])
    rebuilt_lengths = sorted(
        round(to_cm(centerline.GetEndPoint(0).DistanceTo(centerline.GetEndPoint(1))), 1)
        for centerline, _t, _l in walls_to_create
    )
    assert rebuilt_lengths == snapshot_lengths


# ------------------------------------------------------- runner (item 11)
def test_runner_wall_modeling_only(tmp_path, monkeypatch):
    """`runner.run_wall_modeling_only` le' input_real.json e grava
    wall_modeling_snapshot.json - isolado do solver de blocos."""
    from benchmark import runner

    monkeypatch.setattr(runner, "PROJECTS_DIR", str(tmp_path))
    project_id = "projeto_teste_wm"
    paths = runner.project_paths(project_id)
    os.makedirs(paths["dir"])

    payload = _input_real([_seg(0, 0, 300, 0), _seg(0, 14, 300, 14)])
    with open(paths["input_real"], "w", encoding="utf-8") as handle:
        import json
        json.dump(payload, handle)

    snapshot = runner.run_wall_modeling_only(project_id)
    assert len(snapshot["walls"]) == 1
    assert os.path.isfile(paths["wall_modeling_snapshot"])

    reloaded = snap.load(paths["wall_modeling_snapshot"])
    assert reloaded["walls"] == snapshot["walls"]
