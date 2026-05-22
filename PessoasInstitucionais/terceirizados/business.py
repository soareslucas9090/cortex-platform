import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import (
    NotFoundException,
    SystemErrorException,
)

from .rules import TerceirizadoRules

logger = logging.getLogger(__name__)


class TerceirizadoBusiness(ModelInstanceBusiness):

    def criar_terceirizado(
        self,
        usuario_pk: int,
        empresa_pk: int,
        cargo_funcao: str,
        data_inicio,
        data_fim=None,
        **kwargs,
    ):
        """Cria um novo perfil de terceirizado para o usuário informado."""
        from django.conf import settings
        from django.apps import apps

        from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao
        from .models import Terceirizado

        regras = TerceirizadoRules()

        # Validar que o usuário existe
        Usuario = apps.get_model(settings.AUTH_USER_MODEL)
        try:
            usuario = Usuario.objects.get(pk=usuario_pk)
        except Usuario.DoesNotExist:
            raise NotFoundException('Usuário não encontrado.')

        # Validar que o usuário ainda não tem perfil de terceirizado
        regras.usuario_sem_perfil_terceirizado(usuario_pk)

        # Validar e buscar a empresa/instituição
        try:
            empresa = EmpresaInstituicao.objects.get(pk=empresa_pk)
        except EmpresaInstituicao.DoesNotExist:
            raise NotFoundException('Empresa/instituição não encontrada.')

        regras.empresa_ativa(empresa)

        try:
            return Terceirizado.objects.create(
                usuario=usuario,
                empresa=empresa,
                cargo_funcao=cargo_funcao,
                data_inicio=data_inicio,
                data_fim=data_fim,
                **kwargs,
            )
        except Exception as e:
            logger.exception('Erro ao criar terceirizado: %s', e)
            raise SystemErrorException('Não foi possível criar o terceirizado.')

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do terceirizado. Revalida empresa se estiver nos dados."""
        regras = TerceirizadoRules(object_instance=self.object_instance)

        if 'empresa_pk' in dados:
            from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao
            empresa_pk = dados.pop('empresa_pk')
            try:
                empresa = EmpresaInstituicao.objects.get(pk=empresa_pk)
            except EmpresaInstituicao.DoesNotExist:
                raise NotFoundException('Empresa/instituição não encontrada.')
            regras.empresa_ativa(empresa)
            self.object_instance.empresa = empresa

        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar terceirizado: %s', e)
            raise SystemErrorException('Não foi possível atualizar o terceirizado.')

    def desativar(self):
        """Desativa o perfil de terceirizado."""
        regras = TerceirizadoRules(object_instance=self.object_instance)
        regras.pode_desativar()
        try:
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao desativar terceirizado: %s', e)
            raise SystemErrorException('Não foi possível desativar o terceirizado.')

    def reativar(self):
        """Reativa o perfil de terceirizado."""
        regras = TerceirizadoRules(object_instance=self.object_instance)
        regras.pode_reativar()
        try:
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao reativar terceirizado: %s', e)
            raise SystemErrorException('Não foi possível reativar o terceirizado.')
