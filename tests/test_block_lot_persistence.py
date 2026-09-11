# -*- coding: utf-8 -*-
"""Lote PERSISTENTE de blocos (secao 50 de REGRAS_MODULACAO_BLOCOS.md).

Travamento real medido no teste do botao (CPython, 2026-09-11): o lote de
7.257 blocos criado numa sessao anterior nao foi apagado - o handler so'
conhecia o lote anterior por memoria (create_result["created_instances"]) -
e 8.399 blocos novos foram criados por cima: 13.940 avisos "instancias
identicas no mesmo local" e a caixa modal do Revit travou a UI em
"regenerando o modelo". Agora cada instancia criada recebe um carimbo com o
UniqueId da Wall dona e a etiqueta do lote (parametro Comentarios), e uma
sessao nova descobre e substitui o lote anterior das MESMAS paredes. Sem
carimbo nada e' apagado.
"""
from types import SimpleNamespace

import pytest

from test_beta_atomic_creation import Document, Transaction, m, fixture, piece, CATALOG  # noqa: F401
import Autodesk.Revit.DB as DB
import revit_stubs


def test_carimbo_ida_e_volta():
    stamp = m._block_lot_stamp("uid-abc", "20260911-1")
    assert stamp.startswith(m.BLOCK_LOT_MARKER + "|")
    assert m._parse_block_lot_stamp(stamp) == ("uid-abc", "20260911-1")
    assert m._parse_block_lot_stamp("texto do usuario") is None
    assert m._parse_block_lot_stamp("") is None and m._parse_block_lot_stamp(None) is None


def test_create_building_blocks_carimba_cada_instancia_com_a_parede_dona():
    doc = revit_stubs._StubDoc()
    result, walls, _openings = fixture([piece(40), piece(100)], opening=None)
    catalog = {key: dict(value, symbol=SimpleNamespace(IsActive=True)) for key, value in CATALOG.items()}
    out = m.create_building_blocks(doc, result["candidates"], catalog, 0.0, SimpleNamespace(), 2,
                                   course_candidates=result.get("course_candidates"),
                                   owner_uid_by_wall_idx={0: "UID-W0"}, lot_tag="LOTE-1")
    assert out["created_count"] > 0
    assert all(item["stamped"] for item in out["created_instances"]), out["created_instances"][:3]
    for _point, _symbol, _rest, instance in doc.Create.family_instances:
        comments = instance.params.get("BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS")
        assert m._parse_block_lot_stamp(comments) == ("UID-W0", "LOTE-1"), comments
    assert out["perf"].get("stamp_failures", 0) == 0


def test_sem_mapa_de_donos_nao_carimba_nem_falha():
    doc = revit_stubs._StubDoc()
    result, walls, _openings = fixture([piece(40), piece(100)], opening=None)
    catalog = {key: dict(value, symbol=SimpleNamespace(IsActive=True)) for key, value in CATALOG.items()}
    out = m.create_building_blocks(doc, result["candidates"], catalog, 0.0, SimpleNamespace(), 2,
                                   course_candidates=result.get("course_candidates"))
    assert out["created_count"] > 0
    assert not any(item["stamped"] for item in out["created_instances"])


class _Doc(Document):
    """Documento transacional do teste atomico + Walls com UniqueId e um
    'colecionador' de instancias carimbadas (o que a descoberta real le via
    FilteredElementCollector + Comentarios)."""

    def __init__(self):
        Document.__init__(self)
        self.elements = {}
        self.elements[501] = SimpleNamespace(Id=501, UniqueId="UID-501")
        self.stamps = {}     # element id -> texto do carimbo

    def NewFamilyInstance(self, point, symbol, level, structural_type):
        instance = SimpleNamespace(Id=self.next_id)
        holder = self

        class _Param(object):
            IsReadOnly = False

            def Set(self_inner, value):
                holder.stamps[instance.Id] = value
                return True

        instance.get_Parameter = lambda bip: _Param()
        self.elements[instance.Id] = instance
        self.next_id += 1
        return instance

    def Delete(self, ids):
        for eid in ids:
            self.elements.pop(eid, None)
            self.stamps.pop(eid, None)

    def discover(self, owner_uids):
        out = []
        for eid, text in sorted(self.stamps.items()):
            parsed = m._parse_block_lot_stamp(text)
            if parsed and parsed[0] in owner_uids and eid in self.elements:
                out.append({"id": eid, "wall_uid": parsed[0], "lot_tag": parsed[1]})
        return out


def _new_session_handler(monkeypatch, doc):
    status = SimpleNamespace(**{s: s for s in ("Started", "Committed", "RolledBack", "Uninitialized")})
    monkeypatch.setattr(DB, "TransactionStatus", status, raising=False)
    monkeypatch.setattr(m, "Transaction", Transaction)
    monkeypatch.setattr(m, "TransactionGroup", Transaction)
    handler = m._PostCreationEventHandler()
    handler.controlled_beta = True
    result, walls, openings = fixture([piece(40), piece(100)], opening=None)
    handler.solve_result, handler.walls_to_create = result, walls
    handler.openings_per_wall = openings
    handler.catalog = {key: dict(value, symbol=SimpleNamespace(IsActive=True)) for key, value in CATALOG.items()}
    handler.created_walls_by_axis = {0: [(501, "existing")]}
    handler.create_result = None          # sessao NOVA: nenhuma memoria do lote anterior
    handler._discover_previous_lot = lambda app_doc, owners: doc.discover(owners)
    result["beta_input_signature"] = handler._beta_input_signature()
    handler._save_modulation_state_cache = lambda: None
    handler.on_done = lambda *args: None
    return handler


def _blocks(doc):
    return sorted(eid for eid in doc.elements if eid != 501)


def test_sessao_nova_substitui_o_lote_anterior_das_mesmas_paredes(monkeypatch):
    doc = _Doc()
    first = _new_session_handler(monkeypatch, doc)
    first._execute_create(doc)
    lote1 = _blocks(doc)
    assert lote1 and first.create_result["created_count"] == len(lote1)
    assert all(m._parse_block_lot_stamp(doc.stamps[eid])[0] == "UID-501" for eid in lote1)

    second = _new_session_handler(monkeypatch, doc)   # outra sessao, sem memoria
    second._execute_create(doc)
    lote2 = _blocks(doc)
    assert len(lote2) == len(lote1), (len(lote1), len(lote2))     # N, nunca 2N
    assert not set(lote1) & set(lote2), "o lote anterior tinha de ser apagado"
    assert second.create_result["created_count"] == len(lote2)


def test_blocos_sem_carimbo_ou_de_outra_parede_ficam_intocados(monkeypatch):
    doc = _Doc()
    doc.elements[900] = SimpleNamespace(Id=900)                       # bloco a mao (sem carimbo)
    doc.elements[901] = SimpleNamespace(Id=901)
    doc.stamps[901] = m._block_lot_stamp("UID-OUTRA-PAREDE", "X")     # lote de outra parede
    handler = _new_session_handler(monkeypatch, doc)
    handler._execute_create(doc)
    assert 900 in doc.elements and 901 in doc.elements
