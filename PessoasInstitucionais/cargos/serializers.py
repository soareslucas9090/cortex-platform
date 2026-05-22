from rest_framework import serializers
from .models import Cargo


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = ['id', 'nome', 'ativo', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CriarCargoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255)
    ativo = serializers.BooleanField(default=True, required=False)


class AtualizarCargoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255, required=False)
    ativo = serializers.BooleanField(required=False)
