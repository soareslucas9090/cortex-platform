from datetime import datetime

from django.utils import timezone

from AppCore.core.exceptions.exceptions import BusinessRuleException, ValidationException
from AppCore.core.rules.rules import ModelInstanceRules
from Identidade.usuarios.models import TipoContaColetiva


class EventoAcessoRules(ModelInstanceRules):

    def validar_grupo_pendente(self, eventos):
        if not eventos:
            raise BusinessRuleException('A autorização de acesso não foi encontrada.')
        pendentes = [evento for evento in eventos if not hasattr(evento, 'registro')]
        if not pendentes:
            return True
        agora = timezone.localtime()
        inicios = [
            timezone.make_aware(datetime.combine(evento.data_acesso, evento.hora_prevista)) for evento in pendentes
        ]
        if any(evento.expirado_em for evento in pendentes) or any(agora > inicio for inicio in inicios):
            raise BusinessRuleException('A autorização expirou e não pode mais ser registrada.')
        return True

    def validar_alunos_do_grupo(self, eventos, aluno_ids):
        ids_grupo = {evento.aluno_id for evento in eventos}
        ids_informados = set(aluno_ids or [])
        if not ids_informados:
            raise ValidationException('Informe ao menos um aluno para a conferência da turma.')
        if not ids_informados.issubset(ids_grupo):
            raise ValidationException('Há aluno informado que não pertence a esta autorização.')
        return True

    def validar_identificacao_responsavel(self, operador, responsavel_id=None):
        if operador.is_staff or operador.is_admin or operador.is_superuser:
            return True
        if not operador.usuario_coletivo:
            if responsavel_id and responsavel_id != operador.pk:
                raise BusinessRuleException('O responsável deve ser o próprio operador.')
            return True
        if operador.tipo_conta_coletiva != TipoContaColetiva.GUARITA:
            raise BusinessRuleException('Esta conta coletiva não pode operar a portaria.')
        if not responsavel_id:
            raise ValidationException('O responsável pela liberação é obrigatório.')
        return True

    def validar_responsavel_elegivel(self, responsavel):
        if responsavel is None:
            raise BusinessRuleException('O responsável informado não pertence ao pool da guarita.')
        return True
