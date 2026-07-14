from django.apps import apps
from django.conf import settings

from AppCore.core.rules.rules import ModelInstanceRules

from Infraestrutura.permissoes.access import usuario_pode_autorizar_infraestrutura


class AutorizacaoRules(ModelInstanceRules):

    def validar_alvo_xor(self, sala_id=None, recurso_id=None) -> bool:
        """Exige exatamente um alvo: sala ou recurso."""
        tem_sala = sala_id is not None
        tem_recurso = recurso_id is not None
        if tem_sala and tem_recurso:
            self.return_exception('Informe apenas sala ou recurso, não ambos.')
        if not tem_sala and not tem_recurso:
            self.return_exception('Informe sala ou recurso como alvo da autorização.')
        return True

    def validar_vigencia(self, data_inicio, data_fim=None) -> bool:
        """Data de fim, quando informada, deve ser igual ou posterior ao início."""
        if data_fim is not None and data_fim < data_inicio:
            self.return_exception('A data de fim deve ser igual ou posterior à data de início.')
        return True

    def pode_conceder(self, concedente) -> bool:
        """Somente usuários com capacidade autorizar podem conceder."""
        if not usuario_pode_autorizar_infraestrutura(concedente):
            self.return_exception('Você não tem permissão para conceder autorizações.')
        return True

    def pode_revogar(self, revogador) -> bool:
        """Somente usuários com capacidade autorizar podem revogar."""
        if not usuario_pode_autorizar_infraestrutura(revogador):
            self.return_exception('Você não tem permissão para revogar autorizações.')
        if self.object_instance.revogado_em is not None:
            self.return_exception('Esta autorização já foi revogada.')
        return True

    def validar_beneficiario(self, beneficiario_id: int) -> bool:
        """Beneficiário deve existir e estar ativo."""
        Usuario = apps.get_model(settings.AUTH_USER_MODEL)
        beneficiario = Usuario.objects.filter(pk=beneficiario_id).first()
        if beneficiario is None:
            self.return_exception('Beneficiário informado não encontrado.')
        if not beneficiario.ativo:
            self.return_exception('O beneficiário informado está inativo.')
        return True

    def validar_sem_sobreposicao(
        self,
        beneficiario_id: int,
        data_inicio,
        data_fim=None,
        sala_id=None,
        recurso_id=None,
        excluir_id=None,
    ) -> bool:
        """Impede autorização com período sobreposto a outra não revogada."""
        existentes = self.object_instance.helper.buscar_nao_revogadas_sobrepostas(
            beneficiario_id=beneficiario_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            sala_id=sala_id,
            recurso_id=recurso_id,
            excluir_id=excluir_id,
        )
        if existentes.exists():
            self.return_exception(
                'Já existe autorização não revogada para este beneficiário, alvo e período sobreposto.',
            )
        return True

    def pode_reativar(self, concedente) -> bool:
        """Somente autorizações revogadas podem ser reativadas."""
        if not usuario_pode_autorizar_infraestrutura(concedente):
            self.return_exception('Você não tem permissão para reativar autorizações.')
        if self.object_instance.revogado_em is None:
            self.return_exception('Esta autorização não está revogada.')
        return True

    def validar_alvo_ativo(self, sala_id=None, recurso_id=None) -> bool:
        """Sala ou recurso informado deve existir e estar ativo."""
        if sala_id is not None:
            Sala = apps.get_model('salas', 'Sala')
            sala = Sala.objects.filter(pk=sala_id).first()
            if sala is None:
                self.return_exception('Sala informada não encontrada.')
            if not sala.ativo:
                self.return_exception('A sala informada está inativa.')
        if recurso_id is not None:
            Recurso = apps.get_model('recursos', 'Recurso')
            recurso = Recurso.objects.filter(pk=recurso_id).first()
            if recurso is None:
                self.return_exception('Recurso informado não encontrado.')
            if not recurso.ativo:
                self.return_exception('O recurso informado está inativo.')
        return True
