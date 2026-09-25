# -*- coding: utf-8 -*-
"""Rastreio de L (2026-09-24, pedido do usuario apos o ciclo 4): o bond_trace
dos encontros L registra DIRETAMENTE o que antes precisou ser reconstruido
fora do motor - espaco medido em cada braco (a partir do CONTATO, a mesma
medida que decide o B34), espaco exigido, ponto de contato e o candidato de
amarracao de cada fiada fisica (gerado? presente? aceito? por que nao?).

Somente observacao: nenhuma peca muda (prova por assinatura fisica com o
rastreio ligado x desligado, NONE e CHANNEL). Fixture sintetica com a
topologia dos cantos 55/56 do BUTANTA (U: parede A de 101 cm entre dois L,
bracos de 242 cm, janela com pilares de 19,5 e 29,5 cm da face externa) -
nenhum ID do projeto. A inversao de familia do L pela paridade (troca de
arms) usa a fixture l_x_l_124 de test_tie_parity_abutting_ties.

    python3 -m pytest tests/test_bond_trace_l.py -q
"""
import inspect
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pytest
import test_channel_reinforcement as tcr  # noqa: E402
from core.engine import wall_stepper as ws  # noqa: E402

m, ft, seg, solve = tcr.m, tcr.ft, tcr.seg, tcr.solve
NUM = 14
F = 30.48
CAMPOS_L = ("wall_a", "wall_b", "available_space_a", "available_space_b", "required_space", "contact_point",
            "contact_point_a", "contact_point_b", "candidate_code", "candidate_origin", "candidate_rotation",
            "candidate_generated", "candidate_in_final_result", "candidate_accepted", "reject_reason",
            "bond_resolved", "status", "requires_human_review")


def _u(pier_esq=19.5, pier_dir=29.5, espelhar=False, janela=True):
    s = -1.0 if espelhar else 1.0
    lines = [seg(0, 0, s * 101.0, 0), seg(0, 0, 0, -242.0), seg(s * 101.0, 0, s * 101.0, -242.0)]
    vao = [(ft(pier_esq), ft(115.0 - pier_dir), ft(40.0), ft(91.0))] if janela else []
    return lines, [vao, [], []]


def _l_x_l_124():
    return [seg(0, 0, 300, 0), seg(0, 0, 0, 110), seg(-300, 55, 300, 55), seg(0, 110, 300, 110)]


_CACHE = {}


def _solve(estrategia=None, **kw):
    chave = (estrategia, tuple(sorted(kw.items())))
    if chave not in _CACHE:
        lines, ops = _u(**kw)
        _CACHE[chave] = solve(lines, ops, strategy=estrategia, num_courses=NUM)
    return _CACHE[chave]


def _linhas_l(res):
    return [r for r in res["bond_trace"] if r["node_kind"] == "L_CORNER"]


def _dono(r):
    return r["wall_a"] if r["course"] % 2 == 0 else r["wall_b"]


def _espaco_dono(r):
    return r["available_space_a"] if r["course"] % 2 == 0 else r["available_space_b"]


def _peca_final(res, r):
    """A peca do resultado final que o rastreio diz ser o candidato desta fiada."""
    for c in res["course_candidates"][r["course"]]:
        o = c["origin_world"]
        if (c.get("node_index") == r["node_index"] and c["logical_code"] == r["candidate_code"]
                and abs(o.X * F - r["candidate_origin"][0]) <= 0.05 and abs(o.Y * F - r["candidate_origin"][1]) <= 0.05):
            return c
    return None


