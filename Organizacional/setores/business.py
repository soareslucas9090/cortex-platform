import logging

from AppCore.core.business.business import ModelInstanceBusiness

logger = logging.getLogger(__name__)


class SetorBusiness(ModelInstanceBusiness):

    def criar_setor(self, nome: str, sigla: str, **kwargs):
        """Cria um novo setor validando unicidade de sigla."""
        try:
            from .models import Setor
            self.object_instance.rules.sigla_unica(sigla)
            return Setor.objects.create(nome=nome, sigla=sigla, **kwargs)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o setor.', logger)

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do setor. Revalida sigla se estiver nos dados."""
        try:
            if 'sigla' in dados:
                self.object_instance.rules.sigla_unica(
                    dados['sigla'],
                    excluir_id=self.object_instance.pk,
                )
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar o setor.', logger)

    def desativar(self):
        """Desativa o setor. Bloqueado se houver vínculos ativos."""
        try:
            self.object_instance.rules.pode_desativar()
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível desativar o setor.', logger)

    def reativar(self):
        """Reativa o setor."""
        try:
            self.object_instance.rules.pode_reativar()
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar o setor.', logger)
