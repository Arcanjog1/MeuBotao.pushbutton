# -*- coding: utf-8 -*-
"""PIPELINE OFICIAL DE ABERTURAS (2026-08-28, pedido explicito do usuario):

    PAREDE COMPLETA -> MODULACAO COMPLETA -> VALIDACAO -> RECORTE DAS
    ABERTURAS -> REMOCAO DOS BLOCOS CONFLITANTES -> AJUSTE MINIMO ->
    RECALCULO SO' DO NECESSARIO -> VALIDACAO FINAL

Ate' aqui o motor fazia o contrario: cada porta/janela virava uma FRONTEIRA
do preenchimento (`OPENING_LO`/`OPENING_HI` em `solve_wall_free_fill`) ANTES
de qualquer bloco existir, e cada pedaco entre duas fronteiras era resolvido
como um problema independente. O usuario reportou que essa fragmentacao e' a
causa-raiz dos erros de continuidade, alinhamento, amarracao, pilarete,
sobra e excesso de peca especial: uma parede de 8m com duas portas virava
tres problemas de 2m sem nenhuma memoria entre si.

Este modulo contem a aritmetica PURA da nova ordem. Ele nao decide layout de
bloco nenhum (isso continua sendo `_pier_ordered_layout` e familia, regras
inalteradas) - ele decide QUAIS pecas do layout continuo sobrevivem ao
recorte, QUAL e' a regiao minima que precisa ser recalculada por causa
disso, e QUAL e' o menor ajuste geometrico capaz de compatibilizar uma
abertura que nao coincide com a modulacao.

Modulo PURO: so' numeros em cm ao longo do eixo da parede. Nao conhece XYZ,
catalogo, Revit, nem o formato do candidato de bloco - por isso e' testavel
isoladamente e reutilizavel pelo modelador externo. Ver
`nuvem/REGRAS_MODULACAO_BLOCOS.md`, secao 23.
"""

from core.engine.modulation_math import (  # noqa: F401
    BLOCK_JOINT_CM, BLOCK_OPENING_JOINT_CM, PIER_MODULE_CM,
)

__all__ = [
    "OPENING_STRATEGY_SPLIT_FIRST", "OPENING_STRATEGY_CONTINUOUS_FIRST",
    "DEFAULT_OPENING_STRATEGY",
    "BLOCK_OUTSIDE_OPENING", "BLOCK_INSIDE_OPENING", "BLOCK_PARTIAL_OPENING",
    "OPENING_OVERLAP_TOLERANCE_CM", "OPENING_REPAIR_MAX_EXTRA_BLOCKS",
    "OPENING_FIT_TOLERANCE_CM", "MIN_REPAIR_SEGMENT_CM",
    "AXIS_OPENING_SHIFT_MAX_CM", "OPENING_WIDTH_INCREASE_MAX_CM",
    "BOND_STRIP_EDGE_EXEMPT_CM", "BOND_STRIP_OPENING_INFLUENCE_CM",
    "classify_extent_against_openings", "split_extents_by_openings",
    "opening_repair_regions", "region_solid_subsegments",
    "block_edges_cm", "joint_positions_from_extents",
    "minimum_opening_shift_cm", "minimum_opening_widening_cm",
    "plan_minimum_opening_adjustment",
]


# ---- qual estrategia de abertura o solver usa ---------------------------
#
# "split_first" e' o comportamento HISTORICO (a abertura fatia o eixo antes
# de existir bloco). Continua no codigo, e continua testado, porque e' a
# unica forma de comparar as duas ordens no MESMO projeto - mas NAO e' mais
# o padrao. O usuario foi explicito: "nao voltar a logica anterior... essa
# abordagem deve ser abandonada como estrategia principal".
OPENING_STRATEGY_SPLIT_FIRST = "split_first"
OPENING_STRATEGY_CONTINUOUS_FIRST = "continuous_first"
DEFAULT_OPENING_STRATEGY = OPENING_STRATEGY_CONTINUOUS_FIRST

