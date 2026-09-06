# -*- coding: utf-8 -*-
"""Executa os reprodutores minimos dos clusters principais (item 19).
Geometria escolhida MODULAR (como o humano constroi) exceto no mecanismo
sob teste - assim o unico defeito visivel e' o do cluster."""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import repro_lib as R  # noqa: E802
from repro_lib import seg  # noqa: E402

# R1 - boneca de 79 cm (eixo de face a face) entre um T na principal e um L.
#      Principal 604 com L nas duas pontas; T em x=302 (c ≡ 2 mod 5 deixa os
#      trechos da principal modulares nas duas familias); boneca de (302,7)
#      ate' (302,72) (face a face => 79 depois de estender); parede do L
#      de (302,72) a (699,72) (404 depois de estender).
R.describe(R.solve([seg(7, 0, 597, 0), seg(302, 0, 302, 72), seg(302, 72, 699, 72),
                    seg(7, 0, 7, 300), seg(597, 0, 597, 300)]),
           "R1 boneca 79cm entre T e L (TP1 W061/W062): cadeia C09x3 nas duas familias")

# R2 - parede curta de 124 cm (eixo face a face) cruzando em X uma parede
#      longa a 55 cm de um T (TP1 W003 x W021), com L nas pontas da curta.
R.describe(R.solve([seg(7, 0, 1337, 0),            # 0 longa (T em x=7 e x=1337)
                    seg(7, -400, 7, 300),          # 1 chega em T no inicio
                    seg(1337, -400, 1337, 300),    # 2 chega em T no fim
                    seg(62, -55, 62, 55),          # 3 curta cruzando em x=62 (X); L em y=+-62 apos estender
                    seg(62, -55, 262, -55),        # 4 L inferior
                    seg(62, 55, 262, 55)]),        # 5 L superior
           "R2 X de parede curta 124 a 55cm do T (TP1 W003/W021): X degradado + C09x3")
R.describe(R.solve([seg(7, 0, 1337, 0), seg(7, -400, 7, 300), seg(1337, -400, 1337, 300),
                    seg(61.99, -55, 61.99, 55), seg(61.99, -55, 262, -55), seg(61.99, 55, 262, 55)]),
           "R2b idem com o X em 61.99 (ruido de 0.01 cm): degradacao borderline?")

# R3 - fragmento L-L de 324.26 (TGD W036) - ja' estendido (pontas nas faces
#      opostas das perpendiculares): nenhum preenchimento fecha.
for L in (324.26, 324.0, 324.08):
    R.describe(R.solve([seg(0, 0, L, 0), seg(7, 0, 7, -300), seg(L - 7, 0, L - 7, -300)],
                       already_extended=True),
               "R3 fragmento L-L de %.2f cm (ja' estendido)" % L)
