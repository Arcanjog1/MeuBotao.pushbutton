# -*- coding: utf-8 -*-
"""Monta compare_main_vs_block01.json a partir dos JSONs ja' gerados por
este laboratorio (out_main_aggregate_full_census.json,
out_block01_full_census.json, out_node_conflict_breakdown_*.json,
out_b19_location_*.json) - NENHUM numero novo e' calculado aqui, so'
reorganizado em MAIN / CR-BLOCK-01 / DELTA / DELTA%."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PRIMARY = "torre_easy_lo_r00_tgd"


def _load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)


def _delta(main_v, b01_v):
    d = b01_v - main_v
    pct = (d / main_v * 100.0) if main_v else None
    return {"MAIN": main_v, "CR_BLOCK_01": b01_v, "DELTA": d,
            "DELTA_PCT": round(pct, 2) if pct is not None else None}


def main():
    main_data = _load("out_main_aggregate_full_census.json")
    b01_data = _load("out_block01_full_census.json")
    node_main = _load("out_node_conflict_breakdown_MAIN.json")
    node_b01 = _load("out_node_conflict_breakdown_BLOCK01.json")
    b19_main = _load("out_b19_location_MAIN_torre_easy_lo_r00_tgd.json")
    b19_b01 = _load("out_b19_location_BLOCK01_torre_easy_lo_r00_tgd.json")

    mp = main_data["per_project"][PRIMARY]
    bp = b01_data["per_project"][PRIMARY]
    magg = main_data["cross_project_aggregate"]
    bagg = b01_data["cross_project_aggregate"]

    m_cov = mp["coverage_and_performance"]
    b_cov = bp["coverage_and_performance"]
    m_cb = mp["course_bond_prism"]
    b_cb = bp["course_bond_prism"]
    m_sb = mp["special_blocks"]
    b_sb = bp["special_blocks"]
    m_ix = mp["intersections_l_t_x"]
    b_ix = bp["intersections_l_t_x"]
    m_op = mp["openings"]
    b_op = bp["openings"]

    out = {
        "methodology_note": (
            "Todos os numeros vem do MESMO laboratorio (lib_audit.py + "
            "run_*_census.py da CONTA 2, NAO modificados) rodado duas vezes: "
            "uma vez sobre um worktree temporario da MAIN pura "
            "(9f3bab41b35f0e2a5f9782583ead8e1ee7755f49) e uma vez sobre esta "
            "branch (CR-BLOCK-01 + ferramentas da CONTA 2 mescladas). "
            "'_tgd' = so' o projeto principal (torre_easy_lo_r00_tgd, 167 "
            "paredes). '_aggregate' = soma dos 3 projetos de benchmark "
            "(piloto_sintetico_2x2 + torre_easy_lo_r00_tgd + "
            "torre_easy_lo_r00_tp1 = 275 paredes), na MESMA granularidade "
            "que a CONTA 1 reportou no PROJECT_STATUS.md (para permitir "
            "comparacao direta) - recalculado aqui de forma independente, "
            "nao copiado do relato dela."
        ),
        "projects": {"primary_detail": PRIMARY, "aggregate": list(main_data["per_project"].keys())},

        "total_pieces": {
            "_tgd": _delta(m_cov["performance"]["total_materialized_pieces"],
                           b_cov["performance"]["total_materialized_pieces"]),
            "_aggregate": _delta(magg["n_pieces_total"], bagg["n_pieces_total"]),
        },
        "walls_modulated": {
            "_tgd": _delta(mp["run_data_summary"]["n_walls"] - m_cov["walls_not_modulated_at_all"],
                           bp["run_data_summary"]["n_walls"] - b_cov["walls_not_modulated_at_all"]),
            "_aggregate": _delta(magg["n_walls_total"] - magg["walls_not_modulated_total"],
                                 bagg["n_walls_total"] - bagg["walls_not_modulated_total"]),
        },
        "walls_not_modulated": {
            "_tgd": _delta(m_cov["walls_not_modulated_at_all"], b_cov["walls_not_modulated_at_all"]),
            "_aggregate": _delta(magg["walls_not_modulated_total"], bagg["walls_not_modulated_total"]),
            "cause_ranking_tgd": {"MAIN": m_cov["cause_ranking"], "CR_BLOCK_01": b_cov["cause_ranking"]},
        },
        "non_modular_segments": {
            "_tgd": _delta(m_op["solver_reported"]["non_modular_segments"],
                           b_op["solver_reported"]["non_modular_segments"]),
            "_aggregate": _delta(magg["non_modular_segments_total"], bagg["non_modular_segments_total"]),
        },

        "prism": {
            "pairs_of_consecutive_courses_measured": {
                "_tgd": _delta(m_cb["pairs_of_consecutive_courses_measured"],
                               b_cb["pairs_of_consecutive_courses_measured"]),
                "_aggregate": _delta(magg["prism_pairs_measured_total"], bagg["prism_pairs_measured_total"]),
            },
            "suspect_continuous_vertical_joint": {
                "_tgd": _delta(m_cb["joint_coincidence"]["suspect_continuous_vertical_joint"],
                               b_cb["joint_coincidence"]["suspect_continuous_vertical_joint"]),
                "_aggregate": _delta(magg["prism_suspect_continuous_vertical_joint_total"],
                                     bagg["prism_suspect_continuous_vertical_joint_total"]),
            },
            "walls_with_suspect_continuous_joint_tgd": _delta(
                m_cb["walls_with_suspect_continuous_joint"], b_cb["walls_with_suspect_continuous_joint"]),
            "stagger_cm_tgd": {
                "min": {"MAIN": m_cb["stagger_cm_summary"]["min"], "CR_BLOCK_01": b_cb["stagger_cm_summary"]["min"]},
                "mean": {"MAIN": m_cb["stagger_cm_summary"]["mean"], "CR_BLOCK_01": b_cb["stagger_cm_summary"]["mean"]},
                "median": {"MAIN": m_cb["stagger_cm_summary"]["median"], "CR_BLOCK_01": b_cb["stagger_cm_summary"]["median"]},
            },
            "stagger_distribution_cm_tgd": {
                bucket: _delta(m_cb["stagger_cm_summary"]["histogram_cm"].get(bucket, 0),
                               b_cb["stagger_cm_summary"]["histogram_cm"].get(bucket, 0))
                for bucket in ("0-1", "1-3", "3-10", "10-20", ">20")
            },
            "node_conflict_breakdown_proxy_for_UNCLASSIFIED_RULE_CONFLICT_aggregate": {
                "note": ("proxy INDEPENDENTE (nao a categoria da CONTA 1) - "
                         "coincidencias que tocam pelo menos 1 peca de no' "
                         "L/T/X, medidas com a MESMA deteccao/tolerancia do "
                         "censo original de prisma"),
                "total_suspect_recount": _delta(node_main["aggregate_total_suspect"],
                                                node_b01["aggregate_total_suspect"]),
                "touching_L": _delta(node_main["aggregate_breakdown"]["L"], node_b01["aggregate_breakdown"]["L"]),
                "touching_T": _delta(node_main["aggregate_breakdown"]["T"], node_b01["aggregate_breakdown"]["T"]),
                "touching_X": _delta(node_main["aggregate_breakdown"]["X"], node_b01["aggregate_breakdown"]["X"]),
                "touching_any_node_L_T_X": _delta(
                    sum(node_main["aggregate_breakdown"][k] for k in "LTX"),
                    sum(node_b01["aggregate_breakdown"][k] for k in "LTX")),
                "near_opening_jamb_no_node": _delta(node_main["aggregate_breakdown"]["OPENING_JAMB"],
                                                    node_b01["aggregate_breakdown"]["OPENING_JAMB"]),
                "other_no_node_no_opening": _delta(node_main["aggregate_breakdown"]["OTHER_NONE"],
                                                   node_b01["aggregate_breakdown"]["OTHER_NONE"]),
            },
        },

        "c09": {
            "total": {"_tgd": _delta(m_sb["C09"]["total"], b_sb["C09"]["total"]),
                      "_aggregate": _delta(magg["c09_total"], bagg["c09_total"])},
            "sequences_2plus": {"_tgd": _delta(m_sb["C09"]["consecutive_2plus_runs"], b_sb["C09"]["consecutive_2plus_runs"]),
                                "_aggregate": _delta(magg["c09_runs2plus_total"], bagg["c09_runs2plus_total"])},
            "sequences_2plus_mid_wall_fill_only_tgd": _delta(
                m_sb["C09"]["consecutive_runs_mid_wall_fill_only"], b_sb["C09"]["consecutive_runs_mid_wall_fill_only"]),
            "vertical_strips_tgd": _delta(m_sb["C09"]["vertical_strips_total_found"], b_sb["C09"]["vertical_strips_total_found"]),
        },
        "c04": {
            "total": {"_tgd": _delta(m_sb["C04"]["total"], b_sb["C04"]["total"]),
                      "_aggregate": _delta(magg["c04_total"], bagg["c04_total"])},
            "sequences_2plus": {"_tgd": _delta(m_sb["C04"]["consecutive_2plus_runs"], b_sb["C04"]["consecutive_2plus_runs"]),
                                "_aggregate": _delta(magg["c04_runs2plus_total"], bagg["c04_runs2plus_total"])},
            "sequences_2plus_mid_wall_fill_only_tgd": _delta(
                m_sb["C04"]["consecutive_runs_mid_wall_fill_only"], b_sb["C04"]["consecutive_runs_mid_wall_fill_only"]),
            "vertical_strips_tgd": _delta(m_sb["C04"]["vertical_strips_total_found"], b_sb["C04"]["vertical_strips_total_found"]),
        },

        "b19": {
            "total": {"_tgd": _delta(m_sb["B19"]["total"], b_sb["B19"]["total"]),
                      "_aggregate": _delta(magg["b19_total"], bagg["b19_total"])},
            "location_breakdown_tgd_note": "borda do BLOCO (nao centro) a <=5cm de abertura/ponta",
            "mid_wall_far_from_any_edge": _delta(b19_main["location_breakdown"]["MID_WALL"],
                                                 b19_b01["location_breakdown"]["MID_WALL"]),
            "near_opening": _delta(b19_main["location_breakdown"]["NEAR_OPENING"],
                                   b19_b01["location_breakdown"]["NEAR_OPENING"]),
            "near_wall_end": _delta(b19_main["location_breakdown"]["NEAR_WALL_END"],
                                    b19_b01["location_breakdown"]["NEAR_WALL_END"]),
            "vertical_alignment_clusters_2plus_courses": _delta(
                b19_main["vertical_alignment_clusters_2plus_courses"],
                b19_b01["vertical_alignment_clusters_2plus_courses"]),
        },

        "l_corner_tgd": {
            "total": {"MAIN": m_ix["L_CORNER"]["total_nodes"], "CR_BLOCK_01": b_ix["L_CORNER"]["total_nodes"]},
            "valid_true": _delta(m_ix["L_CORNER"]["classified"]["TRUE"], b_ix["L_CORNER"]["classified"]["TRUE"]),
            "failures_unique_nodes": _delta(m_ix["L_CORNER"]["unique_nodes_with_failure"],
                                            b_ix["L_CORNER"]["unique_nodes_with_failure"]),
        },
        "t_intersection_tgd": {
            "total": {"MAIN": m_ix["T_INTERSECTION"]["total_nodes"], "CR_BLOCK_01": b_ix["T_INTERSECTION"]["total_nodes"]},
            "valid_true": _delta(m_ix["T_INTERSECTION"]["classified"]["TRUE"], b_ix["T_INTERSECTION"]["classified"]["TRUE"]),
            "valid_degraded": _delta(m_ix["T_INTERSECTION"]["classified"]["DEGRADED"], b_ix["T_INTERSECTION"]["classified"]["DEGRADED"]),
            "failures_unique_nodes": _delta(m_ix["T_INTERSECTION"]["unique_nodes_with_failure"],
                                            b_ix["T_INTERSECTION"]["unique_nodes_with_failure"]),
        },
        "x_intersection_tgd": {
            "total": {"MAIN": m_ix["X_INTERSECTION"]["total_nodes"], "CR_BLOCK_01": b_ix["X_INTERSECTION"]["total_nodes"]},
            "valid_true": _delta(m_ix["X_INTERSECTION"]["classified"]["TRUE"], b_ix["X_INTERSECTION"]["classified"]["TRUE"]),
            "failures_unique_nodes": _delta(m_ix["X_INTERSECTION"]["unique_nodes_with_failure"],
                                            b_ix["X_INTERSECTION"]["unique_nodes_with_failure"]),
        },

        "openings": {
            "blocks_inside_opening_tgd": _delta(
                m_op["block_extent_vs_opening_own_measurement"]["classification_counts"]["DENTRO"],
                b_op["block_extent_vs_opening_own_measurement"]["classification_counts"]["DENTRO"]),
            "blocks_partial_opening_tgd": _delta(
                m_op["block_extent_vs_opening_own_measurement"]["classification_counts"]["PARCIAL"],
                b_op["block_extent_vs_opening_own_measurement"]["classification_counts"]["PARCIAL"]),
            "door_void_violations": {
                "_tgd": _delta(m_op["solver_reported"]["door_void_violations"], b_op["solver_reported"]["door_void_violations"]),
                "_aggregate": _delta(magg["door_void_violations_total"], bagg["door_void_violations_total"]),
            },
            "alignment_conflicts": {
                "_tgd": _delta(m_op["solver_reported"]["alignment_conflicts"], b_op["solver_reported"]["alignment_conflicts"]),
                "_aggregate": _delta(magg["alignment_conflicts_total"], bagg["alignment_conflicts_total"]),
            },
            "jamb_exceptions": {
                "_tgd": _delta(m_op["solver_reported"]["jamb_exceptions"], b_op["solver_reported"]["jamb_exceptions"]),
                "_aggregate": _delta(magg["jamb_exceptions_total"], bagg["jamb_exceptions_total"]),
            },
        },

        "collisions": {
            "_tgd": _delta(m_ix["_meta"]["total_collisions"], b_ix["_meta"]["total_collisions"]),
            "_aggregate": _delta(magg["collisions_total"], bagg["collisions_total"]),
        },
        "intersection_failures_raw_entries": {
            "_tgd": _delta(m_ix["_meta"]["total_intersection_failures"], b_ix["_meta"]["total_intersection_failures"]),
            "_aggregate": _delta(magg["intersection_failures_total"], bagg["intersection_failures_total"]),
        },

        "runtime_tgd_solver_seconds": _delta(m_cov["performance"]["solver_elapsed_s"],
                                             b_cov["performance"]["solver_elapsed_s"]),

        "determinism": {
            "distinct_fingerprints_8_runs": {
                "MAIN": main_data["determinism_primary_project"]["distinct_fingerprints"],
                "CR_BLOCK_01": b01_data["determinism_primary_project"]["distinct_fingerprints"],
            },
            "pieces_spread_across_8_runs_tgd": {
                "MAIN": (max(r["n_pieces"] for r in main_data["determinism_primary_project"]["runs"])
                         - min(r["n_pieces"] for r in main_data["determinism_primary_project"]["runs"])),
                "CR_BLOCK_01": (max(r["n_pieces"] for r in b01_data["determinism_primary_project"]["runs"])
                               - min(r["n_pieces"] for r in b01_data["determinism_primary_project"]["runs"])),
            },
            "runs_detail": {
                "MAIN": [{"name": r["name"], "n_pieces": r["n_pieces"], "fingerprint16": r["fingerprint"][:16]}
                         for r in main_data["determinism_primary_project"]["runs"]],
                "CR_BLOCK_01": [{"name": r["name"], "n_pieces": r["n_pieces"], "fingerprint16": r["fingerprint"][:16]}
                               for r in b01_data["determinism_primary_project"]["runs"]],
            },
            "verdict": "NEUTRA - mesmo numero de fingerprints distintos (8/8) e mesma amplitude de variacao "
                       "de pecas (130 em ambas); CR-BLOCK-01 nao mexeu em build_wall_graph/extend_wall_ends_to_junctions "
                       "(a camada onde a maior parte da divergencia nasce, ver docs/BLOCK_MODULATION_AUDIT.md secao 14) "
                       "e nao piorou nem melhorou a sensibilidade a ordem.",
        },
    }
    with open(os.path.join(HERE, "compare_main_vs_block01.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("compare_main_vs_block01.json escrito.")


if __name__ == "__main__":
    main()
