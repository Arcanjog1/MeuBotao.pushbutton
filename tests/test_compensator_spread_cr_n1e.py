# -*- coding: utf-8 -*-
"""CR-N1e - quando o tier 7 ja' decidiu entregar N compensadores acima do
teto, eles saem INTERCALADOS, nunca em sequencia.

E' a parte da "opcao 4" da secao 41.5 que ja' esta' INTEGRALMENTE
PERMITIDA pelas regras atuais: a regra ESCRITA do usuario e' "proibido
usar 2 ou mais EM SEQUENCIA no mesmo trecho";
`MAX_COMPENSATORS_PER_TRECHO = 1` e' a implementacao mais restritiva dela,
listada logo abaixo como consequencia. Quando nao existe alternativa (ver
a enumeracao exaustiva da secao 41.5), entregar os compensadores EM
SEQUENCIA viola a regra escrita sem necessidade nenhuma.

NENHUM TETO MUDA: a composicao entregue e' EXATAMENTE a mesma - mesmos
codigos, mesma contagem, mesmo comprimento total. So' a ORDEM muda.

    python3 -m pytest tests/test_compensator_spread_cr_n1e.py -q
"""

import collections
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import load_script  # noqa: E402
import revit_stubs  # noqa: F401,E402

m = load_script.load()

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from nuvem.benchmark.solver_bridge import catalog_from_input  # noqa: E402


@pytest.fixture(scope="module")
def catalog():
    """Catalogo REAL do corpus (B19/B34/B39/B54/C04/C09) - o catalogo
    sintetico de `test_block_bonding` nao tem C04 e nao exercita o caso."""
    path = os.path.join(_ROOT, "nuvem", "benchmark", "projects",
                        "torre_easy_lo_r00_tp1", "input.json")
    with open(path, "r", encoding="utf-8") as handle:
        entrada = json.load(handle)
    cat, _reconstructed, _dropped = catalog_from_input(entrada)
    return cat


# Trechos entre dois NOS (juntas de contorno 0/0 - o `BLOCK_JOINT_CM` ja'
# entrou no inicio do segmento) que so' fecham acima do teto de
# compensadores. `304.0` e' o `TP1/W003 [170, 474]` da secao 41.
TRECHOS_CM = (304.0, 149.0, 249.0, 199.0, 99.0)


def _layout(catalog, pier_cm):
    return m._pier_ordered_layout(pier_cm, catalog, 0.0, 0.0,
                                  leading_open_override=False,
                                  trailing_open_override=False)


@pytest.mark.parametrize("pier_cm", TRECHOS_CM)
def test_nenhum_compensador_encosta_em_outro(catalog, pier_cm):
    """A regra ESCRITA #2: proibido 2 ou mais EM SEQUENCIA."""
    layout = _layout(catalog, pier_cm)
    assert layout, "esperava um layout para %.1fcm" % pier_cm
    assert m._layout_compensator_run_excess(layout, catalog) == 0, (
        "compensadores em sequencia em %.1fcm: %s"
        % (pier_cm, [c for c, _a, _b in layout]))


@pytest.mark.parametrize("pier_cm", TRECHOS_CM)
def test_a_composicao_entregue_e_exatamente_a_mesma(catalog, pier_cm):
    """NENHUM teto muda: a reordenacao nao pode trocar, tirar nem
    acrescentar peca. Comparado contra o layout que o tier 7 montaria sem
    ela (`_spread_compensators_layout` e' idempotente sobre si mesmo, e
    devolve o proprio layout quando nao ha' o que melhorar)."""
    layout = _layout(catalog, pier_cm)
    reordenado = m._spread_compensators_layout(layout, catalog)
    assert (collections.Counter(c for c, _a, _b in layout) ==
            collections.Counter(c for c, _a, _b in reordenado))


