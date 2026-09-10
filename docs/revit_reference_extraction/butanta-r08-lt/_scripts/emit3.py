# -*- coding: utf-8 -*-
"""Entregaveis 09 (padroes) e 10 (comparacao TORRE EASY)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_core import *

DEST = ("C:/Users/CIVIX/OneDrive/\u00c1rea de Trabalho/Scripts.extension/MinhaAba.tab"
        "/MeuPainel.panel/MeuBotao.pushbutton/docs/revit_reference_extraction/butanta-r08-lt")
PROJECT = json.load(io.open(os.path.join(DEST, "01_family_catalog.json"),
                            encoding="utf-8"))["project"]
CTOL = 1.5


def wj(name, obj, compact=False):
    p = os.path.join(DEST, name)
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=(None if compact else 1), ensure_ascii=False,
                           separators=((",", ":") if compact else None)))
    print("  %-42s %8.1f KB" % (name, os.path.getsize(p) / 1024.0))


P, O, OA, by_lvl = build()
g = wall_groups(P)
topz = dict((k, max(p["_z"][0] for p in v)) for k, v in g.items())

AB = json.load(io.open(os.path.join(DEST, "03_above_openings.json"), encoding="utf-8"))["records"]
BE = json.load(io.open(os.path.join(DEST, "04_below_windows.json"), encoding="utf-8"))["records"]
CUT = json.load(io.open(os.path.join(DEST, "06_cut_blocks.json"), encoding="utf-8"))
CH = json.load(io.open(os.path.join(DEST, "05_channels.json"), encoding="utf-8"))


def stats(vals):
    v = sorted(x for x in vals if x is not None)
    if not v:
        return None
    n = len(v)
    q = lambda t: v[min(n - 1, int(round(t * (n - 1))))]
    return {"n": n, "min": v[0], "p25": q(.25), "mediana": q(.5), "p75": q(.75),
            "max": v[-1], "media": round(sum(v) / float(n), 2)}


def pat(pid, desc, occ, tot, conf, exc=None, extra=None):
    d = {"id": pid, "descricao": desc, "ocorrencias": occ, "total": tot,
         "percentual": round(100.0 * occ / tot, 2) if tot else None, "confianca": conf}
    if exc is not None:
        d["excecoes"] = exc
    if extra:
        d.update(extra)
    return d


pats = []
portas = [r for r in AB if r["opening_type"] == "PORTA"]
janelas = [r for r in AB if r["opening_type"] == "JANELA"]
abert = [r for r in AB if r["opening_type"] == "ABERTURA"]

pats.append(pat("BP01", "Toda PORTA tem canaleta apoiada no topo do vao",
                sum(1 for r in portas if r["all_canaleta_over_span"]), len(portas), "ALTA",
                exc=[r["opening_id"] for r in portas if not r["all_canaleta_over_span"]]))
pats.append(pat("BP02", "Toda abertura com peitoril tem canaleta imediatamente abaixo do peitoril",
                sum(1 for r in BE if r["all_canaleta_under_span"]), len(BE), "ALTA",
                exc=[r["opening_id"] for r in BE if not r["all_canaleta_under_span"]]))
pats.append(pat("BP03", "Base da canaleta acima = topo do vao (offset vertical 0,00 cm)",
                sum(1 for r in AB if r["vertical_offset_cm_CALCULADO"] == 0.0),
                sum(1 for r in AB if r["vertical_offset_cm_CALCULADO"] is not None), "ALTA"))
pats.append(pat("BP04", "Topo da canaleta abaixo = peitoril (offset vertical 0,00 cm)",
                sum(1 for r in BE if r["vertical_offset_cm_CALCULADO"] == 0.0),
                sum(1 for r in BE if r["vertical_offset_cm_CALCULADO"] is not None), "ALTA"))
pats.append(pat("BP05", "Qualquer abertura (porta/janela/abertura) tem canaleta acima",
                sum(1 for r in AB if r["all_canaleta_over_span"]), len(AB), "ALTA",
                exc=[r["opening_id"] for r in AB if not r["all_canaleta_over_span"]]))
pats.append(pat("BP06", "Toda JANELA tem canaleta acima",
                sum(1 for r in janelas if r["all_canaleta_over_span"]), len(janelas), "ALTA"))
pats.append(pat("BP07", "Vao rotulado ABERTURA tem canaleta acima",
                sum(1 for r in abert if r["all_canaleta_over_span"]), len(abert), "MEDIA"))
pats.append(pat("BP08", "Topo do vao na cota z_rel = 221 cm",
                sum(1 for r in AB if abs(r["opening_top_z_cm_MEDIDO"] - 221.0) <= 1.0), len(AB), "ALTA"))
pats.append(pat("BP09", "Nenhuma instancia de VERGA/CONTRAVERGA no modelo (69 tipos carregados, 0 usados)",
                0, 65747, "ALTA",
                extra={"tipos_carregados": 69, "instancias": 0,
                       "familias": ["VERGA JANELA", "VERGA JANELA 3 FUROS", "VERGA PORTA", "CONTRAVERGA"]}))
pats.append(pat("BP10", "Parametro de instancia 'Lintel' zerado em todas as pecas",
                65747, 65747, "ALTA"))
pats.append(pat("BP11", "Toda peca de alvenaria tem 14 cm de largura",
                sum(1 for p in P if abs(p["W"] - 14.0) < .1), len(P), "ALTA"))
pats.append(pat("BP12", "Rotacao multipla exata de 90 graus",
                sum(1 for p in P if min(abs(round(p["rot"]) % 90), 90 - abs(round(p["rot"]) % 90)) < .01),
                len(P), "ALTA"))
n_top = sum(1 for k, v in g.items()
            if all(is_canaleta(p["fam"]) for p in v if abs(p["_z"][0] - topz[k]) < .6))
pats.append(pat("BP13", "Ultima fiada da parede e 100% canaleta (cinta de topo)",
                n_top, len(g), "MEDIA"))
pats.append(pat("BP14", "CORTADO = corte na ALTURA (19 -> 9 cm)",
                CUT["mode_counts"].get("ALTURA", 0),
                sum(CUT["mode_counts"].values()), "MEDIA",
                extra={"corte_em_COMPRIMENTO": CUT["mode_counts"].get("COMPRIMENTO", 0)}))
n9 = [p for p in P if abs(p["H"] - 9.0) < .1]
n9ok = sum(1 for p in n9 if round((p["_z"][0] - DATUM[p["lvl"]] - 1.0) % 20.0, 1) in (0.0, 10.0))
pats.append(pat("BP15", "Peca de 9 cm ocupa base ou meia-fiada da grade de 20 cm (9+1+9=19)",
                n9ok, len(n9), "ALTA"))
n2 = sum(1 for r in AB if r["second_course_above_is_canaleta"])
pats.append(pat("BP16", "2a fiada acima do vao tambem e canaleta (verga + cinta de topo adjacentes)",
                n2, len(AB), "MEDIA"))
pats.append(pat("BP17", "Canaleta do modelo esta na fiada de topo da parede",
                CH["context_counts"].get("TOP_BOND_BEAM", 0),
                CH["totals_all_levels"]["n"], "ALTA"))
pats.append(pat("BP18", "Rotulo Titulo_abertura coerente com a geometria (PORTA <-> peitoril 0)",
                sum(1 for o in O if (o["titulo"] == "PORTA") == (o["peitoril"] < .1)), len(O), "ALTA"))

bl = [r.get("left_bearing_cm_solid_CALCULADO") for r in AB]
br = [r.get("right_bearing_cm_solid_CALCULADO") for r in AB]
mn = [min(a, b) for a, b in zip(bl, br) if a is not None and b is not None]
bl2 = [r.get("left_bearing_cm_solid_CALCULADO") for r in BE]
br2 = [r.get("right_bearing_cm_solid_CALCULADO") for r in BE]
mn2 = [min(a, b) for a, b in zip(bl2, br2) if a is not None and b is not None]

apoios = {
    "nota": ("Apoio medido da JAMBA ate' a extremidade da corrida continua de canaleta. "
             "'_bbox' usa a bounding box (inclui 1 cm de junta por face); "
             "'_solid' subtrai esse 1 cm e e' o apoio real de alvenaria. "
             "Quando a corrida encosta na extremidade da parede o valor nao e' uma "
             "decisao de apoio, e sim continuidade - ver campos run_reaches_wall_*."),
    "acima_esquerdo_solid": stats(bl), "acima_direito_solid": stats(br),
    "acima_minimo_por_abertura_solid": stats(mn),
    "abaixo_esquerdo_solid": stats(bl2), "abaixo_direito_solid": stats(br2),
    "abaixo_minimo_por_abertura_solid": stats(mn2),
    "acima_limiares": dict((">=%d cm" % t, sum(1 for v in mn if v >= t)) for t in (4, 9, 14, 19, 24, 34, 39)),
    "abaixo_limiares": dict((">=%d cm" % t, sum(1 for v in mn2 if v >= t)) for t in (4, 9, 14, 19, 24, 34, 39)),
    "acima_n": len(mn), "abaixo_n": len(mn2),
    "corrida_atinge_extremidade_da_parede": {
        "acima": sum(1 for r in AB if r.get("run_reaches_wall_start") or r.get("run_reaches_wall_end")),
        "abaixo": sum(1 for r in BE if r.get("run_reaches_wall_start") or r.get("run_reaches_wall_end"))},
}

largura_x_solucao = {}
for r in AB:
    b = int(r["opening_width_cm"] // 30) * 30
    k = "%d-%d cm" % (b, b + 29)
    d = largura_x_solucao.setdefault(k, {"n": 0, "com_canaleta": 0, "n_pecas": []})
    d["n"] += 1
    d["com_canaleta"] += 1 if r["all_canaleta_over_span"] else 0
    if r.get("n_channel_pieces_in_run"):
        d["n_pecas"].append(r["n_channel_pieces_in_run"])
for k, v in largura_x_solucao.items():
    v["n_pecas_stats"] = stats(v.pop("n_pecas"))

wj("09_observed_patterns.json", {
    "project": PROJECT,
    "aviso": "EVIDENCIA MEDIDA - NAO NORMATIVO. Nenhum destes padroes foi promovido a regra do solver.",
    "amostra": {"pecas": len(P), "aberturas_instanciadas": len(O),
                "aberturas_analisadas_com_clones": len(OA),
                "grupos_de_parede": len(g), "canaletas": CH["totals_all_levels"]["n"],
                "blocos_cortados": CUT["totals_all_levels"]["n"]},
    "padroes": pats,
    "apoios_laterais": apoios,
    "largura_do_vao_x_solucao": largura_x_solucao,
    "excecoes_detalhadas": [
        {"opening_id": r["opening_id"], "tipo": r["opening_type"], "parede": r["wall_label"],
         "nivel": r["level"], "largura_cm": r["opening_width_cm"],
         "topo_vao_cm": r["opening_top_z_cm_MEDIDO"], "topo_parede_cm": r["wall_top_z_cm"],
         "familias_sobre_o_vao": r["families_over_span"],
         "motivo_INFERIDO": ("vao livre ate' o topo da parede - nao ha' fiada sobre o vao"
                             if not r["families_over_span"]
                             else "vao pequeno resolvido com compensador deitado de 9 cm"),
         "confianca": "MEDIA"}
        for r in AB if not r["all_canaleta_over_span"]],
})

# ---------------- 10 comparacao ----------------
comp = {
    "project": PROJECT,
    "aviso": ("Comparacao de FATOS MEDIDOS. Os numeros do TORRE EASY vem da extracao ja "
              "versionada em docs/revit_reference_extraction/ - o RVT antigo NAO foi reaberto. "
              "Esta tabela NAO e' regra do solver."),
    "projeto_A": {"nome": "TORRE EASY-LO-R00", "fonte": "docs/revit_reference_extraction/REPORT_HUMAN_REVIT_MODULATION.md"},
    "projeto_B": {"nome": PROJECT["document_name"], "fonte": "esta pasta"},
    "linhas": [
        {"aspecto": "Sistema acima de PORTA", "torre_easy": "verga (familia dedicada, 9 cm de altura)",
         "butanta": "CANALETA (fiada inteira de 19 cm)", "diferenca": "SISTEMA DIFERENTE"},
        {"aspecto": "Sistema abaixo de PORTA", "torre_easy": "nenhum", "butanta": "nenhum (peitoril 0)",
         "diferenca": "igual"},
        {"aspecto": "Sistema acima de JANELA", "torre_easy": "verga", "butanta": "CANALETA",
         "diferenca": "SISTEMA DIFERENTE"},
        {"aspecto": "Sistema abaixo de JANELA", "torre_easy": "contraverga",
         "butanta": "CANALETA", "diferenca": "SISTEMA DIFERENTE"},
        {"aspecto": "Altura da peca especial", "torre_easy": "9 cm", "butanta": "19 cm (fiada inteira)",
         "diferenca": "2x mais alta"},
        {"aspecto": "Offset base da peca acima x topo do vao", "torre_easy": "0,00 cm (392/392)",
         "butanta": "0,00 cm (136/136 com peca)", "diferenca": "IDENTICO"},
        {"aspecto": "Offset topo da peca abaixo x peitoril", "torre_easy": "0,00 cm (147/147)",
         "butanta": "0,00 cm (89/89)", "diferenca": "IDENTICO"},
        {"aspecto": "Apoio minimo medido", "torre_easy": ">= 9 cm (784/784)",
         "butanta": ">= 4 cm (min 4 cm; mediana 24 cm acima, 24 cm abaixo)",
         "diferenca": "apoio menor, mas a canaleta e' continua e frequentemente vai ate' a proxima abertura"},
        {"aspecto": "Ultima fiada 100% canaleta", "torre_easy": "465/651 = 71,43%",
         "butanta": "%d/%d = %.2f%%" % (n_top, len(g), 100.0 * n_top / len(g)),
         "diferenca": "praticamente igual"},
        {"aspecto": "CORTADO = corte na altura", "torre_easy": "3.636/3.887 = 93,54%",
         "butanta": "%d/%d = %.2f%%" % (CUT["mode_counts"].get("ALTURA", 0),
                                        sum(CUT["mode_counts"].values()),
                                        100.0 * CUT["mode_counts"].get("ALTURA", 0) / sum(CUT["mode_counts"].values())),
         "diferenca": "BUTANTA usa muito mais corte no COMPRIMENTO"},
        {"aspecto": "Cobertura do catalogo do solver (pecas)", "torre_easy": "54.298/67.712 = 80,19%",
         "butanta": "55.963/65.747 = 85,12%", "diferenca": "+4,93 pontos"},
        {"aspecto": "Cobertura do catalogo (tipos)", "torre_easy": "6/57", "butanta": "6/21",
         "diferenca": "BUTANTA tem catalogo de pecas bem mais enxuto"},
        {"aspecto": "Walls nativas", "torre_easy": "0", "butanta": "0", "diferenca": "igual"},
        {"aspecto": "Portas/Janelas nativas", "torre_easy": "0", "butanta": "0", "diferenca": "igual"},
        {"aspecto": "Chave de parede", "torre_easy": "parametro de texto 'Parede' (PAR1..PAR117)",
         "butanta": "parametro de texto 'Parede' ('PARn - <faixa de pavimento>')",
         "diferenca": "mesmo mecanismo; BUTANTA embute a faixa de pavimento no valor"},
        {"aspecto": "Rotulo de abertura", "torre_easy": "Titulo_abertura (PORTA 248 / JANELA 134 / ABERTURA 102)",
         "butanta": "Titulo_abertura (PORTA 47 / JANELA 61 / ABERTURA 34)", "diferenca": "mesmo parametro"},
        {"aspecto": "bbox +2 cm no comprimento", "torre_easy": "sim", "butanta": "sim (20/20 familias)",
         "diferenca": "IDENTICO - mesma biblioteca de familias"},
        {"aspecto": "Familias de verga carregadas", "torre_easy": "usadas (417+122 instancias)",
         "butanta": "carregadas com 0 instancias (69 tipos)",
         "diferenca": "prova de escolha deliberada do sistema de canaleta"},
    ],
}
wj("10_torre_easy_comparison.json", comp)
print("EMIT 09-10 OK")
