import logging

from django.apps import apps

from AppCore.core.business.business import ModelInstanceBusiness

logger = logging.getLogger(__name__)


class PermissaoFuncaoInfraestruturaBusiness(ModelInstanceBusiness):

    def criar_permissao(self, funcao_id: int, **capacidades):
        """Cria permissões de Infraestrutura para uma função."""
        try:
            from .models import PermissaoFuncaoInfraestrutura
            Funcao = apps.get_model('funcoes', 'Funcao')
            funcao = Funcao.objects.get(pk=funcao_id)
            self.object_instance.rules.funcao_deve_estar_ativa(funcao)
            self.object_instance.rules.funcao_sem_permissao_existente(funcao_id)
            return PermissaoFuncaoInfraestrutura.objects.create(
                funcao=funcao,
                **capacidades,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar a permissão de Infraestrutura.', logger)

    def atualizar_capacidades(self, dados: dict):
        """Atualiza as capacidades configuradas para a função."""
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar a permissão de Infraestrutura.', logger)


class PermissaoUsuarioInfraestruturaBusiness(ModelInstanceBusiness):

    def criar_permissao(self, usuario_id: int, **capacidades):
        """Cria permissões de Infraestrutura para um usuário."""
        try:
            from .models import PermissaoUsuarioInfraestrutura
            Usuario = apps.get_model('usuarios', 'Usuario')
            usuario = Usuario.objects.get(pk=usuario_id)
            self.object_instance.rules.usuario_deve_estar_ativo(usuario)
            self.object_instance.rules.usuario_sem_permissao_existente(usuario_id)
            return PermissaoUsuarioInfraestrutura.objects.create(
                usuario=usuario,
                **capacidades,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar a permissão de Infraestrutura por usuário.', logger)

    def atualizar_capacidades(self, dados: dict):
        """Atualiza as capacidades configuradas para o usuário."""
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar a permissão de Infraestrutura por usuário.', logger)
