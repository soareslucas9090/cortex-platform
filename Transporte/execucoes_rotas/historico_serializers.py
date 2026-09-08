from django.utils import timezone
from rest_framework import serializers

from Transporte.percursos.models import Percurso

from .models import ExecucaoRota


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
