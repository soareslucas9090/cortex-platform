import logging

from AppCore.core.business.business import ModelInstanceBusiness

logger = logging.getLogger(__name__)


class CargoBusiness(ModelInstanceBusiness):

    def criar_cargo(self, nome: str, **kwargs):
        """Cria um novo cargo validando unicidade do nome."""
        try:
            from .models import Cargo
            self.object_instance.rules.nome_unico(nome)
            return Cargo.objects.create(nome=nome, **kwargs)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o cargo.', logger)

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do cargo. Revalida nome se estiver nos dados."""
        try:
            if 'nome' in dados:
                self.object_instance.rules.nome_unico(
                    dados['nome'],
                    excluir_id=self.object_instance.pk,
                )
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar o cargo.', logger)

    def desativar(self):
        """Desativa o cargo."""
        try:
            self.object_instance.rules.pode_desativar()
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível desativar o cargo.', logger)

    def reativar(self):
        """Reativa o cargo."""
        try:
            self.object_instance.rules.pode_reativar()
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar o cargo.', logger)

    def importar_cargo(self, nome: str, ativo: bool = True):
        """Cria cargo pelo nome normalizado se ainda não existir (sem atualizar existente)."""
        try:
            from .models import Cargo

            self.object_instance.rules.validar_dados_importacao(nome)
            nome_gravar = ' '.join((nome or '').strip().split())

            cargo = self.object_instance.helper.obter_por_nome_normalizado(nome)
            if cargo:
                return cargo, False

            self.object_instance.rules.nome_unico(nome_gravar)
            cargo = Cargo.objects.create(nome=nome_gravar, ativo=ativo)
            return cargo, True
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível importar o cargo.', logger)
