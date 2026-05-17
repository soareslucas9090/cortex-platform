"""
Serializers de Autenticação do Projeto

Este é o ponto de customização do login para cada projeto.
Sobrescreva LoginSerializer aqui para adicionar dados específicos do domínio
sem modificar o AppCore.

==============================================================================
EXEMPLOS DE CUSTOMIZAÇÃO
==============================================================================

Adicionar dados do usuário à resposta do login:

    class LoginSerializer(BaseHybridLoginSerializer):
        def get_extra_payload(self, user):
            return {
                'nome': user.nome,
                'is_admin': user.is_admin,
            }

Login com tipo de usuário (ex: motorista vs empresa):

    from AppCore.basics.auth.serializers import BaseTypedLoginSerializer

    class LoginSerializer(BaseTypedLoginSerializer):
        tipo_choices = ['motorista', 'empresa']

        def _validate_user_tipo(self, user, tipo):
            if tipo == 'motorista' and not hasattr(user, 'motorista'):
                raise AuthenticationFailed('Usuário não é motorista.')

        def get_extra_payload(self, user):
            return {'nome': user.nome}
"""

from rest_framework import serializers

from AppCore.basics.auth.serializers import BaseHybridLoginSerializer


# Serializer padrão — sobrescreva conforme o domínio do projeto.
class LoginSerializer(BaseHybridLoginSerializer):
    """
    Serializer de login do projeto. Herda de BaseHybridLoginSerializer.

    Aceita ``login`` (e-mail ou CPF) e ``password``.
    Sobrescreva ``get_extra_payload(user)`` para enriquecer o retorno do login
    com dados do domínio (ex: nome, cargo, setores, lotação).
    """

    def get_extra_payload(self, user) -> dict:
        return {}


# Serializers para documentação Swagger
class LoginInputSerializer(serializers.Serializer):
    """Documenta o input do login no Swagger."""

    login = serializers.CharField(
        help_text=(
            'E-mail ou CPF do usuário. '
            'Exemplos: "usuario@email.com", "12345678901" ou "123.456.789-01".'
        )
    )
    password = serializers.CharField(
        write_only=True,
        help_text='Senha do usuário.',
    )


class LoginResponseSerializer(serializers.Serializer):
    """Documenta a resposta do login no Swagger."""

    access = serializers.CharField(help_text='Token JWT de acesso (30 min).')
    refresh = serializers.CharField(help_text='Token JWT de renovação (7 dias).')
