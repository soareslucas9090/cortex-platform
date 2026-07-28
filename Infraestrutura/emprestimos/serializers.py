from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from .models import Emprestimo, ItemEmprestimo


@extend_schema_serializer(component_name='EmprestimoUsuarioResumo')
class UsuarioResumoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField()
    cpf = serializers.CharField()


@extend_schema_serializer(component_name='EmprestimoRecursoResumo')
class RecursoResumoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    codigo = serializers.CharField()
    tipo = serializers.CharField()
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)


class ItemEmprestimoSerializer(serializers.ModelSerializer):
    recurso = RecursoResumoSerializer(read_only=True)
    ativo = serializers.BooleanField(read_only=True)

    class Meta:
        model = ItemEmprestimo
        fields = ['id', 'recurso', 'devolvido_em', 'ativo']


class EmprestimoSerializer(serializers.ModelSerializer):
    solicitante = UsuarioResumoSerializer(read_only=True)
    responsavel = UsuarioResumoSerializer(read_only=True)
    itens = ItemEmprestimoSerializer(many=True, read_only=True)
    ativo = serializers.BooleanField(read_only=True)
    atrasado = serializers.BooleanField(read_only=True)

    class Meta:
        model = Emprestimo
        fields = [
            'id',
            'solicitante',
            'responsavel',
            'retirada_em',
            'observacao',
            'itens',
            'ativo',
            'atrasado',
            'created_at',
        ]


class RealizarEmprestimoSerializer(serializers.Serializer):
    solicitante_id = serializers.IntegerField()
    recurso_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
    )
    observacao = serializers.CharField(required=False, allow_blank=True, default='')
    responsavel_id = serializers.IntegerField(required=False, allow_null=True)


class DevolverItensSerializer(serializers.Serializer):
    item_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
    )


class TrocarTitularSerializer(serializers.Serializer):
    novo_solicitante_id = serializers.IntegerField()
    observacao = serializers.CharField(required=False, allow_blank=True, default='')
    responsavel_id = serializers.IntegerField(required=False, allow_null=True)


class SerializerVazio(serializers.Serializer):
    pass
