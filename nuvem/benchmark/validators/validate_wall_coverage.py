# -*- coding: utf-8 -*-
"""COBERTURA DAS PAREDES - o validador que impede a falha silenciosa.

Motivo de existir, nas palavras do pedido (item 8): *"uma parede nao pode
simplesmente deixar de ser modulada porque o solver encontrou
dificuldade"*. Um solver que desiste de uma parede e nao registra nada
some do relatorio - e o score sobe, porque parede sem bloco tambem e'
parede sem erro de prisma, sem colisao e sem compensador.

Por isso este validador e' o unico que olha o que NAO existe:

* `COVERAGE_WALL_NOT_MODULATED` - a parede nao tem nenhum bloco.
* `COVERAGE_MISSING_ROW` - falta uma fiada no meio da pilha (indice
  ausente entre a primeira e a ultima).
* `COVERAGE_PARTIAL_WALL` - a parede tem blocos, mas a extensao coberta
  nao chega perto do comprimento dela.
* `COVERAGE_GAP_IN_ROW` - buraco numa fiada, FORA de qualquer abertura
  ativa naquela altura (dentro do vao o buraco e' o esperado).
* `COVERAGE_ROW_MOSTLY_EMPTY` - fiada quase vazia numa parede cujas
  outras fiadas fecharam. E' o sintoma de o solver ter perdido UMA das
  duas familias de fiada (A ou B), nao de um encaixe dificil.
* `COVERAGE_ORPHAN_BLOCKS` - blocos sem parede (falha da reconstrucao ou
  peca solta no modelo). Nao e' erro do solver, mas nunca pode sumir.
"""

from .. import analysis
from .. import model
from . import base

# Quanto do comprimento MODULAVEL da parede precisa estar coberto para ela
# nao contar como "modulada pela metade". Comprimento modulavel = a parede
# menos os vaos e menos as zonas de amarracao (ver
# `modulable_intervals`) - medir contra o comprimento BRUTO acusaria toda
# parede com porta, que e' o oposto do que este validador serve para
# achar.
MIN_COVERAGE_RATIO = 0.9

# Buraco menor que isto dentro de uma fiada e' junta/folga de amarracao,
# nao trecho sem modular. Uma peca util nunca e' menor que a pastilha
# (4cm) + junta.
MIN_REPORTABLE_GAP_CM = 5.0

# Abaixo disto a fiada nao esta' "com um buraco": ela esta' vazia. So'
# vira achado quando OUTRA fiada da mesma parede fechou direito - senao o
# caso e' `COVERAGE_PARTIAL_WALL`/`COVERAGE_WALL_NOT_MODULATED`, que ja'
# cobrem a parede inteira mal resolvida.
ROW_MOSTLY_EMPTY_RATIO = 0.5


def wall_top_z_cm(wall):
    """Cota FISICA do topo da parede (`base_z + height`), ou `None` quando a
    parede nao declara altura.

    Sem altura declarada nao existe pe-direito para comparar - e' o unico
    caso em que a falta de fiada no topo fica sem veredito (CR-C1). NAO
    chutar a altura a partir das fiadas existentes: isso tornaria o
    criterio tautologico ("espera-se o que ja' esta' la'").
    """
    height_cm = wall.get("height_cm")
    if not height_cm:
        return None
    return float(wall.get("base_z_cm") or 0.0) + float(height_cm)


