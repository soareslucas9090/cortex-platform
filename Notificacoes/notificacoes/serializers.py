from rest_framework import serializers

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from .models import Notificacao


class NotificacaoSerializer(serializers.ModelSerializer):
    lida = serializers.SerializerMethodField()

    class Meta:
        model = Notificacao
        fields = (
            'id',
            'tipo',
            'titulo',
            'corpo',
            'contexto',
            'lida_em',
            'lida',
            'created_at',
        )
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_lida(self, obj):
        return obj.lida_em is not None


class SerializerVazio(serializers.Serializer):
    """Serializer sem campos — usado em endpoints de ação pura."""
    pass


class ContadorNaoLidasSerializer(serializers.Serializer):
    quantidade = serializers.IntegerField()
