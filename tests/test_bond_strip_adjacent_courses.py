# -*- coding: utf-8 -*-
"""REPEATED_VERTICAL_COMPENSATOR_STRIP: faixa vertical exige fiadas
ADJACENTES, nunca repeticao so' na mesma paridade.

FALSO POSITIVO REAL, medido ao vivo via MCP no primeiro beta controlado do
Revit (2026-09-09), na bancada de 2 paredes / 1 encontro em L / 0
aberturas. O auditor reprovava a parede CURTA (69cm) com:

    REPEATED_VERTICAL_COMPENSATOR_STRIP: B34 repetido(s) em X~37.0cm,
    em 9 fiadas (0, 2, 4, 6, 8, 10, 12, 14, 16)

Todas PARES, nenhuma impar. O usuario confirmou visualmente que a
modulacao esta' correta, e a medicao dos blocos REAIS criados no Revit
provou geometricamente que esta:

    fiada PAR  (A): B19[t 0..19]   B34[t 20..54]
    fiada IMPAR(B): B34[t 0..34]   B34[t 35..69]

No X do cluster (t~37) existe peca especial nas DUAS paridades - mas o
CENTRO do B34 impar cai em t=52, dentro da zona isenta de borda
(BOND_STRIP_EDGE_EXEMPT_CM=25 num eixo de 69cm), e por isso so' as pares
entravam no cluster. As juntas ficam defasadas 15cm entre fiadas
ADJACENTES (par em t~19,5; impar em t~34,5) e nao existe junta corrida.

Causa-raiz: o detector contava len(courses) sem olhar ADJACENCIA. Como
`solve_building_blocks_all_courses` resolve UM par A/B e o repete em toda
fiada par e toda fiada impar, qualquer peca especial da fiada A aparece
por CONSTRUCAO em 100% das fiadas pares - exatamente a mesma causa-raiz ja'
documentada e corrigida para ALTERNATING_JOINT_PATTERN.

Estes testes cobrem os dois lados: o caso VALIDO nao pode mais reprovar, e
o caso RUIM DE VERDADE (pecas especiais empilhadas em fiadas adjacentes)
continua sendo detectado.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import load_script  # noqa: E402
import revit_stubs  # noqa: E402

m = load_script.load()
XYZ = revit_stubs.XYZ
Line = revit_stubs.Line
F = m.FEET_PER_METER


def ft(cm):
    return cm / 100.0 * F


def seg(x0, y0, x1, y1):
    return Line.CreateBound(XYZ(ft(x0), ft(y0), 0.0), XYZ(ft(x1), ft(y1), 0.0))


def _block(code, length_cm, is_compensator=False):
    return {
        "symbol": None, "logical_code": code, "length_cm": float(length_cm),
        "height_cm": 19.0, "width_cm": 14.0, "cells_local": [],
        "is_special_bond": code in ("B34", "B54"),
        "is_compensator": is_compensator,
        "source_instance_id": None,
    }


CATALOG = {
    "B34": _block("B34", 34), "B54": _block("B54", 54), "B19": _block("B19", 19),
    "B39": _block("B39", 39), "C09": _block("C09", 9, is_compensator=True),
    "C04": _block("C04", 4, is_compensator=True),
}


def _wall(x0, y0, x1, y1, thickness_cm=14.0):
    return (seg(x0, y0, x1, y1), ft(thickness_cm), (False, False))


def _place(walls, wall_idx, code, t_center_cm, course="A"):
    entry = CATALOG[code]
    p0, _p1, wall_dir, _len_ft, _th = m._wall_axis_and_length(walls, wall_idx)
    origin = XYZ(p0.X + wall_dir.X * ft(t_center_cm),
                 p0.Y + wall_dir.Y * ft(t_center_cm), p0.Z)
    return m._make_block_candidate(code, entry, course, origin, wall_dir, "TEST",
                                   node_index=None, wall_idx=wall_idx)


def _strip_problems(audit):
    return [p for p in audit["problems"]
            if p.startswith("REPEATED_VERTICAL_COMPENSATOR_STRIP")]


# ---------------------------------------------------------------------
# BANCADA REAL - parede curta de 69cm do primeiro beta no Revit
# ---------------------------------------------------------------------

NUM_COURSES = 17


def _bancada_beta_real():
    """A parede curta de 69cm exatamente como o Revit a criou: 17 fiadas,
    par = B19[0..19] + B34[20..54], impar = B34[0..34] + B34[35..69]."""
    walls = [_wall(0, 0, 0, 69), _wall(0, 62, 354.01, 62)]
    course_candidates = {}
    for ci in range(NUM_COURSES):
        if ci % 2 == 0:
            course_candidates[ci] = [
                _place(walls, 0, "B19", 9.5, "A"),
                _place(walls, 0, "B34", 37.0, "A"),
            ]
        else:
            course_candidates[ci] = [
                _place(walls, 0, "B34", 17.0, "B"),
                _place(walls, 0, "B34", 52.0, "B"),
            ]
    return walls, course_candidates


def _auditar(walls, course_candidates, num_courses=NUM_COURSES):
    return m.audit_wall_bond_quality(
        0, walls, course_candidates, CATALOG, num_courses,
        openings_per_wall=[[], []], nodes=None, end_to_node=None)


def test_bancada_beta_real_nao_e_mais_reprovada_por_faixa_vertical():
    """CONTROLE NEGATIVO (o falso positivo). Esta parede e' a bancada do
    primeiro beta, confirmada visualmente pelo usuario e medida no Revit.
    Ela NAO pode ser reprovada por REPEATED_VERTICAL_COMPENSATOR_STRIP.

    Com a logica ANTIGA este teste falha: o cluster em t~37 tinha 9 fiadas
    de 17 (ratio 0,53 >= BOND_STRIP_RATIO) e virava faixa."""
    walls, cc = _bancada_beta_real()
    audit = _auditar(walls, cc)
    assert _strip_problems(audit) == [], (
        "falso positivo de volta - a parede da bancada do beta foi reprovada: %r"
        % (_strip_problems(audit),))
    assert audit["compensator_strips"] == []


def test_bancada_beta_real_registra_o_padrao_como_dado_sem_penalizar():
    """O auditor NAO foi silenciado: ele continua enxergando e reportando a
    repeticao de mesma paridade - so' que como DADO (`alternating_strips`),
    nunca como defeito. Mesmo tratamento ja' dado a `alternating_joints`."""
    walls, cc = _bancada_beta_real()
    audit = _auditar(walls, cc)
    registros = audit["alternating_strips"]
    assert registros, "o padrao de mesma paridade sumiu do diagnostico - nao pode ser silenciado"
    alvo = [r for r in registros if r["courses"] == [0, 2, 4, 6, 8, 10, 12, 14, 16]]
    assert alvo, [r["courses"] for r in registros]
    assert alvo[0]["adjacent_run"] == 1, alvo[0]
    assert "B34" in alvo[0]["codes"]


