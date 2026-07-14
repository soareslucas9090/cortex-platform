from rest_framework import serializers

from .models import Autorizacao


class UsuarioResumoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField()
    cpf = serializers.CharField()


class SalaResumoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField()


class RecursoResumoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    codigo = serializers.CharField()
    tipo = serializers.CharField()


class AutorizacaoSerializer(serializers.ModelSerializer):
    beneficiario = UsuarioResumoSerializer(read_only=True)
    concedente = UsuarioResumoSerializer(read_only=True)
    revogador = UsuarioResumoSerializer(read_only=True)
    sala = SalaResumoSerializer(read_only=True)
    recurso = RecursoResumoSerializer(read_only=True)
    vigente = serializers.BooleanField(read_only=True)

    class Meta:
        model = Autorizacao
        fields = [
            'id',
            'beneficiario',
            'concedente',
            'sala',
            'recurso',
            'data_inicio',
            'data_fim',
            'revogado_em',
            'revogador',
            'observacao',
            'vigente',
            'created_at',
        ]


class ConcederAutorizacaoSerializer(serializers.Serializer):
    beneficiario_id = serializers.IntegerField()
    sala_id = serializers.IntegerField(required=False, allow_null=True)
    recurso_id = serializers.IntegerField(required=False, allow_null=True)
    data_inicio = serializers.DateField()
    data_fim = serializers.DateField(required=False, allow_null=True)
    observacao = serializers.CharField(required=False, allow_blank=True, default='')


class SerializerVazio(serializers.Serializer):
    pass
