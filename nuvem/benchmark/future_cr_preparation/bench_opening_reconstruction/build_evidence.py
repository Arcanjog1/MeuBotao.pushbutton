# -*- coding: utf-8 -*-
"""BENCH-OPENING-RECONSTRUCTION - coleta de EVIDENCIA (nao altera nada).

Produz `reconstruction_evidence.json` com a proveniencia de cada abertura
do gabarito (`reference.json`) dos dois projetos reais:

  * `envelope`  - uniao dos gaps livres por fiada ativa (o que o detector
                  `opening_audit.detect_wall_openings_from_courses` grava);
  * `consenso`  - intersecao dos mesmos gaps (jamba que TODA fiada respeita);
  * `spread`    - quanto o inicio/fim variam entre fiadas;
  * `no_mais_proximo` - distancia da jamba gravada ate' o no' (T/L/X) mais
                  proximo da propria parede;
  * `par_medido`- abertura `confidence=measured` (Revit) mais proxima, em
                  coordenadas ABSOLUTAS (so' o TGD tem aberturas medidas);
  * `eixo_medido` - trechos de parede MEDIDOS que cobrem o mesmo eixo, para
                  distinguir "vao numa parede" de "espaco entre duas paredes".

Nada aqui e' promovido a referencia. Uso: diagnostico da CR futura.
"""
import collections
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, ROOT)

from nuvem.benchmark import analysis, model  # noqa: E402

PROJECTS = ("torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1")
PROJ_DIR = os.path.join(ROOT, "nuvem", "benchmark", "projects")
# Folga para considerar o buraco de uma fiada "a mesma abertura":
# 40cm cobre a variacao real do dente de amarracao (2x15cm) com margem,
# e exclui a fiada inteiramente vazia.
COMPAT_SLACK_CM = 40.0


def _load(proj, name):
    path = os.path.join(PROJ_DIR, proj, name)
    if not os.path.exists(path):
        return None
    with open(path) as handle:
        return json.load(handle)


def _unit(wall):
    sx, sy = wall["start_cm"]
    ex, ey = wall["end_cm"]
    length = math.hypot(ex - sx, ey - sy) or 1.0
    return (sx, sy), ((ex - sx) / length, (ey - sy) / length), length


def _abs_point(wall, t_cm):
    (sx, sy), (ux, uy), _ = _unit(wall)
    return (sx + ux * t_cm, sy + uy * t_cm)


def _row_free_gap(row, lo_cm, hi_cm):
    """Maior intervalo livre da fiada que intersecta [lo,hi]."""
    occupied = sorted((b["t_start_cm"], b["t_end_cm"])
                      for b in row.get("blocks") or [])
    gaps = []
    prev_end = None
    for start, end in occupied:
        if prev_end is not None and start - prev_end > 1.0:
            gaps.append((prev_end, start))
        prev_end = end if prev_end is None else max(prev_end, end)
    best = None
    for gap in gaps:
        overlap = min(gap[1], hi_cm) - max(gap[0], lo_cm)
        if overlap > 0 and (best is None or (gap[1] - gap[0]) > (best[1] - best[0])):
            best = gap
    return best


def _measured_openings(input_doc):
    out = []
    for wall in (input_doc or {}).get("walls") or []:
        for opening in wall.get("openings") or []:
            if opening.get("confidence") != "measured":
                continue
            _, unit, _ = _unit(wall)
            out.append({
                "input_wall": wall["id"],
                "kind": opening.get("kind"),
                "width_cm": opening.get("width_cm"),
                "unit": unit,
                "p_start": _abs_point(wall, opening["t_start_cm"]),
                "p_end": _abs_point(wall, opening["t_end_cm"]),
                "source_element_id": opening.get("source_element_id"),
            })
    return out


def _measured_axis_runs(input_doc, wall):
    """Trechos de parede MEDIDOS colineares com `wall` (mesmo eixo, +-20cm)."""
    (sx, sy), (ux, uy), length = _unit(wall)
    runs = []
    for other in (input_doc or {}).get("walls") or []:
        (ox, oy), (vx, vy), olen = _unit(other)
        if abs(abs(ux * vx + uy * vy) - 1.0) > 1e-3:
            continue
        perp = abs(-(ox - sx) * uy + (oy - sy) * ux)
        if perp > 20.0:
            continue
        t0 = (ox - sx) * ux + (oy - sy) * uy
        ex, ey = other["end_cm"]
        t1 = (ex - sx) * ux + (ey - sy) * uy
        lo, hi = sorted((t0, t1))
        if hi < -20.0 or lo > length + 20.0:
            continue
        runs.append({"input_wall": other["id"], "perp_cm": round(perp, 2),
                     "t_lo_cm": round(lo, 2), "t_hi_cm": round(hi, 2)})
    return sorted(runs, key=lambda r: r["t_lo_cm"])


