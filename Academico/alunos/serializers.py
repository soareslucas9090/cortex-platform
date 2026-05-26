from rest_framework import serializers

from .choices import FormaIngresso, SituacaoAluno
from .models import Aluno


class AlunoSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.nome', read_only=True)
    usuario_cpf = serializers.CharField(source='usuario.cpf', read_only=True)
    situacao_display = serializers.CharField(source='get_situacao_display', read_only=True)
    forma_ingresso_display = serializers.CharField(source='get_forma_ingresso_display', read_only=True)

    class Meta:
        model = Aluno
        fields = [
            'usuario_id',
            'usuario_nome',
            'usuario_cpf',
            'ira',
            'situacao',
            'situacao_display',
            'forma_ingresso',
            'forma_ingresso_display',
            'ativo',
            'created_at',
        ]
        read_only_fields = [
            'usuario_id',
            'usuario_nome',
            'usuario_cpf',
            'situacao_display',
            'forma_ingresso_display',
            'created_at',
        ]


class CriarAlunoSerializer(serializers.Serializer):
    usuario = serializers.IntegerField(required=True)
    ira = serializers.FloatField(required=False)
    situacao = serializers.ChoiceField(choices=SituacaoAluno.choices, required=False)
    forma_ingresso = serializers.ChoiceField(choices=FormaIngresso.choices, required=False)
    ativo = serializers.BooleanField(required=False, default=True)


class AtualizarAlunoSerializer(serializers.Serializer):
    ira = serializers.FloatField(required=False)
    situacao = serializers.ChoiceField(choices=SituacaoAluno.choices, required=False)
    forma_ingresso = serializers.ChoiceField(choices=FormaIngresso.choices, required=False)
    ativo = serializers.BooleanField(required=False)

