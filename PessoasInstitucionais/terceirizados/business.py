import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import (
    NotFoundException,
    ValidationException,
)

logger = logging.getLogger(__name__)


class TerceirizadoBusiness(ModelInstanceBusiness):

    def criar_terceirizado(
        self,
        usuario_pk: int,
        empresa_pk: int = None,
        data_inicio=None,
        cargo_pk: int = None,
        data_fim=None,
        **kwargs,
    ):
        """Cria um novo perfil de terceirizado para o usuário informado."""
        try:
            from django.conf import settings
            from django.apps import apps
            from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao
            from .models import Terceirizado
            Usuario = apps.get_model(settings.AUTH_USER_MODEL)
            try:
                usuario = Usuario.objects.get(pk=usuario_pk)
            except Usuario.DoesNotExist:
                raise NotFoundException('Usuário não encontrado.')
            self.object_instance.rules.usuario_sem_perfil_terceirizado(usuario_pk)
            empresa_id = empresa_pk or kwargs.pop('empresa_instituicao_pk', None)
            if not empresa_id:
                raise ValidationException('O campo empresa/instituição é obrigatório.')
            try:
                empresa = EmpresaInstituicao.objects.get(pk=empresa_id)
            except EmpresaInstituicao.DoesNotExist:
                raise NotFoundException('Empresa/instituição não encontrada.')
            self.object_instance.rules.empresa_ativa(empresa)
            cargo = None
            if cargo_pk is not None:
                from PessoasInstitucionais.cargos.models import Cargo
                try:
                    cargo = Cargo.objects.get(pk=cargo_pk)
                except Cargo.DoesNotExist:
                    raise NotFoundException('Cargo não encontrado.')
                self.object_instance.rules.cargo_ativo(cargo)
            return Terceirizado.objects.create(
                usuario=usuario,
                empresa_instituicao=empresa,
                cargo=cargo,
                data_inicio=data_inicio,
                data_fim=data_fim,
                **kwargs,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o terceirizado.', logger)

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do terceirizado. Revalida empresa e cargo se estiverem nos dados."""
        try:
            if 'empresa_pk' in dados or 'empresa_instituicao_pk' in dados:
                from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao
                empresa_pk = dados.pop('empresa_pk', None) or dados.pop('empresa_instituicao_pk', None)
                try:
                    empresa = EmpresaInstituicao.objects.get(pk=empresa_pk)
                except EmpresaInstituicao.DoesNotExist:
                    raise NotFoundException('Empresa/instituição não encontrada.')
                self.object_instance.rules.empresa_ativa(empresa)
                self.object_instance.empresa_instituicao = empresa
            if 'cargo_pk' in dados:
                from PessoasInstitucionais.cargos.models import Cargo
                cargo_pk = dados.pop('cargo_pk')
                cargo = None
                if cargo_pk is not None:
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
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar o terceirizado.', logger)

    def desativar(self):
        """Desativa o perfil de terceirizado."""
        try:
            self.object_instance.rules.pode_desativar()
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível desativar o terceirizado.', logger)

    def reativar(self):
        """Reativa o perfil de terceirizado."""
        try:
            self.object_instance.rules.pode_reativar()
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar o terceirizado.', logger)
