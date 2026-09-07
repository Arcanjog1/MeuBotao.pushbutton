# -*- coding: utf-8 -*-
"""CR-BENCH-OPENING-RECONSTRUCTION-A - o detector de aberturas separa
IDENTIDADE de GEOMETRIA.

`detect_wall_openings_from_courses` agregava o vao como ENVELOPE (uniao
`min`/`max`) dos vazios de cada fiada, aceitando desencontro de borda de
ate' `OPENING_RUN_EDGE_MATCH_TOLERANCE_CM = 15,0cm`. A tolerancia existe
pra' decidir IDENTIDADE ("o vazio desta fiada e' a MESMA abertura?") e
acabava decidindo GEOMETRIA ("onde fica a jamba?").

Onde a jamba coincide com um no' T/L as fiadas alternam entre "reserva de
no' vazia" e "peca de amarracao atravessa o no'" - diferenca de exatamente
`B34 - B19 = 34 - 19 = 15,0cm`. O envelope gravava a borda mais larga, e as
pecas das fiadas alternadas passavam a "invadir" o vao em exatamente 15,0cm
(assinatura medida: 19 aberturas por projeto no corpus, 195 achados
`OPENING_BLOCK_CROSSES_JAMB` espurios).

Esta suite exercita a FUNCAO DE PRODUCAO, importada pelo mesmo caminho do
motor (`wall_modeling` faz `from core.engine.opening_audit import *`),
nunca um helper inventado so' para o teste.

    python3 -m pytest tests/test_opening_reconstruction_cr_a.py -q
"""

import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import load_script  # noqa: E402

m = load_script.load()

detect = m.detect_wall_openings_from_courses
TOL = m.OPENING_RUN_EDGE_MATCH_TOLERANCE_CM
GAP_MIN = m.OPENING_GAP_MIN_CM
GAP_MAX = m.OPENING_GAP_MAX_CM
MIN_COURSES = m.OPENING_MIN_CONSEC_COURSES
# `getattr` com padrao, e NAO acesso direto, de proposito: assim esta suite
# ainda COLETA contra o motor sem a correcao (STATE_A) e as falhas que
# aparecem la' sao de COMPORTAMENTO - geometria gravada - em vez de um erro
# de importacao que nao prova nada. A existencia do vocabulario tem teste
# proprio (`test_vocabulario_de_proveniencia_exportado`).
PROV_CONSENSUS = getattr(m, "OPENING_PROVENANCE_CONSENSUS", "RECONSTRUCTED_CONSENSUS")
PROV_INCONCLUSIVE = getattr(m, "OPENING_PROVENANCE_INCONCLUSIVE", "INCONCLUSIVE")
PROV_MEASURED = getattr(m, "OPENING_PROVENANCE_MEASURED", "MEASURED")
PROV_ENVELOPE = getattr(m, "OPENING_PROVENANCE_ENVELOPE", "RECONSTRUCTED_ENVELOPE")

PROJECTS_DIR = os.path.join(_ROOT, "nuvem", "benchmark", "projects")
CORPUS = ["torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"]


# --------------------------------------------------------------------------
# helpers de geometria - so' montam `courses` no formato de producao
# --------------------------------------------------------------------------

def row(*intervals):
    """Uma fiada: pares (inicio_cm, fim_cm) viram tuplas com nome de familia."""
    return [(float(s), float(e), fam) for s, e, fam in intervals]


def solid(t_lo, t_hi, fam="BLOCO INTEIRO"):
    return (t_lo, t_hi, fam)


def courses_from_rows(rows, step=20.0):
    return [(i * step, r) for i, r in enumerate(rows)]


def wall_with_void(t_lo, t_hi, wall_end=1000.0, fam="BLOCO INTEIRO"):
    """Uma fiada cheia de `0` a `wall_end`, menos o vazio `[t_lo, t_hi]`."""
    return [solid(0.0, t_lo, fam), solid(t_hi, wall_end, fam)]


# --------------------------------------------------------------------------
# 1. abertura real com jamba EXATA - o caso que nao pode mudar
# --------------------------------------------------------------------------

