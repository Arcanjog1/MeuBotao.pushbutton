# -*- coding: utf-8 -*-
"""CR-B / CANDIDATO — gera o candidato ISOLADO e mede os invariantes.

    python3 build_candidate.py [--out DIR]

Escreve SO' em `--out` (default: $CR_B_OUT ou ./_out). NAO escreve em
`nuvem/benchmark/projects/**`. Nao toca solver nem regra normativa.

Tres estados por projeto, todos gerados do MESMO dump sintetico do
gabarito oficial (leitura):

  STATE_A  gabarito OFICIAL em disco (`reference.json`) — nao regerado
  STATE_R  round-trip do gabarito SEM corte (controle) — isola o efeito
           ja' mesclado da CR-A (consenso) do efeito do corte
  STATE_C  CANDIDATO = STATE_R + corte estrutural C1 nos 19 casos

O delta que esta CR reivindica e' SEMPRE STATE_C - STATE_R.
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import candidate_lib as C  # noqa: E402


def resumo(p):
    jt = collections.Counter(j["type"] for w in p["walls"]
                             for j in (w.get("junctions") or []))
    nb = sum(len(r.get("blocks") or []) for w in p["walls"]
             for r in (w.get("rows") or []))
    return {
        "paredes": len(p["walls"]),
        "aberturas": sum(len(w.get("openings") or []) for w in p["walls"]),
        "blocos_em_paredes": nb,
        "orfaos": len(p.get("orphan_blocks") or []),
        "juncoes_por_tipo": dict(sorted(jt.items())),
        "comprimento_total_cm": round(sum(w["length_cm"] for w in p["walls"]), 2),
        "fiadas_total": sum(len(w.get("rows") or []) for w in p["walls"]),
    }


def block_index(project):
    """block_key -> lista de (wall_stable_key, row_index)."""
    idx = collections.defaultdict(list)
    for w, r, b in C.all_blocks(project):
        idx[C.block_key(b)].append((C.stable_key(w), r["row"]))
    return idx


def opening_index(project):
    out = {}
    for w in project["walls"]:
        for op in w.get("openings") or []:
            out[C.opening_key(w, op)] = {
                "host_stable_key": C.stable_key(w),
                "host_id": w["id"],
                "kind": op.get("kind"),
                "confidence": op.get("confidence"),
                "source_element_id": op.get("source_element_id"),
                "largura_cm": round(op["t_end_cm"] - op["t_start_cm"], 2),
                "z_range": [op.get("z_start_cm"), op.get("z_end_cm")],
            }
    return out


def invariantes(state_r, state_c, casos):
    """Os invariantes duros do enunciado §8, medidos por IDENTIDADE FISICA."""
    br, bc = block_index(state_r), block_index(state_c)
    perdidos = sorted(set(br) - set(bc))
    novos = sorted(set(bc) - set(br))
    dup_r = sorted(k for k, v in br.items() if len(v) > 1)
    dup_c = sorted(k for k, v in bc.items() if len(v) > 1)

    # bloco "deslocado": mesma identidade fisica, mas mudou de fiada
    # (a fiada e' posicional dentro da parede; mudar de parede e' esperado
    # e legitimo — e' exatamente o que o corte faz)
    mudou_fiada = []
    for k in set(br) & set(bc):
        if sorted(x[1] for x in br[k]) != sorted(x[1] for x in bc[k]):
            mudou_fiada.append(k)

    orr, occ = opening_index(state_r), opening_index(state_c)
    removidas = sorted(set(orr) - set(occ))
    adicionadas = sorted(set(occ) - set(orr))
    alteradas = [k for k in set(orr) & set(occ)
                 if orr[k] != occ[k] and
                 (orr[k]["largura_cm"] != occ[k]["largura_cm"]
                  or orr[k]["z_range"] != occ[k]["z_range"])]

    esperadas = sorted(c["opening_key"] for c in casos)
    return {
        "blocos_humanos_perdidos": perdidos,
        "blocos_humanos_novos": novos,
        "blocos_duplicados_STATE_R": dup_r,
        "blocos_duplicados_STATE_C": dup_c,
        "blocos_que_mudaram_de_fiada": sorted(mudou_fiada),
        "blocos_orfaos_STATE_R": len(state_r.get("orphan_blocks") or []),
        "blocos_orfaos_STATE_C": len(state_c.get("orphan_blocks") or []),
        "aberturas_removidas": removidas,
        "aberturas_adicionadas": adicionadas,
        "aberturas_com_geometria_alterada": sorted(alteradas),
        "aberturas_removidas_sao_exatamente_os_casos_C1":
            removidas == esperadas,
        "aberturas_removidas_com_source_element_id":
            sorted(k for k in removidas if orr[k]["source_element_id"]),
    }


def identity_map(state_r, state_c, casos):
    """Mapeamento de identidade FISICA antiga -> nova, por `stable_key`.

    Uma parede hospedeira cortada some como `stable_key` e da' origem a
    2 (ou mais) novas. Todas as demais mantem `stable_key` identico."""
    r_by_key = {C.stable_key(w): w for w in state_r["walls"]}
    c_by_key = {C.stable_key(w): w for w in state_c["walls"]}
    mantidas = sorted(set(r_by_key) & set(c_by_key))
    sumiram = sorted(set(r_by_key) - set(c_by_key))
    surgiram = sorted(set(c_by_key) - set(r_by_key))

    # cada parede nova e' filha da parede antiga cujo intervalo a contem
    filhos = collections.defaultdict(list)
    for nk in surgiram:
        nw = c_by_key[nk]
        o, d = C.axis(nw)
        melhor, melhor_d = None, None
        for ok in sumiram:
            ow = r_by_key[ok]
            o2, d2 = C.axis(ow)
            if abs(d2[0] * d[0] + d2[1] * d[1]) < 0.999:
                continue
            t0, s0 = C.pr(o2, d2, nw["start_cm"])
            t1, s1 = C.pr(o2, d2, nw["end_cm"])
            if max(abs(s0), abs(s1)) > 2.0:
                continue
            comp = ow["length_cm"]
            if min(t0, t1) < -1.0 or max(t0, t1) > comp + 1.0:
                continue
            dist = max(abs(s0), abs(s1))
            if melhor is None or dist < melhor_d:
                melhor, melhor_d = ok, dist
        filhos[melhor].append(nk)

    linhagem = []
    for ok in sumiram:
        ow = r_by_key[ok]
        kids = sorted(filhos.get(ok) or [])
        linhagem.append({
            "stable_key_antiga": ok,
            "id_antigo_W0xx": ow["id"],
            "comprimento_antigo_cm": round(ow["length_cm"], 2),
            "aberturas_antigas": len(ow.get("openings") or []),
            "filhas": [{"stable_key": k, "id_novo_W0xx": c_by_key[k]["id"],
                        "comprimento_cm": round(c_by_key[k]["length_cm"], 2),
                        "aberturas": len(c_by_key[k].get("openings") or [])}
                       for k in kids],
            "soma_filhas_cm": round(sum(c_by_key[k]["length_cm"] for k in kids), 2),
            "vaos_removidos_cm": round(
                ow["length_cm"] - sum(c_by_key[k]["length_cm"] for k in kids), 2),
        })

    # W0xx que mudou de significado apesar da parede ser a MESMA
    renumeradas = [{"stable_key": k, "W0xx_antigo": r_by_key[k]["id"],
                    "W0xx_novo": c_by_key[k]["id"]}
                   for k in mantidas if r_by_key[k]["id"] != c_by_key[k]["id"]]
    return {
        "paredes_mantidas": len(mantidas),
        "paredes_que_sumiram": len(sumiram),
        "paredes_que_surgiram": len(surgiram),
        "paredes_com_W0xx_renumerado_mesmo_sem_mudar_de_geometria":
            len(renumeradas),
        "renumeracao": renumeradas,
        "linhagem": sorted(linhagem, key=lambda e: e["stable_key_antiga"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.environ.get(
        "CR_B_OUT", os.path.join(HERE, "_out")))
    args = ap.parse_args()

    relatorio = {"candidate_version": C.CANDIDATE_VERSION, "projetos": {}}
    for proj in C.PROJECTS:
        ref = C.load_reference(proj)
        dump = C.dump_from_reference(ref)

        meta_r = dict(ref.get("metadata") or {})
        meta_r["candidate_state"] = "STATE_R"
        state_r = C.build_project_plain(dump, proj, meta_r)

        casos = C.c1_cases(state_r)
        cortes = [(c["xy_lo"], c["xy_hi"]) for c in casos]

        meta_c = dict(ref.get("metadata") or {})
        meta_c.update({
            "candidate_state": "STATE_C",
            "candidate_version": C.CANDIDATE_VERSION,
            "candidate_of": "reference.json (schema_version=2)",
            "candidate_criterion": "C1 estrutural: as DUAS jambas do vao "
                                   "coincidem (<=1,0cm) com a face interna de "
                                   "uma parede perpendicular (reserva de no'). "
                                   "SEM limiar de largura.",
            "candidate_provenance": (
                "gerado offline por build_candidate.py a partir do proprio "
                "reference.json oficial; WALL_SPLIT_GAP_CM/OPENING_GAP_MAX_CM "
                "inalterados (260,0); nenhuma constante de producao alterada"),
            "split_reason": "NODE_RESERVE_BOTH_JAMBS",
        })
        state_c = C.build_with_splits(dump, proj, cortes, metadata=meta_c)

        inv = invariantes(state_r, state_c, casos)
        idm = identity_map(state_r, state_c, casos)

        out_dir = os.path.join(args.out, proj)
        paths = {
            "reference_roundtrip": C.write_json(
                os.path.join(out_dir, "reference_roundtrip.json"), state_r),
            "reference_candidate": C.write_json(
                os.path.join(out_dir, "reference_candidate.json"), state_c),
        }
        from nuvem.benchmark.extract import reconstruct as _rec
        paths["input_roundtrip"] = C.write_json(
            os.path.join(out_dir, "input_roundtrip.json"),
            _rec.input_from_reference(state_r, proj))
        paths["input_candidate"] = C.write_json(
            os.path.join(out_dir, "input_candidate.json"),
            _rec.input_from_reference(state_c, proj))

        a = resumo(json.loads(json.dumps(ref)))
        r, c = resumo(state_r), resumo(state_c)
        entrada = {
            "casos_C1": casos,
            "n_casos_C1": len(casos),
            "STATE_A_oficial_em_disco": a,
            "STATE_R_roundtrip_sem_corte": r,
            "STATE_C_candidato": c,
            "invariantes": inv,
            "identidade": idm,
            # caminho RELATIVO a `--out`: o manifesto tem de ser
            # identico em qualquer maquina, senao o sha256 dele nao serve
            # de verificacao de reproducao.
            "arquivos": {k: {"path": os.path.relpath(v, args.out),
                             "sha256": C.sha256(v)}
                         for k, v in paths.items()},
        }
        relatorio["projetos"][proj] = entrada

        print("=" * 88)
        print(proj, " casos C1 =", len(casos))
        for k in ["paredes", "aberturas", "blocos_em_paredes", "orfaos",
                  "comprimento_total_cm", "fiadas_total"]:
            print("  %-24s A=%-12s R=%-12s C=%-12s  (C-R)=%+g"
                  % (k, a[k], r[k], c[k], c[k] - r[k]))
        for t in sorted(set(r["juncoes_por_tipo"]) | set(c["juncoes_por_tipo"])):
            print("  juncao %-18s A=%-12s R=%-12s C=%-12s  (C-R)=%+d"
                  % (t, a["juncoes_por_tipo"].get(t, 0),
                     r["juncoes_por_tipo"].get(t, 0),
                     c["juncoes_por_tipo"].get(t, 0),
                     c["juncoes_por_tipo"].get(t, 0) - r["juncoes_por_tipo"].get(t, 0)))
        print("  INVARIANTES:")
        for k in ["blocos_humanos_perdidos", "blocos_humanos_novos",
                  "blocos_duplicados_STATE_C", "blocos_que_mudaram_de_fiada",
                  "aberturas_adicionadas", "aberturas_com_geometria_alterada",
                  "aberturas_removidas_com_source_element_id"]:
            print("    %-46s %d" % (k, len(inv[k])))
        print("    %-46s %d" % ("aberturas_removidas", len(inv["aberturas_removidas"])))
        print("    %-46s %s" % ("removidas == casos C1",
                                inv["aberturas_removidas_sao_exatamente_os_casos_C1"]))
        print("    %-46s R=%d C=%d" % ("orfaos", inv["blocos_orfaos_STATE_R"],
                                       inv["blocos_orfaos_STATE_C"]))

    p = C.write_json(os.path.join(args.out, "candidate_manifest.json"), relatorio)
    print("\nescrito:", p)


if __name__ == "__main__":
    main()
