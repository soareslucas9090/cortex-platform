from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

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
    capacidade = serializers.SerializerMethodField()
    percurso = serializers.CharField(source='percurso.descricao', read_only=True)
    percurso_apelido = serializers.CharField(source='percurso.apelido', read_only=True)
    dia_semana_display = serializers.CharField(
        source='get_dia_semana_display',
        read_only=True,
    )
    execucao_id = serializers.SerializerMethodField()
    status_execucao = serializers.SerializerMethodField()
    status_execucao_display = serializers.SerializerMethodField()
    tickets_solicitados = serializers.SerializerMethodField()
    vagas_ocupadas = serializers.SerializerMethodField()
    vagas_disponiveis = serializers.SerializerMethodField()

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
            'execucao_id',
            'status_execucao',
            'status_execucao_display',
            'tickets_solicitados',
            'vagas_ocupadas',
            'vagas_disponiveis',
        ]

    @extend_schema_field(OpenApiTypes.INT)
    def get_capacidade(self, obj):
        execucao = self._obter_execucao_do_dia(obj)
        return execucao.quantidade_vagas if execucao else obj.quantidade_vagas

    @extend_schema_field({'type': 'integer', 'nullable': True})
    def get_execucao_id(self, obj):
        execucao = self._obter_execucao_do_dia(obj)
        return execucao.pk if execucao else None

    @extend_schema_field({'type': 'integer', 'nullable': True})
    def get_status_execucao(self, obj):
        execucao = self._obter_execucao_do_dia(obj)
        return execucao.status if execucao else None

    @extend_schema_field({'type': 'string', 'nullable': True})
    def get_status_execucao_display(self, obj):
        execucao = self._obter_execucao_do_dia(obj)
        return execucao.get_status_display() if execucao else None

    @extend_schema_field(OpenApiTypes.INT)
    def get_tickets_solicitados(self, obj):
        execucao = self._obter_execucao_do_dia(obj)
        return getattr(execucao, 'tickets_solicitados', 0) if execucao else 0

    @extend_schema_field(OpenApiTypes.INT)
    def get_vagas_ocupadas(self, obj):
        execucao = self._obter_execucao_do_dia(obj)
        if not execucao:
            return 0
        return execucao.helper.ocupacao_da_listagem()

    @extend_schema_field(OpenApiTypes.INT)
    def get_vagas_disponiveis(self, obj):
        return max(self.get_capacidade(obj) - self.get_vagas_ocupadas(obj), 0)

    @staticmethod
    def _obter_execucao_do_dia(obj):
        execucoes = getattr(obj, 'execucoes_do_dia', ())
        return execucoes[0] if execucoes else None


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
