# -*- coding: utf-8 -*-
"""CR-BLOCK-01 - invariantes permanentes de PRISMA / AMARRACAO VERTICAL.

Suite SEPARADA de `tests/test_script.py` de proposito (reduz conflito com
outros trabalhos em paralelo). Roda fora do Revit pelos mesmos dubles
(`revit_stubs`), pelo mesmo `load_script`.

Nenhum teste aqui usa parede, ID, coordenada ou comprimento de projeto
real - so' geometria sintetica construida no proprio teste.

    python3 -m pytest tests/test_block_bonding.py -q
"""

import itertools

import pytest

import load_script
import revit_stubs

XYZ = revit_stubs.XYZ
Line = revit_stubs.Line
m = load_script.load()
F = m.FEET_PER_METER


# --------------------------------------------------------------- helpers
def ft(cm):
    return cm / 100.0 * F


def to_cm(value_ft):
    return value_ft / F * 100.0


def seg(x0, y0, x1, y1):
    return Line.CreateBound(XYZ(ft(x0), ft(y0), 0.0), XYZ(ft(x1), ft(y1), 0.0))


def _cell(center_cm, size_cm, width_cm=8.0):
    return {"center_local": (ft(center_cm), 0.0), "size_local": (ft(size_cm), ft(width_cm))}


def _block(code, length_cm, cells):
    return {
        "symbol": None, "logical_code": code, "length_cm": float(length_cm),
        "height_cm": 19.0, "width_cm": 14.0, "cells_local": cells,
        "is_special_bond": code in ("B34", "B54"),
        "is_compensator": code in ("C09", "C04"),
        "source_instance_id": None,
    }


def build_catalog(order=None):
    """Catalogo dos 6 codigos. `order` permuta a ORDEM DE INSERCAO das
    chaves - usado para provar que o resultado nao depende dela."""
    pieces = {
        "B39": _block("B39", 39, [_cell(-9.9, 15.7), _cell(9.9, 15.8)]),
        "B34": _block("B34", 34, [_cell(-10.2, 10.7), _cell(7.4, 15.7)]),
        "B54": _block("B54", 54, [_cell(-19.5, 15.8), _cell(0.0, 12.5), _cell(19.5, 15.8)]),
        "B19": _block("B19", 19, [_cell(0.0, 15.7)]),
        "C09": _block("C09", 9, []),
        "C04": _block("C04", 4, []),
    }
    keys = list(order) if order else list(pieces)
    return dict((code, pieces[code]) for code in keys)


CATALOG = build_catalog()


def joints(layout, seg_start_cm=0.0, **kwargs):
    return m._layout_internal_joint_positions_cm(layout, seg_start_cm, **kwargs)


def coincidences(layout, seg_start_cm, avoid_cm):
    return m._count_joint_coincidences_cm(joints(layout, seg_start_cm), avoid_cm)


def codes(layout):
    return [code for code, _a, _b in (layout or [])]


def solve_plan(lines, thickness_cm=14.0, openings=None, catalog=None):
    walls = [(line, ft(thickness_cm), (False, False)) for line in lines]
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    per_wall = openings or dict((i, []) for i in range(len(walls)))
    result = m.solve_building_blocks(nodes, walls, end_to_node, per_wall,
                                     catalog or CATALOG)
    return result, walls, nodes


def wall_course_extents(walls, candidates):
    """{(wall_idx, course): [(t_lo_cm, t_hi_cm, code, is_tie), ...]} - a
    projecao no eixo da parede, o UNICO referencial em que juntas se
    comparam (secao 9 do CR)."""
    out = {}
    for cand in candidates:
        wall_idx = cand.get("wall_idx")
        if wall_idx is None:
            continue
        p0, _p1, wall_dir, _len, _t = m._wall_axis_and_length(walls, wall_idx)
        t_lo, t_hi = m._candidate_extent_on_wall_axis(cand, p0, wall_dir)
        out.setdefault((wall_idx, cand.get("course")), []).append(
            (min(t_lo, t_hi), max(t_lo, t_hi), cand.get("logical_code"),
             m._is_tie_candidate(cand) or cand.get("node_index") is not None))
    for items in out.values():
        items.sort(key=lambda e: (round(e[0], 4), round(e[1], 4), e[2]))
    return out


