from django.utils import timezone
from rest_framework import serializers

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
