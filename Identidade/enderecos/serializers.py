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

    _SIGLAS_VALIDAS = {
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
        'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
        'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
    }

    def validate_estado(self, value):
        sigla = value.strip().upper()
        if sigla not in self._SIGLAS_VALIDAS:
            raise serializers.ValidationError('Estado deve ser uma sigla de estado brasileiro válida (ex: CE, SP).')
        return sigla
