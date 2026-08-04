"""
Business Layer - Camada de Negócios Práticos

Esta camada é responsável por:
- Orquestrar operações de negócio
- Tratar exceções lançadas pela camada Rules ou outras camadas
- Executar operações de CRUD com validações
- Coordenar interações entre diferentes componentes
- Processar lógica de negócio complexa

A camada Business:
- Pode chamar Rules para validações
- Pode chamar Helpers para operações auxiliares
- Pode chamar State para transições de estado
- Deve retornar resultados processados ou lançar exceções tratadas

Contrato obrigatório de try/except em TODOS os métodos de business:
- O corpo inteiro do método (após docstring) fica dentro de um único try.
- Não pode existir lógica (rules, queries, loops, persistência) fora do try.
- Use ``self.relancar_ou_erro_sistema(e, '...', logger)`` no catch-all
  ``except Exception as e``; o helper já faz os isinstance checks.
- Não duplique manualmente ``except self.exceptions_handled`` /
  ``except SystemErrorException`` / ``logger.exception`` + ``SystemErrorException``.
- Conversões especiais (ex.: ValueError → ValidationException) podem aparecer
  ANTES do catch-all.
- Subclasses podem ampliar ``exceptions_handled``; o padrão raramente precisa mudar.
"""
from AppCore.core.exceptions.exceptions import (
    AuthorizationException,
    BusinessRuleException,
    NotFoundException,
    SystemErrorException,
    ValidationException,
)


class ModelInstanceBusiness:
    """
    Base da camada Business.

    ``exceptions_handled``: exceções de domínio/aceitação que devem atravessar
    o business sem serem convertidas em SystemErrorException. Amplie a tupla
    na subclasse apenas para incluir novos tipos aceitos.
    """

    exceptions_handled = (
        AuthorizationException,
        BusinessRuleException,
        ValidationException,
        NotFoundException,
    )

    def __init__(self, object_instance=None):
        self.object_instance = object_instance

    def relancar_ou_erro_sistema(self, exc: Exception, mensagem: str, logger) -> None:
        """
        Relança exceções aceitas / SystemErrorException; caso contrário,
        registra e levanta SystemErrorException com mensagem genérica.

        Padrão canônico no catch-all do método de business::

            try:
                # corpo inteiro
                ...
            except ValueError as e:
                raise ValidationException('...')  # opcional: conversões antes
            except Exception as e:
                self.relancar_ou_erro_sistema(e, 'Não foi possível ...', logger)

        Não duplique manualmente ``except self.exceptions_handled`` /
        ``except SystemErrorException`` / ``logger.exception`` + ``SystemErrorException``.
        """
        if isinstance(exc, self.exceptions_handled):
            raise exc
        if isinstance(exc, SystemErrorException):
            raise exc
        logger.exception('%s: %s', mensagem, exc)
        raise SystemErrorException(mensagem)