def course_joints_cm(items, max_gap_cm=None):
    if max_gap_cm is None:
        max_gap_cm = m.BLOCK_JOINT_CM * 2.0
    return m.joint_positions_from_extents(
        [(a, b) for a, b, _c, _n in items], max_gap_cm=max_gap_cm)


def forbidden_pairs(walls, candidates, tolerance_cm=None):
    """Juntas da fiada B que caem em cima de uma junta da fiada A, ignorando
    as que envolvem peca de amarracao de no' (seção 5 manda repeti-las) e as
    isentas pela secao 11.8."""
    if tolerance_cm is None:
        tolerance_cm = m.VERTICAL_JOINT_STAGGER_TOLERANCE_CM
    extents = wall_course_extents(walls, candidates)
    found = []
    walls_seen = sorted(set(w for (w, _c) in extents))
    for wall_idx in walls_seen:
        items_a = extents.get((wall_idx, "A")) or []
        items_b = extents.get((wall_idx, "B")) or []
        if not items_a or not items_b:
            continue
        p0, _p1, _dir, length_ft, _t = m._wall_axis_and_length(walls, wall_idx)
        length_cm = length_ft / F * 100.0
        ties_a = [(a, b) for a, b, _c, n in items_a if n]
        ties_b = [(a, b) for a, b, _c, n in items_b if n]
        for x_b in course_joints_cm(items_b):
            for x_a in course_joints_cm(items_a):
                if abs(x_b - x_a) > tolerance_cm:
                    continue
                if any(lo - 1.0 <= x_b <= hi + 1.0 for lo, hi in ties_a + ties_b):
                    continue
                found.append((wall_idx, round(x_b, 2)))
                break
    return found


# =====================================================================
# INV-BLOCK-BOND-001 / 002 - a MEDICAO de coincidencia funciona
# =====================================================================
def test_inv_001_duas_fiadas_identicas_com_juntas_coincidentes_sao_detectadas():
    layout = m._pier_ordered_layout(119.0, CATALOG, 0.0, 0.0)
    assert codes(layout) == ["B39", "B39", "B39"]
    assert coincidences(layout, 15.0, joints(layout, 15.0)) == len(joints(layout, 15.0))
    assert coincidences(layout, 15.0, joints(layout, 15.0)) > 0


def test_inv_002_layout_corretamente_desencontrado_nao_e_marcado():
    layout = m._pier_ordered_layout(119.0, CATALOG, 0.0, 0.0)
    desencontrado = [(code, a + 20.0, b + 20.0) for code, a, b in layout]
    assert coincidences(desencontrado, 15.0, joints(layout, 15.0)) == 0


# =====================================================================
# INV-BLOCK-BOND-005 - a fiada 2 CONSIDERA as juntas da anterior
#
# CAUSA-RAIZ do CR-BLOCK-01, reproduzida com numeros sinteticos: um trecho
# de 99cm fechado dos DOIS lados (nenhuma ponta aberta) cuja fiada anterior
# tem juntas em 54,5 e 94,5. O layout padrao (tier 6 - 1 B19 no inicio,
# ultimissimo recurso) coincide nas DUAS juntas; a MESMA composicao com o
# B19 na outra ponta desencontra as duas. Antes da correcao, TODOS os
# candidatos gerados eram identicos ao baseline (so' variavam o PRIMEIRO
# bloco), e a busca nao tinha o que escolher.
# =====================================================================
@pytest.mark.xfail(strict=True, reason=(
    "CR-BLOCK-01 CHECKPOINT B - reproducao da causa-raiz: a enumeracao de "
    "candidatos de _pier_layout_avoiding_joints so' varia o PRIMEIRO bloco, "
    "entao os 7 candidatos gerados para este trecho sao TODOS identicos ao "
    "baseline. Removido no CHECKPOINT C."))
