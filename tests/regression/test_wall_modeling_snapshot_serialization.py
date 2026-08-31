# -*- coding: utf-8 -*-
"""O snapshot da FASE A tem que sobreviver a uma planta REAL.

Defeito medido em 2026-08-31, na primeira vez que o pipeline rodou sobre um
.rvt de verdade (Etapa 2B):

    TypeError: Object of type XYZ is not JSON serializable
      when serializing dict item 'bbox_center_xy'
      when serializing dict item 'op'
      ... 'assignments' ... 'openings' ... 'diagnostics'

`core/engine/wall_pairing.py::assign_openings_to_walls` guarda em
`diagnostics["openings"]["assignments"]` os dicts `op` ORIGINAIS - e esses
carregam `XYZ` VIVO em `center_xy` e `bbox_center_xy`. `build_snapshot()`
repassava esse dicionario inteiro para o snapshot, e `save()` estourava na
primeira abertura atribuida a uma parede.

POR QUE OS TESTES DA ETAPA 2A NAO PEGARAM (o ponto deste arquivo):

  1. `test_wall_modeling_bridge.py` para em `build_snapshot()` - um dict em
     memoria aceita `XYZ` numa boa. Quem estoura e' `save()`, que nenhum
     teste chamava.
  2. O `_opening()` daquele arquivo nao preenche `bbox_center_cm`, entao
     `wall_modeling_bridge._op_from_dict` nunca criava `bbox_center_xy`.

Uma planta real tem as duas coisas. Por isso os testes aqui SEMPRE passam
por `save()` em disco e SEMPRE incluem `bbox_center_cm` - e' o unico jeito
de reproduzir o caso que quebrou.

Nao basta "nao estourar": a informacao de diagnostico tem que continuar
LEGIVEL no arquivo (em cm), senao a correcao teria sido apagar o problema
em vez de resolve-lo.
"""

import json

import pytest

from benchmark import wall_modeling_bridge
from benchmark.extract import wall_modeling_snapshot as snap

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


def _opening_with_bbox(center_cm, width_cm, sill_cm, head_cm,
                       bbox_center_cm, element_id="OP1"):
    """Abertura como um documento REAL a produz: com `bbox_center_cm`.

    `revit_input_real_dump.py` sempre preenche esse campo (vem da
    bounding box da familia), e `wall_modeling_bridge._op_from_dict` o
    converte em `XYZ` vivo - a peca que faltava para o teste da Etapa 2A
    reproduzir o defeito."""
    return {
        "element_id": element_id,
        "center_cm": [float(center_cm[0]), float(center_cm[1])],
        "bbox_center_cm": [float(bbox_center_cm[0]), float(bbox_center_cm[1])],
        "width_cm": float(width_cm),
        "sill_cm": float(sill_cm),
        "head_cm": float(head_cm),
        "center_source": "geometria",
    }


def _input_real(segments, openings=None, **setup_overrides):
    return {
        "schema_version": 1,
        "project_id": "teste_snapshot_serializacao",
        "setup_frozen": _setup(**setup_overrides),
        "segments": segments,
        "openings": openings or [],
        "metadata": {},
    }


@pytest.fixture
def bridge_result_with_assigned_opening():
    """Uma parede de 300cm com uma abertura de 90cm no meio - atribuida,
    portanto com registro em `diagnostics["openings"]["assignments"]`."""
    payload = _input_real(
        [_seg(0, 0, 300, 0), _seg(0, 14, 300, 14)],
        [_opening_with_bbox((150.0, 7.0), 90.0, 0.0, 210.0,
                            bbox_center_cm=(167.0, 7.0), element_id="OP-REAL")],
    )
    result = wall_modeling_bridge.run_wall_modeling(payload)
    assignments = result["diagnostics"]["openings"].get("assignments") or []
    assert assignments, "a abertura precisava ter sido atribuida para o teste valer"
    # Confirma que o caso reproduzido e' MESMO o que quebrou: o `op` que o
    # motor guardou tem XYZ vivo nos dois campos.
    op = assignments[0]["op"]
    assert hasattr(op["center_xy"], "X")
    assert op.get("bbox_center_xy") is not None and hasattr(op["bbox_center_xy"], "X")
    return result


