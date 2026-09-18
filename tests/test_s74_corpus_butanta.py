# -*- coding: utf-8 -*-
"""AUDITORIA DA SECAO 74 sobre o corpus versionado do BUTANTA R08_LT.

Este arquivo existe para responder a uma limitacao real de uma auditoria
independente: as alegacoes da secao 74 foram medidas sobre a geometria do
projeto, que nao estava no repositorio - entao nao dava para reproduzir nos
24/44/46, controles 12/26, a parede 8284580 nem o hash do snapshot.

O corpus agora esta' versionado em
`reference_projects/butanta_r08_lt/s74_corpus/` (STATUS: EVIDENCIA / NAO NORMA)
e estes testes o entregam as FUNCOES REAIS do motor. Nenhuma decisao do motor e'
reimplementada aqui: `_t_intersection_room_ok` e' chamada, nunca copiada.

    python3 -m pytest tests/test_s74_corpus_butanta.py -q
"""
import hashlib
import io
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "audit"))

import s74_corpus as S  # noqa: E402

GEO = S.geometry()
EXP = S.t_nodes_expected()
CASO = S.wall_case()
SNAP = S.snapshot_expected()
CTX = S.build_context(GEO)
POR_INDICE = dict((r["provenance"]["bench_node_index"], r) for r in EXP["t_nodes"])

# apelidos do relatorio -> o que cada no' e'
RUIDO = (24, 44, 46)          # reprovavam por variacao submilimetrica de modelagem
CONTROLES = (12, 26)          # a MESMA principal, sobrando pela mesma magnitude
FALTA_4CM = (19, 20, 39)
FALTA_15CM = (30, 18)
FALTA_20CM = (28, 22)


def _no(indice):
    assert indice in POR_INDICE, "o corpus nao tem o no' %s" % indice
    return POR_INDICE[indice]


def _solve(rotulo, geo=None):
    """(ctx, res) do solve REAL, memorizado - cada configuracao roda uma vez.

    Cada configuracao resolve sobre um GRAFO NOVO: o motor grava nos proprios
    nos a marca de decisao unica da secao 72, entao reaproveitar o grafo faria
    a busca de paridade rodar de verdade so na PRIMEIRA configuracao e ser
    curto-circuitada nas seguintes. Ver s74_corpus.solve_on_fresh_context."""
    cache = _solve.__dict__.setdefault("cache", {})
    if rotulo not in cache:
        alvo = geo if geo is not None else GEO
        if rotulo in ("off", "variante_off"):
            cache[rotulo] = S.solve_on_fresh_context(alvo, False)
        elif rotulo in ("on", "variante_on"):
            cache[rotulo] = S.solve_on_fresh_context(alvo, True)
        elif rotulo == "pre_regra76":
            cache[rotulo] = S.solve_on_fresh_context(alvo, False, regra76_d1=False,
                                                     regra76_nao_resolvido=False)
        elif rotulo.startswith("legado_"):
            cache[rotulo] = S.solve_on_fresh_context(alvo, rotulo.endswith("_on"),
                                                     strategy=None)
        else:
            with S.forced_tolerance_cm(float(rotulo)):
                cache[rotulo] = S.solve_on_fresh_context(alvo, True)
    return cache[rotulo]


# =============================================== 1. a geometria reconstroi
def test_a_geometria_versionada_reconstroi_a_planta():
    assert len(GEO["walls"]) == 34
    assert len(GEO["openings"]) == 44
    assert sum(len(v) for v in CTX["openings_per_wall"]) == 44
    assert len(CTX["diag"]["unassigned_openings"]) == 0
    assert len(S.tee_nodes(CTX)) == 37


def test_as_chaves_do_corpus_sao_as_do_grafo_reconstruido():
    vistas = set(S.node_key(CTX, i) for i, _n in S.tee_nodes(CTX))
    assert vistas == set(r["key"] for r in EXP["t_nodes"])


def test_a_chave_logica_nao_depende_de_elementid_nem_de_indice():
    for r in EXP["t_nodes"]:
        x, y = r["position_cm"]
        assert r["key"] == "T@%.1f,%.1f" % (round(x, 1) + 0.0, round(y, 1) + 0.0)


