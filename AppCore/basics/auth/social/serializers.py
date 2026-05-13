"""
Serializer para autenticação social com retorno de JWT

Recebe o token/código OAuth do provider social e retorna access + refresh JWT.
"""

from rest_framework import serializers


class SocialTokenInputSerializer(serializers.Serializer):
    """
    Input para autenticação social.

    Envie o ``access_token`` obtido do provider (ex: Google) após o fluxo OAuth
    no lado do cliente. O backend valida o token com o provider e emite JWT.

    Alternativamente, use ``code`` se estiver usando o fluxo Authorization Code
    (menos comum em SPAs/mobile).
    """

    access_token = serializers.CharField(
        required=False,
        write_only=True,
        help_text='Token de acesso OAuth obtido do provider (Google, etc.).',
    )
    code = serializers.CharField(
        required=False,
        write_only=True,
        help_text='Código de autorização OAuth (fluxo Authorization Code).',
    )

    def validate(self, attrs):
        if not attrs.get('access_token') and not attrs.get('code'):
            raise serializers.ValidationError(
                'Informe access_token ou code para autenticação social.'
            )
        return attrs


class SocialTokenResponseSerializer(serializers.Serializer):
    """Documenta o formato de resposta do login social (apenas para Swagger)."""

    access = serializers.CharField(help_text='Token JWT de acesso (30 min).')
    refresh = serializers.CharField(help_text='Token JWT de renovação (7 dias).')
