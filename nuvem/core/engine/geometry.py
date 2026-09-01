# -*- coding: utf-8 -*-
"""Geometria pura (linhas/paralelismo/distancias/eixo central) extraida
verbatim de `core/wall_modeling.py` - primeira fatia da extracao fisica do
motor de regras para `core/engine/` (ver ARQUITETURA_INTERATIVA.md,
"Por que a extracao fisica do motor nao foi feita" - esta e' a
continuacao mecanica, funcao por funcao, prometida la').

Nenhuma formula mudou. `wall_modeling.py` importa tudo daqui (`from
core.engine.geometry import *`, SEM fallback - ver o ponto onde o import
acontece: e' agora uma dependencia obrigatoria, nao mais opcional como as
constantes de tolerancia) para que todos os call-sites existentes (por
nome solto, dentro do mesmo modulo) continuem funcionando sem nenhuma
alteracao.

`__all__` inclui os nomes com underscore de proposito - `import *` os
ignoraria por padrao, e varias funcoes "privadas" daqui (`_line_geom_cache`
etc.) sao chamadas por nome solto de FORA deste arquivo, dentro de
`wall_modeling.py`.

Modulo PURO: as unicas dependencias de "Revit" aqui sao os TIPOS `XYZ`/
`Line` (usados so' para construir/ler pontos e curvas - nunca `doc`/
`uidoc`, nunca uma consulta ao documento) - por isso e' seguro e testado
sem nenhum Revit de verdade (ver tests/revit_stubs.py).
"""

import math

from Autodesk.Revit.DB import XYZ, Line

from core.engine.tolerances import (
    MIN_WALL_SEGMENT_OVERLAP_RATIO, MIN_WALL_SEGMENT_ABS_FLOOR_FT,
    OPENING_BRIDGE_TOLERANCE_FT, FEET_PER_METER,
)

__all__ = [
    "are_lines_parallel", "get_line_midpoint", "project_point_on_line",
    "get_distance_between_parallel_lines", "_line_geom_cache",
    "_are_parallel_cached", "_distance_between_parallel_cached",
    "_line_pair_overlap_ft_cached", "_xy_deviation_ft", "_axis_offset_error_ft",
    "_pair_frame_lines", "_interval_in_frame", "_axis_offset_in_frame",
    "_line_span_key", "create_centerline",
    "_opening_bridges_gap", "_merge_collinear_cluster",
    "_cluster_axis", "_cluster_interval", "_clusters_bridge_via_opening",
    "_bridge_clusters_via_openings", "merge_collinear_fragments",
    "_line_pair_overlap_ft", "lines_overlap_enough",
    "_pair_frame_cached", "_pair_symmetric_overlap_ft_cached",
    "_pair_symmetric_thickness_ft_cached", "_line_identity_key_cached",
    "_symmetric_within_distance_cached", "symmetric_lines_within_distance",
]


def are_lines_parallel(l1, l2, tolerance=0.05):
    """Verifica se duas linhas 2D sao paralelas (produto vetorial ~ 0)."""
    dir1 = l1.Direction.Normalize()
    dir2 = l2.Direction.Normalize()
    cross = dir1.CrossProduct(dir2)
    return abs(cross.Z) < tolerance


def get_line_midpoint(line):
    """Retorna o ponto medio de uma linha."""
    return line.Evaluate(0.5, True)


def project_point_on_line(point, line):
    """Projeta um ponto 3D sobre a linha (tratada como infinita)."""
    p0 = line.GetEndPoint(0)
    p1 = line.GetEndPoint(1)
    v = (p1 - p0).Normalize()
    w = point - p0
    proj_dist = w.DotProduct(v)
    return p0 + v * proj_dist


def get_distance_between_parallel_lines(l1, l2):
    """Mede a distancia perpendicular entre duas linhas paralelas."""
    mid_p1 = get_line_midpoint(l1)
    proj_p2 = project_point_on_line(mid_p1, l2)
    return mid_p1.DistanceTo(proj_p2)


def _line_geom_cache(line):
    """Pre-calcula (p0, direcao normalizada, comprimento, ponto medio) de
    UMA linha - para reuso nos lacos O(n^2)/O(m^2) que comparam cada linha
    contra TODAS as outras (ver PERFORMANCE em find_wall_pairs,
    scan_possible_missed_bonecas, merge_collinear_fragments e
    _bridge_clusters_via_openings).

    Sem isso, are_lines_parallel/get_distance_between_parallel_lines
    recalculavam a direcao normalizada (Direction.Normalize(), uma conta
    com raiz quadrada) e o ponto medio (Evaluate) da MESMA linha `i` do ZERO
    a cada uma das O(n) comparacoes contra `j` - repetido, sem necessidade,
    porque a linha `i` fica fixa durante toda a varredura do laco interno.
    Calcular uma vez por linha (O(n) chamadas no total, em vez de O(n^2))
    e' um dos motivos do script ficar lento em Layers de CAD grandes,
    junto com a complexidade algoritmica ja corrigida (ver os
    PERFORMANCE das funcoes citadas acima).

    O ponto medio e' reconstruido como `p0 + direcao * (comprimento / 2)`
    em vez de `line.Evaluate(0.5, True)` (usado por get_line_midpoint) -
    matematicamente identico para uma Line reta e bound (mesma formula que
    o proprio Revit aplica internamente), sem nenhuma perda de precisao
    relevante para as tolerancias (na ordem de mm a cm) usadas em todas as
    comparacoes que consomem este cache."""
    p0 = line.GetEndPoint(0)
    p1 = line.GetEndPoint(1)
    direction = (p1 - p0).Normalize()
    length = p0.DistanceTo(p1)
    midpoint = p0 + direction * (length * 0.5)
    return (p0, p1, direction, length, midpoint)


def _are_parallel_cached(cache1, cache2, tolerance=0.05):
    """Equivalente a are_lines_parallel, usando direcoes ja calculadas por
    _line_geom_cache em vez de recalcula-las a partir da Line."""
    direction1 = cache1[2]
    direction2 = cache2[2]
    cross = direction1.CrossProduct(direction2)
    return abs(cross.Z) < tolerance


def _distance_between_parallel_cached(cache1, cache2):
    """Equivalente a get_distance_between_parallel_lines(l1, l2), usando o
    ponto medio de `l1` e a posicao/direcao de `l2` ja calculados por
    _line_geom_cache em vez de recalcula-los a partir das Line."""
    midpoint1 = cache1[4]
    p0_2, direction2 = cache2[0], cache2[2]
    w = midpoint1 - p0_2
    proj_dist = w.DotProduct(direction2)
    proj_point = p0_2 + direction2 * proj_dist
    return midpoint1.DistanceTo(proj_point)


def _line_pair_overlap_ft_cached(cache1, cache2):
    """Equivalente a _line_pair_overlap_ft(line1, line2), usando p0/p1/
    direcao/comprimento ja calculados por _line_geom_cache em vez de
    recalcula-los a partir das Line."""
    p0, _p1, direction, length1, _mid = cache1
    q0, q1, _dir2, length2, _mid2 = cache2

    t_q0 = (q0 - p0).DotProduct(direction)
    t_q1 = (q1 - p0).DotProduct(direction)
    t2_lo, t2_hi = min(t_q0, t_q1), max(t_q0, t_q1)

    overlap_lo = max(0.0, t2_lo)
    overlap_hi = min(length1, t2_hi)
    overlap_ft = max(0.0, overlap_hi - overlap_lo)
    return overlap_ft, length1, length2


