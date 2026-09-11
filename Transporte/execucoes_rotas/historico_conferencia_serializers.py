from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from .historico_serializers import HistoricoRotaSerializer


class ConferenteHistoricoSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    nome = serializers.CharField(read_only=True)


class AlunoHistoricoConferenciaSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='aluno.usuario_id', read_only=True)
    nome = serializers.CharField(source='aluno.usuario.nome', read_only=True)
    cpf = serializers.CharField(source='aluno.usuario.cpf', read_only=True)
    tem_deficiencia = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_tem_deficiencia(self, obj) -> bool:
        valor = getattr(getattr(obj.aluno, 'usuario', None), 'deficiencia', None)
        return bool(valor and str(valor).strip())


class DetalheHistoricoConferenciaSerializer(HistoricoRotaSerializer):
    percurso_descricao = serializers.CharField(source='rota.percurso.descricao', read_only=True)
    conferencia_finalizada_em = serializers.DateTimeField(
        source='embarcado_em', read_only=True, allow_null=True,
    )
    conferencia_finalizada_por = ConferenteHistoricoSerializer(read_only=True, allow_null=True)
    tickets_presentes = AlunoHistoricoConferenciaSerializer(many=True, read_only=True)
    tickets_ausentes = AlunoHistoricoConferenciaSerializer(many=True, read_only=True)
    passageiros_sem_ticket = AlunoHistoricoConferenciaSerializer(many=True, read_only=True)

    class Meta(HistoricoRotaSerializer.Meta):
        fields = HistoricoRotaSerializer.Meta.fields + [
            'percurso_descricao', 'quantidade_vagas',
            'conferencia_finalizada_em', 'conferencia_finalizada_por',
            'tickets_presentes', 'tickets_ausentes', 'passageiros_sem_ticket',
        ]
        read_only_fields = fields
