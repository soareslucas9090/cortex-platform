from rest_framework import serializers

from .models import EmpresaInstituicao


class EmpresaInstituicaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaInstituicao
        fields = [
            'id', 'nome', 'cnpj', 'ativo',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CriarEmpresaInstituicaoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255)
    cnpj = serializers.CharField(max_length=14, required=False, allow_blank=True)
    ativo = serializers.BooleanField(default=True, required=False)


class AtualizarEmpresaInstituicaoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255, required=False)
    cnpj = serializers.CharField(max_length=14, required=False, allow_blank=True)
    ativo = serializers.BooleanField(required=False)
