from rest_framework import serializers

from .models import Sala, SalaSetor


class BlocoResumoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField()


class SetorResumoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sigla = serializers.CharField()
    nome = serializers.CharField()


class SalaSerializer(serializers.ModelSerializer):
    bloco = BlocoResumoSerializer(read_only=True)

    class Meta:
        model = Sala
        fields = ['id', 'bloco', 'nome', 'ativo', 'created_at']


class CriarSalaSerializer(serializers.Serializer):
    bloco_id = serializers.IntegerField()
    nome = serializers.CharField(max_length=255)


class AtualizarSalaSerializer(serializers.Serializer):
    bloco_id = serializers.IntegerField(required=False)
    nome = serializers.CharField(max_length=255, required=False)


class SalaSetorSerializer(serializers.ModelSerializer):
    sala = SalaSerializer(read_only=True)
    setor = SetorResumoSerializer(read_only=True)

    class Meta:
        model = SalaSetor
        fields = ['id', 'sala', 'setor', 'created_at']


class CriarSalaSetorSerializer(serializers.Serializer):
    sala_id = serializers.IntegerField()
    setor_id = serializers.IntegerField()


class SerializerVazio(serializers.Serializer):
    pass
