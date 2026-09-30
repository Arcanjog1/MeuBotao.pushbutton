# -*- coding: utf-8 -*-
"""ARRANJO CONJUNTO DAS CORRIDAS DE PREENCHIMENTO (secao 60 de
REGRAS_MODULACAO_BLOCOS.md) - vazado menor do B34 entre fiadas.

Medido no BUTANTA (34 paredes, fiadas 0-11): das 316 violacoes que restavam
depois da orientacao da secao 52, 157 sao B34 sobre B39 e 114 sao B34 sobre B34
num deslocamento que so' alinharia com a orientacao OPOSTA - sinal de que a
posicao dos B34 dentro da corrida, e nao a rotacao, e' o que falta. O humano
resolve na ORDEM das mesmas pecas: parede 8284543, trecho 815-964 cm, o solver
assentava `B34 B39 B39 B34` e o humano `B34 B34 B39 B39`, encaixando a corrida de
B34 na corrida da fiada vizinha, deslocada ~20 cm e girada 180 graus.

O que este passe faz, parede por parede:

1. agrupa as fiadas FISICAS em familias (fiadas com a mesma fileira, peca por
   peca) e conta quantas vezes cada par de familias fica em fiadas vizinhas;
2. em cada corrida de preenchimento (pecas STANDARD_FILL encostadas, fora de
   no', canaleta e peca compartilhada entre familias), enumera as ordens
   DISTINTAS das MESMAS pecas - mesmas pontas, mesmas juntas, mesmo
   comprimento - e a orientacao dos B34 de cada ordem;
3. fica com a ordem que reduz ESTRITAMENTE as violacoes do vazado menor contra
   as familias vizinhas, sem piorar nenhuma guarda: face repetida entre fiadas
   vizinhas, junta empilhada em 3+ fiadas, compensadores encostados (regra #2 e
   56.2) e compensador longo como peca extrema da parede (secao 58);
4. repete ate' estabilizar (no maximo `MAX_PASSES`), entao a escolha de uma
   corrida enxerga a escolha ja' feita nas corridas vizinhas - a diferenca para
   a tentativa rejeitada da secao 57, que decidia cada corrida uma vez so',
   contra vizinhas que ainda iam se mover.

Geometria: o "vazado menor" e' a celula de menor area (`candidate_small_cell`,
secao 52), lida das `cells_world` de cada peca. Nenhum codigo de familia,
parede, comprimento ou coordenada especifica entra aqui. Deterministico
(paredes por indice, familias pela primeira fiada, corridas pela posicao,
ordens em ordem lexicografica, empate pela menor quantidade de pecas trocadas)
e idempotente (uma segunda passada nao encontra melhoria).
"""
import bisect
import collections

try:  # Revit / dubles dos testes
    from Autodesk.Revit.DB import XYZ
except Exception:  # pragma: no cover - so' fora do Revit sem dubles
    XYZ = None

from core.engine import small_void_alignment as _sva

B34_RUN_ARRANGEMENT_ENABLED = True
# O legado (strategy=None) fica IDENTICO a' main por padrao: ele nao refaz a
# auditoria de amarracao depois do solve. Ligar so' para medir o corpus legado.
B34_RUN_ARRANGEMENT_LEGACY = False
# SECAO 64.2: as pecas do REPARO de abertura (`OPENING_REPAIR_FILL`) entram nas
# corridas - jamba -> no' como UMA unidade. O reparo e' preenchimento comum para
# todos os efeitos (wall_stepper, OPENING_REPAIR_PLACEMENT_REASON), mas ficava
# congelado: a corrida parava na primeira peca de reparo e o arranjo nao
# alcancava as pecas junto da jamba. As pontas da corrida continuam fixas (a
# face da jamba nao se move); a orientacao dos compensadores e a validacao
# CHANNEL sao refeitas depois (secao 64.1) e entram na aceitacao por parede.
B34_RUN_OPENING_REPAIR_MOVABLE = True
_MOVABLE_REASONS = ("STANDARD_FILL", "OPENING_REPAIR_FILL")
MAX_ARRANGEMENTS_PER_RUN = 240
# SECAO 61: composicao de MESMO comprimento (a ate' 2 pecas trocadas, sem mais
# especiais), aceita por dominancia e, por parede, pelos validadores de producao.
B34_RUN_COMPOSITION_ENABLED = True
MAX_COMPOSITIONS_PER_RUN = 40
MAX_ARRANGEMENTS_PER_COMPOSITION = 60
# 3 desde a secao 63.2: `B39 B39 C09 -> B34 B34 B19` (ponta da parede 8284574
# junto a no' T, sem especial) so' existe tirando 3 pecas; sem a orientacao
# conjunta da 63 o 3 nao muda nada na BUTANTA (medido)
COMPOSITION_MAX_REMOVED = 3
COMPOSITION_MAX_ADDED = 3
JOINT_REGULAR_TOLERANCE_CM = 0.05
# SECAO 62: orientacao otima exata por parede. A descida gulosa da secao 52 gira
# uma peca (ou um par) por vez e para quando nenhuma melhora sozinha; em corridas
# longas de B34 encadeadas entre fiadas a orientacao tem de alternar ao longo da
# cadeia inteira, e um trecho "fora de fase" so' se corrige girando varias pecas
# juntas. A DP enxerga isso: o custo de cada B34-fonte depende so' da orientacao
# dele e dos B34 que podem cobrir o vazado dele (a menos de meia peca), entao,
# em ordem de posicao, cada fator envolve variaveis vizinhas.
B34_ORIENTATION_DP_ENABLED = True
ORIENTATION_DP_MAX_BAND = 12
# SECAO 63: orientacao CONJUNTA na avaliacao de cada ordem/composicao (60/61).
# A descida antiga girava so' os B34 da familia do trecho, um por vez; a ordem
# que o humano usa pode exigir girar JUNTO o B34 da fiada vizinha (vizinhos) e
# dois B34 de uma vez (pares). Medido na ponta da parede 8284574: a composicao
# sem especial valia 32 (pior que as 16 atuais) na descida antiga e 0 com os dois
# giros juntos. A 62 (DP) gira mas nao reordena - nenhuma das duas achava sozinha.
NEIGHBOUR_FLIPS_ENABLED = True
NEIGHBOUR_REACH_CM = 40.0
# pares de inversao (ver `_Wall._pair_flips`)
PAIR_FLIPS_ENABLED = True
PAIR_FLIP_REACH_CM = 25.0
# Duas etapas (custo: conjunta em todas as ordens = 342 s na bancada, contra
# 19 s): a descida barata avalia TODAS as ordens; a conjunta so' reavalia as
# REFINE_TOP_K que passam nas guardas geometricas (nao dependem de orientacao),
# nao dominaram, e cujo LIMITE INFERIOR de vazado (`_violations_lower_bound`)
# ainda pode dominar - ordenadas por esse limite. K=4 ja' da' o mesmo resultado
# de K=8/16 e da conjunta em todas.
REFINE_TOP_K = 4
# alcance para achar as fontes cobertas por uma peca (centro do vazado a ate'
# ~9 cm do centro do B34; folga para qualquer peca do catalogo)
COVER_REACH_CM = 30.0
MAX_PASSES = 3
RUN_MAX_GAP_CM = 2.5
FACE_TOLERANCE_CM = 0.6
EDGE_TOLERANCE_CM = 1.0
TOUCH_TOLERANCE_CM = 1.6
# Alcance do custo local de um trecho: o centro do vazado menor fica a menos de
# meia peca do centro dela, e a peca vizinha que o cobre tem no maximo 54 cm.
WINDOW_PAD_CM = 60.0
WALL_END_TOLERANCE_CM = 2.0
# Compensador a partir deste comprimento e' "longo" (C09); o humano nunca termina
# uma fiada com ele, mas termina com C04 (secao 58).
LONG_COMPENSATOR_MIN_CM = 6.0
CM_PER_FT = 30.48
# SECAO 84 (correcao do usuario, 2026-09-28): FAIXA DE COMPENSACAO NA JAMBA.
# Compensador (C09) e pastilha (C04) junto de porta/janela ficam ENCOSTADOS no
# vao e na MESMA faixa vertical em todas as fiadas da lateral, em vez de
# alternar entre "junto do vao" e "20/40/60 cm para dentro". As fiadas da
# lateral sao resolvidas EM CONJUNTO (familias de fiada), so' PERMUTANDO as
# pecas moveis da corrida jamba -> primeira peca fixa (nenhuma peca criada ou
# removida). Restricoes duras (nunca pioram): prisma dos vazados pela
# geometria real das celulas, vazado menor do B34 (secao 52), compensadores
# encostados, meio bloco perto de amarracao, compensador longo na ponta da
# parede, junta coincidente NOVA fora da faixa e junta empilhada em 3+ fiadas.
# A unica isencao e' a face INTERNA do compensador encostado na jamba.
JAMB_COMPENSATOR_ALIGNMENT_ENABLED = True
# alcance da corrida a partir da jamba = BOND_STRIP_OPENING_INFLUENCE_CM
JAMB_REACH_CM = 60.0
# encostado = OPENING_ALIGNED_TOUCH_TOLERANCE_CM (junta de 1 cm + arredondamento)
JAMB_TOUCH_TOLERANCE_CM = 2.0
# ponto logo DENTRO do vao para saber se a abertura corta esta fiada
JAMB_INSIDE_PROBE_CM = 2.0
# vazado alinhado entre fiadas: centro a ate' 2,0 cm do centro de um vazado da
# peca de baixo/cima (aparelho corrido real: B19 sobre B39 = 0,9 cm; B34 x B39
# chega a 1,75 cm - 1,5 cm cegava a medida)
PRISM_ALIGNED_DC_MAX_CM = 2.0
JAMB_MAX_ORDERS_PER_FAMILY = 120
JAMB_JOINT_MAX_COMBINATIONS = 4096
JAMB_DESCENT_ROUNDS = 4
# SECAO 85 (2026-09-29): a unidade da lateral alcanca a corrida movel inteira
# ate' a peca fixa (a outra paridade tambem chega na faixa), e as candidatas
# incluem COMPOSICOES de mesmo comprimento (+-1 peca) - prisma vem antes de
# "menos compensadores" no pedido do usuario.
JAMB_FULL_RUN_MAX_CM = 240.0
JAMB_UNIT_MAX_PIECES = 7
JAMB_COMPOSITION_ENABLED = True
JAMB_COMPOSITION_MAX_EXTRA = 1
JAMB_COMPOSITION_CODES = ("B39", "B34", "B19", "C09", "C04")
JAMB_MAX_COMPOSITION_ORDERS = 60
JAMB_UNIT_ROUNDS = 400
# SECAO 85 (pedido do usuario, 2026-09-29, segundo prompt): a coluna de vazados
# junto de cada jamba e' PERCURSO OBRIGATORIO (graute/vergalhao nas laterais de
# abertura e nos pilaretes): quebrada = composicao invalida; o recompositor nunca
# piora e, sem solucao, registra PRISM_REQUIRED_PATH_BROKEN.
JAMB_PATH_REACH_CM = 30.0
# SECAO 85 - pontos criticos COMPATIBILIZADOS: as fiadas CHEIAS logo acima da
# verga e logo abaixo do peitoril (o par de fiadas alternadas de cada lado) entram
# na unidade da lateral - "verifique o trecho acima da porta e sua relacao com a
# composicao lateral"; "fiadas equivalentes acima e abaixo seguem a mesma
# composicao; a abertura nao reinicia a modulacao". A corrida da ponte vai do
# lado do pilar ate' a primeira peca fixa e, sobre o vao, so' ate' o meio dele
# (cada jamba recompoe a sua metade).
JAMB_BRIDGE_ENABLED = True
JAMB_BRIDGE_COURSES = 2
# SECAO 85 - ordem dos pontos criticos: menor liberdade geometrica primeiro
# (pilarete entre duas aberturas, depois a corrida mais curta ate' peca fixa) e
# uma rodada LIMITADA de compatibilizacao: a unidade cujo percurso obrigatorio
# quebrou depois que uma vizinha mudou e' reavaliada (no maximo
# JAMB_COMPAT_ROUNDS vezes); o que nao fechar fica registrado.
JAMB_COMPAT_ROUNDS = 2
# SECAO 85 - coluna de vazado PRINCIPAL sobre vazado principal: largura comum
# acumulada >= 13,9 cm (a menor celula de bloco principal do catalogo real, o
# B19, tem 13,99). "Preservar o alinhamento dos vaos dos blocos principais":
# uma coluna que so' passa pelo vazado menor do B34 (8,99 x 10,76) passa no
# limiar, mas vale menos que uma coluna cheia.
PRISM_FULL_COLUMN_WIDTH_CM = 13.9
# SECAO 85 - alternativas antes de consolidar: estagio A = as K melhores
# composicoes das fiadas da JAMBA com as fiadas-ponte (acima da verga / abaixo
# do peitoril) transparentes; estagio B = para cada uma, descida nas fiadas-ponte
# com a regua completa. Orcamento limitado (nada se repete indefinidamente).
JAMB_ALT_TOPK = 3
JAMB_BRIDGE_OPTIONS_MAX = 40
JAMB_BRIDGE_DESCENT_ROUNDS = 1
# orcamento deterministico do estagio A (combinacoes das fiadas da jamba)
JAMB_ALT_MAX_EVAL = 4096
# SECAO 85.8 (correcao do usuario, 2026-09-30): o vazado MENOR do B34 so' passa
# sobre outro vazado menor (B34) ou o central do B54. Celula estreita (< 11,5 cm
# ao longo da parede - o vazado menor real tem 10,75) contra celula de vazado
# PRINCIPAL (> 13 cm) e' quebra, mesmo com 9 cm de area comum.
SMALL_CELL_MAX_CM = 11.5
MAIN_CELL_MIN_CM = 13.0
# SECAO 85.8: B19 fora de fechamento tambem em trecho SEM abertura (caixa de
# shaft W27/W33): recompoe a corrida movel em volta dele; o B54 entra como
# preenchimento SO' nessas unidades (autorizado pelo usuario em 2026-09-30:
# `B54 + C09` no trecho de 64 cm do shaft).
HALF_BLOCK_FIX_ENABLED = True
HALF_BLOCK_FIX_EXTRA_CODES = ("B54",)
# SECAO 85.8: canaleta U34 + pastilha onde cabem U39 exatas vira U39 (verga da W2)
CHANNEL_RUN_CLEANUP_ENABLED = True
# SECAO 85.9 (desenho do usuario, 2026-09-30, W4 pilarete 945-1144): "o uso dos
# blocos 34 para uma melhor modulacao e' aconselhavel". A fiada acima da verga /
# abaixo do peitoril SEGUE a grade da fiada da jamba de mesma paridade (pecas de
# fechamento junto da jamba - B19, compensador - nao sobem; sobre o vao a fiada e'
# continua) e o trecho sobre o vao fecha com B39/B34 exatos (6 x B34 absorvem os
# 10 cm de fase sem pastilha). A fiada da VERGA/contraverga entra na unidade da
# jamba: peca que comeca dentro da extensao original da canaleta vira U39/U34
# (a verga nunca encolhe); o resto segue a grade como bloco.
JAMB_GRID_FOLLOW_ENABLED = True
# SECAO 85.9 / 11.8: a junta do B19 de FECHAMENTO (encostado na jamba ativa, ou
# logo atras da faixa de compensadores encostada - excecao da secao 2) e' isenta
# na guarda de junta do recompositor, a mesma leitura da auditoria de producao
# (11.8: "B4, B9 e B19 podem ficar alinhados quando estao encostados nas
# aberturas") - mas SO' contra uma junta que nao e' de fechamento de B19 na outra
# fiada: B19 sobre B19 continua proibido (sem isso o pilarete da W5 virava
# `C04 | B19 | B39 | B19` nas duas paridades, a prumo). Caso medido: W5,
# pilarete 230-314 - o desenho do usuario (`C04 | B39 | B39` /
# `C04 | B19 | B39 | B19`) so' falhava em NEW_COINCIDENT_JOINT contra as pontas
# das vergas da fiada 11.
JAMB_CLOSURE_B19_JOINT_EXEMPT = True
# falhas que so' dependem das fiadas da jamba (a ponte/verga nao conserta):
# o estagio A ordena primeiro por elas - antes `B19 | B34 | C04 | C09` (pastilha
# nova) ficava no topo e empurrava a grade de B34 do usuario para o 88o lugar
JAMB_INTRINSIC_FAILURES = ("NEW_COMPENSATOR", "COMPENSATOR_OFF_JAMB", "HALF_BLOCK_NOT_ADMISSIBLE",
                           "ADJACENT_COMPENSATORS", "HALF_BLOCK_NEAR_TIE", "LONG_COMPENSATOR_AT_WALL_END")
JAMB_VERGA_MEMBER_ENABLED = True
# a corrida da ponte/verga cresce PRIMEIRO ate' a peca fixa do lado do pilar e so'
# depois sobre o vao, com teto proprio (W1: a grade da porta 8079007 so' fecha
# com 5 x B34 = 175 cm sobre o vao; o teto de 240 cm/7 pecas crescendo para os dois
# lados parava antes do B54 do T e antes da junta que fecha)
JAMB_BRIDGE_RUN_MAX_CM = 420.0
JAMB_BRIDGE_RUN_MAX_PIECES = 11
CHANNEL_OF_BLOCK = {"B39": "CHANNEL_U_39", "B34": "CHANNEL_U_34", "B19": "CHANNEL_U_19"}


class _Slot(object):
    __slots__ = ("lo", "hi", "code", "side", "movable", "node", "hollow", "orientable",
                 "void_off", "void_half", "compensator", "cells", "cell_side")

    def __init__(self):
        self.lo = self.hi = 0.0
        self.code = None
        self.side = 0
        self.movable = self.node = self.hollow = self.orientable = self.compensator = False
        self.void_off = self.void_half = None
        # SECAO 84: TODAS as celulas (deslocamento do centro de cada uma ate' o
        # centro da peca, meia largura) na orientacao `cell_side`
        self.cells = ()
        self.cell_side = 0

    @property
    def mid(self):
        return (self.lo + self.hi) / 2.0

    def copy(self):
        other = _Slot()
        for name in _Slot.__slots__:
            setattr(other, name, getattr(self, name))
        return other


def _is_channel_code(code):
    try:
        from core.engine import opening_reinforcement as _reinforcement
        return bool(_reinforcement.is_channel_code(code))
    except Exception:  # pragma: no cover - modulo sempre presente no motor
        return str(code or "").upper().startswith("CHANNEL")


def _axis(walls_to_create, wall_idx):
    from core.engine.wall_stepper import _wall_axis_and_length
    p0, _p1, wall_dir, length_ft, _t = _wall_axis_and_length(walls_to_create, wall_idx)
    return p0, wall_dir, length_ft * CM_PER_FT


def _extent_cm(cand, p0, wall_dir):
    from core.engine.wall_stepper import _candidate_t_range_on_wall
    a, b = _candidate_t_range_on_wall(cand, p0, wall_dir)
    return min(a, b), max(a, b)


def _void_geometry(cand, p0, wall_dir, lo, hi):
    """(deslocamento com sinal do centro da celula menor ate' o centro da peca,
    meia largura dela ao longo da parede) - ou (None, None) sem celula menor."""
    cell = _sva.candidate_small_cell(cand)
    if cell is None:
        return None, None
    pt = cell["point"]
    t_cell = ((pt.X - p0.X) * wall_dir.X + (pt.Y - p0.Y) * wall_dir.Y) * CM_PER_FT
    half = float(cell["size_local"][0]) * CM_PER_FT / 2.0
    return t_cell - (lo + hi) / 2.0, half


def _cells_geometry(cand, p0, wall_dir, lo, hi):
    """SECAO 84: ((deslocamento com sinal do centro de CADA celula ate' o centro
    da peca, meia largura), ...) lidos das `cells_world` REAIS da peca - a
    geometria da familia, nao uma suposicao pelo codigo."""
    mid = (lo + hi) / 2.0
    out = []
    for cell in cand.get("cells_world") or []:
        pt = cell["point"]
        t_cell = ((pt.X - p0.X) * wall_dir.X + (pt.Y - p0.Y) * wall_dir.Y) * CM_PER_FT
        out.append((t_cell - mid, float(cell["size_local"][0]) * CM_PER_FT / 2.0))
    out.sort()
    return tuple(out)


