# -*- coding: utf-8 -*-
"""Optional presentation payload. Never infers physical outcomes from a plan."""


def count(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


class ExecutionPresentation(object):
    """The host owns run identity; revisions are complete snapshots, not deltas."""

    def __init__(self, run_id=None):
        self.run_id = run_id
        self.revision = -1
        self.data = {}

    def update(self, snapshot):
        revision = count(snapshot.get("revision"))
        if not self.run_id or snapshot.get("run_id") != self.run_id or revision is None or revision <= self.revision:
            return False
        self.data = dict(snapshot)
        self.revision = revision
        return True

    def metric(self, key):
        value = count(self.data.get(key))
        return str(value) if value is not None else "—"

    def adjustment_text(self):
        status = self.data.get("adjustment_status")
        moved = count(self.data.get("openings_moved"))
        if status == "confirmed" and moved is not None:
            if moved:
                return "✓ Abertura foi ajustada automaticamente · {} movimentada(s) no Revit".format(moved)
            return "✓ Microajuste concluído · nenhuma abertura movimentada"
        return {
            "planned": "○ Microajuste proposto · movimentação no Revit ainda não confirmada",
            "applying": "◌ Aplicando microajuste · aguardando confirmação do Revit",
            "failed": "! Microajuste falhou · confira o modelo e os detalhes",
            "cancelled": "! Microajuste interrompido · confira o modelo antes de continuar",
            "not_required": "○ Microajuste não necessário nesta análise",
            # O fluxo do botao NAO roda a Etapa 3B (secao 66): dizer "nao
            # necessario" seria inventar um veredito que o motor nao deu.
            "not_evaluated": "○ Microajuste não avaliado nesta execução (Etapa 3B fora do fluxo do botão)",
        }.get(status, "○ Microajuste · confirmação ainda não recebida")

    def review_text(self):
        """Regra 76.1: encontros marcados para revisao humana. Nunca vira "erro"."""
        pendentes = count(self.data.get("review_items"))
        if pendentes is None:
            return "Revisão humana: —"
        if not pendentes:
            return "Revisão humana: nenhum encontro pendente"
        return "Revisão humana: {} encontro(s) a revisar".format(pendentes)

    def summary(self):
        # Even a reported moved count cannot certify an uncommitted transaction.
        moved = self.metric("openings_moved") if self.data.get("adjustment_status") == "confirmed" else "—"
        return "Paredes analisadas: {} · Aberturas movidas: {}\nAvisos: {} · Bloqueios críticos: {}\n{}\n{}".format(
            self.metric("walls_analyzed"), moved, self.metric("warnings"), self.metric("hard_gates"),
            self.review_text(), self.adjustment_text())

    def details(self):
        return self.summary() + "\n\n" + str(self.data.get("detail") or "Aguardando dados confirmados desta execução.")
