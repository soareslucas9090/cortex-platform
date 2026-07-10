from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated


class AllowAnyPermission(AllowAny):
    """
    Permissão que permite acesso a qualquer usuário, independentemente de autenticação.
    """
    pass


class IsAuthenticatedPermission(IsAuthenticated):
    """
    Permissão que exige apenas autenticação.
    """
    pass


def _tem_acesso_elevado(user) -> bool:
    return getattr(user, 'tem_acesso_elevado', lambda: False)()


def _tem_leitura_ampla(user) -> bool:
    return getattr(user, 'tem_leitura_ampla', lambda: False)()


class IsOwnerOrAdminPermission(BasePermission):
    """
    Esta view permite que apenas o dono de um objeto ou um administrador acesse o recurso.
    Ela também permite acesso a qualquer usuário autenticado, mas restringe a ações que não interajam com nenhum objeto específico.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser or getattr(request.user, 'is_admin', False):
            return True

        if _tem_acesso_elevado(request.user):
            return True

        if request.method in ('GET', 'HEAD', 'OPTIONS') and _tem_leitura_ampla(request.user):
            return True

        usuario_proprietario = view.obter_usuario_dono(obj)

        return usuario_proprietario == request.user


class IsAdminPermission(BasePermission):
    """
    Permite acesso apenas a superusuários, usuários com is_admin=True ou nível EDITAR_TUDO.
    O campo is_admin é opcional no modelo — usa getattr com fallback False.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser or getattr(request.user, 'is_admin', False):
            return True

        return _tem_acesso_elevado(request.user)

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser or getattr(request.user, 'is_admin', False):
            return True

        return _tem_acesso_elevado(request.user)