def test_abertura_real_com_jamba_exata_permanece_identica():
    """Todas as fiadas concordam: envelope == consenso, desacordo ZERO.

    E' o caso majoritario do corpus (63/94 no TGD) e e' a rede de seguranca
    contra "estreitar todos os vaos": sem desacordo entre fiadas, a
    geometria gravada tem de ser exatamente a medida."""
    rows = [wall_with_void(300.0, 391.0) for _ in range(6)]
    openings = detect(courses_from_rows(rows))

    assert len(openings) == 1, openings
    op = openings[0]
    assert op["x_range"] == (300.0, 391.0), op
    assert op["width_cm"] == 91.0, op
    assert op["x_range_envelope"] == (300.0, 391.0), op
    assert op["jamb_spread_start_cm"] == 0.0
    assert op["jamb_spread_end_cm"] == 0.0
    assert op["jamb_spread_cm"] == 0.0
    assert op["opening_provenance"] == PROV_CONSENSUS


# --------------------------------------------------------------------------
# 2. o reproducer minimo - no' T/L na jamba, fiadas alternadas
# --------------------------------------------------------------------------

def _courses_no_TL_na_jamba(n_courses=8):
    """Reproduz `W003` do TGD, medido no gabarito humano:

        fiada par   ... C09 570-579   <- reserva de no' VAZIA nesta fiada
        fiada impar ... B34 560-594   <- peca de amarracao ATRAVESSA o no'
                            ^^^ 594 - 579 = 15,0cm = B34 - B19

    Vazio fisico real (o que TODA fiada respeita): [594, 750] = 156cm.
    Envelope (o que o STATE_A gravava): [579, 765] = 186cm.
    """
    par = [solid(0.0, 570.0), solid(570.0, 579.0, "C09"),
           solid(765.0, 774.0, "C09"), solid(774.0, 1400.0)]
    impar = [solid(0.0, 560.0), solid(560.0, 594.0, "BLOCO 34 - 14x19x34"),
             solid(750.0, 784.0, "BLOCO 34 - 14x19x34"), solid(784.0, 1400.0)]
    return courses_from_rows([par if i % 2 == 0 else impar
                              for i in range(n_courses)])


def test_no_TL_na_jamba_grava_o_vao_fisico_e_nao_o_envelope():
    """FALHA no STATE_A (gravava 186,0cm), PASSA no STATE_B (156,0cm)."""
    openings = detect(_courses_no_TL_na_jamba())

    assert len(openings) == 1, openings
    op = openings[0]
    assert op["x_range"] == (594.0, 750.0), op
    assert op["width_cm"] == 156.0, op
    # o envelope continua LEGIVEL, so' nao e' mais a geometria gravada
    assert op["x_range_envelope"] == (579.0, 765.0), op
    # ... e o desacordo de 15,0cm vira DADO, nao arredondamento silencioso
    assert op["jamb_spread_start_cm"] == 15.0, op
    assert op["jamb_spread_end_cm"] == 15.0, op
    assert op["jamb_spread_cm"] == 15.0, op
    assert op["opening_provenance"] == PROV_CONSENSUS


def test_no_TL_na_jamba_nenhuma_peca_medida_invade_o_vao_gravado():
    """AUSENCIA DE INVASAO FISICA - o criterio que impede "esconder bloco
    invasor estreitando o vao": o vao gravado nao pode conter NENHUM ponto
    onde ALGUMA fiada tem peca. E' o mesmo teste que o validador
    `OPENING_BLOCK_CROSSES_JAMB` faz sobre o resultado."""
    courses = _courses_no_TL_na_jamba()
    op = detect(courses)[0]
    lo, hi = op["x_range"]
    for z_cm, intervals in courses:
        for t_lo, t_hi, fam in intervals:
            assert t_hi <= lo or t_lo >= hi, (
                "peca %s [%s,%s] da fiada z=%s invade o vao gravado [%s,%s]"
                % (fam, t_lo, t_hi, z_cm, lo, hi))


def test_no_TL_na_jamba_a_borda_gravada_e_uma_borda_OBSERVADA():
    """A reducao de largura nao pode ser um numero inventado: cada jamba
    gravada tem de ser exatamente uma borda de vazio MEDIDA em alguma
    fiada. Sem isso, "reduzir CROSS_JAMB" viraria so' redefinir o vao."""
    courses = _courses_no_TL_na_jamba()
    op = detect(courses)[0]
    bordas_inicio, bordas_fim = set(), set()
    for _z, intervals in courses:
        ordered = sorted(intervals)
        for a, b in zip(ordered, ordered[1:]):
            if GAP_MIN <= b[0] - a[1] <= GAP_MAX:
                bordas_inicio.add(a[1])
                bordas_fim.add(b[0])
    assert op["x_range"][0] in bordas_inicio, (op["x_range"], bordas_inicio)
    assert op["x_range"][1] in bordas_fim, (op["x_range"], bordas_fim)


