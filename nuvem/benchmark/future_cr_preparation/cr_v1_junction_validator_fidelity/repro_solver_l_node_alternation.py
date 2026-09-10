# -*- coding: utf-8 -*-
"""REPRODUTOR - o solver DEIXA DE ALTERNAR a amarracao no unico no' que
muda de T (parede atravessando) para L (parede TERMINANDO) e recebe as duas
paredes com peca de amarracao.

DIAGNOSTICO. Nao altera producao, nao corrige nada, nao toca regra de
amarracao.

O NO'
-----
    TGD  (338.52 ; 187.05)      TP1  (8017.26 ; 1289.95)
    (o mesmo ponto fisico dos dois niveis: + [7678.7371 ; 1102.9024])

    IN_R  a parede N-S ATRAVESSA y=187.05  -> no' T
    IN_C  a parede N-S COMECA em y=180.05  -> no' L

O QUE FOI MEDIDO (todas as pecas do projeto que alcancam o ponto, sem
depender de qual parede DECLARA a juncao):

    alvenaria HUMANA  STATE_R   13 fiadas, 2 donos alternando   ALTERNA
    alvenaria HUMANA  STATE_C   13 fiadas, 2 donos alternando   ALTERNA
    solver sobre IN_R           17 fiadas, 2 donos alternando   ALTERNA
    solver sobre IN_C           17 fiadas, 1 dono em TODAS      NAO ALTERNA

Ou seja: a pessoa amarra certo nas duas topologias; o solver amarra certo
na topologia antiga e para de amarrar na nova. E' defeito REAL do solver,
exposto pela mudanca T->L - nao e' artefato do validador nem do gabarito.

Os +16 `JUNCTION_NOT_ALTERNATING` da projecao sao ESTE UNICO NO',
contado uma vez por par de fiadas consecutivas (17 fiadas = 16 pares).

COMO RODAR
----------
Precisa das saidas do solver sobre `input_roundtrip.json` e
`input_candidate.json` (evidencia da CR-B):

    export CR_B_OUT=/tmp/cr_b_candidate
    cd ../bench_opening_reconstruction_b_candidate
    python3 build_candidate.py
    cd -
    python3 repro_solver_l_node_alternation.py        # roda o solver se faltar
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT)

from nuvem.benchmark.validators import validate_junctions as VJ  # noqa: E402

OUT = os.environ.get("CR_B_OUT", "/tmp/cr_b_candidate")
NOS = {"torre_easy_lo_r00_tgd": [338.52, 187.05],
       "torre_easy_lo_r00_tp1": [8017.26, 1289.95]}


def solver_out(projeto, tag):
    """Saida do solver de PRODUCAO sobre `input_<tag>.json`. Gera se faltar."""
    destino = os.path.join(OUT, projeto, "solver_%s.json" % tag)
    if os.path.exists(destino):
        return json.load(open(destino, encoding="utf-8"))
    from nuvem.benchmark import solver_bridge
    from nuvem.benchmark.extract import from_solver
    entrada = json.load(open(os.path.join(OUT, projeto, "input_%s.json" % tag),
                             encoding="utf-8"))
    r = solver_bridge.run_solver(entrada)
    resultado = from_solver.project_from_solver(
        projeto, r[0], r[1], r[2], r[3], r[4], r[5], r[6],
        metadata={"from_input": "repro CR-B reconciliacao"})
    json.dump(resultado, open(destino, "w", encoding="utf-8"),
              ensure_ascii=False, sort_keys=True, indent=1)
    return resultado


def ocupacao(projeto, ponto):
    """cota -> [(parede, codigo)] de TODA peca do projeto que alcanca o ponto.
    Nao usa `collect_nodes`: o veredito nao pode depender de qual parede
    declarou a juncao."""
    por_cota = {}
    for parede in projeto.get("walls") or []:
        for fiada in parede.get("rows") or []:
            for peca in fiada.get("blocks") or []:
                if VJ.block_covers_point(peca, ponto):
                    por_cota.setdefault(round(float(peca["z_cm"]), 1), []).append(
                        (peca.get("wall_id"), peca.get("code")))
    return por_cota


def relatar(rotulo, projeto, ponto):
    por_cota = ocupacao(projeto, ponto)
    donos = {tuple(sorted({w for w, _c in por_cota[z]})) for z in por_cota}
    alterna = len(donos) > 1
    print("  %-22s fiadas=%-3d donos_distintos=%-2d  %s"
          % (rotulo, len(por_cota), len(donos),
             "ALTERNA" if alterna else "NAO ALTERNA  <<<"))
    for z in sorted(por_cota)[:6]:
        print("        z=%-7s %s" % (z, sorted(por_cota[z])))
    return alterna


def main():
    print(__doc__.split("\n\n")[0])
    falhas = []
    for projeto_id, ponto in NOS.items():
        print()
        print("=" * 78)
        print("%s   no' fisico %s" % (projeto_id, ponto))
        base = os.path.join(OUT, projeto_id)
        if not os.path.exists(os.path.join(base, "input_candidate.json")):
            print("  FALTA %s - rode build_candidate.py primeiro" % base)
            return 2
        estados = [
            ("gabarito IN_R", json.load(open(os.path.join(base, "reference_roundtrip.json"), encoding="utf-8"))),
            ("gabarito IN_C", json.load(open(os.path.join(base, "reference_candidate.json"), encoding="utf-8"))),
            ("solver IN_R", solver_out(projeto_id, "roundtrip")),
            ("solver IN_C", solver_out(projeto_id, "candidate")),
        ]
        resultado = {}
        for rotulo, projeto in estados:
            resultado[rotulo] = relatar(rotulo, projeto, ponto)
        if resultado["gabarito IN_C"] and not resultado["solver IN_C"]:
            falhas.append(projeto_id)
            print("  >>> REGRESSAO CONFIRMADA: a pessoa alterna, o solver nao.")
        if resultado["solver IN_R"] and not resultado["solver IN_C"]:
            print("  >>> e o solver ALTERNAVA neste mesmo no' com a entrada antiga.")
    print()
    print("=" * 78)
    print("projetos com a regressao reproduzida: %d de %d" % (len(falhas), len(NOS)))
    return 0 if len(falhas) == len(NOS) else 1


if __name__ == "__main__":
    sys.exit(main())
