from rest_framework import serializers

from .choices import FormaIngresso, SituacaoAluno
from .models import Aluno


class AlunoSerializer(serializers.Serializer):
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.nome', read_only=True)
    usuario_cpf = serializers.CharField(source='usuario.cpf', read_only=True)
    ira = serializers.DecimalField(max_digits=5, decimal_places=4, read_only=True)
    situacao = serializers.ChoiceField(choices=SituacaoAluno.choices, read_only=True)
    forma_ingresso = serializers.ChoiceField(choices=FormaIngresso.choices, read_only=True)
    ativo = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class CriarAlunoSerializer(serializers.Serializer):
    usuario = serializers.IntegerField(required=True)
    ira = serializers.DecimalField(max_digits=5, decimal_places=4, required=False)
    situacao = serializers.ChoiceField(choices=SituacaoAluno.choices, required=False)
    forma_ingresso = serializers.ChoiceField(choices=FormaIngresso.choices, required=False)
    ativo = serializers.BooleanField(required=False, default=True)


class AtualizarAlunoSerializer(serializers.Serializer):
    ira = serializers.DecimalField(max_digits=5, decimal_places=4, required=False)
    situacao = serializers.ChoiceField(choices=SituacaoAluno.choices, required=False)
    forma_ingresso = serializers.ChoiceField(choices=FormaIngresso.choices, required=False)
    ativo = serializers.BooleanField(required=False)
