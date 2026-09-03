from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from Transporte.justificativas.serializers import JustificativaPendenteDetalheSerializer
from Transporte.strikes.choices import StatusStrike


def _strikes_ativos_de(aluno):
    strikes = []
    for ticket in aluno.tickets_transporte.all():
        strike = getattr(ticket, 'strike', None)
        if strike and strike.status == StatusStrike.ATIVO:
            strikes.append(strike)
    return strikes


class BloqueioSerializer(serializers.Serializer):
    aluno_pk = serializers.IntegerField(source='pk')
    nome = serializers.CharField(source='usuario.nome')
    cpf = serializers.CharField(source='usuario.cpf')
    faltas = serializers.IntegerField()
    ausencias = serializers.IntegerField(source='faltas')
    bloqueios = serializers.IntegerField(source='quantidade_bloqueios')
    is_bloqueado = serializers.BooleanField()
    tem_justificativa_pendente = serializers.SerializerMethodField()
    curso_nome = serializers.SerializerMethodField()
    data_bloqueio = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_tem_justificativa_pendente(self, obj):
        return bool(getattr(obj, 'justificativas_pendentes', []))

    @extend_schema_field(OpenApiTypes.STR)
    def get_curso_nome(self, obj):
        vinculos = getattr(obj, 'vinculos_cursos_ativos', None)
        if vinculos is not None:
            return vinculos[0].curso.nome if vinculos else None
        vinculo = (
            obj.vinculos_cursos.filter(ativo=True)
            .select_related('curso')
            .order_by('id')
            .first()
        )
        return vinculo.curso.nome if vinculo else None

    @extend_schema_field(OpenApiTypes.DATETIME)
    def get_data_bloqueio(self, obj):
        strikes_ativos = _strikes_ativos_de(obj)
        if not strikes_ativos:
            return None
        return max(strike.created_at for strike in strikes_ativos)


class BloqueioDetalheSerializer(BloqueioSerializer):
    deficiencia = serializers.CharField(source='usuario.deficiencia', allow_null=True)
    ultimo_login = serializers.DateTimeField(source='usuario.last_login', allow_null=True)
    justificativa_pendente = serializers.SerializerMethodField()

    @extend_schema_field(JustificativaPendenteDetalheSerializer(allow_null=True))
    def get_justificativa_pendente(self, obj):
        pendentes = getattr(obj, 'justificativas_pendentes', [])
        if not pendentes:
            return None
        justificativa = pendentes[0]
        return JustificativaPendenteDetalheSerializer(
            justificativa,
            context=self.context,
        ).data
