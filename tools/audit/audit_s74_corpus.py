# -*- coding: utf-8 -*-
"""Runner autonomo da auditoria da SECAO 74 sobre o corpus versionado do BUTANTA R08_LT.

PARA QUE SERVE
--------------
A secao 74 (commit 2c55211) trocou UMA comparacao em `nuvem/core/engine/wall_stepper.py`,
dentro de `_t_intersection_room_ok`: o teste "cabe um B54 centrado no no'?" comparava com
+1e-6 PES (0,3 micrometro - epsilon de ponto flutuante) e passou a comparar com a tolerancia
FISICA `PIER_PHYSICAL_FIT_TOLERANCE_CM` = 0,05 cm, que o motor ja' definia. A mudanca e'
SEMANTICA e DELIBERADA: a fronteira historica de cabe / nao cabe foi ampliada em ate' 0,05 cm
para absorver a variacao submilimetrica REAL de modelagem da planta - nao e' correcao de
ruido numerico.

Uma auditoria independente sustentou a implementacao, mas com uma limitacao material: a
geometria do BUTANTA usada nas alegacoes nao estava versionada, entao nada disso era
reproduzivel de fora. O corpus agora esta' em `reference_projects/butanta_r08_lt/s74_corpus/`
(STATUS: EVIDENCIA / NAO NORMA - a modulacao humana e' testemunha, nunca gabarito) e este
runner o entrega as FUNCOES REAIS do motor.

A FRONTEIRA E' EXPLICITA
------------------------
Nada que decida "cabe / nao cabe" e' reimplementado aqui. `_t_intersection_room_ok` e
`_t_intersection_room_assessment` sao CHAMADAS atraves de `tools/audit/s74_corpus.py`, nunca
copiadas. Este arquivo so' compara o que o motor devolve com o que o corpus registrou.

COMO LER A JUSTIFICATIVA DO 0,05 cm
-----------------------------------
O caso 08 e' a justificativa: a maior variacao de modelagem medida no corpus e' 0,013251 cm,
a tolerancia fica acima dela (cerca de 3,8x) e MUITO abaixo do primeiro caso materialmente
insuficiente, 4,001054 cm (cerca de 80x a tolerancia). O caso 12 (saturacao: 0,05 / 0,10 /
0,30 produzem o MESMO conjunto fisico) NAO justifica o valor - ele so' mostra que nao ha'
precipicio perto da fronteira escolhida.

COMO RODAR
----------
    python tools/audit/audit_s74_corpus.py            # completo (casos 10-12 rodam o solver)
    python tools/audit/audit_s74_corpus.py --rapido   # pula so' os casos 10, 11 e 12

Sai com codigo 0 se tudo o que rodou passou, 1 se qualquer caso falhou. Os casos 10, 11 e 12
rodam o solver REAL das 34 paredes (cerca de 30 s por configuracao); cada configuracao e'
resolvida uma unica vez e memorizada.
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import s74_corpus as S  # noqa: E402

# apelidos do relatorio -> o que cada no' e' (indices de bancada, gravados no corpus)
RUIDO = (24, 44, 46)              # so' passam COM a secao 74
CONTROLES = (12, 26)              # ja' passavam, pela mesma magnitude com sinal contrario
FALTA_4CM = (19, 20, 39)
FALTA_15CM = (30, 18)
FALTA_20CM = (28, 22)
PARES_CONTROLE = ((24, 26), (44, 12), (46, 12))

CAMPOS_ESPACO = ("room_plus_cm", "room_minus_cm", "room_min_cm", "room_incoming_cm")
TOL_MEDIDA_CM = 1e-6              # o corpus e o motor tem de bater nesta casa
TOL_MODULO_CM = 1e-9              # "mesmo modulo" entre caso e controle
FRONTEIRA_CM = 0.1                # |falta| <= 0,1 cm: onde a modelagem decide o veredito
GATES_ZERADOS = {"collisions": 0, "non_modular": 0, "unsupported": 0, "opening_invasion": 0,
                 "channel_as_junction_bond": 0}
TRANSLACAO_CM = (1234.0, -567.0)
SATURACAO = (("flag_off", "off"), ("tol_0_05", "on"), ("tol_0_10", "0.10"), ("tol_0_30", "0.30"))
MOTIVO_RAPIDO = "--rapido: solver completo (cerca de 30 s por configuracao) nao executado"


def _v(ok):
    return "PASSA" if ok else "REPROVA"


def _resumo_pecas(contagem):
    return " ".join("%s=%d" % (k, contagem[k]) for k in sorted(contagem) if not k.startswith("Z_"))


# ================================================================== bancada
class Bancada(object):
    """Corpus lido uma vez, contexto do motor montado uma vez, solves memorizados."""

    def __init__(self):
        self.geo = S.geometry()
        self.exp = S.t_nodes_expected()
        self.parede = S.wall_case()
        self.snap = S.snapshot_expected()
        self.ctx = S.build_context(self.geo)
        self.por_indice = dict((r["provenance"]["bench_node_index"], r) for r in self.exp["t_nodes"])
        self.b54_cm, self.b34_cm = S.exige_cm()
        self.tol_cm = S.tolerance_cm()
        self._solucoes = {}
        self._faltas = None

    def no(self, indice):
        if indice not in self.por_indice:
            raise KeyError("o corpus nao tem o no' %s" % indice)
        return self.por_indice[indice]

    def falta_b54_cm(self, indice, ctx=None):
        """Falta medida para o B54, derivada da AVALIACAO do motor (positiva = nao cabe)."""
        a = S.assessment_cm(ctx or self.ctx, indice)
        if a is None:
            raise ValueError("o motor nao avaliou o no' %s" % indice)
        return self.b54_cm - a["room_min_cm"]

    def faltas(self):
        if self._faltas is None:
            self._faltas = dict((i, self.falta_b54_cm(i)) for i in sorted(self.por_indice))
        return self._faltas

    def veredito(self, indice, ctx=None):
        alvo = ctx or self.ctx
        return S.room_ok(alvo, indice, False), S.room_ok(alvo, indice, True)

    def solucao(self, rotulo):
        """Solve REAL memorizado - cada configuracao roda uma unica vez.

        'off' e 'on' usam a flag do PRODUTO; 'pre76' desliga tambem a D1 da regra 76 (motor
        anterior a' regra 76); '0.10' e '0.30' usam a varredura de saturacao
        (troca so' o parametro da tolerancia, nunca a constante nem a decisao do motor).
        """
        if rotulo not in self._solucoes:
            inicio = time.time()
            if rotulo == "off":
                self._solucoes[rotulo] = S.solve(self.ctx, False, geo=self.geo)
            elif rotulo == "on":
                self._solucoes[rotulo] = S.solve(self.ctx, True, geo=self.geo)
            elif rotulo == "pre76":
                self._solucoes[rotulo] = S.solve(self.ctx, False, geo=self.geo, regra76_d1=False)
            else:
                with S.forced_tolerance_cm(float(rotulo)):
                    self._solucoes[rotulo] = S.solve(self.ctx, True, geo=self.geo)
            print("       (solve %-4s concluido em %.1f s)" % (rotulo, time.time() - inicio))
        return self._solucoes[rotulo]


# ================================================================ relatorio
class Relatorio(object):
    """Uma linha por verificacao, com PASS/FAIL/SKIP e o valor medido."""

    def __init__(self):
        self.pass_n = 0
        self.fail_n = 0
        self.skip_n = 0

    def secao(self, titulo):
        print("")
        print("-- %s" % titulo)

    def _linha(self, status, rotulo, titulo, medido):
        print("%-4s %-6s %-48s %s" % (status, rotulo, titulo, medido))

    def caso(self, rotulo, titulo, ok, medido):
        if ok:
            self.pass_n += 1
        else:
            self.fail_n += 1
        self._linha("PASS" if ok else "FAIL", rotulo, titulo, medido)

    def pulado(self, rotulo, titulo, motivo):
        self.skip_n += 1
        self._linha("SKIP", rotulo, titulo, motivo)

    def nota(self, texto):
        print("     nota: %s" % texto)

    @property
    def total(self):
        return self.pass_n + self.fail_n + self.skip_n


# ============================================================= os 12 casos
def caso_01_geometria(rel, B):
    paredes = len(B.geo["walls"])
    rel.caso("01.1", "paredes de alvenaria reconstruidas", paredes == 34,
             "medido %d (esperado 34)" % paredes)
    aberturas = len(B.geo["openings"])
    rel.caso("01.2", "aberturas no corpus", aberturas == 44,
             "medido %d (esperado 44)" % aberturas)
    atribuidas = sum(len(v) for v in B.ctx["openings_per_wall"])
    orfas = len(B.ctx["diag"]["unassigned_openings"])
    rel.caso("01.3", "aberturas sem parede", orfas == 0 and atribuidas == 44,
             "medido %d orfas, %d atribuidas (esperado 0 / 44)" % (orfas, atribuidas))
    tees = len(S.tee_nodes(B.ctx))
    rel.caso("01.4", "encontros T no grafo do motor", tees == 37,
             "medido %d (esperado 37)" % tees)


def caso_02_espaco_medido(rel, B):
    pior, onde, divergentes = 0.0, "-", []
    for indice in sorted(B.por_indice):
        r = B.no(indice)
        a = S.assessment_cm(B.ctx, indice)
        if a is None:
            divergentes.append("no %d sem avaliacao" % indice)
            continue
        for campo in CAMPOS_ESPACO:
            d = abs(a[campo] - r[campo])
            if d > pior:
                pior, onde = d, "no %d / %s" % (indice, campo)
            if d >= TOL_MEDIDA_CM:
                divergentes.append("no %d / %s" % (indice, campo))
    medidas = len(B.por_indice) * len(CAMPOS_ESPACO)
    rel.caso("02.1", "o espaco de cada T e' reproduzido pelo motor", not divergentes,
             "%d medidas em %d T, maior diferenca %.2e cm (%s)" % (medidas, len(B.por_indice), pior, onde))
    if divergentes:
        rel.nota("divergiram acima de %.0e cm: %s" % (TOL_MEDIDA_CM, ", ".join(divergentes[:8])))

    vistas = set(S.node_key(B.ctx, i) for i, _n in S.tee_nodes(B.ctx))
    esperadas = set(r["key"] for r in B.exp["t_nodes"])
    rel.caso("02.2", "as chaves logicas dos T batem com o corpus", vistas == esperadas,
             "%d chaves, %d divergentes" % (len(vistas), len(vistas ^ esperadas)))

    pior_falta = max(abs(f - B.no(i)["shortfall_b54_cm"]) for i, f in B.faltas().items())
    rel.caso("02.3", "a falta para o B54 derivada do motor bate", pior_falta < TOL_MEDIDA_CM,
             "maior diferenca %.2e cm (exige %.1f cm de cada lado)" % (pior_falta, B.b54_cm))


def caso_03_tres_casos_de_modelagem(rel, B):
    _m, ws = S.engine()
    rel.caso("03.0", "a flag da secao 74 nasce desligada no motor", ws.T_ROOM_PHYSICAL_TOLERANCE is False,
             "T_ROOM_PHYSICAL_TOLERANCE = %s | tolerancia %.2f cm" % (ws.T_ROOM_PHYSICAL_TOLERANCE, B.tol_cm))
    for indice in RUIDO:
        falta = B.faltas()[indice]
        off, on = B.veredito(indice)
        ok = (off is False) and (on is True) and (0.0 < falta <= B.tol_cm)
        rel.caso("03.%d" % indice, "no %d so' cabe COM a secao 74" % indice, ok,
                 "falta %.6f cm | flag off=%s on=%s" % (falta, _v(off), _v(on)))


def caso_04_controles(rel, B):
    for indice in CONTROLES:
        sobra = -B.faltas()[indice]
        off, on = B.veredito(indice)
        ok = (off is True) and (on is True) and (0.0 < sobra <= B.tol_cm)
        rel.caso("04.%d" % indice, "controle %d ja' cabia nos dois estados" % indice, ok,
                 "sobra %.6f cm | flag off=%s on=%s" % (sobra, _v(off), _v(on)))


def caso_05_mesma_principal(rel, B):
    for alvo, controle in PARES_CONTROLE:
        a, b = B.no(alvo), B.no(controle)
        mesma = a["main_wall_key"] == b["main_wall_key"]
        fa, fb = abs(B.faltas()[alvo]), abs(B.faltas()[controle])
        mesmo_modulo = abs(fa - fb) < TOL_MODULO_CM
        rel.caso("05.%d" % alvo, "no %d x controle %d: mesma principal" % (alvo, controle),
                 mesma and mesmo_modulo,
                 "principal %s / %s | modulo %.6f x %.6f cm" % (
                     a["main_wall_key"], b["main_wall_key"], fa, fb))


def caso_06_falta_material(rel, B):
    for ordem, indices in (("4 cm", FALTA_4CM), ("15 cm", FALTA_15CM), ("20 cm", FALTA_20CM)):
        for indice in indices:
            falta = B.faltas()[indice]
            off, on = B.veredito(indice)
            ok = (off is False) and (on is False) and (falta > 1.0)
            rel.caso("06.%d" % indice, "no %d (ordem de %s) reprova nos dois" % (indice, ordem), ok,
                     "falta %.6f cm | flag off=%s on=%s" % (falta, _v(off), _v(on)))


def caso_07_quantos_vereditos_mudam(rel, B):
    mudaram = [i for i in sorted(B.por_indice)
               if S.room_ok(B.ctx, i, False) != S.room_ok(B.ctx, i, True)]
    rel.caso("07.1", "a secao 74 muda exatamente 3 vereditos", mudaram == sorted(RUIDO),
             "mudaram %d de %d T: %s" % (len(mudaram), len(B.por_indice),
                                         ", ".join(str(i) for i in mudaram) or "nenhum"))


def caso_08_separacao(rel, B):
    mv = B.exp["modeling_variation"]
    fontes = mv["max_modeling_deviation_by_source_cm"]
    proximo_gravado = mv["next_materially_insufficient_cm"]

    # a variacao de modelagem e' MEDIDA aqui (afastamento do centimetro inteiro),
    # nao lida de um campo: comprimento de parede, ponta de parede e espaco do T.
    comprimentos = max(abs(w["length_cm"] - round(w["length_cm"])) for w in B.geo["walls"])
    pontas = max(abs(c - round(c)) for w in B.geo["walls"]
                 for p in (w["p0_cm"], w["p1_cm"]) for c in p)
    salas = max(abs(r["room_min_cm"] - round(r["room_min_cm"])) for r in B.exp["t_nodes"])
    variacao = max(comprimentos, pontas, salas)
    # o corpus grava estes valores com 6 casas, entao a comparacao e' na mesma casa (1e-6)
    ok_0 = (abs(comprimentos - fontes["wall_length"]) < TOL_MEDIDA_CM
            and abs(pontas - fontes["wall_endpoint"]) < TOL_MEDIDA_CM
            and abs(salas - fontes["t_room_min"]) < TOL_MEDIDA_CM
            and abs(variacao - mv["max_modeling_deviation_cm"]) < TOL_MEDIDA_CM)
    rel.caso("08.0", "a variacao de modelagem e' medida na geometria", ok_0,
             "comprimento %.6f / ponta %.6f / espaco no T %.6f -> maior %.6f cm (corpus %.6f)" % (
                 comprimentos, pontas, salas, variacao, mv["max_modeling_deviation_cm"]))

    faltas = B.faltas()
    fronteira = max(abs(f) for f in faltas.values() if abs(f) <= FRONTEIRA_CM)
    proximo = min(f for f in faltas.values() if f > FRONTEIRA_CM)

    razao_tol = B.tol_cm / variacao
    ok_1 = (B.tol_cm > variacao > fronteira
            and abs(mv["ratio_tolerance_over_max_modeling_deviation"] - round(razao_tol, 2)) < TOL_MODULO_CM)
    rel.caso("08.1", "tolerancia acima de toda variacao de modelagem", ok_1,
             "variacao %.6f cm (na fronteira %.6f) | tolerancia %.2f cm = %.2fx" % (
                 variacao, fronteira, B.tol_cm, razao_tol))

    razao_prox = proximo / B.tol_cm
    ok_2 = (abs(proximo - proximo_gravado) < TOL_MEDIDA_CM and razao_prox > 50.0
            and abs(mv["ratio_next_over_tolerance"] - round(razao_prox, 1)) < TOL_MODULO_CM)
    rel.caso("08.2", "primeiro caso materialmente insuficiente", ok_2,
             "medido %.6f cm (corpus %.6f) = %.1fx a tolerancia" % (proximo, proximo_gravado, razao_prox))

    ok_3 = (proximo - variacao) > 3.5
    rel.caso("08.3", "separacao entre modelagem e falta real", ok_3,
             "%.6f cm entre a maior variacao e a primeira falta real" % (proximo - variacao))
    rel.nota("o 0,05 cm se justifica por esta separacao, NAO pela saturacao do caso 12")


def caso_09_invariancia(rel, B):
    base = _mapa_vereditos(B.ctx)
    ctx_t = S.build_context(B.geo, translate=TRANSLACAO_CM)
    mapa_t = _mapa_vereditos(ctx_t)
    dif_t = _diferencas(base, mapa_t)
    rel.caso("09.1", "translacao nao muda nenhum veredito", not dif_t and len(mapa_t) == len(base),
             "%d T comparados, %d diferencas (translacao %+.0f, %+.0f cm)" % (
                 len(base), len(dif_t), TRANSLACAO_CM[0], TRANSLACAO_CM[1]))

    principal = B.no(46)["main_wall_key"]
    ctx_s = S.build_context(B.geo, swap_ends=(principal,))
    mapa_s = _mapa_vereditos(ctx_s)
    dif_s = _diferencas(base, mapa_s)
    rel.caso("09.2", "inverter as pontas da principal nao muda nada",
             not dif_s and len(mapa_s) == len(base),
             "%d T comparados, %d diferencas (pontas de %s invertidas)" % (
                 len(base), len(dif_s), principal))


def caso_10_parede_8284580(rel, B):
    humano = B.parede["human_counts"]
    chave = B.parede["wall_key"]
    divs = {}
    for rotulo, solve_id, estado in (
            ("flag_off", "off", "a flag desligada"),
            ("flag_on", "on", "a flag ligada"),
            ("flag_off_motor_pre_regra76", "pre76", "a flag desligada, motor anterior a' regra 76")):
        res = B.solucao(solve_id)
        contagem = S.wall_counts(S.solver_rows(B.ctx, res, B.geo), B.geo, chave)
        esperado = B.parede["expected"][rotulo]
        medida = S.divergence(humano, contagem)
        divs[rotulo] = medida["div"]
        ok = contagem == esperado["solver_counts"] and medida == esperado["divergence"]
        rel.caso("10.%s" % solve_id,
                 "parede 8284580 (%s) com %s" % (chave, estado),
                 ok, "divergencia %.1f (corpus %.1f) | %s" % (
                     medida["div"], esperado["divergence"]["div"], _resumo_pecas(contagem)))
        if not ok:
            rel.nota("contagem medida: %r" % (contagem,))
    antes = divs.get("flag_off_motor_pre_regra76", 0.0)
    ok_salto = antes > 200.0 and divs.get("flag_on", 999.0) < 5.0
    rel.caso("10.3", "a secao 74 aproxima o solver do humano", ok_salto,
             "divergencia %.1f -> %.1f sobre %d pecas humanas" % (
                 antes, divs.get("flag_on", float("nan")),
                 sum(v for k, v in humano.items() if not k.startswith("Z_"))))
    rel.nota("o efeito isolado da secao 74 e' medido contra o motor anterior a' regra 76: com a "
             "correcao D1 da regra 76 o no' 46 ja' degrada para L sem a secao 74 e o flag_off do "
             "produto tambem da' %.1f" % divs.get("flag_off", float("nan")))
    rel.nota("a composicao humana e' EVIDENCIA de uma parede, nao gabarito nem norma")


def caso_11_hard_gates(rel, B):
    for rotulo, solve_id in (("desligada", "off"), ("ligada", "on")):
        g = S.hard_gates(B.solucao(solve_id))
        rel.caso("11.%s" % solve_id, "hard gates com a flag %s" % rotulo, g == GATES_ZERADOS,
                 "colisoes %d / nao-modular %d / sem apoio %d / invasao de vao %d / "
                 "canaleta-como-amarracao %d" % (
                     g["collisions"], g["non_modular"], g["unsupported"], g["opening_invasion"],
                     g["channel_as_junction_bond"]))


def caso_12_saturacao(rel, B):
    gravados = dict((c["label"], c) for c in B.snap["cases"])
    hashes = {}
    for ordem, (rotulo, solve_id) in enumerate(SATURACAO, start=1):
        linhas = S.normalized_snapshot(B.ctx, B.solucao(solve_id))
        assinatura = S.snapshot_sha256(linhas)
        hashes[rotulo] = assinatura
        g = gravados.get(rotulo) or {}
        ok = assinatura == g.get("sha256") and len(linhas) == g.get("pieces")
        rel.caso("12.%d" % ordem, "snapshot %s (%s)" % (rotulo, S.SNAPSHOT_NORMALIZATION), ok,
                 "%d pecas (corpus %s) sha256 %s" % (len(linhas), g.get("pieces"), assinatura[:16]))
    satura = hashes.get("tol_0_05") == hashes.get("tol_0_10") == hashes.get("tol_0_30")
    difere = hashes.get("flag_off") != hashes.get("tol_0_05")
    rel.caso("12.5", "0,05 = 0,10 = 0,30 e a flag desligada difere", bool(satura and difere),
             "saturado=%s | flag desligada difere=%s" % (satura, difere))
    rel.nota("saturacao NAO justifica o valor 0,05 - so' mostra que nao ha' precipicio na fronteira")


def _mapa_vereditos(ctx):
    return dict((S.node_key(ctx, i), (S.room_ok(ctx, i, False), S.room_ok(ctx, i, True)))
                for i, _n in S.tee_nodes(ctx))


def _diferencas(base, outro):
    chaves = set(base) | set(outro)
    return sorted(k for k in chaves if base.get(k) != outro.get(k))


CASOS = (
    ("01", "geometria reconstruida a partir do corpus", caso_01_geometria, False),
    ("02", "o espaco medido em cada T bate com o corpus", caso_02_espaco_medido, False),
    ("03", "os tres casos de variacao de modelagem (24, 44, 46)", caso_03_tres_casos_de_modelagem, False),
    ("04", "os controles da mesma magnitude (12, 26)", caso_04_controles, False),
    ("05", "caso e controle dividem a MESMA parede principal", caso_05_mesma_principal, False),
    ("06", "falta material continua reprovando (4 / 15 / 20 cm)", caso_06_falta_material, False),
    ("07", "quantos vereditos a secao 74 muda", caso_07_quantos_vereditos_mudam, False),
    ("08", "separacao entre modelagem e insuficiencia real", caso_08_separacao, False),
    ("09", "invariancia: translacao e inversao de pontas", caso_09_invariancia, False),
    ("10", "parede 8284580: divergencia com e sem a secao 74", caso_10_parede_8284580, True),
    ("11", "hard gates zerados nos dois estados", caso_11_hard_gates, True),
    ("12", "saturacao 0,05 / 0,10 / 0,30 no mesmo conjunto fisico", caso_12_saturacao, True),
)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Auditoria reproduzivel da SECAO 74 sobre o corpus versionado do BUTANTA R08_LT.")
    parser.add_argument("--rapido", action="store_true",
                        help="pula so' os casos 10, 11 e 12 (os que rodam o solver completo)")
    args = parser.parse_args(argv)

    inicio = time.time()
    print("SECAO 74 - auditoria reproduzivel sobre o corpus versionado do BUTANTA R08_LT")
    print("corpus : %s" % S.CORPUS_DIR)
    print("modo   : %s" % ("rapido (sem solver completo)" if args.rapido else "completo"))
    B = Bancada()
    print("status : %s (o corpus e' EVIDENCIA, nao norma)" % B.geo["status"])
    print("motor  : PIER_PHYSICAL_FIT_TOLERANCE_CM = %.2f cm | exige B54 %.1f cm por lado, B34 %.1f cm"
          % (B.tol_cm, B.b54_cm, B.b34_cm))
    print("decisao: _t_intersection_room_ok do motor - nada dela e' reimplementado aqui")

    rel = Relatorio()
    for rotulo, titulo, funcao, lento in CASOS:
        rel.secao("%s. %s" % (rotulo, titulo))
        if lento and args.rapido:
            rel.pulado(rotulo, titulo, MOTIVO_RAPIDO)
            continue
        try:
            funcao(rel, B)
        except Exception as exc:                              # noqa: BLE001 - runner de auditoria
            rel.caso("%s.!!" % rotulo, titulo, False, "excecao %s: %s" % (type(exc).__name__, exc))

    decorrido = time.time() - inicio
    print("")
    print("=" * 96)
    print("RESUMO: %d casos - %d PASS, %d FAIL, %d SKIP - %.1f s"
          % (rel.total, rel.pass_n, rel.fail_n, rel.skip_n, decorrido))
    if rel.fail_n:
        print("VEREDITO: FAIL - %d caso(s) nao reproduziram o corpus" % rel.fail_n)
    elif rel.skip_n:
        print("VEREDITO: PASS com %d caso(s) pulados - rode sem --rapido para a auditoria completa"
              % rel.skip_n)
    else:
        print("VEREDITO: PASS - todas as alegacoes da secao 74 foram reproduzidas")
    return 1 if rel.fail_n else 0


if __name__ == "__main__":
    sys.exit(main())