def missing_course_above_cm(wall, block_height_cm, course_step_cm):
    """`(cota_da_fiada_que_falta, topo_coberto_cm, topo_da_parede_cm)` quando
    ainda CABE uma fiada INTEIRA acima da fiada mais alta desta parede -
    senao `None`.

    Este e' o criterio fisico que substituiu, na CR-C1, a comparacao
    `len(fiadas) < expected_rows` (um numero GLOBAL de projeto aplicado
    igualmente a toda parede). Ver secao 37 de
    `nuvem/REGRAS_MODULACAO_BLOCOS.md`.

    Por que a contagem global estava errada: `expected_rows` sai de
    `settings.num_courses`, que e' o TETO de fiadas do projeto inteiro. As
    paredes tem alturas diferentes (220/260/270/280/281cm no corpus real),
    e uma parede baixa NUNCA tera' aquele numero de fiadas - ela estava
    correta e era acusada assim mesmo. Medido: rodando os validadores
    sobre o PROPRIO gabarito humano, 95 (TGD) e 94 (TP1)
    `COVERAGE_MISSING_ROW`, 100% deles neste ramo e ZERO no ramo do meio
    da pilha.

    Por que a expectativa NAO e' calculada como "quantas fiadas cabem":
    a fiada do topo nao segue o passo do grid - ela e' encostada no
    pe-direito (medido no gabarito: parede de 270cm fecha em z=250, de
    281cm em z=261, com canaleta `CJ19` de 29cm e pecas `_C` de 9cm).
    Reproduzir aqui ONDE cada fiada cai seria reimplementar a politica de
    empilhamento do solver DENTRO do validador - e um validador que
    duplica a regra que ele fiscaliza para de fiscalizar.

    O criterio usado nao precisa saber onde as fiadas caem: pergunta so'
    se sobra espaco para MAIS UMA fiada inteira (proximo passo + corpo da
    peca) abaixo do pe-direito. Conservador de proposito - a maior folga
    LEGITIMA medida no gabarito humano e' 11cm contra um passo de 20cm.
    """
    top_z = wall_top_z_cm(wall)
    if top_z is None:
        return None
    elevations = [float(block.get("z_cm") or 0.0)
                  for row in (wall.get("rows") or [])
                  for block in (row.get("blocks") or [])]
    if not elevations:
        return None
    highest_cm = max(elevations)
    next_course_cm = highest_cm + float(course_step_cm)
    if next_course_cm + float(block_height_cm) <= top_z + 1e-6:
        return (next_course_cm, highest_cm, top_z)
    return None


def junction_reserved_intervals(wall):
    """Pedacos do eixo que pertencem a' PAREDE VIZINHA num encontro.

    `extend_wall_ends_to_junctions` estica o eixo ate' a face oposta da
    parede que ele encontra; nessa sobra quem coloca a peca e' a vizinha,
    alternando por fiada (a fiada A amarra por uma parede, a B pela
    outra). Contar essa sobra como "trecho sem modular" acusaria TODA
    parede com canto - foi exatamente o falso positivo medido na primeira
    rodada do piloto sintetico (124 achados, todos de 15cm nas pontas,
    todos legitimos).

    A sobra vai do ponto do no' ate' a ponta, mais meia espessura (a peca
    de amarracao encosta na face oposta) e uma junta."""
    reserved = []
    reach = (wall.get("thickness_cm") or 0.0) / 2.0 + analysis.BLOCK_JOINT_CM
    length = wall["length_cm"]
    for junction in wall.get("junctions") or []:
        if junction.get("type") == model.JUNCTION_FREE_END:
            continue
        t_cm = float(junction.get("t_cm", 0.0))
        if t_cm <= reach + 1e-6:
            reserved.append((0.0, t_cm + reach))
        elif t_cm >= length - reach - 1e-6:
            reserved.append((t_cm - reach, length))
    return analysis.merge_intervals(reserved)


def modulable_intervals(wall, row, block_height_cm):
    """O que aquela fiada REALMENTE tinha que preencher: a parede menos os
    vaos ativos naquela altura e menos as zonas de amarracao."""
    holes = [(o_start, o_end) for o_start, o_end, _op
             in analysis.active_opening_intervals(wall, row, block_height_cm)]
    holes.extend(junction_reserved_intervals(wall))
    return analysis.subtract_intervals((0.0, wall["length_cm"]), holes)


def _covered_intervals(row):
    return analysis.merge_intervals(
        [(b["t_start_cm"], b["t_end_cm"]) for b in row.get("blocks") or []],
        tolerance_cm=analysis.BOND_MAX_ADJACENT_GAP_CM,
    )


