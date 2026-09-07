# -*- coding: utf-8 -*-
"""Gera as tabelas markdown dos 19 casos a partir dos JSON de evidencia."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    return json.load(open(os.path.join(HERE, name), encoding="utf-8"))


dossier = load("case_dossier.json")
occ = load("void_occupancy.json")
lint = load("lintel_test.json")
crit = load("criterion_selectivity.json")
conf = {(c["wall_id_reference"], tuple(c["consenso_cm"])): c
        for c in load("measured_jamb_confirmation.json")}

RESSALVA = {
    ("torre_easy_lo_r00_tgd", "W052", (939.0, 1175.0)): "R1",
    ("torre_easy_lo_r00_tgd", "W006", (324.0, 425.0)): "R2",
    ("torre_easy_lo_r00_tgd", "W007", (324.0, 425.0)): "R2",
    ("torre_easy_lo_r00_tgd", "W015", (579.0, 735.0)): "R3",
    ("torre_easy_lo_r00_tp1", "W052", (939.0, 1175.0)): "R1",
    ("torre_easy_lo_r00_tp1", "W006", (324.0, 425.0)): "R2",
    ("torre_easy_lo_r00_tp1", "W007", (324.0, 425.0)): "R2",
    ("torre_easy_lo_r00_tp1", "W017", (579.0, 735.0)): "R3",
}

for proj in ["torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"]:
    casos = dossier[proj]["casos"]
    occ_by = {(c["wall_id_reference"], tuple(c["consenso_cm"])): c for c in occ[proj]}
    lin_by = {(c["wall_id_reference"], tuple(c["consenso_cm"])): c for c in lint[proj]}
    cri_by = {(c["wall"], tuple(c["consenso"])): c for c in crit[proj]
              if c["assinatura_15cm"]}
    medido = proj.endswith("tgd")
    print()
    print("### %s" % proj)
    print()
    print("| # | id ref | identidade fisica (jamba lo XY -> hi XY, cm) | envelope | consenso | larg | fiadas | perp. lo / hi (reserva de no') | blocos no vao | verga | jamba lo medida | jamba hi medida | classificacao | conf. |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for i, c in enumerate(sorted(casos, key=lambda x: (
            x["identidade_fisica"]["jamba_lo_xy_cm"],
            x["identidade_fisica"]["jamba_hi_xy_cm"])), 1):
        key = (c["wall_id_reference"], tuple(c["consenso_cm"]))
        o = occ_by[key]
        li = lin_by[key]
        cr = cri_by[key]
        cf = conf.get(key)
        idf = c["identidade_fisica"]
        perp = o["eixos_perpendiculares_cruzando"]
        perp_s = " / ".join("%s@%.0f%s" % (p["wall"], p["t_do_cruzamento_cm"],
                                           p["faixa_ocupada_cm"]) for p in perp)
        if li["n_fiadas_acima_do_trecho"] == 0:
            verga = "n/a (vao de altura plena)"
        else:
            verga = "NAO (%d fiada(s) acima, cobertura %.0f%%)" % (
                li["n_fiadas_acima_do_trecho"], li["cobertura_max_acima_pct"])
        if medido and cf:
            lo_s = "%s `%s` %+.3f" % (cf["confirmacao_jamba_lo"][0],
                                      cf["confirmacao_jamba_lo"][1],
                                      cf["confirmacao_jamba_lo"][2])
            hi_s = "%s `%s` %+.3f" % (cf["confirmacao_jamba_hi"][0],
                                      cf["confirmacao_jamba_hi"][1],
                                      cf["confirmacao_jamba_hi"][2])
        else:
            lo_s = hi_s = "sem fonte medida"
        r = RESSALVA.get((proj, c["wall_id_reference"], tuple(c["consenso_cm"])))
        classe = "DUAS_PAREDES_SEPARADAS" + (" (%s)" % r if r else "")
        if medido:
            confianca = "MEDIA-ALTA" if r in ("R1", "R2") else "ALTA"
        else:
            confianca = "MEDIA" if r in ("R1", "R2") else "MEDIA-ALTA"
        print("| %d | `%s` | (%.1f, %.1f) -> (%.1f, %.1f) | %s | %s | %.0f | %d | %s | %d | %s | %s | %s | %s | %s |" % (
            i, c["wall_id_reference"],
            idf["jamba_lo_xy_cm"][0], idf["jamba_lo_xy_cm"][1],
            idf["jamba_hi_xy_cm"][0], idf["jamba_hi_xy_cm"][1],
            c["envelope_cm"], c["consenso_cm"], c["largura_consenso_cm"],
            c["n_fiadas_do_trecho"], perp_s, o["n_blocos_no_consenso"],
            verga, lo_s, hi_s, classe, confianca))