def _confere_dono_e_origem(res):
    """Toda fiada L com a amarracao aceita: o candidato e' uma peca REAL do
    resultado (mesma origem), na parede que o rastreio diz ser a dona da
    familia fisica da fiada. Pega familia trocada, parede trocada e origem
    de outra peca."""
    vistos = 0
    for r in _linhas_l(res):
        if not r["candidate_accepted"]:
            continue
        peca = _peca_final(res, r)
        assert peca is not None, (r["node_index"], r["course"], r["candidate_origin"])
        assert peca["wall_idx"] == _dono(r), (r["node_index"], r["course"], peca["wall_idx"], r["wall_a"], r["wall_b"])
        assert r["room_cm"] == {"arm_a": r["available_space_a"], "arm_b": r["available_space_b"]}
        vistos += 1
    return vistos


# ----------------------------------------------------------------- campos
def test_toda_linha_de_l_traz_os_campos_de_espaco_e_candidato():
    res, _w, _n, _o = _solve()
    linhas = _linhas_l(res)
    assert len(linhas) == 2 * NUM
    for r in linhas:
        for campo in CAMPOS_L:
            assert campo in r, (campo, r["node_index"], r["course"])
        assert r["required_space"] == pytest.approx(34.0, abs=1e-6)
        assert r["space_unit"] == "cm"


def test_paredes_e_pontos_de_contato_de_cada_braco():
    """Fixture normal (sem bloqueio, sem inversao): cada braco e' a parede do
    L com o contato na face externa; contact_point e' o do braco DONO da
    fiada fisica."""
    res, walls, nodes, _o = _solve()
    for r in _linhas_l(res):
        node = nodes[r["node_index"]]
        esperado = {}
        for w in (r["wall_a"], r["wall_b"]):
            p = ws._node_contact_point_for_wall(node, w)
            esperado[w] = [round(p.X * F, 4), round(p.Y * F, 4)]
        assert set((r["wall_a"], r["wall_b"])) == set(ws._l_corner_wall_pair(node))
        assert r["contact_point_a"] == pytest.approx(esperado[r["wall_a"]], abs=1e-3)
        assert r["contact_point_b"] == pytest.approx(esperado[r["wall_b"]], abs=1e-3)
        assert r["contact_point"] == (r["contact_point_a"] if r["course"] % 2 == 0 else r["contact_point_b"])
    assert _confere_dono_e_origem(res) == 2 * NUM - 3


# ----------------------------------------------------------------- 55/56
@pytest.mark.parametrize("espelhar,falhas", [
    (False, {(0, 2): 19.5, (0, 4): 19.5, (1, 3): 29.5}),
    (True, {(0, 3): 19.5, (1, 2): 29.5, (1, 4): 29.5}),
])
def test_l_como_55_56_registra_o_espaco_real_e_o_b34_nao_gerado(espelhar, falhas):
    """As 3 fiadas sem espaco: o braco dono tem 19,5 / 29,5 cm (< 34), o B34
    nao e' gerado, o motivo vem do teste de espaco do braco e a fiada fica
    BOND_UNRESOLVED com revisao humana. No espelho a distribuicao entre os
    cantos troca (a paridade acompanha), o total e' o mesmo."""
    res, _w, _n, _o = _solve(espelhar=espelhar)
    faltando = dict(((r["node_index"], r["course"]), r) for r in _linhas_l(res) if not r["bond_resolved"])
    assert sorted(faltando) == sorted(falhas)
    for chave, espaco in falhas.items():
        r = faltando[chave]
        assert _espaco_dono(r) == pytest.approx(espaco, abs=0.01)
        assert r["classification"] == m.BOND_TRACE_NOT_GENERATED
        assert r["candidate_code"] == "B34" and r["candidate_generated"] is False
        assert r["candidate_in_final_result"] is False and r["candidate_accepted"] is False
        assert r["candidate_origin"] is None
        assert r["reject_reason"].startswith("L_CORNER_ROOM_INSUFFICIENT: B34 da familia")
        assert "{:.3f}".format(espaco) in r["reject_reason"]
        assert r["rejection_rule"] == "L_CORNER_B34"
        assert r["status"] == "BOND_UNRESOLVED" and r["requires_human_review"] is True
        # o C09 que fecha o braco e' preenchimento, nunca a amarracao
        assert r["selected"]["code"] == "C09"


