# -*- coding: utf-8 -*-
"""Ferramenta de auditoria: roda a auditoria adversarial da guarda de
espaco fisico do no' T SEM pytest, e imprime as fronteiras MEDIDAS.

    python3 tests/audit_t_room_physical_guard.py

Serve para dois usos que o arquivo de teste nao cobre: rodar em ambiente
sem pytest (IronPython/pyRevit inclusive) e MOSTRAR os numeros - onde
cada transicao acontece de fato, nao so' que ela esta' no lugar certo.

Nao altera producao e nao depende de baseline/golden nenhum.
"""

import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import test_t_room_physical_guard_independent_audit as A  # noqa: E402


def _boundaries():
    """Onde, em cm, cada fronteira REALMENTE fica - medida por bisseccao."""
    print("== fronteiras medidas por bisseccao (resolucao 1e-7 cm)")
    for label, kw, nominal in (
            ("B54, lado direito ", "gap_right_cm", A.B54_HALF_ROOM_CM),
            ("B54, lado esquerdo", "gap_left_cm", A.B54_HALF_ROOM_CM),
            ("B34, boneca       ", "inc_cm", A.B34_CM)):
        lo, hi = nominal - 1.0, nominal + 1.0
        assert not A.room_ok(**{kw: lo}) and A.room_ok(**{kw: hi})
        while hi - lo > 1e-7:
            mid = (lo + hi) / 2.0
            if A.room_ok(**{kw: mid}):
                hi = mid
            else:
                lo = mid
        print("   %s: exige %9.6f cm  (nominal %.2f, desvio %+.2e cm)"
              % (label, hi, nominal, hi - nominal))

    print("== folga interna das duas guardas")
    print("   no' T (_t_intersection_room_ok) : 1e-6 pes = %.3e cm"
          % A.to_cm(1e-6))
    print("   jamba (PIER_PHYSICAL_FIT_TOL)   : %.3e cm" % A.PHYSICAL_TOL_CM)
    print("   razao entre elas                : %.0fx"
          % (A.PHYSICAL_TOL_CM / A.to_cm(1e-6)))


def main():
    checks = [(n, getattr(A, n)) for n in sorted(dir(A)) if n.startswith("test_")]
    fails = []
    for name, func in checks:
        try:
            func()
            print("  OK   %s" % name)
        except Exception:
            fails.append((name, traceback.format_exc()))
            print("  FALHA %s" % name)
    print("")
    _boundaries()
    print("")
    print("%d verificacao(oes), %d falha(s)" % (len(checks), len(fails)))
    for name, tb in fails:
        print("\n=== %s ===\n%s" % (name, tb))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
