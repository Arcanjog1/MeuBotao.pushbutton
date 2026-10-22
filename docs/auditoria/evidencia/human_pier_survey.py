# -*- coding: utf-8 -*-
"""Levantamento do padrao HUMANO de pilarete/vao no BUTANTA R08_LT.

AUDITORIA / EVIDENCIA — nao normativo, nao altera nada no motor.

Le SOMENTE dados ja versionados no repositorio:
  docs/revit_reference_extraction/butanta-r08-lt/08_piece_opening_wall_relations.json
  docs/revit_reference_extraction/butanta-r08-lt/01_family_catalog.json

Diferenca em relacao a bancada do PR #42: aquela depende de
`target_1pav.clean.json` / `human_1pav.clean.json`, que NAO estao no Git.
Este script e' reproduzivel a partir do repositorio sozinho.

Escopo e limite (ler antes de citar qualquer numero):
- o 08 cobre 3.625 pecas RELACIONADAS A ABERTURA (142 vaos, todos os
  pavimentos), nao o modelo inteiro de 65.747 pecas;
- portanto serve para pilarete/jamba/acima/abaixo de vao, e NAO serve para
  meio de parede longe de abertura nem para amarracao L/T/X;
- pecas clonadas entre pavimentos estao incluidas (ver REVIEW_2026-09-10.md);
- nao ha' campo de espelhamento no 08, entao a orientacao do vazado menor
  do B34 NAO e' reconstruivel com confianca por aqui.

Uso: python3 docs/auditoria/evidencia/human_pier_survey.py
"""
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC = os.path.join(REPO, "docs", "revit_reference_extraction", "butanta-r08-lt",
                   "08_piece_opening_wall_relations.json")

CODE = {
    "BLOCO INTEIRO - 14x19x39": "B39", "BLOCO 34 - 14x19x34": "B34",
    "MEIO BLOCO - 14x19x19": "B19", "BLOCO 54 - 14x19x54": "B54",
    "PASTILHA - 14x19X4": "C04", "COMPENSADOR 14x19x9": "C09",
    "COMPENSADOR 14x19x9 (deitado)": "C09D",
    "COMPENSADOR CORTADO 14x19x9 (deitado)": "C09DH",
    "CANALETA INTEIRA - 14x19x39": "K39", "CANALETA 34 - 14x19x34": "K34",
    "MEIA CANALETA - 14x19x19": "K19", "CANALETA J - 14x9-19x19": "KJ",
    "MEIO BLOCO CORTADO - 14x9x19": "B19H",
    "BLOCO CANALETA CORTADO - 14x19xVAR": "KVH",
    "PASTILHA CORTADA- 14x9X4": "C04H",
}
# "especial" = compensador/pastilha VERTICAL (a peca de acerto da regra #2).
# O compensador DEITADO (C09D) e' outro mecanismo: fiada de meia altura sobre
# vao pequeno. Contado separado de proposito.
SPECIAL = {"C04", "C09", "C04H"}
JOINT = 1.0


def load():
    d = json.load(open(SRC, encoding="utf-8"))
    for r in d["relations"]:
        r["c"] = CODE.get(r["family_name"], r["family_name"][:6])
        ax = "Y" if "|ax=Y" in r["wall_physical_key"] else "X"
        r["s"] = r["y_cm"] if ax == "Y" else r["x_cm"]
    return d["relations"]


def contiguous_runs(recs, position=None):
    """Corridas de pecas EFETIVAMENTE encostadas (junta <= 1,6 cm).

    Sem isto, agrupar por (parede, fiada, vao) junta os dois lados do vao e
    produz sequencias falsas como "B39+C04+C04+B39" (dois pilaretes opostos
    lidos como um so').
    """
    grp = collections.defaultdict(list)
    for i, r in enumerate(recs):
        if position and r["relative_position_to_opening"] != position:
            continue
        grp[(r["wall_physical_key"], r["level"], round(r["z_rel_cm"], 1),
             r["opening_id"], r["relative_position_to_opening"])].append(i)
    runs = []
    for key, idx in grp.items():
        idx.sort(key=lambda i: recs[i]["s"])
        cur = [idx[0]]
        for prev, i in zip(idx, idx[1:]):
            gap = ((recs[i]["s"] - recs[i]["piece_length_cm"] / 2.0)
                   - (recs[prev]["s"] + recs[prev]["piece_length_cm"] / 2.0))
            if -0.3 <= gap <= 1.6 * JOINT:
                cur.append(i)
            else:
                runs.append((key, cur))
                cur = [i]
        runs.append((key, cur))
    return runs


