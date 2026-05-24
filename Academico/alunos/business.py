import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException, ValidationException

logger = logging.getLogger(__name__)


class AlunoBusiness(ModelInstanceBusiness):

    def criar_aluno(self, **dados):
        from Identidade.usuarios.models import Usuario
        from .models import Aluno
        from .rules import AlunoRules
        from .choices import SituacaoAluno, FormaIngresso

        usuario_id = dados.get('usuario')
        if not usuario_id:
            raise ValidationException('O campo "usuario" é obrigatório.')

        try:
            usuario = Usuario.objects.get(pk=usuario_id)
        except Usuario.DoesNotExist:
            raise ValidationException('Usuário não encontrado.')

        if Aluno.objects.filter(usuario=usuario).exists():
            raise ValidationException('Este usuário já possui um perfil de aluno.')

        regras = AlunoRules()
        if not regras.can_create():
            raise ValidationException('Não é possível criar este aluno devido às regras de negócio.')

        aluno_dados = {
            'usuario': usuario,
            'ira': dados.get('ira', 0.0000),
            'situacao': dados.get('situacao', SituacaoAluno.MATRICULADO),
            'forma_ingresso': dados.get('forma_ingresso', FormaIngresso.VESTIBULAR),
            'ativo': dados.get('ativo', True),
        }

        try:
            return Aluno.objects.create(**aluno_dados)
        except Exception as e:
            logger.exception('Erro ao criar aluno: %s', e)
            raise SystemErrorException('Não foi possível criar o aluno.')

    def atualizar_dados(self, dados):
        try:
            for attr, value in dados.items():
                if attr != 'usuario':
                    setattr(self.object_instance, attr, value)
            self.object_instance.save()
            return self.object_instance
        except Exception as e:
            logger.exception('Erro ao atualizar aluno: %s', e)
            raise SystemErrorException('Não foi possível atualizar os dados do aluno.')

