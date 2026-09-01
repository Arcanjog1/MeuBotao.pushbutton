# -*- coding: utf-8 -*-
"""ETAPA 2D (laboratorio) - DIAGNOSTICO VISUAL DA `W097`.

SOMENTE LEITURA de `nuvem/core/**`. Nenhuma funcao do motor e' alterada nem
reimplementada: a geometria desenhada aqui e' EXATAMENTE a que o solver
carrega, mescla, pareia e deduplica (via `diagnostics_2f/lib2f.py`, que
importa o motor ao vivo por `solver_bridge.engine()`).

Gera:
  nuvem/benchmark/diagnostics_2d/w097_geometry.png       visao local + contexto
  nuvem/benchmark/diagnostics_2d/w097_geometry_zoom.png  zoom da W097

    pip install matplotlib
    python3 nuvem/benchmark/diagnostics_2d/render_w097.py
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "diagnostics_2f"))

import lib2f as L  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

ALVO = "W097"          # parede do gabarito sob investigacao
BANDA_EIXO_CM = 0.5    # tolerancia de "eixo correto" usada pelo benchmark

C_REF = "#1f4fd8"      # gabarito / eixo esperado
C_REC = "#0f9d58"      # parede recuperavel (removida hoje)
C_AUX = "#d81b1b"      # linha auxiliar / eixo espurio (mantido hoje)
C_FACE = "#e07b00"     # faces do CAD que formaram o par
C_CAD = "#9aa0a6"      # demais segmentos crus do CAD


# --------------------------------------------------------------------------
# COLETA - tudo vem do motor
# --------------------------------------------------------------------------
class Espiao(object):
    """Registra (face_a, face_b, eixo) de cada par que `find_wall_pairs`
    aceitou, embrulhando `create_centerline` no dict de globais do modulo
    (mesma tecnica das etapas 2G/2I). Nenhum arquivo e' tocado."""

    def __init__(self, mod):
        self.g = mod.find_wall_pairs.__globals__
        self.registros = []

    def __enter__(self):
        real = self.g["create_centerline"]
        self.old = real

        def wrapper(l1, l2, ext):
            out = real(l1, l2, ext)
            if out is not None:
                self.registros.append((l1, l2, out))
            return out

        self.g["create_centerline"] = wrapper
        return self

    def __exit__(self, *a):
        self.g["create_centerline"] = self.old
        return False


def xy(line):
    p0, p1 = line.GetEndPoint(0), line.GetEndPoint(1)
    return (L.cm(p0.X), L.cm(p0.Y), L.cm(p1.X), L.cm(p1.Y))


def comprimento(line):
    x0, y0, x1, y1 = xy(line)
    return math.hypot(x1 - x0, y1 - y0)


def angulo(line):
    x0, y0, x1, y1 = xy(line)
    return math.degrees(math.atan2(y1 - y0, x1 - x0)) % 180.0


def faces_do_eixo(eixo, registros):
    """As duas linhas do CAD (ja' mescladas) que geraram este eixo."""
    A = L.Ax(*xy(eixo))
    melhor, melhor_erro = None, None
    for l1, l2, out in registros:
        B = L.Ax(*xy(out))
        if L.adiff(A.a, B.a) > 0.2:
            continue
        mx, my = (A.x0 + A.x1) / 2.0, (A.y0 + A.y1) / 2.0
        erro = abs(B.perp(mx, my))
        if erro > 1.0:
            continue
        if melhor_erro is None or erro < melhor_erro:
            melhor, melhor_erro = (l1, l2), erro
    return melhor


