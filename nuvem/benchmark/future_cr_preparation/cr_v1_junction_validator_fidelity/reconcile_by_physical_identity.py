# -*- coding: utf-8 -*-
"""RECONCILIACAO POR IDENTIDADE FISICA - CR-B (revisao independente).

DIAGNOSTICO. Nao altera nenhum arquivo de producao.

Reconcilia STATE_R -> STATE_C (gabarito) e IN_R -> IN_C (solver) SEM usar
`W0xx` e SEM usar indice ordinal de fiada. Cada achado vira uma chave em
COORDENADA DE MUNDO + ELEVACAO EM CM, e o delta e' decomposto em
identidades NOVAS / SUMIDAS / PRESERVADAS.

Alem disso mede tres coisas que a contagem por codigo esconde:

1. `JUNCTION_MISSING_BINDING` recontado por ELEVACAO FISICA (e na unidade
   estrita: cota presente em >=2 paredes do no').
2. `COVERAGE_GAP_IN_ROW` como UNIAO DE SEGMENTOS no mundo - quantos
   CENTIMETROS de vazio novo/antigo, em vez de quantos achados.
3. `POSITION_OVERLAP` pela COORDENADA DOS BLOCOS que colidem.

    export CR_B_OUT=/tmp/cr_b_candidate     # saida de build_candidate.py
    python3 reconcile_by_physical_identity.py
"""
import collections
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT)

from nuvem.benchmark import runner as bench_runner            # noqa: E402
from nuvem.benchmark import validators                        # noqa: E402
from nuvem.benchmark.validators import base                   # noqa: E402
from nuvem.benchmark.validators import validate_junctions as VJ  # noqa: E402

OUT = os.environ.get("CR_B_OUT", "/tmp/cr_b_candidate")
PROJETOS = ("torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1")
SEVERIDADE = dict((c.code, c.severity) for c in base.ERROR_CLASSES)
GAP_MIN_CM = 1.5


# ------------------------------------------------------- geometria auxiliar
def eixo(parede):
    inicio, fim = parede["start_cm"], parede["end_cm"]
    comprimento = math.hypot(fim[0] - inicio[0], fim[1] - inicio[1]) or 1.0
    return inicio, ((fim[0] - inicio[0]) / comprimento,
                    (fim[1] - inicio[1]) / comprimento)


def para_mundo(parede, t):
    inicio, direcao = eixo(parede)
    return (inicio[0] + direcao[0] * t, inicio[1] + direcao[1] * t)


def elevacao(parede, indice_fiada):
    for fiada in parede.get("rows") or []:
        if fiada["row"] == indice_fiada:
            return round(float(fiada.get("elevation_cm")), 2)
    return None


def indexar(projeto):
    return dict((w["id"], w) for w in projeto.get("walls") or [])


def chave_fisica(paredes, achado, grade=2.0):
    """Identidade fisica do achado. O ultimo elemento diz se a chave e'
    forte (coordenada real) ou fraca (so' a parede) - achado sem campo de
    coordenada NAO pode ser reconciliado e fica marcado como tal."""
    parede = paredes.get(achado.get("wall"))
    if parede is None:
        return (achado["code"], "SEM_PAREDE", "FRACA")
    z = elevacao(parede, achado["row"]) if achado.get("row") is not None else None
    za = elevacao(parede, achado.get("row_a"))
    zb = elevacao(parede, achado.get("row_b"))
    for campo in ("joint_t_cm",):
        if achado.get(campo) is not None:
            p = para_mundo(parede, achado[campo])
            return (achado["code"], round(p[0] / grade), round(p[1] / grade), z, za, zb, "FORTE")
    for campo in ("gap_t_cm", "run_t_cm"):
        if achado.get(campo):
            a, b = achado[campo]
            pa, pb = para_mundo(parede, a), para_mundo(parede, b)
            return (achado["code"], round(pa[0] / grade), round(pa[1] / grade),
                    round(pb[0] / grade), round(pb[1] / grade), z, "FORTE")
    if achado.get("point_cm"):
        p = achado["point_cm"]
        return (achado["code"], round(p[0] / grade), round(p[1] / grade), z, za, zb, "FORTE")
    if achado.get("t_cm") is not None and not isinstance(achado["t_cm"], list):
        p = para_mundo(parede, achado["t_cm"])
        return (achado["code"], round(p[0] / grade), round(p[1] / grade), z, "FORTE")
    if isinstance(achado.get("t_cm"), list) and achado["t_cm"]:
        p = para_mundo(parede, achado["t_cm"][0])
        return (achado["code"], round(p[0] / grade), round(p[1] / grade), z, "FORTE")
    meio = para_mundo(parede, (parede.get("length_cm") or 0.0) / 2.0)
    return (achado["code"], round(meio[0] / grade), round(meio[1] / grade), z, "FRACA")


