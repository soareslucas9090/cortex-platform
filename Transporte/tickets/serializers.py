from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from Transporte.execucoes_rotas.serializers import ExecucaoRotaSerializer

from .choices import StatusTicket
from .models import Ticket


class AlunoTicketSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='usuario_id', read_only=True)
    nome = serializers.CharField(source='usuario.nome', read_only=True)
    foto = serializers.URLField(source='usuario.foto', read_only=True, allow_null=True)


class PosicaoTicketSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=['RESERVA', 'ESPERA'], read_only=True)
    atual = serializers.IntegerField(min_value=1, read_only=True)
    total = serializers.IntegerField(min_value=1, read_only=True)


class TicketSerializer(serializers.ModelSerializer):
    execucao_rota = ExecucaoRotaSerializer(read_only=True)
    aluno = AlunoTicketSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    posicao = serializers.SerializerMethodField()
    posicao_fila = serializers.SerializerMethodField()
    codigo_qr = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'codigo',
            'execucao_rota',
            'aluno',
            'status',
            'status_display',
            'posicao',
            'posicao_fila',
            'codigo_qr',
            'reservado_em',
            'entrou_em_espera_em',
            'cancelado_em',
            'embarcado_em',
            'ausente_em',
            'created_at',
        ]

    @extend_schema_field(PosicaoTicketSerializer)
    def get_posicao(self, obj):
        return self._obter_posicao(obj)

    @extend_schema_field(OpenApiTypes.INT)
    def get_posicao_fila(self, obj):
        posicao = self._obter_posicao(obj)
        return posicao['atual'] if posicao and posicao['tipo'] == 'ESPERA' else None

    def _obter_posicao(self, obj):
        if not hasattr(self, '_posicoes_por_execucao'):
            self._posicoes_por_execucao = {}
        if obj.execucao_rota_id not in self._posicoes_por_execucao:
            self._posicoes_por_execucao[obj.execucao_rota_id] = (
                obj.business.obter_posicoes_da_execucao(obj.execucao_rota)
            )
        return self._posicoes_por_execucao[obj.execucao_rota_id].get(obj.pk)

    @extend_schema_field(OpenApiTypes.STR)
    def get_codigo_qr(self, obj):
        if obj.status not in (StatusTicket.RESERVADO, StatusTicket.EMBARCADO):
            return None
        return obj.business.gerar_codigo_qr()


class SerializerVazio(serializers.Serializer):
    pass


class ValidarQrSerializer(serializers.Serializer):
    codigo_qr = serializers.CharField(trim_whitespace=True)


class ResultadoValidacaoQrSerializer(serializers.Serializer):
    ticket = TicketSerializer()
    ja_validado = serializers.BooleanField()


class ResultadoCancelamentoTicketSerializer(serializers.Serializer):
    ticket = TicketSerializer()
    ticket_promovido = TicketSerializer(allow_null=True)


class ResultadoAusenciaTicketSerializer(serializers.Serializer):
    ticket = TicketSerializer()
    strike_id = serializers.IntegerField()
