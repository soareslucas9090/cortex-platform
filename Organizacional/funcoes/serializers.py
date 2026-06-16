from rest_framework import serializers

from .models import Funcao


class FuncaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcao
        fields = ['id', 'papel_funcao', 'descricao', 'e_gratificada', 'exige_aluno', 'ativo', 'created_at']


class CriarFuncaoSerializer(serializers.Serializer):
    papel_funcao = serializers.CharField(max_length=255)
    descricao = serializers.CharField(max_length=255)
    e_gratificada = serializers.BooleanField(default=False, required=False)
    exige_aluno = serializers.BooleanField(default=False, required=False)


class AtualizarFuncaoSerializer(serializers.Serializer):
    papel_funcao = serializers.CharField(max_length=255, required=False)
    descricao = serializers.CharField(max_length=255, required=False)
    e_gratificada = serializers.BooleanField(required=False)
    exige_aluno = serializers.BooleanField(required=False)


class SerializerVazio(serializers.Serializer):
    """Serializer sem campos — usado em endpoints de ação pura."""
    pass
