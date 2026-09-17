# -*- coding: utf-8 -*-
"""Proteção operacional da PURGA da bancada — `remaining` TEM que ser 0.

Pedido do usuário (2026-09-17): antes do próximo apply no Revit, a purga
do lote carimbado não pode mais apenas REGISTRAR quantas instâncias
sobraram; se sobrou alguma, o run tem que ABORTAR em vez de seguir sobre
um TARGET sujo.

Motivação (lacuna medida na auditoria do nó T): hoje o harness faz

    step("PURGE", removed=len(olds), remaining=len(bench_instances()))

e continua independentemente de `remaining`. Se a exclusão falhar
parcialmente — elemento pinado, membro de grupo, instância em outro nível,
transação revertida — o resíduo só aparece muito depois, como divergência
de contagem, já misturado ao resultado do run.

Este módulo é Python puro (roda em CPython e em IronPython/pyRevit) e NÃO
importa nada do Revit nem do solver: recebe números, devolve veredito.
Deliberadamente fora de `nuvem/` — não é produção, é preflight
operacional.

Integração no harness, no lugar da linha `step("PURGE", ...)`:

    from tools.preflight.purge_guard import assert_purge_clean
    report = assert_purge_clean(
        removed=len(olds),
        remaining=len(bench_instances()),
        expected_removed=n_before,
        total_before=total_before,
        total_after=total_after,
        human_modified=H.IsModified,
    )
    step("PURGE", **report)          # levanta PurgeNotCleanError antes disto

`assert_purge_clean` levanta `PurgeNotCleanError` em qualquer violação;
`check_purge` devolve o relatório sem levantar, para quem quiser só medir.
"""


class PurgeNotCleanError(RuntimeError):
    """A purga não deixou o TARGET limpo — o run NÃO pode continuar."""


def check_purge(removed, remaining, expected_removed=None,
                total_before=None, total_after=None, human_modified=None):
    """Avalia a purga e devolve `(ok, report)` sem levantar exceção.

    `removed`/`remaining`: quantas instâncias carimbadas foram apagadas e
    quantas ainda respondem ao filtro da bancada DEPOIS da transação.
    Os demais são opcionais — cada um que vier é conferido.

    `report` é um dict pronto para `step("PURGE", **report)`, com a lista
    `violations` sempre presente (vazia quando está tudo certo).
    """
    violations = []

    if remaining != 0:
        violations.append(
            "remaining=%r, esperado 0 - TARGET sujo, exclusao parcial "
            "(elemento pinado, membro de grupo, instancia em outro nivel "
            "ou transacao revertida)" % (remaining,))

    if expected_removed is not None and removed != expected_removed:
        violations.append(
            "removed=%r difere da contagem inicial de bancada (%r) - a "
            "purga apagou de menos ou de mais" % (removed, expected_removed))

    if total_before is not None and total_after is not None:
        delta = total_before - total_after
        if delta != removed:
            violations.append(
                "o total de FamilyInstance caiu %r, mas removed=%r - a "
                "purga alcancou elemento que NAO era da bancada"
                % (delta, removed))

    if human_modified:
        violations.append(
            "human_modified=%r - o documento HUMANO foi tocado, o que a "
            "purga nunca pode fazer" % (human_modified,))

    report = {
        "removed": removed,
        "remaining": remaining,
        "expected_removed": expected_removed,
        "total_before": total_before,
        "total_after": total_after,
        "human_modified": human_modified,
        "violations": violations,
    }
    return (not violations), report


def assert_purge_clean(removed, remaining, expected_removed=None,
                       total_before=None, total_after=None,
                       human_modified=None):
    """Como `check_purge`, mas ABORTA (levanta `PurgeNotCleanError`) na
    primeira violação. Devolve o `report` quando está tudo limpo."""
    ok, report = check_purge(
        removed=removed, remaining=remaining,
        expected_removed=expected_removed, total_before=total_before,
        total_after=total_after, human_modified=human_modified)
    if not ok:
        raise PurgeNotCleanError(
            "PURGA NAO LIMPA - apply abortado antes de tocar o TARGET:\n  - "
            + "\n  - ".join(report["violations"]))
    return report
