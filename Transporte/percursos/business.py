import logging

from AppCore.core.business.business import ModelInstanceBusiness

logger = logging.getLogger(__name__)


class PercursoBusiness(ModelInstanceBusiness):

    def criar_percurso(self, apelido: str, descricao: str, **kwargs):
        """Cria um novo percurso validando unicidade do apelido."""
        try:
            from .models import Percurso
            self.object_instance.rules.validar_apelido_unico(apelido)
            return Percurso.objects.create(apelido=apelido, descricao=descricao, **kwargs)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o percurso.', logger)

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do percurso. Revalida apelido se estiver nos dados."""
        try:
            if 'apelido' in dados:
                self.object_instance.rules.validar_apelido_unico(
                    dados['apelido'],
                    excluir_id=self.object_instance.pk,
                )
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar o percurso.', logger)

    def desativar(self):
        """Desativa o percurso."""
        try:
            self.object_instance.rules.pode_desativar()
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível desativar o percurso.', logger)

    def reativar(self):
        """Reativa o percurso."""
        try:
            self.object_instance.rules.pode_reativar()
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar o percurso.', logger)
