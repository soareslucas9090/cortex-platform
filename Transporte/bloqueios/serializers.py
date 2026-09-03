from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from Transporte.justificativas.serializers import JustificativaSerializer
from Transporte.strikes.serializers import StrikeSerializer


class BloqueioSerializer(serializers.Serializer):
    aluno_pk = serializers.IntegerField(source='pk')
    nome = serializers.CharField(source='usuario.nome')
    cpf = serializers.CharField(source='usuario.cpf')
    faltas = serializers.IntegerField()
    is_bloqueado = serializers.BooleanField()
    tem_justificativa_pendente = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_tem_justificativa_pendente(self, obj):
        return bool(getattr(obj, 'justificativas_pendentes', []))


class BloqueioDetalheSerializer(BloqueioSerializer):
    strikes = serializers.SerializerMethodField()
    justificativa_pendente = serializers.SerializerMethodField()

    @extend_schema_field(StrikeSerializer(many=True))
    def get_strikes(self, obj):
        strikes = []
        for ticket in obj.tickets_transporte.all():
            if hasattr(ticket, 'strike'):
                strikes.append(ticket.strike)
        return StrikeSerializer(strikes, many=True, context=self.context).data

    @extend_schema_field(JustificativaSerializer(allow_null=True))
    def get_justificativa_pendente(self, obj):
        pendentes = getattr(obj, 'justificativas_pendentes', [])
        if not pendentes:
            return None
        return JustificativaSerializer(pendentes[0], context=self.context).data
