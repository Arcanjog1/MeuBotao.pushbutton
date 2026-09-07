# -*- coding: utf-8 -*-
"""BENCH-OPENING-RECONSTRUCTION - CANDIDATO (nao substitui nada).

Gera, em ESTE diretorio, `candidate_reference.json` e (quando o
`input.json` do projeto tambem carrega aberturas RECONSTRUIDAS)
`candidate_input.json`, corrigindo SO' as aberturas com a assinatura de
envelope de 15,0cm identificada em `reconstruction_evidence.json`.

Correcao aplicada: a jamba passa do ENVELOPE (uniao dos gaps por fiada,
que absorve a reserva de no'/dente de amarracao alternado) para o
CONSENSO (intersecao - a jamba que TODA fiada ativa respeita).

NAO toca:
  * blocos do gabarito humano;
  * paredes, nos, fiadas;
  * qualquer arquivo em `nuvem/benchmark/projects/**`.

Proveniencia de cada abertura corrigida fica em `candidate_provenance.json`.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT)

PROJ_DIR = os.path.join(ROOT, "nuvem", "benchmark", "projects")
SIG_TOL_CM = 0.02
SIG_VALUE_CM = 15.0


def _is_envelope_15(rec):
    return (abs(rec["spread_inicio_cm"] - SIG_VALUE_CM) < SIG_TOL_CM
            and abs(rec["spread_fim_cm"] - SIG_VALUE_CM) < SIG_TOL_CM)


def _apply(doc, corrections, label):
    """Aplica as correcoes a uma copia do documento. Devolve (doc, aplicadas)."""
    applied = []
    for wall in doc.get("walls") or []:
        for opening in wall.get("openings") or []:
            key = (wall["id"], round(opening["t_start_cm"], 3),
                   round(opening["t_end_cm"], 3))
            fix = corrections.get(key)
            if fix is None:
                continue
            before = [opening["t_start_cm"], opening["t_end_cm"]]
            opening["t_start_cm"] = fix["consenso_t_cm"][0]
            opening["t_end_cm"] = fix["consenso_t_cm"][1]
            opening["width_cm"] = round(fix["consenso_t_cm"][1] - fix["consenso_t_cm"][0], 3)
            opening["confidence"] = "reconstructed_candidate"
            opening["reconstruction_note"] = (
                "BENCH-OPENING-RECONSTRUCTION: jamba movida do ENVELOPE para o "
                "CONSENSO dos gaps por fiada (-15,0cm por jamba). Evidencia: "
                "reconstruction_evidence.json")
            applied.append({"documento": label, "wall": wall["id"],
                            "opening": opening.get("id"),
                            "antes_t_cm": before,
                            "depois_t_cm": list(fix["consenso_t_cm"])})
    return doc, applied


def main():
    with open(os.path.join(HERE, "reconstruction_evidence.json")) as handle:
        evidence = json.load(handle)

    provenance = {"aviso": "CANDIDATO DIAGNOSTICO - nao e' referencia aprovada.",
                  "criterio": "spread_inicio == spread_fim == 15,0cm (envelope)",
                  "projetos": {}}

    for proj, data in evidence["projetos"].items():
        corrections = {}
        for rec in data["aberturas"]:
            if not _is_envelope_15(rec):
                continue
            key = (rec["wall"], round(rec["gravado_t_cm"][0], 3),
                   round(rec["gravado_t_cm"][1], 3))
            corrections[key] = rec

        with open(os.path.join(PROJ_DIR, proj, "reference.json")) as handle:
            reference = json.load(handle)
        reference, applied_ref = _apply(reference, corrections, "reference")
        out_ref = os.path.join(HERE, "candidate_reference_%s.json" % proj)
        with open(out_ref, "w") as handle:
            json.dump(reference, handle, indent=1, sort_keys=True)

        applied_inp = []
        with open(os.path.join(PROJ_DIR, proj, "input.json")) as handle:
            input_doc = json.load(handle)
        reconstructed = any(
            (o.get("confidence") or "").startswith("reconstructed")
            for w in input_doc.get("walls") or []
            for o in w.get("openings") or [])
        if reconstructed:
            input_doc, applied_inp = _apply(input_doc, corrections, "input")
            out_inp = os.path.join(HERE, "candidate_input_%s.json" % proj)
            with open(out_inp, "w") as handle:
                json.dump(input_doc, handle, indent=1, sort_keys=True)

        provenance["projetos"][proj] = {
            "aberturas_corrigidas": len(corrections),
            "input_tem_aberturas_reconstruidas": reconstructed,
            "aplicadas_no_reference": applied_ref,
            "aplicadas_no_input": applied_inp,
            "evidencia_por_abertura": [
                {"wall": r["wall"], "opening": r["opening"],
                 "gravado_t_cm": r["gravado_t_cm"],
                 "consenso_t_cm": r["consenso_t_cm"],
                 "spread_cm": [r["spread_inicio_cm"], r["spread_fim_cm"]],
                 "fiadas_ativas": r["fiadas_ativas"],
                 "no_perto_jamba_inicial": r["no_perto_jamba_inicial"],
                 "no_perto_jamba_final": r["no_perto_jamba_final"],
                 "par_medido": r["par_medido"],
                 "trechos_medidos_no_eixo": r["trechos_medidos_no_eixo"]}
                for r in data["aberturas"] if _is_envelope_15(r)],
        }
        print("%s: %d aberturas corrigidas | reference=%d | input=%d (%s)" % (
            proj, len(corrections), len(applied_ref), len(applied_inp),
            "reconstruido" if reconstructed else "input MEDIDO - nao alterado"))

    with open(os.path.join(HERE, "candidate_provenance.json"), "w") as handle:
        json.dump(provenance, handle, indent=1, sort_keys=True)
    print("escrito: candidate_provenance.json")


if __name__ == "__main__":
    main()
