import logging

from AppCore.core.business.business import ModelInstanceBusiness

logger = logging.getLogger(__name__)


class FuncaoBusiness(ModelInstanceBusiness):

    def criar_funcao(
        self,
        papel_funcao: str,
        descricao: str,
        categoria: str,
        e_gratificada: bool = False,
        exige_aluno: bool = False,
        **kwargs,
    ):
        """Cria uma nova função validando unicidade de papel/função."""
        try:
            from .models import Funcao
            self.object_instance.rules.papel_funcao_unico(papel_funcao)
            return Funcao.objects.create(
                papel_funcao=papel_funcao,
                categoria=categoria,
                descricao=descricao,
                e_gratificada=e_gratificada,
                exige_aluno=exige_aluno,
                **kwargs,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar a função.', logger)

    def atualizar_dados(self, dados: dict):
        """Atualiza campos da função. Revalida papel_função se estiver nos dados."""
        try:
            if 'papel_funcao' in dados:
                self.object_instance.rules.papel_funcao_unico(
                    dados['papel_funcao'],
                    excluir_id=self.object_instance.pk,
                )
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar a função.', logger)

    def desativar(self):
        """Desativa a função. Bloqueado se estiver em uso em vínculos."""
        try:
            self.object_instance.rules.pode_desativar()
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível desativar a função.', logger)

    def reativar(self):
        """Reativa a função."""
        try:
            self.object_instance.rules.pode_reativar()
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar a função.', logger)

    def importar_funcao(
        self,
        papel_funcao: str,
        descricao: str,
        categoria,
        ativo: bool = True,
    ):
        """Cria função pelo papel normalizado se ainda não existir (sem atualizar existente)."""
        try:
            from .models import Funcao

            self.object_instance.rules.validar_dados_importacao(papel_funcao)
            categoria_resolvida = self.object_instance.helper.resolver_categoria_funcao(categoria)
            self.object_instance.rules.validar_categoria_funcao(categoria_resolvida)

            papel_gravar = ' '.join((papel_funcao or '').strip().split())
            if (descricao or '').strip():
                descricao_gravar = ' '.join(descricao.strip().split())
            else:
                descricao_gravar = papel_gravar

            funcao = self.object_instance.helper.obter_por_papel_funcao_normalizado(papel_funcao)
            if funcao:
                return funcao, False

            self.object_instance.rules.papel_funcao_unico(papel_gravar)
            funcao = Funcao.objects.create(
                papel_funcao=papel_gravar,
                descricao=descricao_gravar,
                categoria=categoria_resolvida,
                ativo=ativo,
            )
            return funcao, True
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível importar a função.', logger)