# Classificacao de UMA peca contra o conjunto de vaos (item 18 do pedido:
# "nao utilizar apenas o ponto central do bloco - verificar a area/volume
# real de intersecao").
BLOCK_OUTSIDE_OPENING = "FORA"
BLOCK_INSIDE_OPENING = "DENTRO"
BLOCK_PARTIAL_OPENING = "PARCIAL"

# Sobreposicao (cm) abaixo da qual a intersecao e' ruido numerico, nao
# invasao de vao: um bloco que ENCOSTA na borda da abertura (junta de
# abertura = 0cm, ver BLOCK_OPENING_JOINT_CM) toca o vao em exatamente 0cm
# e precisa continuar sendo "FORA". Mesma ordem de grandeza das demais
# tolerancias de contato do motor.
OPENING_OVERLAP_TOLERANCE_CM = 0.2

# Quanto a sobra ao lado do vao pode desviar de "fecha exatamente na borda"
# e ainda contar como compativel - abaixo disso nao ha' o que reparar nem
# o que ajustar (item 13: "se a abertura ja' estiver compativel, nao
# alterar a parede").
OPENING_FIT_TOLERANCE_CM = 0.5

# Item 22 ("recalcular apenas o necessario"): quantas pecas INTEIRAS, ALEM
# das que o vao ja' derrubou, a regiao de reparo pode engolir de cada lado
# antes de desistir e partir para o ajuste geometrico. Cada expansao devolve
# ~39-54cm a mais de liberdade ao solver de pilarete; 3 pecas (~1,2m de cada
# lado) e' folga de sobra para qualquer sobra real, e mantem o reparo LOCAL
# em vez de virar "re-resolver a parede inteira" pela porta dos fundos.
OPENING_REPAIR_MAX_EXTRA_BLOCKS = 3

# Teto (cm) de deslocamento AUTOMATICO de uma abertura - pedido explicito
# do usuario: acima disso a correcao existe matematicamente mas e' grande
# demais para aplicar sozinha, o eixo inteiro vai para revisao manual (ver
# ETAPA 3B, solve_axis_opening_modulation/plan_axis_opening_fix, em
# wall_modeling.py). MOVIDO PARA CA' em 2026-08-28: o pipeline "parede
# completa primeiro" precisa do mesmo teto DENTRO do motor puro (ver
# plan_minimum_opening_adjustment), e duplicar o numero em dois arquivos e'
# exatamente como um teto acaba mudando so' num deles.
AXIS_OPENING_SHIFT_MAX_CM = 5.0

# Teto (cm) de AUMENTO de largura de abertura - ultimo recurso. Pedido
# explicito do usuario (2026-08-20): NUNCA reduzir, NUNCA passar deste teto,
# e sempre preferir a menor alteracao possivel dentre as combinacoes
# validas.
OPENING_WIDTH_INCREASE_MAX_CM = 5.0

# Zona (cm) em que uma peca PEQUENA (compensador/pastilha/meio bloco) ou
# ESPECIAL (B34/B54) e' considerada NORMAL, e nao "faixa vertical
# repetitiva": perto da ponta da parede, ou perto de uma abertura - e' a
# funcao natural dela ali. Usadas em DOIS lugares desde 2026-08-28:
#   - `audit_wall_bond_quality` (wall_modeling.py), que ISENTA a repeticao
#     nessas regioes - o uso historico;
#   - a escolha do layout do trecho CONTINUO (wall_stepper.py), que agora
#     PREFERE, entre composicoes igualmente validas, a que coloca a peca de
#     acerto dentro de uma dessas zonas em vez de no meio da parede.
# Estavam so' no primeiro; o segundo precisa exatamente do mesmo criterio,
# e um numero desses vivendo em dois arquivos e' um numero que muda so' num
# deles.
BOND_STRIP_EDGE_EXEMPT_CM = 25.0
BOND_STRIP_OPENING_INFLUENCE_CM = 60.0

