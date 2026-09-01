# -*- coding: utf-8 -*-
"""ETAPA 2K - CENSO DE ASSIMETRIA E DO DISCRIMINADOR (CR-2F-D).

SOMENTE LEITURA de `nuvem/core/**`. Tres medicoes sobre o projeto real
`torre_easy_lo_r00_tgd` (9.258 segmentos de CAD):

  A. MERGE      - `compat(A,B) == compat(B,A)` (heranca do CR-2F-A; tem de
                  continuar 0). Reaproveita o pre-filtro vetorizado da
                  Etapa 2J, sem reimplementa-lo.
  B. DEDUP      - a mesma propriedade sobre a relacao de duplicidade COMPLETA
                  que o CR-2F-D deixou em producao (conjuncao do predicado do
                  CR-2F-A com o do trecho compartilhado).
  C. DISCRIMINADOR - reproduz o `deduplicate_walls` SEM o criterio do
                  CR-2F-D (isto e', o comportamento anterior) e mede, para
                  CADA remocao, a separacao maxima no trecho compartilhado.
                  E' a prova de que a tolerancia de 2 cm ja' existente separa
                  as duas classes - nenhum valor novo foi calibrado.

    pip install numpy
    python3 nuvem/benchmark/diagnostics_2k/run_a_census.py

Sai com codigo 0 somente se A e B derem 0 violacoes.
"""
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "diagnostics_2f"))
sys.path.insert(0, os.path.join(_HERE, "..", "diagnostics_2j"))

import lib2f as L  # noqa: E402
import run_a_census as J2  # noqa: E402  (near_pairs / census_merge da Etapa 2J)


def census_dedup_completo(mod, walls):
    """`dup(A,B) == dup(B,A)` para a relacao de duplicidade COMPLETA de
    producao - os quatro testes de `deduplicate_walls`, na mesma ordem."""
    tol = mod.DUPLICATE_AXIS_TOLERANCE_FT
    thk = mod.WALL_THICKNESS_MATCH_TOLERANCE_FT

    def dup(w1, w2):
        if abs(w1[1] - w2[1]) > thk:
            return False
        if not mod.are_lines_parallel(w1[0], w2[0]):
            return False
        if not mod.symmetric_lines_within_distance(w1[0], w2[0], tol):
            return False
        if mod.symmetric_axis_gap_ft(w1[0], w2[0]) > tol:
            return False
        return mod.lines_overlap_enough(w1[0], w2[0])

    def base_ok(w1, w2):
        return (abs(w1[1] - w2[1]) <= thk and
                mod.are_lines_parallel(w1[0], w2[0]) and
                mod.lines_overlap_enough(w1[0], w2[0]))

    antes = depois = novo = total = 0
    for a in range(len(walls)):
        for b in range(a + 1, len(walls)):
            w1, w2 = walls[a], walls[b]
            if not base_ok(w1, w2):
                continue
            total += 1
            d12 = mod.get_distance_between_parallel_lines(w1[0], w2[0])
            d21 = mod.get_distance_between_parallel_lines(w2[0], w1[0])
            if (d12 <= tol) != (d21 <= tol):
                antes += 1
            if (mod.symmetric_lines_within_distance(w1[0], w2[0], tol) !=
                    mod.symmetric_lines_within_distance(w2[0], w1[0], tol)):
                depois += 1
            if dup(w1, w2) != dup(w2, w1):
                novo += 1
    return antes, depois, novo, total


