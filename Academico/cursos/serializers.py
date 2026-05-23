from rest_framework import serializers

from .choices import TurnoCurso
from .models import Curso


class CursoSerializer(serializers.ModelSerializer):
    turno_display = serializers.CharField(source='get_turno_display', read_only=True)

    class Meta:
        model = Curso
        fields = ['id', 'nome', 'codigo_curso', 'turno', 'turno_display', 'ativo', 'created_at', 'updated_at']
        read_only_fields = ['id', 'turno_display', 'created_at', 'updated_at']


class CriarCursoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255)
    codigo_curso = serializers.CharField(max_length=50)
    turno = serializers.ChoiceField(choices=TurnoCurso.choices, required=False, allow_null=True)


class AtualizarCursoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255, required=False)
    codigo_curso = serializers.CharField(max_length=50, required=False)
    turno = serializers.ChoiceField(choices=TurnoCurso.choices, required=False, allow_null=True)
