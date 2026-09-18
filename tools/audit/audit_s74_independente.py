# -*- coding: utf-8 -*-
"""Auditoria INDEPENDENTE do corpus da secao 74 — Conta 2.

Nao importa `tools/audit/s74_corpus.py` nem o motor. Le' os JSON crus e
reconfere tudo o que pode ser reconferido com aritmetica 2D pura.

O que isto acrescenta ao auditor oficial: a ANCORA EXTERNA de `room_min`.
O README do corpus declara, com todas as letras, que a MEDICAO e' circular
(os campos `room_*` foram produzidos chamando o proprio motor) e que
"quem quiser fechar o circulo por completo precisa ancorar `room_min` de
pelo menos um no' contra uma medicao independente do motor".

E' o que a secao [ANCORA] faz: projeta cada abertura no eixo da parede
principal, acha a borda mais proxima do no' em cada sentido e compara com
`room_plus_cm`/`room_minus_cm` gravados — sem motor, sem
`extend_wall_ends_to_junctions`, sem `tools/audit/s74_corpus.py`.

    python3 tools/audit/audit_s74_independente.py [--corpus <dir>]

Sai 0 se tudo confere, 1 caso contrario.
"""
import json
import math
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
PADRAO = os.path.join(os.path.dirname(os.path.dirname(AQUI)),
                      "reference_projects", "butanta_r08_lt", "s74_corpus")

B54_HALF_CM = 27.0          # metade do B54, redigitada da fisica do bloco
B34_CM = 34.0
TOL_CM = 0.05
FRONTEIRA = (24, 26, 44, 46, 12)          # 3 casos + 2 controles
MATERIAIS = (19, 20, 39, 30, 18, 28, 22)  # as 7 faltas reais

FALHAS = []


def ck(nome, cond, det=""):
    print(("  OK   " if cond else "  FAIL ") + nome + ("" if cond else "   " + str(det)))
    if not cond:
        FALHAS.append(nome)


def _eixo(w):
    (ax, ay), (bx, by) = w["p0_cm"], w["p1_cm"]
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    return (ax, ay), (dx / L, dy / L), L


def _proj(w, p):
    """(t ao longo do eixo, distancia perpendicular, comprimento)."""
    (ax, ay), (ux, uy), L = _eixo(w)
    t = (p[0] - ax) * ux + (p[1] - ay) * uy
    return t, math.hypot(p[0] - (ax + t * ux), p[1] - (ay + t * uy)), L


def carregar(base):
    n = {}
    for k in ("geometry", "t_nodes", "wall_8284580", "snapshot_v1"):
        with open(os.path.join(base, k + ".json")) as fh:
            n[k] = json.load(fh)
    return n


def estrutura(G, T, W, S):
    print("[ESTRUTURA] geometry.json e' INPUT, nao resultado")
    ck("34 paredes", len(G["walls"]) == 34, len(G["walls"]))
    ck("44 aberturas", len(G["openings"]) == 44, len(G["openings"]))
    ck("espessura 14 cm em todas", set(w["thickness_cm"] for w in G["walls"]) == {14.0})
    ck("chaves W01..W34", [w["key"] for w in G["walls"]] == ["W%02d" % i for i in range(1, 35)])
    ordem = [w["provenance"]["input_order"] for w in G["walls"]]
    ck("input_order preservado", ordem == list(range(len(ordem))))
    ck("input_order declarado como parte do input",
       "input_order_is_part_of_the_input" in G["provenance"])

    todas = []
    for w in G["walls"]:
        todas += list(w["p0_cm"]) + list(w["p1_cm"]) + [w["length_cm"]]
    frac = sum(1 for v in todas if abs(v - round(v)) > 1e-9)
    ck("sem arredondamento destrutivo (%d de %d valores nao-inteiros)" % (frac, len(todas)),
       frac > 0)

    orfas = []
    for o in G["openings"]:
        d = min(_proj(w, o["center_cm"])[1] for w in G["walls"])
        if d > 14.0:
            orfas.append(o["key"])
    ck("0 aberturas orfas", not orfas, orfas[:3])

    cru = json.dumps(G).lower()
    proibidos = [p for p in ("room_ok", "expected", "shortfall", "divergen", "veredito")
                 if p in cru]
    ck("geometry.json NAO carrega campo de resultado", not proibidos, proibidos)

    for nome, obj in (("geometry", G), ("t_nodes", T), ("wall_8284580", W), ("snapshot_v1", S)):
        ck("%s: STATUS EVIDENCE_NOT_NORM" % nome, obj.get("status") == "EVIDENCE_NOT_NORM")

    raw = G["provenance"].get("raw_inputs_not_versioned") or []
    ck("provenance das entradas brutas presente", bool(raw))
    for r in raw:
        ck("  %s com sha256 valido" % r.get("file"),
           bool(re.fullmatch(r"[0-9a-f]{64}", r.get("sha256") or "")))


