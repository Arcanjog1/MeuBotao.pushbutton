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
