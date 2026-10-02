# -*- coding: utf-8 -*-
"""SECAO 86.3 de REGRAS_MODULACAO_BLOCOS.md - FAIXA DE B34 EQUILIBRADA entre as
duas ancoras de uma corrida no'-a-no' (aproximacao do projeto humano BUTANTA
R08_LT, 2026-10-01).

PADRAO OBSERVADO no humano (1o pav., human_rows normalizado): numa corrida entre
duas ancoras (ponta que passa P, ponta que para S, B54 N, vao do T G) os B34 de
ajuste do preenchimento formam faixas coladas nas DUAS ancoras com |kE - kD| <= 1
e os B39 no miolo - P..P com 5 B34 = 2+3 em 44/44 fiadas, S..S com 3 = 1+2 em
42/42. O guloso/busca exata do motor punha os B39 primeiro e todos os B34 no fim
(nosso 1+4 / 0+3). A largura k e' a mesma nas duas fiadas: na que passa ha' k+1
B34 contando a peca de canto, na que para ha' k.

As fixtures sao as fileiras HUMANAS reais das paredes W14/W21 (494 cm entre dois
T) e W22 (444 cm, misto), extraidas do human_rows normalizado (peca real, nao a
caixa da familia). A geometria das mini-plantas vem do corpus versionado
`reference_projects/butanta_r08_lt/s74_corpus/` (so' as paredes envolvidas, sem
aberturas) e passa pelo solve REAL (`solve_building_blocks_all_courses`,
estrategia None, a mesma do botao).

    py -3 -m pytest tests/test_b34_balanced_strip.py -q
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "audit"))

import s74_corpus as S  # noqa: E402

m, ws = S.engine()
FT = 30.48
GEO = S.geometry()
CATALOG = S.catalog(GEO)

# Fileiras humanas (BUTANTA R08_LT, 1o pav., human_rows_unpad.json): (codigo com
# o lado do vazado menor, inicio, fim) em cm ao longo do eixo da parede. Fiada 0
# e 1 bastam (as demais repetem a cada duas fiadas).
HUMAN = {
    14: {
        "S-S": [("B34>", 15.0, 49.0)] + [("B39", 50.0 + 40 * i, 89.0 + 40 * i) for i in range(9)]
               + [("B34<", 410.0, 444.0), ("B34<", 445.0, 479.0)],
        "P-P": [("B34<", 0.0, 34.0), ("B34<", 35.5, 69.5)]
               + [("B39", 70.5 + 40 * i, 109.5 + 40 * i) for i in range(8)]
               + [("B34>", 390.0, 424.0), ("B34>", 425.0, 459.0), ("B34>", 460.0, 494.0)],
    },
    21: {
        "P-P": [("B34<", 0.0, 34.0), ("B34<", 35.0, 69.0)]
               + [("B39", 70.0 + 40 * i, 109.0 + 40 * i) for i in range(8)]
               + [("B34>", 390.0, 424.0), ("B34>", 425.0, 459.0), ("B34>", 460.0, 494.0)],
        "S-S": [("B34>", 15.0, 49.0)] + [("B39", 50.0 + 40 * i, 89.0 + 40 * i) for i in range(9)]
               + [("B34<", 410.0, 444.0), ("B34<", 445.0, 479.0)],
    },
    22: {
        "P-S": [("B34<", 0.0, 34.0), ("B34<", 35.0, 69.0)]
               + [("B39", 70.0 + 40 * i, 109.0 + 40 * i) for i in range(9)],
        "S-P": [("B34>", 15.0, 49.0)] + [("B39", 50.0 + 40 * i, 89.0 + 40 * i) for i in range(9)]
               + [("B34>", 410.0, 444.0)],
    },
}
# W9: corrida da ponta em L (t=0) ate' o T de meio de parede em t=487 (a W1 chega ali):
# ancoras P/S na ponta e N (B54) / G (vao do T) no meio - so' as pecas ate' o no'.
HUMAN_W9_TO_T = {
    "P-N": [("B34<", 0.0, 34.0), ("B34<", 35.0, 69.0)]
           + [("B39", 70.0 + 40 * i, 109.0 + 40 * i) for i in range(8)]
           + [("B34>", 390.0, 424.0), ("B34>", 425.0, 459.0), ("B54", 460.0, 514.0)],
    "S-G": [("B34>", 15.0, 49.0)] + [("B39", 50.0 + 40 * i, 89.0 + 40 * i) for i in range(9)]
           + [("B34<", 410.0, 444.0), ("B34<", 445.0, 479.0)],
}
# mini-planta de cada parede: (principais que ela encontra..., a propria parede por ULTIMO)
MINI = {14: (2, 3, 14), 21: (1, 4, 21), 22: (12, 0, 22), 9: (4, 1, 9)}


def _codes(layout):
    return [c for c, _a, _b in layout]


def _fill_of(row, length_cm):
    """(inicio, fim, pecas) do PREENCHIMENTO de uma fileira humana: tira a peca de
    canto das pontas que passam (P) - ela e' do no', nao do trecho. Inicio/fim
    NOMINAIS do trecho do motor: depois da peca de canto + junta (P: 34 + 1) ou da
    face da parede que cruza + junta (S: 14 + 1)."""
    pieces = list(row)
    lo, hi = 15.0, length_cm - 15.0
    if pieces and pieces[0][1] <= 1.0:
        pieces = pieces[1:]
        lo = CATALOG["B34"]["length_cm"] + 1.0
    if pieces and pieces[-1][2] >= length_cm - 1.0:
        pieces = pieces[:-1]
        hi = length_cm - CATALOG["B34"]["length_cm"] - 1.0
    return lo, hi, pieces


# ------------------------------------------------------------------ divisao K
def test_divisao_equilibrada_com_impar_no_fim_do_eixo_por_padrao():
    assert ws.BALANCED_B34_STRIP_ENABLED is True
    assert ws.BALANCED_B34_STRIP_ODD_AT_AXIS_END is True
    tabela = {0: (0, 0), 1: (0, 1), 2: (1, 1), 3: (1, 2), 4: (2, 2), 5: (2, 3), 6: (3, 3)}
    for k, esperado in tabela.items():
        assert ws._balanced_b34_strip_counts(k) == esperado
        ini, fim = ws._balanced_b34_strip_counts(k, odd_at_axis_end=False)
        assert (fim, ini) == esperado
        assert abs(ini - fim) <= 1 and ini + fim == k


# ------------------------------------------------ reordenacao da composicao
@pytest.mark.parametrize("wall,case,odd_end", [
    (21, "P-P", True), (21, "S-S", True), (14, "P-P", True), (14, "S-S", True),
    (22, "P-S", False), (22, "S-P", False)])
def test_composicao_gerada_bate_com_a_fileira_humana(wall, case, odd_end):
    """O trecho entre as duas ancoras (mesmo comprimento do humano) sai do
    `_pier_ordered_layout` com a composicao certa (contagem de B34/B39 igual a
    do humano) e a faixa equilibrada poe cada peca na posicao humana (+-1 cm; a
    W14 humana tem folga de 0,5 cm numa fiada)."""
    length_cm = GEO["walls"][wall]["length_cm"]
    lo, hi, human_fill = _fill_of(HUMAN[wall][case], length_cm)
    base = m._pier_ordered_layout(hi - lo, CATALOG, 0.0, 0.0,
                                  leading_open_override=False, trailing_open_override=False)
    assert sorted(_codes(base)) == sorted(p[0][:3] for p in human_fill)
    novo = ws._balanced_b34_strip_layout(base, CATALOG, odd_at_axis_end=odd_end)
    assert novo is not None
    assert _codes(novo) == [p[0][:3] for p in human_fill]
    for (code, a, b), (hcode, ha, hb) in zip(novo, human_fill):
        assert abs(lo + a - ha) <= 1.0 and abs(lo + b - hb) <= 1.0, (code, lo + a, hcode, ha)
    # mesma composicao, mesmas pontas
    assert sorted(_codes(novo)) == sorted(_codes(base))
    assert abs(novo[0][1] - base[0][1]) < 1e-9 and abs(novo[-1][2] - base[-1][2]) < 1e-6


def test_o_guloso_sozinho_empilhava_os_b34_numa_ponta():
    """Linha de base (o defeito medido): sem a 86.3 a busca exata devolve os B39
    primeiro e os 3 B34 de ajuste juntos no fim - o 0+3 / 1+4 do relatorio."""
    base = m._pier_ordered_layout(424.0, CATALOG, 0.0, 0.0,
                                  leading_open_override=False, trailing_open_override=False)
    assert _codes(base) == ["B39"] * 8 + ["B34"] * 3


def test_so_reordena_composicao_pura_de_b39_e_b34():
    def lay(codes):
        out, pos = [], 0.0
        for c in codes:
            out.append((c, pos, pos + CATALOG[c]["length_cm"]))
            pos += CATALOG[c]["length_cm"] + 1.0
        return out
    assert ws._balanced_b34_strip_layout(lay(["B39", "B39", "C09", "B34"]), CATALOG) is None
    assert ws._balanced_b34_strip_layout(lay(["B19", "B39", "B34", "B34"]), CATALOG) is None
    assert ws._balanced_b34_strip_layout(lay(["B39", "B39", "B39"]), CATALOG) is None
    assert ws._balanced_b34_strip_layout([], CATALOG) is None
    torto = lay(["B39", "B34", "B34"])
    torto[1] = ("B34", torto[1][1] + 0.5, torto[1][2] + 0.5)
    assert ws._balanced_b34_strip_layout(torto, CATALOG) is None
    assert _codes(ws._balanced_b34_strip_layout(lay(["B39", "B39", "B34", "B34"]), CATALOG)) == \
        ["B34", "B39", "B39", "B34"]


# ------------------------------------------------------ guardas do trecho
def _base_424():
    return m._pier_ordered_layout(424.0, CATALOG, 0.0, 0.0,
                                  leading_open_override=False, trailing_open_override=False)


def test_trecho_com_ponta_aberta_abertura_ou_sem_no_nao_muda():
    base = _base_424()
    args = (CATALOG, 35.0, 459.0)
    assert ws._balanced_b34_strip_segment_layout(
        base, *args, kind_left="WALL_START", kind_right="WALL_END", leading_is_open=True,
        trailing_is_open=False, opening_intervals_cm=[], avoid_joint_positions_cm=[]) is base
    assert ws._balanced_b34_strip_segment_layout(
        base, *args, kind_left="OPENING_HI", kind_right="WALL_END", leading_is_open=False,
        trailing_is_open=False, opening_intervals_cm=[], avoid_joint_positions_cm=[]) is base
    assert ws._balanced_b34_strip_segment_layout(
        base, *args, kind_left="WALL_START", kind_right="WALL_END", leading_is_open=False,
        trailing_is_open=False, opening_intervals_cm=[(200.0, 290.0)], avoid_joint_positions_cm=[]) is base
    # abertura FORA do trecho (depois do no') nao impede
    fora = ws._balanced_b34_strip_segment_layout(
        base, *args, kind_left="WALL_START", kind_right="MIDSPAN_LO", leading_is_open=False,
        trailing_is_open=False, opening_intervals_cm=[(480.0, 560.0)], avoid_joint_positions_cm=[])
    assert _codes(fora) == ["B34"] + ["B39"] * 8 + ["B34", "B34"]


def test_flag_desligada_devolve_o_layout_intocado(monkeypatch):
    base = _base_424()
    monkeypatch.setattr(ws, "BALANCED_B34_STRIP_ENABLED", False)
    assert ws._balanced_b34_strip_segment_layout(
        base, CATALOG, 35.0, 459.0, "WALL_START", "WALL_END", False, False, [], []) is base


def test_regra_1_nunca_cede_a_faixa_nao_cria_junta_coincidente():
    """Se a faixa equilibrada empilhasse junta sobre a fiada oposta (lista
    `avoid`), o trecho fica com o layout do caminho normal."""
    base = _base_424()
    novo = ws._balanced_b34_strip_layout(base, CATALOG)
    juntas_novas = ws._layout_internal_joint_positions_cm(novo, 35.0)
    saida = ws._balanced_b34_strip_segment_layout(
        base, CATALOG, 35.0, 459.0, "WALL_START", "WALL_END", False, False, [], juntas_novas)
    assert saida is base
    # contra as juntas REAIS da fiada oposta (S-S equilibrada) a troca passa
    oposta = ws._balanced_b34_strip_layout(
        m._pier_ordered_layout(464.0, CATALOG, 0.0, 0.0, leading_open_override=False,
                               trailing_open_override=False), CATALOG)
    avoid = ws._layout_internal_joint_positions_cm(oposta, 15.0) + [14.5, 479.5]
    saida = ws._balanced_b34_strip_segment_layout(
        base, CATALOG, 35.0, 459.0, "WALL_START", "WALL_END", False, False, [], avoid)
    assert _codes(saida) == ["B34"] + ["B39"] * 8 + ["B34", "B34"]
    assert ws._count_joint_coincidences_cm(ws._layout_internal_joint_positions_cm(saida, 35.0), avoid) == 0


# ------------------------------------------- solve REAL nas mini-plantas
def _window_on_w21():
    """Janela sintetica (peitoril 100, verga 220, 120 cm) no meio da W21."""
    w = GEO["walls"][21]
    cx = (w["p0_cm"][0] + w["p1_cm"][0]) / 2.0
    cy = (w["p0_cm"][1] + w["p1_cm"][1]) / 2.0
    return {"key": 99000001, "center_cm": [cx, cy], "insertion_cm": [cx, cy], "hand": [1.0, 0.0],
            "width_cm": 120.0, "sill_cm": 100.0, "head_cm": 220.0}


def _mini_rows(wall, odd_at_end=True, enabled=True, openings=()):
    idx = MINI[wall]
    sub = dict(GEO, walls=[GEO["walls"][i] for i in idx], openings=list(openings))
    antes = (ws.BALANCED_B34_STRIP_ENABLED, ws.BALANCED_B34_STRIP_ODD_AT_AXIS_END)
    # 2 fiadas de BLOCO: a cinta de topo (86.7) trocaria a ultima por canaleta - aqui
    # so' interessa a faixa de B34 das fiadas de bloco
    cinta_antes = getattr(m, "TOP_BOND_BEAM_ENABLED", None)
    ws.BALANCED_B34_STRIP_ENABLED = enabled
    ws.BALANCED_B34_STRIP_ODD_AT_AXIS_END = odd_at_end
    if cinta_antes is not None:
        m.TOP_BOND_BEAM_ENABLED = False
    try:
        ctx = S.build_context(sub)
        res = S.solve(ctx, True, geo=sub, courses=2, strategy=None)
    finally:
        ws.BALANCED_B34_STRIP_ENABLED, ws.BALANCED_B34_STRIP_ODD_AT_AXIS_END = antes
        if cinta_antes is not None:
            m.TOP_BOND_BEAM_ENABLED = cinta_antes
    wi = len(idx) - 1
    line = ctx["walls"][wi][0]
    p0, p1 = line.GetEndPoint(0), line.GetEndPoint(1)
    x0, y0 = p0.X * FT, p0.Y * FT
    length = ((p1.X - p0.X) ** 2 + (p1.Y - p0.Y) ** 2) ** 0.5 * FT
    dx, dy = (p1.X * FT - x0) / length, (p1.Y * FT - y0) / length
    rows = {}
    for ci in sorted(res["course_candidates"]):
        items = []
        for c in res["course_candidates"][ci]:
            if c.get("wall_idx") != wi:
                continue
            o = c["origin_world"]
            t = (o.X * FT - x0) * dx + (o.Y * FT - y0) * dy
            half = c["length_cm"] / 2.0
            code = c["logical_code"]
            if code == "B34":
                small = min(c["cells_world"], key=lambda cell: cell["size_local"][0] * cell["size_local"][1])
                ts = (small["point"].X * FT - x0) * dx + (small["point"].Y * FT - y0) * dy
                code += "<" if ts < t else ">"
            items.append((code, round(t - half, 2), round(t + half, 2)))
        rows[ci] = sorted(items, key=lambda it: it[1])
    res["_ctx_openings"] = ctx["openings_per_wall"][wi]
    return rows, res, length


def _pattern(row, length_cm):
    ini = "P" if row[0][1] <= 1.0 else "S"
    fim = "P" if row[-1][2] >= length_cm - 1.0 else "S"
    return ini + "-" + fim


def _assert_same_rows(rows, human, length_cm):
    vistos = set()
    for ci, row in rows.items():
        case = _pattern(row, length_cm)
        assert case in human, (ci, case, row)
        hum = human[case]
        assert [c for c, _a, _b in row] == [c for c, _a, _b in hum], (case, row)
        for (c, a, b), (_hc, ha, hb) in zip(row, hum):
            assert abs(a - ha) <= 1.0 and abs(b - hb) <= 1.0, (case, c, a, ha)
        vistos.add(case)
    assert vistos == set(human)


@pytest.mark.parametrize("wall", [14, 21])
def test_paredes_de_494_entre_dois_T_saem_iguais_ao_humano(wall):
    """W14/W21: solve real da mini-planta (as duas principais + a parede), as
    duas fiadas iguais as humanas - codigos, posicoes (+-1 cm) e o lado do vazado
    menor de cada B34 (P para a ponta, S para dentro)."""
    rows, res, length = _mini_rows(wall)
    assert not res.get("non_modular") and not res.get("collisions")
    _assert_same_rows(rows, HUMAN[wall], length)


def test_parede_de_444_mista_sai_igual_ao_humano_com_o_desempate_no_inicio():
    """W22 e' uma das corridas em que o humano poe o B34 impar no INICIO do eixo
    (o desempate configuravel BALANCED_B34_STRIP_ODD_AT_AXIS_END=False)."""
    rows, res, length = _mini_rows(22, odd_at_end=False)
    assert not res.get("non_modular") and not res.get("collisions")
    _assert_same_rows(rows, HUMAN[22], length)


def test_parede_de_444_com_o_desempate_padrao_e_o_espelho_do_humano():
    """Com o desempate padrao (fim do eixo, 7 das 8 paredes de 494) a W22 fica com a
    MESMA composicao, a faixa de 1 B34 no fim: k_inicio=0, k_fim=1 nas duas
    fiadas (k+1 = so' a peca de canto na ponta que passa)."""
    rows, _res, length = _mini_rows(22)
    for row in rows.values():
        case = _pattern(row, length)
        codes = [c[:3] for c, _a, _b in row]
        fill = codes[(1 if case[0] == "P" else 0):(len(codes) - 1 if case[-1] == "P" else len(codes))]
        assert fill == ["B39"] * 9 + ["B34"]


def test_corrida_da_ponta_ao_T_de_meio_de_parede_sai_igual_ao_humano():
    """W9 de t=0 ao T em t=487: ancora de ponta (P/S) e de meio de parede (N = B54
    da principal, G = vao do T). Faixas 1+2 nas duas fiadas e o vazado menor
    para o B54 em N, para dentro em G - igual ao humano peca a peca."""
    rows, res, _length = _mini_rows(9)
    assert not res.get("non_modular") and not res.get("collisions")
    vistos = set()
    for row in rows.values():
        trecho = [p for p in row if p[1] < 487.0]
        case = ("P" if trecho[0][1] <= 1.0 else "S") + "-" + ("N" if trecho[-1][0] == "B54" else "G")
        hum = HUMAN_W9_TO_T[case]
        assert [c for c, _a, _b in trecho] == [c for c, _a, _b in hum], (case, trecho)
        for (c, a, b), (_hc, ha, hb) in zip(trecho, hum):
            assert abs(a - ha) <= 1.0 and abs(b - hb) <= 1.0, (case, c, a, ha)
        vistos.add(case)
    assert vistos == set(HUMAN_W9_TO_T)


@pytest.mark.parametrize("wall", [14, 21])
def test_largura_k_constante_e_k_mais_1_na_fiada_que_passa(wall):
    rows, _res, length = _mini_rows(wall)
    larguras = {}
    for row in rows.values():
        case = _pattern(row, length)
        codes = [c[:3] for c, _a, _b in row]
        n = len(codes)
        gl = 0
        while gl < n and codes[gl] == "B34":
            gl += 1
        gr = 0
        while gr < n - gl and codes[n - 1 - gr] == "B34":
            gr += 1
        assert codes.count("B34") == gl + gr  # nenhum B34 no miolo
        larguras[case] = (gl - (case[0] == "P"), gr - (case[-1] == "P"))
    assert len(set(larguras.values())) == 1
    k_ini, k_fim = list(larguras.values())[0]
    assert (k_ini, k_fim) == (1, 2)


def test_sem_a_regra_a_parede_volta_ao_empilhamento_antigo():
    rows, _res, length = _mini_rows(21, enabled=False)
    pp = [r for r in rows.values() if _pattern(r, length) == "P-P"][0]
    codes = [c[:3] for c, _a, _b in pp]
    assert codes[:2] == ["B34", "B39"]           # nenhum B34 de ajuste junto do inicio
    assert codes[-4:] == ["B34"] * 4             # 3 de ajuste + canto no fim (o 1+4)


def test_parede_com_janela_nao_recebe_a_faixa_nem_nas_fiadas_abaixo_do_peitoril():
    """Escopo da 86.3: "sem abertura" vale para a ALTURA INTEIRA da parede. As
    fiadas 0-1 ficam abaixo do peitoril (a banda delas recebe a lista de aberturas
    FILTRADA, sem a janela), mas a corrida tem janela mais acima - a grade nao
    pode trocar entre bandas junto da janela (risco de septos medido na
    simulacao: 265 -> 375 em W0/W2/W3). Resultado = o da regra desligada."""
    janela = [_window_on_w21()]
    com, res, _l = _mini_rows(21, openings=janela)
    assert res["_ctx_openings"], "a janela sintetica tem de cair na W21"
    sem, _r, _l2 = _mini_rows(21, enabled=False, openings=janela)
    assert com == sem


def test_deterministico():
    a, _r1, _l1 = _mini_rows(21)
    b, _r2, _l2 = _mini_rows(21)
    assert a == b