def _cell_centers(slot):
    """Centros (t_cm) das celulas de `slot` na orientacao ATUAL dele: a peca
    orientavel (B34) girada 180 graus espelha as celulas em torno do centro."""
    cells = slot.cells
    if not cells:
        return ()
    mid = (slot.lo + slot.hi) / 2.0
    if slot.orientable and slot.side and slot.cell_side and slot.side != slot.cell_side:
        return tuple(mid - off for off, _half in cells)
    return tuple(mid + off for off, _half in cells)


def _catalog_template(code, catalog):
    """Slot-modelo de `code` lido do CATALOGO (celulas locais, em pes, eixo X da
    peca ao longo da parede) - para codigos que ainda nao existem na parede."""
    entry = (catalog or {}).get(code) or {}
    length = float(entry.get("length_cm") or 0.0)
    if length <= 0.0:
        return None
    s = _Slot()
    s.code, s.lo, s.hi = code, 0.0, length
    s.compensator = bool(entry.get("is_compensator"))
    cells = entry.get("cells_local") or []
    s.hollow = bool(cells) and not s.compensator
    if len(cells) >= 2:
        ordered = sorted(cells, key=lambda c: float(c["size_local"][0]) * float(c["size_local"][1]))
        a0 = float(ordered[0]["size_local"][0]) * float(ordered[0]["size_local"][1])
        a1 = float(ordered[1]["size_local"][0]) * float(ordered[1]["size_local"][1])
        if a0 <= _sva.SMALL_VOID_MAX_AREA_RATIO * a1:
            s.void_off = float(ordered[0]["center_local"][0]) * CM_PER_FT
            s.void_half = float(ordered[0]["size_local"][0]) * CM_PER_FT / 2.0
            s.orientable = len(cells) == 2
    s.side = (1 if (s.void_off or 0.0) >= 0.0 else -1) if s.orientable else 0
    s.cells = tuple(sorted((float(c["center_local"][0]) * CM_PER_FT, float(c["size_local"][0]) * CM_PER_FT / 2.0)
                           for c in cells)) if s.hollow else ()
    s.cell_side = s.side
    return s


def _void_center(slot):
    if slot.void_off is None:
        return None
    if not slot.orientable:
        return slot.mid + slot.void_off
    return slot.mid + slot.side * abs(slot.void_off)


def _offers(slot, t, tol_cm):
    if not slot.hollow:
        return None
    c = _void_center(slot)
    if c is None:
        return False
    return c - slot.void_half - tol_cm <= t <= c + slot.void_half + tol_cm


def _first_hi_at_least(slots, t):
    """Indice da primeira peca com hi >= t (as pecas de uma fileira estao em
    ordem de posicao e nao se sobrepoem, entao hi tambem e' crescente)."""
    low, high = 0, len(slots)
    while low < high:
        middle = (low + high) // 2
        if slots[middle].hi + 1e-6 < t:
            low = middle + 1
        else:
            high = middle
    return low


def _covering(slots, t):
    i = _first_hi_at_least(slots, t)
    if i < len(slots) and slots[i].lo - 1e-6 <= t:
        return slots[i]
    return None


def _in_window(slots, lo, hi):
    """Pecas que tocam [lo, hi], em ordem (fatia: `lo` tambem e' crescente -
    uma lista em vez de gerador, que custava uma volta Python por peca)."""
    i = _first_hi_at_least(slots, lo)
    low, high = i, len(slots)
    while low < high:
        middle = (low + high) // 2
        if slots[middle].lo <= hi:
            low = middle + 1
        else:
            high = middle
    return slots[i:low]


def _violations_between(lower, upper, tol_cm, window=None):
    count = 0
    for src, dst in ((lower, upper), (upper, lower)):
        pieces = src if window is None else _in_window(src, window[0], window[1])
        for p in pieces:
            if not p.orientable:
                continue
            t = _void_center(p)
            h = _covering(dst, t)
            if h is not None and _offers(h, t, tol_cm) is False:
                count += 1
    return count


def _violations_lower_bound(lower, upper, tol_cm, window=None):
    """Limite INFERIOR das violacoes sobre qualquer orientacao das pecas moveis:
    conta so' o vazado que nenhuma combinacao de lado (da fonte e da peca que a
    cobre, quando moveis e orientaveis) alinha. Ignora o acoplamento entre pares
    (uma peca e' fonte e cobertura ao mesmo tempo), por isso e' so' limite."""
    count = 0
    for src, dst in ((lower, upper), (upper, lower)):
        pieces = src if window is None else _in_window(src, window[0], window[1])
        for p in pieces:
            if not p.orientable:
                continue
            p_sides = (-1, 1) if p.movable else (p.side,)
            saved_p = p.side
            aligned = False
            for p_side in p_sides:
                p.side = p_side
                t = _void_center(p)
                h = _covering(dst, t)
                if h is None:
                    aligned = True
                    break
                h_sides = (-1, 1) if (h.orientable and h.movable) else (h.side,)
                saved_h = h.side
                for h_side in h_sides:
                    h.side = h_side
                    if _offers(h, t, tol_cm) is not False:
                        aligned = True
                        break
                h.side = saved_h
                if aligned:
                    break
            p.side = saved_p
            if not aligned:
                count += 1
    return count


def _has_value_near(sorted_values, value, tolerance):
    """True se `sorted_values` tem algum valor a ate' `tolerance` de `value`."""
    i = bisect.bisect_left(sorted_values, value - tolerance)
    return i < len(sorted_values) and sorted_values[i] <= value + tolerance


def _internal_faces(slots, wall_len, edges, window=None):
    """Faces internas da fileira, sem ponta de parede nem borda de vao.
    `edges` tem de estar ORDENADA (feito uma vez em `_Wall`)."""
    out = []
    for s in (slots if window is None else _in_window(slots, window[0], window[1])):
        for f in (s.lo, s.hi):
            if f <= EDGE_TOLERANCE_CM or f >= wall_len - EDGE_TOLERANCE_CM:
                continue
            if _has_value_near(edges, f, EDGE_TOLERANCE_CM):
                continue
            out.append(f)
    out.sort()
    return out


def _coincident(fa, fb):
    j = n = 0
    for f in fa:
        while j < len(fb) and fb[j] < f - FACE_TOLERANCE_CM:
            j += 1
        if j < len(fb) and fb[j] <= f + FACE_TOLERANCE_CM:
            n += 1
    return n


def _compensator_guard(slots, wall_len):
    """Compensadores encostados (regra #2 e 56.2)."""
    n = 0
    for a, b in zip(slots, slots[1:]):
        if a.compensator and b.compensator and 0.0 <= b.lo - a.hi <= TOUCH_TOLERANCE_CM:
            n += 1
    return n


def _long_compensator_extremes(slots, wall_len):
    """Compensador LONGO como peca extrema da parede (secao 58). Guarda separada
    da de compensadores encostados: somadas, a busca trocava um par encostado
    por um C09 na ponta - e o humano nao faz nenhuma das duas."""
    n = 0
    if slots:
        first, last = slots[0], slots[-1]
        if first.compensator and first.hi - first.lo >= LONG_COMPENSATOR_MIN_CM and \
                first.lo <= WALL_END_TOLERANCE_CM:
            n += 1
        if last.compensator and last.hi - last.lo >= LONG_COMPENSATOR_MIN_CM and \
                last.hi >= wall_len - WALL_END_TOLERANCE_CM:
            n += 1
    return n


def _half_blocks_near_ties(slots, ties, half_code, max_gap_cm):
    """Meio bloco a ate' `max_gap_cm` de uma amarracao da parede - a MESMA
    regra de `HALF_BLOCK_NEAR_TIE` da auditoria de amarracao (regra #2)."""
    if not ties or not half_code:
        return 0
    n = 0
    for s in slots:
        if s.code != half_code:
            continue
        for t in ties:
            gap = s.lo - t if t < s.lo else (t - s.hi if t > s.hi else 0.0)
            if gap <= max_gap_cm:
                n += 1
                break
    return n


def _stacks(fam, course_fam, wall_len, edges):
    """Juntas que se repetem em 3 ou mais fiadas seguidas."""
    by_family = {}
    for f in set(course_fam.values()):
        by_family[f] = _internal_faces(fam[f], wall_len, edges)
    faces = dict((c, by_family[course_fam[c]]) for c in course_fam)
    empty = []
    n = 0
    for c in sorted(faces):
        for f in faces[c]:
            if _has_value_near(faces.get(c - 1, empty), f, FACE_TOLERANCE_CM):
                continue
            length, cc = 1, c
            while _has_value_near(faces.get(cc + 1, empty), f, FACE_TOLERANCE_CM):
                length += 1
                cc += 1
            if length >= 3:
                n += 1
    return n


def _runs(slots):
    out, cur = [], []
    for i, s in enumerate(slots):
        if s.movable and (not cur or s.lo - slots[cur[-1]].hi <= RUN_MAX_GAP_CM):
            cur.append(i)
            continue
        if len(cur) > 1:
            out.append(cur)
        cur = [i] if s.movable else []
    if len(cur) > 1:
        out.append(cur)
    return out


def _combinations_with_replacement(items, size):
    """itertools.combinations_with_replacement (existe no 2.7, mas mantido
    explicito e deterministico)."""
    out = []

    def rec(start, cur):
        if len(cur) == size:
            out.append(tuple(cur))
            return
        for i in range(start, len(items)):
            cur.append(items[i])
            rec(i, cur)
            cur.pop()
    rec(0, [])
    return out


def _multiset_orders(counts, n, cap):
    keys = sorted(counts)
    counts = dict(counts)
    out, cur = [], []

    def rec():
        if len(out) >= cap:
            return
        if len(cur) == n:
            out.append(tuple(cur))
            return
        for k in keys:
            if counts[k]:
                counts[k] -= 1
                cur.append(k)
                rec()
                cur.pop()
                counts[k] += 1
    rec()
    return out


def _arrangements(slots, run):
    """Ordens DISTINTAS do multiconjunto de codigos, geradas direto (sem varrer
    n!), em ordem lexicografica, com teto."""
    counts = collections.Counter(slots[i].code for i in run)
    keys = sorted(counts)
    n = len(run)
    out, cur = [], []

    def rec():
        if len(out) >= MAX_ARRANGEMENTS_PER_RUN:
            return
        if len(cur) == n:
            out.append(tuple(cur))
            return
        for k in keys:
            if counts[k]:
                counts[k] -= 1
                cur.append(k)
                rec()
                cur.pop()
                counts[k] += 1

    rec()
    return out