def test_o_teste_de_espaco_so_reprova_a_familia_do_braco_que_falhou():
    """Na faixa da janela o no' reprova o espaco de UM braco; as fiadas da
    outra familia (braco com espaco) continuam limpas."""
    res, _w, _n, _o = _solve()
    for r in _linhas_l(res):
        if r["course"] not in (2, 3, 4):
            continue
        regras = [x["rule"] for x in r["rejected"]]
        if r["bond_resolved"]:
            assert regras == [] and r["reject_reason"] is None, (r["node_index"], r["course"], regras)
        else:
            assert regras == ["L_CORNER_B34"], regras


def test_passos_do_no_registram_elemento_unico_e_saida_de_bloqueio():
    res, _w, _n, _o = _solve()
    passos = [rec for rec in res["bond_trace_steps"] if rec["kind"] == "L_CORNER" and rec["band"] and 2 in rec["band"]]
    assert len(passos) == 2
    for rec in passos:
        regras = [s["rule"] for s in rec["steps"]]
        assert regras == ["L_CORNER_B34", "L_SINGLE_ELEMENT"], regras
        espaco, unico = rec["steps"]
        assert espaco["block_exit"] == "SEM_BLOQUEIO"
        falhou = [f for f in ("A", "B") if not espaco["arms"][f]["passed"]]
        assert len(falhou) == 1
        assert unico["arms"][falhou[0]]["chosen"] == "C09" and unico["arms"][falhou[0]]["applies"] is True
        outro = "B" if falhou[0] == "A" else "A"
        assert unico["arms"][outro]["applies"] is False and unico["arms"][outro]["chosen"] is None
        assert unico["passed"] is True


def test_fiadas_resolvidas_trazem_o_b34_gerado_e_aceito():
    res, _w, _n, _o = _solve()
    for r in _linhas_l(res):
        if not r["bond_resolved"]:
            continue
        assert r["classification"] == m.BOND_TRACE_RESOLVED
        assert r["candidate_code"] == "B34" and r["candidate_generated"] is True
        assert r["candidate_in_final_result"] is True and r["candidate_accepted"] is True
        assert r["reject_reason"] is None
        assert _espaco_dono(r) + 1e-3 >= 34.0
        assert r["status"] is None and r["requires_human_review"] is False


def test_l_normal_sem_abertura_tudo_resolvido():
    res, _w, _n, _o = _solve(janela=False)
    linhas = _linhas_l(res)
    assert linhas and all(r["bond_resolved"] for r in linhas)
    assert _confere_dono_e_origem(res) == len(linhas)


# ----------------------------------------------------------------- limites
def test_limite_exato_do_b34():
    """34 cm cabe; 33,9 cm nao cabe. Com 33,9 o canto de 45 cm ainda perde 2
    fiadas por APOIO (auditoria 76.1: a meia-fiada ao lado do vao nao
    modular fica sem peca) - efeito lateral conhecido, com o B34 gerado,
    presente e NAO aceito."""
    res34, _w, _n, _o = _solve(pier_esq=34.0, pier_dir=45.0)
    assert all(r["bond_resolved"] for r in _linhas_l(res34))
    res, _w, _n, _o = _solve(pier_esq=33.9, pier_dir=45.0)
    falta = dict(((r["node_index"], r["course"]), r) for r in _linhas_l(res) if not r["bond_resolved"])
    assert sorted(falta) == [(0, 2), (0, 4), (1, 3), (1, 5)]
    for chave in ((0, 2), (0, 4)):
        assert falta[chave]["candidate_generated"] is False
        assert _espaco_dono(falta[chave]) == pytest.approx(33.9, abs=0.01)
    for chave in ((1, 3), (1, 5)):
        r = falta[chave]
        assert r["candidate_generated"] is True and r["candidate_in_final_result"] is True
        assert r["candidate_accepted"] is False
        assert r["reject_reason"].startswith("AUDIT_BOND_PIECE_UNSUPPORTED")
        assert r["classification"] == m.BOND_TRACE_REJECTED


