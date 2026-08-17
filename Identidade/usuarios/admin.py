from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError

from AppCore.basics.admin import CortexModelAdmin, ReadOnlyModelAdmin, run_business
from Identidade.contatos.models import Contato
from Identidade.enderecos.models import Endereco
from Identidade.matriculas.models import Matricula

from .models import Usuario
from .models import ImportacaoLote, Usuario


class UsuarioCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('cpf', 'nome', 'email')


class UsuarioChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = '__all__'


class MatriculaInline(admin.TabularInline):
    model = Matricula
    extra = 0
    fields = ('matricula', 'situacao', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True


class ContatoInline(admin.TabularInline):
    model = Contato
    extra = 0
    fields = ('email_academico', 'email_pessoal', 'telefone', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True


class EnderecoInline(admin.StackedInline):
    model = Endereco
    extra = 0
    max_num = 1
    can_delete = False
    fields = (
        'logradouro',
        'numero',
        'complemento',
        'bairro',
        'cep',
        'cidade',
        'estado',
    )


@admin.register(Usuario)
class UsuarioAdmin(DjangoUserAdmin, CortexModelAdmin):
    form = UsuarioChangeForm
    add_form = UsuarioCreationForm
    inlines = (MatriculaInline, ContatoInline, EnderecoInline)
    ordering = ('nome',)
    list_display = (
        'nome',
        'cpf',
        'email',
        'ativo',
        'colaborador_externo',
        'usuario_coletivo',
        'is_admin',
        'is_staff',
        'is_superuser',
        'deficiencia',
        'created_at',
    )
    list_filter = (
        'ativo',
        'colaborador_externo',
        'usuario_coletivo',
        'is_admin',
        'is_staff',
        'is_superuser',
        'deficiencia',
    )
    search_fields = ('nome', 'cpf', 'email')
    readonly_fields = ('last_login', 'created_at', 'updated_at')
    filter_horizontal = (
        'empresas_coletivo',
        'cargos_coletivo',
        'funcoes_coletivo',
        'setores_coletivo',
    )
    actions = ('desativar_selecionados', 'reativar_selecionados')

    fieldsets = (
        (None, {'fields': ('cpf', 'password')}),
        ('Dados pessoais', {'fields': ('nome', 'email', 'foto', 'foto_secundaria', 'deficiencia', 'colaborador_externo', 'usuario_coletivo')}),
        (
            'Pool do usuário coletivo',
            {
                'fields': (
                    'empresas_coletivo',
                    'cargos_coletivo',
                    'funcoes_coletivo',
                    'setores_coletivo',
                ),
            },
        ),
        (
            'Permissões',
            {
                'fields': (
                    'ativo',
                    'is_admin',
                    'is_staff',
                    'is_superuser',
                ),
            },
        ),
        ('Auditoria', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'cpf',
                    'nome',
                    'email',
                    'password1',
                    'password2',
                    'ativo',
                    'colaborador_externo',
                    'usuario_coletivo',
                    'is_admin',
                    'is_staff',
                    'is_superuser',
                ),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request)

    @admin.action(description='Desativar usuários selecionados')
    def desativar_selecionados(self, request, queryset):
        for usuario in queryset:
            try:
                run_business(lambda current=usuario: current.business.desativar())
            except ValidationError as exc:
                self.message_user(request, f'{usuario}: {exc.message}', level='error')

    @admin.action(description='Reativar usuários selecionados')
    def reativar_selecionados(self, request, queryset):
        for usuario in queryset:
            try:
                run_business(lambda current=usuario: current.business.reativar())
            except ValidationError as exc:
                self.message_user(request, f'{usuario}: {exc.message}', level='error')

    def save_model(self, request, obj, form, change):
        if not change:
            password = form.cleaned_data.get('password1') or form.cleaned_data.get('password')
            dados = {
                'email': obj.email,
                'deficiencia': obj.deficiencia,
                'ativo': obj.ativo,
                'colaborador_externo': obj.colaborador_externo,
                'usuario_coletivo': obj.usuario_coletivo,
                'is_admin': obj.is_admin,
                'is_staff': obj.is_staff,
                'is_superuser': obj.is_superuser,
            }
            created = run_business(
                lambda: Usuario().business.criar_usuario(
                    cpf=obj.cpf,
                    nome=obj.nome,
                    password=password,
                    **dados,
                )
            )
            obj.pk = created.pk
            obj.password = created.password
            return

        if 'password' in form.changed_data and form.cleaned_data.get('password'):
            obj.set_password(form.cleaned_data['password'])
            obj.save(update_fields=['password'])

        if 'cpf' in form.changed_data:
            run_business(lambda: obj.business.atualizar_cpf(form.cleaned_data['cpf']))

        dados_atualizacao = {
            field: form.cleaned_data[field]
            for field in form.changed_data
            if field not in {'cpf', 'password', 'password1', 'password2', 'usuario_coletivo'}
        }
        if 'usuario_coletivo' in form.changed_data:
            flag_coletivo = form.cleaned_data['usuario_coletivo']
            run_business(lambda: obj.business.definir_flag_coletivo(flag_coletivo))
        if dados_atualizacao:
            run_business(lambda: obj.business.atualizar_dados(dados_atualizacao))

    def save_formset(self, request, form, formset, change):
        if formset.model is Matricula:
            self._salvar_matriculas_inline(form, formset)
            return

        if formset.model is Endereco:
            self._salvar_endereco_inline(form, formset)
            return

        formset.save()

    def _salvar_matriculas_inline(self, form, formset):
        usuario = form.instance
        for deleted in formset.deleted_objects:
            run_business(lambda current=deleted: current.business.desativar())

        for inline_form in formset.forms:
            if not inline_form.has_changed() or not inline_form.is_valid():
                continue
            matricula = inline_form.save(commit=False)
            if matricula.pk is None:
                run_business(
                    lambda numero=matricula.matricula: usuario.business.adicionar_matricula(numero)
                )
            else:
                matricula.save()

    def _salvar_endereco_inline(self, form, formset):
        usuario = form.instance
        for inline_form in formset.forms:
            if not inline_form.has_changed() or not inline_form.is_valid():
                continue
            if inline_form.cleaned_data.get('DELETE'):
                continue
            dados = {
                field: inline_form.cleaned_data[field]
                for field in inline_form.changed_data
                if field != 'DELETE'
            }
            if dados or inline_form.instance.pk is None:
                run_business(lambda: usuario.business.salvar_endereco(dados or inline_form.cleaned_data))


@admin.register(ImportacaoLote)
class ImportacaoLoteAdmin(ReadOnlyModelAdmin):
    list_display = (
        'pk',
        'status',
        'total_linhas',
        'linhas_processadas',
        'created_at',
        'updated_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('pk',)
    readonly_fields = (
        'arquivo',
        'status',
        'total_linhas',
        'linhas_processadas',
        'resultado_json',
        'created_at',
        'updated_at',
    )
    fieldsets = (
        (
            'Processamento',
            {
                'fields': (
                    'arquivo',
                    'status',
                    'total_linhas',
                    'linhas_processadas',
                    'resultado_json',
                ),
            },
        ),
        ('Auditoria', {'fields': ('created_at', 'updated_at')}),
    )