def test_faixa_vertical_em_fiadas_adjacentes_continua_reprovando():
    """CONTROLE POSITIVO: pecas especiais EMPILHADAS em fiadas adjacentes
    (uma diretamente sobre a outra) continuam sendo faixa vertical e
    continuam reprovando. Sem isto, a correcao teria desligado o detector."""
    walls = [_wall(0, 0, 0, 69), _wall(0, 62, 354.01, 62)]
    cc = {}
    for ci in range(NUM_COURSES):
        # MESMA peca especial no MESMO t em TODA fiada - par e impar.
        cc[ci] = [
            _place(walls, 0, "B19", 9.5, "A" if ci % 2 == 0 else "B"),
            _place(walls, 0, "B34", 37.0, "A" if ci % 2 == 0 else "B"),
        ]
    audit = _auditar(walls, cc)
    assert _strip_problems(audit), (
        "faixa vertical REAL (fiadas adjacentes) deixou de ser detectada")
    faixa = audit["compensator_strips"][0]
    assert faixa["adjacent_run"] >= m.BOND_STRIP_MIN_ADJACENT_COURSES, faixa
    assert faixa["adjacent_run"] == NUM_COURSES, faixa


def test_faixa_curta_de_duas_fiadas_adjacentes_ainda_e_detectada():
    """CONTROLE POSITIVO 2: o menor caso ruim que a regra ainda tem de
    pegar - duas fiadas ADJACENTES empilhadas, dentro de um padrao que
    tambem repete. `adjacent_run == 2` e' exatamente o limiar."""
    walls = [_wall(0, 0, 0, 69), _wall(0, 62, 354.01, 62)]
    cc = {}
    for ci in range(NUM_COURSES):
        itens = [_place(walls, 0, "B19", 9.5, "A" if ci % 2 == 0 else "B")]
        # Fiadas {0,1,4,6,8,10,12,14,16}: o unico par ADJACENTE e' 0/1
        # (a fiada 2 fica de fora de proposito, senao 0,1,2 daria corrida 3).
        if (ci % 2 == 0 and ci != 2) or ci == 1:
            itens.append(_place(walls, 0, "B34", 37.0, "A" if ci % 2 == 0 else "B"))
        cc[ci] = itens
    audit = _auditar(walls, cc)
    assert _strip_problems(audit), "faixa com 2 fiadas adjacentes deveria reprovar"
    faixa = audit["compensator_strips"][0]
    assert faixa["adjacent_run"] == 2, faixa


