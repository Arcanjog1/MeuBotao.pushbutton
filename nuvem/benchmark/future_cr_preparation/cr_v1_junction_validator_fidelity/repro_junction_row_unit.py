# -*- coding: utf-8 -*-
"""REPRODUTOR MINIMO - defeito de UNIDADE DE AVALIACAO em
`JUNCTION_MISSING_BINDING` / `JUNCTION_NOT_ALTERNATING`.

DIAGNOSTICO. Nao altera producao, nao corrige nada.

O QUE ELE MOSTRA
----------------
`validators/validate_junctions.py` agrupa as fiadas do no' pelo INDICE
ORDINAL `row["row"]` (`_rows_of_group` / `_covering_blocks`). O indice
ordinal e' a posicao da fiada NA PILHA DAQUELA PAREDE - nao a cota. Duas
paredes que chegam ao mesmo no' com pilhas de tamanhos diferentes (meia
fiada de peca CORTADA, base diferente) tem o MESMO indice apontando para
COTAS DIFERENTES.

Consequencia: o validador compara a fiada z=20 de uma parede com a fiada
z=10 da outra, conclui que "nenhuma parede pos peca no encontro" e emite
`JUNCTION_MISSING_BINDING` onde a alvenaria esta' perfeitamente amarrada.

Este arquivo constroi o caso minimo (duas paredes, um canto L, amarracao
alternada CORRETA) e mostra o achado falso aparecendo.

    python3 repro_junction_row_unit.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT)

from nuvem.benchmark.validators import validate_junctions as VJ  # noqa: E402

NODE = [0.0, 0.0]


def bloco(wall_id, code, x, y, z, comprimento, rot):
    return {"id": "%s-Z%03d" % (wall_id, int(z)), "wall_id": wall_id,
            "code": code, "type_name": code, "center_cm": [x, y],
            "z_cm": z, "height_cm": 19.0, "length_cm": comprimento,
            "width_cm": 14.0, "rotation_deg": rot, "role": "standard"}


def parede(wall_id, start, end, fiadas, rot, dx, dy):
    """`fiadas` = lista de (indice_ordinal, elevacao, tem_peca_no_no)."""
    rows = []
    for indice, elev, no_no in fiadas:
        blocos = []
        if no_no:
            blocos.append(bloco(wall_id, "B34", NODE[0] + dx, NODE[1] + dy, elev, 34.0, rot))
        else:                       # peca longe do no', so' para a fiada existir
            blocos.append(bloco(wall_id, "B34", NODE[0] + dx * 12, NODE[1] + dy * 12, elev, 34.0, rot))
        rows.append({"row": indice, "elevation_cm": elev, "blocks": blocos})
    return {"id": wall_id, "start_cm": start, "end_cm": end, "thickness_cm": 14.0,
            "length_cm": 400.0, "rows": rows,
            "junctions": [{"type": "L", "point_cm": list(NODE), "t_cm": 0.0,
                           "at_end": True, "neighbors": []}]}


def caso(titulo, fiadas_a, fiadas_b):
    proj = {"project_id": "repro", "schema_version": 2, "orphan_blocks": [],
            "settings": {}, "catalog": {}, "walls": [
                parede("WA", [0.0, 0.0], [400.0, 0.0], fiadas_a, 0.0, 8.0, 0.0),
                parede("WB", [0.0, 0.0], [0.0, 400.0], fiadas_b, 90.0, 0.0, 8.0)]}
    achados = []
    for grupo in VJ.collect_nodes(proj):
        achados.extend(VJ.validate_node(grupo))
    codigos = sorted(f["code"] for f in achados)
    print("  %-58s achados=%s" % (titulo, codigos or "nenhum"))
    for f in achados:
        print("      %s" % f["detail"])
    return achados


def main():
    print(__doc__.split("\n\n")[0])
    print()
    print("CASO 1 - fiadas ALINHADAS (mesmo indice = mesma cota): amarracao")
    print("         alternada correta, e o validador concorda.")
    alinhadas_a = [(0, 0.0, True), (1, 20.0, False), (2, 40.0, True)]
    alinhadas_b = [(0, 0.0, False), (1, 20.0, True), (2, 40.0, False)]
    ok = caso("L amarrado, indices alinhados", alinhadas_a, alinhadas_b)

    print()
    print("CASO 2 - MESMA alvenaria, mesma amarracao, mesmas COTAS -- mas a")
    print("         parede WB ganhou uma meia-fiada CORTADA (z=10) no meio da")
    print("         pilha, entao os indices ordinais dela deslocam em 1.")
    print("         Nenhuma peca mudou de lugar. Nenhuma cota mudou.")
    deslocadas_b = [(0, 0.0, False), (1, 10.0, False), (2, 20.0, True), (3, 40.0, False)]
    ruim = caso("L amarrado, indices deslocados por meia-fiada", alinhadas_a, deslocadas_b)

    print()
    print("=" * 78)
    print("CASO 1 (indices alinhados):   %d achado(s)" % len(ok))
    print("CASO 2 (indices deslocados):  %d achado(s)  <- FALSOS" % len(ruim))
    print()
    print("A alvenaria dos dois casos amarra igual nas cotas 0/20/40. O que")
    print("mudou foi o INDICE ORDINAL, nao a fisica. A unidade de avaliacao")
    print("correta e' a ELEVACAO (`row['elevation_cm']`), nao `row['row']`.")
    print()
    print("MEDIDO NO CORPUS REAL (CR-B, reconciliacao independente):")
    print("  - STATE_R (gabarito de hoje, SEM corte): 236 de 373 achados de")
    print("    JUNCTION_MISSING_BINDING ja' nascem de um indice ordinal que")
    print("    aponta para MAIS DE UMA cota. O defeito e' PRE-EXISTENTE.")
    print("  - trocando a unidade para ELEVACAO, o delta da CR-B cai de")
    print("    +49 para -5; na unidade estrita (cota presente em >=2 paredes")
    print("    do no') o delta e' +10, todos em nos RECEM-REGISTRADOS.")
    return 0 if ruim else 1


if __name__ == "__main__":
    sys.exit(main())
