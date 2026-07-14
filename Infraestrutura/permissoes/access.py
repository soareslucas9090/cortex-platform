from rest_framework.permissions import BasePermission


def _capacidade_infraestrutura(user, capacidade: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    infraestrutura = getattr(user, 'permissoes', {}).get('infraestrutura', {})
    return bool(infraestrutura.get(capacidade))


def usuario_pode_cadastrar_infraestrutura(user) -> bool:
    """Verifica se o usuário possui a capacidade cadastrar do módulo Infraestrutura."""
    return _capacidade_infraestrutura(user, 'cadastrar')


def usuario_pode_autorizar_infraestrutura(user) -> bool:
    """Verifica se o usuário possui a capacidade autorizar do módulo Infraestrutura."""
    return _capacidade_infraestrutura(user, 'autorizar')


def usuario_pode_operar_infraestrutura(user) -> bool:
    """Verifica se o usuário possui a capacidade operar do módulo Infraestrutura."""
    return _capacidade_infraestrutura(user, 'operar')


class PodeCadastrarInfraestruturaPermission(BasePermission):
    """Exige capacidade cadastrar compilada em permissoes_infraestrutura()."""

    message = 'Você não tem permissão para cadastrar em Infraestrutura.'

    def has_permission(self, request, view):
        return usuario_pode_cadastrar_infraestrutura(request.user)

    def has_object_permission(self, request, view, obj):
        return usuario_pode_cadastrar_infraestrutura(request.user)


class PodeCadastrarInfraestruturaMixin:
    permission_classes = [PodeCadastrarInfraestruturaPermission]


class PodeAutorizarInfraestruturaPermission(BasePermission):
    """Exige capacidade autorizar compilada em permissoes_infraestrutura()."""

    message = 'Você não tem permissão para autorizar em Infraestrutura.'

    def has_permission(self, request, view):
        return usuario_pode_autorizar_infraestrutura(request.user)

    def has_object_permission(self, request, view, obj):
        return usuario_pode_autorizar_infraestrutura(request.user)


class PodeAutorizarInfraestruturaMixin:
    permission_classes = [PodeAutorizarInfraestruturaPermission]


class PodeOperarInfraestruturaPermission(BasePermission):
    """Exige capacidade operar compilada em permissoes_infraestrutura()."""

    message = 'Você não tem permissão para operar empréstimos em Infraestrutura.'

    def has_permission(self, request, view):
        return usuario_pode_operar_infraestrutura(request.user)

    def has_object_permission(self, request, view, obj):
        return usuario_pode_operar_infraestrutura(request.user)


class PodeOperarInfraestruturaMixin:
    permission_classes = [PodeOperarInfraestruturaPermission]
