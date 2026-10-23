from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from Identidade.usuarios.constantes import ANEXO_FOTO_SECUNDARIA

from .models import Emprestimo, ItemEmprestimo, SolicitacaoTrocaTitular


@extend_schema_serializer(component_name='EmprestimoUsuarioResumo')
class UsuarioResumoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField()
    cpf = serializers.CharField()
    foto = serializers.URLField(allow_null=True, allow_blank=True)
    foto_secundaria = serializers.SerializerMethodField()

    def get_foto_secundaria(self, obj) -> str | None:
        return ANEXO_FOTO_SECUNDARIA.url_proxy(obj.pk, obj.foto_secundaria, self.context.get('request'))


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
    solicitacao_troca = serializers.SerializerMethodField()
    origem_conta_coletiva = serializers.CharField(read_only=True, allow_null=True)

    def get_solicitacao_troca(self, obj) -> dict | None:
        solicitacoes = getattr(obj, '_solicitacoes_troca_usuario', [])
        if not solicitacoes:
            return None
        return SolicitacaoTrocaTitularResumoSerializer(solicitacoes[0], context=self.context).data

    class Meta:
        model = Emprestimo
        fields = [
            'id',
            'solicitante',
            'responsavel',
            'origem_conta_coletiva',
            'retirada_em',
            'observacao',
            'itens',
            'ativo',
            'atrasado',
            'solicitacao_troca',
            'created_at',
        ]


class RealizarEmprestimoSerializer(serializers.Serializer):
    solicitante_id = serializers.IntegerField()
    recurso_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    observacao = serializers.CharField(required=False, allow_blank=True, default='')
    responsavel_id = serializers.IntegerField(required=False, allow_null=True)


class DevolverItensSerializer(serializers.Serializer):
    item_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class TrocarTitularSerializer(serializers.Serializer):
    novo_solicitante_id = serializers.IntegerField()
    observacao = serializers.CharField(required=False, allow_blank=True, default='')
    responsavel_id = serializers.IntegerField(required=False, allow_null=True)


class SerializerVazio(serializers.Serializer):
    pass


class CriarSolicitacaoTrocaTitularSerializer(serializers.Serializer):
    destinatario_id = serializers.IntegerField()
    observacao = serializers.CharField(required=False, allow_blank=True, default='')


@extend_schema_serializer(component_name='SolicitacaoTrocaUsuarioResumo')
class UsuarioSolicitacaoResumoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField()


class SolicitacaoTrocaTitularResumoSerializer(serializers.ModelSerializer):
    direcao = serializers.SerializerMethodField()
    solicitante = UsuarioSolicitacaoResumoSerializer(read_only=True)
    destinatario = UsuarioSolicitacaoResumoSerializer(read_only=True)
    pode_aceitar = serializers.SerializerMethodField()
    pode_recusar = serializers.SerializerMethodField()
    pode_cancelar = serializers.SerializerMethodField()

    class Meta:
        model = SolicitacaoTrocaTitular
        fields = [
            'id',
            'status',
            'direcao',
            'solicitante',
            'destinatario',
            'pode_aceitar',
            'pode_recusar',
            'pode_cancelar',
            'created_at',
        ]

    def _usuario(self):
        request = self.context.get('request')
        return request.user if request else None

    def get_direcao(self, obj) -> str | None:
        usuario = self._usuario()
        if not usuario:
            return None
        if obj.solicitante_id == usuario.pk:
            return 'ENVIADA'
        if obj.destinatario_id == usuario.pk:
            return 'RECEBIDA'
        return None

    def get_pode_aceitar(self, obj) -> bool:
        usuario = self._usuario()
        return obj.state.pode_aceitar(usuario) if usuario else False

    def get_pode_recusar(self, obj) -> bool:
        usuario = self._usuario()
        return obj.state.pode_recusar(usuario) if usuario else False

    def get_pode_cancelar(self, obj) -> bool:
        usuario = self._usuario()
        return obj.state.pode_cancelar(usuario) if usuario else False


class EmprestimoSolicitacaoTrocaSerializer(serializers.ModelSerializer):
    solicitante = UsuarioSolicitacaoResumoSerializer(read_only=True)
    responsavel = UsuarioSolicitacaoResumoSerializer(read_only=True)
    itens = ItemEmprestimoSerializer(many=True, read_only=True)
    ativo = serializers.BooleanField(read_only=True)
    atrasado = serializers.BooleanField(read_only=True)
    origem_conta_coletiva = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = Emprestimo
        fields = [
            'id',
            'retirada_em',
            'ativo',
            'atrasado',
            'observacao',
            'solicitante',
            'responsavel',
            'origem_conta_coletiva',
            'itens',
        ]


class SolicitacaoTrocaTitularSerializer(SolicitacaoTrocaTitularResumoSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    emprestimo = EmprestimoSolicitacaoTrocaSerializer(read_only=True)
    novo_emprestimo_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta(SolicitacaoTrocaTitularResumoSerializer.Meta):
        fields = [
            'id',
            'status',
            'status_display',
            'observacao',
            'created_at',
            'updated_at',
            'respondido_em',
            'pode_aceitar',
            'pode_recusar',
            'pode_cancelar',
            'direcao',
            'solicitante',
            'destinatario',
            'emprestimo',
            'novo_emprestimo_id',
        ]


class AceitarSolicitacaoTrocaTitularRespostaSerializer(serializers.Serializer):
    solicitacao = SolicitacaoTrocaTitularSerializer()
    novo_emprestimo = EmprestimoSerializer()
