# -*- coding: utf-8 -*-
"""APRENDIZADO DE PADROES a partir dos projetos entregues (item 11).

A regra que este modulo obedece acima de tudo:

    **Correlacao NAO vira regra obrigatoria automaticamente.**

Se um mesmo tipo de encontro em T aparece 40 vezes e 37 delas foram
resolvidas do mesmo jeito, isso e' um PADRAO OBSERVADO - informacao util
para o solver preferir aquela solucao, e nada mais. Virar regra
obrigatoria e' decisao de pessoa, registrada no
`nuvem/REGRAS_MODULACAO_BLOCOS.md`, nunca consequencia de um contador
passar de um limiar.

Por isso a saida daqui e' rotulada com o MESMO vocabulario de confianca
que aquele documento ja' usa:

* `OBRIGATORIO`  - so' quando uma pessoa marcou como tal (nunca inferido).
* `PREFERENCIAL` - dominante e com amostra grande o suficiente.
* `OBSERVADO`    - dominante mas com amostra pequena, ou dominancia fraca.
* `EXCECAO`      - variante minoritaria que aparece o bastante para nao ser
                   ruido; e' o registro de que o padrao TEM excecao real.

Um padrao so' e' promovido a PREFERENCIAL quando aparece em TODOS os
projetos da amostra (mesma regra de "padrao de escritorio" ja' escrita em
PADRAO_MODULACAO.md) - dominancia num projeto so' e' `OBSERVADO`, por mais
alta que seja.
"""

import json

from . import analysis
from . import model
from .validators import validate_junctions

CONFIDENCE_MANDATORY = "OBRIGATORIO"
CONFIDENCE_PREFERRED = "PREFERENCIAL"
CONFIDENCE_OBSERVED = "OBSERVADO"
CONFIDENCE_EXCEPTION = "EXCECAO"

# Amostra minima para um padrao ser considerado. Abaixo disso e' anedota.
MIN_SAMPLE = 8

# Fracao das ocorrencias que a variante dominante precisa alcancar.
DOMINANCE_RATIO = 0.7

# Variante minoritaria que aparece pelo menos nesta fracao vira EXCECAO
# registrada, em vez de sumir do relatorio.
EXCEPTION_RATIO = 0.1


def junction_patterns(project):
    """Como cada tipo de encontro foi resolvido, por fiada.

    A chave e' `(tipo_do_encontro, paridade_da_fiada)` e o valor e' o
    conjunto de codigos usados. A paridade entra na chave porque a
    amarracao ALTERNA de proposito - juntar fiada par e impar no mesmo
    balde apagaria justamente a informacao que interessa."""
    counts = {}
    for group in validate_junctions.collect_nodes(project):
        junction_type = group.get("type")
        if junction_type not in validate_junctions.BINDING_JUNCTION_TYPES:
            continue
        for row_index in validate_junctions._rows_of_group(group):
            covering = validate_junctions._covering_blocks(group, row_index)
            if not covering:
                continue
            key = (junction_type, "par" if row_index % 2 == 0 else "impar")
            solution = "+".join(sorted(b.get("code") or "?" for b in covering))
            counts.setdefault(key, {})
            counts[key][solution] = counts[key].get(solution, 0) + 1
    return counts


def opening_patterns(project):
    """Como o entorno das aberturas foi resolvido: peca na jamba, peca
    sobre a verga, peca sob o peitoril."""
    block_height = analysis.block_height_of(project)
    counts = {}
    for wall in project.get("walls") or []:
        rows = analysis.wall_rows_by_index(wall)
        for opening in wall.get("openings") or []:
            for row_index, row in rows.items():
                if not analysis.opening_active_in_row(
                        opening, row["elevation_cm"], block_height):
                    continue
                for block in row.get("blocks") or []:
                    for edge, side in ((opening["t_start_cm"], "esquerda"),
                                       (opening["t_end_cm"], "direita")):
                        if abs(block["t_end_cm"] - edge) <= analysis.BLOCK_JOINT_CM * 2:
                            key = (opening.get("kind"), "jamba_" + side)
                            counts.setdefault(key, {})
                            code = block.get("code") or "?"
                            counts[key][code] = counts[key].get(code, 0) + 1
                        elif abs(block["t_start_cm"] - edge) <= analysis.BLOCK_JOINT_CM * 2:
                            key = (opening.get("kind"), "jamba_" + side)
                            counts.setdefault(key, {})
                            code = block.get("code") or "?"
                            counts[key][code] = counts[key].get(code, 0) + 1
            # peca imediatamente ACIMA da verga
            for row_index in sorted(rows):
                row = rows[row_index]
                if not (opening["head_cm"] <= row["elevation_cm"]
                        < opening["head_cm"] + block_height * 1.5):
                    continue
                for block in row.get("blocks") or []:
                    if analysis.interval_overlap_cm(
                            (block["t_start_cm"], block["t_end_cm"]),
                            (opening["t_start_cm"], opening["t_end_cm"])) <= 0:
                        continue
                    key = (opening.get("kind"), "sobre_a_verga")
                    counts.setdefault(key, {})
                    code = block.get("code") or "?"
                    counts[key][code] = counts[key].get(code, 0) + 1
    return counts


