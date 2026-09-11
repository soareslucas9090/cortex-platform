from django.utils import timezone
from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from Transporte.percursos.models import Percurso
from Transporte.permissoes.access import (
    usuario_e_administrador_transporte,
    usuario_pode_operar_rota,
)

from .choices import StatusExecucaoRota
from .models import ExecucaoRota


class ViagemRotaSerializer(serializers.ModelSerializer):
    duracao_rota_segundos = serializers.IntegerField(read_only=True, allow_null=True)
    pode_iniciar_rota = serializers.SerializerMethodField()
    pode_finalizar_rota = serializers.SerializerMethodField()
    servidor_agora = serializers.SerializerMethodField()

    class Meta:
        model = ExecucaoRota
        fields = [
            'id', 'rota_iniciada_em', 'rota_finalizada_em', 'rota_iniciada_por',
            'duracao_rota_segundos', 'pode_iniciar_rota', 'pode_finalizar_rota',
            'servidor_agora',
        ]
        read_only_fields = fields

    def _pode_operar(self):
        if 'viagem_pode_operar' not in self.context:
            request = self.context.get('request')
            self.context['viagem_pode_operar'] = usuario_pode_operar_rota(
                request.user if request else None,
            )
        return self.context['viagem_pode_operar']

    def get_pode_iniciar_rota(self, obj) -> bool:
        return bool(
            self._pode_operar()
            and obj.status == StatusExecucaoRota.EMBARCADO
            and obj.data_execucao == timezone.localdate()
            and obj.rota.ativo and obj.rota.percurso.ativo
            and obj.rota_iniciada_em is None
            and obj.rota_finalizada_em is None
        )

    def get_pode_finalizar_rota(self, obj) -> bool:
        request = self.context.get('request')
        usuario = request.user if request else None
        return bool(
            self._pode_operar()
            and obj.status == StatusExecucaoRota.INICIADA
            and obj.rota_iniciada_em is not None
            and obj.rota_finalizada_em is None
            and (
                obj.rota_iniciada_por_id == usuario.pk
                or usuario_e_administrador_transporte(usuario)
            )
        )

    def get_servidor_agora(self, obj) -> str:
        return timezone.now().isoformat()


# Import tardio: rotas.serializers usa ViagemRotaSerializer e este módulo usa RotaSerializer.
from Transporte.rotas.serializers import RotaSerializer  # noqa: E402


class ExecucaoRotaSerializer(serializers.ModelSerializer):
    viagem = ViagemRotaSerializer(source='*', read_only=True)
    rota = RotaSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    vagas_ocupadas = serializers.SerializerMethodField()
    vagas_disponiveis = serializers.SerializerMethodField()
    pode_monitorar = serializers.SerializerMethodField()

    class Meta:
        model = ExecucaoRota
        fields = [
            'id',
            'viagem',
            'rota',
            'data_execucao',
            'data_hora_saida',
            'quantidade_vagas',
            'vagas_ocupadas',
            'vagas_disponiveis',
            'pode_monitorar',
            'chamada_tickets_concluida',
            'entradas_cpf_concluidas',
            'monitoramento_iniciado_em',
            'chamada_concluida_em',
            'embarcado_em',
            'finalizada_em',
            'status',
            'status_display',
            'created_at',
        ]

    @extend_schema_field(OpenApiTypes.INT)
    def get_vagas_ocupadas(self, obj):
        return self._obter_resumo_vagas(obj)['vagas_ocupadas']

    @extend_schema_field(OpenApiTypes.INT)
    def get_vagas_disponiveis(self, obj):
        return self._obter_resumo_vagas(obj)['vagas_disponiveis']

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_pode_monitorar(self, obj):
        return obj.business.pode_monitorar()

    def _obter_resumo_vagas(self, obj):
        if not hasattr(self, '_resumo_vagas_por_execucao'):
            self._resumo_vagas_por_execucao = {}
        if obj.pk not in self._resumo_vagas_por_execucao:
            self._resumo_vagas_por_execucao[obj.pk] = obj.business.obter_resumo_vagas()
        return self._resumo_vagas_por_execucao[obj.pk]


