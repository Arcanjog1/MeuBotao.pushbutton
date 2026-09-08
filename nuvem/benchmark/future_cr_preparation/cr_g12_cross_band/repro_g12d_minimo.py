# -*- coding: utf-8 -*-
"""REPRODUCER MINIMO DA CR-G12 - 3 paredes REAIS do `input.json` OFICIAL.

E' a quarta tentativa de reducao, e a PRIMEIRA que reproduz. As tres
anteriores (`repro_g12.py`, `repro_g12b.py`, `repro_g12c.py`) e mais duas
varreduras parametricas desta CR (`sweep2_janela.py`,
`sweep3_no_de_meio.py`, ~4.900 combinacoes) falharam porque montavam uma
planta SINTETICA: numa planta pequena inventada o solver simplesmente nao
produz junta continua nenhuma.

Esta reducao e' de outra natureza - delta-debugging (`reduzir.py`) sobre a
planta REAL: parte das 167 paredes do `torre_easy_lo_r00_tgd` e vai
removendo parede enquanto a IDENTIDADE FISICA alvo continuar sendo
acusada. Sobraram TRES:

    indice 55  -> W001 no subplano: eixo de  79,01cm, sem abertura
    indice 82  -> W002 no subplano: eixo de 269,01cm, porta t=19,00..110,00 (verga 221)
    indice 124 -> W003 no subplano: eixo de 169,00cm, JANELA t=83,73..134,76
                                    (peitoril 150, verga 231)  <- parede alvo

Nenhuma coordenada e' inventada: geometria, espessura, cotas, aberturas e
parametros vem do arquivo oficial, intocado.

O que o subplano preserva (e por isso reproduz):

  * as bandas ABAIXO, DENTRO e ACIMA da abertura - [0..6], [7..10], [11],
    [12..16] - inclusive a banda de UMA FIADA SO' (a 11), que e' onde o
    peitoril da janela atravessa a fiada;
  * o estado das fiadas vizinhas da fronteira (z=121 e z=141);
  * as pecas de amarracao e as reservas de no': o L_CORNER na ponta e,
    decisivo, o B54 de `T_INTERSECTION_MIDSPAN` em t=40..94 da fiada z=121;
  * o recorte e o reparo posteriores da abertura (`OPENING_REPAIR_FILL`).

MECANISMO, visivel na saida:

    z=121 (banda 2)  ... C09(30..39) | B54(40..94, T_INTERSECTION_MIDSPAN)
    z=141 (banda 3)  ... C04(35..39) | C09(40..49)          <- PRE-FIX

  A junta de z=121 em t=39,5 e' a BORDA DA PECA DE AMARRACAO: ela nao
  depende de layout nenhum e o preenchimento nao tem como move-la. Quem
  tinha de sair da frente era a fiada de cima - mas ela esta' em OUTRA
  banda, resolvida do zero, e a regra #1 nunca foi avaliada ali.
  Desencontro medido: 0,00cm.

    z=141 (banda 3)  ... C09(35..44) | C04(45..49) | C09(50..59)  <- POS-FIX

  Com a correcao a fiada de cima escolhe outra composicao do MESMO trecho
  (mesmas pecas, ordem diferente): juntas em 44,5 e 49,5. Nenhuma peca de
  amarracao foi movida, nenhuma abertura foi tocada.

    python3 nuvem/benchmark/future_cr_preparation/cr_g12_cross_band/repro_g12d_minimo.py <raiz do repo>
"""

import copy
import json
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
sys.path.insert(0, ROOT)

from nuvem.benchmark import solver_bridge, validators, model  # noqa: E402
from nuvem.benchmark.extract import from_solver  # noqa: E402

ENGINE = solver_bridge.engine()
PROJETO = "torre_easy_lo_r00_tgd"
INDICES = [55, 82, 124]
ALVO_PONTO = (-401.5, 309.5)
ALVO_COTAS = (121.0, 141.0)


def subplano():
    base = json.load(open(os.path.join(
        ROOT, "nuvem/benchmark/projects", PROJETO, "input.json"), encoding="utf-8"))
    projeto = copy.deepcopy(base)
    projeto["walls"] = [base["walls"][i] for i in INDICES]
    return model.assign_ids(projeto)