def test_braco_sem_espaco_nem_para_o_menor_elemento():
    """Pilar de 3 cm: nem o C04 cabe, o no' fica sem solucao na banda. A
    familia do braco curto reprova por espaco; a familia do braco com espaco
    diz que o NO' ficou sem solucao - e nenhuma reprovacao vaza de uma
    familia para a outra, nem com prefixo repetido."""
    res, _w, _n, _o = _solve(pier_esq=3.0)
    linhas = dict(((r["node_index"], r["course"]), r) for r in _linhas_l(res))
    curta, longa = linhas[(0, 2)], linhas[(0, 3)]
    assert _espaco_dono(curta) == pytest.approx(3.0, abs=0.01)
    assert [x["rule"] for x in curta["rejected"]] == ["L_CORNER_B34", "L_SINGLE_ELEMENT"]
    assert curta["rejection_rule"] == "L_CORNER_B34"
    assert curta["reject_reason"].startswith("L_CORNER_ROOM_INSUFFICIENT")
    assert _espaco_dono(longa) == pytest.approx(249.0, abs=0.01)
    assert longa["rejected"] == []
    assert longa["candidate_generated"] is False
    assert longa["reject_reason"].startswith("L_CORNER_NO_SOLUTION: ")
    for r in linhas.values():
        if r["reject_reason"]:
            assert not re.match(r"^(\w+): \1", r["reject_reason"]), r["reject_reason"]


# ----------------------------------------------------------------- inversao / D3
def test_familia_invertida_pela_paridade_do_l_mapeia_o_braco_certo():
    """l_x_l_124: um canto L inverte a paridade trocando os arms (secoes
    31/32). O passo gravado usa a convencao anterior; o rastreio devolve as
    paredes e o espaco da familia FISICA de cada fiada."""
    res, walls, nodes, _o = solve(_l_x_l_124(), [[], [], [], []], strategy=None, num_courses=4)
    invertidos = [i for i, n in enumerate(nodes) if n.get("kind") == "L_CORNER" and n.get("_arm_role_pinned")]
    assert invertidos, "fixture deixou de inverter um L"
    assert _confere_dono_e_origem(res) > 0
    for r in _linhas_l(res):
        if r["node_index"] in invertidos and r["candidate_accepted"]:
            assert _peca_final(res, r)["wall_idx"] == _dono(r)


def test_registro_com_convencao_trocada_ainda_mapeia_a_familia_fisica():
    """Rede de seguranca: se o passo gravado estiver na convencao TROCADA em
    relacao as pecas finais (ex.: passada anterior a uma troca de arms), o
    casamento gerada x final detecta a inversao e paredes, espacos e
    candidato saem na familia FISICA de cada fiada - identicos ao rastreio
    do registro correto."""
    import copy
    lines, ops = _u()
    res, walls, nodes, openings = solve(lines, ops, strategy=None, num_courses=NUM)
    trocado = copy.deepcopy(res["bond_trace_steps"])
    for rec in trocado:
        if rec["kind"] != "L_CORNER":
            continue
        for g in rec["generated"]:
            g["family"] = "B" if g["family"] == "A" else "A"
        for st in rec["steps"]:
            if "arms" in st:
                st["arms"] = {"A": st["arms"]["B"], "B": st["arms"]["A"]}
            if "chosen" in st:
                st["chosen"] = {"A": st["chosen"]["B"], "B": st["chosen"]["A"]}
    copia = dict(res)
    copia["bond_trace_steps"] = trocado
    audit = m._junction_bond_audit_final(copia, nodes, walls, openings, tcr.sb.CATALOG, 0.0, NUM, None)
    linhas = dict(((r["node_index"], r["course"]), r) for r in m._bond_trace_from_result(copia, audit, nodes)
                  if r["node_kind"] == "L_CORNER")
    for r in _linhas_l(res):
        x = linhas[(r["node_index"], r["course"])]
        for campo in ("wall_a", "wall_b", "available_space_a", "available_space_b", "contact_point",
                      "candidate_code", "candidate_origin", "candidate_generated", "candidate_accepted", "reject_reason"):
            assert x[campo] == r[campo], (r["node_index"], r["course"], campo, x[campo], r[campo])