# Trecho solido menor que isto entre o vao e a peca ancora nao e' um
# pilarete: e' uma sobra que nenhuma peca do catalogo preenche (a menor
# pastilha tem 4cm). Vira expansao da regiao de reparo, nunca um trecho
# para o solver tentar preencher.
MIN_REPAIR_SEGMENT_CM = PIER_MODULE_CM - 1.0


def classify_extent_against_openings(t_start_cm, t_end_cm, opening_intervals_cm,
                                     tolerance_cm=OPENING_OVERLAP_TOLERANCE_CM):
    """Classifica o CORPO de uma peca (o intervalo real [t_start, t_end] que
    ela ocupa no eixo, nunca so' o centro dela - item 18 do pedido) contra os
    vaos `opening_intervals_cm` ([(lo_cm, hi_cm), ...], em qualquer ordem).

    Devolve (classificacao, opening_index, overlap_cm):
      - (BLOCK_OUTSIDE_OPENING, None, 0.0) - nao invade vao nenhum (inclui
        a peca que so' ENCOSTA na borda do vao, que e' o caso normal);
      - (BLOCK_INSIDE_OPENING, i, overlap) - esta' inteira dentro do vao i;
      - (BLOCK_PARTIAL_OPENING, i, overlap) - atravessa a borda do vao i.
    Quando invade mais de um vao, devolve o de MAIOR sobreposicao (o
    resultado pratico e' o mesmo - qualquer invasao remove a peca)."""
    lo = min(t_start_cm, t_end_cm)
    hi = max(t_start_cm, t_end_cm)
    best = None
    for index, interval in enumerate(opening_intervals_cm or []):
        a = min(interval[0], interval[1])
        b = max(interval[0], interval[1])
        overlap = min(hi, b) - max(lo, a)
        if overlap <= tolerance_cm:
            continue
        inside = (lo >= a - tolerance_cm) and (hi <= b + tolerance_cm)
        kind = BLOCK_INSIDE_OPENING if inside else BLOCK_PARTIAL_OPENING
        if best is None or overlap > best[2]:
            best = (kind, index, overlap)
    if best is None:
        return (BLOCK_OUTSIDE_OPENING, None, 0.0)
    return best


def split_extents_by_openings(extents, opening_intervals_cm,
                              tolerance_cm=OPENING_OVERLAP_TOLERANCE_CM):
    """ETAPAS 7/8/9/10 do fluxo (identificar / deletar / nao recortar bloco).

    `extents` e' [(t_start_cm, t_end_cm), ...] das pecas JA' POSICIONADAS
    pela modulacao continua, na ordem em que aparecem. Devolve
    (kept_indexes, removed), com `removed` = [{"index", "kind",
    "opening_index", "overlap_cm"}, ...] - a peca que invade o vao e'
    REMOVIDA INTEIRA, nunca cortada nem redimensionada (item 10 do pedido:
    "o bloco e' uma unidade modular")."""
    kept = []
    removed = []
    for index, extent in enumerate(extents or []):
        kind, opening_index, overlap_cm = classify_extent_against_openings(
            extent[0], extent[1], opening_intervals_cm, tolerance_cm=tolerance_cm
        )
        if kind == BLOCK_OUTSIDE_OPENING:
            kept.append(index)
        else:
            removed.append({
                "index": index, "kind": kind,
                "opening_index": opening_index, "overlap_cm": overlap_cm,
            })
    return kept, removed