# --------------------------------------------------------------------------
# 3. a tolerancia de identidade NAO entra na geometria gravada
# --------------------------------------------------------------------------

@pytest.mark.parametrize("desencontro", [0.0, 0.01, 0.12, 1.0, 5.0, 7.5,
                                         10.0, 14.0, 14.89, 14.9, 14.99])
def test_tolerancia_de_identidade_nao_desloca_a_borda_gravada(desencontro):
    """Fiadas pares tem o vazio ESTREITO fixo em [300, 391]; as impares tem
    a borda de inicio recuada de `desencontro` (0 a 14,99cm, sempre dentro
    da tolerancia de identidade). O trecho tem de continuar sendo UMA
    abertura (identidade preservada) e a borda gravada tem de ficar
    CONSTANTE em 300,0 - se ela seguisse a tolerancia, andaria junto."""
    estreito = wall_with_void(300.0, 391.0)
    largo = wall_with_void(300.0 - desencontro, 391.0)
    openings = detect(courses_from_rows(
        [estreito, largo, estreito, largo, estreito, largo]))

    assert len(openings) == 1, (desencontro, openings)
    op = openings[0]
    assert op["x_range"] == (300.0, 391.0), (desencontro, op)
    assert op["width_cm"] == 91.0, (desencontro, op)
    # identidade continua sendo decidida pela tolerancia - o trecho nao
    # se partiu em dois, e o envelope registra o desencontro
    assert op["n_courses"] == 6, (desencontro, op)
    assert op["x_range_envelope"] == (300.0 - desencontro, 391.0), (desencontro, op)
    assert op["jamb_spread_start_cm"] == pytest.approx(desencontro), (desencontro, op)


def test_desencontro_acima_da_tolerancia_nao_forma_um_unico_trecho():
    """Contraprova da identidade: acima de `OPENING_RUN_EDGE_MATCH_
    TOLERANCE_CM` os vazios deixam de ser a mesma abertura. O papel da
    tolerancia continua vivo - so' nao mexe mais na geometria."""
    estreito = wall_with_void(300.0, 391.0)
    largo = wall_with_void(300.0 - (TOL + 0.1), 391.0)
    openings = detect(courses_from_rows(
        [estreito, largo, estreito, largo, estreito, largo]))
    assert all(op["n_courses"] < 6 for op in openings), openings


# --------------------------------------------------------------------------
# 4. desacordo registrado, nunca apagado
# --------------------------------------------------------------------------

def test_desacordo_entre_fiadas_e_gravado_nas_duas_bordas():
    rows = [wall_with_void(300.0, 391.0), wall_with_void(295.0, 397.0),
            wall_with_void(300.0, 391.0), wall_with_void(295.0, 397.0)]
    op = detect(courses_from_rows(rows))[0]
    assert op["x_range"] == (300.0, 391.0), op
    assert op["x_range_envelope"] == (295.0, 397.0), op
    assert op["jamb_spread_start_cm"] == 5.0, op
    assert op["jamb_spread_end_cm"] == 6.0, op
    assert op["jamb_spread_cm"] == 6.0, op


def test_sem_consenso_valido_marca_INCONCLUSIVE_sem_voltar_ao_envelope():
    """Ramo defensivo: quando o desacordo come quase o vao inteiro, o
    consenso cai abaixo de `OPENING_GAP_MIN_CM` e nao ha' consenso valido
    pra' gravar. A funcao NAO volta ao envelope (era exatamente o defeito)
    e NAO apaga a abertura - marca `INCONCLUSIVE` e deixa a decisao pra'
    quem consome. ZERO ocorrencias no corpus atual (TGD e TP1)."""
    rows = [wall_with_void(300.0, 350.0), wall_with_void(315.0, 365.0),
            wall_with_void(300.0, 350.0), wall_with_void(315.0, 365.0)]
    op = detect(courses_from_rows(rows))[0]
    assert op["opening_provenance"] == PROV_INCONCLUSIVE, op
    assert op["x_range"] == (315.0, 350.0), op
    assert op["x_range_envelope"] == (300.0, 365.0), op
    assert op["width_cm"] == 35.0, op
    assert op["width_cm"] < GAP_MIN, op


