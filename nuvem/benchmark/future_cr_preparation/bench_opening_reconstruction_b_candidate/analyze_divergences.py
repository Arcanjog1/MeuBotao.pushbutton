# -*- coding: utf-8 -*-
"""CR-B / CANDIDATO §6 — as TRES divergencias pendentes (R1, R2, R3).

Para cada uma, imprime lado a lado, sem veredito:
  (A) GEOMETRIA MEDIDA  - `input.json` do TGD (167 paredes, 82 aberturas
      `measured`, documento Revit SEPARADO). SO' o TGD tem esta fonte.
  (B) MODULACAO HUMANA  - blocos realmente posicionados no `reference.json`
  (C) RECONSTRUCAO ATUAL - STATE_R (round-trip, sem corte)
  (D) CANDIDATO          - STATE_C

O `input.json` do TP1 e' derivado do proprio gabarito e NUNCA e' tratado
aqui como evidencia independente.
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import candidate_lib as C  # noqa: E402

# Os tres casos, ancorados por COORDENADA DE MUNDO (nunca por `W0xx`).
CASOS = {
    "R1": {
        "titulo": "W052 — sobra de 30,01 cm de parede medida dentro do vao",
        "projeto": "torre_easy_lo_r00_tgd",
        "eixo_xy": [[-139.487, 17.048], [96.513, 17.048]],
        "janela_cm": 260.0,
    },
    "R2": {
        "titulo": "W006/W007 em [324,425] — par de paredes paralelas no CAD",
        "projeto": "torre_easy_lo_r00_tgd",
        "eixo_xy": [[593.513, -246.0], [593.513, -145.0]],
        "janela_cm": 160.0,
    },
    "R3": {
        "titulo": "W015 (TGD) / W017 (TP1) — 193 cm sem parede medida colinear",
        "projeto": "torre_easy_lo_r00_tgd",
        "eixo_xy": [[-146.487, 24.048], [-146.487, 180.048]],
        "janela_cm": 400.0,
    },
}


def frame(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    n = math.hypot(*d)
    return a, (d[0] / n, d[1] / n), n


def perto(walls, o, d, janela, comp, lado_max=60.0):
    """Paredes cuja projecao cai na vizinhanca do trecho."""
    out = []
    for w in walls:
        t0, s0 = C.pr(o, d, w["start_cm"])
        t1, s1 = C.pr(o, d, w["end_cm"])
        if min(t0, t1) > comp + janela or max(t0, t1) < -janela:
            continue
        if min(abs(s0), abs(s1)) > lado_max:
            continue
        out.append({
            "id": w["id"],
            "stable_key": C.stable_key(w),
            "t": [round(min(t0, t1), 3), round(max(t0, t1), 3)],
            "s": [round(s0, 3), round(s1, 3)],
            "comprimento_cm": round(w.get("length_cm") or math.hypot(
                w["end_cm"][0] - w["start_cm"][0],
                w["end_cm"][1] - w["start_cm"][1]), 3),
            "espessura_cm": w.get("thickness_cm"),
            "colinear": abs(s0) <= 8.0 and abs(s1) <= 8.0,
            "perpendicular": abs(t0 - t1) < 1.0,
            "source_element_ids": w.get("source_element_ids"),
            "aberturas": [{"t": [round(op["t_start_cm"], 2),
                                 round(op["t_end_cm"], 2)],
                           "larg": round(op["t_end_cm"] - op["t_start_cm"], 2),
                           "conf": op.get("confidence"),
                           "src": op.get("source_element_id"),
                           "kind": op.get("kind")}
                          for op in (w.get("openings") or [])],
        })
    return sorted(out, key=lambda e: (e["t"][0], e["id"]))


def blocos_no_trecho(project, o, d, t_lo, t_hi, lado=20.0):
    """Blocos HUMANOS cujo centro cai no trecho [t_lo, t_hi] do eixo."""
    por_cota = {}
    for w, r, b in C.all_blocks(project):
        t, s = C.pr(o, d, b["center_cm"])
        if t_lo <= t <= t_hi and abs(s) <= lado:
            por_cota.setdefault(round(r["elevation_cm"], 1), []).append(
                "%s@%.1f(%s)" % (b.get("code"), t, w["id"]))
    return {("z=%.1f" % k): sorted(v) for k, v in sorted(por_cota.items())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.environ.get("CR_B_OUT",
                                                    os.path.join(HERE, "_out")))
    args = ap.parse_args()
    saida = {}
    for nome, caso in sorted(CASOS.items()):
        proj = caso["projeto"]
        d_ = os.path.join(args.out, proj)
        inp = C.load_input(proj)                        # (A) MEDIDO (so' TGD)
        ref = C.load_reference(proj)                    # (B) HUMANO
        R = json.load(open(d_ + "/reference_roundtrip.json", encoding="utf-8"))
        K = json.load(open(d_ + "/reference_candidate.json", encoding="utf-8"))

        a, b = caso["eixo_xy"]
        o, d, comp = frame(a, b)
        jan = caso["janela_cm"]

        entrada = {
            "titulo": caso["titulo"],
            "projeto": proj,
            "eixo_de_referencia_xy": caso["eixo_xy"],
            "comprimento_do_vao_cm": round(comp, 2),
            "A_MEDIDO_input_json": perto(inp["walls"], o, d, jan, comp),
            "C_RECONSTRUCAO_ATUAL_STATE_R": perto(R["walls"], o, d, jan, comp),
            "D_CANDIDATO_STATE_C": perto(K["walls"], o, d, jan, comp),
            "B_BLOCOS_HUMANOS_no_vao": blocos_no_trecho(ref, o, d, 0.0, comp),
            "B_BLOCOS_HUMANOS_ate_janela_depois":
                blocos_no_trecho(ref, o, d, comp, comp + jan),
            "B_BLOCOS_HUMANOS_ate_janela_antes":
                blocos_no_trecho(ref, o, d, -jan, 0.0),
        }
        saida[nome] = entrada
        print("#" * 100)
        print(nome, "—", caso["titulo"], " | projeto:", proj)
        print("  eixo do vao:", caso["eixo_xy"], " comprimento:", round(comp, 2), "cm")
        print("  (A) MEDIDO (input.json, documento Revit separado):")
        for w in entrada["A_MEDIDO_input_json"]:
            print("      %-6s t=%-22s s=%-18s comp=%-9s %s%s%s"
                  % (w["id"], w["t"], w["s"], w["comprimento_cm"],
                     "COLINEAR " if w["colinear"] else "",
                     "PERPENDIC " if w["perpendicular"] else "",
                     ("ab=" + json.dumps(w["aberturas"])) if w["aberturas"] else ""))
        print("  (C) RECONSTRUCAO ATUAL (STATE_R):")
        for w in entrada["C_RECONSTRUCAO_ATUAL_STATE_R"]:
            print("      %-6s t=%-22s s=%-18s comp=%-9s %s%s"
                  % (w["id"], w["t"], w["s"], w["comprimento_cm"],
                     "COLINEAR " if w["colinear"] else "",
                     ("ab=" + json.dumps(w["aberturas"])) if w["aberturas"] else ""))
        print("  (D) CANDIDATO (STATE_C):")
        for w in entrada["D_CANDIDATO_STATE_C"]:
            print("      %-6s t=%-22s s=%-18s comp=%-9s %s%s"
                  % (w["id"], w["t"], w["s"], w["comprimento_cm"],
                     "COLINEAR " if w["colinear"] else "",
                     ("ab=" + json.dumps(w["aberturas"])) if w["aberturas"] else ""))
        print("  (B) BLOCOS HUMANOS DENTRO do vao [0, %.1f]: %s"
              % (comp, entrada["B_BLOCOS_HUMANOS_no_vao"] or "NENHUM"))
    p = C.write_json(os.path.join(args.out, "divergences.json"), saida)
    print("escrito:", p)


if __name__ == "__main__":
    main()
