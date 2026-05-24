from rest_framework import serializers

from .choices import CategoriaServidor
from .models import Servidor


class ServidorSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario.nome', read_only=True)
    usuario_cpf = serializers.CharField(source='usuario.cpf', read_only=True)
    cargo_nome = serializers.CharField(source='cargo.nome', read_only=True)
    categoria_display = serializers.CharField(
        source='get_categoria_display', read_only=True,
    )

    class Meta:
        model = Servidor
        fields = [
            'pk', 'usuario_nome', 'usuario_cpf', 'cargo', 'cargo_nome',
            'categoria', 'categoria_display',
            'ativo', 'created_at', 'updated_at',
        ]
        read_only_fields = ['pk', 'created_at', 'updated_at']


class CriarServidorSerializer(serializers.Serializer):
    usuario_pk = serializers.IntegerField()
    cargo_pk = serializers.IntegerField()
    categoria = serializers.ChoiceField(choices=CategoriaServidor.choices)
    ativo = serializers.BooleanField(default=True, required=False)


class AtualizarServidorSerializer(serializers.Serializer):
    cargo_pk = serializers.IntegerField(required=False)
    categoria = serializers.ChoiceField(
        choices=CategoriaServidor.choices, required=False,
    )
    ativo = serializers.BooleanField(required=False)
