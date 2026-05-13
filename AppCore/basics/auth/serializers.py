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

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed


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
