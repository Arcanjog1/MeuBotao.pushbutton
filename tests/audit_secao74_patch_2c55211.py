# -*- coding: utf-8 -*-
"""Bateria adversarial independente contra o patch da SECAO 74 (2c55211).

Roda com a secao 74 OFF e ON, lado a lado, contra um oraculo fisico
recalculado do zero. Nao importa nenhuma conclusao previa: as constantes
(B54=54 -> 27 cm por lado, B34=34) sao redigitadas da fisica do bloco.

Precisa de um worktree do commit a auditar. Por padrao usa a variavel de
ambiente WT74; sem ela, o proprio repositorio:

    git worktree add /tmp/wt74 2c55211
    WT74=/tmp/wt74 python3 tests/audit_secao74_patch_2c55211.py

Relatorio: docs/AUDITORIA_SECAO_74_PATCH_2c55211.md
"""
import itertools
import math
import os
import random
import sys

WT = os.environ.get("WT74") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WT, "tests"))
os.chdir(WT)

import load_script  # noqa: E402
import revit_stubs  # noqa: E402

m = load_script.load()
ws = sys.modules["core.engine.wall_stepper"]
XYZ, Line = revit_stubs.XYZ, revit_stubs.Line
F = m.FEET_PER_METER

B54_HALF, B34 = 27.0, 34.0
FAILS = []


def ft(cm):
    return cm / 100.0 * F


def to_cm(v):
    return v / F * 100.0


def seg(x0, y0, x1, y1):
    return Line.CreateBound(XYZ(ft(x0), ft(y0), 0.0), XYZ(ft(x1), ft(y1), 0.0))


def scene(gr=200.0, gl=200.0, inc=200.0, node_x=200.0, main_len=1000.0,
          theta=0.0, ox=0.0, oy=0.0, flip_main=False, flip_inc=False, order=(0, 1)):
    c, s = math.cos(theta), math.sin(theta)
    R = lambda x, y: (ox + x * c - y * s, oy + x * s + y * c)  # noqa: E731
    x0, x1, xn, D = 0.0, main_len, node_x, 15.0
    spans = []
    if xn + gr + D <= x1:
        spans.append((xn + gr, xn + gr + D))
    if xn - gl - D >= x0:
        spans.append((xn - gl - D, xn - gl))
    if flip_main:
        pa, pb = R(x1, 0.0), R(x0, 0.0)
        tt = lambda w: x1 - w  # noqa: E731
    else:
        pa, pb = R(x0, 0.0), R(x1, 0.0)
        tt = lambda w: w - x0  # noqa: E731
    main = (seg(pa[0], pa[1], pb[0], pb[1]), ft(14.0), (False, False))
    ops = []
    for (wa, wb) in spans:
        ta, tb = sorted((tt(wa), tt(wb)))
        ops.append((ft(ta), ft(tb), ft(0.0), ft(210.0)))
    qa, qb = (R(xn, -inc), R(xn, 0.0)) if flip_inc else (R(xn, 0.0), R(xn, -inc))
    incw = (seg(qa[0], qa[1], qb[0], qb[1]), ft(14.0), (False, False))
    mi, ii = order
    W = [None, None]; W[mi], W[ii] = main, incw
    O = [None, None]; O[mi], O[ii] = ops, []
    pn = R(xn, 0.0)
    node = {"point": XYZ(ft(pn[0]), ft(pn[1]), 0.0),
            "main_wall_idx": mi, "incoming_wall_idx": ii}
    return node, W, O


def ok(flag, **kw):
    ws.T_ROOM_PHYSICAL_TOLERANCE = flag
    n, W, O = scene(**kw)
    try:
        return ws._t_intersection_room_ok(n, W, O)
    finally:
        ws.T_ROOM_PHYSICAL_TOLERANCE = False


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + ("  " + detail if not cond else ""))
    if not cond:
        FAILS.append((name, detail))


# ---------------------------------------------- A. a flag e o valor
print("[A] mecanica da flag")
ws.T_ROOM_PHYSICAL_TOLERANCE = False
tol_off = ws._t_intersection_room_tolerance_ft()
ws.T_ROOM_PHYSICAL_TOLERANCE = True
tol_on = ws._t_intersection_room_tolerance_ft()
ws.T_ROOM_PHYSICAL_TOLERANCE = False
check("padrao da flag e' False", ws.T_ROOM_PHYSICAL_TOLERANCE is False)
check("OFF devolve exatamente 1e-6 pes", tol_off == 1e-6, repr(tol_off))
check("ON devolve 0,05 cm em pes", abs(to_cm(tol_on) - 0.05) < 1e-12,
      "%.6e cm" % to_cm(tol_on))
check("ON == PIER_PHYSICAL_FIT_TOLERANCE_CM convertida",
      tol_on == m.PIER_PHYSICAL_FIT_TOLERANCE_CM / 100.0 * F)
print("     OFF = %.6e cm   ON = %.6e cm   razao = %.0fx"
      % (to_cm(tol_off), to_cm(tol_on), to_cm(tol_on) / to_cm(tol_off)))

# ---------------------------------------------- item 6. sweep de fronteiras
print("\n[6] fronteiras pedidas (falta de espaco no lado do B54)")
VALORES = [0.0, 0.001, 0.0035, 0.01, 0.012, 0.02, 0.049, 0.050, 0.051,
           0.10, 0.30, 1.00, 4.001]
