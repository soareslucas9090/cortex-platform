import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException

logger = logging.getLogger(__name__)


class EmpresaInstituicaoBusiness(ModelInstanceBusiness):

    def criar_empresa(self, dados: dict):
        """Cria uma nova empresa validando unicidade do nome e CNPJ."""
        from .models import EmpresaInstituicao

        nome = dados.get('nome')
        cnpj = dados.get('cnpj')

        if nome:
            self.object_instance.rules.nome_unico(nome)
        if cnpj:
            self.object_instance.rules.cnpj_unico(cnpj)

        try:
            return EmpresaInstituicao.objects.create(**dados)
        except Exception as e:
            logger.exception('Erro ao criar empresa/instituição: %s', e)
            raise SystemErrorException('Não foi possível criar a empresa/instituição.')

    def atualizar_dados(self, dados: dict):
        """Atualiza campos da empresa/instituição."""
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

        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar empresa/instituição: %s', e)
            raise SystemErrorException('Não foi possível atualizar a empresa/instituição.')

    def desativar(self):
        """Desativa a empresa/instituição."""
        self.object_instance.rules.pode_desativar()
        try:
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao desativar empresa/instituição: %s', e)
            raise SystemErrorException('Não foi possível desativar a empresa/instituição.')

    def reativar(self):
        """Reativa a empresa/instituição."""
        self.object_instance.rules.pode_reativar()
        try:
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao reativar empresa/instituição: %s', e)
            raise SystemErrorException('Não foi possível reativar a empresa/instituição.')