def validate_wall(wall, block_height_cm, expected_rows=None, occupancy=None,
                  course_step_cm=None):
    findings = []
    rows = model.rows_sorted(wall)
    total_blocks = sum(len(row.get("blocks") or []) for row in rows)

    if total_blocks == 0:
        findings.append(base.finding(
            "COVERAGE_WALL_NOT_MODULATED",
            wall=wall["id"],
            detail=(
                "parede de {0:.1f}cm x {1}cm sem nenhum bloco".format(
                    wall["length_cm"], wall.get("height_cm") or "?")
            ),
            expected_blocks=True,
            generated_blocks=0,
            length_cm=wall["length_cm"],
        ))
        return findings

    # ---- fiada faltando no meio ---------------------------------------
    indices = sorted(row["row"] for row in rows if row.get("blocks"))
    if indices:
        missing = [i for i in range(indices[0], indices[-1] + 1)
                   if i not in set(indices)]
        for index in missing:
            findings.append(base.finding(
                "COVERAGE_MISSING_ROW",
                wall=wall["id"],
                detail=(
                    "fiada {0} ausente entre a {1} e a {2}".format(
                        index, indices[0], indices[-1])
                ),
                row=index,
                first_row=indices[0],
                last_row=indices[-1],
            ))
    # Fiadas faltando NO TOPO sao reportadas a parte, porque a causa e'
    # outra: o solver parou antes de chegar ao pe-direito, nao pulou uma
    # fiada no meio.
    #
    # CR-C1: a pergunta e' FISICA e por ELEVACAO ("ainda cabe uma fiada
    # inteira abaixo do pe-direito DESTA parede?"), nunca mais
    # `len(fiadas) < expected_rows` - um numero GLOBAL do projeto
    # comparado com a contagem ordinal de cada parede. Ver
    # `missing_course_above_cm` e a secao 37 das regras. O parametro
    # `expected_rows` continua na assinatura so' para nao quebrar
    # chamadores antigos: ele NAO decide mais este achado.
    if course_step_cm is None:
        course_step_cm = float(block_height_cm) + analysis.BLOCK_JOINT_CM
    above = missing_course_above_cm(wall, block_height_cm, course_step_cm)
    if above is not None:
        next_course_cm, highest_cm, top_z_cm = above
        findings.append(base.finding(
            "COVERAGE_MISSING_ROW",
            wall=wall["id"],
            detail=(
                "fiada mais alta em z={0:.1f}cm, mas ainda cabe fiada em "
                "z={1:.1f}cm abaixo do topo da parede (z={2:.1f}cm)".format(
                    highest_cm, next_course_cm, top_z_cm)
            ),
            row=None,
            rows_found=len(indices),
            highest_course_z_cm=round(highest_cm, 2),
            missing_course_z_cm=round(next_course_cm, 2),
            wall_top_z_cm=round(top_z_cm, 2),
        ))

    # ---- comprimento coberto -------------------------------------------
    best_ratio = 0.0
    best_expected = 0.0
    for row in rows:
        covered = _covered_intervals(row)
        if not covered:
            continue
        expected = modulable_intervals(wall, row, block_height_cm)
        expected_len = sum(end - start for start, end in expected)
        if expected_len <= MIN_REPORTABLE_GAP_CM:
            continue
        pieces = list(covered)
        if occupancy is not None:
            for interval in expected:
                pieces.extend(occupancy.foreign_coverage_on_axis(
                    wall, row, interval[0], interval[1]))
            pieces = analysis.merge_intervals(pieces, tolerance_cm=analysis.BLOCK_JOINT_CM)
        span = sum(
            analysis.interval_overlap_cm(piece, interval)
            for piece in pieces for interval in expected
        )
        ratio = span / expected_len
        if ratio > best_ratio:
            best_ratio, best_expected = ratio, expected_len
    if best_expected > 0 and best_ratio < MIN_COVERAGE_RATIO:
        findings.append(base.finding(
            "COVERAGE_PARTIAL_WALL",
            wall=wall["id"],
            detail=(
                "melhor fiada cobre {0:.0f}% do trecho modulavel "
                "({1:.1f}cm de {2:.1f}cm de parede)".format(
                    100.0 * best_ratio, best_expected, wall["length_cm"])
            ),
            coverage_ratio=round(best_ratio, 4),
            modulable_cm=round(best_expected, 2),
            length_cm=wall["length_cm"],
        ))

    # ---- fiada praticamente vazia numa parede que tem fiadas cheias ----
    #
    # E' um caso a parte do "buraco na fiada", e mais grave: quando METADE
    # das fiadas de uma parede sai quase vazia e a outra metade sai
    # completa, o solver nao teve um problema de encaixe - ele perdeu uma
    # das duas familias de fiada (A ou B). Medido no piloto sintetico:
    # 334cm de 349cm vazios nas fiadas pares de uma parede cujas fiadas
    # impares fecharam inteiras.
    for row in rows:
        expected = modulable_intervals(wall, row, block_height_cm)
        expected_len = sum(end - start for start, end in expected)
        if expected_len <= MIN_REPORTABLE_GAP_CM:
            continue
        pieces = list(_covered_intervals(row))
        if occupancy is not None:
            for interval in expected:
                pieces.extend(occupancy.foreign_coverage_on_axis(
                    wall, row, interval[0], interval[1]))
            pieces = analysis.merge_intervals(pieces, tolerance_cm=analysis.BLOCK_JOINT_CM)
        span = sum(analysis.interval_overlap_cm(piece, interval)
                   for piece in pieces for interval in expected)
        ratio = span / expected_len
        if ratio < ROW_MOSTLY_EMPTY_RATIO and best_ratio >= MIN_COVERAGE_RATIO:
            findings.append(base.finding(
                "COVERAGE_ROW_MOSTLY_EMPTY",
                wall=wall["id"],
                detail=(
                    "fiada {0} cobre so' {1:.0f}% do trecho modulavel "
                    "({2:.1f}cm de {3:.1f}cm), enquanto a melhor fiada da "
                    "mesma parede cobre {4:.0f}%".format(
                        row["row"], 100.0 * ratio, span, expected_len,
                        100.0 * best_ratio)
                ),
                row=row["row"],
                coverage_ratio=round(ratio, 4),
                covered_cm=round(span, 2),
                modulable_cm=round(expected_len, 2),
                best_row_ratio=round(best_ratio, 4),
            ))

    # ---- buracos dentro de cada fiada ----------------------------------
    for row in rows:
        covered = _covered_intervals(row)
        if not covered:
            continue
        for interval in modulable_intervals(wall, row, block_height_cm):
            holes = analysis.subtract_intervals(interval, covered)
            if occupancy is not None and holes:
                # A peca que amarra vindo da parede VIZINHA preenche o vao
                # de verdade - ver `analysis.OccupancyIndex`.
                foreign = occupancy.foreign_coverage_on_axis(
                    wall, row, interval[0], interval[1])
                if foreign:
                    holes = [piece for hole in holes
                             for piece in analysis.subtract_intervals(hole, foreign)]
            for hole_start, hole_end in holes:
                size = hole_end - hole_start
                if size < MIN_REPORTABLE_GAP_CM:
                    continue
                findings.append(base.finding(
                    "COVERAGE_GAP_IN_ROW",
                    wall=wall["id"],
                    detail=(
                        "vazio de {0:.1f}cm em t={1:.1f}..{2:.1f}cm na fiada "
                        "{3}, fora de abertura e fora de zona de "
                        "amarracao".format(size, hole_start, hole_end, row["row"])
                    ),
                    row=row["row"],
                    gap_t_cm=[round(hole_start, 2), round(hole_end, 2)],
                    gap_cm=round(size, 2),
                ))
    return findings


def validate(project, context=None):
    block_height = analysis.block_height_of(project)
    # `settings.expected_rows` NAO e' mais lido aqui (CR-C1): era o teto de
    # fiadas do PROJETO aplicado igualmente a toda parede, independente da
    # altura fisica dela. A expectativa de fiada no topo agora sai da
    # geometria de cada parede - ver `missing_course_above_cm`.
    course_step = analysis.course_step_cm(project)
    findings = []
    occupancy = analysis.OccupancyIndex(project)
    for wall in project.get("walls") or []:
        findings.extend(validate_wall(wall, block_height, None, occupancy,
                                      course_step_cm=course_step))

    orphans = project.get("orphan_blocks") or []
    if orphans:
        findings.append(base.finding(
            "COVERAGE_ORPHAN_BLOCKS",
            wall=None,
            detail="{0} bloco(s) sem parede associada".format(len(orphans)),
            count=len(orphans),
            sample=[b.get("code") for b in orphans[:10]],
        ))
    return findings


base.register("wall_coverage", validate)
