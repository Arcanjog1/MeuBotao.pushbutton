# -*- coding: utf-8 -*-
"""CR-B / CANDIDATO §5 — RISCO PRINCIPAL: a mudanca de topologia T -> L.

Para cada no' cujo TIPO muda entre STATE_R (round-trip sem corte) e
STATE_C (candidato), mede:

  - geometria antes/depois (ponto, bracos, quem termina e quem passa);
  - paredes participantes por IDENTIDADE FISICA (`stable_key`);
  - faces e extremidades reais;
  - blocos HUMANOS que ocupam a pegada do no', fiada a fiada, nas DUAS
    fiadas alternadas, com o dono de cada peca ANTES e DEPOIS;
  - se a mudanca representa a geometria real ou e' artefato do corte.

NAO altera regra de amarracao. NAO forca B54. NAO cria excecao de parede
curta. So' mede.
"""
import argparse
import collections
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import candidate_lib as C  # noqa: E402

NODE_TOL_CM = 12.0   # mesma tolerancia de cluster de `reconstruct.detect_junctions`
BOND_CODES = ("B34", "B54")


def node_id(point):
    return "N%.1f,%.1f" % (round(point[0], 1), round(point[1], 1))


def nodes_of(project):
    """ponto -> {tipo, paredes participantes, quem termina ali}."""
    nodes = {}
    for w in project["walls"]:
        sk = C.stable_key(w)
        for j in w.get("junctions") or []:
            nid = node_id(j["point_cm"])
            e = nodes.setdefault(nid, {
                "node_id": nid, "point_cm": j["point_cm"], "type": j["type"],
                "participantes": [], "termina_ali": [], "passa_por": []})
            e["type"] = j["type"]
            e["participantes"].append(sk)
            (e["termina_ali"] if j.get("at_end") else e["passa_por"]).append(sk)
    for e in nodes.values():
        for k in ("participantes", "termina_ali", "passa_por"):
            e[k] = sorted(set(e[k]))
    return nodes


def block_covers(b, point, tol=0.5):
    """O bloco humano cobre fisicamente o ponto do no'?"""
    ang = math.radians(b.get("rotation_deg") or 0.0)
    dx, dy = point[0] - b["center_cm"][0], point[1] - b["center_cm"][1]
    t = dx * math.cos(ang) + dy * math.sin(ang)
    s = -dx * math.sin(ang) + dy * math.cos(ang)
    half_l = (b.get("length_cm") or 0.0) / 2.0 + tol
    half_w = (b.get("width_cm") or 14.0) / 2.0 + tol
    return abs(t) <= half_l and abs(s) <= half_w


def ownership(project, point):
    """Quem ocupa a pegada do no', fiada a fiada (por COTA fisica z, nao
    por indice ordinal)."""
    por_cota = collections.defaultdict(list)
    for w, r, b in C.all_blocks(project):
        if block_covers(b, point):
            por_cota[round(r["elevation_cm"], 1)].append({
                "dono_stable_key": C.stable_key(w),
                "dono_W0xx": w["id"],
                "code": b.get("code"),
                "type_name": b.get("type_name"),
                "role": b.get("role"),
                "length_cm": b.get("length_cm"),
                "center_cm": [round(b["center_cm"][0], 2),
                              round(b["center_cm"][1], 2)],
            })
    return {("z=%.1f" % z): sorted(v, key=lambda x: (x["dono_stable_key"],
                                                     x["center_cm"]))
            for z, v in sorted(por_cota.items())}


def resumo_amarracao(own):
    """Contagem de peca de amarracao real (B34/B54) por cota."""
    cotas = len(own)
    com_bond = sum(1 for v in own.values()
                   if any(p["code"] in BOND_CODES for p in v))
    donos = collections.Counter(p["dono_W0xx"] for v in own.values() for p in v)
    codes = collections.Counter(p["code"] for v in own.values() for p in v)
    return {"cotas_ocupadas": cotas, "cotas_com_B34_ou_B54": com_bond,
            "pecas_por_dono": dict(donos), "pecas_por_code": dict(codes)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.environ.get("CR_B_OUT",
                                                    os.path.join(HERE, "_out")))
    args = ap.parse_args()
    saida = {}
    for proj in C.PROJECTS:
        d = os.path.join(args.out, proj)
        R = json.load(open(os.path.join(d, "reference_roundtrip.json"),
                           encoding="utf-8"))
        K = json.load(open(os.path.join(d, "reference_candidate.json"),
                           encoding="utf-8"))
        nr, nk = nodes_of(R), nodes_of(K)

        todos = sorted(set(nr) | set(nk))
        transicoes = collections.Counter()
        mudados = []
        for nid in todos:
            a = nr.get(nid)
            b = nk.get(nid)
            ta = a["type"] if a else "AUSENTE"
            tb = b["type"] if b else "AUSENTE"
            if ta == tb and a and b and a["participantes"] == b["participantes"]:
                continue
            transicoes["%s->%s" % (ta, tb)] += 1
            if ta == tb:
                continue
            ponto = (b or a)["point_cm"]
            own_r = ownership(R, ponto)
            own_k = ownership(K, ponto)
            mudados.append({
                "node_id": nid,
                "point_cm": ponto,
                "ANTES": {"tipo": ta,
                          "participantes": a["participantes"] if a else [],
                          "termina_ali": a["termina_ali"] if a else [],
                          "passa_por": a["passa_por"] if a else []},
                "DEPOIS": {"tipo": tb,
                           "participantes": b["participantes"] if b else [],
                           "termina_ali": b["termina_ali"] if b else [],
                           "passa_por": b["passa_por"] if b else []},
                "ocupacao_ANTES": own_r,
                "ocupacao_DEPOIS": own_k,
                "amarracao_ANTES": resumo_amarracao(own_r),
                "amarracao_DEPOIS": resumo_amarracao(own_k),
            })

        # o teste decisivo: a OCUPACAO FISICA do no' mudou?
        iguais = 0
        for m in mudados:
            fa = {(z, p["code"], tuple(p["center_cm"]))
                  for z, v in m["ocupacao_ANTES"].items() for p in v}
            fb = {(z, p["code"], tuple(p["center_cm"]))
                  for z, v in m["ocupacao_DEPOIS"].items() for p in v}
            m["pecas_fisicas_identicas"] = (fa == fb)
            m["pecas_so_ANTES"] = sorted(str(x) for x in fa - fb)
            m["pecas_so_DEPOIS"] = sorted(str(x) for x in fb - fa)
            iguais += 1 if fa == fb else 0

        saida[proj] = {
            "nos_ANTES": len(nr), "nos_DEPOIS": len(nk),
            "transicoes": dict(sorted(transicoes.items())),
            "nos_com_tipo_alterado": len(mudados),
            "nos_alterados_com_pecas_fisicas_identicas": iguais,
            "detalhe": mudados,
        }
        print("=" * 88)
        print(proj)
        print("  nos:", len(nr), "->", len(nk))
        print("  transicoes:", dict(sorted(transicoes.items())))
        print("  nos com tipo alterado:", len(mudados),
              " dos quais com a MESMA ocupacao fisica de peca:", iguais)
        tot = collections.Counter()
        for m in mudados:
            tot["%s->%s" % (m["ANTES"]["tipo"], m["DEPOIS"]["tipo"])] += 1
        print("  por transicao de tipo:", dict(sorted(tot.items())))
    p = C.write_json(os.path.join(args.out, "junction_analysis.json"), saida)
    print("escrito:", p)


if __name__ == "__main__":
    main()
