from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework import serializers

from .models import ImportacaoLote


class ArquivoImportacaoInfraestruturaSerializer(serializers.Serializer):
    file = serializers.FileField(
        help_text='Arquivo .ods da planilha multiaba de importação em lote de infraestrutura.'
    )


@extend_schema_serializer(component_name='ImportacaoErroLinhaInfraestrutura')
class ImportacaoErroLinhaSerializer(serializers.Serializer):
    aba = serializers.CharField()
    numero_linha = serializers.IntegerField()
    campo = serializers.CharField()
    valor = serializers.JSONField(required=False, allow_null=True)
    codigo = serializers.CharField()
    mensagem = serializers.CharField()


@extend_schema_serializer(component_name='ResumoImportacaoInfraestrutura')
class ResumoImportacaoSerializer(serializers.Serializer):
    total_abas_processadas = serializers.IntegerField()
    total_linhas_processadas = serializers.IntegerField()
    total_linhas_com_erro = serializers.IntegerField()
    blocos_criados = serializers.IntegerField()
    blocos_atualizados = serializers.IntegerField()
    salas_criadas = serializers.IntegerField()
    salas_atualizadas = serializers.IntegerField()
    recursos_criados = serializers.IntegerField()
    recursos_atualizados = serializers.IntegerField()


@extend_schema_serializer(component_name='ImportacaoInfraestruturaPreviewResponse')
class ImportacaoInfraestruturaPreviewResponseSerializer(serializers.Serializer):
    sucesso = serializers.BooleanField()
    mensagem = serializers.CharField()
    resumo = ResumoImportacaoSerializer()
    erros = ImportacaoErroLinhaSerializer(many=True)
    metadados = serializers.DictField(required=False)


@extend_schema_serializer(component_name='ImportacaoInfraestruturaResponse')
class ImportacaoInfraestruturaResponseSerializer(serializers.Serializer):
    sucesso = serializers.BooleanField()
    mensagem = serializers.CharField()
    resumo = ResumoImportacaoSerializer()
    erros = ImportacaoErroLinhaSerializer(many=True)
    metadados = serializers.DictField(required=False)


class SerializerVazio(serializers.Serializer):
    """Serializer sem campos — usado em endpoints de ação pura."""

    pass


@extend_schema_serializer(component_name='StatusImportacaoLoteInfraestrutura')
class StatusImportacaoLoteSerializer(serializers.ModelSerializer):
    porcentagem = serializers.SerializerMethodField()
    resultado_json = serializers.SerializerMethodField()

    class Meta:
        model = ImportacaoLote
        fields = [
            'id',
            'status',
            'total_linhas',
            'linhas_processadas',
            'porcentagem',
            'resultado_json',
            'created_at',
            'updated_at',
        ]

    def get_porcentagem(self, obj) -> float:
        if obj.total_linhas == 0:
            return 0.0
        return round((obj.linhas_processadas / obj.total_linhas) * 100, 2)

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_resultado_json(self, obj):
        res = obj.resultado_json
        if res and isinstance(res, dict) and 'erros' in res:
            max_erros = 50
            if isinstance(res['erros'], list) and len(res['erros']) > max_erros:
                res = dict(res)
                total_erros = len(res['erros'])
                res['erros'] = res['erros'][:max_erros]
                res['mensagem_aviso'] = (
                    f'Foram omitidos {total_erros - max_erros} erros devido ao tamanho da resposta. '
                    f'Apenas os primeiros {max_erros} estão sendo exibidos.'
                )
        return res