def span_of(recs, run):
    a, b = recs[run[0]], recs[run[-1]]
    return round((b["s"] + b["piece_length_cm"] / 2.0)
                 - (a["s"] - a["piece_length_cm"] / 2.0), 1)


def opening_centers(recs):
    tmp = collections.defaultdict(list)
    for r in recs:
        if r["relative_position_to_opening"] in ("ABOVE_OPENING_FIRST_COURSE",
                                                 "BELOW_SILL_FIRST_COURSE"):
            tmp[r["opening_id"]].append(r["s"])
    return dict((k, sum(v) / len(v)) for k, v in tmp.items())


def main():
    recs = load()
    runs = contiguous_runs(recs)
    jamb = [(k, c) for k, c in runs if k[4] == "JAMB"]

    print("H1. DENSIDADE DE ESPECIAIS POR CORRIDA CONTIGUA DE PILARETE")
    dist = collections.Counter(
        sum(1 for i in c if recs[i]["c"] in SPECIAL) for k, c in jamb)
    for n, q in sorted(dist.items()):
        print("     %d especial(is): %4d corridas" % (n, q))
    ge2 = sum(q for n, q in dist.items() if n >= 2)
    print("     corridas com >=2 especiais: %d de %d" % (ge2, len(jamb)))

    print("\nH2. PARES ENCOSTADOS ESPECIAL+ESPECIAL (qualquer posicao)")
    pairs = collections.Counter()
    for k, c in runs:
        for a, b in zip(c, c[1:]):
            if recs[a]["c"] in SPECIAL and recs[b]["c"] in SPECIAL:
                pairs[(recs[a]["c"], recs[b]["c"])] += 1
    print("     %s   (total %d em %d corridas)"
          % (dict(pairs) or "NENHUM", sum(pairs.values()), len(runs)))

    print("\nH3. POSICAO DO ESPECIAL DENTRO DO PILARETE")
    oc = opening_centers(recs)
    where = collections.Counter()
    for k, c in jamb:
        if len(c) < 2 or k[3] not in oc:
            continue
        end = "last" if abs(recs[c[-1]]["s"] - oc[k[3]]) < abs(recs[c[0]]["s"] - oc[k[3]]) else "first"
        for pos, i in enumerate(c):
            if recs[i]["c"] not in SPECIAL:
                continue
            if (pos == len(c) - 1 and end == "last") or (pos == 0 and end == "first"):
                where[(recs[i]["c"], "JUNTO_AO_VAO")] += 1
            elif (pos == 0 and end == "last") or (pos == len(c) - 1 and end == "first"):
                where[(recs[i]["c"], "PONTA_OPOSTA")] += 1
            else:
                where[(recs[i]["c"], "MEIO_DO_PILARETE")] += 1
    for k, v in where.most_common():
        print("     %-5s %-18s %4d" % (k[0], k[1], v))

    print("\nH4. DOMINANCIA POR VAO OCUPADO (corridas de pilarete)")
    by_span = collections.defaultdict(collections.Counter)
    for k, c in jamb:
        by_span[span_of(recs, c)]["+".join(recs[i]["c"] for i in c)] += 1
    for sp in sorted(by_span):
        tot = sum(by_span[sp].values())
        if tot < 3:
            continue
        opts = by_span[sp].most_common()
        print("     vao %5.1f cm (n=%d): %s" % (
            sp, tot, "  |  ".join("%s %d (%.0f%%)" % (s, n, 100.0 * n / tot)
                                  for s, n in opts)))

    print("\nH5. COMPOSICAO POR POSICAO RELATIVA AO VAO")
    cols = ["K39", "K34", "K19", "KJ", "C09D", "B39", "B34", "B54", "B19", "C09", "C04"]
    print("     %-30s %s  TOTAL" % ("", " ".join("%5s" % c for c in cols)))
    for p in ["ABOVE_OPENING_FIRST_COURSE", "ABOVE_OPENING_SECOND_COURSE",
              "BELOW_SILL_FIRST_COURSE", "BELOW_SILL_SECOND_COURSE", "JAMB"]:
        cc = collections.Counter(r["c"] for r in recs
                                 if r["relative_position_to_opening"] == p)
        print("     %-30s %s  %5d" % (
            p, " ".join("%5d" % cc.get(c, 0) for c in cols), sum(cc.values())))


if __name__ == "__main__":
    main()
