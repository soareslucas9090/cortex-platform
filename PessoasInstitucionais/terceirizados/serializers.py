from rest_framework import serializers

from .models import Terceirizado


class TerceirizadoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario.nome', read_only=True)
    usuario_cpf = serializers.CharField(source='usuario.cpf', read_only=True)
    empresa_nome = serializers.CharField(source='empresa.nome', read_only=True)

    class Meta:
        model = Terceirizado
        fields = [
            'pk', 'usuario_nome', 'usuario_cpf', 'empresa', 'empresa_nome',
            'cargo_funcao', 'data_inicio', 'data_fim',
            'ativo', 'created_at', 'updated_at',
        ]
        read_only_fields = ['pk', 'created_at', 'updated_at']


class CriarTerceirizadoSerializer(serializers.Serializer):
    usuario_pk = serializers.IntegerField()
    empresa_pk = serializers.IntegerField()
    cargo_funcao = serializers.CharField(max_length=255)
    data_inicio = serializers.DateField()
    data_fim = serializers.DateField(required=False, allow_null=True)
    ativo = serializers.BooleanField(default=True, required=False)


class AtualizarTerceirizadoSerializer(serializers.Serializer):
    empresa_pk = serializers.IntegerField(required=False)
    cargo_funcao = serializers.CharField(max_length=255, required=False)
    data_inicio = serializers.DateField(required=False)
    data_fim = serializers.DateField(required=False, allow_null=True)
    ativo = serializers.BooleanField(required=False)
