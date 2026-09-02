from rest_framework import serializers

from Transporte.percursos.models import Percurso

from .choices import DiaSemana
from .models import Rota


HORARIOS_ENTRADA = ['%H:%M', '%H:%M:%S']
HORARIO_SAIDA_HELP = 'Horário no formato hh:mm (ex.: 07:00). Também aceita hh:mm:ss.'


class PercursoResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Percurso
        fields = ['id', 'apelido', 'ativo']


class RotaSerializer(serializers.ModelSerializer):
    percurso = PercursoResumoSerializer(read_only=True)
    dia_semana_display = serializers.CharField(source='get_dia_semana_display', read_only=True)
    horario_saida = serializers.TimeField(format='%H:%M', read_only=True)

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


class RotaDoDiaSerializer(serializers.ModelSerializer):
    data = serializers.DateField(source='data_operacao', read_only=True)
    horario = serializers.TimeField(source='horario_saida', format='%H:%M', read_only=True)
    capacidade = serializers.IntegerField(source='quantidade_vagas', read_only=True)
    percurso = serializers.CharField(source='percurso.descricao', read_only=True)
    percurso_apelido = serializers.CharField(source='percurso.apelido', read_only=True)
    dia_semana_display = serializers.CharField(
        source='get_dia_semana_display',
        read_only=True,
    )

    class Meta:
        model = Rota
        fields = [
            'id',
            'data',
            'horario',
            'dia_semana',
            'dia_semana_display',
            'capacidade',
            'percurso',
            'percurso_apelido',
        ]


class CriarRotaSerializer(serializers.Serializer):
    percurso_id = serializers.IntegerField()
    horario_saida = serializers.TimeField(
        input_formats=HORARIOS_ENTRADA,
        format='%H:%M',
        help_text=HORARIO_SAIDA_HELP,
    )
    dia_semana = serializers.ChoiceField(choices=DiaSemana.choices)
    quantidade_vagas = serializers.IntegerField(min_value=1)


class AtualizarRotaSerializer(serializers.Serializer):
    percurso_id = serializers.IntegerField(required=False)
    horario_saida = serializers.TimeField(
        input_formats=HORARIOS_ENTRADA,
        format='%H:%M',
        required=False,
        help_text=HORARIO_SAIDA_HELP,
    )
    dia_semana = serializers.ChoiceField(choices=DiaSemana.choices, required=False)
    quantidade_vagas = serializers.IntegerField(min_value=1, required=False)


class SerializerVazio(serializers.Serializer):
    """Serializer sem campos — usado em endpoints de ação pura."""
    pass
