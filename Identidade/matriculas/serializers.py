from rest_framework import serializers

from .models import Matricula


class MatriculaSerializer(serializers.ModelSerializer):
    situacao_display = serializers.CharField(source='get_situacao_display', read_only=True)

    class Meta:
        model = Matricula
        fields = ['id', 'matricula', 'situacao', 'situacao_display']


class AdicionarMatriculaSerializer(serializers.Serializer):
    matricula = serializers.CharField(max_length=50, help_text='Número da matrícula.')


class SerializerVazio(serializers.Serializer):
    """Serializer sem campos — usado em endpoints de ação pura (desativar)."""
    pass