# --- CR-2F-B (PAIR_PREDICATE_ASYMMETRY) ------------------------------------
#
# `_distance_between_parallel_cached` e `_line_pair_overlap_ft_cached` acima
# medem a partir de UMA das duas linhas (a que entra como `cache1`) - a
# escolha de qual e' `cache1` e' so' o indice na lista, entao invertar a
# ordem do par muda o resultado (ate' 185,21 cm de diferenca na espessura e
# 99,77 cm no overlap, medido no censo exaustivo da Etapa 2G - ver
# nuvem/benchmark/PLANO_ETAPA_2G.md, itens A e D.1). Isso faz o conjunto de
# pares candidatos de `find_wall_pairs` depender da ORDEM da lista de
# entrada, nao so' da geometria.
#
# As tres funcoes abaixo sao NOVAS e so' sao usadas por `find_wall_pairs`
# (nuvem/core/engine/wall_pairing.py). `_distance_between_parallel_cached` e
# `_line_pair_overlap_ft_cached` continuam intocadas: o merge nunca deixou de
# medir cada direcao com elas - o CR-2F-A (bloco mais abaixo) passou a exigir
# as DUAS direcoes, sem mudar nenhuma das duas medicoes.
#
# A ideia: em vez de medir a partir de uma das duas linhas, construir um
# referencial (base + normal + origem) que NAO tem lado - a bissetriz das
# duas direcoes, com origem no meio dos dois pontos medios. Trocar
# cache1<->cache2 da o mesmo referencial (ou o mesmo com os dois eixos
# negados, que os `abs()`/diferencas de projecao abaixo absorvem). Prova de
# simetria e medicao (0 divergencias em 4.111.278 pares) no plano, item H.1.
#
# Tudo em float puro sobre os componentes do cache (nunca um XYZ
# intermediario): e' o que faz o custo caber no orcamento de performance
# (+74,6% de aritmetica do predicado simetrico e' compensado por -41,9% da
# reescrita em float, ver PLANO_ETAPA_2G.md item J) - nao e' micro-otimizacao.

def _pair_frame_cached(cache1, cache2):
    """Referencial 2D simetrico do par (cache1, cache2): base = bissetriz
    das duas direcoes (orientadas para o mesmo lado), normal = perpendicular
    a' base, origem = ponto medio entre os dois pontos medios. Devolve
    (bx, by, nx, ny, ox, oy). Ver PLANO_ETAPA_2G.md item H.1 para a prova de
    simetria exata em IEEE-754."""
    d1 = cache1[2]
    d2 = cache2[2]
    m1 = cache1[4]
    m2 = cache2[4]

    dot = d1.X * d2.X + d1.Y * d2.Y
    s = 1.0 if dot >= 0.0 else -1.0
    bx = d1.X + d2.X * s
    by = d1.Y + d2.Y * s
    nb = math.hypot(bx, by)
    if nb < 1e-9:
        bx, by = d1.X, d1.Y
    else:
        bx, by = bx / nb, by / nb

    nx, ny = -by, bx
    ox, oy = (m1.X + m2.X) * 0.5, (m1.Y + m2.Y) * 0.5
    return bx, by, nx, ny, ox, oy


def _pair_symmetric_overlap_ft_cached(cache1, cache2):
    """Equivalente simetrico de `_line_pair_overlap_ft_cached`: projeta as
    quatro pontas sobre a base do referencial de `_pair_frame_cached` (em
    vez da direcao de UMA das duas linhas) e recorta a intersecao dos dois
    intervalos - sem privilegiar `cache1` nem `cache2`. `length1`/`length2`
    continuam sendo os comprimentos ORIGINAIS de cada linha (o denominador
    `min(length1, length2)` do overlap_ratio em find_wall_pairs nao muda,
    ver PLANO_ETAPA_2G.md item H.2/secao G.2.5)."""
    bx, by, _nx, _ny, ox, oy = _pair_frame_cached(cache1, cache2)

    p0_i, p1_i = cache1[0], cache1[1]
    p0_j, p1_j = cache2[0], cache2[1]

    ti0 = bx * (p0_i.X - ox) + by * (p0_i.Y - oy)
    ti1 = bx * (p1_i.X - ox) + by * (p1_i.Y - oy)
    tj0 = bx * (p0_j.X - ox) + by * (p0_j.Y - oy)
    tj1 = bx * (p1_j.X - ox) + by * (p1_j.Y - oy)

    ai, zi = (ti0, ti1) if ti0 <= ti1 else (ti1, ti0)
    aj, zj = (tj0, tj1) if tj0 <= tj1 else (tj1, tj0)

    lo = max(ai, aj)
    hi = min(zi, zj)
    overlap_ft = (hi - lo) if hi > lo else 0.0

    length1, length2 = cache1[3], cache2[3]
    return overlap_ft, length1, length2


def _pair_symmetric_thickness_ft_cached(cache1, cache2):
    """Equivalente simetrico de `_distance_between_parallel_cached`: a folga
    perpendicular MEDIA entre as duas faces, medida so' no trecho em que as
    duas realmente se encaram (a sobreposicao mutua no referencial de
    `_pair_frame_cached`), em vez do ponto medio de UMA das duas linhas -
    que pode estar metros fora desse trecho (caso real medido no
    PLANO_ETAPA_2G.md, item D.2: fragmento de 8,43 cm inclinado 2,75 graus
    ao lado de uma face de 152 cm). Quando as duas faces nao se sobrepoem no
    referencial (retas quase paralelas mas sem trecho comum), cai no
    fallback E_bis (folga na bissetriz entre os dois pontos medios) - guarda
    defensiva, nunca exercida pelos 569 candidatos medidos na 2G (item G.3).
    Ver PLANO_ETAPA_2G.md item H.3 para o raciocinio fisico completo."""
    bx, by, nx, ny, ox, oy = _pair_frame_cached(cache1, cache2)

    p0_i, p1_i = cache1[0], cache1[1]
    p0_j, p1_j = cache2[0], cache2[1]

    ti0 = bx * (p0_i.X - ox) + by * (p0_i.Y - oy)
    si0 = nx * (p0_i.X - ox) + ny * (p0_i.Y - oy)
    ti1 = bx * (p1_i.X - ox) + by * (p1_i.Y - oy)
    si1 = nx * (p1_i.X - ox) + ny * (p1_i.Y - oy)
    tj0 = bx * (p0_j.X - ox) + by * (p0_j.Y - oy)
    sj0 = nx * (p0_j.X - ox) + ny * (p0_j.Y - oy)
    tj1 = bx * (p1_j.X - ox) + by * (p1_j.Y - oy)
    sj1 = nx * (p1_j.X - ox) + ny * (p1_j.Y - oy)

    lo = max(min(ti0, ti1), min(tj0, tj1))
    hi = min(max(ti0, ti1), max(tj0, tj1))

    if (hi - lo) <= 1e-12:
        m1, m2 = cache1[4], cache2[4]
        return abs(nx * (m1.X - m2.X) + ny * (m1.Y - m2.Y))

    def _sa(t0, s0, t1, s1, t):
        if abs(t1 - t0) < 1e-12:
            return s0
        return s0 + (s1 - s0) * (t - t0) / (t1 - t0)

    g_lo = abs(_sa(ti0, si0, ti1, si1, lo) - _sa(tj0, sj0, tj1, sj1, lo))
    g_hi = abs(_sa(ti0, si0, ti1, si1, hi) - _sa(tj0, sj0, tj1, sj1, hi))
    return (g_lo + g_hi) * 0.5


