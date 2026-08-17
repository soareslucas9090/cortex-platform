"""
Rules Layer - Camada de Regras de Negócio Teóricas

Esta camada é responsável por:
- Validações de regras de negócio
- Retorno de booleanos ou exceções
- Não deve conter lógica de persistência
- Não deve conter lógica de orquestração (isso é do business)

Métodos padrões que toda classe de Rules deve ter:
- return_exception(msg, type_exception=BusinessRuleException): lança exceção de domínio
- return_not_allowed(msg): lança AuthorizationException (403)
- return_response(msg, execute_exception=False): retorna False ou lança exceção
"""
from AppCore.core.exceptions.exceptions import AuthorizationException, BusinessRuleException

class ModelInstanceRules:
    def __init__(self, object_instance=None):
        self.object_instance = object_instance

    def return_exception(self, message='', details=None, type_exception=BusinessRuleException):
        """
        Lança uma exceção com a mensagem para ser tratada no business.

        Args:
            message: Mensagem de erro
            details: Detalhes opcionais da exceção
            type_exception: Classe de exceção de domínio a levantar
        """
        raise type_exception(message, details)

    def return_not_allowed(self, message='', details=None):
        """
        Lança AuthorizationException quando a ação não é permitida (403).
        """
        self.return_exception(
            message or 'Você não tem permissão para realizar esta ação.',
            details,
            AuthorizationException,
        )

    def return_response(self, message='', details=None, execute_exception=False):
        """
        Retorna uma resposta negativa ou lança exceção.
        
        Args:
            msg: Mensagem de erro
            execute_exception: Se True, lança exceção
            
        Returns:
            bool: False se não lançar exceção
            
        Raises:
            BaseRuleException: Se execute_exception for True
        """
        if execute_exception:
            self.return_exception(message, details)
        
        return False
    

