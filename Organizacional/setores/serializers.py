from rest_framework import serializers

from .models import Setor


class SetorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setor
        fields = ['id', 'nome', 'sigla', 'ativo', 'created_at']


class CriarSetorSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255)
    sigla = serializers.CharField(max_length=20)


class AtualizarSetorSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255, required=False)
    sigla = serializers.CharField(max_length=20, required=False)


class SerializerVazio(serializers.Serializer):
    """Serializer sem campos — usado em endpoints de ação pura."""
    pass