# --- CR-2F-C (PAIR_GREEDY_INDEX_DEPENDENCE) ---------------------------------
#
# O desempate final de `find_wall_pairs` (CR-1, ver `sort_key` em
# `wall_pairing.py`) terminava em `(i, j)` - a POSICAO de cada linha na
# lista de entrada. Isso garante DETERMINISMO (mesma lista -> mesmo
# resultado), mas nao INVARIANCIA A' ORDEM: a mesma geometria, renumerada,
# pode trocar qual dos dois candidatos empatados (mesmo thickness_rank,
# overlap_ratio e overlap_ft) vence. Medido no censo real (2.868 linhas
# mescladas, predicados ja' simetricos do CR-2F-B): 84 grupos de empate,
# 336 linhas disputadas - renumerar a lista muda 1-2 pares aceitos.
#
# `_line_identity_key_cached` substitui `(i, j)` por uma chave GEOMETRICA
# canonica: os dois endpoints da linha em cm, arredondados a 0,01cm (abaixo
# de qualquer tolerancia usada em `find_wall_pairs`), com o menor primeiro -
# portanto invariante ao indice da linha na lista E ao sentido em que ela
# foi desenhada. O par usa o MENOR das duas chaves de linha primeiro (ver
# uso em `find_wall_pairs`), o que torna o desempate tambem invariante a
# qual das duas linhas entrou como `cache1`/`cache2`. Medido: 0 diferencas
# no conjunto de pares aceitos em 5 permutacoes de 2.868 linhas (antes: 1-2
# pares mudavam por permutacao).

def _line_identity_key_cached(cache, nd=2):
    """Chave geometrica canonica de UMA linha (nd=2 -> 0,01cm de
    precisao) - nao depende do indice da linha na lista nem do sentido em
    que foi desenhada (o endpoint menor, em ordem lexicografica, vem
    primeiro)."""
    scale = 100.0 / FEET_PER_METER
    p0, p1 = cache[0], cache[1]
    a = (round(p0.X * scale, nd), round(p0.Y * scale, nd))
    b = (round(p1.X * scale, nd), round(p1.Y * scale, nd))
    return (a, b) if a <= b else (b, a)


# --- CR-2F-A (MERGE_RELATION_ASYMMETRY) -------------------------------------
#
# `get_distance_between_parallel_lines` / `_distance_between_parallel_cached`
# medem o PONTO MEDIO da PRIMEIRA linha contra a RETA INFINITA da segunda.
# Isso nao e' simetrico: `_are_parallel_cached` aceita ate' 2,87 graus de
# desvio, e nessa faixa `d(A,B)` e `d(B,A)` projetam o MESMO vetor sobre
# normais DIFERENTES - a diferenca cresce com a distancia entre os pontos
# medios. Como quem entra como primeiro argumento e' so' a POSICAO na lista,
# a relacao de compatibilidade que decide o agrupamento passa a depender da
# ordem da entrada, nao so' da geometria.
#
# Censo medido no projeto real (9.258 segmentos de CAD, 281.162 pares
# proximos, ver nuvem/benchmark/diagnostics_2j/):
#   - 393 pares em que o VEREDITO de compatibilidade muda com a direcao;
#   - pior |d(A,B) - d(B,A)| = 182,96 cm;
#   - caso minimo: d(A,B) = 173,4015 cm (incompativel) contra
#     d(B,A) = 0,0196 cm (compativel) - razao 8.841x, entre um fragmento de
#     4,22 cm e uma linha de 65,00 cm cujos pontos medios distam 36,1 m.
# E, ja' na ordem de producao: 39 fragmentos deslocados acima da propria
# tolerancia de 0,20 cm, 21 acima de 10 cm, pior deslocamento 159,14 cm.
#
# A CORRECAO (estrategia T2 do RELATORIO_ETAPA_2F.md item T, aprovada pelo
# usuario em 2026-09-01) e' exigir a compatibilidade nas DUAS direcoes:
#
#     max(d(A,B), d(B,A)) <= tolerancia
#
# que e' o mesmo que `d(A,B) <= tol E d(B,A) <= tol`. As duas funcoes abaixo
# expoem exatamente essa propriedade como um PREDICADO (e nao como uma
# distancia), por dois motivos:
#
#   1. A conjuncao e' COMUTATIVA, entao a simetria e' exata em IEEE-754 -
#      nao depende de nenhum epsilon nem de desempate.
#   2. Permite CURTO-CIRCUITO: quando a primeira direcao ja' reprova, a
#      segunda nem e' calculada. Na passada 1 do merge (~7,9 M avaliacoes
#      contra uma tolerancia de 2 mm) a esmagadora maioria dos pares reprova
#      logo na primeira, entao o custo extra so' incide sobre os pares que
#      realmente sao candidatos.
#
# CADA direcao continua sendo medida pela MESMA primitiva de sempre, bit a
# bit - o que muda e' so' passar a exigir as duas. As primitivas assimetricas
# seguem intactas e em uso pelos DIAGNOSTICOS que nao criam geometria
# (`scan_possible_missed_bonecas`, `classify_unused_line_reason`,
# `scan_candidate_thicknesses_cm`).
#
# ESCOPO: o CR-2F-A entrega a PROPRIEDADE `compat(A,B) == compat(B,A)`. Ele
# NAO torna o merge invariante a' ordem da lista - a relacao continua NAO
# TRANSITIVA e o agrupamento continua sendo ESTRELA (quem sai do `pop(0)`
# vira a base e arrasta quem for compativel COM ELA). Isso e' o CR-2F-D, e
# esta' medido: mesmo com a relacao simetrica, permutar a entrada ainda muda
# o conjunto de linhas mescladas. Ver REGRAS_MODULACAO_BLOCOS.md 26.9.

def _symmetric_within_distance_cached(cache1, cache2, tolerance_ft):
    """`max(d(1,2), d(2,1)) <= tolerance_ft`, com as duas direcoes medidas
    por `_distance_between_parallel_cached` e avaliadas com curto-circuito.

    E' a versao SIMETRICA do teste de compatibilidade usado pelo merge:
    trocar `cache1` por `cache2` devolve exatamente o mesmo booleano, porque
    o `and` de baixo e' comutativo e cada parcela e' a mesma conta com os
    argumentos trocados. Ver o bloco CR-2F-A acima."""
    if _distance_between_parallel_cached(cache1, cache2) > tolerance_ft:
        return False
    return _distance_between_parallel_cached(cache2, cache1) <= tolerance_ft


def symmetric_lines_within_distance(l1, l2, tolerance_ft):
    """Gemea de `_symmetric_within_distance_cached` para os sitios que
    trabalham direto com `Line` (sem o cache de `_line_geom_cache`): a MESMA
    propriedade `max(d(1,2), d(2,1)) <= tolerance_ft`, medida pela primitiva
    `get_distance_between_parallel_lines`.

    As duas existem separadas para que cada sitio continue usando a MESMA
    primitiva numerica que ja' usava (a versao cacheada reconstroi o ponto
    medio como `p0 + direcao * (comprimento / 2)`, a de `Line` usa
    `Evaluate(0.5, True)` - matematicamente identicas, ver `_line_geom_cache`).
    O teste `INV-MERGE-SYM-003` prende as duas a' mesma propriedade, para
    que nao possam divergir no futuro."""
    if get_distance_between_parallel_lines(l1, l2) > tolerance_ft:
        return False
    return get_distance_between_parallel_lines(l2, l1) <= tolerance_ft