# ===================================== 2. o espaco medido bate com o corpus
def test_o_espaco_de_cada_T_e_reproduzido_pelo_motor():
    for indice, r in sorted(POR_INDICE.items()):
        a = S.assessment_cm(CTX, indice)
        assert a is not None, indice
        for campo in ("room_plus_cm", "room_minus_cm", "room_min_cm", "room_incoming_cm"):
            assert abs(a[campo] - r[campo]) < 1e-6, (indice, campo, a[campo], r[campo])


def test_as_exigencias_sao_as_constantes_do_motor():
    b54, b34 = S.exige_cm()
    assert abs(b54 - 27.0) < 1e-9 and abs(b34 - 34.0) < 1e-9
    assert S.tolerance_cm() == 0.05


def test_o_veredito_e_funcao_exata_do_espaco_medido_e_da_tolerancia():
    """O teste que impede a auditoria de ser circular.

    Nao confere o veredito contra um veredito GRAVADO: confere contra a
    ARITMETICA da propria semantica declarada da secao 74 - "o espaco medido
    mais a tolerancia alcanca a exigencia?" - aplicada aos numeros medidos. Se o
    motor decidisse por qualquer outro criterio, ou se um valor esperado do
    corpus estivesse errado, isto quebraria.
    """
    b54, b34 = S.exige_cm()
    sem_secao_74 = 1e-6 * S.CM_PER_FT          # o epsilon historico, em cm
    for indice, r in sorted(POR_INDICE.items()):
        for ligada, t in ((False, sem_secao_74), (True, S.tolerance_cm())):
            previsto = (r["room_min_cm"] + t >= b54) and (r["room_incoming_cm"] + t >= b34)
            assert S.room_ok(CTX, indice, ligada) is previsto, (indice, ligada, r["room_min_cm"])


def test_a_diferenca_entre_as_duas_tolerancias_e_a_secao_74_inteira():
    """0,05 cm contra 0,0000305 cm: a secao 74 e' exatamente este delta."""
    _m, ws = S.engine()
    antes = ws.T_ROOM_PHYSICAL_TOLERANCE
    try:
        ws.T_ROOM_PHYSICAL_TOLERANCE = False
        assert abs(ws._t_intersection_room_tolerance_ft() - 1e-6) < 1e-18
        ws.T_ROOM_PHYSICAL_TOLERANCE = True
        esperado = S.tolerance_cm() / 100.0 * ws.FEET_PER_METER
        assert abs(ws._t_intersection_room_tolerance_ft() - esperado) < 1e-15
    finally:
        ws.T_ROOM_PHYSICAL_TOLERANCE = antes
    assert ws.T_ROOM_PHYSICAL_TOLERANCE is False, "o motor vem desligado por padrao"


# ============================== 3. os tres casos de variacao de modelagem
@pytest.mark.parametrize("indice", RUIDO)
def test_os_nos_24_44_46_so_passam_com_a_secao_74(indice):
    r = _no(indice)
    falta = r["shortfall_b54_cm"]
    assert 0.0 < falta <= S.tolerance_cm(), (indice, falta)
    assert S.room_ok(CTX, indice, False) is False
    assert S.room_ok(CTX, indice, True) is True


@pytest.mark.parametrize("indice", CONTROLES)
def test_os_controles_12_26_ja_passavam_pela_mesma_magnitude(indice):
    r = _no(indice)
    assert r["shortfall_b54_cm"] < 0.0
    assert abs(r["shortfall_b54_cm"]) <= S.tolerance_cm()
    assert S.room_ok(CTX, indice, False) is True
    assert S.room_ok(CTX, indice, True) is True


def test_o_controle_esta_na_MESMA_parede_principal_do_caso():
    """O argumento central: 24 x 26 e 44/46 x 12 dividem a principal e diferem
    so' no SINAL do desvio de modelagem."""
    assert _no(24)["main_wall_key"] == _no(26)["main_wall_key"]
    assert _no(44)["main_wall_key"] == _no(12)["main_wall_key"]
    assert _no(46)["main_wall_key"] == _no(12)["main_wall_key"]
    assert abs(abs(_no(24)["shortfall_b54_cm"]) - abs(_no(26)["shortfall_b54_cm"])) < 1e-9
    assert abs(abs(_no(44)["shortfall_b54_cm"]) - abs(_no(12)["shortfall_b54_cm"])) < 1e-9


