from rest_framework import serializers

from .models import Contato


class ContatoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contato
        fields = ['id', 'email_academico', 'email_pessoal', 'telefone']


class ContatoInputSerializer(serializers.Serializer):
    email_academico = serializers.EmailField(required=False, allow_blank=True, default='')
    email_pessoal = serializers.EmailField(required=False, allow_blank=True, default='')
    telefone = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')

    def validate(self, data):
        if not any([data.get('email_academico'), data.get('email_pessoal'), data.get('telefone')]):
            raise serializers.ValidationError('Informe ao menos um dado de contato.')
        return data
