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
    foto = serializers.SerializerMethodField()

    class Meta:
        model = Recurso
        fields = [
            'id', 'codigo', 'tipo', 'tipo_display', 'sala', 'descricao', 'foto',
            'em_avaria', 'ativo', 'estado_derivado', 'estado_derivado_display', 'created_at',
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_foto(self, obj) -> str | None:
        from AppCore.common.storage.s3 import montar_url_proxy_arquivo
        from .foto import NOME_URL_PROXY, caminho_fallback_proxy
        return montar_url_proxy_arquivo(
            obj.pk,
            obj.foto,
            NOME_URL_PROXY,
            self.context.get('request'),
            caminho_fallback=caminho_fallback_proxy(obj.pk),
        )

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
    foto = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text='Arquivo de imagem opcional (JPEG, PNG ou WebP, até 3 MB). Retrato 3:4, mínimo 480×640 após recorte.',
    )


class EnviarFotoRecursoSerializer(serializers.Serializer):
    foto = serializers.ImageField(
        help_text='Arquivo de imagem (JPEG, PNG ou WebP, até 3 MB). Retrato 3:4, mínimo 480×640 após recorte.',
    )


class AtualizarRecursoSerializer(serializers.Serializer):
    codigo = serializers.CharField(max_length=50, required=False)
    tipo = serializers.ChoiceField(choices=TipoRecurso.choices, required=False)
    sala_id = serializers.IntegerField(required=False, allow_null=True)
    descricao = serializers.CharField(max_length=500, required=False, allow_blank=True)
    em_avaria = serializers.BooleanField(required=False)


class SerializerVazio(serializers.Serializer):
    pass