def _xy_deviation_ft(curve_a, curve_b):
    """Maior distancia, medida SO' no plano XY (planta), entre as pontas
    correspondentes de duas linhas - testando as duas correspondencias
    possiveis (inicio-com-inicio e inicio-com-fim) e devolvendo a menor
    delas, porque o Revit pode devolver a curva de localizacao de uma
    parede com o sentido invertido em relacao a curva que foi passada na
    criacao.

    Ignora Z deliberadamente: a linha calculada a partir do CAD carrega a
    elevacao do proprio CAD, enquanto a curva de localizacao da parede
    criada fica na elevacao do NIVEL de insercao - comparar Z acusaria uma
    "diferenca" enorme que nao tem nada a ver com o alinhamento em planta,
    que e' o que esta sendo verificado aqui."""
    def xy(p):
        return XYZ(p.X, p.Y, 0.0)

    a0, a1 = xy(curve_a.GetEndPoint(0)), xy(curve_a.GetEndPoint(1))
    b0, b1 = xy(curve_b.GetEndPoint(0)), xy(curve_b.GetEndPoint(1))

    same_order = max(a0.DistanceTo(b0), a1.DistanceTo(b1))
    reversed_order = max(a0.DistanceTo(b1), a1.DistanceTo(b0))
    return min(same_order, reversed_order)


def _axis_offset_error_ft(centerline, l1, l2):
    """Mede o quanto `centerline` se desvia de ficar EXATAMENTE a meio
    caminho entre `l1` e `l2` - a propria definicao de "eixo central" - nas
    duas pontas do eixo.

    Em cada ponta, compara a distancia ate' `l1` com a distancia ate' `l2`:
    se o eixo esta' corretamente centralizado, as duas devem ser IGUAIS
    (ambas valem metade da espessura medida), entao a DIFERENCA entre elas
    e' zero. Usada como autoverificacao geometrica de create_centerline
    (ver find_wall_pairs, etapa de validacao final) - independe de qualquer
    comportamento do Revit (WallType, Linha de Referencia etc., que sao
    verificados separadamente em get_or_create_wall_type): mede so' se o
    ALGORITMO calculou o eixo certo a partir das duas linhas do CAD.

    Devolve o maior desvio absoluto (em pes) encontrado entre as duas
    pontas."""
    worst = 0.0
    for idx in (0, 1):
        p = centerline.GetEndPoint(idx)
        dist_to_l1 = p.DistanceTo(project_point_on_line(p, l1))
        dist_to_l2 = p.DistanceTo(project_point_on_line(p, l2))
        worst = max(worst, abs(dist_to_l1 - dist_to_l2))
    return worst


def _pair_frame_lines(l1, l2):
    """Referencial 2D SIMETRICO do par (l1, l2), a partir das duas `Line`:
    base = bissetriz das duas direcoes (orientadas para o mesmo lado),
    normal = perpendicular a' base, origem = ponto medio entre os dois
    pontos medios. Devolve (bx, by, nx, ny, ox, oy).

    E' a MESMA construcao geometrica de `_pair_frame_cached` (CR-2F-B, ver
    a prova de simetria em nuvem/benchmark/PLANO_ETAPA_2G.md item H.1) -
    aquela trabalha sobre o cache de `_line_geom_cache` (usado nos lacos
    O(n^2) de `find_wall_pairs`), esta trabalha sobre as `Line` cruas, que
    e' o que `create_centerline` recebe. Trocar l1<->l2 devolve o mesmo
    referencial, ou o mesmo com os dois eixos negados - e as projecoes que
    consomem o referencial absorvem essa troca de sinal (diferencas e
    `min`/`max` de projecao).

    Tudo em float puro sobre os componentes dos pontos (nunca um XYZ
    intermediario): e' o que faz o eixo simetrico custar MENOS que a versao
    anterior, apesar de projetar quatro pontas em vez de amostrar tres
    pontos (medido: -47%, ver PLANO_ETAPA_2I_CR_2F_E.md item 8)."""
    p0, p1 = l1.GetEndPoint(0), l1.GetEndPoint(1)
    q0, q1 = l2.GetEndPoint(0), l2.GetEndPoint(1)

    d1x, d1y = p1.X - p0.X, p1.Y - p0.Y
    n1 = math.hypot(d1x, d1y)
    if n1 > 1e-12:
        d1x, d1y = d1x / n1, d1y / n1
    d2x, d2y = q1.X - q0.X, q1.Y - q0.Y
    n2 = math.hypot(d2x, d2y)
    if n2 > 1e-12:
        d2x, d2y = d2x / n2, d2y / n2

    s = 1.0 if (d1x * d2x + d1y * d2y) >= 0.0 else -1.0
    bx, by = d1x + d2x * s, d1y + d2y * s
    nb = math.hypot(bx, by)
    if nb < 1e-9:
        bx, by = d1x, d1y
    else:
        bx, by = bx / nb, by / nb

    nx, ny = -by, bx
    ox = (p0.X + p1.X + q0.X + q1.X) * 0.25
    oy = (p0.Y + p1.Y + q0.Y + q1.Y) * 0.25
    return bx, by, nx, ny, ox, oy


def _interval_in_frame(frame, line):
    """Intervalo [t_lo, t_hi] que a linha ocupa ao longo da BASE do
    referencial, e a coordenada perpendicular MEDIA dela. Devolve
    (t_lo, t_hi, s_medio). Nao depende do sentido em que a linha foi
    desenhada (o `min`/`max` absorve a inversao)."""
    bx, by, nx, ny, ox, oy = frame
    a, b = line.GetEndPoint(0), line.GetEndPoint(1)
    ax, ay = a.X - ox, a.Y - oy
    bx_, by_ = b.X - ox, b.Y - oy
    ta = bx * ax + by * ay
    tb = bx * bx_ + by * by_
    sa = nx * ax + ny * ay
    sb = nx * bx_ + ny * by_
    return (ta if ta <= tb else tb), (tb if ta <= tb else ta), (sa + sb) * 0.5


def _axis_offset_in_frame(frame, l1, l2):
    """Coordenada perpendicular do EIXO no referencial: o meio caminho
    entre as duas faces. Media das duas coordenadas perpendiculares medias -
    simetrica por construcao (trocar l1<->l2 nao muda a media)."""
    _t0a, _t1a, s1 = _interval_in_frame(frame, l1)
    _t0b, _t1b, s2 = _interval_in_frame(frame, l2)
    return (s1 + s2) * 0.5


def _line_span_key(line):
    """Chave geometrica canonica de UMA linha em PES (mesma ideia de
    `_line_identity_key_cached`, que trabalha em cm sobre o cache) - usada
    APENAS para desempatar duas faces de comprimento exatamente igual em
    `create_centerline`. Nesse empate os dois intervalos ja' sao identicos,
    entao a escolha nao muda o eixo: a chave existe so' para o codigo nao
    ter um ramo indefinido."""
    p0, p1 = line.GetEndPoint(0), line.GetEndPoint(1)
    a = (p0.X, p0.Y)
    b = (p1.X, p1.Y)
    return (a, b) if a <= b else (b, a)