def opening_repair_regions(extents, opening_intervals_cm, seg_lo_cm, seg_hi_cm,
                           tolerance_cm=OPENING_OVERLAP_TOLERANCE_CM):
    """ETAPA "analisar sobras/pilaretes" + item 22 ("recalcular apenas o
    necessario"): agrupa as pecas derrubadas pelo recorte em REGIOES
    CONTIGUAS e devolve, para cada uma, a menor janela do eixo que precisa
    ser re-resolvida.

    `extents` sao as pecas do trecho continuo em ORDEM CRESCENTE de t;
    `seg_lo_cm`/`seg_hi_cm` sao os limites do proprio trecho (o que a
    modulacao continua tinha para preencher). Cada regiao e':

        {"lo": ancora esquerda (fim da ultima peca que sobreviveu, ou
                seg_lo_cm quando o vao derrubou a primeira peca do trecho),
         "hi": ancora direita (inicio da proxima peca que sobreviveu, ou
                seg_hi_cm),
         "left_anchor_is_block": True quando "lo" e' a face de um bloco
                (precisa de junta de argamassa), False quando e' a propria
                fronteira do trecho (o no'/ponta ja' embutiu a junta dela),
         "right_anchor_is_block": idem do outro lado,
         "removed_indexes": indices em `extents` das pecas derrubadas,
         "opening_indexes": vaos que caem nesta regiao}

    Duas aberturas proximas cujas pecas derrubadas se encostam (o caso do
    PILARETE ENTRE ABERTURAS, item 16) caem na MESMA regiao de proposito:
    o pilarete entre elas so' pode ser resolvido olhando as duas de uma
    vez."""
    _kept, removed = split_extents_by_openings(
        extents, opening_intervals_cm, tolerance_cm=tolerance_cm
    )
    if not removed:
        return []

    removed_indexes = sorted(item["index"] for item in removed)
    runs = []
    for index in removed_indexes:
        if runs and index == runs[-1][-1] + 1:
            runs[-1].append(index)
        else:
            runs.append([index])

    regions = []
    for run in runs:
        first, last = run[0], run[-1]
        if first > 0:
            lo_cm = max(extents[first - 1][0], extents[first - 1][1])
            left_is_block = True
        else:
            lo_cm = seg_lo_cm
            left_is_block = False
        if last < len(extents) - 1:
            hi_cm = min(extents[last + 1][0], extents[last + 1][1])
            right_is_block = True
        else:
            hi_cm = seg_hi_cm
            right_is_block = False
        opening_indexes = []
        for oi, interval in enumerate(opening_intervals_cm or []):
            a = min(interval[0], interval[1])
            b = max(interval[0], interval[1])
            if min(hi_cm, b) - max(lo_cm, a) > tolerance_cm:
                opening_indexes.append(oi)
        regions.append({
            "lo": lo_cm, "hi": hi_cm,
            "left_anchor_is_block": left_is_block,
            "right_anchor_is_block": right_is_block,
            "removed_indexes": list(run),
            "opening_indexes": opening_indexes,
        })
    return regions


def region_solid_subsegments(region, opening_intervals_cm, joint_cm=BLOCK_JOINT_CM,
                             min_length_cm=MIN_REPAIR_SEGMENT_CM):
    """Os trechos SOLIDOS que sobram dentro de uma regiao de reparo depois
    de descontar os vaos dela - e' o que o solver de pilarete de sempre vai
    preencher (item 21: "recalcular regiao afetada", nao a parede toda).

    Devolve {"segments": [...], "undersized": [...]}, cada entrada com
    {"lo", "hi", "leading_open", "trailing_open", "left_opening",
    "right_opening"}, ja' com a junta de argamassa descontada do lado que
    encosta num BLOCO (a ancora) e com junta ZERO do lado que encosta num
    VAO (BLOCK_OPENING_JOINT_CM) - a mesma convencao que
    `solve_wall_free_fill` sempre usou. `leading_open`/`trailing_open`
    dizem se aquela ponta e' "aberta" no sentido da secao 2 (onde o meio
    bloco B19 pode encostar).

    Uma sobra menor que `min_length_cm` NAO vira trecho: sai em
    `"undersized"` para o chamador expandir a regiao (nenhuma peca do
    catalogo preenche 2cm - insistir ali e' que fabricava pastilha onde nao
    cabia peca nenhuma)."""
    lo_cm = region["lo"] + (joint_cm if region.get("left_anchor_is_block") else 0.0)
    hi_cm = region["hi"] - (joint_cm if region.get("right_anchor_is_block") else 0.0)

    intervals = []
    for oi in region.get("opening_indexes") or []:
        interval = opening_intervals_cm[oi]
        intervals.append((min(interval[0], interval[1]), max(interval[0], interval[1]), oi))
    intervals.sort()

    segments = []
    undersized = []
    cursor_cm = lo_cm
    left_opening = None
    for a_cm, b_cm, oi in intervals:
        # O vao pode comecar antes da ancora (peca derrubada por um vao que
        # nasce fora desta regiao) - nesse caso nao ha' trecho solido aqui.
        seg_hi = min(a_cm, hi_cm)
        entry = {
            "lo": cursor_cm, "hi": seg_hi,
            "leading_open": left_opening is not None or not region.get("left_anchor_is_block"),
            "trailing_open": True,
            "left_opening": left_opening, "right_opening": oi,
        }
        if seg_hi - cursor_cm >= min_length_cm:
            segments.append(entry)
        elif seg_hi - cursor_cm > OPENING_FIT_TOLERANCE_CM:
            undersized.append(entry)
        cursor_cm = max(cursor_cm, b_cm)
        left_opening = oi

    entry = {
        "lo": cursor_cm, "hi": hi_cm,
        "leading_open": left_opening is not None or not region.get("left_anchor_is_block"),
        "trailing_open": not region.get("right_anchor_is_block"),
        "left_opening": left_opening, "right_opening": None,
    }
    if hi_cm - cursor_cm >= min_length_cm:
        segments.append(entry)
    elif hi_cm - cursor_cm > OPENING_FIT_TOLERANCE_CM:
        undersized.append(entry)

    return {"segments": segments, "undersized": undersized}


