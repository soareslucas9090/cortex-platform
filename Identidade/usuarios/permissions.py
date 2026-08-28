from AppCore.core.users_permissions.user_permission import UserModelPermission

from Infraestrutura.permissoes.access import usuario_tem_acesso_total_infraestrutura
from Infraestrutura.permissoes.choices import (
    capacidades_infraestrutura_completas,
    capacidades_infraestrutura_vazias,
)
from Infraestrutura.permissoes.models import PermissaoFuncaoInfraestrutura

from .choices import (
    PERMISSAO_CORTEX_EDITAR_EU,
    PERMISSAO_CORTEX_EDITAR_TUDO,
    PERMISSAO_CORTEX_LER_TUDO,
)


class UsuarioPermissions(UserModelPermission):
    """
    Camada de Permissões do Usuário.
    Define as permissões do usuário para os diferentes módulos do frontend.
    """

    def permissoes_cortex(self) -> dict:
        """
        Permissão para o módulo principal (cortex).
        - EDITAR_TUDO: Se o usuário é staff, admin ou superuser.
        - LER_TUDO: Se possui perfil ativo de servidor ou terceirizado.
        - EDITAR_EU: Somente aluno ou qualquer outro caso básico.
        """
        user = self.object_instance
        if not user:
            return {'cortex': PERMISSAO_CORTEX_EDITAR_EU}

        if user.is_staff or user.is_admin or user.is_superuser:
            cortex_perm = PERMISSAO_CORTEX_EDITAR_TUDO
        else:
            tem_servidor_ativo = False
            try:
                tem_servidor_ativo = (
                    hasattr(user, 'servidor')
                    and user.servidor is not None
                    and getattr(user.servidor, 'ativo', False)
                )
            except Exception:
                pass

            tem_terceirizado_ativo = False
            try:
                tem_terceirizado_ativo = (
                    hasattr(user, 'terceirizado')
                    and user.terceirizado is not None
                    and getattr(user.terceirizado, 'ativo', False)
                )
            except Exception:
                pass

            if tem_servidor_ativo or tem_terceirizado_ativo:
                cortex_perm = PERMISSAO_CORTEX_LER_TUDO
            else:
                cortex_perm = PERMISSAO_CORTEX_EDITAR_EU

        return {
            'cortex': cortex_perm,
        }

    def permissoes_infraestrutura(self) -> dict:
        """
        Capacidades do módulo Infraestrutura: união (OR) das flags por função
        (vínculos ativos) e por usuário (PermissaoUsuarioInfraestrutura).
        Admin e superuser recebem acesso total a todas as capacidades.
        """
        user = self.object_instance
        if not user:
            return {'infraestrutura': capacidades_infraestrutura_vazias()}

        if usuario_tem_acesso_total_infraestrutura(user):
            return {'infraestrutura': capacidades_infraestrutura_completas()}

        return {
            'infraestrutura': PermissaoFuncaoInfraestrutura().helper.compilar_do_usuario(user),
        }

    def permissoes_transporte(self) -> dict:
        """
        Acesso ao módulo Transporte (cadastro de percursos e demais cadastros de TI).
        Apenas L3 (is_staff, is_admin ou superuser) recebe gerenciar=True, para o
        frontend exibir o menu somente ao perfil TI.
        """
        user = self.object_instance
        if not user:
            return {'transporte': {'gerenciar': False}}

        gerenciar = bool(user.is_staff or user.is_admin or user.is_superuser)
        return {'transporte': {'gerenciar': gerenciar}}