def create_centerline(l1, l2, max_extension_ft):
    """Gera a linha do eixo central entre duas linhas paralelas do CAD.

    O eixo cobre a UNIAO do alcance das duas linhas (nao apenas o alcance
    de uma delas): em cada ponta, usa a que for MAIS LONGA das duas faces
    pareadas. Isso evita que a parede nasca curta num encontro em L ou T
    so' porque, naquele ponto, uma das duas faces do CAD (interna/externa)
    foi desenhada um pouco mais curta que a outra - a face mais longa
    sempre prevalece, entao a parede chega ate' o ponto de conexao
    correto em vez de deixar um recuo/mordida no canto.

    Essa extensao, porem, e' LIMITADA a `max_extension_ft` alem do proprio
    alcance da face MAIS LONGA em cada ponta: sem esse teto, um pareamento
    equivocado (uma linha bem mais longa que apenas passa perto/cruza ali)
    faria o eixo disparar muito alem dos limites reais desenhados no CAD.
    Um encontro T/L legitimo normalmente precisa de pouca extensao (da ordem
    da espessura da parede perpendicular que chega ali) - bem menor que esse
    teto.

    --- CR-2F-E (CENTERLINE_ARGUMENT_ASYMMETRY) -------------------------

    ATE' 2026-09-01 esta funcao ancorava tudo em `l1`: o eixo comecava em
    `p0` de `l1`, o intervalo era `[0, len(l1)]` e `l2` so' podia ESTENDER,
    no maximo `max_extension_ft` por ponta. **Quem entrava como `l1` decidia
    o comprimento da parede** - e `l1` e' simplesmente a linha de indice
    menor na lista de entrada de `find_wall_pairs`, ou seja, a ordem em que
    o CAD foi lido.

    A regra da UNIAO acima ja' estava escrita neste docstring, mas o codigo
    so' a cumpria quando `l1` por acaso ja' era a face mais longa. Medido nos
    199 pares aceitos do benchmark real (Etapa 2I, ver
    nuvem/benchmark/PLANO_ETAPA_2I_CR_2F_E.md):

      - `create_centerline(A,B) != create_centerline(B,A)` em **47 pares
        (23,6%)**, com desvio de ate' **2.121,71 cm** (o mesmo par produzia
        uma parede de 1,56 m ou de 43,9 m);
      - **14 pares** mudavam tambem so' invertendo o SENTIDO dos endpoints
        de `l1` (`Line(p0,p1)` contra `Line(p1,p0)`) - invariancia
        DIFERENTE da anterior, e que nunca havia sido medida;
      - era a UNICA camada do Wall Modeling que ainda dependia da ordem da
        lista (as camadas de candidatos e de pares aceitos ja' estavam
        congeladas pelo CR-2F-B e pelo CR-2F-C): **22 a 29 eixos** mudavam
        por permutacao, e com eles as paredes finais.

    Duas fontes, ambas medidas por ablacao: o INTERVALO ancorado em `l1`
    (33 das 47 divergencias e 100% dos desvios grandes) e o deslocamento
    perpendicular amostrado SOBRE `l1` (as outras 14, ate' 10,29 cm). A
    DIRECAO ja' era simetrica - a bissetriz abaixo e' anterior a esta
    correcao e os 47 pares divergentes tinham todos a mesma direcao.

    **Correcao:** construir o eixo num referencial que NAO tem lado
    (`_pair_frame_lines` - a bissetriz das duas direcoes, com origem no
    meio das quatro pontas) e escolher a face de referencia pela GEOMETRIA
    (o COMPRIMENTO), nao pela posicao na lista. Resultado medido: 0
    divergencias de ordem dos argumentos, 0 de sentido dos endpoints e 0 em
    5 permutacoes das 2.868 linhas do benchmark; erro medio de
    centralizacao (`_axis_offset_error_ft`) de 0,0178 cm para 0,0119 cm; e
    custo -47%, por trabalhar em float puro no referencial em vez de
    construir XYZ intermediarios.

    **E' PROIBIDO "resolver" esta assimetria ordenando (l1, l2) por uma
    chave canonica e chamando a formula antiga.** Medido: isso zera a
    variacao mas PIORA a geometria - o erro de centralizacao vai de 1,14 cm
    para 21,33 cm no pior caso (7,1x na media), porque fixar a referencia
    escolhe sistematicamente a resposta menos centrada das duas; e deixa de
    pe' a invariancia ao sentido dos endpoints. Ver
    REGRAS_MODULACAO_BLOCOS.md 26.8.7.6.
    """
    frame = _pair_frame_lines(l1, l2)

    t1_lo, t1_hi, _s1 = _interval_in_frame(frame, l1)
    t2_lo, t2_hi, _s2 = _interval_in_frame(frame, l2)

    # Face de REFERENCIA: a mais longa (medida no referencial, que e' o
    # mesmo para as duas ordens). Empate exato -> chave geometrica canonica,
    # e nesse caso os dois intervalos sao identicos, entao a escolha nao
    # muda o eixo.
    len1, len2 = t1_hi - t1_lo, t2_hi - t2_lo
    if abs(len1 - len2) <= 1e-9:
        ref_is_l1 = _line_span_key(l1) <= _line_span_key(l2)
    else:
        ref_is_l1 = len1 > len2
    ref_lo, ref_hi = (t1_lo, t1_hi) if ref_is_l1 else (t2_lo, t2_hi)

    # UNIAO do alcance das duas faces, limitada a `max_extension_ft` alem
    # do alcance da face de referencia em cada ponta.
    t_lo = max(min(t1_lo, t2_lo), ref_lo - max_extension_ft)
    t_hi = min(max(t1_hi, t2_hi), ref_hi + max_extension_ft)

    s_axis = _axis_offset_in_frame(frame, l1, l2)

    bx, by, nx, ny, ox, oy = frame
    x_start = ox + bx * t_lo + nx * s_axis
    y_start = oy + by * t_lo + ny * s_axis
    x_end = ox + bx * t_hi + nx * s_axis
    y_end = oy + by * t_hi + ny * s_axis

    if math.hypot(x_end - x_start, y_end - y_start) < 0.01:
        return None

    # Sentido CANONICO das pontas (a menor primeiro): sem isso, inverter o
    # sentido em que uma face foi desenhada no CAD ainda mudaria o sentido
    # da Line devolvida. O sentido nao muda a geometria da parede, mas muda
    # a IDENTIDADE do objeto para os estagios seguintes (deduplicate_walls,
    # extend_wall_ends_to_junctions, build_wall_graph), entao tem que ser
    # estavel como o resto.
    if (x_end, y_end) < (x_start, y_start):
        x_start, y_start, x_end, y_end = x_end, y_end, x_start, y_start

    # `l1` preserva a elevacao original do CAD (o eixo e' plano: as duas
    # faces vem do mesmo Layer, na mesma elevacao).
    z = l1.GetEndPoint(0).Z
    return Line.CreateBound(XYZ(x_start, y_start, z), XYZ(x_end, y_end, z))