print("  %-14s %10s %10s  %s" % ("falta (cm)", "OFF", "ON", "divergem?"))
print("  " + "-" * 52)
divergem = []
for v in VALORES:
    a, b = ok(False, gr=B54_HALF - v), ok(True, gr=B54_HALF - v)
    if a != b:
        divergem.append(v)
    print("  %-14.4f %10s %10s  %s" % (v, a, b, "SIM" if a != b else ""))
print("\n  divergem em: %r" % divergem)
check("as faltas REAIS (>= 0,10 cm) nao divergem",
      all(v < 0.10 for v in divergem), "divergiu em %r" % [v for v in divergem if v >= 0.10])
check("4,001 cm reprova nos DOIS", ok(False, gr=B54_HALF - 4.001) is False
      and ok(True, gr=B54_HALF - 4.001) is False)

# ---------------------------------------------- item 5. 4, 15, 20 cm
print("\n[5] faltas fisicas reais, OFF e ON")
for falta in (4.0, 15.0, 20.0):
    for eixo, base in (("gr", B54_HALF), ("gl", B54_HALF), ("inc", B34)):
        a = ok(False, **{eixo: base - falta})
        b = ok(True, **{eixo: base - falta})
        check("falta de %g cm em %s reprova OFF e ON" % (falta, eixo),
              a is False and b is False, "OFF=%r ON=%r" % (a, b))

# ---------------------------------------------- item 7. saturacao da GUARDA
print("\n[7] saturacao no nivel da guarda: 0,05 / 0,10 / 0,30 cm")
import core.engine.modulation_math as mm  # noqa: E402
orig = mm.PIER_PHYSICAL_FIT_TOLERANCE_CM
orig_ws = ws.PIER_PHYSICAL_FIT_TOLERANCE_CM
sweep = [round(x * 0.0005, 6) for x in range(0, 8002)]   # 0 .. 4,001 cm
assinaturas = {}
for tol_cm in (0.05, 0.10, 0.30):
    ws.PIER_PHYSICAL_FIT_TOLERANCE_CM = tol_cm
    vec = tuple(ok(True, gr=B54_HALF - v) for v in sweep)
    assinaturas[tol_cm] = vec
ws.PIER_PHYSICAL_FIT_TOLERANCE_CM = orig_ws
mm.PIER_PHYSICAL_FIT_TOLERANCE_CM = orig
iguais = assinaturas[0.05] == assinaturas[0.10] == assinaturas[0.30]
print("     sweep de 0 a 4,001 cm em passos de 0,0005 cm (%d pontos)" % len(sweep))
for t, v in assinaturas.items():
    print("     tol=%.2f cm -> %d aprovam, fronteira em %.4f cm"
          % (t, sum(v), sweep[max(i for i, x in enumerate(v) if x)]))
check("0,05 / 0,10 / 0,30 NAO saturam no nivel da guarda (esperado: divergem)",
      not iguais, "saturaram - contradiz a medicao da guarda isolada")

# ---------------------------------------------- monotonicidade / fuzz
print("\n[monotonicidade, invariancia e fuzz, com a secao 74 LIGADA]")
for eixo, base in (("gr", B54_HALF), ("gl", B54_HALF), ("inc", B34)):
    visto = False
    v = 5.0
    viol = []
    while v <= 120.0 + 1e-9:
        r = ok(True, **{eixo: v})
        if r:
            visto = True
        elif visto:
            viol.append(v)
        v = round(v + 0.05, 6)
    check("ON: monotono em %s" % eixo, not viol, "%r" % viol[:4])

grid = (10.0, 26.5, 27.0, 27.5, 33.5, 34.0, 60.0)
pts = list(itertools.product(grid, grid, grid))
res = {p: ok(True, gr=p[0], gl=p[1], inc=p[2]) for p in pts}
viol = [(a, b) for a in pts for b in pts
        if all(y >= x for x, y in zip(a, b)) and res[a] and not res[b]]
check("ON: monotonicidade conjunta (%d pares)" % (len(pts) ** 2), not viol, "%r" % viol[:2])

rng = random.Random(20260917)
ANG = [0.0, math.pi / 6, math.pi / 4, math.pi / 3, math.pi / 2, 2.1, 3.0, -0.7, -1.9]
def fisica(gr, gl, inc, tol):
    return (min(gr, gl) >= B54_HALF - tol) and (inc >= B34 - tol)
errados = []
for _ in range(1500):
    gr = round(rng.uniform(1.0, 90.0), 4)
    gl = round(rng.uniform(1.0, 90.0), 4)
    ic = round(rng.uniform(1.0, 90.0), 4)
    kw = dict(gr=gr, gl=gl, inc=ic, theta=rng.choice(ANG),
              ox=round(rng.uniform(-500, 500), 2), oy=round(rng.uniform(-500, 500), 2),
              flip_main=rng.choice((False, True)), flip_inc=rng.choice((False, True)),
              order=rng.choice(((0, 1), (1, 0))))
    if ok(True, **kw) is not fisica(gr, gl, ic, 0.05):
        errados.append((gr, gl, ic))
check("ON: fuzz 1500 (rotacao/translacao/inversao/ordem) bate com a fisica + 0,05",
      not errados, "%r" % errados[:3])

# ---------------------------------------------- legado
print("\n[legado]")
n, W, O = scene(gr=1.0, inc=1.0)
for flag in (False, True):
    ws.T_ROOM_PHYSICAL_TOLERANCE = flag
    check("openings_per_wall=None devolve True (flag=%s)" % flag,
          ws._t_intersection_room_ok(n, W, None) is True)
ws.T_ROOM_PHYSICAL_TOLERANCE = False

print("\n" + "=" * 62)
print("FALHAS: %d" % len(FAILS))
for a, b in FAILS:
    print("  - %s  %s" % (a, b))
