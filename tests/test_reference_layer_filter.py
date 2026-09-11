# -*- coding: utf-8 -*-
"""Secao 49 de REGRAS_MODULACAO_BLOCOS.md - filtro por LAYER DE REFERENCIA
ESTRUTURAL (decisao do usuario, 2026-09-11).

Evidencia (BUTANTA, medida via MCP): o CAD '1 PAV' do doc de teste e' uma
exportacao arquitetonica do Revit - o layer 'Paredes' traz TODAS as paredes
(46 pares) e o layer estrutural 'ARQ-STR-BLOCO' esta' vazio. O projeto pronto
tem o desenho estrutural (import 7097743, layer 'ARQ-STR-BLOCO', 11.415
linhas): ele cobre as 34 paredes de alvenaria em 0,42..0,99 e as 12 que nao
sao alvenaria em 0,03..0,08 - e apara os tocos que o CAD arquitetonico
desenha atraves da parede vizinha (99 -> 64cm nas tres curtas; 1039 -> ~1000
na 8079818). Nenhum ID, nome ou posicao entra no criterio: so' geometria
entre os dois conjuntos de linhas.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pytest
import solver_bench as sb  # noqa: E402

m = sb.m
XYZ, Line = m.XYZ, m.Line
ft = sb.ft
seg = sb.seg
F2CM = 30.48
EV = os.path.join(os.path.dirname(HERE), "docs", "checkpoints", "evidence")
WALLS_JSON = os.path.join(EV, "2026-09-10-butanta-test-walls.json")
CAD_JSON = os.path.join(EV, "2026-09-10-butanta-cad-lines.json")
HUMAN_JSON = os.path.join(EV, "2026-09-10-butanta-human-sequences.json")


def _butanta():
    if not (os.path.isfile(WALLS_JSON) and os.path.isfile(CAD_JSON) and os.path.isfile(HUMAN_JSON)):
        pytest.skip("evidencia de BUTANTA ausente")
    walls_json = json.load(open(WALLS_JSON, encoding="utf-8"))["walls"]
    cad = json.load(open(CAD_JSON, encoding="utf-8"))
    human = json.load(open(HUMAN_JSON, encoding="utf-8"))["per_wall"]
    # linhas do layer estrutural do projeto pronto: JSON em decimetros do
    # frame do import humano -> cm no frame do doc de teste (o envelope do
    # layer coincide com o envelope das 46 paredes: 1629 x 2929cm)
    raw = cad["7097743:ARQ-STR-BLOCO"]
    minx = min(min(v[0], v[2]) for v in raw)
    miny = min(min(v[1], v[3]) for v in raw)
    ref = [Line.CreateBound(XYZ((v[0] - minx) * 10.0 / F2CM, (v[1] - miny) * 10.0 / F2CM, 0.0),
                            XYZ((v[2] - minx) * 10.0 / F2CM, (v[3] - miny) * 10.0 / F2CM, 0.0))
           for v in raw if abs(v[0] - v[2]) > 1e-9 or abs(v[1] - v[3]) > 1e-9]
    axes, ids = [], []
    for w in walls_json:
        axes.append((Line.CreateBound(XYZ(*[float(x) for x in w["p0"]]), XYZ(*[float(x) for x in w["p1"]])),
                     14.0 / 100.0 * m.FEET_PER_METER, (False, False)))
        ids.append(w["id"])
    masonry = set(w["id"] for w in walls_json
                  if sum(len(human.get(str(w["id"]), {}).get(str(c), [])) for c in range(13)) >= 20)
    return axes, ids, ref, masonry


def test_sem_referencia_devolve_a_entrada_intacta():
    axes = [(seg(0, 0, 400, 0), ft(14.0), (False, False))]
    kept, report = m.clip_axes_to_reference_lines(axes, [])
    assert kept == axes and report["kept"] == 1 and not report["dropped"]


def test_sintetico_descarta_apara_e_mantem():
    # duas faces a +-7cm ao longo de [0, 300] de um eixo de 400: cobertura
    # 0,75 -> mantido e aparado a 300; um eixo sem faces -> descartado; um
    # eixo coberto inteiro (com um vao de 80cm no meio) -> mantido intacto
    faces = [seg(0, 7, 300, 7), seg(0, -7, 300, -7),
             seg(0, 507, 100, 507), seg(0, 493, 100, 493), seg(180, 507, 400, 507), seg(180, 493, 400, 493)]
    axes = [(seg(0, 0, 400, 0), ft(14.0), (False, False)),
            (seg(0, 200, 400, 200), ft(14.0), (False, False)),
            (seg(0, 500, 400, 500), ft(14.0), (False, False))]
    kept, report = m.clip_axes_to_reference_lines(axes, faces)
    assert [d["index"] for d in report["dropped"]] == [1]
    assert [t["index"] for t in report["trimmed"]] == [0]
    assert abs(report["trimmed"][0]["new_length_cm"] - 300.0) < 0.5
    assert len(kept) == 2
    assert abs(kept[0][0].Length * F2CM - 300.0) < 0.5
    assert abs(kept[1][0].Length * F2CM - 400.0) < 0.5      # vao interno nao apara


def test_butanta_separa_as_34_de_alvenaria_das_12_que_nao_sao():
    axes, ids, ref, masonry = _butanta()
    kept, report = m.clip_axes_to_reference_lines(axes, ref)
    dropped = set(ids[d["index"]] for d in report["dropped"])
    assert dropped == set(ids) - masonry, sorted(dropped ^ (set(ids) - masonry))
    assert report["kept"] == len(masonry) == 34
    cov = dict(report["coverage"])
    alv = [cov[i] for i in range(len(ids)) if ids[i] in masonry]
    nao = [cov[i] for i in range(len(ids)) if ids[i] not in masonry]
    # margem dos dois lados do limiar - o parametro nao esta' no fio da navalha
    assert min(alv) > m.REFERENCE_LAYER_MIN_COVERAGE + 0.10, min(alv)
    assert max(nao) < m.REFERENCE_LAYER_MIN_COVERAGE - 0.10, max(nao)


def test_butanta_apara_os_tocos_que_o_projeto_pronto_nao_constroi():
    axes, ids, ref, masonry = _butanta()
    kept, report = m.clip_axes_to_reference_lines(axes, ref)
    trimmed = dict((ids[t["index"]], t) for t in report["trimmed"])
    for wid in (8079861, 8079862, 8079863):
        assert wid in trimmed, wid
        assert 60.0 <= trimmed[wid]["new_length_cm"] <= 68.0, trimmed[wid]
    assert 8079818 in trimmed and 990.0 <= trimmed[8079818]["new_length_cm"] <= 1010.0, trimmed.get(8079818)
    # aparar nunca alonga nem inverte o eixo
    for t in report["trimmed"]:
        assert t["new_length_cm"] < t["length_cm"] + 1e-6