def test_consenso_tem_piso_matematico_de_GAP_MIN_menos_duas_tolerancias():
    """Propriedade do agrupamento, nao numero magico: toda borda observada
    fica a no maximo `TOL` do envelope corrente e todo vazio de fiada tem
    ao menos `GAP_MIN` de largura, logo

        consenso >= GAP_MIN - 2 * TOL

    Com as constantes de hoje (50,0 e 15,0) isso da' 20,0cm: o consenso
    NUNCA inverte no dominio atual, e por isso o corpus nao tem nenhum
    `INCONCLUSIVE`. O grampo abaixo existe para o dia em que uma dessas
    duas constantes mudar."""
    assert GAP_MIN - 2 * TOL > 0.0


def test_consenso_invertido_nunca_gera_largura_negativa():
    """Exercita o grampo do ramo `INCONCLUSIVE` num dominio onde a
    inversao E' alcancavel (`GAP_MIN` rebaixado), sem tocar no valor de
    producao fora do teste."""
    audit = sys.modules[detect.__module__]
    original = audit.OPENING_GAP_MIN_CM
    audit.OPENING_GAP_MIN_CM = 5.0
    try:
        rows = [wall_with_void(300.0, 310.0), wall_with_void(314.0, 324.0),
                wall_with_void(300.0, 310.0), wall_with_void(314.0, 324.0)]
        op = detect(courses_from_rows(rows))[0]
    finally:
        audit.OPENING_GAP_MIN_CM = original
    assert op["opening_provenance"] == PROV_INCONCLUSIVE, op
    assert op["x_range"] == (314.0, 314.0), op
    assert op["width_cm"] == 0.0, op
    assert op["x_range"][0] <= op["x_range"][1], op


# --------------------------------------------------------------------------
# 5. espaco entre paredes separadas x abertura dentro de UMA parede
# --------------------------------------------------------------------------

def test_vao_gravado_nunca_ultrapassa_OPENING_GAP_MAX_CM():
    """No STATE_A o envelope podia gravar um vao MAIOR que o proprio teto
    de dominio do modulo (`W052` do TGD: envelope 266,0cm contra
    `OPENING_GAP_MAX_CM = 260,0`) - isto e', a tolerancia produzia uma
    abertura que o proprio detector teria recusado como "outra parede".
    O consenso nunca passa do teto."""
    par = wall_with_void(100.0, 358.0)      # vazio de 258,0cm - dentro do teto
    impar = wall_with_void(92.0, 350.0)     # vazio de 258,0cm - dentro do teto
    op = detect(courses_from_rows([par, impar, par, impar]))[0]
    assert op["x_range_envelope"][1] - op["x_range_envelope"][0] > GAP_MAX
    assert op["width_cm"] <= GAP_MAX, op
    assert op["opening_provenance"] == PROV_CONSENSUS, op


def test_espaco_grande_demais_continua_nao_sendo_abertura():
    """Regra de dominio preservada (secao 10): um espaco acima do teto e'
    OUTRA parede, nao um vao - o detector nao pode passar a inventar
    abertura em cima disso. CR-A nao transforma dois trechos de parede em
    uma parede com abertura; essa decisao e' da CR-B."""
    rows = [[solid(0.0, 100.0), solid(100.0 + GAP_MAX + 10.0, 1000.0)]
            for _ in range(6)]
    assert detect(courses_from_rows(rows)) == []


def test_dois_trechos_separados_nao_ganham_abertura_por_consenso():
    """Uma fiada com DOIS vazios distintos continua produzindo DOIS
    trechos - o consenso nao funde nem cria abertura nova."""
    rows = [[solid(0.0, 100.0), solid(200.0, 400.0), solid(500.0, 900.0)]
            for _ in range(6)]
    openings = detect(courses_from_rows(rows))
    assert len(openings) == 2, openings
    assert [op["x_range"] for op in openings] == [(100.0, 200.0), (400.0, 500.0)]
    assert all(op["jamb_spread_cm"] == 0.0 for op in openings)


# --------------------------------------------------------------------------
# 6. proveniencia: abertura MEDIDA x RECONSTRUIDA
# --------------------------------------------------------------------------

