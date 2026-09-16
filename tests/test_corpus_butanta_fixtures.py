# -*- coding: utf-8 -*-
"""Fixtures minimas do corpus BUTANTA - validade estrutural e fisica.

Este arquivo NAO prova modulacao e NAO congela gabarito: enquanto o PR #42
estiver mudando a fisica, gravar um `expected` a partir da saida corrente
transformaria um estado em movimento em "verdade" (e codigo novo contaria
como regressao critica em `golden/compare.py::_critical_regressions`).

O que ele garante, e que hoje nao existe:

1. cada fixture carrega e respeita o `schema_version` 2 do benchmark;
2. a geometria e' internamente coerente (comprimento bate com os
   extremos, vao dentro da parede, peitoril abaixo da verga, verga dentro
   da altura);
3. nenhuma fixture carrega identidade de projeto - nada de ElementId,
   `W0xx`, `source_element_id` preenchido ou coordenada do BUTANTA;
4. todo caso declara o PRINCIPIO que representa e a asercao que vai valer
   quando houver gabarito autorizado;
5. o gerador e' deterministico - rodar de novo nao muda byte nenhum;
6. as fixtures NAO entram em `runner.list_projects()`, ou seja, nao mexem
   no portao de corpus enquanto o #42 esta' em voo.

    python3 -m pytest tests/test_corpus_butanta_fixtures.py -q
"""

import json
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

CORPUS = os.path.join(_ROOT, "nuvem", "benchmark", "corpus_butanta")
FIXTURES = os.path.join(CORPUS, "fixtures")

# Os oito grupos pedidos pela missao. Um grupo vazio e' falha: a estrutura
# so' serve se cada area coberta pelas correcoes fisicas tiver caso.
GROUPS = ("b34_alignment", "channel_window", "channel_door", "t_with_b54",
          "special_clusters", "under_window", "opening_adjustment", "support")

WALL_ID = re.compile(r"^[A-Z]$")


def _cases():
    found = []
    for group in sorted(os.listdir(FIXTURES)):
        group_dir = os.path.join(FIXTURES, group)
        if not os.path.isdir(group_dir):
            continue
        for name in sorted(os.listdir(group_dir)):
            case = os.path.join(group_dir, name)
            if os.path.isfile(os.path.join(case, "input.json")):
                found.append((group, name, case))
    return found


CASES = _cases()
IDS = ["{0}/{1}".format(g, n) for g, n, _ in CASES]


def _load(case_dir, name):
    with open(os.path.join(case_dir, name), encoding="utf-8") as handle:
        return json.load(handle)


def test_os_oito_grupos_existem():
    presentes = set(group for group, _name, _dir in CASES)
    assert presentes == set(GROUPS), sorted(presentes ^ set(GROUPS))


def test_ha_pelo_menos_um_caso_por_grupo():
    assert CASES, "nenhuma fixture encontrada - rode build_fixtures.py"


@pytest.mark.parametrize("group,name,case_dir", CASES, ids=IDS)
def test_schema_e_settings_do_benchmark(group, name, case_dir):
    data = _load(case_dir, "input.json")
    assert data["schema_version"] == 2
    assert data["source"] == "input"
    settings = data["settings"]
    # a grade fisica: passo 20cm, bloco 19cm - a junta de 1cm e' a diferenca
    assert settings["course_step_cm"] - settings["block_height_cm"] == 1.0
    assert settings["num_courses"] >= 2
    assert settings["expected_rows"] == settings["num_courses"]
    assert data["walls"], "fixture sem parede"


@pytest.mark.parametrize("group,name,case_dir", CASES, ids=IDS)
def test_geometria_internamente_coerente(group, name, case_dir):
    data = _load(case_dir, "input.json")
    for wall in data["walls"]:
        (x0, y0), (x1, y1) = wall["start_cm"], wall["end_cm"]
        medido = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        assert abs(medido - wall["length_cm"]) < 1e-6, (wall["id"], medido)
        assert wall["length_cm"] > 0
        assert wall["height_cm"] > 0
        assert wall["thickness_cm"] == data["settings"]["wall_thickness_cm"]
        for opening in wall["openings"]:
            assert 0.0 < opening["t_start_cm"] < opening["t_end_cm"] < wall["length_cm"], (
                "vao fora da parede", wall["id"], opening["id"])
            assert opening["sill_cm"] < opening["head_cm"], opening["id"]
            assert opening["head_cm"] <= wall["height_cm"], (
                "verga acima do topo da parede", opening["id"])
            assert opening["width_cm"] == opening["t_end_cm"] - opening["t_start_cm"]
            assert opening["height_cm"] == opening["head_cm"] - opening["sill_cm"]
            if opening["kind"] == "door":
                assert opening["sill_cm"] == 0.0, "porta nao tem peitoril"
            else:
                assert opening["sill_cm"] > 0.0, "janela precisa de peitoril"


