from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework import serializers

from .choices import TipoRecurso
from .models import Recurso


@extend_schema_serializer(component_name='RecursoSalaResumo')
class SalaResumoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField()


class RecursoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_derivado = serializers.CharField(read_only=True)
    estado_derivado_display = serializers.SerializerMethodField()
    sala = SalaResumoSerializer(read_only=True)

    class Meta:
        model = Recurso
        fields = [
            'id', 'codigo', 'tipo', 'tipo_display', 'sala', 'descricao',
            'em_avaria', 'ativo', 'estado_derivado', 'estado_derivado_display', 'created_at',
        ]

    @extend_schema_field(serializers.CharField())
    def get_estado_derivado_display(self, obj):
        from .choices import EstadoRecurso
        return EstadoRecurso(obj.estado_derivado).label


class CriarRecursoSerializer(serializers.Serializer):
    codigo = serializers.CharField(max_length=50)
    tipo = serializers.ChoiceField(choices=TipoRecurso.choices)
    sala_id = serializers.IntegerField(required=False, allow_null=True)
    descricao = serializers.CharField(max_length=500, required=False, allow_blank=True, default='')
    em_avaria = serializers.BooleanField(required=False, default=False)


class AtualizarRecursoSerializer(serializers.Serializer):
    codigo = serializers.CharField(max_length=50, required=False)
    tipo = serializers.ChoiceField(choices=TipoRecurso.choices, required=False)
    sala_id = serializers.IntegerField(required=False, allow_null=True)
    descricao = serializers.CharField(max_length=500, required=False, allow_blank=True)
    em_avaria = serializers.BooleanField(required=False)


class SerializerVazio(serializers.Serializer):
    pass