def block_usage(project):
    """Quanto cada peca e' usada, e em que papel - a base para dizer que
    'o escritorio usa B34 como enchimento' ou 'nunca usa'."""
    counts = {}
    for _wall, _row, block in model.iter_blocks(project):
        key = (block.get("code") or "?", block.get("role") or "?")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _merge_counts(all_counts):
    """Junta os contadores de varios projetos, guardando em QUANTOS
    projetos cada variante apareceu - e' o que separa PREFERENCIAL
    (aparece em todos) de OBSERVADO (so' num)."""
    merged = {}
    for project_counts in all_counts:
        for key, variants in project_counts.items():
            entry = merged.setdefault(key, {"variants": {}, "projects": {}})
            for variant, count in variants.items():
                entry["variants"][variant] = entry["variants"].get(variant, 0) + count
                entry["projects"].setdefault(variant, set()).add(id(project_counts))
    return merged


def classify(merged, total_projects):
    """Contadores -> padroes rotulados. NUNCA devolve OBRIGATORIO: esse
    rotulo so' entra por decisao humana, escrita no
    REGRAS_MODULACAO_BLOCOS.md."""
    patterns = []
    for key, entry in sorted(merged.items(), key=lambda kv: str(kv[0])):
        variants = entry["variants"]
        total = sum(variants.values())
        if total < MIN_SAMPLE:
            continue
        ordered = sorted(variants.items(), key=lambda kv: (-kv[1], kv[0]))
        dominant, dominant_count = ordered[0]
        ratio = dominant_count / float(total)
        in_all_projects = len(entry["projects"].get(dominant, set())) >= total_projects
        if ratio >= DOMINANCE_RATIO and in_all_projects and total_projects >= 2:
            confidence = CONFIDENCE_PREFERRED
        else:
            confidence = CONFIDENCE_OBSERVED
        patterns.append({
            "context": list(key) if isinstance(key, tuple) else [key],
            "dominant": dominant,
            "count": dominant_count,
            "total": total,
            "ratio": round(ratio, 4),
            "confidence": confidence,
            "projects_with_dominant": len(entry["projects"].get(dominant, set())),
            "alternatives": [
                {
                    "variant": variant,
                    "count": count,
                    "ratio": round(count / float(total), 4),
                    "confidence": CONFIDENCE_EXCEPTION,
                }
                for variant, count in ordered[1:]
                if count / float(total) >= EXCEPTION_RATIO
            ],
        })
    return patterns


def learn(reference_projects):
    """Padroes de um conjunto de projetos de REFERENCIA (nunca de
    resultados do solver - aprender com a propria saida seria realimentar
    o proprio erro)."""
    for project in reference_projects:
        if project.get("source") == "solver":
            raise ValueError(
                "patterns.learn() so' aceita projetos de referencia; "
                "'{0}' veio do solver. Aprender com a saida do proprio "
                "solver realimentaria o erro dele.".format(project.get("project_id"))
            )
    total = len(reference_projects)
    return {
        "schema_version": 1,
        "projects": [p.get("project_id") for p in reference_projects],
        "n_projects": total,
        "note": (
            "PADRAO OBSERVADO nao e' regra. Promover algo daqui a regra "
            "obrigatoria e' decisao humana, registrada em "
            "nuvem/REGRAS_MODULACAO_BLOCOS.md."
        ),
        "junctions": classify(
            _merge_counts([junction_patterns(p) for p in reference_projects]), total),
        "openings": classify(
            _merge_counts([opening_patterns(p) for p in reference_projects]), total),
        "block_usage": sorted(
            [
                {"code": code, "role": role, "count": count}
                for (code, role), count in _sum_usage(reference_projects).items()
            ],
            key=lambda item: -item["count"],
        ),
    }


def _sum_usage(projects):
    total = {}
    for project in projects:
        for key, count in block_usage(project).items():
            total[key] = total.get(key, 0) + count
    return total


def save(patterns, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(patterns, handle, ensure_ascii=False, indent=1)
    return path


def format_report(patterns):
    lines = []
    lines.append("PADROES APRENDIDOS - {0} projeto(s) de referencia: {1}".format(
        patterns.get("n_projects"), ", ".join(patterns.get("projects") or [])))
    lines.append(patterns.get("note", ""))
    for section in ("junctions", "openings"):
        lines.append("")
        lines.append("== {0} ==".format(section.upper()))
        for pattern in patterns.get(section) or []:
            lines.append("  {0:<26} -> {1:<22} {2}/{3} ({4:.0f}%)  [{5}]".format(
                " / ".join(str(c) for c in pattern["context"]),
                pattern["dominant"], pattern["count"], pattern["total"],
                100.0 * pattern["ratio"], pattern["confidence"]))
            for alternative in pattern["alternatives"]:
                lines.append("      excecao real: {0:<20} {1} ({2:.0f}%)".format(
                    alternative["variant"], alternative["count"],
                    100.0 * alternative["ratio"]))
    return "\n".join(lines)
