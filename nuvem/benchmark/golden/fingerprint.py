# -*- coding: utf-8 -*-
"""Fingerprint CANONICO de um projeto (CR-BLOCK-GOLDEN-BENCHMARK, itens
15/16; expandido no CR-BLOCK-REFERENCE-CORPUS, itens 22-24).

Objetivo: rodar o MESMO projeto N vezes e responder "1 fingerprint" (e'
deterministico) ou "N fingerprints" (nao e' - e' exatamente o que o
CR-BLOCK-DETERMINISM, em paralelo nesta outra frente, esta' investigando
em `wall_stepper.py`/`wall_pairing.py`).

O fingerprint NAO pode depender de (item 16/22):

* `wall_idx` / posicao na lista (`walls` pode vir em qualquer ordem);
* `id()` do Python nem `ElementId`;
* `GetEndPoint(0)`/`GetEndPoint(1)` cru (sentido do desenho da parede).

Construido sobre as chaves GEOMETRICAS que `benchmark/model.py` ja' define
(`wall_stable_key`, `block_stable_key`, `opening_stable_key`) - nao
reinventa identidade nova, so' agrega o que ja' existe de forma ordenada e
hasheavel.

REVERSAO DE PONTA - o ajuste que faltava (item 22/23)
------------------------------------------------------
`wall_stable_key` normaliza a CHAVE da parede, mas `t_start_cm`/`t_end_cm`
de blocos e aberturas continuam medidos a partir do `start_cm` QUE AQUELE
OBJETO GUARDA - que pode ser qualquer uma das duas pontas fisicas. Duas
copias da MESMA parede fisica, uma desenhada ponta-A->ponta-B e outra
ponta-B->ponta-A, tem os MESMOS blocos/aberturas fisicos mas com
`t_start_cm`/`t_end_cm` **espelhados** (`t_novo = comprimento - t_velho`).
Sem corrigir isso, duas execucoes que decidem exatamente a mesma coisa,
so' com a parede "olhando" para o outro lado, dariam fingerprints
DIFERENTES - exatamente o falso-positivo de nao-determinismo que este
modulo existe para evitar. `wall_signature` abaixo detecta a reversao
(comparando `start_cm` contra `model.canonical_segment`) e espelha os
`t_*_cm` antes de assinar - nunca depois de calculado o hash.

ABERTURAS E NOS L/T/X (itens 23/24 - antes limitacao explicita, agora
implementado)
------------------------------------------------------------------------
* Abertura: `opening_signature` usa `model.opening_stable_key` (que ja'
  inclui a chave de parede canonica) sobre o `t_start_cm`/`t_end_cm` JA'
  espelhado quando a parede esta' em sentido reverso - mesma correcao
  acima, aplicada aqui tambem.
* No' L/T/X: `wall["junctions"]` grava `neighbors` como **indice** da
  lista `raw_walls` da extracao (`extract/reconstruct.py::detect_junctions`)
  - exatamente o `wall_idx` que este modulo e' proibido de usar (item 22).
  Em vez de confiar nesse indice, `canonical_junction_signatures` agrupa
  as copias do MESMO no' (cada parede que toca ali guarda a sua propria
  copia) pelo `point_cm` (arredondado na mesma grade de
  `model.STABLE_ID_GRID_CM`) e usa a CHAVE ESTAVEL de cada parede
  participante - nunca o indice cru.
"""

import hashlib
import json

from .. import model

FINGERPRINT_SCHEMA_VERSION = 2


def _snap(value, grid=model.STABLE_ID_GRID_CM):
    """Mesma grade de `model._snap` - reimplementada aqui (3 linhas) em vez
    de importar um simbolo `_privado` de outro modulo."""
    return round(round(float(value) / grid) * grid, 3)


def _wall_length(wall):
    length = wall.get("length_cm")
    if length:
        return float(length)
    return model.direction_of(wall["start_cm"], wall["end_cm"])[1]