# ------------------------------------------------------ reconciliacao base
def reconciliar(achados_a, paredes_a, achados_b, paredes_b):
    linhas = {}
    codigos = {f["code"] for f in achados_a} | {f["code"] for f in achados_b}
    for codigo in sorted(codigos):
        ka = collections.Counter(chave_fisica(paredes_a, f) for f in achados_a if f["code"] == codigo)
        kb = collections.Counter(chave_fisica(paredes_b, f) for f in achados_b if f["code"] == codigo)
        fraca = any(k[-1] == "FRACA" for k in list(ka) + list(kb))
        linhas[codigo] = {
            "severidade": SEVERIDADE.get(codigo),
            "antes": sum(ka.values()), "depois": sum(kb.values()),
            "delta": sum(kb.values()) - sum(ka.values()),
            "identidades_novas": sum(max(0, kb[k] - ka.get(k, 0)) for k in kb),
            "identidades_sumidas": sum(max(0, ka[k] - kb.get(k, 0)) for k in ka),
            "identidades_preservadas": sum(min(ka[k], kb.get(k, 0)) for k in ka),
            "chave": "FRACA (achado sem coordenada - nao reconciliavel)" if fraca else "fisica",
        }
    return linhas


# ------------------------------- 1) MISSING_BINDING por elevacao / estrito
def binding_por_elevacao(projeto, estrito):
    """Mesma regra do validador, mas a fiada e' a ELEVACAO.
    `estrito`: so' conta cota presente em >=2 paredes do no' - a unica
    situacao em que 'faltou amarracao' e' afirmavel."""
    faltas, avaliaveis = [], 0
    for grupo in VJ.collect_nodes(projeto):
        if grupo.get("type") not in VJ.BINDING_JUNCTION_TYPES:
            continue
        ids = sorted({w.get("id") for w, _j in grupo["walls"]})
        if len(ids) < 2:
            continue
        paredes_por_cota = collections.defaultdict(set)
        pecas_por_cota = collections.defaultdict(list)
        for parede, _j in grupo["walls"]:
            for fiada in parede.get("rows") or []:
                if not fiada.get("blocks"):
                    continue
                z = round(float(fiada["elevation_cm"]), 2)
                paredes_por_cota[z].add(parede["id"])
                pecas_por_cota[z].extend(fiada["blocks"])
        for z in sorted(paredes_por_cota):
            if estrito and len(paredes_por_cota[z]) < 2:
                continue
            avaliaveis += 1
            se_cobre = [b for b in pecas_por_cota[z]
                        if VJ.block_covers_point(b, grupo["point_cm"])]
            if not se_cobre:
                faltas.append(((round(grupo["point_cm"][0] / 5.0),
                                round(grupo["point_cm"][1] / 5.0)), z))
    return faltas, avaliaveis


# ------------------------------- 2) COVERAGE_GAP_IN_ROW como CENTIMETROS
def segmentos_de_vazio(achados, paredes):
    por_linha = collections.defaultdict(list)
    for f in achados:
        if f.get("code") != "COVERAGE_GAP_IN_ROW" or not f.get("gap_t_cm"):
            continue
        parede = paredes.get(f.get("wall"))
        if parede is None:
            continue
        z = elevacao(parede, f.get("row"))
        inicio, (ux, uy) = eixo(parede)
        if (ux, uy) < (-ux, -uy):
            ux, uy = -ux, -uy
        deslocamento = round(-inicio[0] * uy + inicio[1] * ux, 1)
        a, b = f["gap_t_cm"]
        pa, pb = para_mundo(parede, a), para_mundo(parede, b)
        ta, tb = pa[0] * ux + pa[1] * uy, pb[0] * ux + pb[1] * uy
        por_linha[(round(ux, 3), round(uy, 3), deslocamento, z)].append(
            (min(ta, tb), max(ta, tb)))
    return por_linha


