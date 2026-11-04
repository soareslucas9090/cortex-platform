from rest_framework import serializers

from .models import TipoAutorizacaoAcesso


class TipoAutorizacaoAcessoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAutorizacaoAcesso
        fields = ['id', 'nome', 'ativo', 'eh_base', 'created_at', 'updated_at']
        read_only_fields = ['id', 'nome', 'ativo', 'eh_base', 'created_at', 'updated_at']
