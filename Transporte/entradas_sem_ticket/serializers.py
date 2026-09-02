from rest_framework import serializers

from .models import EntradaSemTicket


class RegistrarEntradaSemTicketSerializer(serializers.Serializer):
    cpf = serializers.CharField(max_length=14)
    observacao = serializers.CharField(required=False, allow_blank=True, default='')


class AlunoEntradaSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='usuario_id', read_only=True)
    nome = serializers.CharField(source='usuario.nome', read_only=True)
    cpf = serializers.CharField(source='usuario.cpf', read_only=True)
    foto = serializers.URLField(source='usuario.foto', read_only=True, allow_null=True)


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