def _wall_is_reversed(wall):
    """`True` quando `wall["start_cm"]` e' a ponta MAIOR da chave canonica
    (ou seja: esta copia da parede foi desenhada no sentido contrario ao
    que `wall_stable_key` normaliza) - e' quando `t_start_cm`/`t_end_cm`
    de blocos/aberturas precisam ser espelhados antes de assinar."""
    canonical_a, _b = model.canonical_segment(wall["start_cm"], wall["end_cm"])
    start = (_snap(wall["start_cm"][0]), _snap(wall["start_cm"][1]))
    canonical_start = (_snap(canonical_a[0]), _snap(canonical_a[1]))
    return start != canonical_start


def _mirror_t(t_cm, length_cm):
    return round(float(length_cm) - float(t_cm), 2)


def _canonical_t_range(t_start_cm, t_end_cm, length_cm, reversed_):
    """`(t_start, t_end)` no sentido CANONICO da parede - espelhado quando
    esta copia da parede esta' em sentido reverso, senao devolvido como
    esta'. Sempre devolvido com o menor valor primeiro."""
    if reversed_:
        t_start_cm, t_end_cm = _mirror_t(t_end_cm, length_cm), _mirror_t(t_start_cm, length_cm)
    return (round(float(t_start_cm), 2), round(float(t_end_cm), 2))


# --------------------------------------------------------------- blocos
def _block_signature(block, length_cm, reversed_):
    """Uma peca, em forma canonica e hasheavel: SEM `id`/`source_element_id`
    (podem mudar entre execucoes sem a decisao do solver ter mudado) e SEM
    `wall_id`/`row` crus (dependem de `assign_ids`, ja' cobertos pela
    fiada+posicao dentro da chave). `t_start_cm`/`t_end_cm` ja' saem
    CANONICOS (espelhados se a parede estiver em sentido reverso)."""
    t0, t1 = _canonical_t_range(block["t_start_cm"], block["t_end_cm"], length_cm, reversed_)
    return {
        "code": block.get("code"),
        "t_start_cm": t0,
        "t_end_cm": t1,
        "role": block.get("role"),
        "mirrored": bool(block.get("mirrored")),
        "rotation_deg": round(float(block.get("rotation_deg") or 0.0), 1),
    }


def wall_signature(wall):
    """Uma parede inteira, canonica: chave geometrica + fiadas ordenadas
    por indice + blocos ordenados pelo inicio CANONICO no eixo. Duas
    copias da MESMA parede fisica, uma start->end e outra end->start, dao
    a MESMA assinatura (ver o cabecalho do modulo)."""
    key = model.wall_stable_key(wall["start_cm"], wall["end_cm"], wall["thickness_cm"])
    length_cm = _wall_length(wall)
    reversed_ = _wall_is_reversed(wall)
    rows_sig = []
    for row in model.rows_sorted(wall):
        blocks_sig = [_block_signature(b, length_cm, reversed_)
                     for b in row.get("blocks") or []]
        blocks_sig.sort(key=lambda b: (b["t_start_cm"], b["t_end_cm"], b["code"] or ""))
        rows_sig.append({"row": row["row"], "blocks": blocks_sig})
    return {"key": key, "rows": rows_sig}


# -------------------------------------------------------------- aberturas
def opening_signature(wall, opening):
    """Item 23: chave canonica de UMA abertura - tipo, centro no eixo
    (canonico, espelhado se a parede estiver reversa), largura, altura,
    peitoril e a parede geometrica associada (`model.opening_stable_key`,
    que ja' usa a chave de parede canonica)."""
    length_cm = _wall_length(wall)
    reversed_ = _wall_is_reversed(wall)
    t0, t1 = _canonical_t_range(opening["t_start_cm"], opening["t_end_cm"], length_cm, reversed_)
    wall_key = model.wall_stable_key(wall["start_cm"], wall["end_cm"], wall["thickness_cm"])
    return {
        "key": model.opening_stable_key(wall_key, t0, t1, opening.get("sill_cm") or 0.0),
        "wall_key": wall_key,
        "kind": opening.get("kind"),
        "t_start_cm": t0,
        "t_end_cm": t1,
        "width_cm": round(abs(t1 - t0), 2),
        "sill_cm": round(float(opening.get("sill_cm") or 0.0), 2),
        "head_cm": round(float(opening.get("head_cm") or 0.0), 2),
        "height_cm": round(float(opening.get("height_cm") or
                                 ((opening.get("head_cm") or 0.0) - (opening.get("sill_cm") or 0.0))), 2),
    }