# ========================== 4. o portao continua reprovando quem nao cabe
@pytest.mark.parametrize("indice", FALTA_4CM + FALTA_15CM + FALTA_20CM)
def test_falta_material_continua_reprovando_nos_dois_estados(indice):
    r = _no(indice)
    assert r["shortfall_b54_cm"] > 1.0, (indice, r["shortfall_b54_cm"])
    assert S.room_ok(CTX, indice, False) is False
    assert S.room_ok(CTX, indice, True) is False


def test_as_faixas_de_falta_do_relatorio_existem_no_corpus():
    def faixa(indices):
        return [round(_no(i)["shortfall_b54_cm"], 1) for i in indices]
    assert faixa(FALTA_4CM) == [4.0, 4.0, 4.0]
    assert faixa(FALTA_15CM) == [15.0, 15.0]
    assert faixa(FALTA_20CM) == [20.0, 20.0]


def test_a_secao_74_muda_o_veredito_de_exatamente_tres_nos():
    mudaram = [i for i in sorted(POR_INDICE)
               if S.room_ok(CTX, i, False) != S.room_ok(CTX, i, True)]
    assert mudaram == sorted(RUIDO)


# ===================== 5. a separacao entre modelagem e insuficiencia real
def test_ha_uma_separacao_grande_entre_variacao_de_modelagem_e_falta_real():
    """A justificativa do 0,05 cm - que NAO e' a saturacao, e sim esta separacao."""
    mv = EXP["modeling_variation"]
    tol = S.tolerance_cm()
    na_fronteira = max(abs(r["shortfall_b54_cm"]) for r in EXP["t_nodes"]
                       if abs(r["shortfall_b54_cm"]) <= 0.1)
    proximo = min(r["shortfall_b54_cm"] for r in EXP["t_nodes"]
                  if r["shortfall_b54_cm"] > 0.1)
    assert abs(na_fronteira - mv["max_abs_deviation_at_boundary_cm"]) < 1e-6
    assert abs(proximo - mv["next_materially_insufficient_cm"]) < 1e-6
    # a tolerancia fica ACIMA de toda a variacao de modelagem observada...
    assert tol > mv["max_modeling_deviation_cm"] > na_fronteira
    assert abs(mv["ratio_tolerance_over_max_modeling_deviation"]
               - round(tol / mv["max_modeling_deviation_cm"], 2)) < 1e-9
    # ...e MUITO abaixo do primeiro caso materialmente insuficiente
    assert abs(mv["ratio_next_over_tolerance"] - round(proximo / tol, 1)) < 1e-6
    assert proximo / tol > 50.0
    assert proximo - mv["max_modeling_deviation_cm"] > 3.5


def test_a_variacao_de_modelagem_e_medida_na_propria_geometria():
    """Nao e' um numero declarado: e' o afastamento do centimetro inteiro que a
    geometria versionada realmente tem."""
    mv = EXP["modeling_variation"]
    fontes = mv["max_modeling_deviation_by_source_cm"]
    comprimentos = max(abs(w["length_cm"] - round(w["length_cm"])) for w in GEO["walls"])
    pontas = max(abs(c - round(c)) for w in GEO["walls"]
                 for p in (w["p0_cm"], w["p1_cm"]) for c in p)
    salas = max(abs(r["room_min_cm"] - round(r["room_min_cm"])) for r in EXP["t_nodes"])
    assert abs(comprimentos - fontes["wall_length"]) < 1e-6
    assert abs(pontas - fontes["wall_endpoint"]) < 1e-6
    assert abs(salas - fontes["t_room_min"]) < 1e-6
    assert abs(max(comprimentos, pontas, salas) - mv["max_modeling_deviation_cm"]) < 1e-6


# ================================ 6. o veredito nao depende da apresentacao
def test_o_veredito_nao_muda_com_translacao():
    ctx2 = S.build_context(GEO, translate=(1234.0, -567.0))
    _compara_vereditos(ctx2)


