from django.contrib.auth import get_user_model

from rest_framework import serializers

from Organizacional.funcoes.models import Funcao
from .models import SetorVinculo


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
