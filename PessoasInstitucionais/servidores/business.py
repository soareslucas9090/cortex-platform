import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import (
    NotFoundException,
    SystemErrorException,
)

from .rules import ServidorRules

logger = logging.getLogger(__name__)


class ServidorBusiness(ModelInstanceBusiness):

    def criar_servidor(self, usuario_pk: int, cargo_pk: int, categoria: int, **kwargs):
        """Cria um novo perfil de servidor para o usuário informado."""
        from django.conf import settings
        from django.apps import apps

        from PessoasInstitucionais.cargos.models import Cargo
        from .models import Servidor

        regras = ServidorRules()

        # Validar que o usuário existe
        Usuario = apps.get_model(settings.AUTH_USER_MODEL)
        try:
            usuario = Usuario.objects.get(pk=usuario_pk)
        except Usuario.DoesNotExist:
            raise NotFoundException('Usuário não encontrado.')

        # Validar que o usuário ainda não tem perfil de servidor
        regras.usuario_sem_perfil_servidor(usuario_pk)

        # Validar e buscar o cargo
        try:
            cargo = Cargo.objects.get(pk=cargo_pk)
        except Cargo.DoesNotExist:
            raise NotFoundException('Cargo não encontrado.')

        regras.cargo_ativo(cargo)

        try:
            return Servidor.objects.create(
                usuario=usuario,
                cargo=cargo,
                categoria=categoria,
                **kwargs,
            )
        except Exception as e:
            logger.exception('Erro ao criar servidor: %s', e)
            raise SystemErrorException('Não foi possível criar o servidor.')

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do servidor. Revalida cargo se estiver nos dados."""
        regras = ServidorRules(object_instance=self.object_instance)

        if 'cargo_pk' in dados:
            from PessoasInstitucionais.cargos.models import Cargo
            cargo_pk = dados.pop('cargo_pk')
            try:
                cargo = Cargo.objects.get(pk=cargo_pk)
            except Cargo.DoesNotExist:
                raise NotFoundException('Cargo não encontrado.')
            regras.cargo_ativo(cargo)
            self.object_instance.cargo = cargo

        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar servidor: %s', e)
            raise SystemErrorException('Não foi possível atualizar o servidor.')

    def desativar(self):
        """Desativa o perfil de servidor."""
        regras = ServidorRules(object_instance=self.object_instance)
        regras.pode_desativar()
        try:
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao desativar servidor: %s', e)
            raise SystemErrorException('Não foi possível desativar o servidor.')

    def reativar(self):
        """Reativa o perfil de servidor."""
        regras = ServidorRules(object_instance=self.object_instance)
        regras.pode_reativar()
        try:
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao reativar servidor: %s', e)
            raise SystemErrorException('Não foi possível reativar o servidor.')
