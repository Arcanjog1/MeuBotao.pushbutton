# -*- coding: utf-8 -*-
"""Secao 87 de REGRAS_MODULACAO_BLOCOS.md (2026-10-08): o fluxo CAD -> Walls do
botao reproduz a geometria que gerou a modulacao APROVADA do BUTANTA
(lote 20261008-143828, motor 06ecb87, calculo r7_13) a partir do arquivo CRU.

Evidencia versionada em docs/checkpoints/evidence/2026-10-08-s87-cad-flow/:
linhas do layer `Estrutura _1_` (import arquitetonico 8079028), linhas do layer
`ARQ-STR-BLOCO` (import estrutural 7097743, ja' na escala/posicao das
paredes), as 44 aberturas (Mobiliario) e os 34 eixos + aberturas por parede
que o calculo aprovado recebeu.

O que esta' protegido aqui:
- 87.1 o layer certo e' `Estrutura _1_` (46 pares = as 46 paredes historicas);
  `Paredes` (acabamento) fragmenta e NAO reproduz;
- 87.2 a regra 49 so' CLASSIFICA no fluxo CAD (sem aparar) e a referencia
  pode vir de OUTRO import (rotulo "<import> | <layer>" no combo);
- 87.3 a sobra de CAD de ate' 10 cm e' aparada mesmo com testa (W8, 5 cm);
- 87.4 peitoril ate' 2 cm abaixo da base sobe para a base (porta 8078997);
- o conjunto final (34 eixos + aberturas) e' igual ao da referencia aprovada.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pytest

import load_script  # noqa: E402

m = load_script.load()
XYZ, Line = m.XYZ, m.Line
FT = 30.48
EV = os.path.join(os.path.dirname(HERE), "docs", "checkpoints", "evidence", "2026-10-08-s87-cad-flow")
FILES = ("cad_estrutura_1_lines_cm.json", "cad_paredes_lines_cm.json", "ref_arq_str_bloco_lines_cm.json",
         "openings_cm.json", "approved_axes_cm.json")


def ft(cm):
    return cm / 100.0 * m.FEET_PER_METER


def seg(x0, y0, x1, y1):
    return Line.CreateBound(XYZ(ft(x0), ft(y0), 0.0), XYZ(ft(x1), ft(y1), 0.0))


def _lines(name):
    rows = json.load(open(os.path.join(EV, name), encoding="utf-8"))["lines_cm"]
    out = []
    for x0, y0, x1, y1 in rows:
        if math.hypot(x1 - x0, y1 - y0) < 1e-6:
            continue
        out.append(Line.CreateBound(XYZ(x0 / FT, y0 / FT, 0.0), XYZ(x1 / FT, y1 / FT, 0.0)))
    return out


def _openings():
    ops = []
    for o in json.load(open(os.path.join(EV, "openings_cm.json"), encoding="utf-8"))["openings"]:
        center = XYZ(o["center_cm"][0] / FT, o["center_cm"][1] / FT, 0.0)
        ops.append({
            "center_xy": center, "center_source": o["center_source"],
            "insertion_xy": XYZ(o["insertion_cm"][0] / FT, o["insertion_cm"][1] / FT, 0.0),
            "bbox_center_xy": center,
            "hand_xy": XYZ(o["hand"][0], o["hand"][1], 0.0) if o.get("hand") else None,
            "width_ft": o["width_cm"] / FT, "sill_z_abs": o["sill_cm"] / FT, "head_z_abs": o["head_cm"] / FT,
            "element_id": str(o["element_id"]), "element_id_obj": o["element_id"],
        })
    return ops


@pytest.fixture(scope="module")
def butanta():
    for name in FILES:
        if not os.path.isfile(os.path.join(EV, name)):
            pytest.skip("evidencia da secao 87 ausente: {}".format(name))
    return {
        "estrutura": _lines("cad_estrutura_1_lines_cm.json"),
        "paredes": _lines("cad_paredes_lines_cm.json"),
        "ref": _lines("ref_arq_str_bloco_lines_cm.json"),
        "openings": _openings(),
        "approved": json.load(open(os.path.join(EV, "approved_axes_cm.json"), encoding="utf-8")),
    }


def _diag():
    return {"parallel_pairs": 0, "min_dist_ft": None, "max_dist_ft": None, "offset_suspect_count": 0,
            "offset_suspect_max_ft": 0.0, "cap_clipped_count": 0}


def _pairs(layer_lines, openings):
    """merge -> pares -> dedupe -> fechamento dos encontros (as mesmas chamadas do main())."""
    lines = m.merge_collinear_fragments(layer_lines, m.COLLINEAR_MATCH_TOLERANCE_FT, m.MAX_JUNCTION_GAP_FT, openings,
                                        m.OPENING_GAP_PERP_TOLERANCE_FT, m.OPENING_GAP_WIDTH_SLACK_FT)
    th = [ft(14.0)]
    tol = m.compute_detection_tolerance_ft(th)
    pairs, _unused = m.find_wall_pairs(lines, th, tol, lines, openings, _diag())
    walls, _dup = m.deduplicate_walls(pairs)
    walls, _jm = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    return pairs, walls


def _stage1(layer_lines, openings, ref_lines, base_z_abs=0.0):
    """Ordem do main() depois da secao 87: pares -> dedupe -> extend -> regra 49
    (so' classificacao) -> aberturas -> peitoril na base -> sobra de CAD -> extend -> grafo."""
    _pairs_, walls = _pairs(layer_lines, openings)
    kept, report = m.clip_axes_to_reference_lines(walls, ref_lines, trim=False)
    diag = {"clamped_opening_count": 0, "opening_center_gap_max_ft": 0.0, "opening_off_center_count": 0,
            "assignments": [], "unassigned_openings": []}
    opw = m.assign_openings_to_walls(kept, openings, diag)
    opw, snaps = m.snap_openings_to_wall_base(opw, base_z_abs)
    kept, opw, stubs = m.trim_wall_end_stubs(kept, opw)
    kept, jm = m.extend_wall_ends_to_junctions(kept, m.JUNCTION_FACE_SEARCH_FT)
    nodes, _e2n = m.build_wall_graph(kept, jm)
    return {"walls": kept, "openings_per_wall": opw, "report": report, "snaps": snaps, "stubs": stubs,
            "nodes": nodes, "unassigned": diag["unassigned_openings"]}


def _axis_cm(entry):
    a, b = entry[0].GetEndPoint(0), entry[0].GetEndPoint(1)
    return (a.X * FT, a.Y * FT), (b.X * FT, b.Y * FT)


def _match_approved(walls, approved):
    """Para cada eixo, o indice do eixo aprovado com os mesmos extremos (<= 0,6 cm) e se o sentido e' o mesmo."""
    out = []
    for entry in walls:
        p0, p1 = _axis_cm(entry)
        best = None
        for j, (q0, q1, _th) in enumerate(approved["walls_cm"]):
            for same, (u0, u1) in ((True, (q0, q1)), (False, (q1, q0))):
                d = max(math.hypot(p0[0] - u0[0], p0[1] - u0[1]), math.hypot(p1[0] - u1[0], p1[1] - u1[1]))
                if best is None or d < best[0]:
                    best = (d, j, same)
        out.append(best)
    return out


# ---------------------------------------------------------------- 87.1

def test_layer_estrutura_forma_as_46_paredes_historicas(butanta):
    pairs, walls = _pairs(butanta["estrutura"], butanta["openings"])
    assert len(pairs) == 46
    assert len(walls) == 46


def test_layer_paredes_fragmenta_e_nao_reproduz(butanta):
    """87.1: o layer `Paredes` (acabamento arquitetonico) e' o layer ERRADO -
    forma mais pares (faces quebradas nas portas e nos encontros) e deixa
    paredes partidas. Registro do diagnostico, nao uma meta."""
    pairs, walls = _pairs(butanta["paredes"], butanta["openings"])
    assert len(pairs) > 46
    assert len(walls) != 46


# ---------------------------------------------------------------- 87.2

def test_referencia_de_outro_import_seleciona_34_sem_aparar(butanta):
    _pairs_, walls = _pairs(butanta["estrutura"], butanta["openings"])
    kept, report = m.clip_axes_to_reference_lines(walls, butanta["ref"], trim=False)
    assert report["kept"] == 34 and len(report["dropped"]) == 12
    assert report["trimmed"] == []
    lengths_before = sorted(round(w[0].Length * FT, 1) for w in walls)
    lengths_after = sorted(round(w[0].Length * FT, 1) for w in kept)
    assert set(lengths_after) <= set(lengths_before)  # nenhum eixo encurtado


def test_combo_de_referencia_lista_layers_de_outros_imports():
    same = {"Estrutura _1_": [seg(0, 0, 100, 0)] * 3, "Pisos": [seg(0, 0, 50, 0)]}
    other_label = m.reference_layer_label("1 PAV", "ARQ-STR-BLOCO")
    refs = dict(same)
    refs[other_label] = [seg(0, 7, 100, 7)] * 10
    form = m._SetupForm(same, ["Nivel 1"], {"reference_layer": other_label}, reference_layers=refs)
    items = list(form._reference_combo.Items)
    assert items[0] == m.REFERENCE_LAYER_NONE_LABEL
    assert other_label in items and set(same) <= set(items)
    # ordenado por numero de linhas: o layer do outro import (10 linhas) vem primeiro
    assert items[1] == other_label
    assert form._reference_combo.SelectedItem == other_label  # escolha lembrada


def test_combo_de_referencia_sem_outros_imports_continua_igual():
    same = {"Estrutura _1_": [seg(0, 0, 100, 0)] * 3, "Pisos": [seg(0, 0, 50, 0)]}
    form = m._SetupForm(same, ["Nivel 1"], {})
    assert list(form._reference_combo.Items) == [m.REFERENCE_LAYER_NONE_LABEL, "Estrutura _1_", "Pisos"]
    assert form._reference_combo.SelectedIndex == 0


def test_collect_reference_layers_rotula_os_outros_imports(monkeypatch):
    class _Id(object):
        def __init__(self, n):
            self.n = n

        def __eq__(self, other):
            return isinstance(other, _Id) and other.n == self.n

        def __ne__(self, other):
            return not self.__eq__(other)

        def ToString(self):
            return str(self.n)

    class _Param(object):
        def __init__(self, v):
            self.v = v

        def AsString(self):
            return self.v

    class _Type(object):
        def __init__(self, name):
            self.name = name

        def get_Parameter(self, _bip):
            return _Param(self.name)

    class _Doc(object):
        def __init__(self, types):
            self.types = types

        def GetElement(self, tid):
            return self.types[tid]

    class _Import(object):
        def __init__(self, n, name, layers, document):
            self.Id = _Id(n)
            self.Document = document
            self._name = name
            self._layers = layers

        def GetTypeId(self):
            return self._name

        def get_Geometry(self, _opt):
            return self._layers

    class _Collector(object):
        def __init__(self, _doc):
            pass

        def OfClass(self, _cls):
            return self

        def ToElements(self):
            return imports

    document = _Doc({"ARQ": _Type("ARQ"), "1 PAV": _Type("1 PAV")})
    selected = _Import(1, "ARQ", {"Estrutura _1_": [seg(0, 0, 100, 0)]}, document)
    other = _Import(2, "1 PAV", {"ARQ-STR-BLOCO": [seg(0, 7, 100, 7)], "VAZIO": []}, document)
    imports = [selected, other]
    monkeypatch.setattr(m, "FilteredElementCollector", _Collector)
    monkeypatch.setattr(m, "extract_lines_by_layer", lambda geom, by_layer, stats=None: by_layer.update(geom))
    result = m.collect_reference_layers_from_document(document, selected, {"Estrutura _1_": selected._layers["Estrutura _1_"]})
    assert set(result) == {"Estrutura _1_", m.reference_layer_label("1 PAV", "ARQ-STR-BLOCO")}
    assert len(result[m.reference_layer_label("1 PAV", "ARQ-STR-BLOCO")]) == 1


# ---------------------------------------------------------------- 87.3

def test_sobra_de_5cm_com_testa_e_aparada_no_butanta(butanta):
    res = _stage1(butanta["estrutura"], butanta["openings"], butanta["ref"])
    assert [round(s["stub_cm"], 1) for s in res["stubs"]] == [5.0]
    stub = res["stubs"][0]
    assert round(res["walls"][stub["wall_idx"]][0].Length * FT, 1) == 714.0  # 719 - 5 (W8)
    # 87.3: a sobra e' aparada MESMO quando a ponta esta' travada por testa do CAD
    # (o sentido do eixo vem do CAD, entao a ponta pode ser a 0 ou a 1)
    _pairs_, walls = _pairs(butanta["estrutura"], butanta["openings"])
    kept, _report = m.clip_axes_to_reference_lines(walls, butanta["ref"], trim=False)
    locked = []
    for entry in kept:
        p0, p1 = _axis_cm(entry)
        if abs(p0[0] - 1142.0) < 1.0 and abs(p1[0] - 1142.0) < 1.0 and 1448.0 < max(p0[1], p1[1]) < 1460.0:
            locked.append((entry[0], entry[1], (True, True)))
        else:
            locked.append(entry)
    assert sum(1 for e in locked if e[2] == (True, True)) == 1
    diag = {"clamped_opening_count": 0, "opening_center_gap_max_ft": 0.0, "opening_off_center_count": 0,
            "assignments": [], "unassigned_openings": []}
    opw = m.assign_openings_to_walls(locked, butanta["openings"], diag)
    _w, _o, stubs_locked = m.trim_wall_end_stubs(locked, opw)
    assert [round(s["stub_cm"], 1) for s in stubs_locked] == [5.0]


def test_sobra_de_cad_apara_mesmo_com_testa_e_toco_pleno_respeita_a_testa():
    # parede que cruza em x = 100 (faces 93 / 107); a parede horizontal passa 5 cm da face (x = 112)
    crossing = (seg(100, -200, 100, 200), ft(14.0), (False, False))
    locked = (seg(0, 0, 112, 0), ft(14.0), (False, True))
    walls, _opw, stubs = m.trim_wall_end_stubs([crossing, locked], [[], []])
    assert [round(s["stub_cm"], 1) for s in stubs] == [5.0]
    assert round(walls[1][0].Length * FT, 1) == 107.0
    assert walls[1][2] == (False, True)  # a testa continua registrada (impede a extensao)
    # modo pleno (86.9 ligada explicitamente): a testa protege a ponta, como antes
    walls_full, _o, stubs_full = m.trim_wall_end_stubs([crossing, locked], [[], []], enabled=True)
    assert stubs_full == []
    assert round(walls_full[1][0].Length * FT, 1) == 112.0


# ---------------------------------------------------------------- 87.4

def test_peitoril_1cm_abaixo_da_base_sobe_para_a_base_no_butanta(butanta):
    res = _stage1(butanta["estrutura"], butanta["openings"], butanta["ref"])
    assert [(s["wall_idx"] is not None, round(s["delta_cm"], 2), round(s["sill_cm_before"], 2)) for s in res["snaps"]] == [(True, 1.0, -1.0)]
    item = res["snaps"][0]
    op = res["openings_per_wall"][item["wall_idx"]][item["opening_index"]]
    assert round(op[2] * FT, 2) == 0.0 and round(op[3] * FT, 2) == 221.0


@pytest.mark.parametrize("sill_cm,head_cm,expected", [
    (0.0, 221.0, (0.0, 221.0)),      # ja' na base: nada muda
    (-1.0, 220.0, (0.0, 221.0)),     # 1 cm abaixo: sobe, altura preservada
    (-2.0, 219.0, (0.0, 221.0)),     # no limite (2 cm): sobe
    (-2.5, 218.5, (-2.5, 218.5)),    # alem do limite: abertura rebaixada de verdade, fica
    (100.0, 221.0, (100.0, 221.0)),  # janela: nada muda
])
def test_snap_openings_to_wall_base_unitario(sill_cm, head_cm, expected):
    rows = [[(ft(50), ft(150), ft(sill_cm), ft(head_cm))], []]
    out, adjusted = m.snap_openings_to_wall_base(rows, 0.0)
    got = (round(out[0][0][2] * FT, 2), round(out[0][0][3] * FT, 2))
    assert got == expected
    assert (len(adjusted) == 1) == (got != (sill_cm, head_cm))
    assert rows[0][0][2] == ft(sill_cm)  # entrada intacta
    assert out[1] == []


def test_snap_sem_base_devolve_copia_intacta():
    rows = [[(ft(50), ft(150), ft(-1.0), ft(220.0))]]
    out, adjusted = m.snap_openings_to_wall_base(rows, None)
    assert adjusted == [] and out[0][0] == rows[0][0] and out is not rows


# ---------------------------------------------------------------- conjunto final

def test_eixos_e_aberturas_iguais_a_referencia_aprovada(butanta):
    res = _stage1(butanta["estrutura"], butanta["openings"], butanta["ref"])
    approved = butanta["approved"]
    assert len(res["walls"]) == len(approved["walls_cm"]) == 34
    assert res["unassigned"] == []
    matches = _match_approved(res["walls"], approved)
    assert max(d for d, _j, _same in matches) <= 0.6
    assert sorted(j for _d, j, _same in matches) == list(range(34))
    for i, (_d, j, same) in enumerate(matches):
        length_cm = res["walls"][i][0].Length * FT
        mine = sorted((o[0] * FT, o[1] * FT, o[2] * FT, o[3] * FT) for o in res["openings_per_wall"][i])
        theirs = approved["openings_per_wall_cm"][j]
        if not same:
            theirs = [(length_cm - o[1], length_cm - o[0], o[2], o[3]) for o in theirs]
        theirs = sorted(tuple(o) for o in theirs)
        assert len(mine) == len(theirs), (i, j)
        for a, b in zip(mine, theirs):
            assert max(abs(x - y) for x, y in zip(a, b)) <= 0.5, (i, j, a, b)


def test_deterministico_para_a_mesma_entrada(butanta):
    r1 = _stage1(butanta["estrutura"], butanta["openings"], butanta["ref"])
    r2 = _stage1(list(reversed(butanta["estrutura"])), butanta["openings"], butanta["ref"])
    k1 = sorted((tuple(round(v, 3) for v in _axis_cm(w)[0] + _axis_cm(w)[1])) for w in r1["walls"])
    k2 = sorted((tuple(round(v, 3) for v in _axis_cm(w)[0] + _axis_cm(w)[1])) for w in r2["walls"])
    assert k1 == k2
