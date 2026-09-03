from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from Academico.alunos.serializers import AlunoSerializer
from Transporte.strikes.serializers import StrikeSerializer

from .models import Justificativa


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


class CriarJustificativaSerializer(serializers.Serializer):
    texto = serializers.CharField(min_length=10, max_length=5000, trim_whitespace=True)


class AnalisarJustificativaSerializer(serializers.Serializer):
    observacao_analise = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=5000,
        trim_whitespace=True,
    )
