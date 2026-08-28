from rest_framework import serializers

from .models import Percurso


class PercursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Percurso
        fields = ['id', 'apelido', 'descricao', 'ativo', 'created_at']
        read_only_fields = ['id', 'created_at']


class CriarPercursoSerializer(serializers.Serializer):
    apelido = serializers.CharField(max_length=255)
    descricao = serializers.CharField()


class AtualizarPercursoSerializer(serializers.Serializer):
    apelido = serializers.CharField(max_length=255, required=False)
    descricao = serializers.CharField(required=False)


class SerializerVazio(serializers.Serializer):
    """Serializer sem campos — usado em endpoints de ação pura."""
    pass
