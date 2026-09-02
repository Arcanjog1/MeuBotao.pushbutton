# -*- coding: utf-8 -*-
"""Fingerprint CANONICO de um projeto (itens 15 e 16 do pedido).

Objetivo: rodar o MESMO projeto N vezes e responder "1 fingerprint" (e'
deterministico) ou "N fingerprints" (nao e' - e' exatamente o que o
CR-BLOCK-DETERMINISM, rodando em paralelo nesta outra frente, esta'
investigando em `wall_stepper.py`/`wall_pairing.py`).

O fingerprint NAO pode depender de (item 16):

* `wall_idx` / posicao na lista (`walls` pode vir em qualquer ordem);
* `id()` do Python;
* `GetEndPoint(0)`/`GetEndPoint(1)` cru (sentido do desenho da parede).

Por isso ele e' construido inteiramente sobre as chaves GEOMETRICAS que
`benchmark/model.py` ja' define (`wall_stable_key`, `block_stable_key`) -
nao reinventa identidade nova, so' agrega o que ja' existe de forma
ordenada e hasheavel. `model.wall_stable_key` ja' e' invariante a
reversao de ponta (testado em `test_benchmark_infra.py` e de novo aqui,
no contexto do golden benchmark).

LIMITACAO EXPLICITA (documentada em vez de fingida resolvida, item 16):
aberturas e juntas/encontros (`wall["junctions"]`) ainda nao tem chave
canonica dedicada em `model.py` - por isso o fingerprint aqui cobre
GEOMETRIA DE PAREDE + POSICIONAMENTO DE BLOCO (o que o solver decide),
que e' o escopo do CR-BLOCK-DETERMINISM. Um fingerprint mais amplo
(aberturas, no's L/T/X) fica para quando `model.py` ganhar chave estavel
para eles - nao inventada aqui.
"""

import hashlib
import json

from .. import model


def _block_signature(block):
    """Uma peca, em forma canonica e hasheavel: SEM `id`/`source_element_id`
    (podem mudar entre execucoes sem a decisao do solver ter mudado) e SEM
    `wall_id`/`row` crus (dependem de `assign_ids`, ja' cobertos pela
    fiada+posicao dentro da chave)."""
    return {
        "code": block.get("code"),
        "t_start_cm": round(float(block["t_start_cm"]), 2),
        "t_end_cm": round(float(block["t_end_cm"]), 2),
        "role": block.get("role"),
        "mirrored": bool(block.get("mirrored")),
        "rotation_deg": round(float(block.get("rotation_deg") or 0.0), 1),
    }


def wall_signature(wall):
    """Uma parede inteira, canonica: chave geometrica + fiadas ordenadas
    por indice + blocos ordenados por inicio no eixo (`model.blocks_sorted`
    ja' faz isso). Duas paredes com o MESMO layout de blocos, uma desenhada
    start->end e outra end->start, produzem a mesma assinatura porque
    `wall_stable_key` ja' normaliza o sentido - mas os `t_start_cm` dos
    blocos sao relativos ao eixo ORIGINAL, entao esta funcao nao tenta
    "desvirar" blocos sozinha (ver `canonical_wall_key` abaixo e o teste
    `test_reversao_de_ponta_nao_muda_a_chave_da_parede`)."""
    key = model.wall_stable_key(wall["start_cm"], wall["end_cm"], wall["thickness_cm"])
    rows_sig = []
    for row in model.rows_sorted(wall):
        blocks_sig = [_block_signature(b) for b in model.blocks_sorted(row)]
        rows_sig.append({"row": row["row"], "blocks": blocks_sig})
    return {"key": key, "rows": rows_sig}


def canonical_project_signature(project):
    """Estrutura ordenada e determinista do projeto inteiro - a entrada
    que vai pro hash. Publica de proposito: um teste/diagnostico pode
    comparar duas assinaturas campo a campo antes de olhar o hash."""
    wall_sigs = [wall_signature(w) for w in project.get("walls") or []]
    # Ordena pela CHAVE (geometrica), nunca pelo `id`/indice de entrada -
    # e' o que garante independencia de ordem (item 16).
    wall_sigs.sort(key=lambda w: w["key"])
    return {
        "project_id": project.get("project_id"),
        "walls": wall_sigs,
    }


def canonical_fingerprint(project):
    """sha256 hex da assinatura canonica. Determinista: mesmo projeto (a
    menos de ordem/identificadores efemeros) -> mesmo hash, sempre."""
    signature = canonical_project_signature(project)
    payload = json.dumps(signature, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def multi_run_report(projects):
    """Resposta direta ao item 15: rodar o MESMO projeto varias vezes
    produziu 1 fingerprint (deterministico) ou N (nao e')?

    `projects` e' uma lista de resultados (`result.json`-shaped) de
    execucoes SEPARADAS do mesmo input. Nao roda nada sozinho - quem
    chama e' responsavel por gerar as N execucoes (este modulo e' puro,
    sem solver)."""
    fingerprints = [canonical_fingerprint(p) for p in projects]
    distinct = sorted(set(fingerprints))
    return {
        "runs": len(projects),
        "fingerprints": fingerprints,
        "distinct_fingerprints": len(distinct),
        "deterministic": len(distinct) <= 1,
        "distinct_values": distinct,
    }
