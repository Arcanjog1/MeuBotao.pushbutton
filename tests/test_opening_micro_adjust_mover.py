# -*- coding: utf-8 -*-
"""SECAO 85 - movedor transacional do microajuste de abertura (pedido do
usuario, 2026-09-29): "pode deslocar portas e janelas ate' 10 cm da posicao
ORIGINAL ... a busca deve manter a posicao original como referencia para
impedir deslocamentos cumulativos".

Marca no comentario da instancia: `MICROAJUSTE off=+5.00 orig=x,y` (cm). O
teto vale para o TOTAL desde a posicao original; abertura fixada nao anda;
largura/altura/peitoril/hospedeira conferidos depois do Regenerate.

    py -3 -m pytest tests/test_opening_micro_adjust_mover.py -q
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import solver_bench as sb  # noqa: E402

m = sb.m
FT = 30.48


class _Param(object):
    def __init__(self, value=None, read_only=False):
        self.value, self.IsReadOnly = value, read_only

    @property
    def HasValue(self):
        return self.value is not None

    def AsDouble(self):
        return self.value

    def AsString(self):
        return self.value

    def Set(self, value):
        self.value = value
        return True


class _Loc(object):
    def __init__(self, point):
        self.Point = point


class _Host(object):
    def __init__(self, id_):
        self.Id = id_


class _Instance(object):
    def __init__(self, eid, point_cm, comments=None, pinned=False):
        self.Id = eid
        self.Location = _Loc(m.XYZ(point_cm[0] / FT, point_cm[1] / FT, 0.0))
        self.Host = _Host(77)
        self.Pinned = pinned
        self.IsValidObject = True
        self.params = {"Largura_abertura": _Param(141.0 / FT), "Altura_abertura": _Param(121.0 / FT),
                       "Peitoril": _Param(100.0 / FT)}
        self.comments = _Param(comments)

    def LookupParameter(self, name):
        return self.params.get(name)

    def get_Parameter(self, _bip):
        return self.comments


class _Doc(object):
    def __init__(self, instances):
        self.by_id = dict((i.Id, i) for i in instances)

    def GetElement(self, eid):
        return self.by_id.get(eid)

    def Regenerate(self):
        pass


class _MovingETU(object):
    """ElementTransformUtils que MOVE o ponto do duble (o stub padrao so' registra)."""

    def __init__(self, doc):
        self.doc = doc

    def MoveElement(self, document, element_id, vec):
        inst = document.GetElement(element_id)
        p = inst.Location.Point
        inst.Location.Point = m.XYZ(p.X + vec.X, p.Y + vec.Y, p.Z + vec.Z)


def _scene(comments=None, pinned=False):
    walls = [(m.Line.CreateBound(m.XYZ(0.0, 0.0, 0.0), m.XYZ(1000.0 / FT, 0.0, 0.0)), 14.0 / FT, (False, False))]
    openings_per_wall = [[(300.0 / FT, 441.0 / FT, 100.0 / FT, 221.0 / FT)]]
    inst = _Instance(8078993, (370.5, 0.0), comments=comments, pinned=pinned)
    op = {"element_id": "8078993", "element_id_obj": 8078993, "width_ft": 141.0 / FT,
          "center_xy": m.XYZ(370.5 / FT, 0.0, 0.0), "insertion_xy": m.XYZ(370.5 / FT, 0.0, 0.0)}
    return walls, openings_per_wall, [op], _Doc([inst]), inst


def _apply(doc, records, walls, ops_wall, all_ops, moved=None):
    saved = m.ElementTransformUtils
    m.ElementTransformUtils = _MovingETU(doc)
    try:
        return m.apply_opening_micro_adjustments(doc, records, walls, ops_wall, all_ops, moved_so_far_cm=moved)
    finally:
        m.ElementTransformUtils = saved


def test_marca_ida_e_volta():
    assert m.parse_micro_adjust_mark(None) == (None, None)
    assert m.parse_micro_adjust_mark("MICROAJUSTE off=+10.00") == (10.0, None)
    text = m.micro_adjust_mark_text("", 5.0, (804.0, 7.0))
    assert text == "MICROAJUSTE off=+5.00 orig=804.00,7.00"
    assert m.parse_micro_adjust_mark(text) == (5.0, (804.0, 7.0))
    # texto do usuario preservado; a marca antiga e' trocada, nunca duplicada
    kept = m.micro_adjust_mark_text("janela da sala", -3.0, (804.0, 7.0))
    assert kept.startswith("janela da sala | MICROAJUSTE off=-3.00")
    again = m.micro_adjust_mark_text(kept, 2.0, (804.0, 7.0))
    assert again.count("MICROAJUSTE") == 1 and "off=+2.00" in again and again.startswith("janela da sala")


def test_move_ao_longo_da_parede_e_grava_a_posicao_original():
    walls, ops_wall, all_ops, doc, inst = _scene()
    aplicados, falhas = _apply(doc, [{"wall_idx": 0, "opening_index": 0, "chosen_offset_cm": 5.0}],
                               walls, ops_wall, all_ops)
    assert falhas == []
    assert len(aplicados) == 1 and aplicados[0]["offset_cm"] == 5.0
    assert abs(inst.Location.Point.X * FT - 375.5) < 1e-6 and abs(inst.Location.Point.Y) < 1e-9
    assert m.parse_micro_adjust_mark(inst.comments.value) == (5.0, (370.5, 0.0))
    # a geometria em memoria acompanha (vao no eixo e centro do op)
    new_ops = m.shift_openings_in_memory(ops_wall, all_ops, walls, aplicados)
    assert abs(new_ops[0][0][0] * FT - 305.0) < 1e-6 and abs(all_ops[0]["center_xy"].X * FT - 375.5) < 1e-6


def test_teto_vale_para_o_total_desde_a_original():
    # ja' andou +8 (marca com orig): +5 levaria a +13 > 10 -> nada se move
    walls, ops_wall, all_ops, doc, inst = _scene(comments="MICROAJUSTE off=+8.00 orig=362.50,0.00")
    moved = m.opening_moved_so_far_cm(walls, ops_wall, all_ops, {"8078993": inst.comments.value})
    assert moved == {(0, 0): 8.0}
    aplicados, falhas = _apply(doc, [{"wall_idx": 0, "opening_index": 0, "chosen_offset_cm": 5.0}],
                               walls, ops_wall, all_ops, moved)
    assert aplicados == [] and falhas and "teto" in falhas[0]
    assert abs(inst.Location.Point.X * FT - 370.5) < 1e-6
    # voltar para perto da original e' permitido, e a marca continua medindo da original
    aplicados, falhas = _apply(doc, [{"wall_idx": 0, "opening_index": 0, "chosen_offset_cm": -6.0}],
                               walls, ops_wall, all_ops, moved)
    assert falhas == [] and aplicados[0]["total_from_original_cm"] == 2.0
    assert m.parse_micro_adjust_mark(inst.comments.value) == (2.0, (362.5, 0.0))


def test_abertura_fixada_nao_anda():
    walls, ops_wall, all_ops, doc, inst = _scene(pinned=True)
    aplicados, falhas = _apply(doc, [{"wall_idx": 0, "opening_index": 0, "chosen_offset_cm": 5.0}],
                               walls, ops_wall, all_ops)
    assert aplicados == [] and "Pinned" in falhas[0]
    assert abs(inst.Location.Point.X * FT - 370.5) < 1e-6


def test_plano_externo_por_id_e_deslocamento_global():
    """Plano calculado fora (harness): ElementId + deslocamento em XY global - a
    ordem das paredes e o sentido do eixo desta execucao podem ser outros."""
    walls, ops_wall, all_ops, _doc, _inst = _scene()

    class _H(object):
        pass
    h = _H()
    h.walls_to_create, h.openings_per_wall, h.all_openings = walls, ops_wall, all_ops
    fn = m._PostCreationEventHandler._micro_adjust_records_from_plan
    recs = fn(h, [{"element_id": 8078993, "delta_xy_cm": [5.0, 0.0]},
                  {"element_id": 8078993, "delta_xy_cm": [0.0, 5.0]},     # fora do plano da parede
                  {"element_id": 999, "delta_xy_cm": [5.0, 0.0]}])
    assert recs[0]["wall_idx"] == 0 and recs[0]["opening_index"] == 0 and recs[0]["chosen_offset_cm"] == 5.0
    assert recs[1].get("unresolved") and recs[2].get("unresolved")


def test_nao_move_sem_poder_gravar_a_marca():
    """Sem a marca da posicao original o teto deixaria de ser TOTAL: nao move."""
    walls, ops_wall, all_ops, doc, inst = _scene()
    inst.comments.IsReadOnly = True
    aplicados, falhas = _apply(doc, [{"wall_idx": 0, "opening_index": 0, "chosen_offset_cm": 5.0}],
                               walls, ops_wall, all_ops)
    assert aplicados == [] and "marca" in falhas[0]
    assert abs(inst.Location.Point.X * FT - 370.5) < 1e-6


def test_interferencia_com_abertura_de_outra_parede():
    """Abertura de outra parede a 8 cm depois do movimento (minimo 10 cm): nada se move."""
    walls, ops_wall, all_ops, doc, inst = _scene()
    all_ops[0]["hand_xy"] = m.XYZ(1.0, 0.0, 0.0)
    # porta de uma parede perpendicular, 12 cm alem da ponta direita (441 -> 453) antes do movimento
    all_ops.append({"element_id": "999", "element_id_obj": 999, "width_ft": 91.0 / FT,
                    "center_xy": m.XYZ(453.0 / FT, 45.5 / FT, 0.0), "hand_xy": m.XYZ(0.0, 1.0, 0.0)})
    aplicados, falhas = _apply(doc, [{"wall_idx": 0, "opening_index": 0, "chosen_offset_cm": 5.0}],
                               walls, ops_wall, all_ops)
    assert aplicados == [] and "999" in falhas[0], falhas
    # para o outro lado nao ha interferencia
    aplicados, falhas = _apply(doc, [{"wall_idx": 0, "opening_index": 0, "chosen_offset_cm": -5.0}],
                               walls, ops_wall, all_ops)
    assert falhas == [] and aplicados[0]["offset_cm"] == -5.0
