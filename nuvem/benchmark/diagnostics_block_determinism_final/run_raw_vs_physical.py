# -*- coding: utf-8 -*-
"""Explica a diferenca entre a camada CRUA da CONTA 2 (`lib_det.
layer_block_layouts`, que identifica a peca por `origin_world` +
`rotation_deg`) e a camada FISICA da finalizacao (`lib_final.
layer_physical_block_layouts`, que identifica pela CELULA em mundo).

Item 40 da missao: "nao deixe p0/p1 invertidos gerarem diferenca apenas na
serializacao". Este script MEDE quanto do que ainda diverge na camada crua
e' exatamente isso.
"""
import sys
import json

import lib_final as F
import variants as V
import run_row_diff as RD


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "endpoint_reversal"
    project_id = sys.argv[2] if len(sys.argv) > 2 else F.PRIMARY_PROJECT_ID
    base_project = F.load_input(project_id)
    base = F.run_solver(project_id, input_project=base_project)
    var = F.run_solver(project_id, input_project=RD.VARIANT_BUILDERS[variant](base_project))

    _fp_b, raw_b = F.L.layer_block_layouts(base)
    _fp_v, raw_v = F.L.layer_block_layouts(var)
    _fp_pb, phys_b = F.layer_physical_block_layouts(base)
    _fp_pv, phys_v = F.layer_physical_block_layouts(var)

    def as_set(rows):
        return set(json.dumps(r, default=str, sort_keys=True) for r in rows)

    raw_only_b = as_set(raw_b) - as_set(raw_v)
    raw_only_v = as_set(raw_v) - as_set(raw_b)
    phys_only_b = as_set(phys_b) - as_set(phys_v)
    phys_only_v = as_set(phys_v) - as_set(phys_b)

    # Das linhas que divergem na camada CRUA, quantas sao a MESMA peca
    # fisica com rotacao 180 graus diferente?
    rotations = {}
    for blob in raw_only_b:
        row = json.loads(blob)
        rotations.setdefault((row[0] and tuple(row[0]), row[1], row[2], row[3], row[4]),
                             {})["base"] = row[5]
    for blob in raw_only_v:
        row = json.loads(blob)
        rotations.setdefault((row[0] and tuple(row[0]), row[1], row[2], row[3], row[4]),
                             {})["variant"] = row[5]
    same_place_diff_rotation = [
        (k, v) for k, v in rotations.items()
        if "base" in v and "variant" in v and abs((v["base"] - v["variant"]) % 360 - 180) < 1e-6
    ]
    codes = {}
    for k, _v in same_place_diff_rotation:
        codes[k[2]] = codes.get(k[2], 0) + 1

    report = {
        "variant": variant, "project_id": project_id,
        "raw_layer_diff": {"only_base": len(raw_only_b), "only_variant": len(raw_only_v)},
        "physical_layer_diff": {"only_base": len(phys_only_b), "only_variant": len(phys_only_v)},
        "same_position_rotated_180": len(same_place_diff_rotation),
        "same_position_rotated_180_by_code": codes,
        "sample": [list(k) for k, _v in same_place_diff_rotation[:6]],
    }
    print(json.dumps(report, indent=2, default=str)[:2500])
    F.write_json(F.out_path("out_raw_vs_physical_%s.json" % variant), report)


if __name__ == "__main__":
    main()