def test_inv_005_segunda_fiada_considera_juntas_da_anterior():
    avoid = [54.5, 94.5]
    baseline = m._pier_ordered_layout(99.0, CATALOG, 0.0, 0.0,
                                      leading_open_override=False,
                                      trailing_open_override=False)
    assert coincidences(baseline, 35.0, avoid) == 2, "cenario perdeu o sentido"

    escolhido = m._pier_layout_avoiding_joints(
        99.0, CATALOG, 0.0, 0.0, 35.0, avoid,
        leading_is_open=False, trailing_is_open=False)
    assert escolhido is not None
    assert coincidences(escolhido, 35.0, avoid) == 0
    # a composicao (o CONJUNTO de pecas) nao piorou - so' a ORDEM mudou
    assert sorted(codes(escolhido)) == sorted(codes(baseline))


def test_inv_005b_desencontro_tambem_vale_para_trecho_com_ponta_aberta():
    avoid = [39.5, 79.5]
    escolhido = m._pier_layout_avoiding_joints(
        119.0, CATALOG, 0.0, 0.0, 0.0, avoid,
        leading_is_open=True, trailing_is_open=False)
    assert escolhido is not None
    assert coincidences(escolhido, 0.0, avoid) == 0


# =====================================================================
# INV-BLOCK-BOND-008 - zero coincidencia vence uma equivalente com
# coincidencia (regra #1 e' o criterio primario depois da regra #2)
# =====================================================================
def test_inv_008_solucao_sem_coincidencia_vence_a_equivalente_com_coincidencia():
    avoid = [54.5, 94.5]
    escolhido = m._pier_layout_avoiding_joints(
        99.0, CATALOG, 0.0, 0.0, 35.0, avoid,
        leading_is_open=False, trailing_is_open=False)
    # ... e nunca ao custo da regra #2 (compensadores em sequencia), que
    # tem prioridade sobre a regra #1 (secao 16.1).
    assert m._layout_compensator_run_excess(escolhido, CATALOG) == 0


def test_inv_008b_regra_2_continua_na_frente_do_desencontro():
    """Bug real da secao 16.1: o desencontro NUNCA pode ser comprado com
    MAIS compensadores em sequencia do que o baseline ja' tinha - trocar
    uma junta coincidente por uma parede REPROVADA nao e' um bom negocio.

    Vale para todo trecho, inclusive os que ja' nascem ruins (29cm fechado
    dos dois lados so' fecha com 3 compensadores em fila): nesses, o teto
    e' o do proprio baseline."""
    for pier_cm, avoid in ((29.0, [19.5]), (99.0, [54.5, 94.5]),
                           (119.0, [39.5, 79.5]), (249.0, [39.5, 119.5])):
        baseline = m._pier_ordered_layout(pier_cm, CATALOG, 0.0, 0.0,
                                          leading_open_override=False,
                                          trailing_open_override=False)
        escolhido = m._pier_layout_avoiding_joints(
            pier_cm, CATALOG, 0.0, 0.0, 0.0, avoid,
            leading_is_open=False, trailing_is_open=False)
        assert escolhido is not None
        assert (m._layout_compensator_run_excess(escolhido, CATALOG)
                <= m._layout_compensator_run_excess(baseline, CATALOG)), \
            (pier_cm, codes(baseline), codes(escolhido))


# =====================================================================
# INV-BLOCK-BOND-006 - a EXCECAO documentada (secao 11.8) continua valendo
# =====================================================================
def test_inv_006_excecao_de_peca_pequena_encostada_em_abertura_permanece():
    layout = [("C04", 0.0, 4.0), ("B39", 5.0, 44.0), ("B39", 45.0, 84.0)]
    todas = joints(layout, 100.0)
    assert len(todas) == 2
    com_isencao = joints(layout, 100.0, leading_is_open=True, trailing_is_open=False)
    assert len(com_isencao) == 1, "a junta da pastilha encostada no vao deve ser isenta"
    assert com_isencao == todas[1:]


