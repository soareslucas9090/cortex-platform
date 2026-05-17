from django.db import transaction
from django.http import Http404

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from AppCore.core.exceptions.exceptions import SystemErrorException, NotFoundException
from AppCore.basics.decorators.decorators import handle_exceptions

from AppCore.common.textos.mensagens import RESPONSE_ALGUM_DADO_NAO_FOI_ENCONTRADO


def _build_success_response(resultado, mensagem_sucesso):
    """Monta o dict de resposta de sucesso com base no retorno do hook da view."""
    if not resultado:
        resultado = {}
    mensagem = resultado.get('mensagem') or mensagem_sucesso or 'Sucesso'
    return {'status': 'success', 'mensagem': mensagem}, resultado.get('status_code', status.HTTP_200_OK)


class BasicPostAPIView(GenericAPIView):
    """
    View base para operações POST.

    Sobrescreva ``do_action_post(serializer_data, request)`` para implementar a lógica.
    O retorno opcional é um dict com ``mensagem`` e/ou ``status_code`` para customizar a resposta.
    A operação inteira roda dentro de ``transaction.atomic()`` com savepoint automático.
    """

    http_method_names = ['post']
    mensagem_sucesso = ''

    def do_action_post(self, serializer_data, request):
        raise SystemErrorException('Este método não foi implementado.')

    @handle_exceptions
    def post(self, request, *args, **kwargs):
        serializer_object = self.get_serializer(data=request.data)
        serializer_object.is_valid(raise_exception=True)
        serializer_data = serializer_object.validated_data

        resultado = {}

        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                resultado = self.do_action_post(serializer_data, request) or {}
            except Exception as e:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)

        data, status_code = _build_success_response(resultado, self.mensagem_sucesso)
        return Response(data, status=status_code)


class BasicGetAPIView(GenericAPIView):
    """
    View base para operações GET com lista paginada.

    Sobrescreva ``validate_get(request, *args, **kwargs)`` para validações/permissões
    extras antes de executar a query (ex: verificar parâmetros obrigatórios).
    """

    http_method_names = ['get']
    mensagem_sucesso = ''

    def validate_get(self, request, *args, **kwargs):
        """Hook opcional: levante exceções aqui para bloquear a requisição."""
        pass

    @handle_exceptions
    def get(self, request, *args, **kwargs):
        self.validate_get(request, *args, **kwargs)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            data = {
                'status': 'success',
                'mensagem': self.mensagem_sucesso or 'Sucesso',
                'count': paginated_response.data.get('count'),
                'next': paginated_response.data.get('next'),
                'previous': paginated_response.data.get('previous'),
                'dados': paginated_response.data.get('results'),
            }
            return Response(data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(queryset, many=True)
        data = {
            'status': 'success',
            'mensagem': self.mensagem_sucesso or 'Sucesso',
            'dados': serializer.data,
        }
        return Response(data, status=status.HTTP_200_OK)


class BasicDeleteAPIView(GenericAPIView):
    """
    View base para operações DELETE.

    Sobrescreva ``do_action_delete(request)`` para implementar a lógica de deleção.
    O objeto recuperado fica disponível em ``self.object``.
    """

    http_method_names = ['delete']
    mensagem_sucesso = ''

    def do_action_delete(self, request):
        raise SystemErrorException('Este método não foi implementado.')

    @handle_exceptions
    def delete(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            raise NotFoundException(RESPONSE_ALGUM_DADO_NAO_FOI_ENCONTRADO)

        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                self.do_action_delete(request)
            except Exception as e:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)

        return Response(status=status.HTTP_204_NO_CONTENT)


class BasicPutAPIView(GenericAPIView):
    """
    View base para operações PUT (atualização completa).

    Sobrescreva ``do_action_put(serializer_data, request)`` para implementar a lógica.
    O objeto recuperado fica disponível em ``self.object``.
    O retorno opcional é um dict com ``mensagem`` e/ou ``status_code``.
    """

    http_method_names = ['put']
    mensagem_sucesso = ''

    def do_action_put(self, serializer_data, request):
        raise SystemErrorException('Este método não foi implementado.')

    @handle_exceptions
    def put(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            raise NotFoundException(RESPONSE_ALGUM_DADO_NAO_FOI_ENCONTRADO)

        serializer_object = self.get_serializer(data=request.data)
        serializer_object.is_valid(raise_exception=True)
        serializer_data = serializer_object.validated_data

        resultado = {}

        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                resultado = self.do_action_put(serializer_data, request) or {}
            except Exception as e:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)

        data, status_code = _build_success_response(resultado, self.mensagem_sucesso)
        return Response(data, status=status_code)


class BasicPatchAPIView(GenericAPIView):
    """
    View base para operações PATCH (atualização parcial).

    Idêntica ao BasicPutAPIView, mas passa ``partial=True`` ao serializer,
    tornando todos os campos opcionais na validação.
    Sobrescreva ``do_action_patch(serializer_data, request)`` para implementar a lógica.
    """

    http_method_names = ['patch']
    mensagem_sucesso = ''

    def do_action_patch(self, serializer_data, request):
        raise SystemErrorException('Este método não foi implementado.')

    @handle_exceptions
    def patch(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            raise NotFoundException(RESPONSE_ALGUM_DADO_NAO_FOI_ENCONTRADO)

        serializer_object = self.get_serializer(data=request.data, partial=True)
        serializer_object.is_valid(raise_exception=True)
        serializer_data = serializer_object.validated_data

        resultado = {}

        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                resultado = self.do_action_patch(serializer_data, request) or {}
            except Exception as e:
                transaction.savepoint_rollback(sid)
                raise
            transaction.savepoint_commit(sid)

        data, status_code = _build_success_response(resultado, self.mensagem_sucesso)
        return Response(data, status=status_code)


class BasicRetrieveAPIView(GenericAPIView):
    """
    View base para operações GET de detalhe (objeto único).

    Sobrescreva ``validate_retrieve(request, *args, **kwargs)`` para validações extras.
    O objeto recuperado fica disponível em ``self.object``.
    """

    http_method_names = ['get']
    mensagem_sucesso = ''

    def validate_retrieve(self, request, *args, **kwargs):
        """Hook opcional: levante exceções aqui para bloquear a requisição."""
        pass

    @handle_exceptions
    def get(self, request, *args, **kwargs):
        self.validate_retrieve(request, *args, **kwargs)

        try:
            self.object = self.get_object()
        except Http404:
            raise NotFoundException(RESPONSE_ALGUM_DADO_NAO_FOI_ENCONTRADO)

        serializer = self.get_serializer(self.object)

        data = {
            'status': 'success',
            'mensagem': self.mensagem_sucesso or 'Sucesso',
            'dados': serializer.data,
        }
        return Response(data, status=status.HTTP_200_OK)