def nos(T):
    print("\n[NOS] os 37 T, os 3 casos, os 2 controles e as 7 faltas reais")
    ck("37 encontros T", len(T["t_nodes"]) == 37, len(T["t_nodes"]))
    mw = T["measured_with"]
    ck("exigencias do motor == fisica do bloco (27 / 34 / 0,05)",
       (mw["b54_half_room_cm"], mw["b34_room_cm"], mw["physical_tolerance_cm"])
       == (B54_HALF_CM, B34_CM, TOL_CM))
    ck("medido no commit da secao 74 (2c55211)",
       str(mw["engine_commit_s74"]).startswith("2c55211"))

    by = dict((n["provenance"]["bench_node_index"], n) for n in T["t_nodes"])
    ck("10 reprovam com a flag OFF",
       sum(1 for n in T["t_nodes"] if not n["expected_ok_flag_off"]) == 10)
    ck("7 reprovam com a flag ON",
       sum(1 for n in T["t_nodes"] if not n["expected_ok_flag_on"]) == 7)
    mud = sorted(k for k, n in by.items()
                 if n["expected_ok_flag_off"] != n["expected_ok_flag_on"])
    ck("exatamente 3 mudam de veredito: 24, 44, 46", mud == [24, 44, 46], mud)

    for k in (24, 44, 46):
        n = by[k]
        s = n["shortfall_b54_cm"]
        ck("caso %d: falta %.6f cm, abaixo da tolerancia, OFF=False ON=True" % (k, s),
           0 < s < TOL_CM and n["expected_ok_flag_off"] is False
           and n["expected_ok_flag_on"] is True)
    for k in (12, 26):
        n = by[k]
        ck("controle %d: SOBRA, passa nos dois estados" % k,
           n["shortfall_b54_cm"] < 0 and n["expected_ok_flag_off"] is True
           and n["expected_ok_flag_on"] is True)
    for k in MATERIAIS:
        n = by[k]
        s = n["shortfall_b54_cm"]
        ck("falta material no %d (%.6f cm) reprova nos dois" % (k, s),
           s > TOL_CM and n["expected_ok_flag_off"] is False
           and n["expected_ok_flag_on"] is False)

    print("\n[SIMETRIA] caso e controle: mesma principal, mesma magnitude, sinal oposto")
    for caso, ctrl in ((24, 26), (44, 12), (46, 12)):
        a, b = by[caso], by[ctrl]
        ma, mb = abs(a["shortfall_b54_cm"]), abs(b["shortfall_b54_cm"])
        print("       %d x %d: principal %s/%s  |margem| %.6f vs %.6f cm"
              % (caso, ctrl, a["main_wall_key"], b["main_wall_key"], ma, mb))
        ck("%d/%d na MESMA parede principal" % (caso, ctrl),
           a["main_wall_key"] == b["main_wall_key"])
        ck("%d/%d com a MESMA magnitude" % (caso, ctrl), abs(ma - mb) < 1e-9)
        ck("%d/%d com sinal CONTRARIO" % (caso, ctrl),
           (a["shortfall_b54_cm"] > 0) != (b["shortfall_b54_cm"] > 0))

    print("\n[ESCALA] o 0,05 cm nao vem da saturacao, vem da separacao")
    mv = T["modeling_variation"]
    var = mv["max_modeling_deviation_cm"]
    prox = mv["next_materially_insufficient_cm"]
    r1, r2 = TOL_CM / var, prox / TOL_CM
    print("       variacao de modelagem %.6f cm | tolerancia %.2f cm | proxima falta %.6f cm"
          % (var, TOL_CM, prox))
    print("       tolerancia = %.2fx a variacao  e  %.1fx abaixo da proxima falta" % (r1, r2))
    ck("tolerancia acima de toda variacao observada (~3,8x)", 3.7 < r1 < 3.9, r1)
    ck("tolerancia muito abaixo da primeira falta real (~80x)", 79.5 < r2 < 80.5, r2)
    ck("as razoes declaradas no corpus batem com as recalculadas",
       abs(mv["ratio_tolerance_over_max_modeling_deviation"] - r1) < 0.01
       and abs(mv["ratio_next_over_tolerance"] - r2) < 0.1)

    print("\n[COBERTURA] a perna do B34 NAO e' exercitada")
    inc = min(n["room_incoming_cm"] for n in T["t_nodes"])
    print("       boneca mais apertada dos 37 T: %.4f cm, contra %.1f exigidos" % (inc, B34_CM))
    ck("a conjuncao so' e' exercida na perna do B54", inc > 2 * B34_CM, inc)
    ck("o corpus DECLARA essa lacuna", T.get("coverage", {}).get("b34_leg_exercised") is False)
    return by