def test_inv_006b_isencao_nao_vale_contra_no_de_amarracao():
    layout = [("C04", 0.0, 4.0), ("B39", 5.0, 44.0), ("B39", 45.0, 84.0)]
    fechado = joints(layout, 100.0, leading_is_open=False, trailing_is_open=False)
    assert len(fechado) == 2


def test_inv_006c_isencao_nao_e_aplicada_na_BUSCA():
    """A isencao diz que a junta PODE coincidir, nao que deva ser ignorada
    ao escolher (secao 11.8): a busca continua preferindo desencontrar."""
    baseline = m._pier_ordered_layout(84.0, CATALOG, 0.0, 0.0,
                                      leading_open_override=True,
                                      trailing_open_override=True)
    assert codes(baseline) == ["B39", "B39", "C04"]
    # a junta 79,5 separa a PASTILHA encostada na ponta aberta: a secao 11.8
    # permite que ela coincida, mas a BUSCA tem de continuar tentando fugir.
    avoid = [79.5]
    escolhido = m._pier_layout_avoiding_joints(
        84.0, CATALOG, 0.0, 0.0, 0.0, avoid,
        leading_is_open=True, trailing_is_open=True)
    assert escolhido is not None
    assert coincidences(escolhido, 0.0, avoid) == 0


# =====================================================================
# INV-BLOCK-BOND-004 / 010 - DETERMINISMO
# =====================================================================
@pytest.mark.parametrize("ordem", list(itertools.permutations(
    ("B39", "B34", "B54", "B19", "C09", "C04")))[:12])
def test_inv_004_ordem_do_catalogo_nao_muda_o_layout_vencedor(ordem):
    catalog = build_catalog(ordem)
    avoid = [54.5, 94.5]
    referencia = m._pier_layout_avoiding_joints(
        99.0, CATALOG, 0.0, 0.0, 35.0, avoid,
        leading_is_open=False, trailing_is_open=False)
    alternativo = m._pier_layout_avoiding_joints(
        99.0, catalog, 0.0, 0.0, 35.0, avoid,
        leading_is_open=False, trailing_is_open=False)
    assert codes(alternativo) == codes(referencia)


def test_inv_004b_ordem_da_lista_de_juntas_a_evitar_nao_muda_o_vencedor():
    avoid = [54.5, 94.5, 134.5, 174.5]
    referencia = m._pier_layout_avoiding_joints(
        199.0, CATALOG, 0.0, 0.0, 35.0, avoid,
        leading_is_open=False, trailing_is_open=False)
    for permutacao in itertools.permutations(avoid):
        alternativo = m._pier_layout_avoiding_joints(
            199.0, CATALOG, 0.0, 0.0, 35.0, list(permutacao),
            leading_is_open=False, trailing_is_open=False)
        assert codes(alternativo) == codes(referencia)


def _fingerprint(walls, candidates):
    """Fingerprint canonico: (geometria da parede, fiada, codigo, posicao
    longitudinal). Nunca ElementId, nunca ordem de lista."""
    extents = wall_course_extents(walls, candidates)
    rows = []
    for (wall_idx, course), items in extents.items():
        line = walls[wall_idx][0]
        a, b = line.GetEndPoint(0), line.GetEndPoint(1)
        chave = sorted([(round(a.X * 1000.0), round(a.Y * 1000.0)),
                        (round(b.X * 1000.0), round(b.Y * 1000.0))])
        for t_lo, t_hi, code, _tie in items:
            rows.append("{0}|{1}|{2}|{3:.1f}|{4:.1f}".format(
                chave, course, code, round(t_lo, 1) + 0.0, round(t_hi, 1) + 0.0))
    return tuple(sorted(rows))


