"""Exercise the real handler and creator with transactional document doubles."""
from types import SimpleNamespace
import pytest
from test_controlled_beta_preflight import m, fixture, piece, CATALOG
import Autodesk.Revit.DB as DB


class Transaction:
    def __init__(self, doc, name):
        self.doc, self.name, self.status = doc, name, "Uninitialized"
        doc.transactions.append(self)

    def Start(self):
        self.before = dict(self.doc.elements)
        self.status = "Started"
        return self.status

    def GetStatus(self):
        return self.status

    def Commit(self):
        if self.doc.fail == self.name:
            return self.RollBack()
        self.status = "Committed"
        return self.status

    def Assimilate(self):
        return self.Commit()

    def RollBack(self):
        if self.doc.fail == "rollback" and self.name.startswith("Beta"):
            raise RuntimeError("rollback simulated failure")
        self.doc.elements = dict(self.before)
        self.status = "RolledBack"
        return self.status


class Document:
    def __init__(self, fail=None):
        self.fail = fail
        self.elements = {99: SimpleNamespace(Id=99)}
        self.transactions = []
        self.next_id = 100
        self.Create = self

    def GetElement(self, eid):
        return self.elements.get(eid)

    def Delete(self, ids):
        if self.fail == "delete":
            raise RuntimeError("delete refused")
        if self.fail != "delete_noop":
            for eid in ids:
                self.elements.pop(eid, None)

    def Regenerate(self):
        pass

    def NewFamilyInstance(self, point, symbol, level, structural_type):
        if self.next_id == 101 and self.fail in ("partial", "rollback"):
            raise RuntimeError("second piece refused")
        instance = SimpleNamespace(Id=self.next_id)
        self.elements[instance.Id] = instance
        self.next_id += 1
        return instance


@pytest.fixture
def setup(monkeypatch):
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
    previous = {"created_count": 1, "created_instances": [{"id": 99}]}
    handler.create_result = previous
    events = []
    handler._save_modulation_state_cache = lambda: events.append("save")
    handler.on_done = lambda *args: events.append(args)
    return handler, previous, events


def test_complete_replacement_commits_before_publishing(setup):
    handler, previous, events = setup
    doc = Document()
    handler._execute_create(doc)
    assert set(doc.elements) == {100, 101}
    assert handler.create_result is not previous
    assert handler.create_result["created_count"] == 2
    assert all(t.GetStatus() == "Committed" for t in doc.transactions)
    assert doc.transactions[0].IsFailureHandlingForcedModal is True
    assert events == ["save", ("create", None)]


@pytest.mark.parametrize("failure", [
    "delete", "delete_noop", "partial", "Remove lote anterior de blocos (recalculo)",
    "Ativa tipos de bloco", "Cria instancias de bloco", "Etapa 5 - Cria blocos estruturais",
    "Beta - substitui lote completo de blocos",
])
def test_failure_restores_previous_batch_without_publishing(setup, failure):
    handler, previous, events = setup
    doc = Document(failure)
    with pytest.raises(RuntimeError):
        handler._execute_create(doc)
    assert set(doc.elements) == {99}
    assert handler.create_result is previous
    assert events == []
    assert handler.beta_transaction_error is None
    assert doc.transactions[0].GetStatus() == "RolledBack"


@pytest.mark.parametrize("damage", ["missing_record", "duplicate_id", "missing_element", "false_count"])
def test_created_result_must_match_every_planned_piece_and_real_instance(setup, damage):
    handler, previous, events = setup
    doc = Document()
    real_create = handler._create_building_blocks

    def altered(*args, **kwargs):
        result = real_create(*args, **kwargs)
        if damage == "missing_record":
            result["created_instances"].pop()
        elif damage == "duplicate_id":
            result["created_instances"][1]["id"] = result["created_instances"][0]["id"]
        elif damage == "missing_element":
            doc.elements.pop(100)
        else:
            result["created_count"] = 0
        return result

    handler._create_building_blocks = altered
    with pytest.raises(RuntimeError, match="BETA BLOQUEADO"):
        handler._execute_create(doc)
    assert set(doc.elements) == {99}
    assert handler.create_result is previous
    assert events == []


def test_unconfirmed_rollback_locks_create_and_finalize(setup):
    handler, previous, events = setup
    doc = Document("rollback")
    with pytest.raises(RuntimeError, match="restauracao do lote nao confirmada"):
        handler._execute_create(doc)
    count = len(doc.transactions)
    for operation in (handler._execute_create, handler._execute_delete):
        with pytest.raises(RuntimeError, match="restauracao do lote nao confirmada"):
            operation(doc)
    assert len(doc.transactions) == count
    assert events == []


def test_empty_wall_may_be_retained_without_invalidating_complete_neighbor(setup):
    handler, previous, events = setup
    handler.walls_to_create.append(handler.walls_to_create[0])
    handler.openings_per_wall.append([])
    handler._apply_solid_color_override = lambda *args, **kwargs: None
    doc = Document()
    handler._execute_create(doc)
    assert handler.create_result["skipped_wall_idxs"] == [1]
    assert set(doc.elements) == {100, 101}


def test_status_return_cannot_override_actual_transaction_state(setup):
    tx = Transaction(Document(), "test")
    tx.Start()
    with pytest.raises(RuntimeError, match="nao confirmou Committed"):
        m._require_beta_transaction_status(tx, "Committed", "Committed")
