import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class ServidorBusiness(ModelInstanceBusiness):

    def criar_servidor(self, usuario_pk: int, cargo_pk: int, categoria: int, **kwargs):
        """Cria um novo perfil de servidor para o usuário informado."""
        try:
            from django.conf import settings
            from django.apps import apps
            from PessoasInstitucionais.cargos.models import Cargo
            from .models import Servidor
            Usuario = apps.get_model(settings.AUTH_USER_MODEL)
            try:
                usuario = Usuario.objects.get(pk=usuario_pk)
            except Usuario.DoesNotExist:
                raise NotFoundException('Usuário não encontrado.')
            self.object_instance.rules.usuario_sem_perfil_servidor(usuario_pk)
            try:
                cargo = Cargo.objects.get(pk=cargo_pk)
            except Cargo.DoesNotExist:
                raise NotFoundException('Cargo não encontrado.')
            self.object_instance.rules.cargo_ativo(cargo)
            return Servidor.objects.create(
                usuario=usuario,
                cargo=cargo,
                categoria=categoria,
                **kwargs,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o servidor.', logger)

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do servidor. Revalida cargo se estiver nos dados."""
        try:
            if 'cargo_pk' in dados:
                from PessoasInstitucionais.cargos.models import Cargo
                cargo_pk = dados.pop('cargo_pk')
                try:
                    cargo = Cargo.objects.get(pk=cargo_pk)
                except Cargo.DoesNotExist:
                    raise NotFoundException('Cargo não encontrado.')
                self.object_instance.rules.cargo_ativo(cargo)
                self.object_instance.cargo = cargo
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar o servidor.', logger)

    def desativar(self):
        """Desativa o perfil de servidor."""
        try:
            self.object_instance.rules.pode_desativar()
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível desativar o servidor.', logger)

    def reativar(self):
        """Reativa o perfil de servidor."""
        try:
            self.object_instance.rules.pode_reativar()
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar o servidor.', logger)
