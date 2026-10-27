from zoneinfo import ZoneInfo

from AppCore.core.helpers.helpers import ModelInstanceHelpers

from .choices import OrigemSolicitacaoAcesso, StatusSolicitacaoAcesso

FUSO_FORTALEZA = ZoneInfo('America/Fortaleza')


def texto_historico(descricao, momento) -> str:
    local = momento.astimezone(FUSO_FORTALEZA)
    return f'{descricao} {local.strftime("%d/%m/%y")} às {local.strftime("%H:%M")}'


class SolicitacaoAcessoHelpers(ModelInstanceHelpers):

    def montar_historico(self) -> list:
        solicitacao = self.object_instance
        if solicitacao.origem == OrigemSolicitacaoAcesso.GESTAO:
            eventos = [('Autorização registrada', solicitacao.created_at)]
        else:
            eventos = [('Solicitação enviada', solicitacao.created_at)]
            if solicitacao.status == StatusSolicitacaoAcesso.ACEITA and solicitacao.avaliada_em:
                eventos.append(('Solicitação aceita', solicitacao.avaliada_em))
            elif solicitacao.status == StatusSolicitacaoAcesso.RECUSADA and solicitacao.avaliada_em:
                eventos.append(('Solicitação recusada', solicitacao.avaliada_em))
        return [
            {
                'descricao': descricao,
                'em': momento,
                'texto': texto_historico(descricao, momento),
            }
            for descricao, momento in eventos
        ]

    def existe_autorizacao_aceita(self, aluno_ids, data_acesso, tipo, excluir_pk=None) -> bool:
        from .models import SolicitacaoAcesso

        existentes = SolicitacaoAcesso.objects.filter(
            aluno_id__in=aluno_ids,
            data_acesso=data_acesso,
            tipo=tipo,
            status=StatusSolicitacaoAcesso.ACEITA,
        )
        if excluir_pk is not None:
            existentes = existentes.exclude(pk=excluir_pk)
        return existentes.exists()
