import re

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from .models import Usuario


class UsuarioServidorSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    cargo = serializers.IntegerField(allow_null=True)
    cargo_nome = serializers.CharField(allow_null=True)
    categoria = serializers.IntegerField()
    categoria_display = serializers.CharField()
    ativo = serializers.BooleanField()


class UsuarioTerceirizadoSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    empresa_instituicao = serializers.IntegerField(allow_null=True)
    empresa_nome = serializers.CharField(allow_null=True)
    cargo = serializers.IntegerField(allow_null=True)
    cargo_nome = serializers.CharField(allow_null=True)
    data_inicio = serializers.CharField(allow_null=True)
    data_fim = serializers.CharField(allow_null=True)
    ativo = serializers.BooleanField()


class UsuarioVinculoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    setor = serializers.IntegerField()
    setor_sigla = serializers.CharField()
    setor_nome = serializers.CharField()
    funcao = serializers.IntegerField(allow_null=True)
    funcao_papel_funcao = serializers.CharField(allow_null=True)
    funcao_descricao = serializers.CharField(allow_null=True)
    responsavel = serializers.BooleanField()
    created_at = serializers.CharField(allow_null=True)


class UsuarioSerializer(serializers.ModelSerializer):
    tem_perfil_aluno = serializers.SerializerMethodField()
    servidor = serializers.SerializerMethodField()
    terceirizado = serializers.SerializerMethodField()
    vinculos = serializers.SerializerMethodField()
    foto_secundaria = serializers.SerializerMethodField()

    def get_foto_secundaria(self, obj) -> str | None:
        from Identidade.usuarios.fotos.s3_helper import montar_url_proxy_foto_secundaria

        return montar_url_proxy_foto_secundaria(
            obj.pk,
            obj.foto_secundaria,
            self.context.get('request'),
        )

    def get_tem_perfil_aluno(self, obj) -> bool:
        """
        Indica se o usuário possui um perfil acadêmico associado.
        Detectado via reverse relation nativa do Django, sem importar
        models do domínio Acadêmico dentro do domínio Identidade.
        """
        return hasattr(obj, 'aluno') and obj.aluno is not None

    @extend_schema_field(UsuarioServidorSerializer)
    def get_servidor(self, obj):
        try:
            serv = obj.servidor
            if serv:
                return {
                    'pk': serv.pk,
                    'cargo': serv.cargo_id,
                    'cargo_nome': serv.cargo.nome if serv.cargo else None,
                    'categoria': serv.categoria,
                    'categoria_display': serv.get_categoria_display(),
                    'ativo': serv.ativo,
                }
        except Exception:
            pass
        return None

    @extend_schema_field(UsuarioTerceirizadoSerializer)
    def get_terceirizado(self, obj):
        try:
            terc = obj.terceirizado
            if terc:
                return {
                    'pk': terc.pk,
                    'empresa_instituicao': terc.empresa_instituicao_id,
                    'empresa_nome': terc.empresa_instituicao.nome if terc.empresa_instituicao else None,
                    'cargo': terc.cargo_id,
                    'cargo_nome': terc.cargo.nome if terc.cargo else None,
                    'data_inicio': terc.data_inicio.isoformat() if terc.data_inicio else None,
                    'data_fim': terc.data_fim.isoformat() if terc.data_fim else None,
                    'ativo': terc.ativo,
                }
        except Exception:
            pass
        return None

    @extend_schema_field(UsuarioVinculoSerializer(many=True))
    def get_vinculos(self, obj):
        try:
            qs = obj.setor_vinculos.select_related('setor', 'funcao').all()
            return [
                {
                    'id': v.id,
                    'setor': v.setor_id,
                    'setor_sigla': v.setor.sigla,
                    'setor_nome': v.setor.nome,
                    'funcao': v.funcao_id if v.funcao else None,
                    'funcao_papel_funcao': v.funcao.papel_funcao if v.funcao else None,
                    'funcao_descricao': v.funcao.descricao if v.funcao else None,
                    'responsavel': v.responsavel,
                    'created_at': v.created_at.isoformat() if v.created_at else None,
                }
                for v in qs
            ]
        except Exception:
            return []

    class Meta:
        model = Usuario
        fields = [
            'id', 'cpf', 'nome', 'email', 'ativo', 'is_admin',
            'foto', 'foto_secundaria', 'deficiencia', 'tem_perfil_aluno', 'created_at',
            'servidor', 'terceirizado', 'vinculos',
        ]