def test_longest_adjacent_course_run():
    """O discriminador isolado - o que separa padrao A/B de faixa real."""
    assert m._longest_adjacent_course_run([]) == 0
    assert m._longest_adjacent_course_run([0, 2, 4, 6, 8, 10, 12, 14, 16]) == 1
    assert m._longest_adjacent_course_run([1, 3, 5, 7]) == 1
    assert m._longest_adjacent_course_run([0, 1]) == 2
    assert m._longest_adjacent_course_run([0, 2, 3, 6]) == 2
    assert m._longest_adjacent_course_run([4, 5, 6, 9, 11]) == 3
    assert m._longest_adjacent_course_run(list(range(17))) == 17


def test_juntas_da_bancada_real_ficam_defasadas_entre_fiadas_adjacentes():
    """A prova FISICA que sustenta a reclassificacao: nas fiadas
    adjacentes as juntas nao coincidem, entao nao ha' junta corrida nem
    quebra de prisma - o caso e' bom de verdade, nao apenas 'nao
    detectado'."""
    walls, cc = _bancada_beta_real()
    p0, _p1, wall_dir, _len_ft, _th = m._wall_axis_and_length(walls, 0)

    def juntas(ci):
        extents = sorted(m._candidate_extent_on_wall_axis(c, p0, wall_dir)
                         for c in cc[ci])
        return [round((extents[i][1] + extents[i + 1][0]) / 2.0, 2)
                for i in range(len(extents) - 1)]

    juntas_par = juntas(0)
    juntas_impar = juntas(1)
    assert juntas_par and juntas_impar
    for jp in juntas_par:
        for ji in juntas_impar:
            assert abs(jp - ji) > 10.0, (
                "junta praticamente coincidente entre fiadas adjacentes: "
                "par=%.2f impar=%.2f" % (jp, ji))
    assert audit_sem_junta_corrida(walls, cc)


def audit_sem_junta_corrida(walls, cc):
    audit = _auditar(walls, cc)
    assert audit["continuous_joints"] == [], audit["continuous_joints"]
    return True


# =====================================================================
# REPRODUCAO COM O SOLVER REAL (2026-09-10) - sem Revit, sem MCP
#
# Os testes acima codificam a geometria MEDIDA no Revit. Este roda o
# SOLVER DE VERDADE sobre a bancada e reproduz o falso positivo com a
# mensagem exata que o usuario viu, provando tambem POR QUE o bench
# offline nunca o pegava: o solver, no referencial do input do benchmark,
# atribui as letras A/B TROCADAS em relacao a execucao real no Revit.
#
#   offline: fiada par = B34[0..34] B34[35..69] | impar = B19[0..19] B34[20..54]
#   Revit  : fiada par = B19[0..19] B34[20..54] | impar = B34[0..34] B34[35..69]
#
# O cluster de peca especial nao isenta fica em t~37 nas DUAS. A diferenca
# e' so' quantas fiadas entram nele:
#
#   paridade offline -> 8 fiadas de 17 = 0,471  < BOND_STRIP_RATIO (0,5) -> nao dispara
#   paridade Revit   -> 9 fiadas de 17 = 0,529 >= BOND_STRIP_RATIO       -> DISPARA
#
# Ou seja: o veredito do auditor dependia de QUAL paridade o solver
# escolheu para uma solucao fisicamente equivalente - um cara-ou-coroa em
# cima do limiar. A correcao por adjacencia torna o auditor INVARIANTE a
# paridade, que e' a propriedade correta.
# =====================================================================

L_LONGA_CM = 354.01
L_CURTA_CM = 69.0


