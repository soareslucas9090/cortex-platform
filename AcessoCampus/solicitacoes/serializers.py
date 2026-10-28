from rest_framework import serializers

from Identidade.usuarios.constantes import ANEXO_FOTO_SECUNDARIA

from .choices import RESULTADO_AVALIACAO, TipoSolicitacaoAcesso
from .helpers import FUSO_FORTALEZA
from .models import SolicitacaoAcesso


class AlunoElegivelSerializer(serializers.Serializer):
    aluno_curso = serializers.IntegerField(source='id')
    nome = serializers.CharField(source='aluno.usuario.nome')
    cpf = serializers.CharField(source='aluno.usuario.cpf', allow_null=True)
    foto = serializers.URLField(source='aluno.usuario.foto', allow_null=True)
    foto_secundaria = serializers.SerializerMethodField()
    curso_id = serializers.IntegerField()
    curso_nome = serializers.CharField(source='curso.nome')
    turma = serializers.CharField(allow_null=True)

    def get_foto_secundaria(self, obj):
        usuario = obj.aluno.usuario
        return ANEXO_FOTO_SECUNDARIA.url_proxy(
            usuario.pk,
            usuario.foto_secundaria,
            self.context.get('request'),
        )


class TurmaElegivelSerializer(serializers.Serializer):
    curso_id = serializers.IntegerField()
    curso_nome = serializers.CharField()
    turma = serializers.CharField()


class UsuarioResumoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField()


class AutorizarAcessoSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=TipoSolicitacaoAcesso.choices)
    data_acesso = serializers.DateField()
    hora_autorizada = serializers.TimeField()
    motivo = serializers.CharField(max_length=255)
    observacao = serializers.CharField(required=False, allow_blank=True)
    aluno_curso_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=False,
    )
    curso_id = serializers.IntegerField(required=False)
    turma = serializers.CharField(required=False, allow_blank=True, max_length=50)


class AceitarSolicitacaoSerializer(serializers.Serializer):
    hora_autorizada = serializers.TimeField(required=False)
    observacao = serializers.CharField(required=False, allow_blank=True)


class RecusarSolicitacaoSerializer(serializers.Serializer):
    observacao = serializers.CharField(required=False, allow_blank=True)


class SolicitacaoAcessoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    resultado_avaliacao = serializers.SerializerMethodField()
    avaliada_por = serializers.SerializerMethodField()
    data_solicitacao = serializers.SerializerMethodField()
    hora_solicitacao = serializers.SerializerMethodField()

    class Meta:
        model = SolicitacaoAcesso
        fields = [
            'id',
            'origem',
            'tipo',
            'tipo_display',
            'status',
            'status_display',
            'resultado_avaliacao',
            'data_acesso',
            'hora_autorizada',
            'data_solicitacao',
            'hora_solicitacao',
            'motivo',
            'avaliada_por',
            'aluno_nome',
            'curso_nome',
            'matricula',
            'created_at',
        ]

    def get_resultado_avaliacao(self, obj):
        return RESULTADO_AVALIACAO[obj.status]

    def get_avaliada_por(self, obj):
        if obj.avaliada_por_id is None:
            return None
        return UsuarioResumoSerializer(obj.avaliada_por).data

    def get_data_solicitacao(self, obj):
        return obj.created_at.astimezone(FUSO_FORTALEZA).date()

    def get_hora_solicitacao(self, obj):
        return obj.created_at.astimezone(FUSO_FORTALEZA).time().replace(microsecond=0)


class SolicitacaoAcessoDetalheSerializer(SolicitacaoAcessoSerializer):
    historico = serializers.SerializerMethodField()
    liberado_por = serializers.SerializerMethodField()
    aluno = serializers.SerializerMethodField()

    class Meta(SolicitacaoAcessoSerializer.Meta):
        fields = SolicitacaoAcessoSerializer.Meta.fields + [
            'hora_solicitada',
            'justificativa',
            'observacao_avaliacao',
            'avaliada_em',
            'liberado_por',
            'aluno',
            'historico',
            'lote_id',
            'turma_origem',
        ]

    def get_historico(self, obj):
        return obj.helper.montar_historico()

    def get_liberado_por(self, obj):
        if obj.liberado_por_id is None:
            return None
        return UsuarioResumoSerializer(obj.liberado_por).data

    def get_aluno(self, obj):
        usuario = obj.aluno.usuario
        return {
            'nome': usuario.nome,
            'foto': usuario.foto,
            'foto_secundaria': ANEXO_FOTO_SECUNDARIA.url_proxy(
                usuario.pk,
                usuario.foto_secundaria,
                self.context.get('request'),
            ),
        }
