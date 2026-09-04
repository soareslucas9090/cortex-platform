from django.utils import timezone
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from Academico.alunos.serializers import AlunoSerializer
from Transporte.strikes.serializers import StrikeSerializer

from .models import Justificativa


def montar_itens_ausencia(justificativa):
    strikes = sorted(
        justificativa.strikes_cobertos.all(),
        key=lambda strike: strike.ticket.execucao_rota.data_hora_saida,
    )
    itens = []
    for strike in strikes:
        data_hora_saida = timezone.localtime(strike.ticket.execucao_rota.data_hora_saida)
        itens.append({
            'strike_id': strike.pk,
            'envio': justificativa.created_at,
            'data_ausencia': data_hora_saida.date(),
            'horario': data_hora_saida.strftime('%H:%M'),
            'justificativa': justificativa.texto,
        })
    return itens


class ItemAusenciaJustificativaSerializer(serializers.Serializer):
    strike_id = serializers.IntegerField()
    envio = serializers.DateTimeField()
    data_ausencia = serializers.DateField()
    horario = serializers.CharField()
    justificativa = serializers.CharField()


class JustificativaPendenteDetalheSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    strikes_cobertos = StrikeSerializer(many=True, read_only=True)
    itens_ausencia = serializers.SerializerMethodField()

    class Meta:
        model = Justificativa
        fields = [
            'id',
            'status',
            'status_display',
            'texto',
            'strikes_cobertos',
            'itens_ausencia',
        ]

    @extend_schema_field(ItemAusenciaJustificativaSerializer(many=True))
    def get_itens_ausencia(self, obj):
        return ItemAusenciaJustificativaSerializer(
            montar_itens_ausencia(obj),
            many=True,
        ).data


class JustificativaSerializer(serializers.ModelSerializer):
    aluno = AlunoSerializer(read_only=True)
    strikes_cobertos = StrikeSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    analisada_por_nome = serializers.CharField(source='analisada_por.nome', read_only=True)

    class Meta:
        model = Justificativa
        fields = [
            'id',
            'aluno',
            'strikes_cobertos',
            'texto',
            'status',
            'status_display',
            'observacao_analise',
            'analisada_por_nome',
            'analisada_em',
            'created_at',
        ]


class JustificativaDetalheSerializer(JustificativaSerializer):
    itens_ausencia = serializers.SerializerMethodField()

    class Meta(JustificativaSerializer.Meta):
        fields = JustificativaSerializer.Meta.fields + ['itens_ausencia']

    @extend_schema_field(ItemAusenciaJustificativaSerializer(many=True))
    def get_itens_ausencia(self, obj):
        return ItemAusenciaJustificativaSerializer(
            montar_itens_ausencia(obj),
            many=True,
        ).data


class CriarJustificativaSerializer(serializers.Serializer):
    texto = serializers.CharField(min_length=10, max_length=5000, trim_whitespace=True)


class AnalisarJustificativaSerializer(serializers.Serializer):
    observacao_analise = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=5000,
        trim_whitespace=True,
    )