def test_candidata_d3_ligada_mostra_o_braco_que_de_fato_ficou_com_a_familia(monkeypatch):
    monkeypatch.setattr(ws, "L_CORNER_OTHER_ARM_OWNS", True)
    monkeypatch.setattr(ws, "COMPENSATOR_NEVER_JUNCTION_BOND", True)
    lines, ops = _u()
    res, _w, _n, _o = solve(lines, ops, strategy=None, num_courses=NUM)
    movidos = [s for rec in res["bond_trace_steps"] for s in rec["steps"] if s["rule"] == "L_CORNER_OTHER_ARM_OWNS"]
    assert movidos and all(s["moved_family"] in ("A", "B") and s["to_wall_idx"] is not None for s in movidos)
    assert _confere_dono_e_origem(res) > 0
    for r in _linhas_l(res):
        if r["course"] in (2, 3, 4) and r["candidate_accepted"]:
            assert "L_CORNER_B34" not in [x["rule"] for x in r["rejected"]]


# ----------------------------------------------------------------- nenhuma peca muda
def _assinatura_completa(res):
    """Identidade FISICA completa de cada peca (todos os campos que decidem o
    que e' criado) + gates, colisoes e trechos nao resolvidos."""
    linhas = []
    for ci, pecas in sorted(res["course_candidates"].items()):
        for c in pecas:
            o, xd = c["origin_world"], c.get("x_dir")
            linhas.append("|".join(str(x) for x in (
                ci, c["logical_code"], round(o.X * F, 4), round(o.Y * F, 4), round(o.Z * F, 4),
                round(c.get("rotation_deg") or 0.0, 3), c.get("wall_idx"), c.get("secondary_wall_idx"),
                c.get("course"), c.get("placement_reason"), c.get("node_index"), c.get("length_cm"),
                c.get("width_cm"), (round(xd.X, 6), round(xd.Y, 6)) if xd is not None else None)))
    extra = (sorted(str(v) for v in res.get("missing_required_junction_bond") or []),
             sorted(str(v) for v in res.get("compensator_as_junction_bond") or []),
             len(res.get("collisions") or []), len(res.get("unresolved_spans") or []))
    return sorted(linhas), extra


GRADE = [dict(), dict(espelhar=True), dict(pier_esq=34.0, pier_dir=45.0), dict(pier_esq=45.0, pier_dir=34.0),
         dict(pier_esq=34.0, pier_dir=34.0), dict(pier_esq=33.9, pier_dir=45.0), dict(janela=False), dict(pier_esq=3.0)]


@pytest.mark.parametrize("estrategia", [None, tcr.CHANNEL])
@pytest.mark.parametrize("geometria", GRADE, ids=lambda g: "-".join("%s=%s" % kv for kv in sorted(g.items())) or "padrao")
def test_o_rastreio_nao_muda_nenhuma_peca(monkeypatch, estrategia, geometria):
    lines, ops = _u(**geometria)
    com, _w, _n, _o = solve(lines, ops, strategy=estrategia, num_courses=NUM)
    assert com.get("bond_trace")
    monkeypatch.setattr(m, "BOND_TRACE_ENABLED", False)
    sem, _w2, _n2, _o2 = solve(lines, ops, strategy=estrategia, num_courses=NUM)
    assert not sem.get("bond_trace")
    assert _assinatura_completa(com) == _assinatura_completa(sem)


