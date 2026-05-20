from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import Setor, Funcao, SetorVinculo


# =============================================================================
# Serializers de saída (leitura)
# =============================================================================

class SetorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setor
        fields = ['id', 'nome', 'sigla', 'ativo', 'created_at']


class FuncaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcao
        fields = ['id', 'sigla', 'descricao', 'e_gratificada', 'ativo', 'created_at']


class SetorVinculoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario.nome', read_only=True)
    funcao_sigla = serializers.CharField(source='funcao.sigla', read_only=True)
    funcao_descricao = serializers.CharField(source='funcao.descricao', read_only=True)

    class Meta:
        model = SetorVinculo
        fields = [
            'id', 'usuario', 'usuario_nome', 'setor',
            'funcao', 'funcao_sigla', 'funcao_descricao',
            'responsavel', 'created_at',
        ]


# =============================================================================
# Serializers de entrada (escrita)
# =============================================================================

class CriarSetorSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255)
    sigla = serializers.CharField(max_length=20)


class AtualizarSetorSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255, required=False)
    sigla = serializers.CharField(max_length=20, required=False)


class CriarFuncaoSerializer(serializers.Serializer):
    sigla = serializers.CharField(max_length=20)
    descricao = serializers.CharField(max_length=255)
    e_gratificada = serializers.BooleanField(default=False, required=False)


class AtualizarFuncaoSerializer(serializers.Serializer):
    sigla = serializers.CharField(max_length=20, required=False)
    descricao = serializers.CharField(max_length=255, required=False)
    e_gratificada = serializers.BooleanField(required=False)


class CriarVinculoSerializer(serializers.Serializer):
    usuario = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
        help_text='ID do usuário a ser vinculado ao setor.',
    )
    funcao = serializers.PrimaryKeyRelatedField(
        queryset=Funcao.objects.all(),
        help_text='ID da função a ser exercida no setor.',
    )
    responsavel = serializers.BooleanField(
        default=False,
        required=False,
        help_text='Define se o usuário será marcado como responsável pelo setor.',
    )


class AtualizarVinculoFuncaoSerializer(serializers.Serializer):
    funcao = serializers.PrimaryKeyRelatedField(
        queryset=Funcao.objects.all(),
        help_text='ID da nova função a ser atribuída ao vínculo.',
    )


class SerializerVazio(serializers.Serializer):
    """Serializer sem campos — usado em endpoints de ação pura."""
    pass
