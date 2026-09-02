from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from Transporte.strikes.serializers import StrikeSerializer

from .models import Justificativa


class JustificativaSerializer(serializers.ModelSerializer):
    strike = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    analisada_por_nome = serializers.CharField(source='analisada_por.nome', read_only=True)

    class Meta:
        model = Justificativa
        fields = [
            'id',
            'strike',
            'texto',
            'status',
            'status_display',
            'observacao_analise',
            'analisada_por_nome',
            'analisada_em',
            'created_at',
        ]

    @extend_schema_field(StrikeSerializer)
    def get_strike(self, obj):
        strike = obj.strike
        if hasattr(obj, 'quantidade_strikes_ativos'):
            strike.quantidade_strikes_ativos = obj.quantidade_strikes_ativos
        return StrikeSerializer(strike, context=self.context).data


class CriarJustificativaSerializer(serializers.Serializer):
    texto = serializers.CharField(min_length=10, max_length=5000, trim_whitespace=True)


class AnalisarJustificativaSerializer(serializers.Serializer):
    observacao_analise = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=5000,
        trim_whitespace=True,
    )
