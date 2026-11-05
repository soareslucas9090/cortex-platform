from zoneinfo import ZoneInfo

from django.db.models import F, Q
from django.db.models.functions import Lower

from AppCore.core.helpers.helpers import ModelInstanceHelpers

from .choices import OrigemSolicitacaoAcesso, StatusSolicitacaoAcesso
from .constantes import ASSINATURAS_ANEXO, ORDENACAO_PADRAO_ALUNO, ORDENACOES_ALUNO

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

    # ------------------------------------------------------------------
    # Pedido do aluno
    # ------------------------------------------------------------------

    def _com_relacionamentos(self):
        from .models import SolicitacaoAcesso

        return SolicitacaoAcesso.objects.select_related(
            'avaliada_por',
            'liberado_por',
            'aluno__usuario',
            'aluno_curso',
            'tipo',
        )

    def _ordenar_do_aluno(self, queryset, ordenacao):
        """
        Aplica a ``ordenacao`` da listagem do aluno; valor fora de ORDENACOES_ALUNO usa o padrão.
        ``tipo`` ordena pelo nome do tipo; pedidos ainda não avaliados ficam no fim ao ordenar
        por avaliador.
        """
        if ordenacao not in ORDENACOES_ALUNO:
            ordenacao = ORDENACAO_PADRAO_ALUNO

        avaliador = F('avaliada_por__nome')
        campos = {
            'data_liberacao': ('data_acesso', 'hora_solicitada', '-created_at', '-pk'),
            '-data_liberacao': ('-data_acesso', '-hora_solicitada', '-created_at', '-pk'),
            'data_solicitacao': ('created_at', 'pk'),
            '-data_solicitacao': ('-created_at', '-pk'),
            'tipo': (Lower('tipo__nome'), '-created_at', '-pk'),
            '-tipo': (Lower('tipo__nome').desc(), '-created_at', '-pk'),
            'motivo': (Lower('motivo'), '-created_at', '-pk'),
            '-motivo': (Lower('motivo').desc(), '-created_at', '-pk'),
            'avaliado_por': (avaliador.asc(nulls_last=True), '-created_at', '-pk'),
            '-avaliado_por': (avaliador.desc(nulls_last=True), '-created_at', '-pk'),
        }
        return queryset.order_by(*campos[ordenacao])

    def listar_do_aluno(self, usuario, status=None, tipo=None, busca=None, ordenacao=None):
        """
        Pedidos e autorizações do próprio aluno (inclusive as criadas pela gestão).
        Os filtros e a ordenação só reduzem/reordenam o conjunto do próprio aluno.
        """
        aluno = getattr(usuario, 'aluno', None)
        if aluno is None:
            return self._com_relacionamentos().none()

        queryset = self._com_relacionamentos().filter(aluno=aluno)
        if status is not None:
            queryset = queryset.filter(status=status)
        if tipo is not None:
            queryset = queryset.filter(tipo_id=tipo)
        if busca:
            queryset = queryset.filter(
                Q(motivo__unaccent__icontains=busca)
                | Q(avaliada_por__nome__unaccent__icontains=busca)
            )
        return self._ordenar_do_aluno(queryset, ordenacao)

    def listar_com_anexo_visivel(self, usuario, vinculos_gestao):
        """Solicitações cujo comprovante o usuário pode abrir: as próprias e as do escopo da gestão."""
        filtro = Q(aluno_curso__in=vinculos_gestao)
        aluno = getattr(usuario, 'aluno', None)
        if aluno is not None:
            filtro |= Q(aluno=aluno)
        return self._com_relacionamentos().filter(filtro)

    def obter_vinculo_elegivel(self, aluno, aluno_curso_id, vinculos_elegiveis):
        """Vínculo informado, se for do próprio aluno e elegível ao acesso ao campus; senão None."""
        return (
            vinculos_elegiveis.select_related('curso')
            .filter(pk=aluno_curso_id, aluno=aluno)
            .first()
        )

    def detectar_tipo_anexo(self, arquivo):
        """Identifica PDF, PNG ou JPEG pela assinatura do arquivo, não pelo content-type enviado."""
        if hasattr(arquivo, 'seek'):
            arquivo.seek(0)
        cabecalho = arquivo.read(8)
        if hasattr(arquivo, 'seek'):
            arquivo.seek(0)
        for assinatura, content_type in ASSINATURAS_ANEXO:
            if cabecalho.startswith(assinatura):
                return content_type
        return None
