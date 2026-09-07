# -*- coding: utf-8 -*-
"""CR-B / §6: uma mudanca de WALL_SPLIT_GAP_CM consegue separar os 19?

Mede o vazio que `split_axis_into_walls` REALMENTE ve' em cada um dos 19
(uniao de todas as fiadas do GRUPO DE EIXO, nao do host) e confronta com
as larguras de abertura MEDIDAS no Revit (TGD, `confidence=measured`).

Se as duas populacoes se sobrepoem, nenhum limiar global separa os 19 sem
destruir porta medida real -> a decisao NAO pode ser uma constante.

READ-ONLY. Nao altera nenhuma constante; le' os valores de producao.
"""
import collections
import json
import os
import sys

ROOT = os.environ.get("REPO_ROOT", "/home/user/MeuBotao.pushbutton")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from nuvem.benchmark.extract import reconstruct  # noqa: E402


def main():
    print("constantes de producao (LIDAS, nao alteradas):")
    print("  WALL_SPLIT_GAP_CM = %.1f" % reconstruct.WALL_SPLIT_GAP_CM)
    print("  AXIS_OFFSET_TOLERANCE_CM = %.1f" % reconstruct.AXIS_OFFSET_TOLERANCE_CM)
    print("  MIN_WALL_LENGTH_CM = %.1f" % reconstruct.MIN_WALL_LENGTH_CM)
    print()

    out = {}
    for proj in ["torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"]:
        ref = json.load(open(os.path.join(
            ROOT, "nuvem/benchmark/projects", proj, "reference.json"),
            encoding="utf-8"))
        repro = json.load(open(os.path.join(
            ROOT, "nuvem/benchmark/future_cr_preparation",
            "bench_opening_reconstruction_a/repro_envelope.json"),
            encoding="utf-8"))[proj]
        walls = {w["id"]: w for w in ref["walls"]}

        # vazio visto pelo SPLIT: uniao das fiadas do PROPRIO host
        # (o grupo de eixo do host; blocos de outras paredes ficam noutro
        # grupo por afastamento perpendicular > AXIS_OFFSET_TOLERANCE_CM)
        vazio_dos_19, vazio_dos_demais = [], []
        for rec in repro["runs"]:
            host = walls[rec["wall"]]
            segs = []
            for row in host.get("rows") or []:
                for b in row.get("blocks") or []:
                    segs.append((b["t_start_cm"], b["t_end_cm"]))
            segs.sort()
            merged = []
            for s, e in segs:
                if merged and s <= merged[-1][1] + 1e-9:
                    merged[-1][1] = max(merged[-1][1], e)
                else:
                    merged.append([s, e])
            # o SPLIT enxerga a UNIAO de todas as fiadas: para janela (com
            # peitoril e verga) essa uniao nao tem vazio nenhum e a parede
            # nunca e' quebrada. So' vao de altura PLENA chega ao limiar.
            cons = rec["consenso"]
            meio = (cons[0] + cons[1]) / 2.0
            vazio = 0.0
            for a, b in zip(merged, merged[1:]):
                if a[1] <= meio <= b[0]:
                    vazio = b[0] - a[1]
                    break
            alvo = (vazio_dos_19 if (rec["spread_inicio"] >= 14.9
                                     and rec["spread_fim"] >= 14.9)
                    else vazio_dos_demais)
            alvo.append(round(vazio, 2))

        larguras_medidas = []
        inp = json.load(open(os.path.join(
            ROOT, "nuvem/benchmark/projects", proj, "input.json"), encoding="utf-8"))
        for w in inp["walls"]:
            for o in w.get("openings") or []:
                if o.get("confidence") == "measured":
                    larguras_medidas.append(round(o["width_cm"], 1))

        print("=" * 88)
        print(proj)
        print("  vazio (uniao de fiadas) dos 19    : min=%.1f  max=%.1f  %s"
              % (min(vazio_dos_19), max(vazio_dos_19),
                 dict(sorted(collections.Counter(vazio_dos_19).items()))))
        print("  vazio (uniao de fiadas) dos demais: min=%.1f  max=%.1f  n=%d"
              % (min(vazio_dos_demais), max(vazio_dos_demais), len(vazio_dos_demais)))
        if larguras_medidas:
            print("  larguras MEDIDAS no Revit (n=%d)   : min=%.1f  max=%.1f"
                  % (len(larguras_medidas), min(larguras_medidas), max(larguras_medidas)))
            colisao = [v for v in vazio_dos_19
                       if any(abs(v - L) <= 1.0 for L in larguras_medidas)]
            print("  >> vazios dos 19 que COINCIDEM com largura medida real: %d de %d  %s"
                  % (len(colisao), len(vazio_dos_19),
                     sorted(set(colisao))))
            acima = [L for L in larguras_medidas if L >= min(vazio_dos_19)]
            print("  >> aberturas MEDIDAS que um limiar de %.0fcm tambem quebraria: %d de %d"
                  % (min(vazio_dos_19), len(acima), len(larguras_medidas)))
        else:
            print("  larguras MEDIDAS no Revit         : NENHUMA (input reconstruido)")
        out[proj] = {
            "vazio_dos_19": sorted(vazio_dos_19),
            "vazio_dos_demais_min": min(vazio_dos_demais),
            "vazio_dos_demais_max": max(vazio_dos_demais),
            "larguras_measured": sorted(larguras_medidas),
        }
    p = os.path.join(HERE, "split_threshold_probe.json")
    json.dump(out, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False,
              sort_keys=True)
    print("escrito:", p)


if __name__ == "__main__":
    main()
