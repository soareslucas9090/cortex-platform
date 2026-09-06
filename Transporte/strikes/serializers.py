from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from Transporte.tickets.serializers import TicketSerializer

from .models import Strike


class StrikeSerializer(serializers.ModelSerializer):
    ticket = TicketSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    bloqueia_novas_reservas = serializers.SerializerMethodField()

    class Meta:
        model = Strike
        fields = [
            'id',
            'ticket',
            'status',
            'status_display',
            'bloqueia_novas_reservas',
            'created_at',
        ]

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_bloqueia_novas_reservas(self, obj):
        return obj.ticket.aluno.is_bloqueado