class CriarUsuarioSerializer(serializers.Serializer):
    cpf = serializers.CharField(
        max_length=14,
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text='CPF do usuário. Aceita com ou sem máscara (ex: 12345678901 ou 123.456.789-01).',
    )
    matricula = serializers.CharField(
        max_length=50,
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text='Matrícula do usuário (obrigatória caso o CPF não seja informado).',
    )
    nome = serializers.CharField(max_length=255)
    password = serializers.CharField(
        write_only=True,
        required=False,
        help_text='Senha (opcional). Se não for informada, será usada a senha padrão (CPF ou matrícula).',
    )
    email = serializers.EmailField(
        required=False,
        allow_null=True,
        default=None,
        help_text='E-mail do usuário (opcional).',
    )
    deficiencia = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default='',
        help_text=(
            'Descrição de deficiência ou necessidade especial (opcional). '
            'Opções válidas: deficiencia_intelectual (Deficiência Intelectual), '
            'deficiencia_visual (Deficiência Visual), deficiencia_auditiva (Deficiência Auditiva), '
            'deficiencia_multipla (Deficiência Múltipla), '
            'deficiencia_fisica (Deficiência Física). Qualquer outro valor não correspondente '
            'será normalizado como null. Strings equivalentes (ex: "Deficiência Múltipla") '
            'serão normalizadas automaticamente para sua chave de escolha.'
        ),
    )

    def validate(self, attrs):
        cpf = attrs.get('cpf')
        matricula = attrs.get('matricula')
        if not cpf and not matricula:
            raise serializers.ValidationError('É necessário informar o CPF ou a Matrícula.')
        return attrs

    def validate_deficiencia(self, value):
        from Identidade.usuarios.utils import normalizar_deficiencia

        return normalizar_deficiencia(value)

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('A senha deve ter pelo menos 8 caracteres.')
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError('A senha deve conter pelo menos uma letra maiúscula.')
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError('A senha deve conter pelo menos uma letra minúscula.')
        if not re.search(r'\d', value):
            raise serializers.ValidationError('A senha deve conter pelo menos um número.')
        if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>?/\\|`~]', value):
            raise serializers.ValidationError('A senha deve conter pelo menos um caractere especial.')
        return value


class AtualizarUsuarioSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255, required=False)
    email = serializers.EmailField(required=False, allow_null=True)
    deficiencia = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text=(
            'Descrição de deficiência ou necessidade especial (opcional). '
            'Opções válidas: deficiencia_intelectual (Deficiência Intelectual), '
            'deficiencia_visual (Deficiência Visual), deficiencia_auditiva (Deficiência Auditiva), '
            'deficiencia_multipla (Deficiência Múltipla), '
            'deficiencia_fisica (Deficiência Física). Qualquer outro valor não correspondente '
            'será normalizado como null. Strings equivalentes (ex: "Deficiência Múltipla") '
            'serão normalizadas automaticamente para sua chave de escolha.'
        ),
    )

    def validate_deficiencia(self, value):
        from Identidade.usuarios.utils import normalizar_deficiencia

        return normalizar_deficiencia(value)


class AtualizarFotoPrimariaSerializer(serializers.Serializer):
    foto = serializers.URLField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text='URL pública da foto primária vinda de sistemas externos.',
    )


class AtualizarFotoSecundariaSerializer(serializers.Serializer):
    foto = serializers.ImageField(
        help_text='Arquivo de imagem (JPEG, PNG ou WebP, até 3 MB).',
    )


class ArquivoImportacaoUsuariosSerializer(serializers.Serializer):
    file = serializers.FileField(
        help_text='Arquivo .ods da planilha multiaba de importação em lote de usuários.'
    )


class ImportacaoErroLinhaSerializer(serializers.Serializer):
    aba = serializers.CharField()
    numero_linha = serializers.IntegerField()
    campo = serializers.CharField()
    valor = serializers.JSONField(required=False, allow_null=True)
    codigo = serializers.CharField()
    mensagem = serializers.CharField()


class ResumoImportacaoSerializer(serializers.Serializer):
    total_abas_processadas = serializers.IntegerField()
    total_linhas_processadas = serializers.IntegerField()
    total_linhas_com_erro = serializers.IntegerField()
    usuarios_criados = serializers.IntegerField()
    usuarios_atualizados = serializers.IntegerField()
    contatos_criados = serializers.IntegerField()
    contatos_atualizados = serializers.IntegerField()
    enderecos_criados = serializers.IntegerField()
    enderecos_atualizados = serializers.IntegerField()
    matriculas_criadas = serializers.IntegerField()
    matriculas_atualizadas = serializers.IntegerField()
    alunos_criados = serializers.IntegerField()
    servidores_criados = serializers.IntegerField()
    terceirizados_criados = serializers.IntegerField()
    vinculos_aluno_curso_criados = serializers.IntegerField()
    lotacoes_criadas = serializers.IntegerField()


class ImportacaoUsuariosPreviewResponseSerializer(serializers.Serializer):
    sucesso = serializers.BooleanField()
    mensagem = serializers.CharField()
    resumo = ResumoImportacaoSerializer()
    erros = ImportacaoErroLinhaSerializer(many=True)
    metadados = serializers.DictField(required=False)


class ImportacaoUsuariosResponseSerializer(serializers.Serializer):
    sucesso = serializers.BooleanField()
    mensagem = serializers.CharField()
    resumo = ResumoImportacaoSerializer()
    erros = ImportacaoErroLinhaSerializer(many=True)
    metadados = serializers.DictField(required=False)


class SerializerVazio(serializers.Serializer):
    """Serializer sem campos — usado em endpoints de ação pura (desativar, reativar)."""
    pass


class StatusImportacaoLoteSerializer(serializers.ModelSerializer):
    porcentagem = serializers.SerializerMethodField()
    resultado_json = serializers.SerializerMethodField()

    class Meta:
        from .models import ImportacaoLote
        model = ImportacaoLote
        fields = [
            'id', 'status', 'total_linhas', 'linhas_processadas', 
            'porcentagem', 'resultado_json', 'created_at', 'updated_at'
        ]

    def get_porcentagem(self, obj) -> float:
        if obj.total_linhas == 0:
            return 0.0
        return round((obj.linhas_processadas / obj.total_linhas) * 100, 2)

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_resultado_json(self, obj):
        res = obj.resultado_json
        if res and isinstance(res, dict) and 'erros' in res:
            max_erros = 50
            if isinstance(res['erros'], list) and len(res['erros']) > max_erros:
                res = dict(res)
                total_erros = len(res['erros'])
                res['erros'] = res['erros'][:max_erros]
                res['mensagem_aviso'] = f"Foram omitidos {total_erros - max_erros} erros devido ao tamanho da resposta. Apenas os primeiros {max_erros} estão sendo exibidos."
        return res