def test_vocabulario_de_proveniencia_exportado():
    """As quatro etiquetas sao contrato publico do modulo (`__all__`) -
    quem reconstroi gabarito precisa poder nomear a origem da geometria."""
    for name, value in (("OPENING_PROVENANCE_MEASURED", "MEASURED"),
                        ("OPENING_PROVENANCE_CONSENSUS", "RECONSTRUCTED_CONSENSUS"),
                        ("OPENING_PROVENANCE_ENVELOPE", "RECONSTRUCTED_ENVELOPE"),
                        ("OPENING_PROVENANCE_INCONCLUSIVE", "INCONCLUSIVE")):
        assert getattr(m, name, None) == value, name


def test_toda_abertura_reconstruida_carrega_proveniencia():
    rows = [wall_with_void(300.0, 391.0) for _ in range(6)]
    for op in detect(courses_from_rows(rows)):
        assert op["opening_provenance"] in (PROV_CONSENSUS, PROV_INCONCLUSIVE)


def test_detector_nunca_declara_abertura_MEASURED():
    """Este modulo RECONSTROI a partir das pecas; `MEASURED` e' reservado
    a quem tem `source_element_id` do Revit. O vocabulario existe para os
    dois lados, mas o detector nao pode se autodeclarar medido."""
    assert PROV_MEASURED == "MEASURED"
    assert PROV_ENVELOPE == "RECONSTRUCTED_ENVELOPE"
    rows = [wall_with_void(300.0, 391.0), wall_with_void(295.0, 391.0),
            wall_with_void(300.0, 391.0), wall_with_void(295.0, 391.0)]
    codes = {op["opening_provenance"] for op in detect(courses_from_rows(rows))}
    assert PROV_MEASURED not in codes
    assert PROV_ENVELOPE not in codes


# --------------------------------------------------------------------------
# 7. determinismo e invariancias
# --------------------------------------------------------------------------

def test_determinismo_repeticao_e_ordem_de_entrada():
    courses = _courses_no_TL_na_jamba()
    primeiro = detect(courses)
    for _ in range(5):
        assert detect(courses) == primeiro
    # a funcao ordena por z: embaralhar a entrada nao pode mudar a saida
    assert detect(list(reversed(courses))) == primeiro


@pytest.mark.parametrize("delta", [-1234.5, -0.75, 0.0, 0.75, 5000.0])
def test_invariancia_a_translacao_do_eixo(delta):
    """Transladar a parede inteira desloca o vao pelo mesmo valor e nao
    muda largura, desacordo nem proveniencia."""
    base = detect(_courses_no_TL_na_jamba())[0]
    movido = [(z, [(s + delta, e + delta, f) for s, e, f in iv])
              for z, iv in _courses_no_TL_na_jamba()]
    op = detect(movido)[0]
    assert op["x_range"][0] == pytest.approx(base["x_range"][0] + delta)
    assert op["x_range"][1] == pytest.approx(base["x_range"][1] + delta)
    assert op["width_cm"] == pytest.approx(base["width_cm"])
    assert op["jamb_spread_cm"] == pytest.approx(base["jamb_spread_cm"])
    assert op["opening_provenance"] == base["opening_provenance"]


def test_invariancia_a_reversao_do_eixo():
    """Reverter o sentido do eixo (equivalente, em coordenada axial, ao
    espelhamento da parede e a' rotacao de 180 graus no plano) espelha o
    vao e preserva largura e desacordo."""
    courses = _courses_no_TL_na_jamba()
    base = detect(courses)[0]
    length = 1400.0
    revertido = [(z, [(length - e, length - s, f) for s, e, f in iv])
                 for z, iv in courses]
    op = detect(revertido)[0]
    assert op["x_range"] == (length - base["x_range"][1],
                             length - base["x_range"][0]), (op, base)
    assert op["width_cm"] == pytest.approx(base["width_cm"])
    assert op["jamb_spread_start_cm"] == pytest.approx(base["jamb_spread_end_cm"])
    assert op["jamb_spread_end_cm"] == pytest.approx(base["jamb_spread_start_cm"])


def test_invariancia_a_espelho_da_ordem_das_fiadas():
    """Espelhar a ordem VERTICAL das fiadas (z crescente x decrescente) nao
    pode mudar a geometria gravada - so' a classificacao PORTA/JANELA
    depende de qual fiada e' a base."""
    courses = _courses_no_TL_na_jamba()
    base = detect(courses)[0]
    z_max = max(z for z, _ in courses)
    espelhado = [(z_max - z, iv) for z, iv in courses]
    op = detect(espelhado)[0]
    assert op["x_range"] == base["x_range"]
    assert op["width_cm"] == base["width_cm"]
    assert op["jamb_spread_cm"] == base["jamb_spread_cm"]


