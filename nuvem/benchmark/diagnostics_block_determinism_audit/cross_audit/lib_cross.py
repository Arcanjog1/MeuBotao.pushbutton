# -*- coding: utf-8 -*-
"""Utilitários específicos do CROSS-AUDIT — reusa `lib_det`/`oracle`/
`variants` do diretório-pai sem duplicá-los. Contém só o que a fase de
cross-audit precisa e que o baseline não tinha (ex.: uma versão CANÔNICA
de `wall_end_to_node`, que a original de `lib_det.py` não é — ver
`docs/BLOCK_DETERMINISM_CROSS_AUDIT.md`, seção 'wall_end_to_node')."""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

import lib_det as L  # noqa: E402


def canonical_wall_end_to_node(run_data):
    """Versão CANÔNICA de `lib_det.layer_wall_end_to_node`.

    A original usa `end_index` CRU (literalmente GetEndPoint(0)/(1)) — que
    por definição TROCA de valor quando o sentido de desenho de uma parede
    é invertido (`endpoint_reversal`). Comparar `end_index` cru entre um
    caso A→B e o mesmo caso B→A dá "divergência" mesmo que o grafo esteja
    perfeitamente correto e estável — é um artefato da métrica, não do
    motor. Esta versão identifica cada ponta pelo PONTO CANÔNICO da
    própria parede (`lo`/`hi` de `wall_geom_key`, independente de qual
    `end_index` ele tem hoje), então SÓ diverge se a ponta LO (ou HI) da
    parede aponta para um nó geometricamente diferente — o que é, de
    fato, um bug."""
    walls = run_data["walls_to_create"]
    rows = []
    for node in run_data["nodes"]:
        point = L.node_point_key(node)
        for wall_idx, end_index in (node.get("arms") or []):
            p0, p1, _length, _thick = L.wall_axis(walls, wall_idx)
            lo, hi = sorted([p0, p1])
            this_end = p0 if end_index == 0 else p1
            canonical_end = "lo" if this_end == lo else "hi"
            rows.append((L.wall_geom_key(walls, wall_idx), canonical_end, point))
    rows.sort()
    import hashlib
    import json
    blob = json.dumps(rows, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest(), rows