def test_solve_l_corner_sem_rastreio_devolve_o_resultado_de_sempre():
    lines, ops = _u()
    res, walls, nodes, openings = solve(lines, ops, strategy=None, num_courses=NUM)
    assert ws.BOND_TRACE is None                       # restaurado depois do solve
    ni = [i for i, n in enumerate(nodes) if n.get("kind") == "L_CORNER"][0]
    direto = ws.solve_l_corner(nodes[ni], walls, tcr.sb.CATALOG, node_index=ni, openings_per_wall=openings)
    assert "trace" not in direto
    assert set(direto) <= {"ok", "reason", "course_a", "course_b", "degraded", "missing_bond_courses"}


def test_regra_48_na_materializacao_marca_o_candidato_rejeitado():
    res, _w, _n, _o = _solve()
    rastreio = [dict(r) for r in res["bond_trace"]]
    alvo = [r for r in rastreio if r["node_kind"] == "L_CORNER" and r["bond_resolved"]][0]
    m._bond_trace_apply_materialization(rastreio, [{"node_index": alvo["node_index"], "course_index": alvo["course"],
                                                    "rejected_rule": "OPENING", "message": "invadia a abertura"}])
    linha = [r for r in rastreio if r["node_index"] == alvo["node_index"] and r["course"] == alvo["course"]][0]
    assert linha["candidate_generated"] is True and linha["candidate_accepted"] is False
    assert linha["reject_reason"].startswith("REGRA_48_OPENING")
    assert linha["status"] == "BOND_UNRESOLVED" and linha["requires_human_review"] is True


def test_linhas_de_t_nao_ganham_os_campos_de_l():
    lines = [seg(0, 0, 604, 0), seg(302.0, 0, 302.0, 242)]
    res, _w, nodes, _o = solve(lines, [[], []], strategy=None, num_courses=4)
    t = [r for r in res["bond_trace"] if r["node_kind"] == "T_INTERSECTION"]
    assert t and all("available_space_a" not in r for r in t)
    assert all("requires_human_review" in r and "status" in r for r in t)


# ----------------------------------------------------------------- sem hardcode / IronPython
def test_nenhum_identificador_de_projeto_no_rastreio_de_l():
    fontes = [inspect.getsource(f) for f in (ws.solve_l_corner, ws._l_room_trace_step, ws._solve_l_corner_steps,
                                             m._bond_trace_from_result, m._bond_trace_l_fields,
                                             m._bond_trace_row_reason, m._bond_trace_apply_materialization)]
    texto = "\n".join(fontes)
    assert "8284" not in texto and "BUTANT" not in texto.upper()
    assert not re.search(r"node_index\s*==\s*\d|wall_idx\s*==\s*\d|==\s*(47|48|55|56)\b", texto)


