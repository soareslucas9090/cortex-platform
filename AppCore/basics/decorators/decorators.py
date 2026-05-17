import logging

from functools import wraps

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

logger = logging.getLogger(__name__)

from AppCore.core.exceptions.exceptions import (
    BusinessRuleException, SystemErrorException, ValidationException, AuthorizationException, NotFoundException
)

from AppCore.common.textos.mensagens import (
    RESPONSE_TENTE_NOVAMENTE, RESPONSE_ALGO_QUE_MANDOU_ESTA_ERRADO, RESPONSE_VOCE_NAO_PODE_FAZER_ISSO,
    RESPONSE_ALGUM_DADO_NAO_FOI_ENCONTRADO, RESPONSE_ERRO_INTERNO_SERVIDOR
)


def handle_exceptions(func):
    """Decorator que adiciona tratamento de exceções padronizado"""
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        try:
            return func(self, request, *args, **kwargs)
        except BusinessRuleException as err:
            return Response(
                {'status': 'error', 'detail': str(err) or RESPONSE_TENTE_NOVAMENTE}, status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationException as err:
            return Response(
                {'status': 'error', 'detail': str(err) or RESPONSE_ALGO_QUE_MANDOU_ESTA_ERRADO}, status=status.HTTP_400_BAD_REQUEST
            )
        except (AuthorizationException, PermissionDenied) as err:
            return Response(
                {'status': 'error', 'detail': str(err) or RESPONSE_VOCE_NAO_PODE_FAZER_ISSO}, status=status.HTTP_403_FORBIDDEN
            )
        except NotFoundException as err:
            return Response(
                {'status': 'error', 'detail': str(err) or RESPONSE_ALGUM_DADO_NAO_FOI_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND
            )
        except SystemErrorException as err:
            # SystemErrorException é erro interno — nunca expor a mensagem ao cliente (OWASP A03)
            logger.exception('Erro interno do sistema na view: %s', err)
            return Response(
                {'status': 'error', 'detail': RESPONSE_ERRO_INTERNO_SERVIDOR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as err:
            # Nunca expor detalhes de exceções inesperadas ao cliente (OWASP A03)
            logger.exception('Erro inesperado na view: %s', err)
            return Response(
                {'status': 'error', 'detail': RESPONSE_ERRO_INTERNO_SERVIDOR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return wrapper