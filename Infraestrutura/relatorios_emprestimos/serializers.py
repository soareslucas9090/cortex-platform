from rest_framework import serializers

from Infraestrutura.recursos.choices import TipoRecurso

from .constantes import INTERVALO_MAXIMO_DIAS


class RelatorioEmprestimosQuerySerializer(serializers.Serializer):
    data_inicio = serializers.DateField(input_formats=['%Y-%m-%d'])
    data_fim = serializers.DateField(input_formats=['%Y-%m-%d'])
    solicitante_id = serializers.IntegerField(required=False, min_value=1)
    responsavel_id = serializers.IntegerField(required=False, min_value=1)
    bloco_id = serializers.IntegerField(required=False, min_value=1)
    sala_id = serializers.IntegerField(required=False, min_value=1)
    tipo_recurso = serializers.ChoiceField(required=False, choices=TipoRecurso.choices)

    def validate(self, attrs):
        data_inicio = attrs['data_inicio']
        data_fim = attrs['data_fim']
        if data_inicio > data_fim:
            raise serializers.ValidationError({
                'data_fim': 'A data de fim deve ser posterior ou igual à data de início.',
            })
        if (data_fim - data_inicio).days > INTERVALO_MAXIMO_DIAS:
            raise serializers.ValidationError({
                'data_fim': (
                    f'O intervalo entre as datas não pode ultrapassar {INTERVALO_MAXIMO_DIAS} dias.'
                ),
            })
        return attrs


class ListarPessoasRelatorioQuerySerializer(serializers.Serializer):
    PAPEL_SOLICITANTE = 'solicitante'
    PAPEL_RESPONSAVEL = 'responsavel'
    PAPEL_CHOICES = (
        (PAPEL_SOLICITANTE, 'Solicitante'),
        (PAPEL_RESPONSAVEL, 'Responsável'),
    )

    papel = serializers.ChoiceField(choices=PAPEL_CHOICES)
    nome = serializers.CharField(required=False, allow_blank=True)


class PessoaRelatorioSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField()