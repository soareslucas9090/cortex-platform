from rest_framework import serializers

from .models import Curso


class CursoSerializer(serializers.ModelSerializer):
    setor_nome = serializers.CharField(source='setor.nome', read_only=True, allow_null=True, default=None)
    setor_sigla = serializers.CharField(source='setor.sigla', read_only=True, allow_null=True, default=None)

    class Meta:
        model = Curso
        fields = [
            'id',
            'nome',
            'codigo_curso',
            'setor_id',
            'setor_nome',
            'setor_sigla',
            'ativo',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'setor_id',
            'setor_nome',
            'setor_sigla',
            'created_at',
            'updated_at',
        ]


class CriarCursoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255)
    codigo_curso = serializers.CharField(max_length=50)
    setor_id = serializers.IntegerField()


class AtualizarCursoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255, required=False)
    codigo_curso = serializers.CharField(max_length=50, required=False)
    setor_id = serializers.IntegerField(required=False)
