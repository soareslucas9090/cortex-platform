from rest_framework import serializers

from .models import Bloco


class BlocoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bloco
        fields = ['id', 'nome', 'ativo', 'created_at']


class CriarBlocoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255)


class AtualizarBlocoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255, required=False)


class SerializerVazio(serializers.Serializer):
    """Serializer sem campos — usado em endpoints de ação pura."""
    pass
