import logging

from django.apps import apps

from AppCore.core.business.business import ModelInstanceBusiness

logger = logging.getLogger(__name__)


class PermissaoFuncaoTransporteBusiness(ModelInstanceBusiness):

    def criar_permissao(self, funcao_id: int, conferir=False):
        try:
            from .models import PermissaoFuncaoTransporte

            Funcao = apps.get_model('funcoes', 'Funcao')
            funcao = Funcao.objects.get(pk=funcao_id)
            self.object_instance.rules.validar_funcao_ativa(funcao)
            self.object_instance.rules.validar_funcao_sem_permissao(
                self.object_instance.helper.existe_para_funcao(funcao_id),
            )
            return PermissaoFuncaoTransporte.objects.create(
                funcao=funcao,
                conferir=conferir,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível criar a permissão de Transporte.',
                logger,
            )

    def atualizar_capacidades(self, dados: dict):
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível atualizar a permissão de Transporte.',
                logger,
            )


class PermissaoUsuarioTransporteBusiness(ModelInstanceBusiness):

    def criar_permissao(self, usuario_id: int, conferir=False):
        try:
            from .models import PermissaoUsuarioTransporte

            Usuario = apps.get_model('usuarios', 'Usuario')
            usuario = Usuario.objects.get(pk=usuario_id)
            self.object_instance.rules.validar_usuario_ativo(usuario)
            self.object_instance.rules.validar_usuario_sem_permissao(
                self.object_instance.helper.existe_para_usuario(usuario_id),
            )
            return PermissaoUsuarioTransporte.objects.create(
                usuario=usuario,
                conferir=conferir,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível criar a permissão de Transporte por usuário.',
                logger,
            )

    def atualizar_capacidades(self, dados: dict):
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível atualizar a permissão de Transporte por usuário.',
                logger,
            )