def test_save_produz_json_valido_com_abertura_atribuida(
        bridge_result_with_assigned_opening, tmp_path):
    """O caso exato que estourou: FALHA na implementacao antiga (que jogava
    `diagnostics` cru no snapshot), passa na atual."""
    snapshot = snap.build_snapshot(bridge_result_with_assigned_opening,
                                   "teste_snapshot_serializacao")
    path = tmp_path / "wall_modeling_snapshot.json"
    snap.save(snapshot, str(path))

    reloaded = json.loads(path.read_text(encoding="utf-8"))
    assert reloaded["project_id"] == "teste_snapshot_serializacao"


def test_diagnostics_de_abertura_sobrevivem_em_cm(
        bridge_result_with_assigned_opening, tmp_path):
    """Serializar nao pode virar sinonimo de descartar: os dados do `op`
    continuam no arquivo, agora como numero."""
    snapshot = snap.build_snapshot(bridge_result_with_assigned_opening,
                                   "teste_snapshot_serializacao")
    path = tmp_path / "snapshot.json"
    snap.save(snapshot, str(path))
    reloaded = json.loads(path.read_text(encoding="utf-8"))

    assignments = reloaded["diagnostics"]["openings"]["assignments"]
    assert len(assignments) == 1
    record = assignments[0]
    assert record["op"]["element_id"] == "OP-REAL"
    assert record["op"]["center_cm"] == pytest.approx([150.0, 7.0], abs=0.01)
    assert record["op"]["bbox_center_cm"] == pytest.approx([167.0, 7.0], abs=0.01)
    assert record["op"]["width_cm"] == pytest.approx(90.0, abs=0.01)
    assert record["op"]["sill_cm"] == pytest.approx(0.0, abs=0.01)
    assert record["op"]["head_cm"] == pytest.approx(210.0, abs=0.01)
    assert record["wall_index"] == 0
    assert record["t_end_cm"] - record["t_start_cm"] == pytest.approx(90.0, abs=0.5)


def test_abertura_nao_atribuida_tambem_serializa(tmp_path):
    """`unassigned_openings` guarda o MESMO `op` cru - na planta real sao 9
    delas. Se so' `assignments` tivesse sido tratado, o arquivo quebraria
    igual."""
    payload = _input_real(
        [_seg(0, 0, 300, 0), _seg(0, 14, 300, 14)],
        [_opening_with_bbox((150.0, 5000.0), 90.0, 0.0, 210.0,
                            bbox_center_cm=(167.0, 5000.0), element_id="OP-LONGE")],
    )
    result = wall_modeling_bridge.run_wall_modeling(payload)
    unassigned = result["diagnostics"]["openings"].get("unassigned_openings") or []
    assert unassigned, "a abertura precisava ter ficado sem parede"

    snapshot = snap.build_snapshot(result, "teste_snapshot_serializacao")
    path = tmp_path / "snapshot.json"
    snap.save(snapshot, str(path))
    reloaded = json.loads(path.read_text(encoding="utf-8"))

    entries = reloaded["diagnostics"]["openings"]["unassigned_openings"]
    assert len(entries) == 1
    assert entries[0]["element_id"] == "OP-LONGE"
    assert entries[0]["center_cm"] == pytest.approx([150.0, 5000.0], abs=0.01)


def test_snapshot_inteiro_e_json_puro(bridge_result_with_assigned_opening):
    """Rede de seguranca ampla: `json.dumps` SEM `default=` no snapshot
    inteiro. Qualquer objeto vivo novo que apareca em qualquer secao
    (nao so' em `diagnostics`) derruba este teste."""
    snapshot = snap.build_snapshot(bridge_result_with_assigned_opening,
                                   "teste_snapshot_serializacao")
    json.dumps(snapshot, ensure_ascii=False)


def test_nome_explicito_do_sha_do_motor(bridge_result_with_assigned_opening):
    """Os dois hashes do projeto medem coisas diferentes e ja foram
    confundidos (2026-08-31). O snapshot carrega o sha do ARQUIVO do motor,
    e o nome do campo tem que dizer isso - `solver_decision_fingerprint`
    (tests/solver_bench.py) e' o outro, e nao mora aqui."""
    snapshot = snap.build_snapshot(bridge_result_with_assigned_opening,
                                   "teste_snapshot_serializacao")
    assert "wall_modeling_engine_sha256" in snapshot
    assert "engine_fingerprint" not in snapshot
    digest = snapshot["wall_modeling_engine_sha256"]
    assert digest is None or (len(digest) == 64 and int(digest, 16) >= 0)
