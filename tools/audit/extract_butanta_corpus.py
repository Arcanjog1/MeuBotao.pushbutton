# -*- coding: utf-8 -*-
"""Extrai o corpus auditavel da SECAO 74 a partir da extracao do BUTANTA.

STATUS: EVIDENCIA / NAO NORMA.

ENTRADA (NAO versionada - ~9 MB de extracao bruta do Revit; o sha256 de cada
arquivo fica gravado na proveniencia do corpus):

    <bancada>/target_1pav.clean.json   geometria das paredes/aberturas do TARGET
    <bancada>/human_1pav.clean.json    pecas do projeto HUMANO (so' a parede do caso)
    <bancada>/rv/r_run4.json           catalogo REAL das familias, lido no Revit

SAIDA (versionada em reference_projects/butanta_r08_lt/s74_corpus/):

    geometry.json       INPUT: eixos, espessuras, aberturas, catalogo, proveniencia
    t_nodes.json        FATOS FISICOS ESPERADOS: espaco de cada T e os vereditos
    wall_8284580.json   o caso da parede: composicao humana e divergencia esperada
    snapshot_v1.json    hashes do conjunto fisico por tolerancia

uso:  MB_BENCH=<pasta da bancada> python tools/audit/extract_butanta_corpus.py

A bancada (scratchpad/) NAO faz parte do repositorio: ela so' e' necessaria para
REGERAR o corpus. Para AUDITAR o corpus basta o repositorio - ver
`tools/audit/audit_s74_corpus.py` e `tests/test_s74_corpus_butanta.py`.
"""
import collections
import datetime
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import s74_corpus as S  # noqa: E402

BENCH = os.environ.get("MB_BENCH")
CASO = 8284580
ENTRADAS = ("target_1pav.clean.json", "human_1pav.clean.json", "target_s72.clean.json",
            os.path.join("rv", "r_run4.json"))


def exige_bancada():
    """A bancada NAO faz parte do repositorio. Para AUDITAR o corpus nada disto e'
    necessario - use tools/audit/audit_s74_corpus.py ou o pytest."""
    if not BENCH:
        raise SystemExit(chr(10).join([
            "defina MB_BENCH=<pasta da bancada> para REGERAR o corpus.",
            "Para AUDITAR o corpus versionado, nada disso e' preciso:",
            "    python tools/audit/audit_s74_corpus.py",
            "    python -m pytest tests/test_s74_corpus_butanta.py -q"]))
    if not os.path.isdir(BENCH):
        raise SystemExit("MB_BENCH nao e' uma pasta: %s" % BENCH)
    faltando = [e for e in ENTRADAS if not os.path.isfile(os.path.join(BENCH, e))]
    if faltando:
        raise SystemExit("faltam entradas na bancada %s: %s" % (BENCH, ", ".join(faltando)))
    print("bancada:", BENCH)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for bloco in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def git(*args):
    try:
        return subprocess.check_output(["git"] + list(args), cwd=ROOT).decode().strip()
    except Exception:
        return None