class CriarExecucaoRotaSerializer(serializers.Serializer):
    rota_id = serializers.IntegerField()
    data_execucao = serializers.DateField()


class FinalizarChamadaSerializer(serializers.Serializer):
    ausentes = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
    )


class SerializerVazio(serializers.Serializer):
    pass


class PercursoHistoricoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Percurso
        fields = ['id', 'apelido']
        read_only_fields = fields


class HistoricoRotaSerializer(serializers.ModelSerializer):
    data = serializers.DateField(source='data_execucao', read_only=True)
    horario = serializers.SerializerMethodField()
    percurso = PercursoHistoricoSerializer(source='rota.percurso', read_only=True)
    presentes = serializers.IntegerField(read_only=True)
    ausentes = serializers.IntegerField(read_only=True)
    sem_ticket = serializers.IntegerField(read_only=True)
    duracao_rota_segundos = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = ExecucaoRota
        fields = [
            'id', 'data', 'horario', 'percurso', 'presentes', 'ausentes', 'sem_ticket',
            'rota_iniciada_em', 'rota_finalizada_em', 'duracao_rota_segundos',
        ]
        read_only_fields = fields

    def get_horario(self, obj) -> str:
        return timezone.localtime(obj.data_hora_saida).strftime('%H:%M')


class PassageiroHistoricoSerializer(serializers.Serializer):
    nome = serializers.CharField(source='aluno.usuario.nome', read_only=True)


class DetalheHistoricoRotaSerializer(HistoricoRotaSerializer):
    percurso_descricao = serializers.CharField(source='rota.percurso.descricao', read_only=True)
    motorista_nome = serializers.CharField(source='rota_iniciada_por.nome', read_only=True, allow_null=True)
    tickets_presentes = PassageiroHistoricoSerializer(many=True, read_only=True)
    tickets_ausentes = PassageiroHistoricoSerializer(many=True, read_only=True)
    passageiros_sem_ticket = PassageiroHistoricoSerializer(many=True, read_only=True)

    class Meta(HistoricoRotaSerializer.Meta):
        fields = HistoricoRotaSerializer.Meta.fields + [
            'percurso_descricao', 'motorista_nome', 'quantidade_vagas',
            'tickets_presentes', 'tickets_ausentes', 'passageiros_sem_ticket',
        ]
        read_only_fields = fields


class ConferenteHistoricoSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    nome = serializers.CharField(read_only=True)


class AlunoHistoricoConferenciaSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='aluno.usuario_id', read_only=True)
    nome = serializers.CharField(source='aluno.usuario.nome', read_only=True)
    cpf = serializers.CharField(source='aluno.usuario.cpf', read_only=True)
    tem_deficiencia = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_tem_deficiencia(self, obj) -> bool:
        valor = getattr(getattr(obj.aluno, 'usuario', None), 'deficiencia', None)
        return bool(valor and str(valor).strip())


class DetalheHistoricoConferenciaSerializer(HistoricoRotaSerializer):
    percurso_descricao = serializers.CharField(source='rota.percurso.descricao', read_only=True)
    conferencia_finalizada_em = serializers.DateTimeField(
        source='embarcado_em', read_only=True, allow_null=True,
    )
    conferencia_finalizada_por = ConferenteHistoricoSerializer(read_only=True, allow_null=True)
    tickets_presentes = AlunoHistoricoConferenciaSerializer(many=True, read_only=True)
    tickets_ausentes = AlunoHistoricoConferenciaSerializer(many=True, read_only=True)
    passageiros_sem_ticket = AlunoHistoricoConferenciaSerializer(many=True, read_only=True)

    class Meta(HistoricoRotaSerializer.Meta):
        fields = HistoricoRotaSerializer.Meta.fields + [
            'percurso_descricao', 'quantidade_vagas',
            'conferencia_finalizada_em', 'conferencia_finalizada_por',
            'tickets_presentes', 'tickets_ausentes', 'passageiros_sem_ticket',
        ]
        read_only_fields = fields