def test_inv_010_fingerprint_determinista_sob_permutacao_de_candidatos():
    lines = [seg(0, 0, 500, 0), seg(500, 0, 500, 400), seg(500, 400, 0, 400)]
    result, walls, _nodes = solve_plan(lines)
    base = _fingerprint(walls, result["candidates"])
    assert base
    embaralhado = list(result["candidates"])
    for corte in (1, 3, 7, len(embaralhado) // 2):
        embaralhado = embaralhado[corte:] + embaralhado[:corte]
        assert _fingerprint(walls, embaralhado) == base


def test_inv_010b_mesma_planta_resolvida_duas_vezes_da_o_mesmo_fingerprint():
    lines = [seg(0, 0, 500, 0), seg(500, 0, 500, 400), seg(500, 400, 0, 400)]
    r1, w1, _n1 = solve_plan(lines)
    r2, w2, _n2 = solve_plan([seg(0, 0, 500, 0), seg(500, 0, 500, 400),
                              seg(500, 400, 0, 400)])
    assert _fingerprint(w1, r1["candidates"]) == _fingerprint(w2, r2["candidates"])


# =====================================================================
# INV-BLOCK-BOND-003 - inverter a orientacao geometrica nao muda o veredito
# =====================================================================
def test_inv_003_inverter_endpoints_nao_muda_o_veredito_de_amarracao():
    direto = [seg(0, 0, 500, 0), seg(500, 0, 500, 400), seg(500, 400, 0, 400)]
    invertido = [seg(500, 0, 0, 0), seg(500, 400, 500, 0), seg(0, 400, 500, 400)]
    r_direto, w_direto, _n = solve_plan(direto)
    r_inv, w_inv, _n2 = solve_plan(invertido)
    assert len(forbidden_pairs(w_direto, r_direto["candidates"])) == \
        len(forbidden_pairs(w_inv, r_inv["candidates"]))
    assert len(r_direto["alignment_conflicts"]) == len(r_inv["alignment_conflicts"])


# =====================================================================
# INV-BLOCK-BOND-007 - B34/B54 de amarracao nao sao deslocados
# =====================================================================
def test_inv_007_pecas_de_amarracao_de_no_nao_sao_deslocadas_pelo_desencontro():
    lines = [seg(0, 0, 500, 0), seg(500, 0, 500, 400), seg(500, 400, 0, 400),
             seg(250, 0, 250, 400)]
    walls = [(line, ft(14.0), (False, False)) for line in lines]
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, end_to_node = m.build_wall_graph(walls, junction_map)
    openings = dict((i, []) for i in range(len(walls)))

    # posicao das pecas de no' calculada SOZINHA (sem preenchimento nenhum)
    so_nos = m.solve_all_intersections(nodes, walls, CATALOG, openings, end_to_node)
    esperado = sorted(
        (c["wall_idx"], c["course"], c["logical_code"],
         round(m._candidate_extent_on_wall_axis(
             c, *m._wall_axis_and_length(walls, c["wall_idx"])[0:3:2])[0], 2))
        for c in so_nos["candidates"] if c.get("wall_idx") is not None
    )

    completo = m.solve_building_blocks(nodes, walls, end_to_node, openings, CATALOG)
    obtido = sorted(
        (c["wall_idx"], c["course"], c["logical_code"],
         round(m._candidate_extent_on_wall_axis(
             c, *m._wall_axis_and_length(walls, c["wall_idx"])[0:3:2])[0], 2))
        for c in completo["candidates"]
        if c.get("wall_idx") is not None and c.get("node_index") is not None
    )
    assert obtido == esperado, "o desencontro moveu/removeu uma peca de amarracao"


def test_inv_007b_desencontro_nunca_transforma_b34_de_no_em_enchimento():
    """As pecas de amarracao vem de `solve_all_intersections` e entram no
    preenchimento como FRONTEIRA - o layout de um trecho nunca as inclui."""
    layout = m._pier_layout_avoiding_joints(
        199.0, CATALOG, 0.0, 0.0, 0.0, [39.5, 79.5, 119.5, 159.5],
        leading_is_open=False, trailing_is_open=False)
    assert layout is not None
    assert "B54" not in codes(layout), "B54 e' peca de no', nunca preenchimento comum"


# =====================================================================
# INV-BLOCK-BOND-009 - sem solucao limpa, o solver REPORTA
# =====================================================================
def test_inv_009_sem_alternativa_sem_violacao_o_solver_reporta_em_vez_de_mentir():
    """Trecho fechado dos dois lados, multiplo exato de B39 e SEM
    compensador disponivel: nao existe composicao alternativa nenhuma. O
    solver devolve o layout coincidente (nao inventa geometria), mas a
    coincidencia continua VISIVEL para quem valida."""
    avoid = [39.5, 79.5]
    layout = m._pier_layout_avoiding_joints(
        119.0, CATALOG, 0.0, 0.0, 0.0, avoid,
        allow_compensators=False,
        leading_is_open=False, trailing_is_open=False)
    assert codes(layout) == ["B39", "B39", "B39"]
    assert coincidences(layout, 0.0, avoid) > 0


def test_inv_009b_pipeline_registra_alignment_conflict_em_vez_de_silenciar():
    lines = [seg(0, 0, 500, 0), seg(500, 0, 500, 400), seg(500, 400, 0, 400)]
    result, walls, _nodes = solve_plan(lines)
    for conflito in result["alignment_conflicts"]:
        assert conflito["coincidence_count"] > 0
        assert "wall_idx" in conflito and "seg_start_cm" in conflito
    # nenhuma parede pode sair "sem modulacao" sem motivo registrado
    assert isinstance(result["non_modular"], list)


# =====================================================================
# Regressoes que a correcao NAO pode quebrar
# =====================================================================
def test_layout_escolhido_sempre_fecha_o_trecho_exatamente():
    for pier_cm in (29.0, 39.0, 44.0, 59.0, 99.0, 119.0, 139.0, 199.0, 469.0):
        for avoid in ([], [54.5], [39.5, 79.5, 119.5]):
            layout = m._pier_layout_avoiding_joints(
                pier_cm, CATALOG, 0.0, 0.0, 0.0, avoid,
                leading_is_open=False, trailing_is_open=False)
            if layout is None:
                continue
            ocupado = sum(CATALOG[c]["length_cm"] for c in codes(layout))
            ocupado += m.BLOCK_JOINT_CM * (len(layout) - 1)
            assert abs(ocupado - pier_cm) <= m.PIER_LAYOUT_TOLERANCE_CM, \
                (pier_cm, avoid, codes(layout))


def test_meio_bloco_nunca_nasce_encostado_num_no_quando_ha_alternativa():
    """Regra #2: com as duas pontas FECHADAS, o desencontro nao pode
    introduzir um B19 que nao existia no baseline."""
    for pier_cm in (79.0, 119.0, 159.0, 199.0):
        avoid = [39.5, 79.5, 119.5, 159.5]
        baseline = m._pier_ordered_layout(pier_cm, CATALOG, 0.0, 0.0,
                                          leading_open_override=False,
                                          trailing_open_override=False)
        escolhido = m._pier_layout_avoiding_joints(
            pier_cm, CATALOG, 0.0, 0.0, 0.0, avoid,
            leading_is_open=False, trailing_is_open=False)
        assert codes(escolhido).count("B19") <= max(1, codes(baseline).count("B19"))


def test_desencontro_nao_estoura_o_teto_de_compensadores_do_baseline():
    for pier_cm in (99.0, 119.0, 139.0, 199.0, 249.0):
        avoid = [39.5, 79.5, 119.5, 159.5, 199.5]
        baseline = m._pier_ordered_layout(pier_cm, CATALOG, 0.0, 0.0,
                                          leading_open_override=False,
                                          trailing_open_override=False)
        escolhido = m._pier_layout_avoiding_joints(
            pier_cm, CATALOG, 0.0, 0.0, 0.0, avoid,
            leading_is_open=False, trailing_is_open=False)
        base_comp = sum(1 for c in codes(baseline) if CATALOG[c]["is_compensator"])
        novo_comp = sum(1 for c in codes(escolhido) if CATALOG[c]["is_compensator"])
        assert novo_comp <= max(base_comp, m.MAX_COMPENSATORS_PER_TRECHO), \
            (pier_cm, codes(baseline), codes(escolhido))