def uniao(intervalos):
    saida = []
    for a, b in sorted(intervalos):
        if saida and a <= saida[-1][1] + 0.01:
            saida[-1][1] = max(saida[-1][1], b)
        else:
            saida.append([a, b])
    return saida


def comprimento(u):
    return sum(b - a for a, b in u)


def subtrair(u, v):
    saida = []
    for a, b in u:
        atual = a
        for c, d in v:
            if d <= atual or c >= b:
                continue
            if c > atual:
                saida.append((atual, min(c, b)))
            atual = max(atual, d)
            if atual >= b:
                break
        if atual < b:
            saida.append((atual, b))
    return [x for x in saida if x[1] - x[0] > 0.01]


def vazio_em_cm(achados_a, paredes_a, achados_b, paredes_b):
    A = segmentos_de_vazio(achados_a, paredes_a)
    B = segmentos_de_vazio(achados_b, paredes_b)
    so_a = so_b = ambos = 0.0
    for k in set(A) | set(B):
        ua, ub = uniao(A.get(k, [])), uniao(B.get(k, []))
        so_a += comprimento(subtrair(ua, ub))
        so_b += comprimento(subtrair(ub, ua))
        ambos += comprimento(ua) - comprimento(subtrair(ua, ub))
    return {"cm_so_antes": round(so_a, 1), "cm_so_depois_NOVO": round(so_b, 1),
            "cm_nos_dois": round(ambos, 1)}


# ------------------------------- 3) POSITION_OVERLAP pela coordenada real
def colisoes(achados, projeto):
    blocos = dict((b["id"], b)
                  for w in projeto.get("walls") or []
                  for r in w.get("rows") or []
                  for b in r.get("blocks") or [])
    chaves = collections.Counter()
    for f in achados:
        if f.get("code") != "POSITION_OVERLAP":
            continue
        pontos = []
        for ident in f.get("blocks") or []:
            b = blocos.get(ident)
            if b:
                pontos.append((round(b["center_cm"][0], 1), round(b["center_cm"][1], 1),
                               round(float(b["z_cm"]), 1), b.get("code")))
        chaves[tuple(sorted(pontos))] += 1
    return chaves


# ---------------------------------------------------------------- amarracao
def falha_vertical_nos_nos(projeto):
    """Faixa de altura, no eixo vertical do no', sem NENHUMA peca cobrindo
    o ponto. Imune a indice ordinal E a meia-fiada."""
    saida = {}
    for grupo in VJ.collect_nodes(projeto):
        if grupo.get("type") not in VJ.BINDING_JUNCTION_TYPES:
            continue
        ids = sorted({w.get("id") for w, _j in grupo["walls"]})
        if len(ids) < 2:
            continue
        trechos, z0, z1 = [], None, None
        for parede, _j in grupo["walls"]:
            for fiada in parede.get("rows") or []:
                for peca in fiada.get("blocks") or []:
                    a = float(peca["z_cm"]); b = a + float(peca.get("height_cm") or 19.0)
                    z0 = a if z0 is None else min(z0, a)
                    z1 = b if z1 is None else max(z1, b)
                    if VJ.block_covers_point(peca, grupo["point_cm"]):
                        trechos.append((a, b))
        if z0 is None:
            continue
        buracos, atual = [], z0
        for a, b in sorted(trechos):
            if a - atual > GAP_MIN_CM:
                buracos.append((round(atual, 1), round(a, 1)))
            atual = max(atual, b)
        if z1 - atual > GAP_MIN_CM:
            buracos.append((round(atual, 1), round(z1, 1)))
        saida[(round(grupo["point_cm"][0] / 5.0), round(grupo["point_cm"][1] / 5.0))] = {
            "ponto": [round(v, 2) for v in grupo["point_cm"]], "tipo": grupo.get("type"),
            "paredes": ids, "faixas_sem_amarracao": buracos,
            "cm_sem_amarracao": round(sum(b - a for a, b in buracos), 1)}
    return saida