def main():
    exige_bancada()
    sys.path.insert(0, BENCH)
    import corpus as B          # bancada: mesma regua de humano e solver
    import censo as C
    import tbench as tb

    doc = tb.load_target()
    mas = B.masonry()
    ordem = [w for w in doc["walls"] if w["id"] in mas]
    assert len(ordem) == 34, len(ordem)

    # ------------------------------------------------------------- geometria
    walls = []
    for i, w in enumerate(ordem):
        walls.append({
            "key": "W%02d" % (i + 1),
            "p0_cm": [float(w["p0"][0]), float(w["p0"][1])],
            "p1_cm": [float(w["p1"][0]), float(w["p1"][1])],
            "thickness_cm": float(w["width"]),
            "length_cm": ((w["p1"][0] - w["p0"][0]) ** 2 + (w["p1"][1] - w["p0"][1]) ** 2) ** 0.5,
            "provenance": {"revit_element_id": w["id"], "input_order": i},
        })
    por_id = dict((w["provenance"]["revit_element_id"], w["key"]) for w in walls)

    openings = []
    for i, o in enumerate(doc["openings"]):
        bb = o["bb"]
        cx, cy = (bb[0] + bb[3]) / 2.0, (bb[1] + bb[4]) / 2.0
        sill = o.get("Peitoril") or 0.0
        openings.append({
            "key": o["id"],
            "center_cm": [cx, cy],
            "insertion_cm": [float(o["o"][0]), float(o["o"][1])],
            "hand": [float(o["bx"][0]), float(o["bx"][1])],
            "width_cm": float(o["Largura_abertura"]),
            "sill_cm": float(sill),
            "head_cm": float(sill + (o.get("Altura_abertura") or 0.0)),
            "provenance": {"revit_element_id": o["id"], "input_order": i},
        })

    cat = json.load(open(os.path.join(BENCH, "rv", "r_run4.json"), encoding="utf-8"))["fill_catalog"]

    # variante: o estado das aberturas DEPOIS do microajuste da secao 66 (tres
    # aberturas andaram 10 cm). Foi sobre ele que a varredura de tolerancia do
    # checkpoint mediu os totais da regua - versionado para poder ser conferido.
    pos = json.load(open(os.path.join(BENCH, "target_s72.clean.json"), encoding="utf-8"))
    por_abertura = dict((o["id"], o) for o in pos["openings"])
    variante = []
    for o in openings:
        alt = por_abertura.get(o["key"])
        if alt is None:
            continue
        bb = alt["bb"]
        c = [(bb[0] + bb[3]) / 2.0, (bb[1] + bb[4]) / 2.0]
        i = [float(alt["o"][0]), float(alt["o"][1])]
        if c != o["center_cm"] or i != o["insertion_cm"]:
            variante.append({"key": o["key"], "center_cm": c, "insertion_cm": i,
                             "delta_cm": ((c[0] - o["center_cm"][0]) ** 2
                                          + (c[1] - o["center_cm"][1]) ** 2) ** 0.5})

    fontes = []
    for rel in ENTRADAS:
        p = os.path.join(BENCH, rel)
        fontes.append({"file": rel.replace("\\", "/"), "sha256": sha256(p),
                       "bytes": os.path.getsize(p)})

    geo = {
        "schema_version": 1,
        "status": "EVIDENCE_NOT_NORM",
        "provenance": {
            "source_project": "BUTANTA R08_LT - CIV0495",
            "source_file": "butanta testes.rvt (copia de trabalho do TARGET)",
            "source_version": "Revit 2026, 1o PAVIMENTO",
            "extraction_date": "2026-09-17",
            "units": "cm (comprimento), graus nao usados; direcao como vetor unitario",
            "coordinate_system": "coordenadas internas do projeto Revit, plano XY, Z do nivel",
            "level": "1o PAVIMENTO",
            "wall_population": "34 paredes de alvenaria do 1o pavimento (selecao da missao)",
            "courses_solved": S.COURSES_SOLVE,
            "courses_ruler": S.COURSES_RULER,
            "wall_height_cm": 340.0,
            "extraction_script": "tools/audit/extract_butanta_corpus.py",
            "engine_commit_s74": "2c55211632b96fbe1d3f31e9481df3ec8055cd6f",
            "repo_commit_at_extraction": git("rev-parse", "HEAD"),
            "raw_inputs_not_versioned": fontes,
            "precision": (
                "a geometria e' gravada SEM PERDA (repr de float, ida e volta exata em JSON). "
                "Medido: arredondar os eixos a 1e-6 cm ja' muda a composicao do solver "
                "(5.971 -> 5.972 pecas na regua, 19 B39 a mais, 20 B34 a menos), entao o corpus "
                "nao pode arredondar"),
            "input_order_is_part_of_the_input": (
                "a ordem das paredes e das aberturas e' a mesma que o Revit entregou; "
                "permutar a ordem muda o resultado do solver (comportamento anterior a esta "
                "missao, ver checkpoint 7.9), por isso ela faz parte do corpus"),
        },
        "walls": walls,
        "openings": openings,
        "opening_variants": {"post_micro_adjustment_s66": variante},
        "catalog": cat,
    }
    escreve("geometry.json", geo)

    # ------------------------------------------------------ fatos fisicos do T
    ctx = S.build_context(geo)
    exige_b54, exige_b34 = S.exige_cm()
    linhas = []
    for idx, node in S.tee_nodes(ctx):
        a = S.assessment_cm(ctx, idx)
        if a is None:
            continue
        mi, ii = node.get("main_wall_idx"), node.get("incoming_wall_idx")
        p = node["point"]
        linhas.append({
            "key": S.node_key(ctx, idx),
            "position_cm": [p.X * S.CM_PER_FT, p.Y * S.CM_PER_FT],
            "main_wall_key": ctx["keys"][mi] if mi is not None else None,
            "incoming_wall_key": ctx["keys"][ii] if ii is not None else None,
            "room_plus_cm": a["room_plus_cm"],
            "room_minus_cm": a["room_minus_cm"],
            "room_min_cm": a["room_min_cm"],
            "room_incoming_cm": a["room_incoming_cm"],
            "shortfall_b54_cm": exige_b54 - a["room_min_cm"],
            "shortfall_b34_cm": exige_b34 - a["room_incoming_cm"],
            "expected_ok_flag_off": S.room_ok(ctx, idx, False),
            "expected_ok_flag_on": S.room_ok(ctx, idx, True),
            "provenance": {"bench_node_index": idx,
                           "main_revit_element_id": id_de(geo, ctx, mi),
                           "incoming_revit_element_id": id_de(geo, ctx, ii)},
        })
    linhas.sort(key=lambda r: -r["shortfall_b54_cm"])

    fronteira = [r for r in linhas if abs(r["shortfall_b54_cm"]) <= 0.1]
    proximo_real = min([r["shortfall_b54_cm"] for r in linhas if r["shortfall_b54_cm"] > 0.1] or [None])
    ruido = max([abs(r["shortfall_b54_cm"]) for r in fronteira] or [0.0])

    def _desvio_ao_inteiro(valores):
        return max(abs(v - round(v)) for v in valores)

    dev_len = _desvio_ao_inteiro([w["length_cm"] for w in walls])
    dev_room = _desvio_ao_inteiro([r["room_min_cm"] for r in linhas])
    dev_pontas = _desvio_ao_inteiro([c for w in walls for p in (w["p0_cm"], w["p1_cm"]) for c in p])
    dev_max = max(dev_len, dev_room, dev_pontas)
    tol = S.tolerance_cm()
    tnodes = {
        "schema_version": 1,
        "status": "EVIDENCE_NOT_NORM",
        "measured_with": {"engine_commit_s74": "2c55211632b96fbe1d3f31e9481df3ec8055cd6f",
                          "b54_half_room_cm": round(exige_b54, 6),
                          "b34_room_cm": round(exige_b34, 6),
                          "physical_tolerance_cm": tol},
        "modeling_variation": {
            "note": ("a geometria do projeto NAO e' exata: as paredes foram modeladas com "
                     "variacao submilimetrica real. Duas medidas diferentes, as duas uteis:"),
            "max_modeling_deviation_cm": round(dev_max, 6),
            "max_modeling_deviation_definition": (
                "maior afastamento do centimetro inteiro observado na geometria do corpus "
                "(comprimento de parede, ponta de parede e espaco medido no T)"),
            "max_modeling_deviation_by_source_cm": {
                "wall_length": round(dev_len, 6),
                "wall_endpoint": round(dev_pontas, 6),
                "t_room_min": round(dev_room, 6),
            },
            "boundary_definition": ("|falta para o B54| <= 0,1 cm - os T em que a variacao de "
                                    "modelagem chega a decidir o veredito"),
            "boundary_nodes": len(fronteira),
            "max_abs_deviation_at_boundary_cm": round(ruido, 6),
            "next_materially_insufficient_cm": (round(proximo_real, 6) if proximo_real else None),
            "ratio_tolerance_over_max_modeling_deviation": round(tol / dev_max, 2),
            "ratio_next_over_tolerance": (round(proximo_real / tol, 1) if proximo_real else None),
        },
        "coverage": {
            "b54_leg_exercised": True,
            "b34_leg_exercised": False,
            "min_room_incoming_cm": round(min(r["room_incoming_cm"] for r in linhas), 6),
            "b34_required_cm": round(exige_b34, 6),
            "note": ("`_t_intersection_room_ok` e' uma CONJUNCAO: exige espaco para o B54 na "
                     "parede principal E espaco para o B34 na que chega. Neste corpus so' a "
                     "primeira perna e' exercida - a boneca mais apertada tem %.4f cm contra "
                     "%.1f cm exigidos, folga de %.1f cm em todos os 37 T. Portanto a segunda "
                     "perna NAO tem cobertura de regressao aqui, e isso esta' declarado em vez "
                     "de escondido. A perna do B54 e' a que a secao 74 muda."
                     % (min(r["room_incoming_cm"] for r in linhas), exige_b34,
                        min(r["room_incoming_cm"] for r in linhas) - exige_b34)),
        },
        "t_nodes": linhas,
    }
    escreve("t_nodes.json", tnodes)

    # -------------------------------------------------------------- a parede
    ws_b, mas_b = B.walls(), B.masonry()
    h = C.censo(B.human_pieces(ws_b, mas_b), ws_b, mas_b, "HUMANO")
    H = h["_por_parede"].get(CASO, {})
    chave_caso = por_id[CASO]

    casos = {}
    for rotulo, ligada in (("flag_off", False), ("flag_on", True)):
        ctx_s, res = S.solve_on_fresh_context(geo, ligada)
        rows = S.solver_rows(ctx_s, res, geo)
        Sc = S.wall_counts(rows, geo, chave_caso)
        casos[rotulo] = {"solver_counts": Sc, "divergence": S.divergence(H, Sc),
                         "hard_gates": S.hard_gates(res),
                         "pieces_in_ruler": len(rows)}

    caso = {
        "schema_version": 1,
        "status": "EVIDENCE_NOT_NORM",
        "wall_key": chave_caso,
        "provenance": {"revit_element_id": CASO,
                       "human_source": "human_1pav.clean.json (extracao read-only do projeto humano)",
                       "nota": ("a composicao humana aqui e' EVIDENCIA de uma unica parede, para "
                                "medir a divergencia do caso; nao e' gabarito nem norma - ver "
                                "reference_projects/README.md")},
        "human_counts": H,
        "metric": ("divergence(H, S) definida em tools/audit/s74_corpus.py: "
                   "100*comp/tot_h + 2*livre + 1*esp"),
        "expected": casos,
    }
    escreve("wall_8284580.json", caso)

    # ------------------------------------------------------------- snapshots
    snaps = {"schema_version": 1, "status": "EVIDENCE_NOT_NORM",
             "normalization": S.SNAPSHOT_NORMALIZATION,
             "normalization_note": S.normalized_snapshot.__doc__.strip(),
             "legacy_bench_hash": {
                 "value": "bc261fe485de635a",
                 "nota": ("hash citado no checkpoint; vinha do formato ad-hoc da bancada "
                          "(scratchpad/corpus.dump), que nao esta' versionado. O hash "
                          "auditavel e' o S74_SNAPSHOT_V1 abaixo.")},
             "cases": []}
    for rotulo, tol in (("flag_off", None), ("tol_0_05", 0.05), ("tol_0_10", 0.10), ("tol_0_30", 0.30)):
        if tol is None:
            ctx_s, res = S.solve_on_fresh_context(geo, False)
        elif abs(tol - S.tolerance_cm()) < 1e-12:
            ctx_s, res = S.solve_on_fresh_context(geo, True)      # caminho do PRODUTO
        else:
            with S.forced_tolerance_cm(tol):
                ctx_s, res = S.solve_on_fresh_context(geo, True)
        linhas_s = S.normalized_snapshot(ctx_s, res)
        rows = S.solver_rows(ctx_s, res, geo)
        snaps["cases"].append({"label": rotulo, "tolerance_cm": tol,
                               "pieces": len(linhas_s),
                               "sha256": S.snapshot_sha256(linhas_s),
                               "ruler_pieces": len(rows),
                               "ruler_codes": contagem_de_codigos(rows),
                               "hard_gates": S.hard_gates(res)})

    # A MESMA medida sobre a variante pos-microajuste (secao 66): e' o estado
    # sobre o qual a varredura de tolerancia do checkpoint mediu os totais.
    geo_v = S.with_opening_variant(geo, "post_micro_adjustment_s66")
    snaps["opening_variant_cases"] = []
    for rotulo, ligada in (("flag_off", False), ("tol_0_05", True)):
        ctx_v, res = S.solve_on_fresh_context(geo_v, ligada)
        linhas_s = S.normalized_snapshot(ctx_v, res)
        rows = S.solver_rows(ctx_v, res, geo_v)
        snaps["opening_variant_cases"].append({
            "variant": "post_micro_adjustment_s66", "label": rotulo,
            "pieces": len(linhas_s), "sha256": S.snapshot_sha256(linhas_s),
            "ruler_pieces": len(rows), "ruler_codes": contagem_de_codigos(rows),
            "hard_gates": S.hard_gates(res)})

    # O legado (`strategy=None`) nao passa pelo fluxo CHANNEL e por isso NAO pode
    # ser afetado pela secao 74. Fica no corpus para que "legado byte-identico"
    # deixe de ser alegacao de bancada e passe a ser verificavel no repositorio.
    snaps["legacy_cases"] = []
    for rotulo, ligada in (("strategy_none_flag_off", False), ("strategy_none_flag_on", True)):
        ctx_l, res = S.solve_on_fresh_context(geo, ligada, strategy=None)
        linhas_s = S.normalized_snapshot(ctx_l, res)
        snaps["legacy_cases"].append({"label": rotulo, "strategy": None,
                                      "pieces": len(linhas_s),
                                      "sha256": S.snapshot_sha256(linhas_s),
                                      "hard_gates": S.hard_gates(res)})
    escreve("snapshot_v1.json", snaps)
    print("corpus gravado em", S.CORPUS_DIR)


def contagem_de_codigos(rows):
    c = collections.Counter(code for _k, _ci, code, _lo, _hi in rows)
    return dict(sorted(c.items()))


def id_de(geo, ctx, wall_idx):
    if wall_idx is None:
        return None
    key = ctx["keys"][wall_idx]
    for w in geo["walls"]:
        if w["key"] == key:
            return w["provenance"]["revit_element_id"]
    return None


def escreve(nome, obj):
    if not os.path.isdir(S.CORPUS_DIR):
        os.makedirs(S.CORPUS_DIR)
    caminho = os.path.join(S.CORPUS_DIR, nome)
    with open(caminho, "w", encoding="utf-8", newline="
") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=False)
        fh.write("\n")
    print("  %-22s %8d bytes" % (nome, os.path.getsize(caminho)))


if __name__ == "__main__":
    main()