def coleta():
    S = L.load()
    mod = S["mod"]
    merged, _dt = L.run_merge(S["lines"])

    with Espiao(mod) as esp:
        walls, _unused, _diag, _t = L.run_pairs(merged)
    registros = esp.registros

    # --- deduplicate_walls REPRODUZIDO com instrumentacao. Os predicados,
    # a ordenacao (mais longa primeiro) e a politica sao os do motor - so'
    # se registra QUEM removeu QUEM.
    ordem = sorted(range(len(walls)),
                   key=lambda k: -comprimento(walls[k][0]))
    mantidos, removidos = [], {}
    for k in ordem:
        line, th, _lk = walls[k]
        dup = None
        for kk in mantidos:
            kline, kth, _ = walls[kk]
            if abs(th - kth) > mod.WALL_THICKNESS_MATCH_TOLERANCE_FT:
                continue
            if not mod.are_lines_parallel(line, kline):
                continue
            if not mod.symmetric_lines_within_distance(
                    line, kline, mod.DUPLICATE_AXIS_TOLERANCE_FT):
                continue
            if not mod.lines_overlap_enough(line, kline):
                continue
            dup = kk
            break
        if dup is None:
            mantidos.append(k)
        else:
            removidos.setdefault(dup, []).append(k)

    ref = {w["id"]: w for w in S["ref"]["walls"]}[ALVO]
    A = L.Ax(ref["start_cm"][0], ref["start_cm"][1],
             ref["end_cm"][0], ref["end_cm"][1])

    # a parede REMOVIDA que mais cobre a W097 (sem citar indice nenhum)
    alvo_idx, alvo_cob, alvo_rep = None, -1.0, None
    for rep, membros in removidos.items():
        for k in membros:
            c = L.coverage(A, [xy(walls[k][0])])
            if c > alvo_cob:
                alvo_idx, alvo_cob, alvo_rep = k, c, rep

    return dict(S=S, mod=mod, merged=merged, walls=walls, registros=registros,
                mantidos=mantidos, removidos=removidos, ref=ref, A=A,
                rec_idx=alvo_idx, rec_cob=alvo_cob, rep_idx=alvo_rep)


# --------------------------------------------------------------------------
# DESENHO
# --------------------------------------------------------------------------
def seg(ax, line, **kw):
    x0, y0, x1, y1 = xy(line)
    ax.plot([x0, x1], [y0, y1], **kw)


def pontas(ax, line, cor, tam=55):
    x0, y0, x1, y1 = xy(line)
    ax.plot([x0, x1], [y0, y1], linestyle="none", marker="+",
            markersize=math.sqrt(tam), markeredgewidth=1.3, color=cor,
            zorder=9)