def resolve(projeto, propagacao):
    ENGINE.CROSS_BAND_JOINT_PROPAGATION_ENABLED = propagacao
    res, walls, nodes, ops, cat, base_z, num_courses, _notes = solver_bridge.run_solver(projeto)
    saida = from_solver.project_from_solver(
        "repro_g12d", res, walls, nodes, ops, cat, base_z, num_courses)
    findings, _erros = validators.run_all(saida, {})
    altura, _e = ENGINE._course_height_ft(cat, None)
    bloco = altura - ENGINE._cm_to_ft(ENGINE.COURSE_JOINT_CM)
    grupos = ENGINE._group_course_indices_by_opening_band(
        ops, base_z, altura, bloco, num_courses)
    banda = dict((ci, i) for i, (cis, _f) in enumerate(grupos) for ci in cis)
    return saida, findings, grupos, banda


def continuas(saida, findings, banda):
    achados = []
    for wall in saida["walls"]:
        ordem = dict((r["row"], i) for i, r in enumerate(
            sorted(wall["rows"], key=lambda r: r["elevation_cm"])))
        cota = dict((r["row"], r["elevation_cm"]) for r in wall["rows"])
        direcao, _len = model.direction_of(wall["start_cm"], wall["end_cm"])
        for f in findings:
            if f["code"] != "PRISM_CONTINUOUS_JOINT" or f["wall"] != wall["id"]:
                continue
            t = f["joint_t_cm"]
            ponto = (round(wall["start_cm"][0] + direcao[0] * t, 1),
                     round(wall["start_cm"][1] + direcao[1] * t, 1))
            achados.append({
                "ponto": ponto,
                "cotas": tuple(sorted((round(cota[f["row_a"]], 1), round(cota[f["row_b"]], 1)))),
                "t_cm": round(t, 2), "desencontro_cm": f["stagger_cm"],
                "cross_band": banda.get(ordem[f["row_a"]]) != banda.get(ordem[f["row_b"]]),
            })
    return achados


def main():
    projeto = subplano()
    print("subplano: %d paredes reais do %s (indices %s)"
          % (len(projeto["walls"]), PROJETO, INDICES))
    for wall in projeto["walls"]:
        _d, comprimento = model.direction_of(wall["start_cm"], wall["end_cm"])
        print("   %s  %.2fcm  aberturas=%s" % (
            wall["id"], comprimento,
            [(round(o["t_start_cm"], 2), round(o["t_end_cm"], 2),
              round(o["sill_cm"], 1), round(o["head_cm"], 1)) for o in (wall.get("openings") or [])]))

    resultado = {}
    for propagacao in (False, True):
        saida, findings, grupos, banda = resolve(projeto, propagacao)
        achados = continuas(saida, findings, banda)
        resultado[propagacao] = achados
        print("\n### CROSS_BAND_JOINT_PROPAGATION_ENABLED = %s  | bandas: %s"
              % (propagacao, [g[0] for g in grupos]))
        for a in achados:
            print("    junta ponto=%s cotas=%s t=%.2f desencontro=%.2fcm cross_band=%s"
                  % (a["ponto"], a["cotas"], a["t_cm"], a["desencontro_cm"], a["cross_band"]))
        if not achados:
            print("    (nenhuma junta continua)")

    def tem_alvo(achados):
        return any(a["ponto"] == ALVO_PONTO and a["cotas"] == ALVO_COTAS and a["cross_band"]
                   for a in achados)

    print("\n>>> identidade alvo %s %s: PRE-FIX=%s  POS-FIX=%s"
          % (ALVO_PONTO, ALVO_COTAS, tem_alvo(resultado[False]), tem_alvo(resultado[True])))
    if tem_alvo(resultado[False]) and not tem_alvo(resultado[True]) and not resultado[True]:
        print(">>> REPRODUZ o mecanismo cross-band e a correcao o elimina.")
        return 0
    print(">>> NAO reproduziu o esperado - investigar antes de mexer no teste.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
