"""
Serializers de Autenticação do Projeto

Este é o ponto de customização do login para cada projeto.
Sobrescreva LoginSerializer aqui para adicionar dados específicos do domínio
sem modificar o AppCore.

==============================================================================
EXEMPLOS DE CUSTOMIZAÇÃO
==============================================================================

Login simples com dados do usuário:

    from AppCore.basics.auth.serializers import BaseLoginSerializer

    class LoginSerializer(BaseLoginSerializer):
        def get_extra_payload(self, user):
            return {
                'nome': user.nome,
                'is_admin': user.is_admin,
            }

Login com tipo de usuário (ex: motorista vs empresa):

    from AppCore.basics.auth.serializers import BaseTypedLoginSerializer
    from rest_framework_simplejwt.exceptions import AuthenticationFailed

    class LoginSerializer(BaseTypedLoginSerializer):
        tipo_choices = ['motorista', 'empresa']

        def _validate_user_tipo(self, user, tipo):
            if tipo == 'motorista' and not hasattr(user, 'motorista'):
                raise AuthenticationFailed('Usuário não é motorista.')
            if tipo == 'empresa' and not hasattr(user, 'empresa'):
                raise AuthenticationFailed('Usuário não é empresa.')

        def get_extra_payload(self, user):
            return {'nome': user.nome}

Login com CPF em vez de email (altere também USERNAME_FIELD no model):

    class LoginSerializer(BaseLoginSerializer):
        username_field = 'cpf'

        def get_extra_payload(self, user):
            return {'nome': user.nome, 'cpf': user.cpf}
"""

from AppCore.basics.auth.serializers import BaseLoginSerializer


# Serializer padrão — sobrescreva conforme o domínio do projeto.
class LoginSerializer(BaseLoginSerializer):
    """
    Serializer de login do projeto. Herda de BaseLoginSerializer.

    Sobrescreva get_extra_payload(user) para adicionar dados ao retorno do login.
    """

    def get_extra_payload(self, user) -> dict:
        return {}


# Serializers para documentação Swagger (opcionais — personalize conforme necessário)
from rest_framework import serializers


class LoginInputSerializer(serializers.Serializer):
    """Documenta o input do login no Swagger. Ajuste os campos conforme o USERNAME_FIELD."""

    email = serializers.EmailField(help_text='E-mail do usuário (padrão). Troque por cpf se usar CPF.')
    password = serializers.CharField(write_only=True)


class LoginResponseSerializer(serializers.Serializer):
    """Documenta a resposta do login no Swagger."""

    access = serializers.CharField(help_text='Token JWT de acesso (30 min).')
    refresh = serializers.CharField(help_text='Token JWT de renovação (7 dias).')
