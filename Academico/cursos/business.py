import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException

logger = logging.getLogger(__name__)


class CursoBusiness(ModelInstanceBusiness):

    def criar_curso(self, nome: str, codigo_curso: str, **kwargs):
        """Cria um novo curso validando unicidade do código."""
        from .models import Curso
        self.object_instance.rules.codigo_unico(codigo_curso)
        try:
            return Curso.objects.create(nome=nome, codigo_curso=codigo_curso, **kwargs)
        except Exception as e:
            logger.exception('Erro ao criar curso: %s', e)
            raise SystemErrorException('Não foi possível criar o curso.')

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do curso. Revalida código se estiver nos dados."""
        if 'codigo_curso' in dados:
            self.object_instance.rules.codigo_unico(
                dados['codigo_curso'],
                excluir_id=self.object_instance.pk,
            )
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar curso: %s', e)
            raise SystemErrorException('Não foi possível atualizar o curso.')

    def desativar(self):
        """Desativa o curso."""
        self.object_instance.rules.pode_desativar()
        try:
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao desativar curso: %s', e)
            raise SystemErrorException('Não foi possível desativar o curso.')

    def reativar(self):
        """Reativa o curso."""
        self.object_instance.rules.pode_reativar()
        try:
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao reativar curso: %s', e)
            raise SystemErrorException('Não foi possível reativar o curso.')
