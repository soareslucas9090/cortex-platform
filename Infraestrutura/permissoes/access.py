from rest_framework.permissions import BasePermission


def usuario_pode_cadastrar_infraestrutura(user) -> bool:
    """Verifica se o usuário possui a capacidade cadastrar do módulo Infraestrutura."""
    if not user or not user.is_authenticated:
        return False
    infraestrutura = getattr(user, 'permissoes', {}).get('infraestrutura', {})
    return bool(infraestrutura.get('cadastrar'))


class PodeCadastrarInfraestruturaPermission(BasePermission):
    """Exige capacidade cadastrar compilada em permissoes_infraestrutura()."""

    message = 'Você não tem permissão para cadastrar em Infraestrutura.'

    def has_permission(self, request, view):
        return usuario_pode_cadastrar_infraestrutura(request.user)

    def has_object_permission(self, request, view, obj):
        return usuario_pode_cadastrar_infraestrutura(request.user)


class PodeCadastrarInfraestruturaMixin:
    permission_classes = [PodeCadastrarInfraestruturaPermission]