def build(proj):
    reference = _load(proj, "reference.json")
    input_doc = _load(proj, "input.json")
    block_h = (reference.get("settings") or {}).get("block_height_cm") or 19.0
    measured = _measured_openings(input_doc)
    records = []
    for wall in reference["walls"]:
        junctions = wall.get("junctions") or []
        axis_runs = None
        for opening in wall.get("openings") or []:
            lo_cm, hi_cm = opening["t_start_cm"], opening["t_end_cm"]
            per_row = []
            for row in model.rows_sorted(wall):
                if not analysis.opening_active_in_row(opening, row["elevation_cm"], block_h):
                    continue
                gap = _row_free_gap(row, lo_cm, hi_cm)
                if gap:
                    per_row.append({"row": row["row"],
                                    "gap_lo_cm": round(gap[0], 3),
                                    "gap_hi_cm": round(gap[1], 3)})
            if not per_row:
                continue
            # Fiadas COMPATIVEIS: o buraco livre daquela fiada tem largura da
            # ordem do vao gravado. Descarta a fiada VAZIA (buraco de centenas
            # de cm, que nao mede jamba nenhuma) sem descartar a variacao real
            # de 15cm do dente de amarracao.
            gravado_w = hi_cm - lo_cm
            compat = [g for g in per_row
                      if (gravado_w - COMPAT_SLACK_CM) <= (g["gap_hi_cm"] - g["gap_lo_cm"])
                      <= (gravado_w + 5.0)] or per_row
            los = [g["gap_lo_cm"] for g in compat]
            his = [g["gap_hi_cm"] for g in compat]
            envelope = (min(los), max(his))
            consensus = (max(los), min(his))
            spread = (round(max(los) - min(los), 3), round(max(his) - min(his), 3))

            def _node_distance(jamb_cm):
                if not junctions:
                    return None
                near = min(junctions, key=lambda j: abs(j["t_cm"] - jamb_cm))
                return {"type": near["type"], "t_cm": near["t_cm"],
                        "dist_cm": round(abs(near["t_cm"] - jamb_cm), 2)}

            centre = _abs_point(wall, (lo_cm + hi_cm) / 2.0)
            pair, pair_d = None, None
            _, unit, _ = _unit(wall)
            for cand in measured:
                if cand["kind"] != opening.get("kind"):
                    continue
                if abs(abs(cand["unit"][0] * unit[0] + cand["unit"][1] * unit[1]) - 1.0) > 1e-3:
                    continue
                cc = ((cand["p_start"][0] + cand["p_end"][0]) / 2.0,
                      (cand["p_start"][1] + cand["p_end"][1]) / 2.0)
                dist = math.hypot(cc[0] - centre[0], cc[1] - centre[1])
                if pair_d is None or dist < pair_d:
                    pair_d, pair = dist, cand
            if axis_runs is None:
                axis_runs = _measured_axis_runs(input_doc, wall)
            records.append({
                "project": proj,
                "wall": wall["id"],
                "opening": opening.get("id"),
                "kind": opening.get("kind"),
                "confidence": opening.get("confidence"),
                "source_element_id": opening.get("source_element_id"),
                "gravado_t_cm": [round(lo_cm, 3), round(hi_cm, 3)],
                "gravado_largura_cm": round(hi_cm - lo_cm, 3),
                "envelope_t_cm": [round(envelope[0], 3), round(envelope[1], 3)],
                "consenso_t_cm": [round(consensus[0], 3), round(consensus[1], 3)],
                "consenso_largura_cm": round(consensus[1] - consensus[0], 3),
                "spread_inicio_cm": spread[0],
                "spread_fim_cm": spread[1],
                "fiadas_ativas": len(per_row),
                "fiadas_compativeis": len(compat),
                # gaps por fiada so' nas aberturas com a assinatura de
                # envelope - manter os 94 x 14 do corpus inteiro incharia o
                # arquivo sem acrescentar evidencia.
                "gaps_por_fiada": (per_row if (abs(spread[0] - 15.0) < 0.02
                                               and abs(spread[1] - 15.0) < 0.02)
                                   else None),
                "no_perto_jamba_inicial": _node_distance(lo_cm),
                "no_perto_jamba_final": _node_distance(hi_cm),
                "par_medido": None if pair is None else {
                    "input_wall": pair["input_wall"],
                    "largura_cm": pair["width_cm"],
                    "source_element_id": pair["source_element_id"],
                    "dist_centro_cm": round(pair_d, 2),
                },
                "trechos_medidos_no_eixo": axis_runs,
            })
    return records


def main():
    out = {"gerado_por": "nuvem/benchmark/future_cr_preparation/"
                         "bench_opening_reconstruction/build_evidence.py",
           "aviso": "EVIDENCIA DIAGNOSTICA. Nao e' referencia aprovada.",
           "projetos": {}}
    for proj in PROJECTS:
        records = build(proj)
        sig = collections.Counter()
        for rec in records:
            if abs(rec["spread_inicio_cm"] - 15.0) < 0.02 or abs(rec["spread_fim_cm"] - 15.0) < 0.02:
                sig["ENVELOPE_15CM"] += 1
            elif max(rec["spread_inicio_cm"], rec["spread_fim_cm"]) > 1.0:
                sig["ENVELOPE_OUTRO"] += 1
            else:
                sig["ESTAVEL"] += 1
        out["projetos"][proj] = {"resumo": dict(sig), "aberturas": records}
    path = os.path.join(os.path.dirname(__file__), "reconstruction_evidence.json")
    with open(path, "w") as handle:
        json.dump(out, handle, indent=1, sort_keys=True)
    for proj, data in out["projetos"].items():
        print(proj, data["resumo"])
    print("escrito:", path)


if __name__ == "__main__":
    main()
