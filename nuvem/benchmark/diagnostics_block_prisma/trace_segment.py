# -*- coding: utf-8 -*-
"""CR-BLOCK-01 - tracing de UM trecho isolado (prova por ablacao).

Mostra, para um `pier_cm` e uma lista de juntas a evitar, EXATAMENTE quais
candidatos `_pier_layout_avoiding_joints` chega a considerar e qual e' o
score de cada um. E' a prova de que a causa-raiz esta' na ENUMERACAO (o
conjunto de candidatos), nao no criterio de escolha.

    python3 nuvem/benchmark/diagnostics_block_prisma/trace_segment.py \
        --pier 99 --seg-start 35 --avoid 54.5 --avoid 94.5
"""

import argparse
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_BENCH = os.path.dirname(_HERE)
if _BENCH not in sys.path:
    sys.path.insert(0, _BENCH)

import solver_bridge  # noqa: E402


def default_catalog(module):
    """Catalogo dos 6 codigos com as dimensoes reais da familia 14x19."""
    dims = {"B39": 39.0, "B34": 34.0, "B54": 54.0, "B19": 19.0, "C09": 9.0, "C04": 4.0}
    catalog = {}
    for code, length_cm in dims.items():
        catalog[code] = {
            "symbol": None, "logical_code": code, "length_cm": length_cm,
            "height_cm": 19.0, "width_cm": 14.0, "cells_local": [],
            "is_special_bond": code in ("B34", "B54"),
            "is_compensator": code in ("C09", "C04"),
        }
    return catalog


def describe(layout):
    if layout is None:
        return "None"
    return " ".join("{0}@{1:.1f}-{2:.1f}".format(c, a, b) for c, a, b in layout)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pier", type=float, required=True)
    parser.add_argument("--seg-start", type=float, default=0.0)
    parser.add_argument("--lead", type=float, default=0.0)
    parser.add_argument("--trail", type=float, default=0.0)
    parser.add_argument("--avoid", type=float, action="append", default=[])
    parser.add_argument("--leading-open", action="store_true")
    parser.add_argument("--trailing-open", action="store_true")
    args = parser.parse_args(argv)

    module = solver_bridge.engine()
    catalog = default_catalog(module)
    seg = args.seg_start

    def score(layout):
        if layout is None:
            return None
        excess = module._layout_compensator_run_excess(layout, catalog)
        coinc = module._count_joint_coincidences_cm(
            module._layout_internal_joint_positions_cm(layout, seg), args.avoid)
        stagger = module._layout_min_joint_stagger_cm(layout, seg, args.avoid)
        return (excess, coinc, stagger)

    print("pier={0}cm seg_start={1} lead={2} trail={3} avoid={4}".format(
        args.pier, seg, args.lead, args.trail, args.avoid))

    baseline = module._pier_ordered_layout(
        args.pier, catalog, args.lead, args.trail,
        leading_open_override=args.leading_open,
        trailing_open_override=args.trailing_open)
    print("BASELINE          {0}   score={1}".format(describe(baseline), score(baseline)))

    half = module._half_block_leading_layout(
        args.pier, catalog, args.lead, args.trail, trailing_is_open=args.trailing_open)
    print("HALF_LEADING      {0}   score={1}".format(describe(half), score(half)))

    for alt in module._pier_forced_bypass_layouts(
            args.pier, catalog, args.lead, args.trail,
            leading_is_open=args.leading_open, trailing_is_open=args.trailing_open):
        print("BYPASS            {0}   score={1}".format(describe(alt), score(alt)))

    codes = module._pier_codes_by_len_desc(
        catalog, True, pool=module.OPENING_JAMB_BLOCK_CODES)
    for code in codes:
        alt = module._pier_ordered_layout(
            args.pier, catalog, args.lead, args.trail, first_code=code,
            leading_open_override=args.leading_open,
            trailing_open_override=args.trailing_open)
        print("FIRST={0:<4}         {1}   score={2}".format(code, describe(alt), score(alt)))

    chosen = module._pier_layout_avoiding_joints(
        args.pier, catalog, args.lead, args.trail, seg, args.avoid,
        leading_is_open=args.leading_open, trailing_is_open=args.trailing_open)
    print("--")
    print("ESCOLHIDO         {0}   score={1}".format(describe(chosen), score(chosen)))
    print("juntas internas   {0}".format(
        [round(x, 1) for x in module._layout_internal_joint_positions_cm(chosen, seg)]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
