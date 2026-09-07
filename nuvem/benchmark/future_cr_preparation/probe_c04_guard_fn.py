# -*- coding: utf-8 -*-
"""Sondas INDEPENDENTES sobre as funcoes REAIS de producao da guarda C04."""
import os, sys
ROOT=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,ROOT)
from nuvem.benchmark import solver_bridge
solver_bridge.engine()
ws = sys.modules["core.engine.wall_stepper"]
mm = sys.modules["core.engine.modulation_math"]
G   = ws._layout_fitted_to_physical_span
END = ws._layout_physical_end_cm
FLOOR = mm.pier_cm_floored_to_module
FIT  = mm.PIER_FIT_TOLERANCE_CM
PHYS = mm.PIER_PHYSICAL_FIT_TOLERANCE_CM
MOD  = mm.PIER_MODULE_CM
JOINT= mm.BLOCK_JOINT_CM
print(f"FIT={FIT} PHYS={PHYS} MODULO={MOD} JUNTA={JOINT}\n")

def fake_layout(span):
    """Layout ideal para um span: uma peca cobrindo [0, span]."""
    if span is None or span <= 0: return None
    return [("Bxx", 0.0, float(span))]

def snapped_layout(pier_cm):
    """Reproduz o que o solver faz: snapa a sobra e monta ate' o valor snapado."""
    rem = mm._pier_remaining_cm(pier_cm, 0.0, 0.0)
    snapped = MOD*round(rem/MOD)
    if abs(rem-snapped) > FIT: return None
    return fake_layout(snapped - JOINT)

def run(nome, pier_cm, trailing_open=True, leading_open=True):
    sub={"lo":0.0,"hi":pier_cm,"leading_open":leading_open,"trailing_open":trailing_open}
    lay=snapped_layout(pier_cm)
    out=G(lay, pier_cm, sub, lambda s: fake_layout(s))
    ein=END(lay) if lay else None
    eout=END(out) if out else None
    exc = None if ein is None else round(ein-pier_cm,4)
    inv = None if eout is None else round(eout-pier_cm,4)
    sobra = None if eout is None else round(pier_cm-eout,4)
    veredito = ("SEM_LAYOUT" if lay is None else
                "None(vazio)" if out is None else
                "INALTERADO" if out==lay else "REMONTADO")
    ok = (out is None) or (eout - pier_cm <= PHYS + 1e-9)
    print(f"{nome:<46} pier={pier_cm:<10.4f} exc_in={str(exc):<9} -> {veredito:<12}"
          f" invasao_final={str(inv):<9} sobra={str(sobra):<8} {'OK' if ok else '*** INVADE ***'}")
    return ok

print("--- 1. trecho EXATO (fecha certinho) ---")
allok=[run("exato 9cm (C09)", 9.0), run("exato 19cm (B19)", 19.0), run("exato 34cm", 34.0)]
print("\n--- 2. ligeiramente MENOR que o modulo aceito ---")
for d in (0.01,0.04,0.05,0.06,0.10,0.12,0.242,0.267,0.29,0.30,0.31,0.5):
    allok.append(run(f"9.0 - {d}", 9.0-d))
print("\n--- 3. ligeiramente MAIOR que o modulo ---")
for d in (0.01,0.05,0.06,0.242,0.30,0.31):
    allok.append(run(f"9.0 + {d}", 9.0+d))
print("\n--- 4. fronteira FECHADA (junta de argamassa absorve) ---")
allok.append(run("9.0-0.242 trailing FECHADO", 9.0-0.242, trailing_open=False))
allok.append(run("9.0-0.30  trailing FECHADO", 9.0-0.30,  trailing_open=False))
print("\n--- 5. jamba no INICIO (leading aberto, trailing fechado) ---")
allok.append(run("leading aberto / trailing fechado", 9.0-0.242, leading_open=True, trailing_open=False))
print("\n--- 6. as DUAS fronteiras abertas (ponta livre + jamba) ---")
allok.append(run("ambas abertas", 9.0-0.242, leading_open=True, trailing_open=True))
print("\n--- 7. trecho pequeno demais: nem o modulo menor cabe ---")
for p in (0.5,1.0,2.0,3.0,3.9,4.0-0.242,4.0):
    allok.append(run(f"pier={p}", p))
print("\n--- 8. multiplas pecas com juntas ---")
for p in (49.0-0.242, 99.0-0.267, 169.0-0.12):
    allok.append(run(f"pier={p:.3f} (multi-peca)", p))
print("\n--- 9. escala / translacao: mesmo pier, lo deslocado ---")
for lo in (0.0, 100.0, -250.5, 1e5):
    sub={"lo":lo,"hi":lo+8.758,"leading_open":True,"trailing_open":True}
    lay=snapped_layout(8.758); out=G(lay,8.758,sub,lambda s: fake_layout(s))
    print(f"   lo={lo:<10} -> {[ (c,round(a,3),round(b,3)) for c,a,b in (out or []) ]}")
print("\n--- 10. contrato pier_cm_floored_to_module ---")
for p in (8.758, 8.88, 18.758, 23.757, 4.0, 3.9, 0.5):
    f=FLOOR(p,0.0,0.0)
    sobra = None if f is None else round(p-f,4)
    dentro = None if f is None else (MOD-FIT <= sobra < MOD)
    print(f"   pier={p:<9} floored={str(f):<7} sobra={str(sobra):<8} dentro_de_[{MOD-FIT},{MOD})? {dentro}")
print(f"\nRESULTADO: {sum(1 for x in allok if x)}/{len(allok)} sondas sem invasao alem de PHYS={PHYS}")
