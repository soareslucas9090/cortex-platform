import re

from rest_framework import serializers

from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    tem_perfil_aluno = serializers.SerializerMethodField()

    def get_tem_perfil_aluno(self, obj):
        """
        Indica se o usuário possui um perfil acadêmico associado.
        Detectado via reverse relation nativa do Django, sem importar
        models do domínio Acadêmico dentro do domínio Identidade.
        """
        return hasattr(obj, 'aluno') and obj.aluno is not None

    class Meta:
        model = Usuario
        fields = [
            'id', 'cpf', 'nome', 'email', 'ativo', 'is_admin',
            'foto', 'deficiencia', 'tem_perfil_aluno', 'created_at',
        ]


class CriarUsuarioSerializer(serializers.Serializer):
    cpf = serializers.CharField(
        max_length=14,
        help_text='CPF do usuário. Aceita com ou sem máscara (ex: 12345678901 ou 123.456.789-01).',
    )
    nome = serializers.CharField(max_length=255)
    password = serializers.CharField(
        write_only=True,
        help_text='Senha (mín. 8 caracteres, com maiúscula, minúscula, número e caractere especial).',
    )
    email = serializers.EmailField(
        required=False,
        allow_null=True,
        default=None,
        help_text='E-mail do usuário (opcional).',
    )
    deficiencia = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        help_text='Descrição de deficiência ou necessidade especial (opcional).',
    )

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('A senha deve ter pelo menos 8 caracteres.')
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError('A senha deve conter pelo menos uma letra maiúscula.')
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError('A senha deve conter pelo menos uma letra minúscula.')
        if not re.search(r'\d', value):
            raise serializers.ValidationError('A senha deve conter pelo menos um número.')
        if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>?/\\|`~]', value):
            raise serializers.ValidationError('A senha deve conter pelo menos um caractere especial.')
        return value


class AtualizarUsuarioSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255, required=False)
    email = serializers.EmailField(required=False, allow_null=True)
    foto = serializers.ImageField(required=False, allow_null=True)
    deficiencia = serializers.CharField(required=False, allow_blank=True)


class SerializerVazio(serializers.Serializer):
    """Serializer sem campos — usado em endpoints de ação pura (desativar, reativar)."""
    pass