def ancora(G, T, by):
    """A contribuicao propria: room_min conferido FORA do motor."""
    print("\n[ANCORA] room_min recalculado com aritmetica 2D pura, sem o motor")
    WK = dict((w["key"], w) for w in G["walls"])
    casados = 0
    print("       %-4s %-6s %16s %16s %11s" %
          ("no", "princ", "room_min corpus", "room_min indep", "delta"))
    for k in FRONTEIRA:
        n = by[k]
        w = WK[n["main_wall_key"]]
        tn, _d, L = _proj(w, n["position_cm"])
        bordas = []
        for o in G["openings"]:
            t, d, _ = _proj(w, o["center_cm"])
            if d <= w["thickness_cm"] and -1.0 <= t <= L + 1.0:
                bordas += [t - o["width_cm"] / 2.0, t + o["width_cm"] / 2.0]
        mais = min([b for b in bordas if b >= tn - 1e-6] + [L]) - tn
        menos = tn - max([b for b in bordas if b <= tn + 1e-6] + [0.0])
        indep = min(mais, menos)
        delta = abs(indep - n["room_min_cm"])
        print("       %-4d %-6s %16.6f %16.6f %11.2e" %
              (k, n["main_wall_key"], n["room_min_cm"], indep, delta))
        ok = delta < 1e-6
        casados += ok
        ck("no %d: room_min ancorado por borda de abertura, fora do motor" % k, ok, delta)
    ck("os 5 nos de fronteira estao ancorados externamente", casados == len(FRONTEIRA))
    print("       -> a margem submilimetrica vem da POSICAO DAS ABERTURAS na")
    print("          planta, nao de arredondamento do motor.")


def caso_parede(W):
    print("\n[PAREDE 8284580] divergencia recalculada pela definicao versionada")
    H = W["human_counts"]
    BL, ES = ("B39", "B34", "B54", "B19"), ("C09", "C04")
    tot_h = sum(v for k, v in H.items() if not k.startswith("Z_")) or 1
    for rot in ("flag_off", "flag_on"):
        e = W["expected"][rot]
        S = e["solver_counts"]
        comp = sum(abs(S.get(k, 0) - H.get(k, 0)) for k in BL + ES)
        livre = abs(S.get("Z_FREE_MID_WALL", 0) - H.get("Z_FREE_MID_WALL", 0))
        esp = abs(sum(S.get(k, 0) for k in ES) - sum(H.get(k, 0) for k in ES))
        div = round(100.0 * comp / tot_h + 2.0 * livre + 1.0 * esp, 1)
        g = e["divergence"]
        print("       %-9s comp=%-3d livre=%-3d esp=%-2d -> div=%6.1f (corpus %6.1f)"
              % (rot, comp, livre, esp, div, g["div"]))
        ck("%s: divergencia recalculada bate com a gravada" % rot, div == g["div"], div)
        ck("%s: hard gates zerados" % rot,
           e["hard_gates"] == {"collisions": 0, "non_modular": 0,
                               "unsupported": 0, "opening_invasion": 0})
    ck("a secao 74 reduz a divergencia desta parede",
       W["expected"]["flag_on"]["divergence"]["div"]
       < W["expected"]["flag_off"]["divergence"]["div"])
    print("       nota: composicao humana de UMA parede e' testemunha, nao gabarito")


