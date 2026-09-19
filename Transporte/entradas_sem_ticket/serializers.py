from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import EntradaSemTicket


class ValidarEntradaSemTicketSerializer(serializers.Serializer):
    cpf = serializers.CharField(max_length=14)


class RegistrarEntradaSemTicketSerializer(serializers.Serializer):
    versao = serializers.IntegerField(min_value=0)


class AlunoEntradaSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='usuario_id', read_only=True)
    nome = serializers.CharField(source='usuario.nome', read_only=True)
    cpf = serializers.CharField(source='usuario.cpf', read_only=True)
    foto = serializers.URLField(source='usuario.foto', read_only=True, allow_null=True)
    tem_deficiencia = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_tem_deficiencia(self, obj) -> bool:
        valor = getattr(obj.usuario, 'deficiencia', None)
        return bool(valor and str(valor).strip())


class ElegibilidadeEntradaSerializer(serializers.Serializer):
    aluno = AlunoEntradaSerializer()
    elegivel = serializers.BooleanField()


class RascunhoEntradaCpfSerializer(serializers.Serializer):
    versao = serializers.IntegerField(read_only=True)
    concluido = serializers.BooleanField(read_only=True)
    alunos = AlunoEntradaSerializer(many=True, read_only=True)


class CardRascunhoEntradaSerializer(serializers.Serializer):
    aluno = AlunoEntradaSerializer()
    versao = serializers.IntegerField()


class EntradaSemTicketSerializer(serializers.ModelSerializer):
    aluno = AlunoEntradaSerializer(read_only=True)

    class Meta:
        model = EntradaSemTicket
        fields = [
            'id',
            'execucao_rota',
            'aluno',
            'cpf',
            'observacao',
            'data_hora_entrada',
            'created_at',
        ]