def test_o_veredito_nao_muda_invertendo_as_pontas_da_principal():
    ctx2 = S.build_context(GEO, swap_ends=(_no(46)["main_wall_key"],))
    _compara_vereditos(ctx2)


def _compara_vereditos(ctx2):
    def mapa(ctx):
        return dict((S.node_key(ctx, i), (S.room_ok(ctx, i, False), S.room_ok(ctx, i, True)))
                    for i, _n in S.tee_nodes(ctx))
    assert mapa(ctx2) == mapa(CTX)


def test_determinismo_do_veredito():
    for indice in RUIDO:
        assert (S.room_ok(CTX, indice, True) is S.room_ok(CTX, indice, True)
                is S.room_ok(CTX, indice, True))


def test_a_flag_e_restaurada_depois_de_cada_consulta():
    _m, ws = S.engine()
    antes = ws.T_ROOM_PHYSICAL_TOLERANCE
    S.room_ok(CTX, 46, True)
    S.room_ok(CTX, 46, False)
    assert ws.T_ROOM_PHYSICAL_TOLERANCE is antes
    assert ws.T_ROOM_PHYSICAL_TOLERANCE is False, "o motor precisa vir desligado por padrao"


# ============================================= 7. a parede 8284580 (o caso)
@pytest.mark.slow
def test_a_parede_8284580_muda_de_composicao_com_a_secao_74():
    """A composicao humana e TESTEMUNHA de uma parede, nao alvo: o teste nao
    exige que o solver chegue perto dela. Confere que composicao e divergencia
    MEDIDAS batem com o corpus e que os estados diferem entre si.

    O efeito isolado da secao 74 e' medido contra `flag_off_motor_pre_regra76`
    (secao 74 E correcao D1 da regra 76 desligadas - o motor que a auditoria
    independente conferiu). Com a D1 ligada, o `flag_off` do produto ja' resgata o
    no' 46 como L degradado e a parede fica igual a `flag_on`: isso e' da regra 76,
    nao da secao 74, e fica declarado aqui em vez de apagar o contrafactual."""
    H = CASO["human_counts"]
    medidas = {}
    for rotulo, chave in (("flag_off", "off"), ("flag_on", "on"),
                          ("flag_off_motor_pre_regra76", "pre_regra76")):
        ctx_s, res = _solve(chave)
        contagem = S.wall_counts(S.solver_rows(ctx_s, res, GEO), GEO, CASO["wall_key"])
        esperado = CASO["expected"][rotulo]
        assert contagem == esperado["solver_counts"], (rotulo, contagem)
        medidas[rotulo] = S.divergence(H, contagem)
        assert medidas[rotulo] == esperado["divergence"], (rotulo, medidas[rotulo])
    # comparacao entre estados medidos - sem limiar absoluto contra o humano
    antes = medidas["flag_off_motor_pre_regra76"]
    assert medidas["flag_on"]["div"] < antes["div"]
    assert medidas["flag_on"]["comp_delta"] < antes["comp_delta"]
    assert medidas["flag_off"] == medidas["flag_on"], "com a D1 o no' 46 ja' degrada para L sem a secao 74"


@pytest.mark.slow
def test_os_hard_gates_continuam_zerados_com_a_secao_74():
    for rotulo in ("off", "on"):
        _ctx, res = _solve(rotulo)
        assert S.hard_gates(res) == {"collisions": 0, "non_modular": 0,
                                     "unsupported": 0, "opening_invasion": 0,
                                     "channel_as_junction_bond": 0}


# ================================================ 8. saturacao da tolerancia
@pytest.mark.slow
def test_a_tolerancia_satura_o_conjunto_fisico_e_por_isso_nao_ha_precipicio():
    hashes = {}
    for rotulo, chave in (("flag_off", "off"), ("tol_0_05", "on"),
                          ("tol_0_10", "0.10"), ("tol_0_30", "0.30")):
        ctx_s, res = _solve(chave)
        linhas = S.normalized_snapshot(ctx_s, res)
        hashes[rotulo] = S.snapshot_sha256(linhas)
        gravado = [c for c in SNAP["cases"] if c["label"] == rotulo][0]
        assert hashes[rotulo] == gravado["sha256"], rotulo
        assert len(linhas) == gravado["pieces"], rotulo
    assert hashes["tol_0_05"] == hashes["tol_0_10"] == hashes["tol_0_30"]
    assert hashes["flag_off"] != hashes["tol_0_05"]


