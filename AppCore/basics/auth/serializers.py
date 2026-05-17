"""
Serializers de Autenticação Base

Este módulo fornece serializers reutilizáveis para diferentes estratégias de login:

1. BaseLoginSerializer — Login simples com hook para payload extra
2. BaseTypedLoginSerializer — Login com campo "tipo" para diferenciar perfis de usuário

==============================================================================
COMO USAR: LOGIN SIMPLES
==============================================================================

    # Auth/auth/serializers.py
    from AppCore.basics.auth.serializers import BaseLoginSerializer

    class LoginSerializer(BaseLoginSerializer):
        def get_extra_payload(self, user):
            return {
                'nome': user.nome,
                'is_admin': user.is_admin,
            }

==============================================================================
COMO USAR: LOGIN COM TIPO (ex: motorista vs empresa)
==============================================================================

    # Auth/auth/serializers.py
    from AppCore.basics.auth.serializers import BaseTypedLoginSerializer
    from rest_framework_simplejwt.exceptions import AuthenticationFailed

    class LoginSerializer(BaseTypedLoginSerializer):
        tipo_choices = ['motorista', 'empresa']

        def _validate_user_tipo(self, user, tipo):
            '''
            Lança AuthenticationFailed se o usuário não pertence ao tipo informado.
            Implemente a lógica de verificação conforme o seu domínio.
            '''
            if tipo == 'motorista' and not hasattr(user, 'motorista'):
                raise AuthenticationFailed('Usuário não possui perfil de motorista.')
            if tipo == 'empresa' and not hasattr(user, 'empresa'):
                raise AuthenticationFailed('Usuário não possui perfil de empresa.')

        def get_extra_payload(self, user):
            return {'nome': user.nome}
"""

from django.contrib.auth import authenticate as django_authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings


class BaseLoginSerializer(TokenObtainPairSerializer):
    """
    Serializer de login base.

    Sobrescreva ``get_extra_payload(user)`` para adicionar dados customizados
    à resposta do login (ex: nome, perfis, campus, etc.).
    Os dados retornados são mesclados ao dict de resposta que já contém
    ``access`` e ``refresh``.
    """

    def get_extra_payload(self, user) -> dict:
        """
        Hook para adicionar dados extras à resposta do login.

        Args:
            user: Instância do usuário autenticado.

        Returns:
            dict com os dados extras a serem incluídos na resposta.
        """
        return {}

    def validate(self, attrs):
        data = super().validate(attrs)
        extra = self.get_extra_payload(self.user)
        if extra:
            data.update(extra)
        return data


class BaseTypedLoginSerializer(BaseLoginSerializer):
    """
    Serializer de login com suporte a tipo de usuário.

    Adiciona o campo ``tipo`` ao input do login, permitindo que sistemas com
    múltiplos perfis (ex: motorista/empresa, aluno/servidor) diferenciem o
    fluxo de autenticação sem precisar de endpoints separados.

    Configure ``tipo_choices`` com a lista de tipos válidos para o seu projeto.
    Sobrescreva ``_validate_user_tipo(user, tipo)`` para implementar a lógica
    de verificação do tipo de perfil.

    Exemplo:
        tipo_choices = ['motorista', 'empresa']
    """

    tipo_choices: list = []

    def get_fields(self):
        fields = super().get_fields()
        if self.tipo_choices:
            fields['tipo'] = serializers.ChoiceField(
                choices=self.tipo_choices,
                write_only=True,
            )
        else:
            fields['tipo'] = serializers.CharField(write_only=True)
        return fields

    def _validate_user_tipo(self, user, tipo: str) -> None:
        """
        Valida se o usuário autenticado possui o perfil correspondente ao tipo informado.

        Sobrescreva este método no seu serializer concreto.
        Deve lançar ``AuthenticationFailed`` se o tipo não for válido.

        Args:
            user: Instância do usuário autenticado.
            tipo: Valor do campo 'tipo' enviado na requisição.

        Raises:
            AuthenticationFailed: Se o usuário não possui o perfil do tipo informado.
        """
        raise NotImplementedError(
            f'{self.__class__.__name__} deve implementar _validate_user_tipo(user, tipo).'
        )

    def validate(self, attrs):
        tipo = attrs.pop('tipo', None)
        data = super().validate(attrs)
        if tipo is not None:
            self._validate_user_tipo(self.user, tipo)
            data['tipo'] = tipo
        return data


class BaseHybridLoginSerializer(TokenObtainPairSerializer):
    """
    Serializer de login com campo único ``login`` (aceita e-mail ou CPF).

    Substitui o campo padrão do USERNAME_FIELD por um campo único ``login``,
    e delega a detecção do tipo de identificador ao backend registrado em
    ``AUTHENTICATION_BACKENDS`` (ex: ``EmailOrCpfBackend``).

    Sobrescreva ``get_extra_payload(user)`` para adicionar dados extras à
    resposta do login. Os dados serão mesclados ao dict que já contém
    ``access`` e ``refresh``.

    Requer que ``AUTHENTICATION_BACKENDS`` inclua um backend que aceite
    o parâmetro ``login`` (ver ``AppCore.basics.auth.backends.EmailOrCpfBackend``).

    Exemplo::

        # Auth/auth/serializers.py
        from AppCore.basics.auth.serializers import BaseHybridLoginSerializer

        class LoginSerializer(BaseHybridLoginSerializer):
            def get_extra_payload(self, user):
                return {'nome': user.nome}
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove o campo padrão do USERNAME_FIELD (ex: email) e adiciona 'login'
        if self.username_field in self.fields:
            del self.fields[self.username_field]
        self.fields['login'] = serializers.CharField(write_only=True)

    def get_extra_payload(self, user) -> dict:
        """
        Hook para adicionar dados extras à resposta do login.

        Args:
            user: Instância do usuário autenticado.

        Returns:
            dict com os dados extras a serem incluídos na resposta.
        """
        return {}

    def validate(self, attrs):
        login_value = attrs.get('login')
        password = attrs.get('password')
        request = self.context.get('request')

        self.user = django_authenticate(
            request=request,
            login=login_value,
            password=password,
        )

        if not api_settings.USER_AUTHENTICATION_RULE(self.user):
            raise AuthenticationFailed(
                self.error_messages['no_active_account'],
                'no_active_account',
            )

        refresh = self.get_token(self.user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        extra = self.get_extra_payload(self.user)
        if extra:
            data.update(extra)

        return data