def _opening_bridges_gap(p0, direction, gap_lo, gap_hi, openings, perp_tolerance_ft, width_slack_ft):
    """Verifica se existe, dentre `openings`, uma abertura REAL do projeto
    (porta/janela ja' inserida, com Largura_abertura/Altura_abertura/
    Peitoril) cujo centro projetado sobre a reta (p0, direction) caia
    dentro da quebra [gap_lo, gap_hi] entre dois fragmentos colineares, com
    distancia perpendicular plausivel (dentro de `perp_tolerance_ft`, a
    espessura maxima de parede aceita) e largura compativel com o tamanho
    da propria quebra (dentro de `width_slack_ft`, folga para jambas/
    enquadramento desenhados no CAD).

    Usada para religar fragmentos separados por um vao MAIOR que
    `gap_tolerance_ft` (ver _merge_collinear_cluster) quando esse vao e'
    genuinamente o vao de uma porta/janela - only entao, nunca para
    quebras sem nenhuma abertura real correspondente ali.

    A largura da abertura vem diretamente de `op["width_ft"]` (o parametro
    Largura_abertura, ja lido em get_opening_instances) - nao da bounding
    box 3D da instancia, que pode incluir moldura/enquadramento e outras
    geometrias que se estendem alem do vao real.

    IMPORTANTE: `op["center_xy"]` (ver get_opening_instances) fica sempre
    em Z=0, enquanto `p0` (ponto da linha do CAD) costuma estar na
    elevacao ABSOLUTA do nivel/import (Z != 0). Comparar os pontos
    originais faria XYZ.DistanceTo() somar essa diferenca de elevacao
    inteira na "distancia perpendicular", estourando sempre `perp_tolerance_ft`
    e fazendo esta funcao nunca religar nada - por isso `p0` e' achatado
    para Z=0 aqui antes de qualquer calculo de distancia (mesmo ajuste ja'
    feito em find_openings_on_line)."""
    p0_flat = XYZ(p0.X, p0.Y, 0.0)
    gap_span_ft = gap_hi - gap_lo
    for op in openings:
        center = op["center_xy"]
        t_center = (center - p0_flat).DotProduct(direction)
        if t_center < gap_lo or t_center > gap_hi:
            continue

        proj_point = p0_flat + direction * t_center
        if center.DistanceTo(proj_point) > perp_tolerance_ft:
            continue

        if abs(gap_span_ft - op["width_ft"]) > width_slack_ft:
            continue

        return True
    return False


def _merge_collinear_cluster(cluster, gap_tolerance_ft, openings, opening_perp_tolerance_ft, opening_width_slack_ft):
    """Recebe um grupo de linhas ja confirmadas como colineares entre si e
    devolve a(s) linha(s) reconstruida(s), religando fragmentos cujo
    espaco entre um e outro seja <= `gap_tolerance_ft` (tipicamente a
    quebra deixada por outra parede cruzando esta) OU que corresponda a
    uma ABERTURA real do projeto na mesma posicao/largura (ver
    _opening_bridges_gap) - o vao de uma porta/janela costuma ser desenhado
    no CAD como uma quebra genuina na linha da parede (bem maior que
    `gap_tolerance_ft`), mas fisicamente a parede E' continua ali (so' com
    um vao recortado verticalmente, nao uma interrupcao estrutural) -
    religar esse trecho e' o que permite depois recortar exatamente a
    altura certa do vao (find_openings_on_line/build_wall_segments) e
    preservar tanto a parede acima da verga quanto qualquer "boneca" curta
    de parede entre a porta e um canto/encontro proximo, que sem isso nunca
    teriam eixo nenhum de parede passando por ali. Fragmentos separados por
    um vao maior que nao corresponde a nenhuma abertura real permanecem
    como linhas distintas - nada e' religado nesse caso."""
    # DIRECAO de referencia: a do fragmento MAIS LONGO do cluster - nao
    # simplesmente `cluster[0]` (a ordem de chegada dos fragmentos, ditada
    # so' pela ordem de travessia da geometria do CAD, e' arbitraria).
    base = max(cluster, key=lambda line: line.GetEndPoint(0).DistanceTo(line.GetEndPoint(1)))
    base_p0 = base.GetEndPoint(0)
    direction = (base.GetEndPoint(1) - base_p0).Normalize()

    # POSICAO de referencia: media dos fragmentos PONDERADA PELO COMPRIMENTO
    # de cada um - nao a posicao do fragmento mais longo. Uma versao anterior
    # ancorava a reta reconstruida exatamente sobre o fragmento mais longo,
    # o que REALOCAVA lateralmente todos os demais fragmentos do grupo ate'
    # a reta dele (ver a nota extensa em COLLINEAR_MATCH_TOLERANCE_M: com a
    # tolerancia generosa de entao, isso deslocava bonecas em ~0,5cm em
    # plantas cujas linhas nao sao perfeitamente alinhadas).
    #
    # Com a tolerancia agora apertada (2mm), todo fragmento que chega aqui
    # ja' esta' comprovadamente sobre a mesma reta, entao esta media so'
    # distribui ruido sub-milimetrico em vez de deixar um unico fragmento
    # ditar a posicao de todos. A ponderacao por comprimento faz os
    # fragmentos longos (mais confiaveis, menos sensiveis a imprecisao de
    # desenho) pesarem mais que os curtos, sem que os curtos sejam
    # simplesmente descartados.
    total_weight = 0.0
    weighted_offset_sum = XYZ(0.0, 0.0, 0.0)
    for line in cluster:
        a_pt, b_pt = line.GetEndPoint(0), line.GetEndPoint(1)
        weight = a_pt.DistanceTo(b_pt)
        if weight < 1e-12:
            continue
        mid = (a_pt + b_pt) * 0.5
        # Componente PERPENDICULAR (em relacao a `direction`) do vetor que
        # vai da reta base ate' o meio deste fragmento.
        rel = mid - base_p0
        perp = rel - direction * rel.DotProduct(direction)
        weighted_offset_sum += perp * weight
        total_weight += weight

    p0 = base_p0 + (weighted_offset_sum / total_weight if total_weight > 1e-12 else XYZ(0.0, 0.0, 0.0))

    intervals = []
    for line in cluster:
        a = (line.GetEndPoint(0) - p0).DotProduct(direction)
        b = (line.GetEndPoint(1) - p0).DotProduct(direction)
        intervals.append((min(a, b), max(a, b)))
    intervals.sort()

    merged = []
    cur_lo, cur_hi = intervals[0]
    for lo, hi in intervals[1:]:
        if lo <= cur_hi + gap_tolerance_ft or _opening_bridges_gap(
            p0, direction, cur_hi, lo, openings, opening_perp_tolerance_ft, opening_width_slack_ft
        ):
            cur_hi = max(cur_hi, hi)
        else:
            merged.append((cur_lo, cur_hi))
            cur_lo, cur_hi = lo, hi
    merged.append((cur_lo, cur_hi))

    return [
        Line.CreateBound(p0 + direction * lo, p0 + direction * hi)
        for lo, hi in merged
        if hi - lo > 1e-6
    ]


def _cluster_axis(cluster):
    """Devolve (p0, direction) de referencia para um cluster de fragmentos
    colineares - mesma convencao usada em _merge_collinear_cluster (ponto
    inicial e direcao do fragmento MAIS LONGO do cluster) - para servir de
    eixo de projecao ao TESTAR uma possivel fusao entre dois clusters
    distintos (ver _clusters_bridge_via_opening). NAO decide a posicao
    final de nenhum fragmento - isso continua sendo feito, do mesmo jeito de
    sempre, por _merge_collinear_cluster depois que os clusters candidatos a
    fusao ja tiverem sido decididos."""
    base = max(cluster, key=lambda line: line.GetEndPoint(0).DistanceTo(line.GetEndPoint(1)))
    p0 = base.GetEndPoint(0)
    direction = (base.GetEndPoint(1) - p0).Normalize()
    return p0, direction


