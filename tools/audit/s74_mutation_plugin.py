# -*- coding: utf-8 -*-
"""Plugin pytest que PRENDE `_t_intersection_room_ok` num valor fixo.

Serve para provar que a suite do corpus da secao 74 NAO e' tautologica:
se os testes so' se autoconfirmassem, prender a guarda em True ou em
False nao quebraria nada.

    WT=<worktree>
    MUT=true  PYTHONPATH=tools/audit python3 -m pytest tests/test_s74_corpus_butanta.py -q -p s74_mutation_plugin
    MUT=false PYTHONPATH=tools/audit python3 -m pytest tests/test_s74_corpus_butanta.py -q -p s74_mutation_plugin

Medido em 2c55211 (auditoria independente de 2026-09-18):
preso em True  -> 17 falhas (12 rapidas + 5 lentas)
preso em False -> 11 falhas

A mutacao e' GLOBAL (troca o atributo do modulo), entao alcanca tambem o
fluxo legado - por isso o teste do hash do legado quebra nas duas
direcoes. Uma injecao restrita ao fluxo CHANNEL da' uma falha a menos em
cada direcao (16/10).
"""
import os


def pytest_collection_finish(session):
    import sys
    alvo = os.environ.get("MUT")
    if alvo not in ("true", "false"):
        return
    ws = sys.modules.get("core.engine.wall_stepper")
    if ws is None:
        raise RuntimeError("wall_stepper nao carregado - mutacao nao aplicada")
    fixo = (alvo == "true")
    ws._t_intersection_room_ok = lambda *a, **k: fixo
    print("\n[MUTACAO] _t_intersection_room_ok preso em %s" % fixo)
