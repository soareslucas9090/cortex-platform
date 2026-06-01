from rest_framework import serializers

from .models import Terceirizado


class TerceirizadoSerializer(serializers.ModelSerializer):
    pk = serializers.IntegerField(read_only=True)
    usuario_nome = serializers.CharField(source='usuario.nome', read_only=True)
    usuario_cpf = serializers.CharField(source='usuario.cpf', read_only=True)
    empresa_nome = serializers.CharField(source='empresa_instituicao.nome', read_only=True)
    cargo_nome = serializers.CharField(source='cargo.nome', read_only=True)

    class Meta:
        model = Terceirizado
        fields = [
            'pk', 'usuario_nome', 'usuario_cpf', 'empresa_instituicao', 'empresa_nome',
            'cargo', 'cargo_nome', 'data_inicio', 'data_fim',
            'ativo', 'created_at', 'updated_at',
        ]
        read_only_fields = ['pk', 'created_at', 'updated_at']


class CriarTerceirizadoSerializer(serializers.Serializer):
    usuario_pk = serializers.IntegerField()
    empresa_pk = serializers.IntegerField()
    cargo_pk = serializers.IntegerField(required=False, allow_null=True)
    data_inicio = serializers.DateField()
    data_fim = serializers.DateField(required=False, allow_null=True)
    ativo = serializers.BooleanField(default=True, required=False)


class AtualizarTerceirizadoSerializer(serializers.Serializer):
    empresa_pk = serializers.IntegerField(required=False)
    cargo_pk = serializers.IntegerField(required=False, allow_null=True)
    data_inicio = serializers.DateField(required=False)
    data_fim = serializers.DateField(required=False, allow_null=True)
    ativo = serializers.BooleanField(required=False)