def _cluster_interval(cluster, p0, direction):
    """Projeta todos os pontos de `cluster` sobre o eixo (p0, direction) e
    devolve (t_min, t_max) - o intervalo ocupado pelo cluster nesse eixo."""
    ts = [
        (line.GetEndPoint(idx) - p0).DotProduct(direction)
        for line in cluster
        for idx in (0, 1)
    ]
    return min(ts), max(ts)


def _clusters_bridge_via_opening(cluster_a, cluster_b, bridge_tolerance_ft, openings,
                                  opening_perp_tolerance_ft, opening_width_slack_ft):
    """Verifica se dois clusters de fragmentos colineares DISTINTOS (cada um
    ja formado com a tolerancia apertada COLLINEAR_MATCH_TOLERANCE_FT - ver
    merge_collinear_fragments) na verdade pertencem a MESMA face de parede,
    apenas separados pelo vao de uma abertura real do projeto desenhada com
    um desalinhamento entre as jambas maior que os 2mm tolerados no
    agrupamento "cru", mas ainda dentro de `bridge_tolerance_ft` (ver
    OPENING_BRIDGE_TOLERANCE_M).

    So' devolve True quando HA uma abertura real cujo vao explica o espaco
    entre os dois clusters (ver _opening_bridges_gap) - nunca so' por
    proximidade/paralelismo, para nao reintroduzir o deslocamento lateral
    que a tolerancia apertada corrigiu em juncoes SEM nenhuma abertura no
    meio (ex.: cruzamento com outra parede)."""
    ref_a = max(cluster_a, key=lambda line: line.GetEndPoint(0).DistanceTo(line.GetEndPoint(1)))
    ref_b = max(cluster_b, key=lambda line: line.GetEndPoint(0).DistanceTo(line.GetEndPoint(1)))
    if not are_lines_parallel(ref_a, ref_b):
        return False
    # CR-2F-A: compatibilidade exigida nas DUAS direcoes (ver o bloco
    # CR-2F-A em geometry.py). Tem de ser o MESMO predicado do pre-filtro de
    # _bridge_clusters_via_openings, senao o pre-filtro (que so' pode
    # PARTICIONAR clusters que jamais se fundiriam) passaria a separar pares
    # que este teste ainda aceitaria.
    if not symmetric_lines_within_distance(ref_a, ref_b, bridge_tolerance_ft):
        return False

    p0, direction = _cluster_axis(cluster_a)
    lo_a, hi_a = _cluster_interval(cluster_a, p0, direction)
    lo_b, hi_b = _cluster_interval(cluster_b, p0, direction)

    if hi_a <= lo_b:
        gap_lo, gap_hi = hi_a, lo_b
    elif hi_b <= lo_a:
        gap_lo, gap_hi = hi_b, lo_a
    else:
        return False  # clusters se sobrepoem no eixo - nao e' um "gap" para religar

    return _opening_bridges_gap(
        p0, direction, gap_lo, gap_hi, openings, opening_perp_tolerance_ft, opening_width_slack_ft
    )


def _bridge_clusters_via_openings(raw_clusters, bridge_tolerance_ft, openings,
                                   opening_perp_tolerance_ft, opening_width_slack_ft):
    """Funde clusters distintos quando uma abertura real do projeto religar
    o espaco entre eles - mesma regra de _clusters_bridge_via_opening,
    repetida em cascata ate' nao haver mais nenhuma fusao possivel (ver a
    docstring de merge_collinear_fragments).

    PERFORMANCE: rodar essa cascata (que reavalia TODOS os pares restantes
    do zero a cada fusao aceita) sobre os clusters do Layer inteiro de uma
    vez custa O(fusoes * clusters^2), recalculando a linha de referencia de
    cada cluster (max() sobre o cluster) a cada par comparado, em cada
    restart - em Layers de CAD com milhares de fragmentos (comuns em
    plantas reais), isso e' o principal motivo do script ficar muito lento
    logo depois da etapa de aberturas (que fornece `openings`, usado
    aqui).

    _clusters_bridge_via_opening so' pode devolver True quando as linhas de
    referencia dos dois clusters sao PARALELAS e estao a no maximo
    `bridge_tolerance_ft` uma da outra - exatamente esse mesmo teste,
    barato e feito aqui UMA UNICA vez (com as linhas de referencia ja
    calculadas de antemao, em vez de recalculadas a cada comparacao),
    particiona os clusters em grupos (Union-Find) sem NUNCA poder separar
    dois clusters que de fato pudessem se fundir - clusters de grupos
    diferentes jamais passariam nesse teste de qualquer forma, com
    QUALQUER abertura. A cascata cara (a mesma de sempre, sem nenhuma
    mudanca de comportamento) so' roda entao DENTRO de cada grupo -
    tipicamente pequeno (fragmentos que podem pertencer a mesma face de
    parede), nunca sobre o Layer inteiro."""
    n = len(raw_clusters)
    if n <= 1:
        return raw_clusters

    ref_lines = [
        max(cluster, key=lambda line: line.GetEndPoint(0).DistanceTo(line.GetEndPoint(1)))
        for cluster in raw_clusters
    ]
    # Geometria de cada linha de referencia calculada uma unica vez (ver
    # PERFORMANCE em _line_geom_cache) - o teste abaixo compara cada
    # cluster contra TODOS os outros (O(n^2)), o que sem cache recalcularia
    # a direcao/ponto medio da MESMA linha de referencia repetidas vezes.
    ref_caches = [_line_geom_cache(ref_line) for ref_line in ref_lines]

    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(n):
        cache_i = ref_caches[i]
        for j in range(i + 1, n):
            cache_j = ref_caches[j]
            # CR-2F-A: mesmo predicado simetrico de
            # _clusters_bridge_via_opening (ver o bloco CR-2F-A acima).
            if (_are_parallel_cached(cache_i, cache_j) and
                    _symmetric_within_distance_cached(cache_i, cache_j,
                                                      bridge_tolerance_ft)):
                union(i, j)

    groups = {}
    for idx in range(n):
        groups.setdefault(find(idx), []).append(idx)

    result = []
    for member_idxs in groups.values():
        if len(member_idxs) == 1:
            result.append(raw_clusters[member_idxs[0]])
            continue

        # Cascata original, sem nenhuma alteracao de comportamento - so'
        # rodando sobre um grupo pequeno em vez do Layer inteiro.
        group_clusters = [raw_clusters[idx] for idx in member_idxs]
        merged_any = True
        while merged_any and len(group_clusters) > 1:
            merged_any = False
            for gi in range(len(group_clusters)):
                for gj in range(gi + 1, len(group_clusters)):
                    if _clusters_bridge_via_opening(
                        group_clusters[gi], group_clusters[gj], bridge_tolerance_ft,
                        openings, opening_perp_tolerance_ft, opening_width_slack_ft
                    ):
                        group_clusters[gi] = group_clusters[gi] + group_clusters[gj]
                        del group_clusters[gj]
                        merged_any = True
                        break
                if merged_any:
                    break
        result.extend(group_clusters)

    return result


