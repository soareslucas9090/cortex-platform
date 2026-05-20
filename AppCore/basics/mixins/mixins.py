from rest_framework import status
from rest_framework.response import Response

from AppCore.core.exceptions.exceptions import AuthorizationException
from AppCore.core.permissions.permissions import AllowAnyPermission, IsOwnerOrAdminPermission, IsAdminPermission


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


class IsOwnerOrAdminMixin:
    permission_classes = [IsOwnerOrAdminPermission]

    def obter_usuario_dono(self, obj):
        raise NotImplementedError(
            f'{self.__class__.__name__} deve implementar o método obter_usuario_dono(obj)'
        )

    def verificar_acesso_usuario(self, request, usuario_pk):
        """
        Verifica manualmente se o usuário autenticado é dono do recurso ou administrador.

        Utilizado em endpoints de listagem de sub-recursos onde has_object_permission
        não é acionado automaticamente pelo DRF.
        Os query params de filtragem são aplicados APÓS esta verificação —
        eles nunca expandem o acesso, apenas reduzem o conjunto de resultados.
        """
        if not (
            request.user.pk == int(usuario_pk)
            or getattr(request.user, 'is_admin', False)
            or request.user.is_superuser
        ):
            raise AuthorizationException('Você não tem permissão para acessar esses dados.')


class IsAdminMixin:
    permission_classes = [IsAdminPermission]
