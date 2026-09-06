from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import BasePermission, IsAuthenticated


def usuario_e_administrador_transporte(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    return bool(
        getattr(user, 'is_superuser', False)
        or getattr(user, 'is_staff', False)
        or getattr(user, 'is_admin', False)
    )


def usuario_tem_perfil_colaborador_ativo(user) -> bool:
    if not user:
        return False
    for atributo in ('servidor', 'terceirizado'):
        try:
            perfil = getattr(user, atributo)
        except ObjectDoesNotExist:
            continue
        if perfil is not None and getattr(perfil, 'ativo', False):
            return True
    return False


def usuario_pode_conferir_transporte(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if usuario_e_administrador_transporte(user):
        return True
    transporte = getattr(user, 'permissoes', {}).get('transporte', {})
    return bool(transporte.get('conferir'))


class PodeConferirTransportePermission(BasePermission):
    message = 'Você não tem permissão para conferir o transporte.'

    def has_permission(self, request, view):
        return usuario_pode_conferir_transporte(request.user)

    def has_object_permission(self, request, view, obj):
        return usuario_pode_conferir_transporte(request.user)


class PodeConferirTransporteMixin:
    permission_classes = [IsAuthenticated, PodeConferirTransportePermission]
