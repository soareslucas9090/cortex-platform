from rest_framework import serializers

from .models import AlunoCurso


class AlunoCursoSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.CharField(source='aluno.usuario.nome', read_only=True)
    aluno_cpf = serializers.CharField(source='aluno.usuario.cpf', read_only=True)
    curso_nome = serializers.CharField(source='curso.nome', read_only=True)
    curso_codigo = serializers.CharField(source='curso.codigo_curso', read_only=True)

    class Meta:
        model = AlunoCurso
        fields = [
            'id',
            'aluno_id',
            'aluno_nome',
            'aluno_cpf',
            'curso_id',
            'curso_nome',
            'curso_codigo',
            'matricula',
            'ano_conclusao',
            'ira',
            'turma',
            'turno',
            'situacao_curso',
            'ativo',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'aluno_nome', 'aluno_cpf',
            'curso_nome', 'curso_codigo',
            'created_at', 'updated_at',
        ]


class CriarAlunoCursoSerializer(serializers.Serializer):
    aluno = serializers.IntegerField(required=True)
    curso = serializers.IntegerField(required=True)
    matricula = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    ano_conclusao = serializers.IntegerField(required=False, allow_null=True)
    ira = serializers.FloatField(required=False, allow_null=True)
    turma = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    turno = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    situacao_curso = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class AtualizarAlunoCursoSerializer(serializers.Serializer):
    matricula = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    ano_conclusao = serializers.IntegerField(required=False, allow_null=True)
    ira = serializers.FloatField(required=False, allow_null=True)
    turma = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    turno = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    situacao_curso = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    ativo = serializers.BooleanField(required=False)


class EncerrarAlunoCursoSerializer(serializers.Serializer):
    ano_conclusao = serializers.IntegerField(required=True)