def canonical_opening_signatures(project):
    signatures = []
    for wall in project.get("walls") or []:
        for opening in wall.get("openings") or []:
            signatures.append(opening_signature(wall, opening))
    signatures.sort(key=lambda o: (o["wall_key"], o["t_start_cm"], o["t_end_cm"]))
    return signatures


# ---------------------------------------------------------------- L/T/X
def canonical_junction_signatures(project):
    """Item 24: um no' L/T/X por PONTO (nao por indice). Cada parede que
    toca o no' guarda a sua propria copia em `wall["junctions"]`, com
    `neighbors` apontando para indices de lista da extracao (`wall_idx` -
    proibido aqui, item 22) - por isso a identidade usada e' o PONTO
    (arredondado na grade de `model.STABLE_ID_GRID_CM`) mais a CHAVE
    ESTAVEL de cada parede que tem uma copia daquele no', nunca o indice.

    Quando as copias discordam do `type` (nao deveria acontecer, mas o
    dado e' de reconstrucao geometrica) os DOIS valores aparecem em
    `type` - a divergencia fica visivel, nunca escondida silenciosamente
    escolhendo uma delas."""
    groups = {}
    for wall in project.get("walls") or []:
        wall_key = model.wall_stable_key(wall["start_cm"], wall["end_cm"], wall["thickness_cm"])
        for junction in wall.get("junctions") or []:
            point = junction.get("point_cm")
            if not point:
                continue
            point_key = (_snap(point[0]), _snap(point[1]))
            group = groups.setdefault(point_key, {
                "point_cm": [round(point_key[0], 1), round(point_key[1], 1)],
                "types": set(),
                "walls": set(),
            })
            group["types"].add(junction.get("type"))
            group["walls"].add(wall_key)

    signatures = []
    for point_key in sorted(groups):
        group = groups[point_key]
        signatures.append({
            "point_cm": group["point_cm"],
            "type": sorted(t for t in group["types"] if t is not None),
            "walls": sorted(group["walls"]),
        })
    return signatures


# ----------------------------------------------------------- assinatura
def canonical_project_signature(project):
    """Estrutura ordenada e determinista do projeto inteiro - a entrada
    que vai pro hash. Publica de proposito: um teste/diagnostico pode
    comparar duas assinaturas campo a campo antes de olhar o hash."""
    wall_sigs = [wall_signature(w) for w in project.get("walls") or []]
    # Ordena pela CHAVE (geometrica), nunca pelo `id`/indice de entrada -
    # e' o que garante independencia de ordem (item 16).
    wall_sigs.sort(key=lambda w: w["key"])
    return {
        "schema_version": FINGERPRINT_SCHEMA_VERSION,
        "project_id": project.get("project_id"),
        "walls": wall_sigs,
        "openings": canonical_opening_signatures(project),
        "junctions": canonical_junction_signatures(project),
    }


def _hash_payload(payload):
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_fingerprint(project):
    """sha256 hex da assinatura canonica INTEIRA (parede+bloco+abertura+
    no'). Determinista: mesmo projeto (a menos de ordem/identificadores
    efemeros/sentido de ponta) -> mesmo hash, sempre."""
    return _hash_payload(canonical_project_signature(project))


def component_fingerprints(project):
    """Os TRES hashes separados (item 21/33: "abrir o diagnostico" de
    QUAL parte mudou) - util quando o fingerprint geral muda e a pergunta
    seguinte e' "foi bloco, abertura ou no'?"."""
    signature = canonical_project_signature(project)
    return {
        "walls_blocks": _hash_payload({"schema_version": signature["schema_version"],
                                       "walls": signature["walls"]}),
        "openings": _hash_payload({"schema_version": signature["schema_version"],
                                   "openings": signature["openings"]}),
        "junctions": _hash_payload({"schema_version": signature["schema_version"],
                                    "junctions": signature["junctions"]}),
        "overall": _hash_payload(signature),
    }


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