def block_edges_cm(extents, seg_lo_cm=None, seg_hi_cm=None):
    """Todas as FACES (inicio e fim) das pecas de um trecho, ordenadas e sem
    repeticao - o conjunto de posicoes em que a borda de uma abertura PODE
    cair sem deixar sobra nenhuma. Base do ajuste minimo (itens 11 a 13)."""
    edges = []
    for extent in extents or []:
        edges.append(min(extent[0], extent[1]))
        edges.append(max(extent[0], extent[1]))
    if seg_lo_cm is not None:
        edges.append(seg_lo_cm)
    if seg_hi_cm is not None:
        edges.append(seg_hi_cm)
    edges.sort()
    unique = []
    for value in edges:
        if not unique or abs(value - unique[-1]) > 1e-6:
            unique.append(value)
    return unique


def joint_positions_from_extents(extents, max_gap_cm=BLOCK_JOINT_CM * 2.0):
    """Centro das juntas de argamassa INTERNAS deduzidas da geometria REAL
    das pecas ja' posicionadas (duas pecas consecutivas separadas por, no
    maximo, `max_gap_cm`) - o equivalente de
    `_layout_internal_joint_positions_cm` para um conjunto que ja' passou
    pelo recorte e pelo reparo, onde o "layout" original nao existe mais.

    Duas pecas separadas por um VAO nao formam junta (o intervalo entre elas
    e' grande demais) - a mesma protecao de BOND_MAX_ADJACENT_GAP_CM na
    auditoria de amarracao, que existe justamente porque contar essa "junta
    fantasma" reprovava quase toda parede com abertura."""
    ordered = sorted(
        (min(a, b), max(a, b)) for a, b in (extents or [])
    )
    joints = []
    for i in range(len(ordered) - 1):
        gap = ordered[i + 1][0] - ordered[i][1]
        if -1e-6 <= gap <= max_gap_cm:
            joints.append(ordered[i][1] + gap / 2.0)
    return joints


def _nearest_edge_delta(edges_cm, value_cm, max_delta_cm):
    """Menor deslocamento (com sinal) que leva `value_cm` ate' uma das
    `edges_cm`, dentro de `max_delta_cm`. None quando nenhuma borda esta'
    ao alcance."""
    best = None
    for edge in edges_cm or []:
        delta = edge - value_cm
        if abs(delta) > max_delta_cm + 1e-9:
            continue
        if best is None or abs(delta) < abs(best) - 1e-9:
            best = delta
    return best


