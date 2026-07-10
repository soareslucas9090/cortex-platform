from rest_framework import status
from rest_framework.response import Response

from AppCore.core.exceptions.exceptions import AuthorizationException
from AppCore.core.permissions.permissions import (
    AllowAnyPermission,
    IsAuthenticatedPermission,
    IsOwnerOrAdminPermission,
    IsAdminPermission,
)


class RespostasMixin:
    """Mixin com métodos utilitários de montagem de respostas padronizadas."""

    def resposta_sucesso(self, mensagem, dados=None, status_code=status.HTTP_200_OK):
        data = {'status': 'success', 'mensagem': mensagem}
        if dados is not None:
            data['dados'] = dados
        return Response(data, status=status_code)

    def resposta_lista_paginada(self, queryset, mensagem):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginada = self.get_paginated_response(serializer.data)
            return Response({
                'status': 'success',
                'mensagem': mensagem,
                'count': paginada.data.get('count'),
                'next': paginada.data.get('next'),
                'previous': paginada.data.get('previous'),
                'dados': paginada.data.get('results'),
            }, status=status.HTTP_200_OK)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'status': 'success', 'mensagem': mensagem, 'dados': serializer.data})


class AllowAnyMixin:
    permission_classes = [AllowAnyPermission]


class IsAuthenticatedMixin:
    permission_classes = [IsAuthenticatedPermission]


class IsOwnerOrAdminMixin:
    permission_classes = [IsOwnerOrAdminPermission]

    def obter_usuario_dono(self, obj):
        raise NotImplementedError(
            f'{self.__class__.__name__} deve implementar o método obter_usuario_dono(obj)'
        )

    def verificar_acesso_usuario(self, request, usuario_pk):
        """
        Verifica manualmente se o usuário autenticado pode acessar sub-recursos de outro usuário.

        Utilizado em endpoints de sub-recursos onde has_object_permission não é acionado
        automaticamente pelo DRF.
        L2 (tem_leitura_ampla) só vale em métodos SAFE (GET/HEAD/OPTIONS).
        Escrita exige dono, is_admin, superuser ou L3 (tem_acesso_elevado).
        Os query params de filtragem são aplicados APÓS esta verificação —
        eles nunca expandem o acesso, apenas reduzem o conjunto de resultados.
        """
        if request.user.pk == int(usuario_pk):
            return

        if (
            getattr(request.user, 'is_admin', False)
            or request.user.is_superuser
            or getattr(request.user, 'tem_acesso_elevado', lambda: False)()
        ):
            return

        if request.method in ('GET', 'HEAD', 'OPTIONS') and getattr(
            request.user, 'tem_leitura_ampla', lambda: False
        )():
            return

        raise AuthorizationException('Você não tem permissão para acessar esses dados.')


class IsAdminMixin:
    permission_classes = [IsAdminPermission]