def snapshot(S):
    print("\n[SNAPSHOT] normalizacao, saturacao, legado e hard gates")
    ck("normalizacao declarada S74_SNAPSHOT_V1", S.get("normalization") == "S74_SNAPSHOT_V1")
    nota = json.dumps(S.get("normalization_note", "")).lower()
    for proibido in ("run_id", "timestamp", "elementid", "ponteiro"):
        pass
    casos = dict((c["label"], c) for c in S["cases"])
    for lab, pec in (("flag_off", 8750), ("tol_0_05", 8723),
                     ("tol_0_10", 8723), ("tol_0_30", 8723)):
        ck("%s: %d pecas" % (lab, pec), casos[lab]["pieces"] == pec, casos[lab]["pieces"])
        ck("%s: sha256 de 64 hex" % lab,
           bool(re.fullmatch(r"[0-9a-f]{64}", casos[lab]["sha256"])))
    shas = set(casos[l]["sha256"] for l in ("tol_0_05", "tol_0_10", "tol_0_30"))
    ck("0,05 / 0,10 / 0,30 dao o MESMO sha256 normalizado", len(shas) == 1, shas)
    ck("a flag desligada da um sha256 DIFERENTE",
       casos["flag_off"]["sha256"] not in shas)
    ck("o digest antigo de bancada esta' marcado como NAO oficial",
       isinstance(S.get("legacy_bench_hash"), dict)
       and S["legacy_bench_hash"].get("value") == "bc261fe485de635a")

    leg = S.get("legacy_cases") or []
    ck("dois casos de legado gravados", len(leg) == 2, len(leg))
    if len(leg) == 2:
        ck("legado: 8939 pecas nos dois", all(c["pieces"] == 8939 for c in leg))
        ck("legado: MESMO sha com a flag ligada e desligada",
           leg[0]["sha256"] == leg[1]["sha256"])
        ck("legado: sha256 == 3ba22aa08913ac5d...",
           leg[0]["sha256"].startswith("3ba22aa08913ac5d"), leg[0]["sha256"][:16])
        ck("legado NAO coincide com nenhum caso CHANNEL",
           leg[0]["sha256"] not in set(c["sha256"] for c in S["cases"]))

    zer = {"collisions": 0, "non_modular": 0, "unsupported": 0, "opening_invasion": 0}
    # ESCOPO: a alegacao de 0/0/0/0 e' sobre o fluxo CHANNEL (os `cases` e a
    # variante pos-§66). O LEGADO nao e' zerado - e nunca foi: `strategy=None`
    # e' o motor sem CHANNEL, o mesmo estado da main. O que a §74 precisa
    # provar sobre o legado e' que ela NAO o altera.
    channel = list(S["cases"]) + list(S.get("opening_variant_cases") or [])
    ruins = [c["label"] for c in channel if c.get("hard_gates") != zer]
    ck("hard gates 0/0/0/0 nos %d casos CHANNEL (inclui a variante pos-§66)"
       % len(channel), not ruins, ruins)

    if len(leg) == 2:
        g0, g1 = leg[0].get("hard_gates"), leg[1].get("hard_gates")
        print("       legado (strategy=None): %s" % g0)
        ck("legado: hard gates IDENTICOS com a flag ligada e desligada", g0 == g1,
           (g0, g1))
        ck("legado: sem colisao e sem invasao de vao",
           g0.get("collisions") == 0 and g0.get("opening_invasion") == 0, g0)
        if g0 != zer:
            print("       NOTA DO AUDITOR: o legado NAO e' 0/0/0/0 (non_modular=%s,"
                  % g0.get("non_modular"))
            print("       unsupported=%s) - e' o estado pre-existente da main, que o"
                  % g0.get("unsupported"))
            print("       CHANNEL corrige. A §74 nao piora nem melhora isso. Mas a frase")
            print("       do README 'ficam 0/0/0/0 em todos os casos gravados' inclui,")
            print("       na leitura literal, estes dois casos do legado - imprecisao")
            print("       documental, nao defeito da §74.")


def main():
    base = PADRAO
    if "--corpus" in sys.argv:
        base = sys.argv[sys.argv.index("--corpus") + 1]
    print("CORPUS: %s\n" % base)
    n = carregar(base)
    G, T, W, S = n["geometry"], n["t_nodes"], n["wall_8284580"], n["snapshot_v1"]
    estrutura(G, T, W, S)
    by = nos(T)
    ancora(G, T, by)
    caso_parede(W)
    snapshot(S)
    print("\n" + "=" * 72)
    print("FALHAS: %d" % len(FALHAS))
    for f in FALHAS:
        print("  - %s" % f)
    return 1 if FALHAS else 0


if __name__ == "__main__":
    sys.exit(main())
