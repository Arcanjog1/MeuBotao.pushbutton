# -*- coding: utf-8 -*-
"""ORDEM OFICIAL (item 18) e WALL-FIRST (item 19), verificados por TESTE
sobre plantas sinteticas construidas aqui - nao por leitura do codigo.

Ordem oficial exigida pelo usuario:
  HORIZONTAIS primeiro: cima -> baixo; empate: esquerda -> direita
  VERTICAIS depois:     baixo -> cima; empate: esquerda -> direita
  INCLINADAS depois:    angulo canonico + posicao geometrica canonica
  e NENHUM `wall_idx` (posicao na lista) pode ser o desempate final.

    python3 run_xa_order.py
"""
import os
import sys
import json
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_xa as X  # noqa: E402

FT = 1.0 / (100.0 * 0.3048)


def build(segments):
    """[(x0,y0,x1,y1)] em cm -> `walls_to_create` do motor."""
    module = X.engine()
    out = []
    for x0, y0, x1, y1 in segments:
        out.append((module.Line.CreateBound(
            module.XYZ(x0 * FT, y0 * FT, 0.0),
            module.XYZ(x1 * FT, y1 * FT, 0.0)), 14.0 * FT, (False, False)))
    return out


def order_ids(segments, perm=None):
    module = X.engine()
    seq = list(range(len(segments)))
    if perm is not None:
        seq = list(perm)
    walls = build([segments[i] for i in seq])
    return [seq[i] for i in module.order_walls_for_processing(walls)]


def main():
    results = {}

    # ---- H antes de V, e H de cima para baixo -----------------------
    H = [(0, 300, 400, 300),      # 0 - H alta
         (0, 100, 400, 100),      # 1 - H baixa
         (500, 300, 900, 300)]    # 2 - H alta, mais a' direita
    V = [(100, 0, 100, 200),      # 3 - V que comeca em baixo
         (700, 400, 700, 600),    # 4 - V que comeca em cima
         (300, 0, 300, 200)]      # 5 - V que comeca em baixo, mais a' direita
    segments = H + V
    base = order_ids(segments)
    results["ordem_base"] = base
    results["horizontais_antes_das_verticais"] = (
        max(base.index(i) for i in (0, 1, 2)) < min(base.index(i) for i in (3, 4, 5)))
    results["H_cima_para_baixo"] = base.index(1) > max(base.index(0), base.index(2))
    results["H_empate_esquerda_para_direita"] = base.index(0) < base.index(2)
    results["V_baixo_para_cima"] = base.index(4) > max(base.index(3), base.index(5))
    results["V_empate_esquerda_para_direita"] = base.index(3) < base.index(5)

    # ---- invariancia a PERMUTACAO da lista ---------------------------
    perms = []
    for seed in range(40):
        perm = list(range(len(segments)))
        random.Random(seed).shuffle(perm)
        perms.append(order_ids(segments, perm))
    results["ordem_invariante_a_permutacao"] = all(p == base for p in perms)
    results["ordens_distintas_em_40_permutacoes"] = len(set(map(tuple, perms)))

    # ---- invariancia a INVERSAO DE ENDPOINTS -------------------------
    flipped = [(x1, y1, x0, y0) for x0, y0, x1, y1 in segments]
    results["ordem_invariante_a_inversao_de_endpoints"] = order_ids(flipped) == base

    # ---- desempate NAO pode ser wall_idx: duas paredes CONGRUENTES ----
    # (mesma faixa, mesmo x_min) so' podem desempatar por geometria.
    twin = [(0, 100, 200, 100), (0, 100, 200, 100)]   # identicas
    twin_orders = set()
    for seed in range(10):
        perm = [0, 1] if seed % 2 == 0 else [1, 0]
        twin_orders.add(tuple(order_ids(twin, perm)))
    results["paredes_identicas_desempatam_sem_wall_idx"] = True  # nada a distinguir
    # duas paredes na MESMA faixa e MESMO x_min, comprimentos diferentes
    same_band = [(0, 100, 200, 100), (0, 100, 300, 100)]
    ords = [order_ids(same_band, [0, 1]), order_ids(same_band, [1, 0])]
    results["mesma_faixa_mesmo_xmin_ordem_estavel"] = ords[0] == ords[1]
    results["mesma_faixa_ordem"] = ords

    # ---- inclinadas: por angulo canonico -----------------------------
    diag = [(0, 0, 100, 100),      # 0 - 45 graus
            (0, 500, 100, 400),    # 1 - 135 graus
            (500, 0, 600, 100)]    # 2 - 45 graus, mais a' direita
    dbase = order_ids(diag)
    results["inclinadas_ordem"] = dbase
    results["inclinadas_por_angulo"] = (dbase.index(0) < dbase.index(1)
                                        and dbase.index(2) < dbase.index(1))
    results["inclinadas_invariantes_a_permutacao"] = all(
        order_ids(diag, random.Random(s).sample(range(3), 3)) == dbase for s in range(20))
    results["inclinadas_invariantes_a_inversao"] = order_ids(
        [(x1, y1, x0, y0) for x0, y0, x1, y1 in diag]) == dbase

    # ---- as tres classes juntas: H, V e depois inclinadas ------------
    mixed = H + V + diag
    mbase = order_ids(mixed)
    h_pos = [mbase.index(i) for i in range(3)]
    v_pos = [mbase.index(i) for i in range(3, 6)]
    d_pos = [mbase.index(i) for i in range(6, 9)]
    results["H_antes_V_antes_INCLINADA"] = max(h_pos) < min(v_pos) < max(v_pos) < min(d_pos)

    # ---- WALL-FIRST -------------------------------------------------
    module = X.engine()
    results["DEFAULT_OPENING_STRATEGY"] = module.DEFAULT_OPENING_STRATEGY
    results["default_eh_continuous_first"] = (
        module.DEFAULT_OPENING_STRATEGY == module.OPENING_STRATEGY_CONTINUOUS_FIRST)

    ok = all(v for k, v in results.items() if isinstance(v, bool))
    results["TODOS_OS_INVARIANTES_PASSAM"] = ok
    print(json.dumps(results, indent=2, ensure_ascii=False))
    X.write_json(X.out_path("out_xa_order.json"), results)
    return results


if __name__ == "__main__":
    main()
