from AppCore.core.state.state import ModelInstanceState

from .choices import StatusSolicitacaoTrocaTitular


class SolicitacaoTrocaTitularState(ModelInstanceState):
    status_choices_class = StatusSolicitacaoTrocaTitular
    transicoes_permitidas = frozenset()

    def pode_aceitar(self, usuario, possui_itens_abertos=None) -> bool:
        return False

    def pode_recusar(self, usuario) -> bool:
        return False

    def pode_cancelar(self, usuario) -> bool:
        return False


class SolicitacaoTrocaTitularPendenteState(SolicitacaoTrocaTitularState):
    transicoes_permitidas = frozenset({
        StatusSolicitacaoTrocaTitular.ACEITA,
        StatusSolicitacaoTrocaTitular.RECUSADA,
        StatusSolicitacaoTrocaTitular.CANCELADA,
    })

    def pode_aceitar(self, usuario, possui_itens_abertos=None) -> bool:
        if possui_itens_abertos is None:
            possui_itens_abertos = getattr(
                self.object_instance,
                '_emprestimo_aberto',
                getattr(self.object_instance.emprestimo, '_aberto', False),
            )
        return bool(
            self.object_instance.destinatario_id == usuario.pk
            and possui_itens_abertos
        )

    def pode_recusar(self, usuario) -> bool:
        return self.object_instance.destinatario_id == usuario.pk

    def pode_cancelar(self, usuario) -> bool:
        return self.object_instance.solicitante_id == usuario.pk


class SolicitacaoTrocaTitularAceitaState(SolicitacaoTrocaTitularState):
    pass


class SolicitacaoTrocaTitularRecusadaState(SolicitacaoTrocaTitularState):
    pass


class SolicitacaoTrocaTitularCanceladaState(SolicitacaoTrocaTitularState):
    pass


ESTADOS_SOLICITACAO_TROCA_TITULAR = {
    StatusSolicitacaoTrocaTitular.PENDENTE: SolicitacaoTrocaTitularPendenteState,
    StatusSolicitacaoTrocaTitular.ACEITA: SolicitacaoTrocaTitularAceitaState,
    StatusSolicitacaoTrocaTitular.RECUSADA: SolicitacaoTrocaTitularRecusadaState,
    StatusSolicitacaoTrocaTitular.CANCELADA: SolicitacaoTrocaTitularCanceladaState,
}