def desenha(D, caminho, xlim, ylim, titulo, zoom, caixa=(0.006, 0.02),
            caixa_va="bottom", frac_esp=0.02, zoom_box=None):
    S, walls = D["S"], D["walls"]
    rec = walls[D["rec_idx"]]
    esp_ = walls[D["rep_idx"]]
    ref = D["ref"]

    th_rec = L.cm(rec[1])
    y_ref = ref["start_cm"][1]
    xr0, xr1 = ref["start_cm"][0], ref["end_cm"][0]
    rx0, ry0, rx1, ry1 = xy(rec[0])
    y_rec = (ry0 + ry1) / 2.0

    fig, ax = plt.subplots(figsize=(22, 9) if zoom else (24, 7))

    # ---- 8. todos os segmentos crus do CAD na janela ---------------------
    n_cad = 0
    for l in S["lines"]:
        x0, y0, x1, y1 = xy(l)
        if max(x0, x1) < xlim[0] or min(x0, x1) > xlim[1]:
            continue
        if max(y0, y1) < ylim[0] or min(y0, y1) > ylim[1]:
            continue
        ax.plot([x0, x1], [y0, y1], color=C_CAD, lw=0.9, zorder=2)
        ax.plot([x0, x1], [y0, y1], linestyle="none", marker="+",
                markersize=4.5, markeredgewidth=0.8, color=C_CAD, zorder=3)
        n_cad += 1

    # ---- 1. W097 esperada: corpo de 14 cm + eixo -------------------------
    th_ref = ref["thickness_cm"]
    ax.add_patch(Rectangle((xr0, y_ref - th_ref / 2.0), xr1 - xr0, th_ref,
                           facecolor=C_REF, alpha=0.10, edgecolor=C_REF,
                           lw=1.2, linestyle=":", zorder=1))
    # ---- 12. banda de tolerancia de eixo (<= 0,5 cm) ---------------------
    ax.add_patch(Rectangle((xr0, y_ref - BANDA_EIXO_CM), xr1 - xr0,
                           2 * BANDA_EIXO_CM, facecolor=C_REF, alpha=0.30,
                           edgecolor="none", zorder=4))
    # ---- 3. eixo esperado -----------------------------------------------
    ax.plot([xr0, xr1], [y_ref, y_ref], color=C_REF, lw=2.2, ls="--", zorder=6)

    # ---- 6. as duas faces do CAD que formaram a parede recuperada --------
    faces = faces_do_eixo(rec[0], D["registros"])
    if faces:
        for f in faces:
            seg(ax, f, color=C_FACE, lw=3.4, solid_capstyle="butt", zorder=7)
            pontas(ax, f, C_FACE)

    # ---- 7. linha auxiliar de 43,9 m e o eixo espurio --------------------
    faces_esp = faces_do_eixo(esp_[0], D["registros"])
    aux = None
    if faces_esp:
        aux = max(faces_esp, key=comprimento)
        curta = min(faces_esp, key=comprimento)
        seg(ax, aux, color=C_AUX, lw=2.0, ls=(0, (7, 4)), zorder=7)
        pontas(ax, aux, C_AUX)
        seg(ax, curta, color=C_AUX, lw=3.0, alpha=0.55, zorder=7)
        pontas(ax, curta, C_AUX)
    seg(ax, esp_[0], color=C_AUX, lw=2.6, zorder=8)

    # ---- 2/4. parede recuperada (removida hoje) e seu eixo ---------------
    ax.add_patch(Rectangle((min(rx0, rx1), y_rec - th_rec / 2.0),
                           abs(rx1 - rx0), th_rec, facecolor=C_REC,
                           alpha=0.12, edgecolor=C_REC, lw=1.0, zorder=5))
    ax.plot([rx0, rx1], [ry0, ry1], color=C_REC, lw=3.2, zorder=9)
    pontas(ax, rec[0], C_REC, 90)

    # ---- 5. cota do delta de eixo ---------------------------------------
    xc = (max(xr0, xlim[0]) + min(xr1, xlim[1])) / 2.0
    ax.annotate("", xy=(xc, y_ref), xytext=(xc, y_rec),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.6),
                zorder=11)
    ax.text(xc + (xlim[1] - xlim[0]) * 0.006, (y_ref + y_rec) / 2.0,
            u"Δ eixo = %.3f cm" % abs(y_ref - y_rec), fontsize=13,
            fontweight="bold", va="center", zorder=12,
            bbox=dict(fc="white", ec="black", alpha=0.9, pad=2))

    # ---- rotulos diretos na imagem --------------------------------------
    def rot(x, y, txt, cor, va="bottom"):
        ax.text(x, y, txt, color=cor, fontsize=11, fontweight="bold",
                va=va, zorder=12,
                bbox=dict(fc="white", ec=cor, alpha=0.88, pad=2))

    rot(xr0 + (xr1 - xr0) * 0.62, y_ref + 0.35,
        u"W097 esperada\ny = %.3f  (esp. %.1f cm)" % (y_ref, th_ref), C_REF)
    rot(min(rx0, rx1) + 6, y_rec - 0.45,
        u"Recuperada (REMOVIDA hoje pelo dedup)\ny = %.3f  |  %.2f cm  |  esp. %.1f cm"
        % (y_rec, comprimento(rec[0]), th_rec), C_REC, va="top")
    if faces:
        for f in faces:
            fx0, fy0, fx1, fy1 = xy(f)
            rot(min(fx0, fx1) + 4, (fy0 + fy1) / 2.0 + 0.2,
                u"face CAD  y = %.3f  (%.2f cm)" % ((fy0 + fy1) / 2.0,
                                                    comprimento(f)), C_FACE)
    ex0, ey0, ex1, ey1 = xy(esp_[0])
    xe = xlim[0] + (xlim[1] - xlim[0]) * frac_esp
    ye = ey0 + (ey1 - ey0) * ((xe - ex0) / (ex1 - ex0)) if ex1 != ex0 else ey0
    rot(xe, ye + 0.35,
        u"MANTIDA pelo dedup: eixo espurio %.1f cm, %.4f°\n(linha auxiliar de %.2f cm)"
        % (comprimento(esp_[0]), angulo(esp_[0]),
           comprimento(aux) if aux is not None else float("nan")), C_AUX)

    # ---- caixa de medicoes ----------------------------------------------
    mod = D["mod"]
    d_mid = L.cm(max(
        mod.get_distance_between_parallel_lines(rec[0], esp_[0]),
        mod.get_distance_between_parallel_lines(esp_[0], rec[0])))
    sep = L.cm(sep_no_trecho(mod, rec[0], esp_[0]))
    tol = L.cm(mod.DUPLICATE_AXIS_TOLERANCE_FT)
    txt = (
        u"POR QUE O dedup CONFUNDE AS DUAS\n"
        u"  predicado de hoje (pontos medios)      d = %.4f cm  <= %.1f cm  -> \"duplicata\"\n"
        u"  separacao MAXIMA no trecho comum       d = %.4f cm  >  %.1f cm  -> nao e' duplicata\n"
        u"  politica: mantem a mais longa do grupo -> %.1f cm (espuria)  vence  %.1f cm (boa)\n\n"
        u"COBERTURA DE W097 PELA PAREDE REMOVIDA: %.3f\n"
        u"tolerancia de \"eixo correto\" do benchmark: <= %.1f cm (faixa azul)"
    ) % (d_mid, tol, sep, tol, comprimento(esp_[0]), comprimento(rec[0]),
         D["rec_cob"], BANDA_EIXO_CM)
    ax.text(caixa[0], caixa[1], txt, transform=ax.transAxes, fontsize=10.5,
            family="monospace", va=caixa_va, zorder=13,
            bbox=dict(fc="#fffbe6", ec="#b08900", alpha=0.95, pad=6))

    if zoom_box is not None:
        (zx0, zx1), (zy0, zy1) = zoom_box
        ax.add_patch(Rectangle((zx0, zy0), zx1 - zx0, zy1 - zy0,
                               facecolor="none", edgecolor="black",
                               lw=1.6, ls=(0, (5, 3)), zorder=10))
        ax.text(zx1 + (xlim[1] - xlim[0]) * 0.008, zy1,
                u"janela da 2a imagem\n(w097_geometry_zoom.png)",
                fontsize=10, fontweight="bold", va="top", zorder=12,
                bbox=dict(fc="white", ec="black", alpha=0.9, pad=2))

    handles = [
        Line2D([], [], color=C_REF, lw=2.2, ls="--", label=u"eixo esperado (gabarito W097)"),
        Line2D([], [], color=C_REF, lw=8, alpha=0.30, label=u"tolerancia de eixo ±0,5 cm"),
        Line2D([], [], color=C_REF, lw=8, alpha=0.10, label=u"corpo da W097 esperada (14 cm)"),
        Line2D([], [], color=C_REC, lw=3.2, label=u"parede recuperada (REMOVIDA pelo dedup)"),
        Line2D([], [], color=C_FACE, lw=3.4, label=u"faces do CAD que formaram o par"),
        Line2D([], [], color=C_AUX, lw=2.6, label=u"eixo espurio 43,9 m (MANTIDO pelo dedup)"),
        Line2D([], [], color=C_AUX, lw=2.0, ls=(0, (7, 4)), label=u"linha auxiliar do CAD (43,9 m)"),
        Line2D([], [], color=C_CAD, lw=0.9, marker="+", label=u"demais segmentos crus do CAD (%d)" % n_cad),
    ]
    ax.legend(handles=handles, loc="upper right", fontsize=10, framealpha=0.95)

    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    fx = (xlim[1] - xlim[0]) / fig.get_size_inches()[0]
    fy = (ylim[1] - ylim[0]) / fig.get_size_inches()[1]
    ax.set_title(u"%s   |   escala Y exagerada %.0fx em relacao a X "
                 u"(sem isso os 2 cm seriam invisiveis)" % (titulo, fx / fy),
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("x (cm)")
    ax.set_ylabel("y (cm)")
    ax.grid(True, ls=":", lw=0.5, alpha=0.6)
    fig.tight_layout()
    fig.savefig(caminho, dpi=110)
    plt.close(fig)
    return n_cad


def sep_no_trecho(mod, l1, l2):
    """Separacao perpendicular MAXIMA entre dois eixos, medida so' no trecho
    em que eles se sobrepoem, no referencial simetrico da bissetriz
    (`_pair_frame_cached`, do proprio motor). Diagnostico apenas."""
    c1, c2 = mod._line_geom_cache(l1), mod._line_geom_cache(l2)
    bx, by, nx, ny, ox, oy = mod._pair_frame_cached(c1, c2)

    def tp(p):
        return (bx * (p.X - ox) + by * (p.Y - oy),
                nx * (p.X - ox) + ny * (p.Y - oy))

    t0, s0 = tp(c1[0])
    t1, s1 = tp(c1[1])
    u0, r0 = tp(c2[0])
    u1, r1 = tp(c2[1])
    lo = max(min(t0, t1), min(u0, u1))
    hi = min(max(t0, t1), max(u0, u1))
    if (hi - lo) <= 1e-12:
        m1, m2 = c1[4], c2[4]
        return abs(nx * (m1.X - m2.X) + ny * (m1.Y - m2.Y))

    def sa(a, b, c, d, t):
        return b if abs(c - a) < 1e-12 else b + (d - b) * (t - a) / (c - a)

    return max(abs(sa(t0, s0, t1, s1, lo) - sa(u0, r0, u1, r1, lo)),
               abs(sa(t0, s0, t1, s1, hi) - sa(u0, r0, u1, r1, hi)))


def main():
    D = coleta()
    rec, esp_ = D["walls"][D["rec_idx"]], D["walls"][D["rep_idx"]]
    ex0, ey0, ex1, ey1 = xy(esp_[0])
    rx0, ry0, rx1, ry1 = xy(rec[0])
    ref = D["ref"]

    p1 = os.path.join(_HERE, "w097_geometry.png")
    p2 = os.path.join(_HERE, "w097_geometry_zoom.png")

    zbox = ((min(rx0, rx1) - 70, max(rx0, rx1) + 70), (802.0, 828.0))
    n1 = desenha(D, p1,
                 (min(ex0, ex1) - 120, max(ex0, ex1) + 120),
                 (min(ey0, ey1, ry0) - 14, max(ey0, ey1, ry0) + 14),
                 u"W097 - VISAO LOCAL COM CONTEXTO (a linha auxiliar de 43,9 m inteira)",
                 zoom=False, caixa=(0.006, 0.975), caixa_va="top",
                 frac_esp=0.70, zoom_box=zbox)
    n2 = desenha(D, p2,
                 (min(rx0, rx1) - 70, max(rx0, rx1) + 70),
                 (802.0, 828.0),
                 u"W097 - ZOOM: gabarito, parede recuperada, faces do CAD e o Δ de eixo",
                 zoom=True, caixa=(0.006, 0.02), caixa_va="bottom",
                 frac_esp=0.02)

    print("== ARQUIVOS ==")
    print("  %s  (%d segmentos crus na janela)" % (p1, n1))
    print("  %s  (%d segmentos crus na janela)" % (p2, n2))
    print("")
    print("== GABARITO ==")
    print("  %s  %s -> %s  len=%.2f  esp=%.1f  eixo y=%.3f"
          % (ref["id"], ref["start_cm"], ref["end_cm"], ref["length_cm"],
             ref["thickness_cm"], ref["start_cm"][1]))
    print("")
    print("== PAREDE RECUPERADA (removida hoje pelo deduplicate_walls) ==")
    print("  (%.2f, %.2f) -> (%.2f, %.2f)  len=%.2f  esp=%.1f  cobertura de %s=%.3f"
          % (rx0, ry0, rx1, ry1, comprimento(rec[0]), L.cm(rec[1]), ALVO,
             D["rec_cob"]))
    faces = faces_do_eixo(rec[0], D["registros"])
    for f in faces or []:
        fx0, fy0, fx1, fy1 = xy(f)
        print("    face CAD: (%.2f, %.3f) -> (%.2f, %.3f)  len=%.2f"
              % (fx0, fy0, fx1, fy1, comprimento(f)))
    print("")
    print("== REPRESENTANTE MANTIDO (eixo espurio) ==")
    print("  (%.2f, %.2f) -> (%.2f, %.2f)  len=%.2f  ang=%.4f graus"
          % (ex0, ey0, ex1, ey1, comprimento(esp_[0]), angulo(esp_[0])))
    for f in faces_do_eixo(esp_[0], D["registros"]) or []:
        fx0, fy0, fx1, fy1 = xy(f)
        print("    face CAD: (%.2f, %.3f) -> (%.2f, %.3f)  len=%.2f  ang=%.4f"
              % (fx0, fy0, fx1, fy1, comprimento(f), angulo(f)))
    print("")
    mod = D["mod"]
    print("== POR QUE O dedup CONFUNDE AS DUAS ==")
    print("  d pelos pontos medios (predicado de hoje) = %.4f cm  (tol %.1f cm)"
          % (L.cm(max(mod.get_distance_between_parallel_lines(rec[0], esp_[0]),
                      mod.get_distance_between_parallel_lines(esp_[0], rec[0]))),
             L.cm(mod.DUPLICATE_AXIS_TOLERANCE_FT)))
    print("  separacao MAXIMA no trecho comum          = %.4f cm  (tol %.1f cm)"
          % (L.cm(sep_no_trecho(mod, rec[0], esp_[0])),
             L.cm(mod.DUPLICATE_AXIS_TOLERANCE_FT)))


if __name__ == "__main__":
    main()
