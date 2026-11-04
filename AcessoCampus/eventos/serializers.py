from rest_framework import serializers

from AppCore.common.util.util import formatar_cpf
from AcessoCampus.tipos.choices import NOME_TIPO_ENTRADA_CAMPUS
from Identidade.usuarios.models import Usuario

from .choices import StatusEventoAcesso
from .models import EventoAcesso


def _usuario_resumo(usuario):
    if usuario is None:
        return None
    return {"id": usuario.pk, "nome": usuario.nome}


def _cpf_completo(usuario):
    cpf = getattr(usuario, "cpf", None)
    return formatar_cpf(cpf) if cpf else None


class EventoAcessoSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="grupo_portaria_id", read_only=True)
    tipo_beneficiario = serializers.SerializerMethodField()
    beneficiario = serializers.SerializerMethodField()
    tipo_movimento = serializers.SerializerMethodField()
    autorizado_por = serializers.SerializerMethodField()
    data_autorizada = serializers.DateField(source="data_acesso", read_only=True)
    hora_autorizada = serializers.TimeField(source="hora_prevista", read_only=True)
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
            "id",
            "tipo_beneficiario",
            "beneficiario",
            "tipo_movimento",
            "autorizado_por",
            "data_autorizada",
            "hora_autorizada",
            "expira_em",
            "status",
            "responsavel_liberacao",
            "concluida_em",
            "expirada_em",
            "progresso",
            "acoes",
        ]

    def _eventos(self, obj):
        cache = getattr(obj, "_eventos_serializacao", None)
        if cache is None:
            cache = list(EventoAcesso().helper.eventos_do_grupo(obj.grupo_portaria_id))
            obj._eventos_serializacao = cache
        return cache

    def get_tipo_beneficiario(self, obj):
        return "TURMA" if obj.turma_origem else "INDIVIDUAL"

    def get_beneficiario(self, obj):
        if obj.turma_origem:
            return {"id": str(obj.grupo_portaria_id), "tipo": "TURMA", "nome": f"Turma {obj.turma_origem}"}
        return {"id": obj.aluno_id, "tipo": "INDIVIDUAL", "nome": obj.aluno_nome}

    def get_tipo_movimento(self, obj):
        return "ENTRADA" if obj.tipo.nome == NOME_TIPO_ENTRADA_CAMPUS else "SAIDA"

    def get_autorizado_por(self, obj):
        return _usuario_resumo(obj.solicitacao.avaliada_por)

    def get_expira_em(self, obj):
        return obj.helper.instante_expiracao(obj.data_acesso, obj.hora_prevista)

    def get_status(self, obj):
        anotado = getattr(obj, "status_operacional", None)
        if anotado:
            return anotado
        eventos = self._eventos(obj)
        if eventos and all(hasattr(evento, "registro") for evento in eventos):
            return StatusEventoAcesso.CONCLUIDA
        if any(
            evento.expirado_em or evento.helper.horario_expirado(evento.data_acesso, evento.hora_prevista)
            for evento in eventos
        ):
            return StatusEventoAcesso.EXPIRADA
        return StatusEventoAcesso.PENDENTE

    def get_responsavel_liberacao(self, obj):
        registros = [evento.registro for evento in self._eventos(obj) if hasattr(evento, "registro")]
        if not registros:
            return None
        ultimo = max(registros, key=lambda registro: registro.registrado_em)
        return _usuario_resumo(ultimo.registrado_por)

    def get_concluida_em(self, obj):
        eventos = self._eventos(obj)
        if not eventos or not all(hasattr(evento, "registro") for evento in eventos):
            return None
        return max(evento.registro.registrado_em for evento in eventos)

    def get_expirada_em(self, obj):
        datas = [evento.expirado_em for evento in self._eventos(obj) if evento.expirado_em]
        return max(datas) if datas else None

    def get_progresso(self, obj):
        eventos = self._eventos(obj)
        liberados = sum(hasattr(evento, "registro") for evento in eventos)
        return {"total": len(eventos), "liberados": liberados, "pendentes": len(eventos) - liberados}

    def get_acoes(self, obj):
        pendente = self.get_status(obj) == StatusEventoAcesso.PENDENTE
        horario_disponivel = obj.helper.horario_disponivel(obj.data_acesso, obj.hora_prevista)
        pode_registrar = pendente and horario_disponivel
        return {"pode_registrar": pode_registrar, "pode_conferir_turma": pode_registrar and bool(obj.turma_origem)}


class EventoAcessoDetalheSerializer(EventoAcessoSerializer):
    observacao = serializers.CharField(source="solicitacao.observacao_avaliacao", read_only=True)
    motivo = serializers.CharField(source="solicitacao.motivo", read_only=True)

    class Meta(EventoAcessoSerializer.Meta):
        fields = EventoAcessoSerializer.Meta.fields + ["motivo", "observacao"]


class AlunoEventoAcessoSerializer(serializers.ModelSerializer):
    aluno = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    liberado_por = serializers.SerializerMethodField()
    liberado_em = serializers.SerializerMethodField()
    pode_liberar = serializers.SerializerMethodField()

    class Meta:
        model = EventoAcesso
        fields = ["id", "aluno", "status", "liberado_por", "liberado_em", "pode_liberar"]

    def get_aluno(self, obj):
        usuario = obj.aluno.usuario
        return {"id": obj.aluno_id, "nome": obj.aluno_nome, "cpf": _cpf_completo(usuario), "foto": usuario.foto}

    def get_status(self, obj):
        return "LIBERADO" if hasattr(obj, "registro") else "PENDENTE"

    def get_liberado_por(self, obj):
        return _usuario_resumo(obj.registro.registrado_por) if hasattr(obj, "registro") else None

    def get_liberado_em(self, obj):
        return obj.registro.registrado_em if hasattr(obj, "registro") else None

    def get_pode_liberar(self, obj):
        return (
            not hasattr(obj, "registro")
            and not obj.expirado_em
            and obj.helper.horario_disponivel(obj.data_acesso, obj.hora_prevista)
        )


class RegistrarEventoAcessoSerializer(serializers.Serializer):
    responsavel_liberacao_id = serializers.IntegerField(required=False)
    aluno_ids = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=False)
    observacao = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_aluno_ids(self, value):
        return list(dict.fromkeys(value))


class ResponsavelElegivelSerializer(serializers.ModelSerializer):
    cpf = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ["id", "nome", "cpf", "foto"]

    def get_cpf(self, obj):
        return _cpf_completo(obj)
