# -*- coding: utf-8 -*-
"""G18 da CR-B — TABELA DE MIGRACAO de identidade entre versoes do gabarito.

DIAGNOSTICO/PREPARACAO. Nao altera nada oficial: le' o gabarito de disco e
o candidato reproduzido em `$CR_B_OUT`, e escreve a tabela em `--out`
(default: ao lado deste script).

Por que existe (reconciliacao §9, G18): o rotulo `W0xx` e' derivado do
INDICE da parede no estado exportado - `W065` aponta para paredes
DIFERENTES em cada estado. Toda metrica historica registrada por `W0xx`
fica sem sentido depois de uma reconstrucao que muda a contagem de
paredes. A identidade estavel ja' existe no proprio arquivo: o campo
`key` (`model.wall_stable_key`), que e' GEOMETRICO (eixo canonico +
espessura).

Esta tabela responde, por identidade FISICA:

  - quais paredes sobrevivem intactas de um estado para o outro;
  - quais MUDAM de rotulo `W0xx` (o dado que o G18 exige medir);
  - quais somem e quais aparecem (o corte das 19 aberturas divide eixos).

Uso:
    export CR_B_OUT=/tmp/cr_b_candidate
    python3 build_identity_migration.py
"""
import argparse
import collections
import json
import os


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def index_by_key(project):
    """`key` geometrica -> lista de rotulos. Lista (nao escalar) de
    proposito: duas paredes com a MESMA chave sao uma ambiguidade real e
    precisam aparecer, nunca ser sobrescritas em silencio."""
    index = collections.defaultdict(list)
    for wall in project.get("walls") or []:
        index[wall.get("key")].append(wall.get("id"))
    return index


def migrate(from_project, to_project):
    origem, destino = index_by_key(from_project), index_by_key(to_project)
    linhas, ambiguas = [], []
    for key in sorted(set(origem) | set(destino)):
        de, para = origem.get(key) or [], destino.get(key) or []
        if len(de) > 1 or len(para) > 1:
            ambiguas.append({"key": key, "de": de, "para": para})
        if de and para:
            situacao = "PRESERVADA" if de == para else "MUDOU_DE_ROTULO"
        elif de:
            situacao = "SUMIU"
        else:
            situacao = "NOVA"
        linhas.append({"key": key, "de": de or None, "para": para or None,
                       "situacao": situacao})
    return linhas, ambiguas


def resumo(linhas):
    contagem = collections.Counter(linha["situacao"] for linha in linhas)
    return dict(sorted(contagem.items()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cr-b-out", default=os.environ.get("CR_B_OUT", "/tmp/cr_b_candidate"))
    parser.add_argument("--projects-dir", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
    projects_dir = args.projects_dir or os.path.join(root, "nuvem", "benchmark", "projects")
    out_path = args.out or os.path.join(here, "identity_migration.json")

    saida = {"gerado_por": "cr_b_identity_migration/build_identity_migration.py",
             "identidade": "model.wall_stable_key (eixo canonico + espessura)",
             "projetos": {}}
    for project_id in sorted(os.listdir(projects_dir)):
        oficial = os.path.join(projects_dir, project_id, "reference.json")
        candidato = os.path.join(args.cr_b_out, project_id, "reference_candidate.json")
        roundtrip = os.path.join(args.cr_b_out, project_id, "reference_roundtrip.json")
        if not (os.path.exists(oficial) and os.path.exists(candidato)):
            continue
        state_a, state_c = load(oficial), load(candidato)
        pares = [("STATE_A_oficial->STATE_C_candidato", state_a, state_c)]
        if os.path.exists(roundtrip):
            state_r = load(roundtrip)
            pares.append(("STATE_A_oficial->STATE_R_roundtrip", state_a, state_r))
            pares.append(("STATE_R_roundtrip->STATE_C_candidato", state_r, state_c))
        bloco = {}
        for nome, de, para in pares:
            linhas, ambiguas = migrate(de, para)
            bloco[nome] = {"resumo": resumo(linhas),
                           "n_paredes_de": len(de.get("walls") or []),
                           "n_paredes_para": len(para.get("walls") or []),
                           "chaves_ambiguas": ambiguas,
                           "linhas": linhas}
        saida["projetos"][project_id] = bloco
        principal = bloco["STATE_A_oficial->STATE_C_candidato"]
        print("%-26s %s  (ambiguas: %d)" % (project_id, principal["resumo"],
                                            len(principal["chaves_ambiguas"])))
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(saida, handle, ensure_ascii=False, sort_keys=True, indent=1)
    print("escrito:", out_path)


if __name__ == "__main__":
    main()
