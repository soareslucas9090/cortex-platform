import logging

from AppCore.core.business.business import ModelInstanceBusiness

logger = logging.getLogger(__name__)


class EmpresaInstituicaoBusiness(ModelInstanceBusiness):

    def criar_empresa(self, dados: dict):
        """Cria uma nova empresa validando unicidade do nome e CNPJ."""
        try:
            from .models import EmpresaInstituicao
            nome = dados.get('nome')
            cnpj = dados.get('cnpj')
            if nome:
                self.object_instance.rules.nome_unico(nome)
            if cnpj:
                self.object_instance.rules.cnpj_unico(cnpj)
            return EmpresaInstituicao.objects.create(**dados)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar a empresa/instituição.', logger)

    def atualizar_dados(self, dados: dict):
        """Atualiza campos da empresa/instituição."""
        try:
            if 'nome' in dados:
                self.object_instance.rules.nome_unico(
                    dados['nome'],
                    excluir_id=self.object_instance.pk,
                )
            if 'cnpj' in dados:
                self.object_instance.rules.cnpj_unico(
                    dados['cnpj'],
                    excluir_id=self.object_instance.pk,
                )
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar a empresa/instituição.', logger)

    def desativar(self):
        """Desativa a empresa/instituição."""
        try:
            self.object_instance.rules.pode_desativar()
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível desativar a empresa/instituição.', logger)

    def reativar(self):
        """Reativa a empresa/instituição."""
        try:
            self.object_instance.rules.pode_reativar()
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar a empresa/instituição.', logger)