class _Wall(object):
    def __init__(self, wall_idx, rows, walls_to_create, openings_per_wall, catalog, tol_cm,
                 ties=None, half_code=None, half_tie_gap_cm=0.0, fill_codes=(),
                 joint_identity_guard=False, jamb_alignment=False):
        self.wall_idx = wall_idx
        # SECAO 84: faixa de compensacao na jamba (so' quando o chamador liga)
        self.jamb_alignment = bool(jamb_alignment) and JAMB_COMPENSATOR_ALIGNMENT_ENABLED
        self.jamb_conflicts = []
        self.broken_paths = []
        # SECAO 85: fiadas ignoradas pelas reguas de coluna (estagio A da busca)
        self._transparent = frozenset()
        self.verga_changes = []
        # SECAO 81.1: com a guarda, nenhuma troca pode criar junta coincidente
        # entre fiadas vizinhas numa POSICAO onde ela nao existia (a guarda de
        # contagem da janela aceitava trocar junta isenta junto da jamba por junta
        # a prumo de verdade no meio da parede)
        self.joint_guard = bool(joint_identity_guard)
        self.tol = tol_cm
        # SECAO 77: `ties` pode vir por fiada ({fiada: [t_cm]}) quando um no'
        # da parede nao e' encontro em alguma fiada
        self.ties_by_course = ties if isinstance(ties, dict) else None
        self.ties = [] if isinstance(ties, dict) else list(ties or [])
        self.half_code = half_code
        self.half_tie_gap = half_tie_gap_cm
        self.fill_codes = sorted(fill_codes or ())
        self.p0, self.dir, self.length = _axis(walls_to_create, wall_idx)
        self.edges = []
        self.openings_cm = []
        ops = (openings_per_wall or [])
        for op in (ops[wall_idx] if wall_idx < len(ops) else None) or ():
            lo_cm, hi_cm = float(op[0]) * CM_PER_FT, float(op[1]) * CM_PER_FT
            self.edges.extend([lo_cm, hi_cm])
            self.openings_cm.append((min(lo_cm, hi_cm), max(lo_cm, hi_cm)))
        self.edges.sort()
        self.openings_cm.sort()
        self.rows = rows
        self.catalog = catalog or {}
        self._build()

    def _entry_movable(self, entry, family):
        """Preenchimento comum que e' BLOCO VAZADO de alvenaria ou COMPENSADOR do
        catalogo. A etiqueta STANDARD_FILL sozinha nao basta: a canaleta do
        reforco CHANNEL herda a etiqueta da peca que substituiu (medido: o
        arranjo reordenou canaletas da fiada 3 da parede 8284502), e canaleta
        e' posicao de vao/verga, nunca peca de ajuste de corrida."""
        cand, _lo, _hi, courses = entry
        code = cand.get("logical_code")
        cat = self.catalog.get(code) or {}
        if cat.get("is_channel") or _is_channel_code(code):
            return False
        if not (_sva._is_hollow_masonry(cand, self.catalog) or cat.get("is_compensator")):
            return False
        reason = cand.get("placement_reason")
        movable_reason = (reason in _MOVABLE_REASONS) if B34_RUN_OPENING_REPAIR_MOVABLE \
            else reason == "STANDARD_FILL"
        return (movable_reason and cand.get("node_index") is None
                and bool(cand.get("length_cm"))
                and all(self.course_fam.get(cc) == family for cc in courses))

    def _slot(self, entry):
        cand, lo, hi, courses = entry
        s = _Slot()
        s.lo, s.hi, s.code = lo, hi, cand.get("logical_code")
        cat = self.catalog.get(s.code) or {}
        s.compensator = bool(cat.get("is_compensator"))
        s.node = cand.get("node_index") is not None
        s.hollow = _sva._is_hollow_masonry(cand, self.catalog)
        s.orientable = _sva._is_orientable_small_void_piece(cand)
        s.void_off, s.void_half = _void_geometry(cand, self.p0, self.dir, lo, hi)
        s.side = (1 if (s.void_off or 0.0) >= 0.0 else -1) if s.orientable else 0
        s.cells = _cells_geometry(cand, self.p0, self.dir, lo, hi) if s.hollow else ()
        s.cell_side = s.side
        return s

    def _build(self):
        sig_of = {}
        for c, entries in self.rows.items():
            sig_of[c] = tuple((round(lo, 1), round(hi, 1), cand.get("logical_code"),
                               1 if _sva._is_orientable_small_void_piece(cand) and
                               (_void_geometry(cand, self.p0, self.dir, lo, hi)[0] or 0.0) >= 0.0 else 0)
                              for cand, lo, hi, _courses in entries)
        order = sorted(set(sig_of.values()), key=lambda sig: min(c for c in sig_of if sig_of[c] == sig))
        name = dict((sig, i) for i, sig in enumerate(order))
        self.course_fam = dict((c, name[sig_of[c]]) for c in sig_of)
        self.fam, self.fam_rows = {}, {}
        for c in sorted(self.rows):
            f = self.course_fam[c]
            if f in self.fam:
                continue
            members = [cc for cc in sorted(self.rows) if self.course_fam[cc] == f]
            slots = []
            for index, entry in enumerate(self.rows[c]):
                s = self._slot(entry)
                # Movel so' se, em TODAS as fiadas desta familia, o objeto nesta
                # posicao for preenchimento comum que nao aparece em fiada de outra
                # familia. Conferir so' a primeira fiada deixava mover um objeto
                # compartilhado com outra familia (medido: B19 levado para cima de
                # uma amarracao na fiada 3 da parede 8284502).
                s.movable = all(self._entry_movable(self.rows[cc][index], f) for cc in members)
                slots.append(s)
            self.fam[f] = slots
        self.weights = collections.Counter()
        courses = sorted(self.course_fam)
        for c in courses:
            if c + 1 in self.course_fam:
                self.weights[(self.course_fam[c], self.course_fam[c + 1])] += 1
        self.count = collections.Counter(self.course_fam.values())
        # Template por codigo = COPIA congelada: a busca reescreve os slots vivos
        # (codigo, comprimento), e um template que fosse o proprio slot mudaria
        # de comprimento no meio da busca (bug medido: B34 com 39 cm, trecho
        # deslocado 5 cm e buraco de 6 cm na parede 8284502).
        self.template = {}
        for f in sorted(self.fam):
            for s in self.fam[f]:
                if s.code not in self.template:
                    self.template[s.code] = s.copy()

    # ------------------------------------------------------------ custo
    def _half_near_ties(self, slots, f):
        """HALF_BLOCK_NEAR_TIE da familia `f`: por fiada quando as posicoes de
        amarracao dependem da fiada (secao 77), senao a conta de sempre."""
        if self.ties_by_course is None:
            return _half_blocks_near_ties(slots, self.ties, self.half_code, self.half_tie_gap) * self.count[f]
        return sum(_half_blocks_near_ties(slots, self.ties_by_course.get(c) or [], self.half_code,
                                          self.half_tie_gap)
                   for c in sorted(self.course_fam) if self.course_fam[c] == f)

    def _window(self, f, run):
        slots = self.fam[f]
        return (slots[run[0]].lo - WINDOW_PAD_CM, slots[run[-1]].hi + WINDOW_PAD_CM)

    def _local(self, f, run):
        """Custo so' na JANELA do trecho: as outras familias nao mudam durante a
        avaliacao, entao a diferenca entre duas ordens e' exata."""
        window = self._window(f, run)
        v = co = 0
        faces_f = _internal_faces(self.fam[f], self.length, self.edges, window)
        wider = (window[0] - FACE_TOLERANCE_CM, window[1] + FACE_TOLERANCE_CM)
        for (a, b), k in self.weights.items():
            # vazado: TODAS as interfaces na janela - um vizinho girado junto
            # pode mexer na interface dele com uma terceira familia
            v += k * _violations_between(self.fam[a], self.fam[b], self.tol, window)
            if f not in (a, b):
                continue
            other = b if a == f else a
            if other != f:
                co += k * _coincident(faces_f, _internal_faces(self.fam[other], self.length, self.edges, wider))
        near = list(_in_window(self.fam[f], window[0], window[1]))
        cp = _compensator_guard(near, self.length) * self.count[f]
        ht = self._half_near_ties(near, f)
        # extremo da parede: olha a fileira inteira (a janela pode nao conter a ponta)
        ex = _long_compensator_extremes(self.fam[f], self.length) * self.count[f]
        return v, co, cp, ht, ex

    def _coincident_positions(self, f, window):
        """[(face, familia vizinha)] das faces da familia `f` na janela que
        coincidem com uma face de uma familia de fiada VIZINHA (secao 81.1)."""
        faces_f = _internal_faces(self.fam[f], self.length, self.edges, window)
        wider = (window[0] - FACE_TOLERANCE_CM, window[1] + FACE_TOLERANCE_CM)
        out = []
        for other in sorted(set(b if a == f else a for (a, b) in self.weights if f in (a, b))):
            if other == f:
                continue
            faces_o = _internal_faces(self.fam[other], self.length, self.edges, wider)
            for face in faces_f:
                if _has_value_near(faces_o, face, FACE_TOLERANCE_CM):
                    out.append((face, other))
        return out

    def _creates_joint(self, f, window, ref_positions):
        """True se a familia `f` passou a ter junta coincidente numa posicao
        (contra uma familia vizinha) que nao existia em `ref_positions`."""
        if not self.joint_guard:
            return False
        for face, other in self._coincident_positions(f, window):
            if not any(o == other and abs(face - q) <= FACE_TOLERANCE_CM for q, o in ref_positions):
                return True
        return False

    def _local_bound(self, f, run):
        window = self._window(f, run)
        return sum(k * _violations_lower_bound(self.fam[a], self.fam[b], self.tol, window)
                   for (a, b), k in sorted(self.weights.items()))

    def totals(self):
        v = co = cp = 0
        for (a, b), k in self.weights.items():
            v += k * _violations_between(self.fam[a], self.fam[b], self.tol)
            co += k * _coincident(_internal_faces(self.fam[a], self.length, self.edges),
                                  _internal_faces(self.fam[b], self.length, self.edges))
        ht = ex = 0
        for f in self.fam:
            cp += _compensator_guard(self.fam[f], self.length) * self.count[f]
            ex += _long_compensator_extremes(self.fam[f], self.length) * self.count[f]
            ht += self._half_near_ties(self.fam[f], f)
        out = {"violations": v, "coincident_faces": co, "compensator_guard": cp,
               "long_compensator_extremes": ex, "half_block_near_tie": ht,
               "stacked_joints": _stacks(self.fam, self.course_fam, self.length, self.edges)}
        if self.jamb_alignment:
            out["jamb_compensator_distance"] = round(sum(self._jamb_distance(f) * self.count[f]
                                                         for f in self.fam), 3)
        return out

    # ------------------------------------------------------------ busca
    def _apply(self, f, run, codes, sides):
        slots = self.fam[f]
        gaps = [slots[run[k + 1]].lo - slots[run[k]].hi for k in range(len(run) - 1)]
        cur = slots[run[0]].lo
        for k, i in enumerate(run):
            tpl = self.template[codes[k]]
            length = tpl.hi - tpl.lo
            s = slots[i]
            s.lo, s.hi, s.code = cur, cur + length, codes[k]
            s.compensator, s.hollow, s.orientable = tpl.compensator, tpl.hollow, tpl.orientable
            s.void_off, s.void_half = tpl.void_off, tpl.void_half
            s.cells, s.cell_side = tpl.cells, tpl.cell_side
            s.side = sides[k] if tpl.orientable else 0
            cur += length + (gaps[k] if k < len(gaps) else 0.0)

    def _snap(self, f, run):
        return [self.fam[f][i].copy() for i in run]

    def _restore(self, f, run, snap):
        for i, s in zip(run, snap):
            self.fam[f][i] = s.copy()

    def _best_sides(self, f, run, joint=False):
        """Descida coordenada na orientacao dos B34 do trecho - e, com
        NEIGHBOUR_FLIPS_ENABLED, dos B34 de preenchimento das outras familias que
        se sobrepoem ao trecho. Inverter UMA peca so' muda violacoes perto dela:
        cada teste mede a janela da propria peca em TODAS as interfaces."""
        slots = self.fam[f]
        pieces = [(slots[i], f) for i in run if slots[i].orientable]
        if joint and NEIGHBOUR_FLIPS_ENABLED and run:
            lo = slots[run[0]].lo - NEIGHBOUR_REACH_CM
            hi = slots[run[-1]].hi + NEIGHBOUR_REACH_CM
            for other in sorted(self.fam):
                if other == f:
                    continue
                for slot in _in_window(self.fam[other], lo, hi):
                    if slot.orientable and slot.movable:
                        pieces.append((slot, other))
        # interfaces de cada familia: inverter pecas das familias `families` so'
        # muda essas parcelas (as outras sao iguais antes e depois do teste)
        touching = collections.defaultdict(list)
        for (a, b), k in sorted(self.weights.items()):
            touching[a].append((a, b, k))
            if b != a:
                touching[b].append((a, b, k))

        def cost(items):
            return self._flip_cost(items, touching)
        for _round in range(4):
            improved = False
            for item in pieces:
                slot = item[0]
                before = cost((item,))
                slot.side = -slot.side
                if cost((item,)) < before:
                    improved = True
                else:
                    slot.side = -slot.side
            if joint and PAIR_FLIPS_ENABLED and not improved:
                improved = self._pair_flips(pieces, cost)
            if not improved:
                break

    def _flip_cost(self, items, touching):
        """Violacoes que PODEM mudar quando as pecas `items` [(slot, familia)]
        giram: cada peca como FONTE (contra a peca que cobre o vazado dela) e
        cada fonte que ELA cobre. Inverter so' muda o centro do vazado da propria
        peca, entao a diferenca antes/depois e' exatamente a da janela inteira.
        Chave por (interface, sentido, fonte): cada fonte tem uma cobertura so'."""
        counted = {}
        for p, g in items:
            for a, b, k in touching.get(g, ()):
                for direction, (src_family, dst_family) in enumerate(((a, b), (b, a))):
                    if src_family == g:
                        key = (a, b, direction, id(p))
                        if key not in counted:
                            t = _void_center(p)
                            h = _covering(self.fam[dst_family], t)
                            counted[key] = k if (h is not None and _offers(h, t, self.tol) is False) else 0
                    if dst_family == g:
                        for q in _in_window(self.fam[src_family], p.lo - COVER_REACH_CM, p.hi + COVER_REACH_CM):
                            if not q.orientable:
                                continue
                            key = (a, b, direction, id(q))
                            if key in counted:
                                continue
                            t = _void_center(q)
                            if _covering(self.fam[dst_family], t) is not p:
                                continue
                            counted[key] = k if _offers(p, t, self.tol) is False else 0
        return sum(counted.values())

    def _pair_flips(self, pieces, cost):
        """Inverte DUAS pecas de FAMILIAS DIFERENTES, uma sobre a outra (centros a
        ate' PAIR_FLIP_REACH_CM), de uma vez - primeira melhora, ordem fixa.
        Minimo local medido na parede 8284574 (ponta junto a no' T): o vazado
        menor do B34 da fiada par so' alinha se o B34 da impar logo acima girar
        JUNTO - cada inversao isolada fica em 32 ou sobe para 64; o par vai a 0."""
        ordered = sorted(pieces, key=lambda item: (item[0].lo, item[1]))
        for a in range(len(ordered)):
            pa, fa = ordered[a]
            mid_a = (pa.lo + pa.hi) / 2.0
            for b in range(a + 1, len(ordered)):
                pb, fb = ordered[b]
                if (pb.lo + pb.hi) / 2.0 - mid_a > PAIR_FLIP_REACH_CM:
                    break
                if fa == fb:
                    continue
                pair = (ordered[a], ordered[b])
                before = cost(pair)
                if before == 0:
                    continue
                pa.side, pb.side = -pa.side, -pb.side
                if cost(pair) < before:
                    return True
                pa.side, pb.side = -pa.side, -pb.side
        return False

    def optimize(self):
        runs = [(f, r) for f in sorted(self.fam) for r in _runs(self.fam[f])]
        changed_runs = set()
        for _pass in range(MAX_PASSES):
            changed = False
            for f, run in runs:
                orig = self._snap(f, run)
                neighbour_sides = self._neighbour_sides(f, run)
                ref = self._local(f, run)
                if ref[0] == 0:
                    continue
                window = self._window(f, run)
                ref_joints = self._coincident_positions(f, window) if self.joint_guard else ()
                ranked, pool = [], []
                sides0 = [s.side or 1 for s in orig]
                for index, codes in enumerate(self._arrangements_for(f, run)):
                    self._apply(f, run, codes, sides0)
                    self._best_sides(f, run)
                    cost = self._local(f, run)
                    if all(cost[k] <= ref[k] for k in range(1, len(ref))) and \
                            not self._creates_joint(f, window, ref_joints):
                        if cost[0] < ref[0]:
                            moved = sum(1 for o, i in zip(orig, run) if o.code != self.fam[f][i].code)
                            ranked.append((cost, moved, index, self._snap(f, run), self._neighbour_sides(f, run)))
                        else:
                            bound = self._local_bound(f, run)
                            if bound < ref[0]:
                                pool.append((bound, cost[0], index, codes))
                    self._restore(f, run, orig)
                    self._set_neighbour_sides(neighbour_sides)
                if REFINE_TOP_K and (NEIGHBOUR_FLIPS_ENABLED or PAIR_FLIPS_ENABLED):
                    for _bound, _v, index, codes in sorted(pool)[:REFINE_TOP_K]:
                        self._apply(f, run, codes, sides0)
                        self._best_sides(f, run, joint=True)
                        cost = self._local(f, run)
                        if cost[0] < ref[0] and not self._creates_joint(f, window, ref_joints):
                            moved = sum(1 for o, i in zip(orig, run) if o.code != self.fam[f][i].code)
                            ranked.append((cost, moved, index, self._snap(f, run), self._neighbour_sides(f, run)))
                        self._restore(f, run, orig)
                        self._set_neighbour_sides(neighbour_sides)
                if not ranked:
                    continue
                ranked.sort(key=lambda item: (item[0], item[1], item[2]))
                stacks_ref = _stacks(self.fam, self.course_fam, self.length, self.edges)
                for _cost, _moved, _index, snap, sides in ranked:
                    self._restore(f, run, snap)
                    self._set_neighbour_sides(sides)
                    if _stacks(self.fam, self.course_fam, self.length, self.edges) <= stacks_ref:
                        changed = True
                        changed_runs.add((f, tuple(run)))
                        break
                    self._restore(f, run, orig)
                    self._set_neighbour_sides(neighbour_sides)
            if not changed:
                break
        return changed_runs

    def _neighbour_sides(self, f, run):
        """[(slot, lado)] dos B34 de preenchimento das OUTRAS familias ao alcance."""
        if not NEIGHBOUR_FLIPS_ENABLED or not run:
            return []
        lo = self.fam[f][run[0]].lo - NEIGHBOUR_REACH_CM
        hi = self.fam[f][run[-1]].hi + NEIGHBOUR_REACH_CM
        out = []
        for other in sorted(self.fam):
            if other == f:
                continue
            for slot in _in_window(self.fam[other], lo, hi):
                if slot.orientable and slot.movable:
                    out.append((slot, slot.side))
        return out

    def _set_neighbour_sides(self, sides):
        for slot, side in sides:
            slot.side = side

    def _arrangements_for(self, f, run):
        return _arrangements(self.fam[f], run)

    # ------------------------------------------------------------ composicao (secao 61)
    def _tpl(self, code):
        if code not in self.template:
            tpl = _catalog_template(code, self.catalog)
            if tpl is None:
                return None
            self.template[code] = tpl
        return self.template[code]

    def _neighbour_multisets(self, codes, joint):
        """Multiconjuntos a ate' COMPOSITION_MAX_REMOVED pecas trocadas por ate'
        COMPOSITION_MAX_ADDED pecas de MESMO comprimento (juntas incluidas), sem
        aumentar o numero de especiais (compensadores). Ordem deterministica."""
        units = {}
        for code in self.fill_codes:
            tpl = self._tpl(code)
            if tpl is not None:
                units[code] = int(round((tpl.hi - tpl.lo + joint) * 10.0))
        if any(c not in units for c in codes):
            return []
        base = collections.Counter(codes)
        pool = sorted(units)
        adds = []
        for size in range(1, COMPOSITION_MAX_ADDED + 1):
            adds.extend(_combinations_with_replacement(pool, size))
        removes = []
        for size in range(1, COMPOSITION_MAX_REMOVED + 1):
            for rem in _combinations_with_replacement(sorted(base), size):
                need = collections.Counter(rem)
                if all(base[k] >= v for k, v in need.items()):
                    removes.append(rem)
        seen, out = set(), []
        for rem in removes:
            total = sum(units[k] for k in rem)
            specials = sum(1 for k in rem if self._tpl(k).compensator)
            for add in adds:
                if sorted(add) == sorted(rem) or sum(units[k] for k in add) != total:
                    continue
                if sum(1 for k in add if self._tpl(k).compensator) > specials:
                    continue
                new = base - collections.Counter(rem) + collections.Counter(add)
                key = tuple(sorted(new.elements()))
                if key not in seen:
                    seen.add(key)
                    out.append(key)
                    if len(out) >= MAX_COMPOSITIONS_PER_RUN:
                        return out
        return out

    def _splice(self, f, run, codes, joint):
        slots = self.fam[f]
        cur = slots[run[0]].lo
        new = []
        for code in codes:
            tpl = self._tpl(code)
            s = tpl.copy()
            s.lo, s.hi = cur, cur + (tpl.hi - tpl.lo)
            s.movable, s.node = True, False
            new.append(s)
            cur = s.hi + joint
        self.fam[f] = slots[:run[0]] + new + slots[run[-1] + 1:]
        return list(range(run[0], run[0] + len(new)))

    def _compose(self, f, run):
        slots = self.fam[f]
        gaps = [slots[run[k + 1]].lo - slots[run[k]].hi for k in range(len(run) - 1)]
        if not gaps or any(abs(g - gaps[0]) > JOINT_REGULAR_TOLERANCE_CM for g in gaps):
            return False
        joint = gaps[0]
        codes = [slots[i].code for i in run]
        ref = self._local(f, run)
        ref_specials = sum(1 for i in run if slots[i].compensator)
        if ref[0] == 0 and ref_specials == 0:
            return False  # nada a ganhar: dominancia exige menos vazado ou menos especiais
        original = list(slots)
        neighbour_sides = self._neighbour_sides(f, run)
        best = None
        pool = []
        # a composicao cobre o MESMO trecho (pontas fixas): a janela da corrida
        # original contem a nova
        window = self._window(f, run)
        ref_joints = self._coincident_positions(f, window) if self.joint_guard else ()

        def consider(order, specials, ms_index, arr_index, joint_sides):
            new_run = self._splice(f, run, order, joint)
            self._best_sides(f, new_run, joint=joint_sides)
            cost = self._local(f, new_run)
            guards_ok = all(cost[k] <= ref[k] for k in range(1, len(ref))) and \
                not self._creates_joint(f, window, ref_joints)
            dominates = ((cost[0] < ref[0] and specials <= ref_specials)
                         or (cost[0] <= ref[0] and specials < ref_specials))
            found = None
            bound = None
            if guards_ok and not dominates and not joint_sides:
                bound = self._local_bound(f, new_run)
            if guards_ok and dominates:
                found = ((cost[0], specials, len(order), ms_index, arr_index),
                         [x.copy() for x in self.fam[f]], self._neighbour_sides(f, new_run))
            self.fam[f] = list(original)
            self._set_neighbour_sides(neighbour_sides)
            return found, guards_ok, bound
        for ms_index, multiset in enumerate(self._neighbour_multisets(codes, joint)):
            specials = sum(1 for code in multiset if self._tpl(code).compensator)
            counts = collections.Counter(multiset)
            for arr_index, order in enumerate(_multiset_orders(counts, len(multiset),
                                                                MAX_ARRANGEMENTS_PER_COMPOSITION)):
                found, guards_ok, bound = consider(order, specials, ms_index, arr_index, False)
                if found is not None:
                    if best is None or found[0] < best[0]:
                        best = found
                elif guards_ok and bound is not None and (
                        (bound < ref[0] and specials <= ref_specials)
                        or (bound <= ref[0] and specials < ref_specials)):
                    pool.append((bound, specials, ms_index, arr_index, tuple(order)))
        if REFINE_TOP_K and (NEIGHBOUR_FLIPS_ENABLED or PAIR_FLIPS_ENABLED):
            for _bound, specials, ms_index, arr_index, order in sorted(pool)[:REFINE_TOP_K]:
                found, _ok, _v2 = consider(list(order), specials, ms_index, arr_index, True)
                if found is not None and (best is None or found[0] < best[0]):
                    best = found
        if best is None:
            return False
        stacks_ref = _stacks(self.fam, self.course_fam, self.length, self.edges)
        self.fam[f] = best[1]
        self._set_neighbour_sides(best[2])
        if _stacks(self.fam, self.course_fam, self.length, self.edges) <= stacks_ref:
            return True
        self.fam[f] = original
        self._set_neighbour_sides(neighbour_sides)
        return False

    # ------------------------------------------------------------ orientacao exata (secao 62)
    def _source_violations(self, f, i, weights_by_family):
        """Violacoes em que o B34 (f, i) e' a FONTE, contra as familias vizinhas,
        ja' multiplicadas pela quantidade de interfaces."""
        p = self.fam[f][i]
        t = _void_center(p)
        n = 0
        for other, k in weights_by_family.get(f, ()):
            h = _covering(self.fam[other], t)
            if h is not None and _offers(h, t, self.tol) is False:
                n += k
        return n

    def orient_exact(self):
        """Orientacao otima dos B34 de preenchimento (movel, orientavel) desta
        parede. Devolve quantas orientacoes mudaram (0 se o otimo nao for
        ESTRITAMENTE melhor ou se a banda passar do teto)."""
        if not B34_ORIENTATION_DP_ENABLED:
            return 0
        weights_by_family = collections.defaultdict(list)
        for (a, b), k in sorted(self.weights.items()):
            weights_by_family[a].append((b, k))
            if a != b:
                weights_by_family[b].append((a, k))
        variables = []
        for f in sorted(self.fam):
            for i, slot in enumerate(self.fam[f]):
                if slot.orientable and slot.movable and slot.void_off is not None:
                    variables.append((slot.mid, f, i))
        if not variables:
            return 0
        variables.sort()
        position = dict(((f, i), n) for n, (_mid, f, i) in enumerate(variables))
        # fatores: um por B34-fonte (variavel ou fixo) que dependa de alguma variavel
        factors = collections.defaultdict(list)
        band = 0
        for f in sorted(self.fam):
            for i, slot in enumerate(self.fam[f]):
                if not slot.orientable or slot.void_off is None:
                    continue
                involved = set()
                if (f, i) in position:
                    involved.add(position[(f, i)])
                saved = slot.side
                for side in (-1, 1):
                    slot.side = side
                    t = _void_center(slot)
                    for other, _k in weights_by_family.get(f, ()):
                        j = _first_hi_at_least(self.fam[other], t)
                        if j < len(self.fam[other]) and self.fam[other][j].lo - 1e-6 <= t and \
                                (other, j) in position:
                            involved.add(position[(other, j)])
                    if (f, i) not in position:
                        break  # fonte fixa: o lado dela nao muda
                slot.side = saved
                if not involved:
                    continue
                low, high = min(involved), max(involved)
                band = max(band, high - low)
                factors[high].append((f, i, sorted(involved)))
        if band > ORIENTATION_DP_MAX_BAND:
            return 0
        slots_of = [self.fam[f][i] for _mid, f, i in variables]
        current = [s.side for s in slots_of]
        # TABELA por fator: custo para cada combinacao dos lados das variaveis
        # envolvidas (no maximo a fonte e os B34 que podem cobrir o vazado).
        # A DP so' consulta a tabela - nada de geometria dentro do laco.
        tables = collections.defaultdict(list)
        current_cost = 0
        for at in sorted(factors):
            for f, i, positions in factors[at]:
                table = []
                for mask in range(1 << len(positions)):
                    for bit, q in enumerate(positions):
                        slots_of[q].side = 1 if (mask >> bit) & 1 else -1
                    table.append(self._source_violations(f, i, weights_by_family))
                for q in positions:
                    slots_of[q].side = current[q]
                tables[at].append((positions, table))
                mask = 0
                for bit, q in enumerate(positions):
                    if current[q] > 0:
                        mask |= 1 << bit
                current_cost += table[mask]

        def factor_cost(at, full):
            total = 0
            for positions, table in tables.get(at, ()):
                mask = 0
                for bit, q in enumerate(positions):
                    if (full >> (at - q)) & 1:
                        mask |= 1 << bit
                total += table[mask]
            return total

        # Estado = MASCARA DE BITS das ultimas `band` variaveis: bit j = lado da
        # variavel n-j (1 = lado positivo). Mesmo resultado da versao com tuplas,
        # mas aritmetica inteira - o IronPython 2.7 do Revit roda a DP ~3x mais
        # rapido so' com a tabela de fatores e bem mais com a mascara.
        keep_mask = (1 << band) - 1
        layer = {0: (0, None)}
        history = []
        for n in range(len(slots_of)):
            nxt = {}
            # ordem ORDENADA: empate entre caminhos de mesmo custo decide igual em
            # qualquer runtime (dict do IronPython 2.7 nao guarda ordem de insercao)
            for state, (cost, _prev) in sorted(layer.items()):
                shifted = state << 1
                for bit in (0, 1):
                    full = shifted | bit
                    total = cost + factor_cost(n, full)
                    key = full & keep_mask
                    if key not in nxt or total < nxt[key][0]:
                        nxt[key] = (total, (state, bit))
            history.append(nxt)
            layer = nxt
        best_state = min(sorted(layer), key=lambda st: layer[st][0])
        best_cost = layer[best_state][0]
        if best_cost >= current_cost:
            for slot, side in zip(slots_of, current):
                slot.side = side
            return 0
        chosen = [0] * len(slots_of)
        state = best_state
        for n in range(len(slots_of) - 1, -1, -1):
            _total, (prev, bit) = history[n][state]
            chosen[n] = 1 if bit else -1
            state = prev
        changed = 0
        for slot, side, old in zip(slots_of, chosen, current):
            slot.side = side
            if side != old:
                changed += 1
        return changed

    def compose(self):
        """Uma composicao aceita muda os indices da familia: recomeca as corridas
        dela. Teto de iteracoes por parede, deterministico."""
        if not B34_RUN_COMPOSITION_ENABLED or not self.fill_codes:
            return 0
        accepted = 0
        for f in sorted(self.fam):
            for _guard in range(64):
                changed = False
                for run in _runs(self.fam[f]):
                    if self._compose(f, run):
                        accepted += 1
                        changed = True
                        break
                if not changed:
                    break
        return accepted

    # ------------------------------------------------------------ faixa de jamba (secao 84)
    def _active_jamb_edges(self, f):
        """[(t_cm da borda, sentido)] das jambas ATIVAS na familia `f` - a fileira
        nao tem peca logo dentro do vao (a abertura corta esta fiada). Sentido
        -1: as pecas ficam antes da borda (borda inicial do vao); +1: depois."""
        slots = self.fam[f]
        out = []
        for lo, hi in self.openings_cm:
            if hi - lo <= 2.0 * JAMB_INSIDE_PROBE_CM:
                continue
            if _covering(slots, lo + JAMB_INSIDE_PROBE_CM) is None:
                out.append((lo, -1))
            if _covering(slots, hi - JAMB_INSIDE_PROBE_CM) is None:
                out.append((hi, 1))
        return out

    @staticmethod
    def _distance_to_edge(slot, edge, d):
        """Distancia (cm) da face de `slot` voltada para a jamba ate' a borda
        (0 = encostado, contando a junta dentro da tolerancia)."""
        return (slot.lo - edge) if d > 0 else (edge - slot.hi)

    def _strip_distance(self, f, i, edges):
        """Distancia (cm) do compensador `self.fam[f][i]` ate' a jamba ativa mais
        proxima do lado dele, SEM contar os compensadores entre ele e o vao: um
        par C04+C09 encostado e' UMA faixa (os dois contam 0). None fora do
        alcance de 2x JAMB_REACH_CM ou do lado errado da borda."""
        slots = self.fam[f]
        s = slots[i]
        best = None
        for edge, d in edges:
            raw = self._distance_to_edge(s, edge, d)
            if raw < -JAMB_TOUCH_TOLERANCE_CM or raw > 2.0 * JAMB_REACH_CM:
                continue
            strip = 0.0
            k = i - d
            while 0 <= k < len(slots):
                q = slots[k]
                if self._distance_to_edge(q, edge, d) < -JAMB_TOUCH_TOLERANCE_CM:
                    break
                if q.compensator:
                    # comprimento do compensador + a junta do lado de fora dele
                    strip += (slots[k + 1].lo - q.lo) if d > 0 else (q.hi - slots[k - 1].hi)
                k -= d
            dist = max(raw - strip, 0.0)
            if best is None or dist < best:
                best = dist
        return best

    def _jamb_distance(self, f):
        """Soma das distancias dos compensadores da familia `f` ate' a jamba ativa
        mais proxima do lado deles (teto JAMB_REACH_CM). Encostado (ou atras de
        outro compensador encostado) conta 0 - a folga da junta nao penaliza."""
        edges = self._active_jamb_edges(f)
        if not edges:
            return 0.0
        total = 0.0
        for i, s in enumerate(self.fam[f]):
            if not s.compensator:
                continue
            best = self._strip_distance(f, i, edges)
            if best is None or best <= JAMB_TOUCH_TOLERANCE_CM:
                continue
            total += min(best, JAMB_REACH_CM)
        return round(total, 3)

    def _jamb_strip_faces(self, f, b19=False):
        """Faces ISENTAS da familia `f`: as DUAS faces da junta interna da faixa
        de compensadores (C09/C04) encostada numa jamba ativa - a do compensador
        mais de dentro e a da peca vizinha do outro lado da mesma junta. Nao vale
        para a junta seguinte (depois do B19/B39) nem para ponta de no'."""
        out = []
        edges = self._active_jamb_edges(f)
        slots = self.fam[f]
        for edge, d in edges:
            i = self._touching_index(slots, edge, d)
            if i is None:
                continue
            if not slots[i].compensator:
                if b19 and slots[i].code == "B19":
                    # 11.8: B19 de fechamento encostado no vao
                    self._closure_faces(slots, i, d, out)
                continue
            if b19:
                # so' o B19 logo atras da faixa (a faixa em si e' da lista normal)
                j = i
                while 0 <= j + d < len(slots) and slots[j + d].compensator:
                    j += d
                if 0 <= j + d < len(slots) and slots[j + d].code == "B19":
                    self._closure_faces(slots, j + d, d, out)
                continue
            # anda pela faixa (compensadores encostados) ate' a ultima peca dela;
            # as juntas ENTRE compensadores da faixa (C04|C09) tambem sao dela
            j = i
            while 0 <= j + d < len(slots) and slots[j + d].compensator:
                gap = (slots[j + d].lo - slots[j].hi) if d > 0 else (slots[j].lo - slots[j + d].hi)
                if gap > RUN_MAX_GAP_CM:
                    break
                out.extend([slots[j].hi, slots[j + d].lo] if d > 0 else [slots[j].lo, slots[j + d].hi])
                j += d
            last = slots[j]
            out.append(last.hi if d > 0 else last.lo)
            if 0 <= j + d < len(slots):
                nxt = slots[j + d]
                gap = (nxt.lo - last.hi) if d > 0 else (last.lo - nxt.hi)
                if gap <= RUN_MAX_GAP_CM:
                    out.append(nxt.lo if d > 0 else nxt.hi)
        out.sort()
        return out

    @staticmethod
    def _closure_faces(slots, k, d, out):
        """As duas faces da junta do lado de DENTRO da peca de fechamento k."""
        if 0 <= k + d < len(slots):
            a, b = slots[k], slots[k + d]
            gap = (b.lo - a.hi) if d > 0 else (a.lo - b.hi)
            if gap <= RUN_MAX_GAP_CM:
                out.extend([a.hi, b.lo] if d > 0 else [a.lo, b.hi])

    @staticmethod
    def _touching_index(slots, edge, d):
        for i, s in enumerate(slots):
            face = s.lo if d > 0 else s.hi
            if abs(face - edge) <= JAMB_TOUCH_TOLERANCE_CM:
                return i
        return None

    def _courses_of(self, f):
        return [c for c in sorted(self.course_fam) if self.course_fam[c] == f]

    def _node_closure(self, f, i):
        """SECAO 85: o compensador `self.fam[f][i]` (com os compensadores
        encostados nele) fecha contra um ENCONTRO - peca de no' encostada, ou a
        parede que cruza (vazio > RUN_MAX_GAP_CM com amarracao a ate' 20 cm).
        E' fechamento (desenho do usuario do pilar direito da janela central:
        `B39 | B39 | C09 | encontro`), nao pastilha solta no miolo."""
        slots = self.fam[f]
        ties = list(self.ties or [])
        if self.ties_by_course:
            for c in self._courses_of(f):
                ties.extend(self.ties_by_course.get(c) or [])
        for step in (-1, 1):
            j = i
            while 0 <= j + step < len(slots) and slots[j + step].compensator:
                q, r = slots[j], slots[j + step]
                if ((r.lo - q.hi) if step > 0 else (q.lo - r.hi)) > RUN_MAX_GAP_CM:
                    break
                j += step
            face = slots[j].hi if step > 0 else slots[j].lo
            k = j + step
            if 0 <= k < len(slots):
                nb = slots[k]
                gap = (nb.lo - face) if step > 0 else (face - nb.hi)
                if gap <= RUN_MAX_GAP_CM:
                    if nb.node and not nb.movable:
                        return True
                    continue
            if any(abs(t - face) <= 20.0 for t in ties):
                return True
        return False

    def _free_end_positions(self):
        """Pontas da parede SEM amarracao (nenhum encontro a ate' 20 cm): la' o
        B19 fecha de verdade (ponta livre)."""
        ties = list(self.ties or [])
        if self.ties_by_course:
            for lst in self.ties_by_course.values():
                ties.extend(lst or [])
        out = []
        for end in (0.0, self.length):
            if not any(abs(t - end) <= 20.0 for t in ties):
                out.append(end)
        return out

    def _half_block_admissible(self, f, i, edges=None):
        """SECAO 85 (pedido do usuario, 2026-09-29): B19 SO' em fechamento
        admissivel - encostado numa jamba ATIVA desta fiada, numa ponta livre de
        parede, ou imediatamente atras da faixa de compensadores (C09/C04) que
        encosta no vao (forma estreita da secao 84, desenho do usuario
        `B54 | B19 | C09 | vao`). Encostar numa peca de no' NAO basta."""
        slots = self.fam[f]
        s = slots[i]
        if edges is None:
            edges = self._active_jamb_edges(f)
        for edge, d in edges:
            face = s.lo if d > 0 else s.hi
            if abs(face - edge) <= JAMB_TOUCH_TOLERANCE_CM:
                return True
        for end in self._free_end_positions():
            if abs(s.lo - end) <= WALL_END_TOLERANCE_CM or abs(s.hi - end) <= WALL_END_TOLERANCE_CM:
                return True
        for step in (-1, 1):
            j, cur, seen = i + step, (s.lo if step < 0 else s.hi), False
            while 0 <= j < len(slots):
                q = slots[j]
                gap = (cur - q.hi) if step < 0 else (q.lo - cur)
                if gap > RUN_MAX_GAP_CM or not q.compensator:
                    break
                seen = True
                cur = q.lo if step < 0 else q.hi
                j += step
            if seen and any(abs(cur - e) <= JAMB_TOUCH_TOLERANCE_CM for e, _d in edges):
                return True
        return False

    def _half_blocks_misplaced(self, f, window=None):
        n = 0
        edges = self._active_jamb_edges(f)
        for i, s in enumerate(self.fam[f]):
            if s.code != "B19":
                continue
            if window is not None and (s.hi < window[0] or s.lo > window[1]):
                continue
            if not self._half_block_admissible(f, i, edges):
                n += 1
        return n

    def _jamb_units(self):
        """({chave: [(familia, (ini, fim) indices da corrida, [(borda, sentido)])]},
        [conflitos de peca fixa]). A unidade e' a corrida MOVEL contigua que sai
        da jamba: ate' JAMB_REACH_CM e, quando a corrida continua movel, ate' a
        primeira peca fixa (no', canaleta, verga) - limitada a JAMB_FULL_RUN_MAX_CM
        / JAMB_UNIT_MAX_PIECES (secao 85: a outra paridade tambem precisa alcancar
        a faixa). Num pilarete as corridas das duas jambas que se sobrepoem viram
        UMA unidade."""
        units = collections.defaultdict(list)
        blocked = []
        bridge = self._bridge_edges() if JAMB_BRIDGE_ENABLED else {}
        bridge_members = []
        for f in sorted(self.fam):
            slots = self.fam[f]
            per_edge = []
            active_f = self._active_jamb_edges(f)
            for edge, d, limit in bridge.get(f, ()):
                if any(abs(e - edge) < EDGE_TOLERANCE_CM and dd == d for e, dd in active_f):
                    continue
                if limit == "verga":
                    run = self._bridge_run(f, edge, d, None, allow_channel=True)
                else:
                    run = self._bridge_run(f, edge, d, limit)
                if run:
                    bridge_members.append((f, run, (edge, d)))
            for edge, d in self._active_jamb_edges(f):
                i0 = self._touching_index(slots, edge, d)
                if i0 is None:
                    continue
                idx = []
                j = i0
                while 0 <= j < len(slots):
                    s = slots[j]
                    dist = self._distance_to_edge(s, edge, d)
                    if not s.movable:
                        break
                    if dist >= JAMB_FULL_RUN_MAX_CM or len(idx) >= JAMB_UNIT_MAX_PIECES:
                        idx = []  # corrida longa demais: fica so' o alcance curto
                        j = i0
                        while 0 <= j < len(slots) and slots[j].movable and \
                                self._distance_to_edge(slots[j], edge, d) < JAMB_REACH_CM:
                            if idx:
                                prev = slots[idx[-1]]
                                gap = (slots[j].lo - prev.hi) if d > 0 else (prev.lo - slots[j].hi)
                                if gap < -FACE_TOLERANCE_CM or gap > RUN_MAX_GAP_CM:
                                    break
                            idx.append(j)
                            j += d
                        break
                    if idx:
                        prev = slots[idx[-1]]
                        gap = (s.lo - prev.hi) if d > 0 else (prev.lo - s.hi)
                        if gap < -FACE_TOLERANCE_CM or gap > RUN_MAX_GAP_CM:
                            break
                    idx.append(j)
                    j += d
                # compensador ao alcance, mas atras de peca fixa: nada alcanca ele
                behind = []
                k = j
                while 0 <= k < len(slots):
                    s = slots[k]
                    dist = self._distance_to_edge(s, edge, d)
                    if dist >= JAMB_REACH_CM:
                        break
                    if s.compensator and dist >= -JAMB_TOUCH_TOLERANCE_CM and (not idx or k not in idx):
                        behind.append(k)
                    k += d
                if behind:
                    blocked.append({"wall_idx": self.wall_idx, "edges_cm": [round(edge, 1)], "side": d,
                                    "courses": self._courses_of(f),
                                    "distance_cm": round(min(self._distance_to_edge(slots[k2], edge, d)
                                                             for k2 in behind), 1),
                                    "codes": [slots[k2].code for k2 in behind],
                                    "reasons": ["FIXED_PIECE_BETWEEN"]})
                if not idx:
                    continue
                per_edge.append((sorted(idx), [(edge, d)]))
            merged = []
            for idx, edges in sorted(per_edge):
                if merged and set(idx) & set(merged[-1][0]):
                    merged[-1] = (sorted(set(idx) | set(merged[-1][0])), merged[-1][1] + edges)
                else:
                    merged.append((idx, edges))
            for idx, edges in merged:
                key = tuple(sorted((round(e, 1), d) for e, d in edges))
                units[key].append((f, (idx[0], idx[-1]), edges))
        # a fiada-ponte entra na unidade da PROPRIA jamba (pilarete: na do par);
        # a mesma corrida pode servir as duas jambas da abertura - resolvidas em
        # sequencia, a segunda nao piora as colunas da primeira (falhas duras)
        for f, run, (edge, d) in bridge_members:
            target = None
            for key in sorted(units, key=lambda k: (-len(k), k)):
                if any(abs(e - edge) < EDGE_TOLERANCE_CM and dd == d for e, dd in key):
                    target = key
                    break
            if target is None:
                target = ((round(edge, 1), d),)
            if any(mf == f for mf, _sp, _es in units[target]):
                continue
            units[target].append((f, (run[0], run[-1]), [(edge, d)]))
        return units, blocked

    def _bridge_edges(self):
        """{familia: [(borda, sentido, limite_sobre_o_vao)]} - as JAMB_BRIDGE_COURSES
        primeiras fiadas de bloco (canaleta atravessada) acima da abertura e abaixo
        dela (janela), na coluna da jamba. `limite` None: a corrida vai de peca
        fixa a peca fixa - deslocar a grade sobre a porta pede mudar a ponta
        oposta do trecho (medido: W1, porta [534,625])."""
        out = collections.defaultdict(list)
        courses = sorted(self.course_fam)
        active = {}
        for f in self.fam:
            active[f] = self._active_jamb_edges(f)
        for lo, hi in self.openings_cm:
            mid = (lo + hi) / 2.0
            for edge, d in ((lo, -1), (hi, 1)):
                cut = [c for c in courses
                       if any(abs(e - edge) < EDGE_TOLERANCE_CM and dd == d for e, dd in active[self.course_fam[c]])]
                if not cut:
                    continue
                probe = edge + d * 10.0
                for start, step in ((max(cut) + 1, 1), (min(cut) - 1, -1)):
                    c, found = start, 0
                    verga = False
                    while c in self.course_fam and found < JAMB_BRIDGE_COURSES:
                        slots = self.fam[self.course_fam[c]]
                        host = _covering(slots, probe)
                        if host is None:
                            break  # outra abertura ou fora da parede
                        f = self.course_fam[c]
                        if not _is_channel_code(host.code):
                            if not any(abs(e - edge) < EDGE_TOLERANCE_CM and dd == d for e, dd, _l in out[f]):
                                out[f].append((edge, d, None))
                            found += 1
                        elif JAMB_VERGA_MEMBER_ENABLED and JAMB_GRID_FOLLOW_ENABLED and not verga and found == 0:
                            # 85.9: a fiada da verga/contraverga (logo acima/abaixo
                            # do vao) tambem segue a grade da jamba
                            verga = True
                            if not any(abs(e - edge) < EDGE_TOLERANCE_CM and dd == d for e, dd, _l in out[f]):
                                out[f].append((edge, d, "verga"))
                        c += step
        return out

    def _bridge_run(self, f, edge, d, limit, allow_channel=False):
        """Indices da corrida MOVEL da fiada-ponte que cobre a coluna da jamba:
        cresce para o lado do pilar ate' a peca fixa e, para cima do vao, ate'
        `limite` (meio do vao) - JAMB_FULL_RUN_MAX_CM / JAMB_UNIT_MAX_PIECES."""
        slots = self.fam[f]
        probe = edge + d * 10.0
        i0 = None
        for i, sl in enumerate(slots):
            if sl.lo - 1e-6 <= probe <= sl.hi + 1e-6:
                i0 = i
                break
        def free(sl):
            return sl.movable or (allow_channel and _is_channel_code(sl.code))

        if i0 is None or not free(slots[i0]):
            return None
        lo_i = hi_i = i0

        def ok(j, nb):
            if not (0 <= j < len(slots)) or not free(slots[j]):
                return False
            gap = (slots[j].lo - slots[nb].hi) if j > nb else (slots[nb].lo - slots[j].hi)
            if gap < -FACE_TOLERANCE_CM or gap > RUN_MAX_GAP_CM:
                return False
            if limit is not None and d > 0 and j < nb and slots[j].lo < limit:
                return False  # limite opcional sobre o vao
            if limit is not None and d < 0 and j > nb and slots[j].hi > limit:
                return False
            lo_t = min(slots[lo_i].lo, slots[j].lo)
            hi_t = max(slots[hi_i].hi, slots[j].hi)
            if JAMB_GRID_FOLLOW_ENABLED:
                return hi_t - lo_t <= JAMB_BRIDGE_RUN_MAX_CM and (hi_i - lo_i + 2) <= JAMB_BRIDGE_RUN_MAX_PIECES
            return hi_t - lo_t <= JAMB_FULL_RUN_MAX_CM and (hi_i - lo_i + 2) <= JAMB_UNIT_MAX_PIECES
        if JAMB_GRID_FOLLOW_ENABLED:
            # 85.9: primeiro ate' a peca fixa do lado do pilar, depois sobre o vao
            if d > 0:
                while ok(hi_i + 1, hi_i):
                    hi_i += 1
                while ok(lo_i - 1, lo_i):
                    lo_i -= 1
            else:
                while ok(lo_i - 1, lo_i):
                    lo_i -= 1
                while ok(hi_i + 1, hi_i):
                    hi_i += 1
        grown = not JAMB_GRID_FOLLOW_ENABLED
        while grown:
            grown = False
            if ok(lo_i - 1, lo_i):
                lo_i -= 1
                grown = True
            if ok(hi_i + 1, hi_i):
                hi_i += 1
                grown = True
        if allow_channel and not any(slots[k].movable for k in range(lo_i, hi_i + 1)):
            return None  # verga sem peca de bloco no trecho: nada a acompanhar
        return list(range(lo_i, hi_i + 1))

    def _fill_exact(self, length, joint, side):
        """[(codigo, lado)] de B39/B34 com comprimento+juntas = `length` (o menor
        numero de B34) - None se nao fecha. B34 virados para `side`."""
        if abs(length) <= EDGE_TOLERANCE_CM:
            return []
        if length < 0:
            return None
        t39, t34 = self._tpl("B39"), self._tpl("B34")
        if t39 is None or t34 is None:
            return None
        u39, u34 = t39.hi - t39.lo + joint, t34.hi - t34.lo + joint
        for b in range(0, 13):
            rest = length - b * u34
            if rest < -EDGE_TOLERANCE_CM:
                break
            a = int(round(rest / u39))
            if a >= 0 and abs(rest - a * u39) <= EDGE_TOLERANCE_CM:
                return [("B39", 0)] * a + [("B34", side)] * b
        return None

    def _grid_follow(self, run, arun, edges):
        """SECAO 85.9: (codigo, lado) da corrida-ponte `run` (pecas originais)
        seguindo a grade `arun` da fiada da jamba de mesma paridade. Em cada ponta
        da grade: se e' jamba, as pecas de fechamento (B19, compensador) nao sobem
        - sobre o vao a fiada e' continua - e o trecho sobre o vao fecha com
        B39/B34 exatos a partir da junta ORIGINAL mais proxima que fecha (as pecas
        alem dela ficam como estao); se e' peca fixa, a ponta da ponte e' a mesma.
        Fiada da verga: peca nova dentro da extensao original da canaleta vira
        U39/U34 (a verga nunca encolhe). None quando nao fecha."""
        if not run or not arun:
            return None
        gaps = [run[k + 1].lo - run[k].hi for k in range(len(run) - 1)]
        joint = sorted(gaps)[len(gaps) // 2] if gaps else 1.0
        left_jamb = any(d == 1 and abs(e - arun[0].lo) <= EDGE_TOLERANCE_CM + JAMB_TOUCH_TOLERANCE_CM
                        for e, d in edges)
        right_jamb = any(d == -1 and abs(e - arun[-1].hi) <= EDGE_TOLERANCE_CM + JAMB_TOUCH_TOLERANCE_CM
                         for e, d in edges)
        if not (left_jamb or right_jamb):
            return None
        grid = list(arun)
        if left_jamb:
            while grid and (grid[0].code == "B19" or grid[0].compensator):
                grid.pop(0)
        if right_jamb:
            while grid and (grid[-1].code == "B19" or grid[-1].compensator):
                grid.pop()
        if not grid or any(g.node or not g.movable for g in grid):
            return None
        side = next((g.side for g in grid if g.orientable and g.side), 1)
        # ponta esquerda
        if left_jamb:
            prefix = fill_l = None
            for k in range(len(run) - 1, -1, -1):
                if run[k].lo > grid[0].lo + EDGE_TOLERANCE_CM:
                    continue
                fl = self._fill_exact(grid[0].lo - run[k].lo, joint, side)
                if fl is not None:
                    prefix, fill_l = run[:k], fl  # do vao para a grade: B39 longe, B34 junto
                    break
            if fill_l is None:
                return None
        else:
            if abs(run[0].lo - grid[0].lo) > EDGE_TOLERANCE_CM:
                return None
            prefix, fill_l = [], []
        # ponta direita
        if right_jamb:
            suffix = fill_r = None
            for k in range(0, len(run)):
                if run[k].hi < grid[-1].hi - EDGE_TOLERANCE_CM:
                    continue
                fr = self._fill_exact(run[k].hi - grid[-1].hi, joint, side)
                if fr is not None:
                    suffix, fill_r = run[k + 1:], list(reversed(fr))
                    break
            if fill_r is None:
                return None
        else:
            if abs(run[-1].hi - grid[-1].hi) > EDGE_TOLERANCE_CM:
                return None
            suffix, fill_r = [], []
        keep = lambda sl: (sl.code, sl.side if sl.orientable else 0)
        lay = ([keep(sl) for sl in prefix] + fill_l + [(g.code, g.side if g.orientable else 0) for g in grid]
               + fill_r + [keep(sl) for sl in suffix])
        if [c for c, _s in lay] == [sl.code for sl in run] and \
                [x for x in lay] == [keep(sl) for sl in run]:
            return None  # ja' segue a grade
        channels = [sl for sl in run if _is_channel_code(sl.code)]
        if channels:
            # posicoes da nova corrida (mesmo criterio do _splice_layout)
            pos = []
            seq = gaps if len(lay) == len(run) else [joint] * (len(lay) - 1)
            cur = run[0].lo
            for k, (code, _s) in enumerate(lay):
                tpl = self._tpl(code)
                pos.append((cur, cur + (tpl.hi - tpl.lo)))
                cur = pos[-1][1] + (seq[k] if k < len(seq) else 0.0)
            out = []
            for (lo, hi), (code, sd) in zip(pos, lay):
                inside = any(min(hi, ch.hi) - max(lo, ch.lo) > FACE_TOLERANCE_CM for ch in channels)
                if inside and not _is_channel_code(code):
                    ch = CHANNEL_OF_BLOCK.get(code)
                    if ch is None or self._tpl(ch) is None:
                        return None  # B19/pastilha na verga: nao
                    out.append((ch, 0))
                elif inside or _is_channel_code(code):
                    if not _is_channel_code(code):
                        return None
                    out.append((code, 0))
                else:
                    out.append((code, sd))
            # a verga nunca encolhe: o centro e as pontas de cada canaleta original
            # continuam dentro de canaleta
            ch_new = [pp for pp, (c, _s) in zip(pos, out) if _is_channel_code(c)]
            for ch in channels:
                for t in ((ch.lo + ch.hi) / 2.0, ch.lo + joint + FACE_TOLERANCE_CM, ch.hi - joint - FACE_TOLERANCE_CM):
                    if not any(a - FACE_TOLERANCE_CM <= t <= b + FACE_TOLERANCE_CM for a, b in ch_new):
                        return None
            lay = out
        return tuple(lay)

    def _derived_bridge_layouts(self, bridge_f, span0, orig_lists, active_f, spans, edges):
        """{familia-ponte: layout} - cada fiada-ponte/verga seguindo a grade da
        fiada da jamba de MESMA paridade desta unidade (85.9)."""
        out = {}
        for fb in bridge_f:
            cb = self._courses_of(fb)
            if not cb:
                continue
            run = orig_lists[fb][span0[fb][0]:span0[fb][1] + 1]
            for fa in active_f:
                ca = self._courses_of(fa)
                if not ca or (ca[0] - cb[0]) % 2:
                    continue
                arun = self.fam[fa][spans[fa][0]:spans[fa][1] + 1]
                act = [(e, d) for e, d in edges
                       if any(abs(e - e2) < EDGE_TOLERANCE_CM and d == d2 for e2, d2 in self._active_jamb_edges(fa))]
                lay = self._grid_follow(run, arun, act) if act else None
                if lay:
                    out[fb] = lay
                    break
        return out

    def _cell_intervals(self, slot):
        if not slot.cells:
            return ()
        cs = _cell_centers(slot)
        return tuple((c - half, c + half) for c, (_off, half) in zip(cs, slot.cells))

    def _cell_status(self, iv, dst_slots):
        """'ok' | 'bad' | None (sem vizinha: vao, canaleta) - largura livre comum
        (geometria real, secao 85) da celula `iv` contra a fileira `dst_slots`."""
        from core.engine.prism_free_area import PRISM_MIN_COMMON_WIDTH_CM
        c = (iv[0] + iv[1]) / 2.0
        h = _covering(dst_slots, c)
        if h is None:
            i = _first_hi_at_least(dst_slots, c)
            if 0 < i < len(dst_slots) and dst_slots[i].lo - dst_slots[i - 1].hi <= RUN_MAX_GAP_CM:
                return "bad"  # vazado sobre a junta
            return None
        if _is_channel_code(h.code):
            return None
        best = 0.0
        for q in _in_window(dst_slots, iv[0] - 1.0, iv[1] + 1.0):
            for lo2, hi2 in self._cell_intervals(q):
                if not self._cells_compatible(iv[1] - iv[0], hi2 - lo2):
                    continue
                best = max(best, min(iv[1], hi2) - max(iv[0], lo2))
        return "ok" if best >= PRISM_MIN_COMMON_WIDTH_CM - 1e-6 else "bad"

    def _prism_pairs(self, fams_set):
        """[(fonte, destino, via, peso)] das interfaces que tocam as familias da
        unidade: fiadas vizinhas e, atraves de uma fiada com canaleta (U), a
        fiada seguinte - so' a FASE (a passagem pela U nao e' declarada)."""
        courses = sorted(self.course_fam)
        weights = collections.Counter()
        for c in courses:
            a = self.course_fam[c]
            b = self.course_fam.get(c + 1)
            if b is not None:
                weights[(a, b, None)] += 1
                if any(_is_channel_code(s.code) for s in self.fam[b]):
                    b2 = self.course_fam.get(c + 2)
                    if b2 is not None:
                        weights[(a, b2, b)] += 1
        return sorted(((a, b, via, k) for (a, b, via), k in weights.items()
                       if a in fams_set or b in fams_set),
                      key=lambda t: (t[0], t[1], -1 if t[2] is None else t[2], t[3]))

    def _transparent_fams(self):
        """Familias das fiadas transparentes do estagio A (secao 85/85.9): as
        interfaces com elas nao contam - a ponte/verga ainda vai seguir a grade."""
        if not self._transparent:
            return frozenset()
        return frozenset(self.course_fam[c] for c in self._transparent if c in self.course_fam)

    def _prism_bad(self, pairs3, window):
        n = 0
        tf = self._transparent_fams()
        for a, b, via, k in pairs3:
            if a in tf or b in tf or (via is not None and via in tf):
                continue
            for src, dst in ((a, b), (b, a)):
                dst_slots = self.fam[dst]
                for p in _in_window(self.fam[src], window[0], window[1]):
                    for iv in self._cell_intervals(p):
                        c = (iv[0] + iv[1]) / 2.0
                        if c < window[0] or c > window[1]:
                            continue
                        if via is not None:
                            h = _covering(self.fam[via], c)
                            if h is None or not _is_channel_code(h.code):
                                continue
                        if self._cell_status(iv, dst_slots) == "bad":
                            n += k
        return n

    def _prism_misaligned(self, a, b, window):
        """Compatibilidade: interfaces diretas entre `a` e `b` (regua por area)."""
        return self._prism_bad([(a, b, None, 1)], window)

    @staticmethod
    def _cells_compatible(w1, w2):
        """Secao 85.8: vazado menor (B34) x vazado principal nao forma coluna."""
        return not (min(w1, w2) < SMALL_CELL_MAX_CM and max(w1, w2) > MAIN_CELL_MIN_CM)

    def _trace_column(self, c0, cell, restart=True):
        """(ok, menor_largura) da coluna que passa pela celula `cell` da fiada
        `c0`, na ALTURA INTEIRA: fiada a fiada a celula que mais se sobrepoe,
        intersecao acumulada >= PRISM_MIN_COMMON_WIDTH_CM; vao e canaleta so' pela
        fase; vazado sobre junta ou peca macica = quebra; vazado menor sobre vazado
        principal = quebra (85.8). `restart`: cada sentido (desce/sobe) parte da
        propria celula - a mesma definicao de `prism_free_area.column_census`."""
        from core.engine.prism_free_area import PRISM_MIN_COMMON_WIDTH_CM
        narrowest = cell[1] - cell[0]
        col = cell
        for step in (-1, 1):
            if restart:
                col = cell
            prev_w = cell[1] - cell[0]
            c = c0 + step
            while c in self.course_fam:
                if c in self._transparent:
                    c += step
                    continue
                slots = self.fam[self.course_fam[c]]
                mid = (col[0] + col[1]) / 2.0
                host = _covering(slots, mid)
                if host is None:
                    i = _first_hi_at_least(slots, mid)
                    if 0 < i < len(slots) and slots[i].lo - slots[i - 1].hi <= RUN_MAX_GAP_CM:
                        return False, 0.0  # vazado sobre a junta
                    c += step
                    continue
                if _is_channel_code(host.code):
                    c += step
                    continue
                best = None
                for q in _in_window(slots, col[0] - 1.0, col[1] + 1.0):
                    for lo2, hi2 in self._cell_intervals(q):
                        if not self._cells_compatible(prev_w, hi2 - lo2):
                            continue
                        w = min(col[1], hi2) - max(col[0], lo2)
                        if best is None or w > best[0]:
                            best = (w, (max(col[0], lo2), min(col[1], hi2)), hi2 - lo2)
                if best is None or best[0] < PRISM_MIN_COMMON_WIDTH_CM - 1e-6:
                    return False, (best[0] if best else 0.0)
                col = best[1]
                prev_w = best[2]
                narrowest = min(narrowest, col[1] - col[0])
                c += step
        return True, round(narrowest, 2)

    def _jamb_path(self, edge, d):
        """SECAO 85 - percurso obrigatorio da jamba `edge` (lado `d`): parte da
        celula mais proxima da borda (ate' JAMB_PATH_REACH_CM) na primeira fiada
        em que a abertura corta a fileira e segue, fiada a fiada, a celula que mais
        se sobrepoe a ela na ALTURA INTEIRA da parede (abaixo e acima da abertura;
        canaleta e vao atravessados so' pela fase), com a intersecao ACUMULADA.
        Devolve (ok, largura_comum_cm): ok = largura >= PRISM_MIN_COMMON_WIDTH_CM
        em todas as fiadas; vazado sobre junta ou peca macica = quebrado."""
        from core.engine.prism_free_area import PRISM_MIN_COMMON_WIDTH_CM
        courses = sorted(self.course_fam)
        seed = None
        for c in courses:
            f = self.course_fam[c]
            if not any(abs(e - edge) < EDGE_TOLERANCE_CM and dd == d for e, dd in self._active_jamb_edges(f)):
                continue
            for q in _in_window(self.fam[f], edge - JAMB_PATH_REACH_CM - 40.0, edge + JAMB_PATH_REACH_CM + 40.0):
                if _is_channel_code(q.code):
                    continue
                for lo2, hi2 in self._cell_intervals(q):
                    dist = (lo2 - edge) if d > 0 else (edge - hi2)
                    if -0.5 <= dist <= JAMB_PATH_REACH_CM and (seed is None or dist < seed[0]):
                        seed = (dist, (lo2, hi2), c)
            if seed is not None:
                break
        if seed is None:
            return True, None  # nenhuma celula junto da jamba (ex.: faixa macica inteira): nada a exigir aqui
        return self._trace_column(seed[2], seed[1], restart=False)

    def _staged_search(self, fams, active_f, bridge_f, options, start, base, measure, objective,
                       best, best_any, derive=None):
        """SECAO 85 - pontos criticos compatibilizados com alternativas: A) as
        JAMB_ALT_TOPK melhores combinacoes das fiadas da jamba, com as fiadas-ponte
        transparentes (so a fase atravessa); B) para cada uma, descida nas
        fiadas-ponte com a regua completa. Nada e consolidado antes de B."""
        bridge_courses = frozenset(c for c in self.course_fam if self.course_fam[c] in bridge_f)
        saved = self._transparent
        self._transparent = bridge_courses
        try:
            assigns = [dict(start)]
            # 85.9: triagem por familia - opcao com falha INTRINSECA (pastilha nova,
            # pastilha fora da jamba, B19 fora de fechamento...) medida com as outras
            # fiadas como estao sai antes da combinacao. Sem isso 66 x 63 = 4.158
            # combinacoes passavam do orcamento e o estagio A caia na descida fiada a
            # fiada, que nunca troca as duas paridades juntas (W4, grade de B34)
            screened = {}
            for f in active_f:
                keep = [start[f]]
                for o in options[f]:
                    if o == start[f]:
                        continue
                    trial = dict(start)
                    trial[f] = o
                    if not any(x in JAMB_INTRINSIC_FAILURES for x in self._jamb_failures(measure(trial), base)):
                        keep.append(o)
                screened[f] = keep
            n = 1
            for f in active_f:
                n *= len(screened[f])
            if n <= JAMB_ALT_MAX_EVAL:
                for f in active_f:
                    assigns = [_merged(a, f, o) for a in assigns for o in screened[f]]
            else:
                current = dict(start)
                for _round in range(JAMB_DESCENT_ROUNDS):
                    improved = False
                    for f in active_f:
                        for o in options[f]:
                            trial = dict(current)
                            trial[f] = o
                            assigns.append(trial)
                            if objective(measure(trial), trial) < objective(measure(current), current):
                                current, improved = trial, True
                    if not improved:
                        break
            def rank(a):
                m = measure(a)
                intrinsic = sum(1 for x in self._jamb_failures(m, base) if x in JAMB_INTRINSIC_FAILURES)
                return (intrinsic, objective(m, a))

            ranked = sorted(((rank(a), a) for a in assigns), key=lambda item: item[0])
            seeds, seen = [], set()
            for _obj, a in ranked:
                sig = tuple(a[f] for f in active_f)
                if sig in seen:
                    continue
                seen.add(sig)
                seeds.append(a)
                if len(seeds) >= JAMB_ALT_TOPK:
                    break
            if tuple(start[f] for f in active_f) not in seen:
                seeds.append(dict(start))
        finally:
            self._transparent = saved
        for seed in seeds:
            current = seed = dict(seed)
            m = measure(current)
            obj = objective(m, current)
            if obj < best_any[0]:
                best_any = (obj, current)
            if not self._jamb_failures(m, base) and obj < best[0]:
                best = (obj, current)
            if derive is not None:
                # 85.9: a ponte/verga seguindo a grade da lateral, TODAS juntas
                # (uma fiada so' nunca melhora sozinha: a coluna quebra na outra)
                trial = derive(seed)
                if trial is not None:
                    m = measure(trial)
                    obj = objective(m, trial)
                    if obj < best_any[0]:
                        best_any = (obj, trial)
                    if not self._jamb_failures(m, base) and obj < best[0]:
                        best = (obj, trial)
                    if obj < objective(measure(current), current):
                        current = trial
            if all(seed[f] == start[f] for f in active_f) and current is seed:
                continue  # mesma lateral: a ponte nao tem o que acompanhar
            for _round in range(JAMB_BRIDGE_DESCENT_ROUNDS):
                improved = False
                for f in bridge_f:
                    for o in options[f][:JAMB_BRIDGE_OPTIONS_MAX]:
                        trial = dict(current)
                        trial[f] = o
                        m = measure(trial)
                        obj = objective(m, trial)
                        if obj < best_any[0]:
                            best_any = (obj, trial)
                        if obj < objective(measure(current), current):
                            current, improved = trial, True
                        if not self._jamb_failures(m, base) and obj < best[0]:
                            best = (obj, trial)
                if not improved:
                    break
        return best, best_any

    def _jamb_paths_ok(self, edges):
        return sum(1 for e, d in edges if self._jamb_path(e, d)[0])

    def _column_cells(self, fams, window):
        return self._column_stats(fams, window)[0]

    # (contagem, soma das larguras, colunas cheias) - ver `_column_stats`

    def _column_stats(self, fams, window):
        """SECAO 85: (celulas em coluna continua, soma das menores larguras,
        colunas de vazado principal cheias) das familias da unidade na janela -
        avaliadas em CADA fiada da familia com a regua unica `_trace_column`
        (mesma definicao da regua independente `column_census`: uma troca que so'
        muda a quebra de lugar nao conta; vazado menor sobre principal quebra)."""
        courses = sorted(self.course_fam)
        n = 0
        width_sum = 0.0
        full = 0
        for f in fams:
            member_courses = [c for c in courses if self.course_fam[c] == f]
            if not member_courses:
                continue
            for p in _in_window(self.fam[f], window[0], window[1]):
                for iv in self._cell_intervals(p):
                    for c0 in member_courses:
                        ok, narrowest = self._trace_column(c0, iv, restart=True)
                        if not ok:
                            continue
                        n += 1
                        width_sum += narrowest
                        if narrowest >= PRISM_FULL_COLUMN_WIDTH_CM - 1e-6:
                            full += 1
        return n, round(width_sum, 2), full

    def _coherence_mismatch(self, fams, spans, window, edges):
        """SECAO 85 - referencia modular comum: as juntas da corrida da unidade
        contra as da fiada CHEIA de mesma paridade mais proxima ABAIXO da abertura
        (a abertura so' recorta a grade; nao reinicia a fase). Porta (sem fiada
        cheia abaixo) nao tem referencia aqui: vale 0."""
        courses = sorted(self.course_fam)
        edge_ts = [e for e, _d in edges]
        n = 0
        for f in fams:
            member = [c for c in courses if self.course_fam[c] == f]
            if not member:
                continue
            i0, i1 = spans[f]
            lo, hi = self.fam[f][i0].lo, self.fam[f][i1].hi
            ref = None
            for r in range(member[0] - 2, -1, -2):
                if r not in self.course_fam:
                    continue
                rf = self.course_fam[r]
                slots = self.fam[rf]
                if any(_covering(slots, t) is None for t in edge_ts):
                    continue  # a abertura tambem corta essa fiada
                if any(_is_channel_code(s.code) for s in _in_window(slots, lo, hi)):
                    continue
                ref = slots
                break
            if ref is None:
                continue
            inside = (lo + 0.5, hi - 0.5)
            mine = [x for x in _internal_faces(self.fam[f], self.length, self.edges, inside)
                    if inside[0] < x < inside[1]]
            theirs = [x for x in _internal_faces(ref, self.length, self.edges, inside)
                      if inside[0] < x < inside[1]]
            mism = sum(1 for x in mine if not _has_value_near(theirs, x, FACE_TOLERANCE_CM))
            mism += sum(1 for x in theirs if not _has_value_near(mine, x, FACE_TOLERANCE_CM))
            n += mism * self.count[f]
        return n

    def _coincident_nonexempt(self, a, b, window):
        """Faces da familia `a` na janela que coincidem com uma face da `b` - menos
        a junta da faixa de jamba. Mesma leitura da auditoria de producao (secao
        11.8): a junta da peca de fechamento encostada no vao e' isenta na PROPRIA
        fiada, e isso ja' interrompe a sequencia vertical - vale quando a face e'
        da faixa em pelo menos uma das duas fiadas (ex.: a junta entre as canaletas
        da verga logo acima da faixa). So' a junta da faixa: nenhuma outra."""
        faces_a = _internal_faces(self.fam[a], self.length, self.edges, window)
        faces_b = _internal_faces(self.fam[b], self.length, self.edges,
                                  (window[0] - FACE_TOLERANCE_CM, window[1] + FACE_TOLERANCE_CM))
        strip_a, strip_b = self._jamb_strip_faces(a), self._jamb_strip_faces(b)
        if JAMB_CLOSURE_B19_JOINT_EXEMPT:
            b19_a, b19_b = self._jamb_strip_faces(a, b19=True), self._jamb_strip_faces(b, b19=True)
        else:
            b19_a = b19_b = ()
        out = []
        for face in faces_a:
            if not _has_value_near(faces_b, face, FACE_TOLERANCE_CM):
                continue
            if _has_value_near(strip_a, face, FACE_TOLERANCE_CM) or \
                    _has_value_near(strip_b, face, FACE_TOLERANCE_CM):
                continue
            # 11.8 / 85.9: junta do B19 de fechamento isenta so' contra uma junta
            # que NAO e' de fechamento de B19 (B19 sobre B19 = pilar a prumo)
            if _has_value_near(b19_a, face, FACE_TOLERANCE_CM) != _has_value_near(b19_b, face, FACE_TOLERANCE_CM):
                continue
            out.append(face)
        return out

    def _stacks_nonexempt(self, window):
        """Juntas NAO isentas que se repetem em 3+ fiadas seguidas, na janela."""
        cache = {}
        faces = {}
        for c in sorted(self.course_fam):
            f = self.course_fam[c]
            if f not in cache:
                strip = self._jamb_strip_faces(f)
                cache[f] = [x for x in _internal_faces(self.fam[f], self.length, self.edges, window)
                            if not _has_value_near(strip, x, FACE_TOLERANCE_CM)]
            faces[c] = cache[f]
        empty = []
        n = 0
        for c in sorted(faces):
            for face in faces[c]:
                if _has_value_near(faces.get(c - 1, empty), face, FACE_TOLERANCE_CM):
                    continue
                length, cc = 1, c
                while _has_value_near(faces.get(cc + 1, empty), face, FACE_TOLERANCE_CM):
                    length += 1
                    cc += 1
                if length >= 3:
                    n += 1
        return n

    @staticmethod
    def _unmatched(intervals_a, intervals_b):
        """Compensadores de `a` sem compensador de `b` na mesma faixa vertical
        (sobreposicao >= metade do menor): quebras da coluna entre as fiadas."""
        n = 0
        for lo, hi in intervals_a:
            if not any(min(hi, hi2) - max(lo, lo2) >= 0.5 * min(hi - lo, hi2 - lo2)
                       for lo2, hi2 in intervals_b):
                n += 1
        return n

    def _jamb_measure(self, fams, span_of, edges, pairs, pairs3, window, base_codes):
        dist = 0.0
        comp_iv = {}
        moved = comps = pieces = offjamb = 0
        for f in fams:
            ivs = []
            i0, i1 = span_of[f]
            codes_now = [self.fam[f][i].code for i in range(i0, i1 + 1)]
            if codes_now != base_codes[f]:
                moved += self.count[f] * max(1, sum(1 for a, b in zip(codes_now, base_codes[f]) if a != b)
                                             + abs(len(codes_now) - len(base_codes[f])))
            pieces += len(codes_now) * self.count[f]
            for i in range(i0, i1 + 1):
                s = self.fam[f][i]
                if not s.compensator:
                    continue
                comps += self.count[f]
                best = self._strip_distance(f, i, edges)
                if best is not None and best > JAMB_TOUCH_TOLERANCE_CM:
                    dist += min(best, JAMB_REACH_CM) * self.count[f]
                if (best is None or best > JAMB_TOUCH_TOLERANCE_CM) and not self._node_closure(f, i):
                    offjamb += self.count[f]  # 85.8: pastilha fora da jamba e fora de encontro
                ivs.append((s.lo, s.hi))
            comp_iv[f] = ivs
        breaks = 0
        tf = self._transparent_fams()
        for a, b, k in pairs:
            if a in tf or b in tf:
                continue
            if a != b and a in comp_iv and b in comp_iv:
                breaks += k * (self._unmatched(comp_iv[a], comp_iv[b]) + self._unmatched(comp_iv[b], comp_iv[a]))
        cp = ht = ex = b19 = 0
        wide = (window[0] - WINDOW_PAD_CM, window[1] + WINDOW_PAD_CM)
        for f in fams:
            near = _in_window(self.fam[f], wide[0], wide[1])
            cp += _compensator_guard(near, self.length) * self.count[f]
            ht += self._half_near_ties(near, f)
            ex += _long_compensator_extremes(self.fam[f], self.length) * self.count[f]
            b19 += self._half_blocks_misplaced(f, window) * self.count[f]
        sv = 0
        joints = set()
        for a, b, k in pairs:
            if a in tf or b in tf:
                continue
            sv += k * _violations_between(self.fam[a], self.fam[b], self.tol, window)
            if a != b:
                for face in self._coincident_nonexempt(a, b, window):
                    joints.add((round(face, 1), min(a, b), max(a, b)))
        colstats = self._column_stats(fams, window)
        return {"dist": round(dist, 3), "breaks": breaks, "cp": cp, "ht": ht, "ex": ex, "sv": sv,
                "prism": self._prism_bad(pairs3, window), "b19": b19, "comps": comps, "pieces": pieces,
                "column": colstats[0], "colw": colstats[1], "colfull": colstats[2], "offjamb": offjamb,
                "paths": self._jamb_paths_ok(edges),
                "coh": self._coherence_mismatch(fams, span_of, window, edges),
                "joints": joints, "stacks": self._stacks_nonexempt(window), "moved": moved}

    @staticmethod
    def _jamb_failures(m, base):
        fails = []
        if m["sv"] > base["sv"]:
            fails.append("SMALL_VOID_WOULD_MISALIGN")
        # 85.8 (correcoes do usuario): nenhuma pastilha nova e nenhuma pastilha a
        # mais fora da jamba (atras do B19, no meio do trecho) - a de fechamento
        # de encontro nao conta
        if m["comps"] > base["comps"]:
            fails.append("NEW_COMPENSATOR")
        if m.get("offjamb", 0) > base.get("offjamb", 0):
            fails.append("COMPENSATOR_OFF_JAMB")
        if m.get("paths", 0) < base.get("paths", 0):
            fails.append("PRISM_REQUIRED_PATH_WOULD_BREAK")
        if m["column"] < base["column"]:
            fails.append("PRISM_COLUMN_WOULD_BREAK")
        if m["prism"] > base["prism"]:
            fails.append("PRISM_WOULD_BREAK")
        if m["b19"] > base["b19"]:
            fails.append("HALF_BLOCK_NOT_ADMISSIBLE")
        if m["cp"] > base["cp"]:
            fails.append("ADJACENT_COMPENSATORS")
        if m["ht"] > base["ht"]:
            fails.append("HALF_BLOCK_NEAR_TIE")
        if m["ex"] > base["ex"]:
            fails.append("LONG_COMPENSATOR_AT_WALL_END")
        if not m["joints"] <= base["joints"]:
            fails.append("NEW_COINCIDENT_JOINT")
        if m["stacks"] > base["stacks"]:
            fails.append("STACKED_JOINT")
        return fails

    def _layout_options(self, f, span, extra_codes=()):
        """Candidatas da corrida `span` da familia `f`: a atual, as outras ORDENS
        das mesmas pecas e (secao 85) as COMPOSICOES de mesmo comprimento com +-1
        peca do catalogo de preenchimento (B39/B34/B19/C09/C04) - prisma vem antes
        de 'menos compensadores' no pedido do usuario. Cada candidata =
        tupla de (codigo, lado)."""
        i0, i1 = span
        slots = self.fam[f]
        run = slots[i0:i1 + 1]
        current = tuple((s.code, s.side if s.orientable else 0) for s in run)
        out = [current]
        seen = set([current])
        for order in _multiset_orders(collections.Counter(current), len(current), JAMB_MAX_ORDERS_PER_FAMILY):
            if order not in seen:
                seen.add(order)
                out.append(order)
        if not JAMB_COMPOSITION_ENABLED:
            return out
        if any(_is_channel_code(sl.code) for sl in run):
            # fiada da verga (85.9): canaleta nunca e' permutada nem composta as
            # cegas; so' a grade derivada da jamba (`_grid_follow`) muda ela
            return [current]
        gaps = [run[k + 1].lo - run[k].hi for k in range(len(run) - 1)]
        joint = sorted(gaps)[len(gaps) // 2] if gaps else 1.0
        if any(abs(g - joint) > JOINT_REGULAR_TOLERANCE_CM for g in gaps):
            return out  # juntas irregulares: so' permutacao (pontas exatas)
        total = run[-1].hi - run[0].lo
        units = {}
        for code in tuple(JAMB_COMPOSITION_CODES) + tuple(extra_codes or ()):
            tpl = self._tpl(code)
            if tpl is not None:
                units[code] = tpl.hi - tpl.lo
        codes = sorted(units)
        target = total + joint
        extra = []
        for size in range(max(1, len(run) - 1), len(run) + JAMB_COMPOSITION_MAX_EXTRA + 1):
            if size > JAMB_UNIT_MAX_PIECES:
                break
            for combo in _combinations_with_replacement(codes, size):
                if abs(sum(units[c] + joint for c in combo) - target) > 0.05:
                    continue
                if sorted(combo) == sorted(c for c, _s in current):
                    continue
                extra.append(combo)
        budget = JAMB_MAX_COMPOSITION_ORDERS
        # 85.9: sem compensador e SEM B19 primeiro (B19 so' em fechamento) - antes
        # as ordens de `B19 + B34 + B39...` esgotavam o orcamento e a grade de B34
        # pura (`6 x B34`) nem entrava na lista
        for combo in sorted(extra, key=lambda cb: (sum(1 for c in cb if self._tpl(c).compensator),
                                                   sum(1 for c in cb if c == "B19"), len(cb), cb)):
            for order in _multiset_orders(collections.Counter(combo), len(combo), 60):
                for sides in _side_patterns(order, self._tpl):
                    cand = tuple(zip(order, sides))
                    if cand not in seen:
                        seen.add(cand)
                        out.append(cand)
                        budget -= 1
                        if budget <= 0:
                            return out
        return out

    def _splice_layout(self, f, span, layout, joint):
        """Troca a corrida `span` por `layout` (mesmas pontas); devolve o novo span.
        Com o MESMO numero de pecas preserva a sequencia real de juntas (indice a
        indice); composicao nova so' existe com juntas uniformes (`joint`)."""
        i0, i1 = span
        slots = self.fam[f]
        old = slots[i0:i1 + 1]
        gaps = [old[k + 1].lo - old[k].hi for k in range(len(old) - 1)]
        if len(layout) != len(old):
            gaps = [joint] * (len(layout) - 1)
        cur = slots[i0].lo
        new = []
        for k, (code, side) in enumerate(layout):
            tpl = self._tpl(code)
            sl = tpl.copy()
            sl.lo, sl.hi = cur, cur + (tpl.hi - tpl.lo)
            sl.movable, sl.node = not _is_channel_code(code), False
            sl.side = (side or 1) if sl.orientable else 0
            new.append(sl)
            cur = sl.hi + (gaps[k] if k < len(gaps) else 0.0)
        self.fam[f] = slots[:i0] + new + slots[i1 + 1:]
        return (i0, i0 + len(new) - 1)

    def _solve_jamb_unit(self, key, members, extra_codes=()):
        """Resolve UMA lateral (ou pilarete) com TODAS as familias de fiada dela
        juntas. Devolve True se mudou alguma peca."""
        fams = [f for f, _span, _edges in members]
        span0 = dict((f, span) for f, span, _edges in members)
        edges = sorted(set((e, d) for _f, _sp, es in members for e, d in es))
        lo = min(self.fam[f][span0[f][0]].lo for f in fams)
        hi = max(self.fam[f][span0[f][1]].hi for f in fams)
        window = (lo - 1.0, hi + 1.0)
        pairs = sorted((a, b, k) for (a, b), k in self.weights.items() if a in span0 or b in span0)
        pairs3 = self._prism_pairs(set(fams))
        orig_lists = dict((f, list(self.fam[f])) for f in fams)
        joints = {}
        for f in fams:
            run = self.fam[f][span0[f][0]:span0[f][1] + 1]
            gaps = [run[k + 1].lo - run[k].hi for k in range(len(run) - 1)]
            joints[f] = sorted(gaps)[len(gaps) // 2] if gaps else 1.0
        base_codes = dict((f, [s.code for s in self.fam[f][span0[f][0]:span0[f][1] + 1]]) for f in fams)
        options = dict((f, self._layout_options(f, span0[f], extra_codes)) for f in fams)

        def apply(assign):
            spans = {}
            for f in fams:
                self.fam[f] = list(orig_lists[f])
                if assign[f] == options[f][0]:
                    spans[f] = span0[f]
                else:
                    spans[f] = self._splice_layout(f, span0[f], assign[f], joints[f])
            return spans

        def restore():
            for f in fams:
                self.fam[f] = list(orig_lists[f])

        verga_f = [f for f in fams
                   if any(_is_channel_code(sl.code) for sl in orig_lists[f][span0[f][0]:span0[f][1] + 1])]

        def derive(assign, active, bridge):
            """85.9: as fiadas-ponte/verga seguindo a grade das fiadas da jamba
            de `assign` - novas opcoes entram no fim da lista (desempate)."""
            if not (JAMB_GRID_FOLLOW_ENABLED and active and bridge):
                return None
            spans = apply(assign)
            try:
                der = self._derived_bridge_layouts(bridge, span0, orig_lists, active, spans, edges)
            finally:
                restore()
            if not der:
                return None
            trial = dict(assign)
            for f, lay in der.items():
                if lay not in options[f]:
                    options[f].append(lay)
                trial[f] = lay
            return trial

        memo = {}

        def measure(assign):
            sig = (bool(self._transparent),) + tuple(assign[f] for f in fams)
            if sig not in memo:
                spans = apply(assign)
                memo[sig] = self._jamb_measure(fams, spans, edges, pairs, pairs3, window, base_codes)
                restore()
            return memo[sig]

        # secao 85: B19 fora de fechamento e' proibido (1o); depois a coluna de
        # vazados continua na ALTURA INTEIRA (uma troca que so' muda a quebra de
        # lugar nao conta), a referencia modular comum com a fiada cheia de mesma
        # paridade, a regua por interface, e so' entao a faixa da jamba (84).
        def objective(m, assign):
            # a LARGURA livre comum (menor largura ao longo da coluna, somada)
            # desempata colunas que so' raspam o limiar no vazado menor do B34
            # 85.8: vazado menor do B34 fora de vazado menor/central (sv) e' prisma
            # quebrado - vem logo depois do B19; a faixa encostada na jamba (dist)
            # vem antes da soma de larguras
            return (m["b19"], m["sv"], -m["paths"], -m["column"], m["coh"], -m["colfull"], m["dist"],
                    -m["colw"], m["prism"], m["breaks"], m["comps"], m["pieces"], m["moved"],
                    tuple(options[f].index(assign[f]) for f in fams))

        start = dict((f, options[f][0]) for f in fams)
        base = measure(start)
        base_obj = objective(base, start)
        # faixa reta e encostada NAO prova prisma (pedido do usuario): so' sai sem
        # procurar quando os percursos das jambas e TODAS as celulas da unidade ja'
        # sao colunas continuas na altura inteira
        all_cells = sum(len(self._cell_intervals(p)) * self.count[f] for f in fams
                        for p in _in_window(self.fam[f], window[0], window[1]))
        settled = (base["prism"] == 0 and base["b19"] == 0 and base["dist"] == 0.0 and base["breaks"] == 0
                   and base["paths"] == len(edges) and base["column"] >= all_cells)
        if settled:
            return False
        total = 1
        for f in fams:
            total *= len(options[f])
        best = (base_obj, start)
        best_any = best
        bridge_f = [f for f, _sp, es in members
                    if not any(abs(e - edge) < EDGE_TOLERANCE_CM and dd == d
                               for e, dd in self._active_jamb_edges(f) for edge, d in es)]
        active_f = [f for f in fams if f not in bridge_f]
        defect = (base["paths"] < len(edges) or base["b19"] > 0 or base["dist"] > 0.0 or base["prism"] > 0)
        if bridge_f and active_f and total > JAMB_JOINT_MAX_COMBINATIONS and not defect:
            # sem defeito na lateral: so' as fiadas da jamba (ponte fica como esta')
            fams_search = active_f
            total = 1
            for f in active_f:
                total *= len(options[f])
            if total <= JAMB_JOINT_MAX_COMBINATIONS:
                assigns = [dict(start)]
                for f in active_f:
                    assigns = [_merged(a, f, o) for a in assigns for o in options[f]]
                for assign in assigns:
                    m = measure(assign)
                    obj = objective(m, assign)
                    if obj < best_any[0]:
                        best_any = (obj, assign)
                    if not self._jamb_failures(m, base) and obj < best[0]:
                        best = (obj, assign)
                total = 0
            del fams_search
        if bridge_f and active_f and total > JAMB_JOINT_MAX_COMBINATIONS:
            best, best_any = self._staged_search(fams, active_f, bridge_f, options, start, base, measure,
                                                 objective, best, best_any,
                                                 derive=lambda a: derive(a, active_f, bridge_f))
            total = 0  # resolvido pela busca em estagios
        candidates = None
        if total == 0:
            pass
        elif total <= JAMB_JOINT_MAX_COMBINATIONS:
            assigns = [{}]
            for f in fams:
                assigns = [_merged(a, f, o) for a in assigns for o in options[f]]
            candidates = assigns
        else:
            candidates = None
        if candidates is not None:
            for assign in candidates:
                m = measure(assign)
                obj = objective(m, assign)
                if obj < best_any[0]:
                    best_any = (obj, assign)
                if not self._jamb_failures(m, base) and obj < best[0]:
                    best = (obj, assign)
        if total == 0 or total <= JAMB_JOINT_MAX_COMBINATIONS:
            pass
        else:
            current = dict(start)
            for _round in range(JAMB_DESCENT_ROUNDS):
                improved = False
                for f in fams:
                    for o in options[f]:
                        trial = dict(current)
                        trial[f] = o
                        m = measure(trial)
                        obj = objective(m, trial)
                        if obj < best_any[0]:
                            best_any = (obj, trial)
                        if not self._jamb_failures(m, base) and obj < best[0]:
                            best = (obj, trial)
                            current = trial
                            improved = True
                if not improved:
                    break
        if bridge_f and active_f:
            # 85.9: a melhor lateral encontrada com a ponte/verga seguindo a grade
            for seed in (best[1], best_any[1]):
                trial = derive(seed, active_f, bridge_f)
                if trial is None:
                    continue
                m = measure(trial)
                obj = objective(m, trial)
                if obj < best_any[0]:
                    best_any = (obj, trial)
                if not self._jamb_failures(m, base) and obj < best[0]:
                    best = (obj, trial)
        chosen_obj, chosen = best
        changed = chosen_obj[:12] < base_obj[:12]
        # tudo o que usa `measure` (aplica, mede e RESTAURA) vem antes de aplicar
        final = measure(chosen)
        reasons = ["NO_LAYOUT_REACHES_JAMB"]
        detail = {}
        blocked = final["dist"] > 0.0 or final["b19"] > 0 or final["prism"] > 0 or final["paths"] < len(edges)
        if blocked and best_any[0][:9] < chosen_obj[:9]:
            blocked_by = measure(best_any[1])
            reasons = self._jamb_failures(blocked_by, base) or reasons
            new_joints = sorted(set(j[0] for j in blocked_by["joints"] - base["joints"]))
            if new_joints:
                detail["new_joint_faces_cm"] = new_joints
        self._unit_reasons[key] = (list(reasons), dict(detail))
        spans = span0
        if changed:
            spans = apply(chosen)
            for f in verga_f:
                if chosen[f] != options[f][0]:
                    # 85.9: a fiada da verga mudou - o write-back refaz o trecho
                    run = self.fam[f][spans[f][0]:spans[f][1] + 1]
                    self.verga_changes.append((f, min(orig_lists[f][span0[f][0]].lo, run[0].lo),
                                               max(orig_lists[f][span0[f][1]].hi, run[-1].hi)))
        detail["prism_bad_before"] = base["prism"]
        detail["prism_bad_after"] = final["prism"]
        detail["prism_column_cells_before"] = base["column"]
        detail["prism_column_cells_after"] = final["column"]
        detail["required_paths"] = len(edges)
        detail["required_paths_ok_before"] = base["paths"]
        detail["required_paths_ok_after"] = final["paths"]
        for f in fams:
            i0, i1 = spans[f]
            far = [self._strip_distance(f, i, edges) for i in range(i0, i1 + 1)
                   if self.fam[f][i].compensator and not self._node_closure(f, i)]
            far = [x for x in far if x is not None and x > JAMB_TOUCH_TOLERANCE_CM]
            misplaced = [self.fam[f][i].code for i in range(i0, i1 + 1)
                         if self.fam[f][i].code == "B19" and not self._half_block_admissible(f, i)]
            if far or misplaced:
                self.jamb_conflicts.append({
                    "wall_idx": self.wall_idx, "edges_cm": [round(e, 1) for e, _d in edges],
                    "side": edges[0][1] if len(edges) == 1 else 0, "courses": self._courses_of(f),
                    "distance_cm": round(min(far), 1) if far else None,
                    "codes": [self.fam[f][i].code for i in range(i0, i1 + 1)],
                    "reasons": reasons + (["HALF_BLOCK_NOT_ADMISSIBLE_REMAINS"] if misplaced else []),
                    "detail": dict(detail)})
        return bool(changed)

    def align_jamb_compensators(self):
        """SECOES 84/85: lateral de abertura resolvida com as fiadas em conjunto -
        prisma pela area livre comum real primeiro, B19 so' em fechamento
        admissivel, faixa de compensacao encostada e alinhada. Devolve quantas
        laterais mudaram; os casos que nao fecham ficam em `self.jamb_conflicts`."""
        self.jamb_conflicts = []
        self._unit_reasons = {}
        if not self.jamb_alignment:
            return 0
        changed = 0
        done = set()
        blocked_all = []
        for _round in range(JAMB_UNIT_ROUNDS):
            units, blocked = self._jamb_units()
            if _round == 0:
                blocked_all = blocked
            progressed = False
            for key in sorted(units, key=lambda k: self._unit_priority(k, units[k])):
                if key in done:
                    continue
                conflicts_before = len(self.jamb_conflicts)
                if self._solve_jamb_unit(key, units[key]):
                    changed += 1
                    done.add(key)
                    progressed = True
                    # os indices das familias mudaram: recalcula as unidades
                    break
                del self.jamb_conflicts[conflicts_before:]
                done.add(key)
            if not progressed:
                break
        # compatibilizacao: percurso obrigatorio quebrado DEPOIS das vizinhas
        revisited = collections.Counter()
        for _round in range(JAMB_COMPAT_ROUNDS):
            units, _blocked = self._jamb_units()
            again = [k for k in sorted(units, key=lambda k: self._unit_priority(k, units[k]))
                     if revisited[k] < JAMB_COMPAT_ROUNDS
                     and self._jamb_paths_ok(sorted(set((e, d) for _f, _sp, es in units[k] for e, d in es)))
                     < len(set((e, d) for _f, _sp, es in units[k] for e, d in es))]
            if not again:
                break
            moved_any = False
            for key in again:
                revisited[key] += 1
                units, _blocked = self._jamb_units()
                if key not in units:
                    continue
                conflicts_before = len(self.jamb_conflicts)
                if self._solve_jamb_unit(key, units[key]):
                    changed += 1
                    moved_any = True
                else:
                    del self.jamb_conflicts[conflicts_before:]
            if not moved_any:
                break
        self.compat_revisits = dict((str(k), v) for k, v in revisited.items())
        if HALF_BLOCK_FIX_ENABLED:
            changed += self._fix_misplaced_half_blocks()
        # registro final (estado aplicado): conflitos das unidades remanescentes
        self.jamb_conflicts = list(blocked_all)
        self.broken_paths = []
        units, _blocked = self._jamb_units()
        for key in sorted(units):
            self._report_unit(key, units[key])
        return changed

    def required_paths(self):
        """SECAO 85: [(borda, sentido, ok, largura)] de TODAS as jambas da parede
        (o percurso de graute/vergalhao junto de cada abertura)."""
        out = []
        for lo, hi in self.openings_cm:
            for edge, d in ((lo, -1), (hi, 1)):
                ok, width = self._jamb_path(edge, d)
                out.append((edge, d, ok, width))
        return out

    def _half_block_units(self):
        """{chave: membros} - corridas MOVEIS em volta de cada B19 fora de
        fechamento, por familia; corridas de familias diferentes que se sobrepoem
        (as fiadas alternadas do mesmo trecho) viram UMA unidade."""
        runs = []
        for f in sorted(self.fam):
            slots = self.fam[f]
            edges = self._active_jamb_edges(f)
            for i, sl in enumerate(slots):
                if sl.code != "B19" or not sl.movable or self._half_block_admissible(f, i, edges):
                    continue
                i0 = i1 = i
                while (i0 - 1 >= 0 and slots[i0 - 1].movable and i1 - i0 + 1 < JAMB_UNIT_MAX_PIECES
                       and slots[i0].lo - slots[i0 - 1].hi <= RUN_MAX_GAP_CM):
                    i0 -= 1
                while (i1 + 1 < len(slots) and slots[i1 + 1].movable and i1 - i0 + 1 < JAMB_UNIT_MAX_PIECES
                       and slots[i1 + 1].lo - slots[i1].hi <= RUN_MAX_GAP_CM):
                    i1 += 1
                if i1 > i0:
                    runs.append((slots[i0].lo, slots[i1].hi, f, (i0, i1)))
        units = []
        for lo, hi, f, span in sorted(runs):
            for u in units:
                if lo < u["hi"] and hi > u["lo"] and all(mf != f for mf, _sp, _e in u["members"]):
                    u["members"].append((f, span, []))
                    u["lo"], u["hi"] = min(u["lo"], lo), max(u["hi"], hi)
                    break
            else:
                units.append({"lo": lo, "hi": hi, "members": [(f, span, [])]})
        return [((("B19", round(u["lo"], 1)),), u["members"]) for u in units]

    def _fix_misplaced_half_blocks(self):
        """SECAO 85.8: tira o B19 do miolo onde nenhuma lateral de abertura o
        alcanca (ex.: caixa de shaft). Mesmas falhas duras do recompositor
        (prisma, pastilha nova, pastilha fora da jamba, juntas)."""
        changed = 0
        tried = set()
        for _round in range(JAMB_COMPAT_ROUNDS + 2):
            progressed = False
            for key, members in self._half_block_units():
                if key in tried:
                    continue
                tried.add(key)
                if self._solve_jamb_unit(key, members, extra_codes=HALF_BLOCK_FIX_EXTRA_CODES):
                    changed += 1
                    progressed = True
                    break  # indices mudaram: recalcula as unidades
            if not progressed:
                break
        return changed

    def _unit_priority(self, key, members):
        """Menor liberdade geometrica primeiro: pilarete (2+ jambas) antes,
        depois a corrida mais curta (menos alternativas), depois a posicao."""
        spans = [self.fam[f][i1].hi - self.fam[f][i0].lo for f, (i0, i1), _es in members
                 if 0 <= i0 <= i1 < len(self.fam[f])]
        return (-len(key), min(spans) if spans else 0.0, key)

    def _report_unit(self, key, members):
        """Conflitos de uma unidade no estado atual (sem mexer em nada)."""
        edges = sorted(set((e, d) for _f, _sp, es in members for e, d in es))
        broken_paths = [(round(e, 1), d) for e, d in edges if not self._jamb_path(e, d)[0]]
        if broken_paths:
            self.broken_paths.extend({"wall_idx": self.wall_idx, "edge_cm": e, "side": d,
                                      "width_cm": self._jamb_path(e, d)[1]} for e, d in broken_paths)
        for f, (i0, i1), _es in members:
            far = [self._strip_distance(f, i, edges) for i in range(i0, i1 + 1)
                   if self.fam[f][i].compensator and not self._node_closure(f, i)]
            far = [x for x in far if x is not None and x > JAMB_TOUCH_TOLERANCE_CM]
            misplaced = [i for i in range(i0, i1 + 1)
                         if self.fam[f][i].code == "B19" and not self._half_block_admissible(f, i)]
            if far or misplaced or broken_paths:
                self.jamb_conflicts.append({
                    "wall_idx": self.wall_idx, "edges_cm": [round(e, 1) for e, _d in edges],
                    "side": edges[0][1] if len(edges) == 1 else 0, "courses": self._courses_of(f),
                    "distance_cm": round(min(far), 1) if far else None,
                    "codes": [self.fam[f][i].code for i in range(i0, i1 + 1)],
                    "reasons": (["COMPENSATOR_NOT_AT_JAMB"] if far else []) +
                               (["HALF_BLOCK_NOT_ADMISSIBLE"] if misplaced else []) +
                               (["PRISM_REQUIRED_PATH_BROKEN"] if broken_paths else []) +
                               list((getattr(self, "_unit_reasons", {}).get(key) or ([], {}))[0]),
                    "detail": dict((getattr(self, "_unit_reasons", {}).get(key) or ([], {}))[1])})


def _count_required_paths(summary, wall_idx, before, after):
    """SECAO 85: percursos obrigatorios (coluna de vazados junto de cada jamba, na
    altura inteira) antes/depois do passe; os quebrados ficam listados - nunca
    sao aceitos como validados."""
    rp = summary["required_paths"]
    rp["total"] += len(after)
    rp["ok_before"] += sum(1 for item in before if item[2])
    rp["ok_after"] += sum(1 for item in after if item[2])
    for edge, d, ok, width in after:
        if not ok:
            rp["broken"].append({"wall_idx": wall_idx, "edge_cm": round(edge, 1), "side": d,
                                 "common_width_cm": width})


def cleanup_channel_runs(course_candidates, walls_to_create, catalog=None):
    """SECAO 85.8 (correcao do usuario, verga da W2): corrida contigua de canaleta
    U39/U34 com pastilha (C04/C09) numa fiada cujo comprimento + junta e' multiplo
    exato de 40 cm vira so' U39 - `U34 + ... + C04` onde cabem U39 exatas e' erro.
    Canaleta cortada (U_CUT) nunca entra. Reaproveita os candidatos U39 da propria
    corrida (mesma orientacao e papel de verga/contraverga); remove o resto.
    Devolve o resumo {corridas, removidas, criadas}."""
    out = {"runs": 0, "removed": 0, "created": 0, "detail": []}
    if not CHANNEL_RUN_CLEANUP_ENABLED or XYZ is None:
        return out
    rows_by_wall = _collect_rows(course_candidates, walls_to_create)
    for wi in sorted(rows_by_wall):
        p0, wall_dir, _length = _axis(walls_to_create, wi)
        for c in sorted(rows_by_wall[wi]):
            entries = sorted(rows_by_wall[wi][c], key=lambda e: e[1])
            run = []

            def flush(run):
                if len(run) < 2:
                    return
                codes = [e[0].get("logical_code") for e in run]
                if not any(cd == "CHANNEL_U_39" for cd in codes):
                    return
                if not any(cd in ("CHANNEL_U_34", "C04", "C09") for cd in codes):
                    return
                if not any(_is_channel_code(cd) for cd in codes) or any(cd == "CHANNEL_U_CUT" for cd in codes):
                    return
                if sum(1 for cd in codes if cd in ("C04", "C09")) > 2:
                    return
                lo, hi = run[0][1], run[-1][2]
                n = (hi - lo + 1.0) / 40.0
                if abs(n - round(n)) > 0.002 or round(n) < 1:
                    return
                n = int(round(n))
                templates = [e[0] for e in run if e[0].get("logical_code") == "CHANNEL_U_39"]
                keep = templates[:n]
                lst = course_candidates[c]
                for e in run:
                    if any(e[0] is k for k in keep):
                        continue
                    for k2 in range(len(lst)):
                        if lst[k2] is e[0]:
                            del lst[k2]
                            out["removed"] += 1
                            break
                model = templates[0]
                for k in range(n):
                    target_lo = lo + 40.0 * k
                    if k < len(keep):
                        cand = keep[k]
                        cur_lo, _cur_hi = _extent_cm(cand, p0, wall_dir)
                        if abs(cur_lo - target_lo) > 1e-6:
                            _translate(cand, target_lo - cur_lo, wall_dir)
                    else:
                        cand = dict(model)
                        cur_lo, _cur_hi = _extent_cm(model, p0, wall_dir)
                        delta_ft = (target_lo - cur_lo) / CM_PER_FT
                        cand["origin_world"] = model["origin_world"] + XYZ(wall_dir.X * delta_ft,
                                                                           wall_dir.Y * delta_ft, 0.0)
                        cand["cells_world"] = []
                        lst.append(cand)
                        out["created"] += 1
                out["runs"] += 1
                if len(out["detail"]) < 60:
                    out["detail"].append({"wall_idx": wi, "course": c, "t_cm": [round(lo, 1), round(hi, 1)],
                                          "before": codes, "after": ["CHANNEL_U_39"] * n})

            for e in entries:
                code = e[0].get("logical_code")
                ok = _is_channel_code(code) or code in ("C04", "C09")
                if ok and (not run or e[1] - run[-1][2] <= RUN_MAX_GAP_CM):
                    run.append(e)
                    continue
                flush(run)
                run = [e] if ok else []
            flush(run)
    return out


def _side_patterns(order, tpl_of):
    """SECAO 85.9: lados dos B34 de uma composicao - todos para um lado, todos
    para o outro e alternados. A grade de B34 do desenho do usuario tem a fiada
    inteira virada para o mesmo lado; com ate' 2 B34 isso cobre todas as
    combinacoes (antes: so' as 4 primeiras da arvore, que nunca chegavam em
    `todos para o lado -1` com 3 ou mais B34)."""
    idx = [k for k, c in enumerate(order) if tpl_of(c) is not None and tpl_of(c).orientable]
    out = []
    for pat in ((1,), (-1,), (1, -1), (-1, 1)):
        sides = [0] * len(order)
        for j, k in enumerate(idx):
            sides[k] = pat[j % len(pat)]
        t = tuple(sides)
        if t not in out:
            out.append(t)
    return out


def _merged(assign, family, order):
    out = dict(assign)
    out[family] = order
    return out


def jamb_strip_census(course_candidates, walls_to_create, openings_per_wall, catalog=None):
    """SECAO 84 - regua INDEPENDENTE do passe (validacao/relatorio): para cada
    lateral de abertura, a distancia do compensador mais perto da jamba em cada
    fiada em que a abertura corta a fileira. `alternating` = a lateral tem
    compensador em alguma fiada e ele nao fica na mesma posicao em todas;
    `touching_all` = em toda fiada com compensador ele encosta no vao."""
    out = {"sides": 0, "sides_with_compensator": 0, "alternating": 0, "touching_all": 0, "details": []}
    rows_by_wall = _collect_rows(course_candidates, walls_to_create)
    ops = openings_per_wall or []
    for wi in sorted(rows_by_wall):
        openings = []
        for op in (ops[wi] if wi < len(ops) else None) or ():
            lo_cm, hi_cm = float(op[0]) * CM_PER_FT, float(op[1]) * CM_PER_FT
            openings.append((min(lo_cm, hi_cm), max(lo_cm, hi_cm)))
        if not openings:
            continue
        rows = rows_by_wall[wi]
        for lo_cm, hi_cm in sorted(openings):
            for edge, d in ((lo_cm, -1), (hi_cm, 1)):
                per_course = {}
                for c in sorted(rows):
                    entries = rows[c]
                    probe = edge + JAMB_INSIDE_PROBE_CM if d < 0 else edge - JAMB_INSIDE_PROBE_CM
                    if any(elo - 1e-6 <= probe <= ehi + 1e-6 for _cand, elo, ehi, _cc in entries):
                        continue  # a abertura nao corta esta fiada
                    best = None
                    for cand, elo, ehi, _cc in entries:
                        entry = (catalog or {}).get(cand.get("logical_code")) or {}
                        if not entry.get("is_compensator") or cand.get("wall_idx") != wi:
                            continue
                        dist = (elo - edge) if d > 0 else (edge - ehi)
                        if -JAMB_TOUCH_TOLERANCE_CM <= dist < JAMB_REACH_CM and (best is None or dist < best):
                            best = dist
                    per_course[c] = None if best is None else max(0.0, round(best, 1))
                if not per_course:
                    continue
                out["sides"] += 1
                with_comp = [v for v in per_course.values() if v is not None]
                if not with_comp:
                    continue
                out["sides_with_compensator"] += 1
                touching = [v <= JAMB_TOUCH_TOLERANCE_CM for v in with_comp]
                positions = set(0.0 if v <= JAMB_TOUCH_TOLERANCE_CM else v for v in with_comp)
                alternating = len(positions) > 1
                if alternating:
                    out["alternating"] += 1
                if all(touching):
                    out["touching_all"] += 1
                out["details"].append({"wall_idx": wi, "edge_cm": round(edge, 1), "side": d,
                                       "distance_by_course": dict((str(c), v) for c, v in sorted(per_course.items())),
                                       "alternating": alternating, "touching_all": all(touching)})
    return out


def half_block_census(course_candidates, walls_to_create, openings_per_wall, catalog=None,
                      tie_positions_by_wall=None, limit=200):
    """SECAO 85 - regua INDEPENDENTE (validacao/relatorio): cada B19 da planta e'
    fechamento admissivel (jamba ativa da fiada, ponta livre da parede, ou logo
    atras da faixa de compensadores encostada no vao) ou esta' fora de lugar
    (miolo, ou so' encostado em peca de no'). O pedido do usuario proibe B19 no
    miolo sem excecao automatica: o que sobrar aqui e' incompatibilidade a
    registrar, nunca aceito em silencio."""
    out = {"total": 0, "admissible": 0, "misplaced": 0, "misplaced_by_wall": {}, "list": []}
    rows_by_wall = _collect_rows(course_candidates, walls_to_create)
    for wi in sorted(rows_by_wall):
        try:
            wall = _Wall(wi, rows_by_wall[wi], walls_to_create, openings_per_wall, catalog or {}, 1.5,
                         ties=(tie_positions_by_wall or {}).get(wi))
        except Exception:
            continue
        for f in sorted(wall.fam):
            courses = wall._courses_of(f)
            edges = wall._active_jamb_edges(f)
            slots = wall.fam[f]
            for i, sl in enumerate(slots):
                if sl.code != "B19":
                    continue
                out["total"] += len(courses)
                if wall._half_block_admissible(f, i, edges):
                    out["admissible"] += len(courses)
                    continue
                out["misplaced"] += len(courses)
                out["misplaced_by_wall"][wi] = out["misplaced_by_wall"].get(wi, 0) + len(courses)
                if len(out["list"]) < limit:
                    out["list"].append({
                        "wall_idx": wi, "courses": courses, "t_cm": [round(sl.lo, 1), round(sl.hi, 1)],
                        "neighbours": [slots[k].code + ("(no)" if slots[k].node else "")
                                       for k in (i - 1, i + 1) if 0 <= k < len(slots)]})
    return out


def _collect_rows(course_candidates, walls_to_create):
    """{wall_idx: {course: [(cand, lo, hi, courses)]}} ordenado por lo."""
    occ = {}
    for c in sorted(course_candidates or {}):
        for cand in course_candidates[c] or ():
            if cand.get("wall_idx") is None:
                continue
            occ.setdefault(id(cand), [cand, set()])[1].add(c)
    axes = {}
    walls = collections.defaultdict(lambda: collections.defaultdict(list))
    for cand, courses in occ.values():
        wi = cand["wall_idx"]
        if wi >= len(walls_to_create or ()):
            continue
        if wi not in axes:
            p0, wall_dir, _length = _axis(walls_to_create, wi)
            axes[wi] = (p0, wall_dir)
        p0, wall_dir = axes[wi]
        lo, hi = _extent_cm(cand, p0, wall_dir)
        frozen = frozenset(courses)
        for c in courses:
            walls[wi][c].append((cand, lo, hi, frozen))
    for wi in walls:
        for c in walls[wi]:
            walls[wi][c].sort(key=lambda e: (e[1], e[2], e[0].get("logical_code") or ""))
    return walls


def _translate(cand, delta_cm, wall_dir):
    d_ft = delta_cm / CM_PER_FT
    dx, dy = wall_dir.X * d_ft, wall_dir.Y * d_ft
    o = cand["origin_world"]
    cand["origin_world"] = XYZ(o.X + dx, o.Y + dy, o.Z)
    cells = []
    for cell in cand.get("cells_world") or []:
        p = cell["point"]
        cells.append({"point": XYZ(p.X + dx, p.Y + dy, p.Z), "size_local": cell["size_local"]})
    cand["cells_world"] = cells


def _runs_by_start(slots):
    """Corridas MOVEIS pela ponta inicial - inclusive a de UMA peca so' (o
    recompositor da secao 85 recompoe corrida de 1 peca e troca 2 pecas por 1;
    sem isso a mudanca ficava so' no modelo e nao chegava aos candidatos)."""
    out, cur = {}, []
    for i, s in enumerate(slots):
        if s.movable and (not cur or s.lo - slots[cur[-1]].hi <= RUN_MAX_GAP_CM):
            cur.append(i)
            continue
        if cur:
            out[round(slots[cur[0]].lo, 3)] = cur
        cur = [i] if s.movable else []
    if cur:
        out[round(slots[cur[0]].lo, 3)] = cur
    return out


def _write_back(wall, base_fam, course_candidates, catalog):
    """Leva o estado final do modelo para os candidatos reais, trecho a trecho
    (identificado pela ponta inicial, que nunca muda): reaproveita o objeto
    quando o codigo coincide (so' move/gira), cria peca nova com o construtor do
    solver quando falta e remove a que sobra."""
    from core.engine.wall_stepper import _place_pier_layout
    moved = rotated = created = removed = 0
    done = set()
    verga = _merge_spans(getattr(wall, "verga_changes", ()))
    for f in sorted(verga):
        c2, r2 = _write_back_verga(wall, f, verga[f], course_candidates, catalog, done)
        created += c2
        removed += r2
    for f in sorted(wall.fam):
        old, new = base_fam[f], wall.fam[f]
        old_runs, new_runs = _runs_by_start(old), _runs_by_start(new)
        for start in sorted(old_runs):
            orun, nrun = old_runs[start], new_runs.get(start)
            if nrun is None:
                continue
            if any(old[orun[0]].lo < hi + FACE_TOLERANCE_CM and old[orun[-1]].hi > lo - FACE_TOLERANCE_CM
                   for lo, hi in verga.get(f, ())):
                continue  # trecho da verga ja' refeito acima
            if [(old[i].code, round(old[i].lo, 3), old[i].side) for i in orun] == \
                    [(new[i].code, round(new[i].lo, 3), new[i].side) for i in nrun]:
                continue
            for c in sorted(wall.course_fam):
                if wall.course_fam[c] != f:
                    continue
                originals = [wall.rows[c][i][0] for i in orun]
                model = originals[0]
                pools = collections.defaultdict(list)
                for cand in originals:
                    pools[cand.get("logical_code")].append(cand)
                for i in nrun:
                    slot = new[i]
                    if pools[slot.code]:
                        cand = pools[slot.code].pop(0)
                        if id(cand) not in done:
                            done.add(id(cand))
                            lo, _hi = _extent_cm(cand, wall.p0, wall.dir)
                            if abs(slot.lo - lo) > 1e-6:
                                _translate(cand, slot.lo - lo, wall.dir)
                                moved += 1
                    else:
                        cand = _place_pier_layout([(slot.code, slot.lo, slot.hi)], catalog, wall.p0, wall.dir,
                                                  model.get("course"), wall.wall_idx)[0]
                        for key in ("course_variant",):
                            if key in model:
                                cand[key] = model[key]
                        course_candidates[c].append(cand)
                        done.add(id(cand))
                        created += 1
                    if slot.orientable and id(cand) in done:
                        lo, hi = _extent_cm(cand, wall.p0, wall.dir)
                        off, _half = _void_geometry(cand, wall.p0, wall.dir, lo, hi)
                        if (1 if (off or 0.0) >= 0.0 else -1) != slot.side:
                            _sva.rotate_candidate_180(cand)
                            rotated += 1
                for leftovers in pools.values():
                    for cand in leftovers:
                        done.add(id(cand))
                        lst = course_candidates[c]
                        for k in range(len(lst)):
                            if lst[k] is cand:
                                del lst[k]
                                removed += 1
                                break
    rotated += _sync_orientation(wall, base_fam, done)
    return moved, rotated, created, removed


def _merge_spans(changes):
    """{familia: [(lo, hi)]} unindo os trechos de verga que se sobrepoem."""
    out = {}
    for f, lo, hi in changes or ():
        out.setdefault(f, []).append((lo, hi))
    for f in out:
        merged = []
        for lo, hi in sorted(out[f]):
            if merged and lo <= merged[-1][1] + FACE_TOLERANCE_CM:
                merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
            else:
                merged.append((lo, hi))
        out[f] = merged
    return out


def _write_back_verga(wall, f, spans, course_candidates, catalog, done):
    """SECAO 85.9: refaz o trecho da fiada da verga/contraverga que passou a
    seguir a grade da jamba. Canaleta nova = copia de uma canaleta da propria
    corrida (mesmo papel de verga/contraverga, run_id e aberturas), so' com o
    codigo, o comprimento e a posicao trocados - o mesmo construtor da conversao
    bloco -> canaleta (`opening_reinforcement._channel_candidate_from_group`).
    Bloco novo = construtor do solver. Devolve (criadas, removidas)."""
    from core.engine.wall_stepper import _place_pier_layout
    created = removed = 0
    block_of = dict((v, k) for k, v in CHANNEL_OF_BLOCK.items())
    for c in sorted(wall.course_fam):
        if wall.course_fam[c] != f:
            continue
        lst = course_candidates[c]
        for lo, hi in spans:
            olds = [e for e in wall.rows[c] if e[1] >= lo - FACE_TOLERANCE_CM and e[2] <= hi + FACE_TOLERANCE_CM]
            channel_models = [e[0] for e in olds if _is_channel_code(e[0].get("logical_code"))]
            block_models = [e[0] for e in olds if not _is_channel_code(e[0].get("logical_code"))]
            if not olds:
                continue
            model = (block_models or channel_models)[0]
            for e in olds:
                cand = e[0]
                done.add(id(cand))
                for k in range(len(lst)):
                    if lst[k] is cand:
                        del lst[k]
                        removed += 1
                        break
            for slot in wall.fam[f]:
                if slot.lo < lo - FACE_TOLERANCE_CM or slot.hi > hi + FACE_TOLERANCE_CM:
                    continue
                if _is_channel_code(slot.code):
                    src = next((m for m in channel_models if m.get("logical_code") == slot.code),
                               channel_models[0] if channel_models else None)
                    if src is None:
                        continue
                    cand = dict(src)
                    cur_lo, cur_hi = _extent_cm(src, wall.p0, wall.dir)
                    length = float(((catalog or {}).get(slot.code) or {}).get("length_cm") or (slot.hi - slot.lo))
                    delta_ft = ((slot.lo + slot.hi) / 2.0 - (cur_lo + cur_hi) / 2.0) / CM_PER_FT
                    o = src["origin_world"]
                    cand["origin_world"] = XYZ(o.X + wall.dir.X * delta_ft, o.Y + wall.dir.Y * delta_ft, o.Z)
                    cand["logical_code"] = slot.code
                    cand["length_cm"] = length
                    cand["instance_length_cm"] = None
                    cand["cells_world"] = []
                    cand["mirrored"] = False
                    rein = dict(src.get("reinforcement") or {})
                    if rein:
                        rein["source_codes"] = [block_of.get(slot.code, slot.code)]
                        rein["cut"] = None
                        cand["reinforcement"] = rein
                    for key in ("symbol", "family_symbol"):
                        entry = (catalog or {}).get(slot.code) or {}
                        if key in cand and entry.get(key) is not None:
                            cand[key] = entry.get(key)
                else:
                    cand = _place_pier_layout([(slot.code, slot.lo, slot.hi)], catalog, wall.p0, wall.dir,
                                              model.get("course"), wall.wall_idx)[0]
                    for key in ("course_variant",):
                        if key in model:
                            cand[key] = model[key]
                    if slot.orientable:
                        clo, chi = _extent_cm(cand, wall.p0, wall.dir)
                        off, _half = _void_geometry(cand, wall.p0, wall.dir, clo, chi)
                        if (1 if (off or 0.0) >= 0.0 else -1) != slot.side:
                            _sva.rotate_candidate_180(cand)
                lst.append(cand)
                done.add(id(cand))
                created += 1
    return created, removed


def _sync_orientation(wall, base_fam, done):
    """Gira os candidatos cujo slot manteve codigo e posicao mas mudou de lado
    (orientacao exata, secao 62) - inclusive B34 isolado, que nao forma corrida.
    Casamento por (codigo, posicao): as listas podem ter mudado de tamanho."""
    rotated = 0
    for f in sorted(wall.fam):
        old_index = dict(((s.code, round(s.lo, 3)), i) for i, s in enumerate(base_fam[f]))
        for slot in wall.fam[f]:
            if not slot.orientable:
                continue
            i = old_index.get((slot.code, round(slot.lo, 3)))
            if i is None or base_fam[f][i].side == slot.side:
                continue
            for c in sorted(wall.course_fam):
                if wall.course_fam[c] != f or i >= len(wall.rows[c]):
                    continue
                cand = wall.rows[c][i][0]
                if id(cand) in done:
                    continue
                done.add(id(cand))
                lo, hi = _extent_cm(cand, wall.p0, wall.dir)
                off, _half = _void_geometry(cand, wall.p0, wall.dir, lo, hi)
                if (1 if (off or 0.0) >= 0.0 else -1) != slot.side:
                    _sva.rotate_candidate_180(cand)
                    rotated += 1
    return rotated


def _snapshot_wall(course_candidates, wall_idx):
    lists = []
    geometry = {}
    for c in sorted(course_candidates or {}):
        lst = course_candidates[c]
        if any(cand.get("wall_idx") == wall_idx for cand in lst):
            lists.append((c, list(lst)))
            for cand in lst:
                if cand.get("wall_idx") == wall_idx and id(cand) not in geometry:
                    geometry[id(cand)] = (cand, cand["origin_world"], list(cand.get("cells_world") or []),
                                          cand.get("x_dir"), cand.get("y_dir"), cand.get("rotation_deg"))
    return lists, geometry


def _restore_wall(course_candidates, snapshot):
    lists, geometry = snapshot
    for c, saved in lists:
        course_candidates[c][:] = saved
    for cand, origin, cells, x_dir, y_dir, rotation in geometry.values():
        cand["origin_world"], cand["cells_world"] = origin, cells
        cand["x_dir"], cand["y_dir"], cand["rotation_deg"] = x_dir, y_dir, rotation


def _validation_worse(after, before):
    """Qualquer tipo de problema da auditoria que aumenta, apoio pior, qualquer
    problema CHANNEL que aumenta ou canaleta casada que some."""
    if after is None or before is None:
        return False
    for kind, count in (after.get("audit") or {}).items():
        if count > (before.get("audit") or {}).get(kind, 0):
            return True
    if (after.get("unsupported") or 0) > (before.get("unsupported") or 0):
        return True
    channel_after, channel_before = after.get("channel"), before.get("channel")
    if channel_after is not None and channel_before is not None:
        for kind, count in sorted(channel_after.items()):
            if kind == "matched":
                if any(a < b for a, b in zip(count, channel_before.get("matched") or (0, 0))):
                    return True
            elif count > channel_before.get(kind, 0):
                return True
    return False


def _fill_codes(course_candidates, catalog):
    """Codigos que o solver ja' usa como preenchimento comum (bloco vazado ou
    compensador) em alguma parede - a composicao nunca inventa familia nova.
    Com B34_RUN_OPENING_REPAIR_MOVABLE, as pecas do reparo de abertura contam
    (sao as mesmas pecas moveis das corridas)."""
    reasons = _MOVABLE_REASONS if B34_RUN_OPENING_REPAIR_MOVABLE else ("STANDARD_FILL",)
    codes = set()
    for c in course_candidates or {}:
        for cand in course_candidates[c] or ():
            code = cand.get("logical_code")
            cat = (catalog or {}).get(code) or {}
            if cand.get("placement_reason") not in reasons or cand.get("node_index") is not None:
                continue
            if cat.get("is_channel") or _is_channel_code(code):
                continue
            if _sva._is_hollow_masonry(cand, catalog) or cat.get("is_compensator"):
                codes.add(code)
    return sorted(codes)


def arrange_b34_runs(course_candidates, walls_to_create, openings_per_wall, catalog=None,
                     tolerance_cm=_sva.SMALL_VOID_ALIGN_TOLERANCE_CM, tie_positions_by_wall=None,
                     half_block_code=None, half_block_tie_gap_cm=0.0, validate_wall=None,
                     only_walls=None, joint_identity_guard=False, jamb_compensator_alignment=False):
    """Aplica o arranjo conjunto. Devolve o resumo por parede alterada e os
    totais das guardas antes/depois (as guardas nunca pioram por construcao).
    `joint_identity_guard` (secao 81.1): nenhuma troca cria junta coincidente
    entre fiadas vizinhas numa posicao nova. `jamb_compensator_alignment`
    (secao 84): faixa de compensacao encostada e alinhada na jamba."""
    summary = {"walls_changed": 0, "runs_changed": 0, "moved": 0, "rotated": 0,
               "before": {"violations": 0, "coincident_faces": 0, "compensator_guard": 0,
                          "long_compensator_extremes": 0, "half_block_near_tie": 0, "stacked_joints": 0},
               "after": {"violations": 0, "coincident_faces": 0, "compensator_guard": 0,
                         "long_compensator_extremes": 0, "half_block_near_tie": 0, "stacked_joints": 0},
               "walls": []}
    jamb_on = bool(jamb_compensator_alignment) and JAMB_COMPENSATOR_ALIGNMENT_ENABLED
    if jamb_on:
        summary["before"]["jamb_compensator_distance"] = 0
        summary["after"]["jamb_compensator_distance"] = 0
        summary.update({"jamb_sides_changed": 0, "jamb_conflicts_by_wall": {},
                        "required_paths": {"total": 0, "ok_before": 0, "ok_after": 0, "broken": []}})
    if not B34_RUN_ARRANGEMENT_ENABLED or not course_candidates or XYZ is None:
        return summary
    rows_by_wall = _collect_rows(course_candidates, walls_to_create)
    fill_codes = _fill_codes(course_candidates, catalog)
    summary.update({"compositions": 0, "created": 0, "removed": 0, "walls_rejected_by_validation": []})
    support_total = None
    for wi in sorted(rows_by_wall):
        if only_walls is not None and wi not in only_walls:
            # passe seguinte (secao 65): so' as paredes que o passe anterior mexeu
            continue
        wall = _Wall(wi, rows_by_wall[wi], walls_to_create, openings_per_wall, catalog, tolerance_cm,
                     ties=(tie_positions_by_wall or {}).get(wi), half_code=half_block_code,
                     half_tie_gap_cm=half_block_tie_gap_cm, fill_codes=fill_codes,
                     joint_identity_guard=joint_identity_guard, jamb_alignment=jamb_on)
        before = wall.totals()
        base_fam = dict((f, [s.copy() for s in slots]) for f, slots in wall.fam.items())
        aligned = 0
        if jamb_on:
            # SECAO 84 = passe FINAL so' de permutacao, por cima do arranjo ja'
            # convergido (ordem 60, composicao 61, orientacao 62): a contagem de
            # pecas e' a da busca, toda composicao que TIRA compensador ja'
            # aconteceu (regra 5 do pedido) e nada depois desfaz a faixa
            changed, compositions, oriented = set(), 0, 0
            paths_before = wall.required_paths()
            aligned = wall.align_jamb_compensators()
            paths_after = wall.required_paths()
        else:
            changed = wall.optimize() if before["violations"] else set()
            compositions = wall.compose()
            oriented = wall.orient_exact() if wall.totals()["violations"] else 0
        if oriented:
            summary["orientation_dp_changes"] = summary.get("orientation_dp_changes", 0) + oriented
        if jamb_on:
            summary["jamb_conflicts_by_wall"][wi] = list(wall.jamb_conflicts)
        if not changed and not compositions and not oriented and not aligned:
            for key in summary["before"]:
                summary["before"][key] += before[key]
                summary["after"][key] += before[key]
            if jamb_on:
                _count_required_paths(summary, wi, paths_before, paths_after)
            continue
        after = wall.totals()
        snapshot = _snapshot_wall(course_candidates, wi)
        checked_before = None
        if validate_wall is not None:
            # o apoio fisico e' global: o "antes" desta parede e' o "depois" da
            # anterior (so' recalcula a auditoria, que e' por parede)
            checked_before = validate_wall(wi, support=support_total is None)
            if support_total is not None:
                checked_before["unsupported"], checked_before["channel"] = support_total
        moved, rotated, created, removed = _write_back(wall, base_fam, course_candidates, catalog)
        checked_after = validate_wall(wi) if validate_wall is not None else None
        if checked_after is not None:
            if checked_after.get("channel") is None and checked_before is not None:
                # parede sem abertura: a validacao CHANNEL nao muda
                checked_after["channel"] = checked_before.get("channel")
            support_total = (checked_after["unsupported"], checked_after.get("channel"))
        if _validation_worse(checked_after, checked_before):
            # a busca e' um modelo; quem decide e' o validador de producao
            _restore_wall(course_candidates, snapshot)
            support_total = (checked_before["unsupported"], checked_before.get("channel"))
            summary["walls_rejected_by_validation"].append(
                {"wall_idx": wi, "before": checked_before, "after": checked_after})
            after = before
            moved = rotated = created = removed = 0
            compositions = oriented = 0
            changed = set()
            if jamb_on:
                paths_after = paths_before
            if jamb_on and aligned:
                # a faixa desta parede nao passou no validador de producao
                summary["jamb_conflicts_by_wall"][wi] = [{
                    "wall_idx": wi, "edges_cm": [], "side": 0, "courses": [], "distance_cm": None,
                    "codes": [], "reasons": ["PRODUCTION_VALIDATION_REJECTED"]}]
            aligned = 0
        for key in summary["before"]:
            summary["before"][key] += before[key]
            summary["after"][key] += after[key]
        if jamb_on:
            _count_required_paths(summary, wi, paths_before, paths_after)
        if not changed and not compositions and not oriented and not aligned:
            continue
        if jamb_on:
            summary["jamb_sides_changed"] += aligned
        summary["walls_changed"] += 1
        summary["runs_changed"] += len(changed)
        summary["compositions"] += compositions
        summary["moved"] += moved
        summary["rotated"] += rotated
        summary["created"] += created
        summary["removed"] += removed
        summary["walls"].append({"wall_idx": wi, "before": before, "after": after})
    return summary
