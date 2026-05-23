from django.db import transaction

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import ValidationException


class AlunoBusiness(ModelInstanceBusiness):
    
    def criar_aluno(self, **dados):
        from Identidade.usuarios.models import Usuario
        from .models import Aluno
        from .rules import AlunoRules

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

        # Extract only fields belonging to Aluno
        aluno_dados = {
            'usuario': usuario,
            'ira': dados.get('ira', 0.0000),
            'situacao': dados.get('situacao', 1), # MATRICULADO
            'forma_ingresso': dados.get('forma_ingresso', 1), # VESTIBULAR
            'ativo': dados.get('ativo', True),
        }

        return Aluno.objects.create(**aluno_dados)

    def atualizar_dados(self, dados):
        try:
            for attr, value in dados.items():
                if attr != 'usuario': # Cannot change the linked User
                    setattr(self.object_instance, attr, value)
            self.object_instance.save()
            return self.object_instance
        except Exception as e:
            from AppCore.core.exceptions.exceptions import SystemErrorException
            raise SystemErrorException('Não foi possível atualizar os dados do aluno.')
