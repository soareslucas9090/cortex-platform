import re

from rest_framework import serializers

from .models import Usuario, Contato, Endereco, Matricula


# =============================================================================
# Serializers de saída (leitura e documentação de resposta)
# =============================================================================

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'id', 'cpf', 'nome', 'email', 'ativo', 'is_admin',
            'foto', 'deficiencia', 'created_at',
        ]


class ContatoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contato
        fields = ['id', 'email_academico', 'email_pessoal', 'telefone']


class EnderecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endereco
        fields = [
            'id', 'logradouro', 'numero', 'complemento',
            'bairro', 'cep', 'cidade', 'estado',
        ]


class MatriculaSerializer(serializers.ModelSerializer):
    situacao_display = serializers.CharField(source='get_situacao_display', read_only=True)

    class Meta:
        model = Matricula
        fields = ['id', 'matricula', 'situacao', 'situacao_display']


# =============================================================================
# Serializers de entrada (escrita)
# =============================================================================

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


class ContatoInputSerializer(serializers.Serializer):
    email_academico = serializers.EmailField(required=False, allow_blank=True, default='')
    email_pessoal = serializers.EmailField(required=False, allow_blank=True, default='')
    telefone = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')

    def validate(self, data):
        if not any([data.get('email_academico'), data.get('email_pessoal'), data.get('telefone')]):
            raise serializers.ValidationError('Informe ao menos um dado de contato.')
        return data


class EnderecoInputSerializer(serializers.Serializer):
    logradouro = serializers.CharField(max_length=255)
    numero = serializers.CharField(max_length=20)
    complemento = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    bairro = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    cep = serializers.CharField(max_length=8)
    cidade = serializers.CharField(max_length=100)
    estado = serializers.CharField(max_length=2)

    def validate_cep(self, value):
        if not re.fullmatch(r'\d{8}', value):
            raise serializers.ValidationError('CEP deve conter exatamente 8 dígitos numéricos (sem hífen).')
        return value

    def validate_estado(self, value):
        if len(value.strip()) != 2:
            raise serializers.ValidationError('Estado deve ser a sigla com 2 letras (ex: CE, SP).')
        return value.strip().upper()


class AdicionarMatriculaSerializer(serializers.Serializer):
    matricula = serializers.CharField(max_length=50, help_text='Número da matrícula.')


class SerializerVazio(serializers.Serializer):
    """Serializer sem campos — usado em endpoints de ação pura (desativar, reativar)."""
    pass