def minimum_opening_shift_cm(edges_cm, a_cm, b_cm, max_shift_cm,
                             tolerance_cm=OPENING_FIT_TOLERANCE_CM):
    """Item 12/13: menor deslocamento RIGIDO do vao [a, b] (largura
    preservada - a esquadria nao muda) que faz as DUAS bordas cairem em face
    de bloco. None quando nao existe um dentro de `max_shift_cm`.

    Minimiza |delta| de verdade (varre os candidatos reais gerados pelas
    faces, em ordem de |delta|), em vez de testar 1cm, 2cm, 3cm... - o
    resultado e' o que o usuario descreveu, sem depender de a resposta ser
    um numero inteiro de centimetros."""
    candidates = set()
    for edge in edges_cm or []:
        candidates.add(edge - a_cm)
        candidates.add(edge - b_cm)
    candidates.add(0.0)
    best = None
    for delta in sorted(candidates, key=lambda d: (abs(d), d)):
        if abs(delta) > max_shift_cm + 1e-9:
            continue
        left_ok = _nearest_edge_delta(edges_cm, a_cm + delta, tolerance_cm) is not None
        right_ok = _nearest_edge_delta(edges_cm, b_cm + delta, tolerance_cm) is not None
        if left_ok and right_ok:
            best = delta
            break
    return best


def minimum_opening_widening_cm(edges_cm, a_cm, b_cm, max_widen_cm,
                                tolerance_cm=OPENING_FIT_TOLERANCE_CM):
    """Ultimo recurso geometrico (item 12): alargar o vao ate' as faces de
    bloco mais proximas PARA FORA, mantendo a arquitetura o mais intacta
    possivel. Devolve (delta_esquerda, delta_direita) - os dois >= 0, cada
    um o quanto aquela borda precisa AVANCAR para fora - ou None quando nao
    cabe em `max_widen_cm`.

    Nunca REDUZ o vao: encolher a porta muda o produto especificado, o que o
    usuario nunca autorizou; alargar so' consome pilarete."""
    left = None
    for edge in sorted(edges_cm or [], reverse=True):
        if edge <= a_cm + tolerance_cm:
            left = a_cm - edge
            break
    right = None
    for edge in sorted(edges_cm or []):
        if edge >= b_cm - tolerance_cm:
            right = edge - b_cm
            break
    if left is None or right is None:
        return None
    if left > max_widen_cm + 1e-9 or right > max_widen_cm + 1e-9:
        return None
    return (max(0.0, left), max(0.0, right))


def plan_minimum_opening_adjustment(edges_cm, a_cm, b_cm, max_shift_cm, max_widen_cm,
                                    tolerance_cm=OPENING_FIT_TOLERANCE_CM):
    """ETAPA "ajustar a parede o minimo possivel" (itens 11 a 14) para UM
    vao, na ordem de prioridade do item 24 (a POSICAO da abertura vale mais
    que a modulacao dos blocos, entao mexer nela so' acontece depois de o
    chamador ja' ter tentado recalcular a regiao):

        1. {"kind": "none"}  - ja' compativel, nao alterar nada (item 13);
        2. {"kind": "shift", "delta_cm": d} - menor translacao do vao;
        3. {"kind": "widen", "delta_left_cm": .., "delta_right_cm": ..};
        4. None - nenhuma solucao dentro dos tetos: o chamador reporta
           CONFLITO em vez de fabricar uma modulacao errada (teste 9).
    """
    left_fits = _nearest_edge_delta(edges_cm, a_cm, tolerance_cm) is not None
    right_fits = _nearest_edge_delta(edges_cm, b_cm, tolerance_cm) is not None
    if left_fits and right_fits:
        return {"kind": "none", "delta_cm": 0.0}

    delta = minimum_opening_shift_cm(edges_cm, a_cm, b_cm, max_shift_cm,
                                     tolerance_cm=tolerance_cm)
    if delta is not None:
        return {"kind": "shift", "delta_cm": delta}

    widen = minimum_opening_widening_cm(edges_cm, a_cm, b_cm, max_widen_cm,
                                        tolerance_cm=tolerance_cm)
    if widen is not None:
        return {"kind": "widen", "delta_left_cm": widen[0], "delta_right_cm": widen[1]}
    return None
