from rest_framework import serializers

from .choices import CategoriaRelatorioAluno


class RelatorioPeriodoSerializer(serializers.Serializer):
    data_inicio = serializers.DateField()
    data_fim = serializers.DateField()


class RelatorioResumoSerializer(serializers.Serializer):
    presentes = serializers.IntegerField()
    ausentes = serializers.IntegerField()
    em_espera = serializers.IntegerField()
    bloqueados = serializers.IntegerField()
    sem_ticket = serializers.IntegerField()


class RelatorioPorHorarioSerializer(serializers.Serializer):
    horario = serializers.CharField()
    presentes = serializers.IntegerField()
    ausentes = serializers.IntegerField()
    em_espera = serializers.IntegerField()
    bloqueados = serializers.IntegerField()
    sem_ticket = serializers.IntegerField()


class RelatorioAlunosDashboardSerializer(serializers.Serializer):
    periodo = RelatorioPeriodoSerializer()
    resumo = RelatorioResumoSerializer()
    por_horario = RelatorioPorHorarioSerializer(many=True)


class RelatorioAlunoDetalheSerializer(serializers.Serializer):
    usuario_id = serializers.IntegerField()
    nome = serializers.CharField()
    foto = serializers.URLField(allow_null=True)
    turma = serializers.CharField(allow_null=True)
    matricula = serializers.CharField(allow_null=True)
    turno = serializers.CharField(allow_null=True)
    pcd = serializers.BooleanField()
    primeiro_uso = serializers.DateField(allow_null=True)
    ultimo_uso = serializers.DateField(allow_null=True)
    ausencias = serializers.IntegerField()
    bloqueios = serializers.IntegerField()
    status = serializers.CharField()


class RelatorioAlunosDetalhesSerializer(serializers.Serializer):
    categoria = serializers.ChoiceField(choices=CategoriaRelatorioAluno.choices)
    count = serializers.IntegerField()
    next = serializers.IntegerField(allow_null=True)
    previous = serializers.IntegerField(allow_null=True)
    results = RelatorioAlunoDetalheSerializer(many=True)