# --------------------------------------------------------------------------
# 8. corpus real (gabarito humano congelado) - regressao das 19 aberturas
# --------------------------------------------------------------------------

def _courses_of_wall(wall):
    by_z = {}
    for r in wall.get("rows") or []:
        bucket = by_z.setdefault(r.get("elevation_cm"), [])
        for b in r.get("blocks") or []:
            bucket.append((b["t_start_cm"], b["t_end_cm"], b.get("type_name")))
    return [(z, iv) for z, iv in sorted(by_z.items())]


def _corpus_openings(project_id):
    path = os.path.join(PROJECTS_DIR, project_id, "reference.json")
    if not os.path.isfile(path):
        pytest.skip("corpus ausente: %s" % path)
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    out = []
    for wall in data.get("walls") or []:
        courses = _courses_of_wall(wall)
        for op in detect(courses):
            out.append((wall["id"], courses, op))
    return out


@pytest.mark.parametrize("project_id", CORPUS)
def test_corpus_nenhuma_abertura_alargada_nem_fora_do_envelope(project_id):
    """Hard gate: a correcao so' pode ESTREITAR, e sempre para dentro do
    envelope antigo. Nenhuma abertura pode aparecer, sumir ou crescer."""
    for wall_id, _courses, op in _corpus_openings(project_id):
        lo, hi = op["x_range"]
        elo, ehi = op["x_range_envelope"]
        assert elo <= lo <= hi <= ehi, (project_id, wall_id, op)
        assert op["width_cm"] <= (ehi - elo) + 1e-9, (project_id, wall_id, op)


@pytest.mark.parametrize("project_id", CORPUS)
def test_corpus_vao_gravado_nao_contem_peca_de_nenhuma_fiada(project_id):
    """AUSENCIA DE INVASAO FISICA no corpus inteiro: o vao gravado nao
    encosta em peca de fiada nenhuma do proprio trecho."""
    for wall_id, courses, op in _corpus_openings(project_id):
        if op["opening_provenance"] != PROV_CONSENSUS:
            continue
        lo, hi = op["x_range"]
        z_lo, z_hi = op["z_range"]
        for z_cm, intervals in courses:
            if not (z_lo <= z_cm <= z_hi):
                continue
            for t_lo, t_hi, fam in intervals:
                assert t_hi <= lo + 1e-9 or t_lo >= hi - 1e-9, (
                    project_id, wall_id, z_cm, fam, (t_lo, t_hi), (lo, hi))


@pytest.mark.parametrize("project_id", CORPUS)
def test_corpus_assinatura_de_15cm_some_e_o_desacordo_fica_registrado(project_id):
    """As 19 aberturas por projeto com a assinatura `B34 - B19 = 15,0cm`:
    a largura gravada perde os 30,0cm de inflacao (15,0 em cada jamba) e o
    desacordo passa a ser DADO (`jamb_spread_cm == 15,0`)."""
    ops = [op for _w, _c, op in _corpus_openings(project_id)]
    assinatura = [op for op in ops if op["jamb_spread_cm"] >= 14.9]
    assert len(assinatura) == 19, [op["x_range"] for op in assinatura]
    for op in assinatura:
        elo, ehi = op["x_range_envelope"]
        assert (ehi - elo) - op["width_cm"] == pytest.approx(30.0, abs=0.02), op
        # a largura inflada (186 / 131 / 266) nao existe mais
        assert op["width_cm"] not in (186.0, 131.0, 266.0), op


@pytest.mark.parametrize("project_id", CORPUS)
def test_corpus_toda_abertura_tem_proveniencia_e_largura_de_dominio(project_id):
    for wall_id, _courses, op in _corpus_openings(project_id):
        assert op["opening_provenance"] in (PROV_CONSENSUS, PROV_INCONCLUSIVE), op
        if op["opening_provenance"] == PROV_CONSENSUS:
            assert GAP_MIN <= op["width_cm"] <= GAP_MAX, (wall_id, op)


@pytest.mark.parametrize("project_id", CORPUS)
def test_corpus_determinismo_em_duas_passadas(project_id):
    primeiro = [(w, op) for w, _c, op in _corpus_openings(project_id)]
    segundo = [(w, op) for w, _c, op in _corpus_openings(project_id)]
    assert primeiro == segundo