def merge_collinear_fragments(lines, collinear_tolerance_ft, gap_tolerance_ft, openings,
                               opening_perp_tolerance_ft, opening_width_slack_ft,
                               opening_bridge_tolerance_ft=OPENING_BRIDGE_TOLERANCE_FT):
    """Reconstroi, a partir de fragmentos de linha colineares (mesma reta,
    testa-ponta ou levemente sobrepostos/afastados por ate
    `gap_tolerance_ft`, OU separados pelo vao real de uma abertura do
    projeto - ver _merge_collinear_cluster), o comprimento COMPLETO
    original de cada face de parede desenhada no CAD.

    CADs arquitetonicos costumam desenhar a face de uma parede QUEBRADA em
    varios segmentos exatamente nos pontos onde outra parede a cruza (T, L,
    Cruz +) OU onde ha' uma porta/janela - mesmo quando fisicamente e' uma
    unica parede continua. Sem recompor esses fragmentos numa linha unica
    antes de formar os pares, cada pedaco e' tratado isoladamente e pode
    ficar sem parceiro (a parede correspondente nunca chega a ser criada,
    dando a impressao de que ela foi "cortada" pela metade) - e, no caso
    especifico de uma porta, NENHUM eixo de parede chega a passar pelo
    vao dela, entao nem a "boneca" ao lado nem o preenchimento acima da
    verga tem onde nascer, mesmo que a logica de recorte por altura esteja
    correta.

    Feita em DUAS passadas:
      1. Agrupamento "cru", com a tolerancia APERTADA `collinear_tolerance_ft`
         (2mm) - idem ao comportamento original, preservando o alinhamento
         exato em juncoes/cruzamentos sem nenhuma abertura envolvida.
      2. Fusao adicional de clusters DISTINTOS da passada 1 quando (e so'
         quando) uma abertura real do projeto explica o espaco entre eles -
         ver _clusters_bridge_via_opening - usando a tolerancia mais
         generosa `opening_bridge_tolerance_ft`, para cobrir o desalinhamento
         de desenho tipico ao redor de portas/janelas reais (mais que 2mm,
         mas ainda claramente a MESMA face de parede).

    Esta funcao NAO recorta nada - faz o oposto: religa fragmentos que
    pertencem a mesma reta para restaurar o comprimento original antes de
    qualquer pareamento. O resultado dessas linhas reconstruidas e' o que
    alimenta find_wall_pairs, garantindo paredes de comprimento completo
    mesmo quando isso as faz atravessar/sobrepor outras paredes.
    """
    # Geometria de cada linha calculada uma unica vez (ver PERFORMANCE em
    # _line_geom_cache) - o agrupamento abaixo compara cada linha `base`
    # contra todas as `remaining`, o que sem cache recalcularia a direcao/
    # ponto medio da MESMA linha repetidas vezes.
    remaining = [(line, _line_geom_cache(line)) for line in lines]
    raw_clusters = []

    while remaining:
        base, base_cache = remaining.pop(0)
        cluster = [base]
        rest = []
        for other, other_cache in remaining:
            # CR-2F-A: a compatibilidade "colinear" passa a ser exigida
            # nas DUAS direcoes. Sem isso, medir a partir de `base` ou a
            # partir de `other` dava vereditos diferentes em 393 pares do
            # projeto real (ver o bloco CR-2F-A em geometry.py), e quem era
            # `base` era so' a posicao da linha na lista de entrada.
            if (_are_parallel_cached(base_cache, other_cache) and
                    _symmetric_within_distance_cached(base_cache, other_cache,
                                                      collinear_tolerance_ft)):
                cluster.append(other)
            else:
                rest.append((other, other_cache))
        remaining = rest
        raw_clusters.append(cluster)

    # Segunda passada (ver docstring): funde clusters distintos quando uma
    # abertura real religar o espaco entre eles - repete ate' nao haver mais
    # nenhuma fusao possivel, ja que fundir dois clusters pode abrir um novo
    # gap explicavel entre o resultado e um terceiro cluster vizinho. Ver
    # PERFORMANCE na docstring de _bridge_clusters_via_openings.
    raw_clusters = _bridge_clusters_via_openings(
        raw_clusters, opening_bridge_tolerance_ft, openings,
        opening_perp_tolerance_ft, opening_width_slack_ft
    )

    result = []
    for cluster in raw_clusters:
        result.extend(_merge_collinear_cluster(
            cluster, gap_tolerance_ft, openings, opening_perp_tolerance_ft, opening_width_slack_ft
        ))

    return result


def _line_pair_overlap_ft(line1, line2):
    """Calcula a sobreposicao (em pes), medida ao longo da direcao de
    `line1`, entre `line1` e a projecao de `line2` sobre essa mesma
    direcao.

    Devolve (overlap_ft, length1, length2): `length1`/`length2` sao os
    comprimentos originais de cada linha, usados por quem chamar para
    normalizar a sobreposicao como FRACAO da menor das duas (ver
    lines_overlap_enough e find_wall_pairs) - o que faz o criterio
    funcionar igualmente bem para uma parede de 6 metros ou para uma
    boneca de 12cm, sem depender de nenhum valor fixo em cm.
    """
    p0, p1 = line1.GetEndPoint(0), line1.GetEndPoint(1)
    direction = (p1 - p0).Normalize()
    length1 = p0.DistanceTo(p1)

    q0, q1 = line2.GetEndPoint(0), line2.GetEndPoint(1)
    length2 = q0.DistanceTo(q1)
    t_q0 = (q0 - p0).DotProduct(direction)
    t_q1 = (q1 - p0).DotProduct(direction)
    t2_lo, t2_hi = min(t_q0, t_q1), max(t_q0, t_q1)

    overlap_lo = max(0.0, t2_lo)
    overlap_hi = min(length1, t2_hi)
    overlap_ft = max(0.0, overlap_hi - overlap_lo)
    return overlap_ft, length1, length2


def lines_overlap_enough(line1, line2):
    """Confirma que duas linhas paralelas realmente correm lado a lado
    (representam a mesma parede), e nao apenas estao proximas e paralelas
    sem nenhuma relacao real entre si.

    Aceita o par quando a sobreposicao cobre pelo menos
    MIN_WALL_SEGMENT_OVERLAP_RATIO do comprimento da MENOR das duas linhas
    (ver a nota junto a essa constante para o motivo de usar uma FRACAO em
    vez de um piso fixo em cm) - um piso absoluto minusculo
    (MIN_WALL_SEGMENT_ABS_FLOOR_FT) ainda protege contra sobreposicoes
    numericamente degeneradas.

    Isso e' SOMENTE um criterio de validacao do pareamento - nao recorta,
    nao divide e nao gera "sobras" de nenhuma linha. Uma vez validado, o
    par usa as duas linhas INTEIRAS (ver create_centerline) para gerar a
    parede, preservando o comprimento completo mesmo que isso a faca se
    sobrepor a outras paredes em encontros em T, L, Cruz (+) ou qualquer
    outra configuracao. Sobreposicao entre paredes e' aceitavel e esperada;
    este script nao tenta elimina-la.
    """
    overlap_ft, length1, length2 = _line_pair_overlap_ft(line1, line2)
    if overlap_ft < MIN_WALL_SEGMENT_ABS_FLOOR_FT:
        return False
    shorter_length = min(length1, length2)
    if shorter_length < 1e-9:
        return False
    return (overlap_ft / shorter_length) >= MIN_WALL_SEGMENT_OVERLAP_RATIO
