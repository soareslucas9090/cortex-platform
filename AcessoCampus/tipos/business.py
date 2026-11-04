import logging

from AppCore.core.business.business import ModelInstanceBusiness

logger = logging.getLogger(__name__)


class TipoAutorizacaoAcessoBusiness(ModelInstanceBusiness):

    def criar_tipo(self, nome: str, **kwargs):
        try:
            from .models import TipoAutorizacaoAcesso

            self.object_instance.rules.validar_nome_unico(nome)
            kwargs.pop('eh_base', None)
            return TipoAutorizacaoAcesso.objects.create(nome=nome.strip(), eh_base=False, **kwargs)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o tipo de autorização.', logger)

    def atualizar_dados(self, dados: dict):
        try:
            dados = dict(dados)
            dados.pop('eh_base', None)
            if 'nome' in dados:
                nome = (dados['nome'] or '').strip()
                self.object_instance.rules.validar_nome_tipo_base(nome)
                self.object_instance.rules.validar_nome_unico(
                    nome,
                    excluir_id=self.object_instance.pk,
                )
                dados['nome'] = nome
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar o tipo de autorização.', logger)

    def desativar(self):
        try:
            self.object_instance.rules.pode_desativar()
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível desativar o tipo de autorização.', logger)

    def reativar(self):
        try:
            self.object_instance.rules.pode_reativar()
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar o tipo de autorização.', logger)