# ------------------------------------------------------------------- driver
def main():
    relatorio = {}
    for projeto_id in PROJETOS:
        pasta = os.path.join(OUT, projeto_id)
        if not os.path.exists(os.path.join(pasta, "reference_candidate.json")):
            print("FALTA %s - rode build_candidate.py primeiro" % pasta)
            return 2
        ref_r = json.load(open(os.path.join(pasta, "reference_roundtrip.json"), encoding="utf-8"))
        ref_c = json.load(open(os.path.join(pasta, "reference_candidate.json"), encoding="utf-8"))

        print("=" * 96)
        print(projeto_id)

        # --- gabarito (validadores sobre a alvenaria humana)
        fa, _e = validators.run_all(ref_r, {})
        fb, _e = validators.run_all(ref_c, {})
        gab = reconciliar(fa, indexar(ref_r), fb, indexar(ref_c))
        print("-- GABARITO  STATE_R -> STATE_C   (identidade fisica)")
        print("   %-34s %-9s %6s %6s %7s %7s %7s" %
              ("codigo", "sever.", "R", "C", "delta", "novas", "sumidas"))
        for codigo, v in gab.items():
            print("   %-34s %-9s %6d %6d %+7d %7d %7d %s" %
                  (codigo, v["severidade"], v["antes"], v["depois"], v["delta"],
                   v["identidades_novas"], v["identidades_sumidas"],
                   "" if v["chave"] == "fisica" else "<- chave fraca"))

        # --- amarracao nas tres unidades
        f_ord_r = sum(1 for f in fa if f["code"] == "JUNCTION_MISSING_BINDING")
        f_ord_c = sum(1 for f in fb if f["code"] == "JUNCTION_MISSING_BINDING")
        el_r, _n = binding_por_elevacao(ref_r, False)
        el_c, _n = binding_por_elevacao(ref_c, False)
        es_r, av_r = binding_por_elevacao(ref_r, True)
        es_c, av_c = binding_por_elevacao(ref_c, True)
        novos_estritos = sorted(collections.Counter(es_c) - collections.Counter(es_r))
        nos_r = {(round(g["point_cm"][0] / 5.0), round(g["point_cm"][1] / 5.0))
                 for g in VJ.collect_nodes(ref_r)}
        print("-- JUNCTION_MISSING_BINDING nas TRES unidades de avaliacao")
        print("   por INDICE ORDINAL de fiada (validador de hoje): R=%d C=%d  (%+d)"
              % (f_ord_r, f_ord_c, f_ord_c - f_ord_r))
        print("   por ELEVACAO FISICA:                             R=%d C=%d  (%+d)"
              % (len(el_r), len(el_c), len(el_c) - len(el_r)))
        print("   ESTRITA (cota em >=2 paredes do no'):            R=%d C=%d  (%+d)"
              % (len(es_r), len(es_c), len(es_c) - len(es_r)))
        print("      identidades estritas NOVAS: %d   SUMIDAS: %d"
              % (len(novos_estritos),
                 len(sorted(collections.Counter(es_r) - collections.Counter(es_c)))))
        print("      dessas NOVAS, em no' que NAO existia em STATE_R: %d"
              % sum(1 for k in novos_estritos if k[0] not in nos_r))

        # --- falha vertical (o teste mais fisico)
        vr, vc = falha_vertical_nos_nos(ref_r), falha_vertical_nos_nos(ref_c)
        comuns = set(vr) & set(vc)
        piorou = [k for k in comuns if vc[k]["cm_sem_amarracao"] > vr[k]["cm_sem_amarracao"] + 0.01]
        melhorou = [k for k in comuns if vc[k]["cm_sem_amarracao"] < vr[k]["cm_sem_amarracao"] - 0.01]
        print("-- FALHA VERTICAL DE AMARRACAO no eixo do no' (todas as pecas do no')")
        print("   nos avaliaveis: R=%d C=%d | nos NOVOS=%d SUMIDOS=%d"
              % (len(vr), len(vc), len(set(vc) - set(vr)), len(set(vr) - set(vc))))
        print("   nos presentes NOS DOIS que PIORARAM:   %d   <- so' isto seria defeito novo"
              % len(piorou))
        print("   nos presentes NOS DOIS que MELHORARAM: %d" % len(melhorou))

        entrada = {"gabarito": gab,
                   "missing_binding_unidades": {
                       "ordinal": {"R": f_ord_r, "C": f_ord_c, "delta": f_ord_c - f_ord_r},
                       "elevacao": {"R": len(el_r), "C": len(el_c), "delta": len(el_c) - len(el_r)},
                       "estrita": {"R": len(es_r), "C": len(es_c), "delta": len(es_c) - len(es_r),
                                   "novas_em_no_novo": sum(1 for k in novos_estritos if k[0] not in nos_r),
                                   "novas_total": len(novos_estritos)}},
                   "falha_vertical": {"nos_R": len(vr), "nos_C": len(vc),
                                      "nos_que_pioraram": len(piorou),
                                      "nos_que_melhoraram": len(melhorou),
                                      "nos_novos": len(set(vc) - set(vr))}}

        # --- solver (so' se as saidas existirem)
        sol_r = os.path.join(pasta, "solver_roundtrip.json")
        sol_c = os.path.join(pasta, "solver_candidate.json")
        if os.path.exists(sol_r) and os.path.exists(sol_c):
            sr = json.load(open(sol_r, encoding="utf-8"))
            sc = json.load(open(sol_c, encoding="utf-8"))
            gr, _s, _c = bench_runner.evaluate_project(sr, ref_r)
            gc, _s, _c = bench_runner.evaluate_project(sc, ref_c)
            solver = reconciliar(gr, indexar(sr), gc, indexar(sc))
            print("-- SOLVER  IN_R x STATE_R -> IN_C x STATE_C   (identidade fisica)")
            for codigo, v in solver.items():
                print("   %-34s %-9s %6d %6d %+7d %7d %7d %s" %
                      (codigo, v["severidade"], v["antes"], v["depois"], v["delta"],
                       v["identidades_novas"], v["identidades_sumidas"],
                       "" if v["chave"] == "fisica" else "<- chave fraca"))
            cm = vazio_em_cm(gr, indexar(sr), gc, indexar(sc))
            print("   COVERAGE_GAP_IN_ROW em CENTIMETROS: %s" % cm)
            ca, cb = colisoes(gr, sr), colisoes(gc, sc)
            print("   POSITION_OVERLAP pela coordenada dos blocos: R=%d C=%d "
                  "novas=%d sumidas=%d preservadas=%d"
                  % (sum(ca.values()), sum(cb.values()),
                     sum(max(0, cb[k] - ca.get(k, 0)) for k in cb),
                     sum(max(0, ca[k] - cb.get(k, 0)) for k in ca),
                     sum(min(ca[k], cb.get(k, 0)) for k in ca)))
            entrada["solver"] = solver
            entrada["solver_vazio_cm"] = cm
            entrada["solver_colisoes"] = {
                "R": sum(ca.values()), "C": sum(cb.values()),
                "novas": sum(max(0, cb[k] - ca.get(k, 0)) for k in cb),
                "sumidas": sum(max(0, ca[k] - cb.get(k, 0)) for k in ca)}
        else:
            print("-- SOLVER: saidas ausentes (rode repro_solver_l_node_alternation.py "
                  "ou project_solver.py). Secao do solver pulada.")

        relatorio[projeto_id] = entrada

    destino = os.path.join(HERE, "evidence", "reconciliation_physical_identity.json")
    with open(destino, "w", encoding="utf-8") as fh:
        json.dump(relatorio, fh, ensure_ascii=False, indent=1, sort_keys=True, default=str)
    print()
    print("escrito:", destino)
    return 0


if __name__ == "__main__":
    sys.exit(main())