@pytest.mark.slow
def test_o_contrafactual_anterior_a_regra_76_continua_reproduzivel():
    """O `flag_off` auditado antes da regra 76 e' o caso
    `flag_off_motor_pre_regra76` de agora: mesmo hash, mesmas pecas."""
    ctx_s, res = _solve("pre_regra76")
    linhas = S.normalized_snapshot(ctx_s, res)
    gravado = [c for c in SNAP["cases"] if c["label"] == "flag_off_motor_pre_regra76"][0]
    assert S.snapshot_sha256(linhas) == gravado["sha256"]
    assert len(linhas) == gravado["pieces"]
    assert S.hard_gates(res) == gravado["hard_gates"]


@pytest.mark.slow
def test_o_snapshot_normalizado_e_estavel_na_repeticao():
    ctx_s, res = _solve("on")
    a = S.snapshot_sha256(S.normalized_snapshot(ctx_s, res))
    b = S.snapshot_sha256(S.normalized_snapshot(S.build_context(GEO), res))
    assert a == b


def test_a_normalizacao_do_snapshot_esta_declarada_no_corpus():
    assert SNAP["normalization"] == S.SNAPSHOT_NORMALIZATION == "S74_SNAPSHOT_V1"
    assert "legacy_bench_hash" in SNAP


# ============================ 8.1 a variante pos-microajuste (secao 66)
def test_a_variante_de_abertura_esta_declarada_e_e_de_tres_vaos():
    v = GEO["opening_variants"]["post_micro_adjustment_s66"]
    assert len(v) == 3
    assert sorted(o["key"] for o in v) == [8078984, 8078986, 8079001]
    assert all(abs(o["delta_cm"] - 10.0) < 1e-9 for o in v)
    chaves = set(o["key"] for o in GEO["openings"])
    assert all(o["key"] in chaves for o in v)


@pytest.mark.slow
def test_a_variante_pos_microajuste_reproduz_os_totais_medidos():
    """A varredura de tolerancia do checkpoint mediu os totais da regua sobre o
    estado DEPOIS do microajuste. As duas variantes ficam versionadas para que os
    dois conjuntos de numeros possam ser conferidos."""
    casos = SNAP.get("opening_variant_cases") or []
    assert casos, "o corpus precisa trazer a variante pos-microajuste"
    geo_v = S.with_opening_variant(GEO, "post_micro_adjustment_s66")
    assert [o["center_cm"] for o in geo_v["openings"]] != [o["center_cm"] for o in GEO["openings"]]
    for caso in casos:
        chave = "variante_off" if caso["label"] == "flag_off" else "variante_on"
        ctx_v, res = _solve(chave, geo=geo_v)
        linhas = S.normalized_snapshot(ctx_v, res)
        rows = S.solver_rows(ctx_v, res, geo_v)
        assert S.snapshot_sha256(linhas) == caso["sha256"], caso["label"]
        assert len(linhas) == caso["pieces"], caso["label"]
        assert len(rows) == caso["ruler_pieces"], caso["label"]
        assert S.hard_gates(res) == caso["hard_gates"], caso["label"]
        codigos = {}
        for _k, _ci, code, _lo, _hi in rows:
            codigos[code] = codigos.get(code, 0) + 1
        assert codigos == caso["ruler_codes"], caso["label"]


# ================================================== 9. proveniencia completa
def test_a_proveniencia_responde_de_onde_saiu_cada_numero():
    p = GEO["provenance"]
    for campo in ("source_project", "source_version", "extraction_date", "units",
                  "coordinate_system", "level", "wall_population", "extraction_script",
                  "engine_commit_s74", "raw_inputs_not_versioned"):
        assert p.get(campo), campo
    assert GEO["status"] == "EVIDENCE_NOT_NORM"
    for w in GEO["walls"]:
        assert w["provenance"]["revit_element_id"]
    assert CASO["provenance"]["revit_element_id"] == 8284580


