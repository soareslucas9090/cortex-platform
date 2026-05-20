import re

from rest_framework import serializers

from .models import Endereco


class EnderecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endereco
        fields = [
            'id', 'logradouro', 'numero', 'complemento',
            'bairro', 'cep', 'cidade', 'estado',
        ]


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
