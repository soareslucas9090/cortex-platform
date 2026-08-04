import logging

from AppCore.core.business.business import ModelInstanceBusiness
logger = logging.getLogger(__name__)


class CursoBusiness(ModelInstanceBusiness):

    def criar_curso(self, nome: str, codigo_curso: str, **kwargs):
        """Cria um novo curso validando unicidade do código."""
        try:
            from .models import Curso
            self.object_instance.rules.codigo_unico(codigo_curso)
            return Curso.objects.create(nome=nome, codigo_curso=codigo_curso, **kwargs)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o curso.', logger)

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do curso. Revalida código se estiver nos dados."""
        try:
            if 'codigo_curso' in dados:
                self.object_instance.rules.codigo_unico(
                    dados['codigo_curso'],
                    excluir_id=self.object_instance.pk,
                )
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar o curso.', logger)

    def desativar(self):
        """Desativa o curso."""
        try:
            self.object_instance.rules.pode_desativar()
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível desativar o curso.', logger)

    def reativar(self):
        """Reativa o curso."""
        try:
            self.object_instance.rules.pode_reativar()
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar o curso.', logger)