def census_discriminador(mod, walls):
    """Reproduz o `deduplicate_walls` ANTERIOR ao CR-2F-D (sem o criterio do
    trecho compartilhado) e mede a separacao maxima de cada remocao."""
    tol = mod.DUPLICATE_AXIS_TOLERANCE_FT
    ordered = sorted(
        range(len(walls)),
        key=lambda k: (-walls[k][0].GetEndPoint(0).DistanceTo(
            walls[k][0].GetEndPoint(1)), mod._line_span_key(walls[k][0])))
    kept, linhas = [], []
    for k in ordered:
        line, th, _lk = walls[k]
        rep = None
        for kk in kept:
            kline, kth, _ = walls[kk]
            if abs(th - kth) > mod.WALL_THICKNESS_MATCH_TOLERANCE_FT:
                continue
            if not mod.are_lines_parallel(line, kline):
                continue
            if not mod.symmetric_lines_within_distance(line, kline, tol):
                continue
            if not mod.lines_overlap_enough(line, kline):
                continue
            rep = kk
            break
        if rep is None:
            kept.append(k)
        else:
            linhas.append(dict(
                removida_cm=L.cm(walls[k][0].Length),
                representante_cm=L.cm(walls[rep][0].Length),
                d_pontos_medios_cm=L.cm(max(
                    mod.get_distance_between_parallel_lines(line, walls[rep][0]),
                    mod.get_distance_between_parallel_lines(walls[rep][0], line))),
                sep_trecho_comum_cm=L.cm(
                    mod.symmetric_axis_gap_ft(line, walls[rep][0]))))
    linhas.sort(key=lambda r: -r["sep_trecho_comum_cm"])
    return linhas


def main():
    S = L.load()
    mod = S["mod"]
    lines = S["lines"]
    tol = mod.COLLINEAR_MATCH_TOLERANCE_FT

    print("segmentos de CAD           : %d" % len(lines))
    print("COLLINEAR_MATCH_TOLERANCE  : %.4f cm" % L.cm(tol))
    print("DUPLICATE_AXIS_TOLERANCE   : %.4f cm" % L.cm(mod.DUPLICATE_AXIS_TOLERANCE_FT))
    print("")

    t0 = time.time()
    pairs = J2.near_pairs(lines)
    print("pares proximos avaliados   : %d   (%.1fs)" % (len(pairs), time.time() - t0))

    antes, depois, pior, pior_par = J2.census_merge(mod, lines, pairs, tol)
    print("")
    print("=== A. MERGE (heranca do CR-2F-A) ===")
    print("  vereditos dependentes da direcao, primitiva ANTIGA : %d" % antes)
    print("  vereditos dependentes da direcao, EM PRODUCAO      : %d" % depois)
    print("  pior |d(A,B) - d(B,A)|                             : %.4f cm" % L.cm(pior))

    merged = L.run_merge(lines)[0]
    walls, _u, _d, _t = L.run_pairs(merged)
    a2, d2, novo, tot = census_dedup_completo(mod, walls)
    print("")
    print("=== B. deduplicate_walls (%d paredes aceitas, %d pares candidatos) ==="
          % (len(walls), tot))
    print("  vereditos dependentes da direcao, primitiva ANTIGA : %d" % a2)
    print("  idem, so' o predicado do CR-2F-A                   : %d" % d2)
    print("  idem, relacao COMPLETA em producao (CR-2F-D)       : %d" % novo)

    disc = census_discriminador(mod, walls)
    acima = [r for r in disc if r["sep_trecho_comum_cm"] > L.cm(mod.DUPLICATE_AXIS_TOLERANCE_FT)]
    print("")
    print("=== C. DISCRIMINADOR (%d remocoes do comportamento anterior) ===" % len(disc))
    print("  %-12s %-16s %-18s %s" % ("removida", "representante", "d pontos medios", "sep trecho comum"))
    for r in disc[:6]:
        print("  %10.2f cm %13.2f cm %15.4f cm %16.4f cm"
              % (r["removida_cm"], r["representante_cm"],
                 r["d_pontos_medios_cm"], r["sep_trecho_comum_cm"]))
    print("  ...")
    print("  remocoes com separacao > %.1f cm no trecho comum : %d"
          % (L.cm(mod.DUPLICATE_AXIS_TOLERANCE_FT), len(acima)))
    if len(disc) > len(acima):
        print("  pior separacao entre as remocoes LEGITIMAS      : %.4f cm"
              % max(r["sep_trecho_comum_cm"] for r in disc if r not in acima))

    rep = dict(segments=len(lines), near_pairs=len(pairs),
               merge_asym_primitiva_antiga=antes, merge_asym_producao=depois,
               merge_worst_delta_cm=L.cm(pior),
               dedup_candidates=tot, dedup_asym_primitiva_antiga=a2,
               dedup_asym_cr_2f_a=d2, dedup_asym_producao=novo,
               accepted_walls=len(walls), discriminador=disc)
    with open(os.path.join(_HERE, "out_a_census.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    print("")
    print("-> out_a_census.json")
    return 0 if (depois == 0 and novo == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
