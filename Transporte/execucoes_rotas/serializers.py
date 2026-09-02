from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from Transporte.rotas.serializers import RotaSerializer

from .models import ExecucaoRota


class ExecucaoRotaSerializer(serializers.ModelSerializer):
    rota = RotaSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    vagas_ocupadas = serializers.SerializerMethodField()
    vagas_disponiveis = serializers.SerializerMethodField()
    pode_monitorar = serializers.SerializerMethodField()

    class Meta:
        model = ExecucaoRota
        fields = [
            'id',
            'rota',
            'data_execucao',
            'data_hora_saida',
            'quantidade_vagas',
            'vagas_ocupadas',
            'vagas_disponiveis',
            'pode_monitorar',
            'chamada_tickets_concluida',
            'status',
            'status_display',
            'created_at',
        ]

    @extend_schema_field(OpenApiTypes.INT)
    def get_vagas_ocupadas(self, obj):
        return self._obter_resumo_vagas(obj)['vagas_ocupadas']

    @extend_schema_field(OpenApiTypes.INT)
    def get_vagas_disponiveis(self, obj):
        return self._obter_resumo_vagas(obj)['vagas_disponiveis']

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_pode_monitorar(self, obj):
        return obj.helper.pode_monitorar()

    def _obter_resumo_vagas(self, obj):
        if not hasattr(self, '_resumo_vagas_por_execucao'):
            self._resumo_vagas_por_execucao = {}
        if obj.pk not in self._resumo_vagas_por_execucao:
            self._resumo_vagas_por_execucao[obj.pk] = obj.business.obter_resumo_vagas()
        return self._resumo_vagas_por_execucao[obj.pk]


class CriarExecucaoRotaSerializer(serializers.Serializer):
    rota_id = serializers.IntegerField()
    data_execucao = serializers.DateField()


class FinalizarChamadaSerializer(serializers.Serializer):
    ausentes = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
    )


class SerializerVazio(serializers.Serializer):
    pass
