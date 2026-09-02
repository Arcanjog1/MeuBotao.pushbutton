# -*- coding: utf-8 -*-
"""GOLDEN BENCHMARK - infraestrutura de comparacao com projetos de
referencia (CR-BLOCK-GOLDEN-BENCHMARK).

Este pacote NAO substitui `nuvem/benchmark/*` (model/scoring/validators/
comparator/runner) - ele e' construido EM CIMA daquilo. A regra que
organiza tudo aqui:

    Um `baseline.json` antigo, gravado pelo proprio solver, prova
    REPRODUTIBILIDADE (o motor continua decidindo a mesma coisa). Ele
    NUNCA prova CORRECAO. So' um projeto com prova de validacao humana
    pode ser GOLDEN_REFERENCE.

Ver `docs/GOLDEN_BENCHMARK.md` para a arquitetura completa.
"""
