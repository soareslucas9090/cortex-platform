from datetime import datetime

from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from AppCore.common.util.util import formatar_cpf
from AcessoCampus.tipos.choices import NOME_TIPO_ENTRADA_CAMPUS, NOME_TIPO_SAIDA_CAMPUS
from Identidade.usuarios.models import Usuario

from .choices import StatusEventoAcesso
from .models import EventoAcesso


def _usuario_resumo(usuario):
    if usuario is None:
        return None
    return {'id': usuario.pk, 'nome': usuario.nome}


def _cpf_completo(usuario):
    cpf = getattr(usuario, 'cpf', None)
    return formatar_cpf(cpf) if cpf else None


class UsuarioResumoPortariaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField()


class BeneficiarioEventoAcessoSerializer(serializers.Serializer):
    id = serializers.CharField()
    tipo = serializers.CharField()
    nome = serializers.CharField()


class ProgressoEventoAcessoSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    liberados = serializers.IntegerField()
    pendentes = serializers.IntegerField()


class AcoesEventoAcessoSerializer(serializers.Serializer):
    pode_registrar = serializers.BooleanField()
    pode_conferir_turma = serializers.BooleanField()


class AlunoResumoEventoAcessoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField()
    cpf = serializers.CharField(allow_null=True)
    foto = serializers.CharField(allow_null=True)


class EventoAcessoSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='grupo_portaria_id', read_only=True)
    tipo_beneficiario = serializers.SerializerMethodField()
    beneficiario = serializers.SerializerMethodField()
    tipo_movimento = serializers.SerializerMethodField()
    autorizado_por = serializers.SerializerMethodField()
    data_autorizada = serializers.DateField(source='data_acesso', read_only=True)
    hora_autorizada = serializers.TimeField(source='hora_prevista', read_only=True)
    expira_em = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    responsavel_liberacao = serializers.SerializerMethodField()
    concluida_em = serializers.SerializerMethodField()
    expirada_em = serializers.SerializerMethodField()
    progresso = serializers.SerializerMethodField()
    acoes = serializers.SerializerMethodField()

    class Meta:
        model = EventoAcesso
        fields = [
            'id',
            'tipo_beneficiario',
            'beneficiario',
            'tipo_movimento',
            'autorizado_por',
            'data_autorizada',
            'hora_autorizada',
            'expira_em',
            'status',
            'responsavel_liberacao',
            'concluida_em',
            'expirada_em',
            'progresso',
            'acoes',
        ]

    def _eventos(self, obj):
        return getattr(obj, '_eventos_serializacao', [obj])

    @extend_schema_field(serializers.CharField())
    def get_tipo_beneficiario(self, obj):
        return 'TURMA' if obj.turma_origem else 'INDIVIDUAL'

    @extend_schema_field(BeneficiarioEventoAcessoSerializer)
    def get_beneficiario(self, obj):
        if obj.turma_origem:
            return {'id': str(obj.grupo_portaria_id), 'tipo': 'TURMA', 'nome': f'Turma {obj.turma_origem}'}
        return {'id': obj.aluno_id, 'tipo': 'INDIVIDUAL', 'nome': obj.aluno_nome}

    @extend_schema_field(serializers.CharField())
    def get_tipo_movimento(self, obj):
        if obj.tipo.nome == NOME_TIPO_ENTRADA_CAMPUS:
            return 'ENTRADA'
        if obj.tipo.nome == NOME_TIPO_SAIDA_CAMPUS:
            return 'SAIDA'
        return obj.tipo.nome

    @extend_schema_field(UsuarioResumoPortariaSerializer(allow_null=True))
    def get_autorizado_por(self, obj):
        return _usuario_resumo(obj.solicitacao.avaliada_por)

    @extend_schema_field(serializers.DateTimeField())
    def get_expira_em(self, obj):
        return timezone.make_aware(datetime.combine(obj.data_acesso, obj.hora_prevista))

    @extend_schema_field(serializers.CharField())
    def get_status(self, obj):
        anotado = getattr(obj, 'status_operacional', None)
        if anotado:
            return anotado
        eventos = self._eventos(obj)
        if eventos and all(hasattr(evento, 'registro') for evento in eventos):
            return StatusEventoAcesso.CONCLUIDA
        if any(
            evento.expirado_em
            or timezone.localtime() > timezone.make_aware(datetime.combine(evento.data_acesso, evento.hora_prevista))
            for evento in eventos
        ):
            return StatusEventoAcesso.EXPIRADA
        return StatusEventoAcesso.PENDENTE

    @extend_schema_field(UsuarioResumoPortariaSerializer(allow_null=True))
    def get_responsavel_liberacao(self, obj):
        if hasattr(obj, 'ultimo_registrado_por_id'):
            responsavel_id = obj.ultimo_registrado_por_id
            if responsavel_id is None:
                return None
            return {
                'id': responsavel_id,
                'nome': obj.ultimo_registrado_por_nome,
            }
        registros = [evento.registro for evento in self._eventos(obj) if hasattr(evento, 'registro')]
        if not registros:
            return None
        ultimo = max(registros, key=lambda registro: registro.registrado_em)
        return _usuario_resumo(ultimo.registrado_por)

    @extend_schema_field(serializers.DateTimeField(allow_null=True))
    def get_concluida_em(self, obj):
        if hasattr(obj, 'status_operacional'):
            return obj.ultimo_registro_em if obj.status_operacional == StatusEventoAcesso.CONCLUIDA else None
        eventos = self._eventos(obj)
        if not eventos or not all(hasattr(evento, 'registro') for evento in eventos):
            return None
        return max(evento.registro.registrado_em for evento in eventos)

    @extend_schema_field(serializers.DateTimeField(allow_null=True))
    def get_expirada_em(self, obj):
        if hasattr(obj, 'ultima_expiracao_em'):
            if obj.ultima_expiracao_em:
                return obj.ultima_expiracao_em
            if self.get_status(obj) == StatusEventoAcesso.EXPIRADA:
                return timezone.make_aware(datetime.combine(obj.data_acesso, obj.hora_prevista))
            return None
        datas = [evento.expirado_em for evento in self._eventos(obj) if evento.expirado_em]
        return max(datas) if datas else None

    @extend_schema_field(ProgressoEventoAcessoSerializer)
    def get_progresso(self, obj):
        total = getattr(obj, 'total_eventos', None)
        if total is not None:
            liberados = getattr(obj, 'total_registrados_normalizado', 0)
            return {'total': total, 'liberados': liberados, 'pendentes': total - liberados}
        eventos = self._eventos(obj)
        liberados = sum(hasattr(evento, 'registro') for evento in eventos)
        return {'total': len(eventos), 'liberados': liberados, 'pendentes': len(eventos) - liberados}

    @extend_schema_field(AcoesEventoAcessoSerializer)
    def get_acoes(self, obj):
        pendente = self.get_status(obj) == StatusEventoAcesso.PENDENTE
        return {'pode_registrar': pendente, 'pode_conferir_turma': pendente and bool(obj.turma_origem)}


