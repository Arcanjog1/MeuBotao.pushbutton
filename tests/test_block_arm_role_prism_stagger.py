# -*- coding: utf-8 -*-
"""CR-BLOCK-ARM-ROLE-PRISM-STAGGER - a junta de CONTORNO contra um no'
(entre a peca de amarracao do L_CORNER e o primeiro/ultimo bloco do
preenchimento comum) precisa ser rastreada pela busca de desencontro
(secao 6 de REGRAS_MODULACAO_BLOCOS.md), nao so' as juntas INTERNAS do
preenchimento - ver `docs/BLOCK_ARM_ROLE_INVARIANCE.md` para o relatorio
completo.

Causa-raiz (reproduzida com o corpus real, ver `test_w076_...` abaixo):
`_layout_internal_joint_positions_cm` (por design, ver sua docstring)
NUNCA contou a junta contra um no' como "junta vertical continua entre
fiadas" - inofensivo enquanto normalmente so' uma das duas familias
(A/B) tinha candidato de no' real num dado encontro. A coordenacao de
papel (CR-BLOCK-ARM-ROLE-CONSISTENCY) corrigiu exatamente isso, e como
efeito colateral pode agora dar as DUAS familias um candidato de no'
real no MESMO encontro - se as duas usam a MESMA peca (mesmo comprimento
de B34/B54), a junta de contorno cai na MESMA posicao absoluta nas duas
fiadas, e a busca de desencontro nunca sabia disso.

Fix: `_pier_boundary_joint_positions_cm` (wall_stepper.py) computa essa
posicao e alimenta tanto a busca (`_pier_layout_avoiding_joints`) quanto
a checagem residual (`alignment_conflicts`) - SEPARADA da lista que
alimenta o reparo de abertura (`_recut_openings_and_repair`), para nao
mudar o comportamento perto de portas/janelas (regressao real medida e
corrigida durante o desenvolvimento deste fix, ver o relatorio).

Estes testes rodam o CORPUS REAL (torre_easy_lo_r00_tp1/tgd) via
`nuvem.benchmark.solver_bridge` - o caso minimo sintetico exato de W076
(pier de comprimento zero entre dois L_CORNER que usam a MESMA peca) nao
e' reproduzivel com o plano de 3 paredes usado em
`test_block_arm_role_invariance.py` (a reserva "emprestada" do quadrado
do canto so' aparece com a topologia real de mais de 2 paredes por no') -
por isso o teste usa o projeto real diretamente, a mesma pratica ja'
usada por `tests/regression/test_benchmark_baselines.py`.

    python3 -m pytest tests/test_block_arm_role_prism_stagger.py -q
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import load_script  # noqa: E402

m = load_script.load()

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from nuvem.benchmark import solver_bridge  # noqa: E402
from nuvem.benchmark.extract import from_solver  # noqa: E402


def _run(project_id):
    input_project = __import__("json").load(
        open(os.path.join(_ROOT, "nuvem", "benchmark", "projects", project_id, "input.json"),
             encoding="utf-8")
    )
    (solve_result, walls_to_create, nodes, openings_per_wall, catalog,
     base_z_ft, num_courses, notes) = solver_bridge.run_solver(input_project)
    result_project = from_solver.project_from_solver(
        project_id, solve_result, walls_to_create, nodes, openings_per_wall,
        catalog, base_z_ft, num_courses, metadata={})
    return input_project, solve_result, walls_to_create, result_project


def _wall_row_joints(wall, row_index):
    """{t_cm} - centros de junta ENTRE PECAS ADJACENTES (gap <= 5cm) da
    fiada `row_index` desta parede - mesma definicao de
    `nuvem/benchmark/analysis.row_joints`, reimplementada aqui para nao
    depender do pacote de validadores do benchmark."""
    row = next(r for r in wall["rows"] if r["row"] == row_index)
    blocks = sorted(row["blocks"], key=lambda b: b["t_start_cm"])
    joints = set()
    for i in range(len(blocks) - 1):
        gap = blocks[i + 1]["t_start_cm"] - blocks[i]["t_end_cm"]
        if gap > 5.0:
            continue
        joints.add(round((blocks[i]["t_end_cm"] + blocks[i + 1]["t_start_cm"]) / 2.0, 1))
    return joints


def _physical_key(wall):
    """Identidade FISICA de uma parede (`W|x0,y0|x1,y1|tE`, pontas
    ordenadas) - a UNICA chave comparavel entre `input.json` e o result,
    porque `model.assign_ids` reordena e renumera as paredes."""
    a = (round(wall["start_cm"][0], 1), round(wall["start_cm"][1], 1))
    b = (round(wall["end_cm"][0], 1), round(wall["end_cm"][1], 1))
    lo, hi = sorted([a, b])
    return "W|%.1f,%.1f|%.1f,%.1f|t%.1f" % (lo[0], lo[1], hi[0], hi[1],
                                            round(wall["thickness_cm"], 1))


def _wall_by_id(result_project, wall_id):
    return next(w for w in result_project["walls"] if w["id"] == wall_id)


# ============================================================
# G1/G2/G3 - caso minimo real: W076/TP1, pier de UM bloco so' entre dois
# L_CORNER que usam a MESMA peca (B34, 34cm) - a coincidencia de junta e'
# GEOMETRICAMENTE FORCADA (nenhuma composicao de preenchimento pode
# evitar uma junta cuja posicao e' fixada pelo comprimento da peca do
# no', dos dois lados) - o fix nao pode "consertar" isto sem trocar a
# PECA escolhida num dos dois nos (fora do escopo autorizado desta CR,
# ver o relatorio) - o que o fix faz e' TORNAR ISSO VISIVEL
# (`alignment_conflicts`), em vez de nunca ter sido checado.
# ============================================================

def test_w076_tp1_coincidencia_de_contorno_foi_resolvida_pelo_arm_safe_repair():
    """Historico (G1/G2/G3 - ver cabecalho do modulo): a coincidencia de
    34,5cm em W076 era GEOMETRICAMENTE FORCADA para qualquer FILL, porque
    as duas familias usam a MESMA peca de no' (B34, mesmo comprimento) nos
    dois L_CORNER - so' TROCAR A PECA ESCOLHIDA num dos dois nos
    resolveria, fora do escopo desta CR (PRISM-STAGGER, so' fill).

    `CR-BLOCK-ARM-SAFE-REPAIR-GATE-FIDELITY` (2026-09-04) fecha exatamente
    essa lacuna: o candidato ARM `wall_idx=75/SAME_A` (numeracao desta
    sessao; W076 no benchmark) TROCA o papel do no' - aceito depois do fix
    do compensator gate (a rejeicao antiga era um FANTASMA do agregado
    multi-banda por letra de familia, nao uma regressao real - ver
    REGRAS_MODULACAO_BLOCOS.md 34.1 e docs/BLOCK_ARM_SAFE_REPAIR_GATE_
    FIDELITY_SPEC.md). Com SAFE REPAIR ativo (producao), W076 deixa de ter
    a coincidencia - a "prova da causa-raiz" antiga (a coincidencia
    persistir) so' valia enquanto o papel do no' ficava fixo; a causa-raiz
    do PRISM-STAGGER (junta de contorno invisivel a busca) continua real e
    provada por W041/`test_w041_...` abaixo, que nao depende de ARM.

    CR-N1 (2026-09-09): a SEGUNDA assercao ("um candidato ARM foi aceito
    para W076") caiu pelo mesmo precedente da parede 23. Medido nas DUAS
    arvores (`origin/main` 08495d9 x base+CR-N1), TP1 real, conferindo
    antes que `W076` E' a MESMA parede fisica no input e no result
    (`W|7677.2,1568.0|7677.2,1637.0|t14.0` nos dois - aqui `W0xx` casa,
    mas a chave fisica e' quem manda):

        base   W076 repairable=SIM  aceita=SIM  coincidencia=[]  prisma=NAO
        CR-N1  W076 repairable=NAO  aceita=NAO  coincidencia=[]  prisma=NAO
        paredes repairable no TP1 inteiro   5 -> 0
        prisma forcado FINAL no TP1        29 -> 24

    O RESULTADO FISICO de W076 e' identico nas duas arvores; o que mudou
    foi a rota (reparo aceito -> geracao ja' correta). A assercao de
    mecanismo virou uma assercao FISICA mais forte: a coincidencia de
    contorno tem de estar resolvida em TODOS os pares de fiadas vizinhas
    (o teste antigo so' olhava o par 0/1) e a parede tem de terminar SEM
    prisma forcado."""
    input_project, solve_result, walls_to_create, result_project = _run(
        "torre_easy_lo_r00_tp1")
    wall_idx = next(i for i, w in enumerate(input_project["walls"]) if w["id"] == "W076")

    wall = _wall_by_id(result_project, "W076")
    entrada = input_project["walls"][wall_idx]
    assert _physical_key(entrada) == _physical_key(wall), (
        "W076 do input e W076 do result nao sao a MESMA parede fisica - "
        "`model.assign_ids` reordena as paredes, entao cruzar os dois "
        "arquivos por `W0xx` nao vale (secao 38.5 das regras): %s x %s"
        % (_physical_key(entrada), _physical_key(wall)))

    for row_index in range(len(wall["rows"]) - 1):
        joints_a = _wall_row_joints(wall, row_index)
        joints_b = _wall_row_joints(wall, row_index + 1)
        assert not (joints_a & joints_b), (
            "esperava a coincidencia de contorno de W076 RESOLVIDA entre as "
            "fiadas %d e %d - se voltou a coincidir, ou o candidato ARM "
            "deixou de ser aceito ou a GERACAO regrediu (investigar antes "
            "de ajustar este teste): %s / %s"
            % (row_index, row_index + 1, joints_a, joints_b)
        )
    audits = solve_result.get("wall_bond_audits")
    assert not m._wall_has_forced_corner_prism(wall_idx, audits), (
        "W076 tem de terminar SEM prisma forcado - por reparo ARM aceito "
        "ou por ja' nascer correta na geracao")


# ============================================================
# G3/G7 - caso com liberdade real de composicao: W041/TP1 tinha a MESMA
# regressao de prisma (introduzida pela coordenacao de papel) mas, ao
# contrario de W076, o pier tem espaco para mais de UM bloco - o fix
# consegue mesmo ASSIM encontrar uma composicao sem coincidencia.
# ============================================================

def test_w041_tp1_prisma_resolvido_de_verdade_nao_so_reportado():
    _, _, _, result_project = _run("torre_easy_lo_r00_tp1")
    wall = _wall_by_id(result_project, "W041")
    num_rows = len(wall["rows"])
    for row_index in range(num_rows - 1):
        joints_a = _wall_row_joints(wall, row_index)
        joints_b = _wall_row_joints(wall, row_index + 1)
        assert not (joints_a & joints_b), (
            "W041 nao devia mais ter junta continua entre as fiadas %d e %d: %s"
            % (row_index, row_index + 1, joints_a & joints_b)
        )


# ============================================================
# G6 - a cobertura ganha pelo CR-BLOCK-ARM-ROLE-CONSISTENCY (commit
# d813f45) continua INTACTA depois deste fix - nenhuma fiada volta a
# ficar ausente/quase vazia por causa da mudanca na busca de
# desencontro.
# ============================================================

def test_w022_w093_tp1_cobertura_do_arm_role_consistency_preservada():
    _, _, _, result_project = _run("torre_easy_lo_r00_tp1")
    for wall_id in ("W022", "W093"):
        wall = _wall_by_id(result_project, wall_id)
        for row in wall["rows"]:
            assert row["blocks"], (
                "%s fiada %d ficou sem NENHUM bloco - regressao de cobertura "
                "introduzida pelo fix de prisma" % (wall_id, row["row"])
            )


# ============================================================
# G11/G14 (parcial) - determinismo: rodar duas vezes o mesmo projeto real
# tem que dar exatamente as mesmas juntas em W076/W041 (a busca de
# desencontro nao pode depender de nada nao-deterministico).
# ============================================================

def test_determinismo_w076_w041_duas_rodadas_identicas():
    _, _, _, result_project_1 = _run("torre_easy_lo_r00_tp1")
    _, _, _, result_project_2 = _run("torre_easy_lo_r00_tp1")
    for wall_id in ("W076", "W041"):
        wall1 = _wall_by_id(result_project_1, wall_id)
        wall2 = _wall_by_id(result_project_2, wall_id)
        for row1, row2 in zip(sorted(wall1["rows"], key=lambda r: r["row"]),
                              sorted(wall2["rows"], key=lambda r: r["row"])):
            codes1 = sorted((b["code"], round(b["t_start_cm"], 2)) for b in row1["blocks"])
            codes2 = sorted((b["code"], round(b["t_start_cm"], 2)) for b in row2["blocks"])
            assert codes1 == codes2, (wall_id, row1["row"], codes1, codes2)


# ============================================================
# G12 - o fix nunca deveria mudar o resultado perto de uma abertura por
# um motivo alheio ao vao em si (regressao real medida e corrigida
# durante o desenvolvimento: OPENING_BLOCK_INSIDE_DOOR subiu +3 no TGD
# quando a junta de contorno entrava na lista que alimenta
# `_recut_openings_and_repair` - corrigido mantendo essa lista
# SEPARADA, ver `course_a_boundary_joint_positions_cm` em
# wall_stepper.py). Aqui so' confirma que a peca de fechamento de W010
# (unica parede deste conjunto com abertura) continua sem invadir o
# vao.
# ============================================================

def test_w010_tp1_com_abertura_nenhum_bloco_invade_o_vao():
    from nuvem.benchmark import analysis

    input_project, _, _, result_project = _run("torre_easy_lo_r00_tp1")
    wall_input = next(w for w in input_project["walls"] if w["id"] == "W010")
    wall = _wall_by_id(result_project, "W010")
    block_height_cm = 19.0  # mesma fiada usada pelo catalogo do solver (ver CATALOG)
    for opening in wall_input.get("openings") or []:
        t_lo, t_hi = opening["t_start_cm"], opening["t_end_cm"]
        for row in wall["rows"]:
            if not analysis.opening_active_in_row(opening, row["elevation_cm"], block_height_cm):
                continue  # fiada fora da faixa vertical do vao - solida de proposito
            for block in row["blocks"]:
                overlap = min(block["t_end_cm"], t_hi) - max(block["t_start_cm"], t_lo)
                assert overlap <= 0.5, (
                    "%s invade o vao [%.1f,%.1f] na fiada %d: %s"
                    % ("W010", t_lo, t_hi, row["row"], block)
                )
