# -*- coding: utf-8 -*-
"""Infraestrutura de BENCHMARK, APRENDIZADO e REGRESSAO da modulacao.

Nao faz parte do que o botao baixa/executa: o loader (`Script.py`) so'
sincroniza `nuvem/core/**` (ver `CORE_REPO_PREFIX` la'). Este pacote e'
ferramenta de desenvolvimento - roda em CPython comum, fora do Revit,
sobre arquivos JSON.

Ciclo implementado (ver README.md deste pacote):

    projeto Revit correto -> extract/ -> reference.json
                                      -> input.json
    input.json -> solver real -> extract/from_solver -> result.json
    reference.json + result.json -> validators/ + comparator/
                                 -> scoring -> report -> regressao

Regra que orienta todo o pacote: **validacao determinista sempre que a
regra for geometrica/aritmetica** (item 19 do pedido do usuario). Nenhum
validador aqui pergunta nada a uma IA - todos sao calculo puro sobre os
numeros extraidos.
"""
