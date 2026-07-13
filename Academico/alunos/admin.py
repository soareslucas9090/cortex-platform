from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .models import Aluno


@admin.register(Aluno)
class AlunoAdmin(AtivoModelAdmin):
    list_display = (
        'usuario',
        'ira',
        'situacao',
        'forma_ingresso',
        'ativo',
        'created_at',
    )
    list_filter = ('ativo', 'situacao', 'forma_ingresso')
    search_fields = ('usuario__nome', 'usuario__cpf')
    autocomplete_fields = ('usuario',)
    ordering = ('usuario__nome',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario')

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: Aluno().business.criar_aluno(
                    usuario=obj.usuario_id,
                    ira=obj.ira,
                    situacao=obj.situacao,
                    forma_ingresso=obj.forma_ingresso,
                    ativo=obj.ativo,
                )
            )
            obj.pk = created.pk
            return

        dados = {
            field: form.cleaned_data[field]
            for field in form.changed_data
            if field != 'usuario'
        }
        if dados:
            run_business(lambda: obj.business.atualizar_dados(dados))