def _bancada_com_solver_real():
    """(walls, nodes, ends, openings, catalog, course_candidates) da bancada
    de 2 paredes / 1 L, resolvida pelo solver REAL."""
    walls = [_wall(0.0, 0.0, 0.0, L_CURTA_CM),
             _wall(-7.0, L_CURTA_CM - 7.0, L_LONGA_CM - 7.0, L_CURTA_CM - 7.0)]
    walls, junction_map = m.extend_wall_ends_to_junctions(walls, m.JUNCTION_FACE_SEARCH_FT)
    nodes, ends = m.build_wall_graph(walls, junction_map)
    openings = [[], []]
    res = m.solve_building_blocks_all_courses(
        nodes, walls, ends, openings, CATALOG, ft(612.0), NUM_COURSES,
        variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
    return walls, nodes, ends, openings, res["course_candidates"]


def _reprovadas(walls, nodes, ends, openings, cc, minimo_adjacencia):
    original = m.BOND_STRIP_MIN_ADJACENT_COURSES
    m.BOND_STRIP_MIN_ADJACENT_COURSES = minimo_adjacencia
    try:
        todas = m.audit_all_walls_bond_quality(
            walls, cc, CATALOG, NUM_COURSES,
            openings_per_wall=openings, nodes=nodes, end_to_node=ends)
        faixas = []
        for wi, aud in sorted(todas.items()):
            faixas += [(wi, p) for p in aud["problems"]
                       if p.startswith("REPEATED_VERTICAL_COMPENSATOR_STRIP")]
        return faixas, todas
    finally:
        m.BOND_STRIP_MIN_ADJACENT_COURSES = original


def test_solver_real_reproduz_o_falso_positivo():
    """O solver REAL reproduz o falso positivo com a mensagem EXATA do
    relato - e a correcao o elimina. Fecha o caso sem Revit.

    NAO fixa qual paridade dispara: qual das duas letras o solver chama de
    "A" depende do referencial de coordenadas (foi exatamente isso que fez
    o bench offline nunca pegar o defeito). O que o teste exige e' que, com
    a logica ANTIGA, UMA das duas paridades reprove com a mensagem do
    relato - e que com a NOVA nenhuma reprove."""
    walls, nodes, ends, openings, cc = _bancada_com_solver_real()
    assert sum(len(v) for v in cc.values()) == 187, sum(len(v) for v in cc.values())

    cc_trocada = {ci: cc[1 if ci % 2 == 0 else 0] for ci in range(NUM_COURSES)}

    antigas = []
    for usado in (cc, cc_trocada):
        faixas, _ = _reprovadas(walls, nodes, ends, openings, usado, 0)
        antigas.append(faixas)
    disparadas = [f for f in antigas if f]
    assert disparadas, "a logica antiga nao reproduziu o falso positivo em nenhuma paridade"
    _wi, msg = disparadas[0][0]
    assert "B34" in msg and "9 fiadas" in msg, msg
    assert "0, 2, 4, 6, 8, 10, 12, 14, 16" in msg, msg

    for usado in (cc, cc_trocada):
        novas, todas = _reprovadas(walls, nodes, ends, openings, usado, 2)
        assert novas == [], "a correcao nao eliminou o falso positivo: %r" % (novas,)
        assert all(aud["ok"] for aud in todas.values()), {
            wi: aud["problems"] for wi, aud in todas.items() if not aud["ok"]}
    # e continua VISIVEL como dado, nao silenciado
    _novas, todas = _reprovadas(walls, nodes, ends, openings, cc, 2)
    assert any(aud.get("alternating_strips") for aud in todas.values())


def test_veredito_do_auditor_e_invariante_a_paridade_A_B():
    """A propriedade que a correcao garante: duas solucoes FISICAMENTE
    equivalentes (o mesmo par A/B, com as letras trocadas) recebem o MESMO
    veredito.

    Antes NAO recebiam: o cluster de peca especial nao isenta cai em t~37
    nas duas, mas entram 8 fiadas numa paridade (8/17 = 0,471, abaixo de
    BOND_STRIP_RATIO = 0,5) e 9 na outra (9/17 = 0,529, acima). O limiar
    ficava exatamente entre os dois, e o veredito virava cara-ou-coroa."""
    walls, nodes, ends, openings, cc = _bancada_com_solver_real()
    cc_trocada = {ci: cc[1 if ci % 2 == 0 else 0] for ci in range(NUM_COURSES)}

    nova_direta, _ = _reprovadas(walls, nodes, ends, openings, cc, 2)
    nova_trocada, _ = _reprovadas(walls, nodes, ends, openings, cc_trocada, 2)
    assert nova_direta == nova_trocada == [], (nova_direta, nova_trocada)

    # prova de que a fragilidade EXISTIA: com a logica antiga os dois
    # vereditos DIVERGEM para a mesma fisica.
    antiga_direta, _ = _reprovadas(walls, nodes, ends, openings, cc, 0)
    antiga_trocada, _ = _reprovadas(walls, nodes, ends, openings, cc_trocada, 0)
    assert bool(antiga_direta) != bool(antiga_trocada), (
        "a fragilidade de paridade nao ficou demonstrada: %r vs %r"
        % (antiga_direta, antiga_trocada))


def test_constante_de_adjacencia_esta_ativa_no_codigo_entregue():
    """Os dois testes acima manipulam BOND_STRIP_MIN_ADJACENT_COURSES de
    proposito, para comparar as duas logicas - por isso passariam mesmo se
    o valor ENTREGUE fosse revertido para 0. Este teste guarda o valor de
    producao: sem ele, um `= 0` de volta no codigo passaria batido."""
    assert m.BOND_STRIP_MIN_ADJACENT_COURSES >= 2, m.BOND_STRIP_MIN_ADJACENT_COURSES