class EventoAcessoDetalheSerializer(EventoAcessoSerializer):
    observacao = serializers.CharField(source='solicitacao.observacao_avaliacao', read_only=True)
    motivo = serializers.CharField(source='solicitacao.motivo', read_only=True)

    class Meta(EventoAcessoSerializer.Meta):
        fields = EventoAcessoSerializer.Meta.fields + ['motivo', 'observacao']


class AlunoEventoAcessoSerializer(serializers.ModelSerializer):
    aluno = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    liberado_por = serializers.SerializerMethodField()
    liberado_em = serializers.SerializerMethodField()
    pode_liberar = serializers.SerializerMethodField()

    class Meta:
        model = EventoAcesso
        fields = ['id', 'aluno', 'status', 'liberado_por', 'liberado_em', 'pode_liberar']

    @extend_schema_field(AlunoResumoEventoAcessoSerializer)
    def get_aluno(self, obj):
        usuario = obj.aluno.usuario
        return {'id': obj.aluno_id, 'nome': obj.aluno_nome, 'cpf': _cpf_completo(usuario), 'foto': usuario.foto}

    @extend_schema_field(serializers.CharField())
    def get_status(self, obj):
        return 'LIBERADO' if hasattr(obj, 'registro') else 'PENDENTE'

    @extend_schema_field(UsuarioResumoPortariaSerializer(allow_null=True))
    def get_liberado_por(self, obj):
        return _usuario_resumo(obj.registro.registrado_por) if hasattr(obj, 'registro') else None

    @extend_schema_field(serializers.DateTimeField(allow_null=True))
    def get_liberado_em(self, obj):
        return obj.registro.registrado_em if hasattr(obj, 'registro') else None

    @extend_schema_field(serializers.BooleanField())
    def get_pode_liberar(self, obj):
        anotado = getattr(obj, 'pode_liberar_operacional', None)
        if anotado is not None:
            return anotado
        return (
            not hasattr(obj, 'registro')
            and not obj.expirado_em
            and timezone.localtime() <= timezone.make_aware(datetime.combine(obj.data_acesso, obj.hora_prevista))
        )


class RegistrarEventoAcessoSerializer(serializers.Serializer):
    responsavel_liberacao_id = serializers.IntegerField(required=False)
    aluno_ids = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=False)
    observacao = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_aluno_ids(self, value):
        return list(dict.fromkeys(value))


class ResumoRegistroEventoAcessoSerializer(serializers.Serializer):
    solicitados = serializers.IntegerField()
    confirmados_agora = serializers.IntegerField()
    ja_confirmados = serializers.IntegerField()


class RegistrarEventoAcessoResponseSerializer(serializers.Serializer):
    autorizacao = EventoAcessoDetalheSerializer()
    registro = ResumoRegistroEventoAcessoSerializer()


class ResponsavelElegivelSerializer(serializers.ModelSerializer):
    cpf = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'nome', 'cpf', 'foto']

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_cpf(self, obj):
        return _cpf_completo(obj)