def test_modulos_do_rastreio_compativeis_com_ironpython27():
    """O motor roda em IronPython 2.7 dentro do Revit: nenhuma construcao
    so'-Python-3 nos dois modulos tocados pelo rastreio (analise da arvore de
    sintaxe, nao de texto)."""
    import ast
    raiz = os.path.dirname(HERE)
    proibidos = tuple(getattr(ast, n) for n in ("JoinedStr", "Nonlocal", "NamedExpr", "YieldFrom", "AnnAssign",
                                                 "AsyncFunctionDef", "AsyncFor", "AsyncWith", "Await", "Match")
                      if hasattr(ast, n))
    for rel in (("nuvem", "core", "engine", "wall_stepper.py"), ("nuvem", "core", "wall_modeling.py")):
        arvore = ast.parse(io.open(os.path.join(raiz, *rel), encoding="utf-8").read())
        achados = []
        for no in ast.walk(arvore):
            if isinstance(no, proibidos):
                achados.append((type(no).__name__, getattr(no, "lineno", None)))
            elif isinstance(no, (ast.FunctionDef, ast.Lambda)):
                a = no.args
                if a.kwonlyargs or getattr(a, "posonlyargs", None):
                    achados.append(("kwonly/posonly", getattr(no, "lineno", None)))
                if any(x.annotation is not None for x in a.args + a.kwonlyargs) or getattr(no, "returns", None):
                    achados.append(("anotacao", getattr(no, "lineno", None)))
            elif isinstance(no, (ast.Assign, ast.For)):
                alvos = no.targets if isinstance(no, ast.Assign) else [no.target]
                if any(isinstance(n, ast.Starred) for t in alvos for n in ast.walk(t)):
                    achados.append(("desempacotamento estrelado", no.lineno))
            elif isinstance(no, ast.Raise) and no.cause is not None:
                achados.append(("raise from", no.lineno))
            elif isinstance(no, ast.Dict) and any(k is None for k in no.keys):
                achados.append(("{**d}", no.lineno))
            elif (isinstance(no, ast.Call) and isinstance(no.func, ast.Name) and no.func.id == "print"
                  and any(k.arg in ("end", "sep", "file", "flush") for k in no.keywords)):
                achados.append(("print(..., end=)", no.lineno))
        assert not achados, (rel, achados[:10])


# ----------------------------------------------------------------- X e pecas gemeas
def test_x_cada_fiada_casa_uma_so_peca_gerada_pela_rotacao():
    """As duas B54 de um X nascem no ponto do no' (mesma origem, rotacoes 0 e
    90): o casamento exige a rotacao, entao cada fiada aceita UMA so', da
    familia fisica da fiada."""
    lines = [seg(0, 0, 300, 0), seg(150, -150, 150, 150)]
    res, _w, _n, _o = solve(lines, [[], []], strategy=None, num_courses=4)
    linhas = [r for r in res["bond_trace"] if r["node_kind"] == "X_INTERSECTION"]
    assert len(linhas) == 4
    for r in linhas:
        aceitos = [c for c in r["candidates"] if c["accepted"] is True]
        assert len(aceitos) == 1, r["candidates"]
        assert aceitos[0]["family"] == ("A" if r["course"] % 2 == 0 else "B")


def test_pecas_gemeas_em_banda_impar_nao_invertem_a_familia():
    """Um T a 25 cm do canto manda as duas familias do L para a parede livre
    (mesma origem: pecas gemeas) e a janela cria a banda [3, 4, 5], que comeca
    em fiada impar. Pecas gemeas nao decidem inversao: nenhuma familia troca,
    as duas paredes do rastreio sao a livre e o espaco e' o mesmo nas fiadas."""
    lines = [seg(200, -90, 0, -90), seg(0, 0, 0, -90), seg(25, -90, 25, -300), seg(0, 0, 200, 0)]
    ops = [[], [], [(ft(100.0), ft(160.0), ft(60.0), ft(111.0))], []]
    res, _w, _n, _o = solve(lines, ops, strategy=None, num_courses=NUM)
    assert [3, 4, 5] in [b["course_indices"] for b in res["bands"]]
    gemeos = set(rec["node_index"] for rec in res["bond_trace_steps"] if rec["kind"] == "L_CORNER"
                 and rec["steps"] and rec["steps"][0].get("block_exit") == "AS_DUAS_FIADAS_NA_PAREDE_LIVRE")
    assert len(gemeos) == 1
    ni = gemeos.pop()
    linhas = [r for r in _linhas_l(res) if r["node_index"] == ni]
    assert len(set((r["wall_a"], r["wall_b"]) for r in linhas)) == 1 and linhas[0]["wall_a"] == linhas[0]["wall_b"]
    assert len(set((r["available_space_a"], r["available_space_b"]) for r in linhas)) == 1
    for r in linhas:
        assert all(c["family"] == c["convention_family"] for c in r["candidates"]), (r["course"], r["candidates"])