@pytest.mark.parametrize("pier_cm", TRECHOS_CM)
def test_o_trecho_continua_fechando_exatamente(catalog, pier_cm):
    """O comprimento total e o encadeamento peca+junta sao preservados -
    a peca final termina no MESMO ponto."""
    layout = _layout(catalog, pier_cm)
    assert layout[-1][2] == pytest.approx(pier_cm, abs=m.PIER_LAYOUT_TOLERANCE_CM)
    for anterior, seguinte in zip(layout, layout[1:]):
        assert seguinte[1] == pytest.approx(anterior[2] + m.BLOCK_JOINT_CM,
                                            abs=1e-6)
        largura = catalog[seguinte[0]]["length_cm"]
        assert seguinte[2] - seguinte[1] == pytest.approx(largura, abs=1e-6)


def test_o_caso_w003_da_secao_41(catalog):
    """`TP1/W003 [170, 474]`: 3 compensadores continuam sendo o minimo
    aritmetico com `esp<=1` (a enumeracao exaustiva da 41.5 nao mudou) -
    o que muda e' que eles saem SEPARADOS."""
    layout = _layout(catalog, 304.0)
    codigos = [c for c, _a, _b in layout]
    comps = [c for c in codigos if catalog[c].get("is_compensator")]
    assert len(comps) == 3, (
        "a aritmetica do trecho nao mudou - continuam 3 compensadores: %s"
        % codigos)
    assert m._layout_compensator_run_excess(layout, catalog) == 0
    especiais = [c for c in codigos if catalog[c].get("is_special_bond")]
    assert len(especiais) <= m.MAX_SPECIAL_BOND_PER_TRECHO, (
        "o teto de peca especial continua respeitado: %s" % codigos)


def test_layout_ja_bom_nao_e_alterado(catalog):
    """Idempotencia: um layout sem compensador encostado volta IDENTICO
    (mesmo objeto), sem recalcular posicao nenhuma."""
    layout = _layout(catalog, 199.0)
    assert m._layout_compensator_run_excess(layout, catalog) == 0
    assert m._spread_compensators_layout(layout, catalog) is layout


def test_reordenacao_nunca_piora_o_excesso(catalog):
    """Guarda: `_spread_compensators_layout` devolve o ORIGINAL sempre que
    a alternativa nao for estritamente melhor."""
    for pier_cm in TRECHOS_CM:
        layout = _layout(catalog, pier_cm)
        antes = m._layout_compensator_run_excess(layout, catalog)
        depois = m._layout_compensator_run_excess(
            m._spread_compensators_layout(layout, catalog), catalog)
        assert depois <= antes


def test_meio_bloco_de_ponta_nao_e_movido(catalog):
    """O B19 so' e' legitimo onde o layout o colocou (regra do meio-bloco:
    so' encosta em ponta ABERTA) - a reordenacao nunca o tira da ponta."""
    layout = [("B19", 0.0, 19.0), ("C09", 20.0, 29.0), ("C04", 30.0, 34.0),
              ("B39", 35.0, 74.0), ("B39", 75.0, 114.0)]
    reordenado = m._spread_compensators_layout(layout, catalog)
    assert reordenado[0][0] == "B19", (
        "o B19 saiu da ponta: %s" % [c for c, _a, _b in reordenado])
    assert m._layout_compensator_run_excess(reordenado, catalog) < \
        m._layout_compensator_run_excess(layout, catalog)


def test_relayout_recusa_composicao_que_mudaria_o_trecho(catalog):
    """`_relayout_codes_in_place` devolve None em vez de entregar um
    trecho de comprimento diferente - guarda dura contra qualquer
    reordenacao que trocasse uma peca por outra."""
    layout = [("B39", 0.0, 39.0), ("C09", 40.0, 49.0), ("C09", 50.0, 59.0)]
    assert m._relayout_codes_in_place(["B39", "C09", "C09"], layout, catalog) is not None
    assert m._relayout_codes_in_place(["B39", "B39", "C09"], layout, catalog) is None
