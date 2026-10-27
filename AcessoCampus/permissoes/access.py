from rest_framework.permissions import BasePermission, IsAuthenticated

def usuario_tem_acesso_total_acesso_campus(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    return bool(user.is_staff or getattr(user, 'is_admin', False) or user.is_superuser)


def usuario_pode_analisar_acesso_campus(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if usuario_tem_acesso_total_acesso_campus(user):
        return True
    acesso = getattr(user, 'permissoes', {}).get('acesso_campus', {})
    return bool(acesso.get('analisar_solicitacoes'))


class PodeAnalisarAcessoCampusPermission(BasePermission):
    message = 'Você não tem permissão para analisar o acesso ao campus.'

    def has_permission(self, request, view):
        return usuario_pode_analisar_acesso_campus(request.user)

    def has_object_permission(self, request, view, obj):
        return usuario_pode_analisar_acesso_campus(request.user)


class PodeAnalisarAcessoCampusMixin:
    permission_classes = [IsAuthenticated, PodeAnalisarAcessoCampusPermission]
