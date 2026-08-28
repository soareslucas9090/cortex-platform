from rest_framework import serializers

from Transporte.percursos.models import Percurso

from .choices import DiaSemana
from .models import Rota


class PercursoResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Percurso
        fields = ['id', 'apelido', 'ativo']


class RotaSerializer(serializers.ModelSerializer):
    percurso = PercursoResumoSerializer(read_only=True)
    dia_semana_display = serializers.CharField(source='get_dia_semana_display', read_only=True)

    class Meta:
        model = Rota
        fields = [
            'id',
            'percurso',
            'horario_saida',
            'dia_semana',
            'dia_semana_display',
            'quantidade_vagas',
            'ativo',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CriarRotaSerializer(serializers.Serializer):
    percurso_id = serializers.IntegerField()
    horario_saida = serializers.TimeField()
    dia_semana = serializers.ChoiceField(choices=DiaSemana.choices)
    quantidade_vagas = serializers.IntegerField(min_value=1)


class AtualizarRotaSerializer(serializers.Serializer):
    percurso_id = serializers.IntegerField(required=False)
    horario_saida = serializers.TimeField(required=False)
    dia_semana = serializers.ChoiceField(choices=DiaSemana.choices, required=False)
    quantidade_vagas = serializers.IntegerField(min_value=1, required=False)


class SerializerVazio(serializers.Serializer):
    """Serializer sem campos — usado em endpoints de ação pura."""
    pass
