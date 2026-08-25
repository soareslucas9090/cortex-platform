from rest_framework import serializers

from .models import Curso


class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = ['id', 'nome', 'codigo_curso', 'ativo', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CriarCursoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255)
    codigo_curso = serializers.CharField(max_length=50)


class AtualizarCursoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255, required=False)
    codigo_curso = serializers.CharField(max_length=50, required=False)
