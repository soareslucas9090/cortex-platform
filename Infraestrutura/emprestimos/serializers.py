from rest_framework import serializers

from .models import Emprestimo, ItemEmprestimo


class UsuarioResumoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField()
    cpf = serializers.CharField()


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


class DevolverItensSerializer(serializers.Serializer):
    item_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
    )


class TrocarTitularSerializer(serializers.Serializer):
    novo_solicitante_id = serializers.IntegerField()
    observacao = serializers.CharField(required=False, allow_blank=True, default='')


class SerializerVazio(serializers.Serializer):
    pass
