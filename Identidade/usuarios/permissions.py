from AppCore.core.users_permissions.user_permission import UserModelPermission


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
            return {'cortex': 'EDITAR_EU'}

        if user.is_staff or user.is_admin or user.is_superuser:
            cortex_perm = 'EDITAR_TUDO'
        else:
            # Verifica se possui vínculo ativo de servidor
            tem_servidor_ativo = False
            try:
                tem_servidor_ativo = (
                    hasattr(user, 'servidor')
                    and user.servidor is not None
                    and getattr(user.servidor, 'ativo', False)
                )
            except Exception:
                pass

            # Verifica se possui vínculo ativo de terceirizado
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
                cortex_perm = 'LER_TUDO'
            else:
                cortex_perm = 'EDITAR_EU'

        return {
            'cortex': cortex_perm,
        }
