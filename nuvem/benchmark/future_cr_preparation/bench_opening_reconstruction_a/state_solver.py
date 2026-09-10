# -*- coding: utf-8 -*-
"""STATE_A/STATE_B do SOLVER nos 3 projetos.

Nao escreve nada em nuvem/benchmark/projects nem em reports (write_files=False).
Identidade dos achados = (code, wall, detail) - NAO usa block_id sequencial.
"""
import collections
import hashlib
import json
import os
import sys

ROOT = os.environ.get("REPO_ROOT", os.path.abspath("."))
sys.path.insert(0, ROOT)

from nuvem.benchmark import runner  # noqa: E402


def fingerprint(project):
    parts = []
    for wall in sorted(project.get("walls") or [], key=lambda w: w["id"]):
        for row in sorted(wall.get("rows") or [], key=lambda r: r["row"]):
            for block in sorted(row.get("blocks") or [],
                                key=lambda b: (b["t_start_cm"], b["t_end_cm"])):
                parts.append("%s|%s|%d|%.3f|%.3f" % (
                    wall["id"], block.get("code"), row["row"],
                    block["t_start_cm"], block["t_end_cm"]))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:12], len(parts)


def openings_identity(project_dir):
    """Identidade das aberturas do input.json: medidas x reconstruidas."""
    path = os.path.join(project_dir, "input.json")
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    out = []
    for wall in data.get("walls") or []:
        for op in wall.get("openings") or []:
            out.append({
                "wall": wall.get("id"),
                "kind": op.get("kind"),
                "t_start_cm": op.get("t_start_cm"),
                "t_end_cm": op.get("t_end_cm"),
                "width_cm": round((op.get("t_end_cm") or 0) - (op.get("t_start_cm") or 0), 3),
                "confidence": op.get("confidence"),
                "source_element_id": op.get("source_element_id"),
            })
    return out


def main():
    label = sys.argv[1]
    out_path = sys.argv[2]
    projects = sys.argv[3:] or ["piloto_sintetico_2x2",
                                "torre_easy_lo_r00_tgd",
                                "torre_easy_lo_r00_tp1"]
    state = {"label": label, "projects": {}}
    for proj in projects:
        outcome = runner.run_project(proj, write_files=False)
        digest, pieces = fingerprint(outcome["result"])
        findings = outcome["findings"]
        counts = collections.Counter(f["code"] for f in findings)
        ident = sorted("%s\x1f%s\x1f%s" % (f.get("code"), f.get("wall"), f.get("detail"))
                       for f in findings)
        ident_digest = hashlib.sha256("\n".join(ident).encode("utf-8")).hexdigest()[:12]
        state["projects"][proj] = {
            "fingerprint": digest,
            "pecas": pieces,
            "score": outcome["score"],
            "counts": dict(counts),
            "findings_identity_digest": ident_digest,
            "findings_identity": ident,
            "openings_input": openings_identity(runner.project_paths(proj)["dir"]),
        }
        print("%-24s fp=%s pecas=%-6d criticos=%s findings=%d" % (
            proj, digest, pieces, outcome["score"].get("critical_errors"),
            len(findings)))
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=1, sort_keys=True)
    print("escrito:", out_path)


if __name__ == "__main__":
    main()