# ================== 10. o que este corpus NAO cobre - declarado, nao escondido
def test_o_corpus_declara_que_nao_exerce_a_perna_do_B34():
    """`_t_intersection_room_ok` e' uma CONJUNCAO: espaco para o B54 na parede
    principal E espaco para o B34 na que chega. Neste corpus so' a primeira perna
    e' exercida - a boneca mais apertada tem folga de dezenas de centimetros. Em
    vez de deixar esse buraco invisivel, o corpus declara e este teste confere a
    declaracao: se um dia a geometria trouxer um T apertado na boneca, isto quebra
    e obriga a revisar a cobertura."""
    cov = EXP["coverage"]
    assert cov["b54_leg_exercised"] is True
    assert cov["b34_leg_exercised"] is False
    medido = min(r["room_incoming_cm"] for r in EXP["t_nodes"])
    assert abs(medido - cov["min_room_incoming_cm"]) < 1e-6
    _b54, b34 = S.exige_cm()
    assert abs(b34 - cov["b34_required_cm"]) < 1e-9
    assert medido > b34 + 30.0, (medido, b34)
    assert cov["note"]


# ============ 11. o legado (strategy=None) nao passa pelo fluxo CHANNEL
@pytest.mark.slow
def test_o_legado_e_identico_com_e_sem_a_flag_da_secao_74():
    """`strategy=None` nao entra no fluxo CHANNEL, entao a secao 74 nao pode
    alcanca-lo. Antes isto era alegacao de bancada; agora e' verificavel aqui."""
    casos = SNAP.get("legacy_cases") or []
    assert len(casos) == 2, "o corpus precisa trazer os dois casos do legado"
    vistos = set()
    for caso in casos:
        chave = "legado_off" if caso["label"].endswith("_off") else "legado_on"
        ctx_l, res = _solve(chave)
        linhas = S.normalized_snapshot(ctx_l, res)
        assert S.snapshot_sha256(linhas) == caso["sha256"], caso["label"]
        assert len(linhas) == caso["pieces"], caso["label"]
        vistos.add(caso["sha256"])
    assert len(vistos) == 1, "o legado mudou com a flag - a secao 74 vazou para fora do CHANNEL"
    principais = dict((c["label"], c["sha256"]) for c in SNAP["cases"])
    assert vistos.pop() not in principais.values(), "legado e CHANNEL nao podem coincidir"


# ================== 12. o inventario do acervo aponta para ESTES arquivos
def test_o_inventario_do_acervo_bate_com_os_arquivos_do_corpus():
    """O inventario e' o registro de integridade que deixa um auditor externo
    confiar no corpus. Um hash desatualizado ali inverte o efeito, e ate' agora
    nada cobria isso - entao um README reeditado passava despercebido."""
    caminho = os.path.join(ROOT, "reference_projects", "inventory.json")
    inv = json.load(io.open(caminho, encoding="utf-8"))
    projetos = [p for p in inv["projects"] if p["id"] == "butanta_r08_lt_s74_corpus"]
    assert len(projetos) == 1, "o corpus da secao 74 precisa estar no inventario"
    projeto = projetos[0]
    assert projeto["status"] == "EVIDENCE_NOT_NORM"
    assert projeto["portal"].endswith("s74_corpus/README.md")
    assert projeto["files"], "o inventario precisa listar os arquivos do corpus"
    for entrada in projeto["files"]:
        alvo = os.path.join(ROOT, entrada["path"].replace("/", os.sep))
        assert os.path.isfile(alvo), entrada["path"]
        dados = open(alvo, "rb").read().replace(b"\r\n", b"\n")   # convencao do arquivo: LF
        assert hashlib.sha256(dados).hexdigest() == entrada["sha256"], entrada["path"]
    inventariados = set(os.path.basename(e["path"]) for e in projeto["files"])
    no_disco = set(n for n in os.listdir(S.CORPUS_DIR) if n.endswith(".json"))
    assert no_disco <= inventariados, "ha' JSON no corpus fora do inventario: %s" % (
        sorted(no_disco - inventariados),)