@pytest.mark.parametrize("group,name,case_dir", CASES, ids=IDS)
def test_vaos_da_mesma_parede_nao_se_sobrepoem(group, name, case_dir):
    data = _load(case_dir, "input.json")
    for wall in data["walls"]:
        spans = sorted((o["t_start_cm"], o["t_end_cm"]) for o in wall["openings"])
        for (_lo_a, hi_a), (lo_b, _hi_b) in zip(spans, spans[1:]):
            assert hi_a < lo_b, (wall["id"], "vaos sobrepostos")


@pytest.mark.parametrize("group,name,case_dir", CASES, ids=IDS)
def test_nenhuma_identidade_de_projeto(group, name, case_dir):
    """NAO OVERFIT: a fixture representa um principio, nunca uma peca do
    BUTANTA. Se um ElementId ou um `W0xx` entrar aqui, o caso deixa de
    valer para outro projeto e vira decoracao."""
    bruto = open(os.path.join(case_dir, "input.json"), encoding="utf-8").read()
    assert not re.search(r"\bW\d{3}\b", bruto), "nome de parede de corpus (W0xx)"
    assert not re.search(r"\b\d{7}\b", bruto), "parece ElementId do Revit"
    data = _load(case_dir, "input.json")
    for wall in data["walls"]:
        assert WALL_ID.match(wall["id"]), ("id de parede deve ser local", wall["id"])
        assert wall["source_element_ids"] == []
        for opening in wall["openings"]:
            assert opening["source_element_id"] is None
            assert opening["confidence"] == "synthetic"


@pytest.mark.parametrize("group,name,case_dir", CASES, ids=IDS)
def test_e_pequena_de_verdade(group, name, case_dir):
    """Fixture minima: o valor esta' em caber num portao rapido. Se crescer
    para dezenas de paredes, virou corpus - e corpus tem outro lugar."""
    data = _load(case_dir, "input.json")
    assert len(data["walls"]) <= 3, "fixture deixou de ser minima"
    assert sum(len(w["openings"]) for w in data["walls"]) <= 2


@pytest.mark.parametrize("group,name,case_dir", CASES, ids=IDS)
def test_expected_declarado_como_pendente_e_nao_como_gabarito(group, name, case_dir):
    """O ponto da missao: estrutura sim, verdade congelada nao. Se algum dia
    alguem gravar um expected aqui sem autorizacao de baseline, este teste
    quebra e diz por que."""
    pendente = os.path.join(case_dir, "expected.PENDING.json")
    assert os.path.isfile(pendente), "todo caso declara a asercao futura"
    data = _load(case_dir, "expected.PENDING.json")
    assert data["status"] == "PENDING_REFERENCE"
    assert data["confidence"] == "NONE"
    assert data["reference_kind"] is None
    for campo in ("principle", "assertion_when_frozen", "why_pending",
                  "authorization_required"):
        assert data[campo].strip(), campo
    assert not os.path.isfile(os.path.join(case_dir, "expected.json")), (
        "expected definitivo gravado sem autorizacao de baseline")
    assert not os.path.isfile(os.path.join(case_dir, "baseline.json")), (
        "baseline gravado sem autorizacao")


def test_gerador_e_deterministico():
    """Rodar o construtor de novo nao pode mudar byte nenhum - sem isso a
    fixture vira ruido de diff a cada execucao."""
    sys.path.insert(0, CORPUS)
    try:
        import build_fixtures
    finally:
        sys.path.remove(CORPUS)
    antes = {}
    for _group, _name, case_dir in CASES:
        caminho = os.path.join(case_dir, "input.json")
        antes[caminho] = open(caminho, "rb").read()
    build_fixtures.write()
    for caminho, conteudo in antes.items():
        assert open(caminho, "rb").read() == conteudo, caminho


def test_fixtures_nao_entram_no_portao_de_corpus():
    """Enquanto o #42 esta' em voo, nenhuma fixture pode aparecer em
    `runner.list_projects()`: isso mudaria as parametrizacoes de
    `tests/regression/test_benchmark_baselines.py` sem ninguem pedir."""
    sys.path.insert(0, os.path.join(_ROOT, "nuvem"))
    try:
        from benchmark import runner
    finally:
        sys.path.remove(os.path.join(_ROOT, "nuvem"))
    projetos = set(runner.list_projects())
    assert projetos == {"piloto_sintetico_2x2", "torre_easy_lo_r00_tgd",
                        "torre_easy_lo_r00_tp1"}, sorted(projetos)
    for _group, name, _dir in CASES:
        assert name not in projetos
